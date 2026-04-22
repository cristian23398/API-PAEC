import os
from motor.motor_asyncio import AsyncIOMotorClient

# Intenta obtener la variable de Render
MONGO_URL = os.getenv("MONGO_URL")

# Si por alguna razón Render no la lee, pégala aquí directamente (solo como prueba)
if not MONGO_URL:
    MONGO_URL = "mongodb+srv://oscar24540_db_user:RipHawai@cluster0.ohaz2mw.mongodb.net/MOLO?retryWrites=true&w=majority"

client = AsyncIOMotorClient(MONGO_URL)
db = client["MOLO"]
collection = db["1"]