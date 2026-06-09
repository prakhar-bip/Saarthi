from typing import Any, Dict

from fastapi import APIRouter
from pydantic import BaseModel

from app.services.mcp_service import mcp_client

router = APIRouter(prefix="/api/mcp", tags=["mcp"])


class ExecuteToolRequest(BaseModel):
    tool_name: str
    arguments: Dict[str, Any] = {}


def _format_tool(tool: Any) -> Dict[str, Any]:
    if isinstance(tool, dict):
        return {
            "name": tool.get("name", "unknown"),
            "description": tool.get("description", ""),
        }
    return {
        "name": getattr(tool, "name", "unknown"),
        "description": getattr(tool, "description", ""),
    }


@router.get("/status")
async def get_mcp_status():
    """Return MongoDB partner MCP bridge status for hackathon verification."""
    return {"status": "success", "mcp": mcp_client.get_status()}


@router.get("/tools")
async def get_mcp_tools():
    """Retrieve tools exposed by the MongoDB MCP bridge."""
    tools = await mcp_client.list_tools()
    return {
        "status": "success",
        "mcp": mcp_client.get_status(),
        "tools": [_format_tool(tool) for tool in tools],
    }


@router.post("/execute")
async def execute_mcp_tool(request: ExecuteToolRequest):
    """Execute a MongoDB MCP tool manually from the Sarthi dashboard or API."""
    result_text = await mcp_client.execute_tool(request.tool_name, request.arguments)
    return {
        "status": "success",
        "mcp": mcp_client.get_status(),
        "result": result_text,
    }


@router.get("/evidence")
async def get_mcp_evidence(project_id: str | None = None):
    """Return a compact evidence bundle for Devpost judging and demo videos."""
    evidence = await mcp_client.build_evidence_snapshot(project_id=project_id)
    return {"status": "success", "evidence": evidence}
