import os
from motor.motor_asyncio import AsyncIOMotorClient
from dotenv import load_dotenv

load_dotenv("mongo.env") # Indicamos el nombre exacto de tu archivo

MONGO_URL = os.getenv("MONGO_URL")
client = AsyncIOMotorClient(MONGO_URL)
db = client.MOLO # Usa el nombre de tu DB que pusiste en la captura