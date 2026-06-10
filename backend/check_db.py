import asyncio
from motor.motor_asyncio import AsyncIOMotorClient

async def main():
    client = AsyncIOMotorClient("mongodb+srv://prakharbatwal418_db_user:Prakhar@sm.rovocve.mongodb.net/?appName=SM")
    db = client.sarthi
    chats = await db.chats.find({}).to_list(10)
    for c in chats:
        print(f"Chat ID: {c['_id']}, User ID: {c.get('user_id')}")

asyncio.run(main())
