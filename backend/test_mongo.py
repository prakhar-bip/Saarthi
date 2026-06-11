import asyncio
import os
import sys
from motor.motor_asyncio import AsyncIOMotorClient

# Ensure backend/app can be imported
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.config import settings

async def main():
    print("Configured MONGODB_URI:", settings.MONGODB_URI)
    client = AsyncIOMotorClient(settings.MONGODB_URI, serverSelectionTimeoutMS=5000)
    try:
        print("Pinging MongoDB...")
        await client.admin.command('ping')
        print("Ping successful!")
        
        db = client[settings.DATABASE_NAME]
        collections = await db.list_collection_names()
        print("Database:", settings.DATABASE_NAME)
        print("Collections:", collections)
    except Exception as e:
        print("Failed to connect to MongoDB:", e)
    finally:
        client.close()

if __name__ == "__main__":
    asyncio.run(main())
