import os
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
from app.api import auth, chats, projects, mcp, feedback
from app.services.ws_manager import manager
from app.services.mcp_service import mcp_client

from app.core.logger import setup_logging

# Setup modern logger
setup_logging()
from loguru import logger

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing services on startup...")
    await connect_to_mongo()
    
    # Purge other databases and seed default user 'Asur'
    from app.db.mongodb import seed_default_user_and_clean_slate
    await seed_default_user_and_clean_slate()
    
    await connect_to_redis()
    
    logger.info("Starting MongoDB partner MCP bridge...")
    try:
        await mcp_client.start()
    except Exception as exc:
        logger.warning("MongoDB MCP bridge startup failed; continuing without blocking API startup: %s", exc)
    
    yield
    logger.info("Closing services on shutdown...")
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
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
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
            logger.debug(f"Received WS message: {data}")
            if data == "ping":
                await websocket.send_text("pong")
    except WebSocketDisconnect:
        manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
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
    except Exception as e:
        logger.error(f"Project WS error for {project_id}: {e}")
        manager.disconnect(websocket, project_id=project_id)
