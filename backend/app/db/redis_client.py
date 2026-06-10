from loguru import logger
import logging
import redis.asyncio as aioredis
from app.core.config import settings


class RedisManager:
    client: aioredis.Redis = None

redis_db = RedisManager()

async def connect_to_redis():
    """Establish async connection to Redis."""
    try:
        url = f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}"
        logger.info(f"Connecting to Redis at: {url}")
        redis_db.client = aioredis.from_url(url, encoding="utf-8", decode_responses=True, socket_timeout=2.0)
        # Verify connection
        await redis_db.client.ping()
        logger.info("Successfully connected to Redis.")
    except Exception as e:
        logger.info("Redis is not running on localhost:6379. Caching/task queues will run in default in-memory mode.")
        redis_db.client = None

async def close_redis_connection():
    """Close Redis client connection."""
    if redis_db.client:
        await redis_db.client.close()
        logger.info("Redis connection closed.")

def get_redis() -> aioredis.Redis:
    """Retrieve async Redis client."""
    return redis_db.client
