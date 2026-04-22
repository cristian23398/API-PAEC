import os
from motor.motor_asyncio import AsyncIOMotorClient

# Render leerá la variable MONGO_URL que configuramos en su panel
MONGO_URL = os.getenv("MONGO_URL")

client = AsyncIOMotorClient(MONGO_URL)
db = client["MOLO"]
collection = db["1"]