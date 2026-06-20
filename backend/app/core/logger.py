import logging
import sys
import contextvars
import asyncio
import re
from typing import Any
from loguru import logger

# ContextVar to capture the active project_id for log-broadcasting
current_project_id = contextvars.ContextVar("current_project_id", default=None)


class InterceptHandler(logging.Handler):
    """
    Default handler from examples in loguru documentation.
    See https://loguru.readthedocs.io/en/stable/overview.html#entirely-compatible-with-standard-logging
    """

    def emit(self, record):
        # Get corresponding Loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def ws_log_sink(message):
    """
    Loguru sink that intercept logs and broadcasts them dynamically to the connected 
    project websocket client.
    """
    record = message.record
    proj_id = current_project_id.get()
    if not proj_id:
        return

    sender = record["name"]
    # Filter: strictly allow record names starting with "app."
    # and skip names containing "llm_router" or "ws_manager".
    if not sender.startswith("app."):
        return
    if "llm_router" in sender or "ws_manager" in sender:
        return

    try:
        # Get the running event loop
        loop = asyncio.get_running_loop()
        if loop.is_running():
            msg_text = record["message"]
            
            # Clean up message: strip ANSI escape color codes
            msg_text = re.sub(r'\x1b\[[0-9;]*m', '', msg_text)
            
            level = record["level"].name
            time_str = record["time"].strftime("%H:%M:%S")

            # Construct clean logs payload
            payload = {
                "type": "log",
                "project_id": proj_id,
                "message": msg_text,
                "level": level,
                "timestamp": time_str,
                "sender": sender
            }
            
            # Import connection manager dynamically to avoid circular import issues
            from app.services.ws_manager import manager
            loop.create_task(manager.broadcast_to_project(proj_id, payload))
    except RuntimeError:
        # No running event loop in this thread
        pass


def setup_logging():
    """
    Configures loguru to intercept standard logging and sets up console, file, and websocket sinks.
    """
    # Remove default loguru handler
    logger.remove()

    # Intercept standard logging messages
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

    # Intercept logs from specific libraries
    for logger_name in ("uvicorn.access", "uvicorn.error", "uvicorn", "fastapi"):
        logging_logger = logging.getLogger(logger_name)
        logging_logger.handlers = [InterceptHandler()]
        logging_logger.propagate = False

    # Define dynamic HEAL level in loguru
    try:
        logger.level("HEAL", no=26, color="<cyan><bold>")
    except ValueError:
        pass

    # 1. Add console sink with highly-readable format
    logger.add(
        sys.stderr,
        format="<green>{time:HH:mm:ss}</green> | <level>{level: <7}</level> | <level>{message}</level>",
        level="INFO",
        colorize=True,
    )

    # 2. Add file sink (keeps detailed metadata for offline analysis)
    logger.add(
        "logs/sarthi.log",
        rotation="10 MB",
        retention="10 days",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="INFO",
    )

    # 3. Add dynamic WebSocket sink
    logger.add(
        ws_log_sink,
        level="INFO",
    )
    
    logger.info("Logging configured with loguru. WebSocket live sink enabled.")


class SarthiConsoleLogger:
    """
    Sarthi custom console logging utilities to log phases, agents, successes, warnings, and healing/errors beautifully.
    """
    @staticmethod
    async def log_phase_header(db: Any, project_id: str, phase_name: str, symbol: str = "🚀"):
        msg = (
            f"┌────────────────────────────────────────────────────────┐\n"
            f"│ {symbol}  PHASE: {phase_name.upper():<44} │\n"
            f"└────────────────────────────────────────────────────────┘"
        )
        logger.info(msg)

    @staticmethod
    async def log_agent_start(db: Any, project_id: str, agent_name: str, task_desc: str):
        msg = f"🟢 [{agent_name}] {task_desc}"
        logger.info(msg)

    @staticmethod
    async def log_success(db: Any, project_id: str, agent_name: str, message: str):
        msg = f"✅ [{agent_name}] {message}"
        logger.success(msg)

    @staticmethod
    async def log_warning(db: Any, project_id: str, agent_name: str, message: str):
        msg = f"⚠️ [{agent_name}] {message}"
        logger.warning(msg)

    @staticmethod
    async def log_healing(db: Any, project_id: str, agent_name: str, message: str):
        msg = f"🩹 [{agent_name}] {message}"
        try:
            logger.log("HEAL", msg)
        except Exception:
            logger.info(msg)

    @staticmethod
    async def log_error(db: Any, project_id: str, agent_name: str, message: str):
        msg = f"❌ [{agent_name}] {message}"
        logger.error(msg)
