import os
from motor.motor_asyncio import AsyncIOMotorClient

# Intenta obtener la URL de Render, si no existe usa la de pruebas (pon tu clave real aquí)
MONGO_URL = os.getenv("mongodb+srv://oscar24540_db_user:RipHawai@cluster0.ohaz2mw.mongodb.net/MOLO?retryWrites=true&w=majority")

client = AsyncIOMotorClient(MONGO_URL)
db = client["MOLO"]
collection = db["1"]