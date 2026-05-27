import json
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.db.mongodb import connect_to_mongo, close_mongo_connection
from app.db.redis_client import connect_to_redis, close_redis_connection
from app.api import auth, chats, projects
from app.services.ws_manager import manager

# Setup logger
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing services on startup...")
    await connect_to_mongo()
    await connect_to_redis()
    yield
    logger.info("Closing services on shutdown...")
    await close_mongo_connection()
    await close_redis_connection()

app = FastAPI(
    title=settings.PROJECT_NAME,
    lifespan=lifespan,
    version="1.0.0"
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


# ──────────────────────────────────────────────────────────────
# Health check endpoint  (required for cloud deployment)
# ──────────────────────────────────────────────────────────────
@app.get("/api/health", tags=["system"])
async def health_check():
    return {
        "status": "healthy",
        "service": settings.PROJECT_NAME,
        "version": "1.0.0",
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
        "documentation": "/docs",
    }


# ──────────────────────────────────────────────────────────────
# WebSocket — global notifications channel
# ──────────────────────────────────────────────────────────────
@app.websocket("/ws/notifications")
async def websocket_notifications(websocket: WebSocket):
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
