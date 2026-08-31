import asyncio
import json
import os
import shutil
from contextlib import AsyncExitStack
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from urllib.parse import urlparse

from bson import json_util

try:
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client
    MCP_SDK_IMPORT_ERROR = None
except ImportError as import_error:
    ClientSession = Any  # type: ignore
    StdioServerParameters = None  # type: ignore
    stdio_client = None  # type: ignore
    MCP_SDK_IMPORT_ERROR = import_error

from app.core.config import settings



def _jsonable(value: Any) -> Any:
    """Convert MongoDB BSON values into normal JSON-compatible Python values."""
    return json.loads(json_util.dumps(value))


def _safe_mongo_uri(uri: str) -> str:
    parsed = urlparse(uri)
    if not parsed.scheme:
        return "mongodb://<configured>"
    host = parsed.hostname or "localhost"
    port = f":{parsed.port}" if parsed.port else ""
    path = parsed.path or ""
    return f"{parsed.scheme}://{host}{port}{path}"


class MCPManager:
    """
    Manages the MongoDB partner MCP bridge for Sarthi.

    The primary path starts the official MongoDB MCP server through stdio.
    If the server cannot start in the local demo environment, Sarthi continues
    in a read-only MongoDB fallback mode so the app remains functional.
    """

    def __init__(self) -> None:
        self.server_params: Optional[Any] = None
        self.exit_stack = AsyncExitStack()
        self.session: Optional[ClientSession] = None
        self.is_connected = False
        self.mode = "not_started"
        self.last_error: Optional[str] = None
        self.started_at: Optional[str] = None
        self.last_tool_call: Optional[Dict[str, Any]] = None
        self.tools_cache: List[Any] = []
        self.mongo_uri = getattr(settings, "MONGODB_URI", "mongodb://localhost:27017")
        self.read_only = bool(getattr(settings, "MONGODB_MCP_READ_ONLY", True))

    async def start(self) -> None:
        """Start the official MongoDB MCP server when enabled."""
        self.mongo_uri = getattr(settings, "MONGODB_URI", self.mongo_uri)
        self.read_only = bool(getattr(settings, "MONGODB_MCP_READ_ONLY", True))
        self.started_at = datetime.now(timezone.utc).isoformat()

        if not getattr(settings, "MONGODB_MCP_ENABLED", True):
            self.mode = "disabled"
            self.last_error = "MONGODB_MCP_ENABLED is false."
            pass
            return

        if MCP_SDK_IMPORT_ERROR or StdioServerParameters is None or stdio_client is None:
            self.mode = "local_mongodb_fallback"
            self.last_error = f"Python MCP SDK is not installed: {MCP_SDK_IMPORT_ERROR}"
            pass
            return

        command = shutil.which("npx.cmd") or shutil.which("npx") or "npx"
        args = ["-y", settings.PARTNER_MCP_SERVER]
        if self.read_only:
            args.append("--readOnly")

        env = os.environ.copy()
        env["MDB_MCP_CONNECTION_STRING"] = self.mongo_uri

        self.server_params = StdioServerParameters(
            command=command,
            args=args,
            env=env,
        )

        timeout = max(3, int(getattr(settings, "MONGODB_MCP_STARTUP_TIMEOUT_SECONDS", 15)))
        try:
            pass
            await asyncio.wait_for(self._start_stdio_session(), timeout=timeout)
            self.mode = "official_mcp_stdio"
            self.is_connected = True
            self.last_error = None
            pass
        except Exception as exc:
            self.is_connected = False
            self.mode = "local_mongodb_fallback"
            self.last_error = f"{type(exc).__name__}: {exc}"
            pass
            await self._reset_exit_stack()

    async def _start_stdio_session(self) -> None:
        if not self.server_params:
            raise RuntimeError("MCP server parameters were not configured.")

        stdio_transport = await self.exit_stack.enter_async_context(stdio_client(self.server_params))
        read_stream, write_stream = stdio_transport
        self.session = await self.exit_stack.enter_async_context(ClientSession(read_stream, write_stream))
        await self.session.initialize()
        result = await self.session.list_tools()
        self.tools_cache = list(result.tools or [])

    async def _reset_exit_stack(self) -> None:
        import sys
        if sys.platform == "win32":
            try:
                import subprocess
                cmd = [
                    "powershell",
                    "-NoProfile",
                    "-NonInteractive",
                    "-Command",
                    "Get-WmiObject Win32_Process -Filter \"CommandLine like '%mongodb-mcp-server%'\" | ForEach-Object { $_.Terminate() }"
                ]
                subprocess.run(cmd, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception as e:
                pass

        try:
            # Wrap aclose in a timeout to prevent uvicorn shutdown from hanging if npx gets stuck
            await asyncio.wait_for(self.exit_stack.aclose(), timeout=5.0)
        except Exception:
            pass
        self.exit_stack = AsyncExitStack()
        self.session = None


    async def stop(self) -> None:
        """Close the MCP session and subprocess if they are running."""
        if self.exit_stack:
            pass
            await self._reset_exit_stack()
        self.is_connected = False
        if self.mode == "official_mcp_stdio":
            self.mode = "stopped"

    def get_status(self) -> Dict[str, Any]:
        return {
            "partner_track": settings.PARTNER_TRACK,
            "mcp_server_package": settings.PARTNER_MCP_SERVER,
            "protocol": "Model Context Protocol",
            "mode": self.mode,
            "connected": self.is_connected,
            "read_only": self.read_only,
            "database": settings.DATABASE_NAME,
            "connection": _safe_mongo_uri(self.mongo_uri),
            "started_at": self.started_at,
            "last_error": self.last_error,
            "last_tool_call": self.last_tool_call,
            "tools_cached": len(self.tools_cache),
        }

    async def list_tools(self) -> List[Any]:
        """Fetch available tools from the MCP server or fallback adapter."""
        if self.mode == "official_mcp_stdio":
            if not self.is_connected or getattr(self.session, '_closed', False):
                pass
                await self.stop()
                await self.start()

        if self.is_connected and self.session:
            try:
                result = await asyncio.wait_for(self.session.list_tools(), timeout=8)
                self.tools_cache = list(result.tools or [])
                return self.tools_cache
            except Exception as exc:
                self.last_error = str(exc)
                pass

        return self._fallback_tools()

    def _fallback_tools(self) -> List[Dict[str, Any]]:
        return [
            {
                "name": "list-databases",
                "description": "List MongoDB databases visible to the configured Sarthi connection.",
            },
            {
                "name": "list-collections",
                "description": "List collections in the configured Sarthi MongoDB database.",
            },
            {
                "name": "count",
                "description": "Count documents in a MongoDB collection with an optional filter.",
            },
            {
                "name": "find",
                "description": "Read documents from a MongoDB collection with optional filter, projection, and limit.",
            },
            {
                "name": "aggregate",
                "description": "Run a MongoDB aggregation pipeline in read-only mode.",
            },
        ]

    async def execute_tool(self, name: str, arguments: Optional[Dict[str, Any]] = None) -> str:
        """
        Execute a MongoDB MCP tool. Uses official MCP when connected and a safe
        read-only local fallback when the stdio server is unavailable.
        """
        arguments = arguments or {}
        self.last_tool_call = {
            "name": name,
            "arguments": arguments,
            "mode": self.mode,
            "called_at": datetime.now(timezone.utc).isoformat(),
        }

        if self.mode == "official_mcp_stdio":
            # Check if session is closed or unresponsive and auto-reconnect
            if not self.is_connected or getattr(self.session, '_closed', False):
                pass
                await self.stop()
                await self.start()

        if self.is_connected and self.session:
            try:
                pass
                result = await asyncio.wait_for(self.session.call_tool(name, arguments=arguments), timeout=20)
                if not result.content:
                    return "Success: command executed but returned no data."
                return "\n".join(
                    part.text for part in result.content if hasattr(part, "text") and part.text
                )
            except Exception as exc:
                self.last_error = str(exc)
                pass
                return await self._execute_local_fallback(name, arguments)

        return await self._execute_local_fallback(name, arguments)

    async def _execute_local_fallback(self, name: str, arguments: Dict[str, Any]) -> str:
        from app.db.mongodb import get_database

        database = get_database()
        tool_name = name.lower().replace("_", "-")
        collection_name = (
            arguments.get("collection")
            or arguments.get("collectionName")
            or arguments.get("collection_name")
        )
        filter_doc = arguments.get("filter") or arguments.get("query") or {}
        projection = arguments.get("projection")
        limit = int(arguments.get("limit") or 25)

        try:
            if tool_name in {"list-databases", "mongodb-list-databases", "atlas-list-databases"}:
                names = await database.client.list_database_names()
                return json.dumps({"databases": names}, indent=2)

            if tool_name in {"list-collections", "mongodb-list-collections"}:
                names = await database.list_collection_names()
                return json.dumps({"database": settings.DATABASE_NAME, "collections": names}, indent=2)

            if tool_name in {"count", "mongodb-count", "count-documents"}:
                if not collection_name:
                    raise ValueError("A collection name is required.")
                count = await database[collection_name].count_documents(filter_doc)
                return json.dumps({"collection": collection_name, "count": count}, indent=2)

            if tool_name in {"find", "mongodb-find", "query", "mongodb-query"}:
                if not collection_name:
                    raise ValueError("A collection name is required.")
                cursor = database[collection_name].find(filter_doc, projection).limit(min(limit, 100))
                documents = await cursor.to_list(length=min(limit, 100))
                return json.dumps({"collection": collection_name, "documents": _jsonable(documents)}, indent=2)

            if tool_name in {"aggregate", "mongodb-aggregate"}:
                if not collection_name:
                    raise ValueError("A collection name is required.")
                pipeline = arguments.get("pipeline") or []
                cursor = database[collection_name].aggregate(pipeline)
                documents = await cursor.to_list(length=min(limit, 100))
                return json.dumps({"collection": collection_name, "documents": _jsonable(documents)}, indent=2)

            if tool_name in {"insert-one", "insert", "mongodb-insert-one"} and not self.read_only:
                if not collection_name:
                    raise ValueError("A collection name is required.")
                document = arguments.get("document") or {}
                result = await database[collection_name].insert_one(document)
                return json.dumps({"inserted_id": str(result.inserted_id)}, indent=2)

            return (
                f"Tool '{name}' is not available in local fallback mode. "
                "Use list-collections, count, find, or aggregate."
            )
        except Exception as exc:
            self.last_error = str(exc)
            pass
            return f"Error executing MongoDB fallback tool '{name}': {exc}"

    async def build_evidence_snapshot(self, project_id: Optional[str] = None) -> Dict[str, Any]:
        """Create a compact proof bundle for hackathon judging and generated ZIP files."""
        tools = await self.list_tools()
        tool_names = [
            tool.get("name", "unknown") if isinstance(tool, dict) else getattr(tool, "name", "unknown")
            for tool in tools
        ]

        collection_result = await self.execute_tool("list-collections", {})
        project_count_result = await self.execute_tool("count", {"collection": "projects"})

        return {
            "project_id": project_id,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "partner_track": settings.PARTNER_TRACK,
            "mcp_server_package": settings.PARTNER_MCP_SERVER,
            "mcp_status": self.get_status(),
            "available_tools": tool_names,
            "sample_operations": [
                {"tool": "list-collections", "result": collection_result[:2000]},
                {"tool": "count", "arguments": {"collection": "projects"}, "result": project_count_result[:1000]},
            ],
            "judging_note": (
                "Sarthi uses the MongoDB partner MCP bridge to expose database context to Gemini-powered "
                "planning, architecture, generation, build, and export agents."
            ),
        }


mcp_client = MCPManager()
