from loguru import logger
import logging
import subprocess
import os
import asyncio
import glob
from motor.motor_asyncio import AsyncIOMotorClient
from app.core.config import settings


class Database:
    client: AsyncIOMotorClient = None

db = Database()

def find_mongod_path() -> str:
    """Search standard Windows installation directories for mongod.exe."""
    search_patterns = [
        r"C:\Program Files\MongoDB\Server\*\bin\mongod.exe",
        r"C:\Program Files\MongoDB\Server\8.0\bin\mongod.exe",
        r"C:\Program Files\MongoDB\Server\7.0\bin\mongod.exe",
        r"C:\Program Files\MongoDB\Server\6.0\bin\mongod.exe"
    ]
    for pattern in search_patterns:
        matches = glob.glob(pattern)
        if matches:
            return matches[0]
    return None

async def start_mongodb_process() -> bool:
    """Locate and launch the MongoDB daemon in the background with memory constraints."""
    mongod_path = find_mongod_path()
    if not mongod_path:
        logger.error("Could not locate mongod.exe in standard Windows installation paths.")
        return False
    
    # Resolve local dbpath relative to Sarthi/backend directory
    base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    db_path = os.path.join(base_dir, "mongodb_data")
    os.makedirs(db_path, exist_ok=True)
    
    logger.info(f"Auto-launching MongoDB from: {mongod_path}")
    logger.info(f"Using database path: {db_path}")
    
    try:
        # 1. Run database repair first to clear any stale locks or recovery panic states
        repair_cmd = [mongod_path, "--dbpath", db_path, "--repair"]
        logger.info(f"Running database repair: {' '.join(repair_cmd)}")
        repair_proc = subprocess.run(repair_cmd, capture_output=True, text=True, timeout=30)
        logger.info(f"Database repair finished with exit code {repair_proc.returncode}")
        
        # 2. Spawn mongod process
        cmd = [
            mongod_path,
            "--dbpath", db_path,
            "--port", "27017",
            "--wiredTigerCacheSizeGB", "0.25",
            "--setParameter", "diagnosticDataCollectionEnabled=false"
        ]
        
        creation_flags = 0
        if os.name == 'nt':
            # Run detached process so it persists if python uvicorn reloads
            creation_flags = 0x00000008 | 0x00000200
            
        subprocess.Popen(
            cmd,
            creationflags=creation_flags,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            close_fds=True
        )
        logger.info("MongoDB background process spawned successfully.")
        return True
    except Exception as ex:
        logger.error(f"Failed to spawn MongoDB background process: {ex}")
        return False

async def connect_to_mongo():
    """Create MongoDB client and connect to database, falling back to local if the remote is unreachable."""
    configured_uri = settings.MONGODB_URI
    is_remote = not ("localhost" in configured_uri or "127.0.0.1" in configured_uri)

    logger.info(f"Connecting to MongoDB at: {configured_uri}")
    db.client = AsyncIOMotorClient(configured_uri, serverSelectionTimeoutMS=3000)

    try:
        await db.client.admin.command('ping')
        logger.info("Successfully connected to MongoDB.")
        return
    except Exception as e:
        if is_remote:
            logger.warning(
                f"Failed to connect to remote MongoDB cluster: {e}.\n"
                "This could be due to IP whitelist restrictions or lack of network connectivity.\n"
                "Falling back to local MongoDB..."
            )
        else:
            logger.warning(f"Local MongoDB at {configured_uri} not running: {e}. Attempting auto-start...")

    # Fallback to local MongoDB
    local_uri = "mongodb://localhost:27017"
    if await start_mongodb_process():
        # Wait a short duration for MongoDB to initialize and listen
        await asyncio.sleep(3)
        
        logger.info(f"Connecting to local fallback MongoDB at: {local_uri}")
        db.client = AsyncIOMotorClient(local_uri, serverSelectionTimeoutMS=5000)
        try:
            await db.client.admin.command('ping')
            logger.info("Successfully connected to local fallback MongoDB.")
            settings.MONGODB_URI = local_uri
            return
        except Exception as e:
            logger.error(f"Failed to connect to local MongoDB after auto-start: {e}")
    else:
        logger.error("Could not auto-start MongoDB. Database connection unavailable.")

async def close_mongo_connection():
    """Close MongoDB client connection."""
    if db.client:
        db.client.close()
        logger.info("MongoDB connection closed.")

def get_database():
    """Retrieve database instance."""
    if db.client is None:
        db.client = AsyncIOMotorClient(settings.MONGODB_URI)
    return db.client[settings.DATABASE_NAME]


