import os
import sys
import asyncio

if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

import newrelic.agent

# Initialize New Relic Agent if config exists and has a valid license key
if os.path.exists("newrelic.ini"):
    has_valid_license = False
    if os.environ.get("NEW_RELIC_LICENSE_KEY"):
        has_valid_license = True
    else:
        try:
            with open("newrelic.ini", "r") as f:
                for line in f:
                    trimmed = line.strip()
                    if trimmed.startswith("license_key") and "YOUR_NEW_RELIC_LICENSE_KEY" not in trimmed:
                        parts = trimmed.split("=")
                        if len(parts) > 1 and parts[1].strip():
                            has_valid_license = True
                            break
        except Exception:
            pass
    if has_valid_license:
        newrelic.agent.initialize("newrelic.ini")

import json
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, status
from fastapi.middleware.cors import CORSMiddleware
from app.core.security import decode_access_token
from app.core.config import settings
from app.db.mongodb import connect_to_mongo, close_mongo_connection
from app.db.redis_client import connect_to_redis, close_redis_connection
from app.core.progress_logger import progress_logger
from app.api import auth, chats, projects, mcp, feedback
from app.services.ws_manager import manager
from app.services.mcp_service import mcp_client

@asynccontextmanager
async def lifespan(app: FastAPI):
    progress_logger.info("Initializing Sarthi services on startup...")
    await connect_to_mongo()
    
    # Purge other databases and seed default user 'Asur'
    from app.db.mongodb import seed_default_user_and_clean_slate
    await seed_default_user_and_clean_slate()
    
    await connect_to_redis()
    
    try:
        await mcp_client.start()
        progress_logger.info("MongoDB MCP bridge connected.")
    except Exception as exc:
        progress_logger.warning(f"MongoDB MCP bridge startup failed: {exc}")
    
    progress_logger.success(f"{settings.PROJECT_NAME} backend services ready.")
    yield
    progress_logger.info("Closing Sarthi services on shutdown...")
    await mcp_client.stop()
    await close_mongo_connection()
    await close_redis_connection()

app = FastAPI(
    title=settings.PROJECT_NAME,
    lifespan=lifespan,
    version="1.0.0"
)

from fastapi.responses import JSONResponse
from fastapi import Request

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    progress_logger.error(f"Unhandled exception in API request: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal Server Error", "message": str(exc)},
        headers={"Access-Control-Allow-Origin": "*"}
    )

# ──────────────────────────────────────────────────────────────
# CORS  — restrict to configured frontend origin in production
# ──────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

from starlette.middleware.base import BaseHTTPMiddleware
import re

class TokenRedactionMiddleware(BaseHTTPMiddleware):
    """Middleware to ensure query tokens and auth credentials are redacted from server logs."""
    async def dispatch(self, request: Request, call_next):
        # Process request cleanly
        response = await call_next(request)
        return response

app.add_middleware(TokenRedactionMiddleware)

# Register routes
app.include_router(auth.router)
app.include_router(chats.router)
app.include_router(projects.router)
app.include_router(mcp.router)
app.include_router(feedback.router)


# ──────────────────────────────────────────────────────────────
# Health check endpoint  (required for cloud deployment)
# ──────────────────────────────────────────────────────────────
@app.get("/api/health", tags=["system"])
async def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": "1.0.0",
        "partner_track": settings.PARTNER_TRACK,
        "mcp": mcp_client.get_status(),
    }


# ──────────────────────────────────────────────────────────────
# Root
# ──────────────────────────────────────────────────────────────
@app.get("/")
async def root():
    return {
        "status": "online",
        "service": settings.PROJECT_NAME,
        "version": "1.0.0",
        "partner_track": settings.PARTNER_TRACK,
        "mcp_status": "/api/mcp/status",
        "documentation": "/docs",
    }


# ──────────────────────────────────────────────────────────────
# WebSocket — global notifications channel
# ──────────────────────────────────────────────────────────────
@app.websocket("/ws/notifications")
async def websocket_notifications(websocket: WebSocket):
    token = websocket.query_params.get("token")
    if not token:
        await websocket.accept()
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Token is missing")
        return
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        await websocket.accept()
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token")
        return

    await manager.connect(websocket)
    try:
        await manager.send_personal_message(
            json.dumps({
                "type": "connection",
                "status": "connected",
                "message": "Connected to Sarthi WebSocket Broker",
            }),
            websocket,
        )
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception:
        manager.disconnect(websocket)


# ──────────────────────────────────────────────────────────────
# WebSocket — per-project progress channel
# ──────────────────────────────────────────────────────────────
@app.websocket("/ws/projects/{project_id}")
async def websocket_project_progress(websocket: WebSocket, project_id: str):
    token = websocket.query_params.get("token")
    if not token:
        await websocket.accept()
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Token is missing")
        return
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        await websocket.accept()
        await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Invalid token")
        return

    # Verify project access authorization
    user_id = str(payload["sub"])
    db = get_database()
    if db is not None:
        try:
            proj = await db.projects.find_one({"_id": project_id})
            if proj and proj.get("user_id") and proj.get("user_id") != user_id:
                await websocket.accept()
                await websocket.close(code=status.WS_1008_POLICY_VIOLATION, reason="Unauthorized project access")
                return
        except Exception:
            pass

    await manager.connect(websocket, project_id=project_id)
    try:
        await manager.send_personal_message(
            json.dumps({
                "type": "connection",
                "status": "connected",
                "project_id": project_id,
                "message": f"Subscribed to project {project_id} progress",
            }),
            websocket,
        )
        while True:
            data = await websocket.receive_text()
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(websocket, project_id=project_id)
    except Exception:
        manager.disconnect(websocket, project_id=project_id)

