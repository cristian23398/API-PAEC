from motor.motor_asyncio import AsyncIOMotorClient

MONGO_URL = "mongodb+srv://USUARIO:PASSWORD@cluster0.xxxx.mongodb.net/miDB"

client = AsyncIOMotorClient(MONGO_URL)
