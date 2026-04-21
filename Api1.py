from fastapi import FastAPI
from db import db

app = FastAPI()

@app.get("/")
def home():
    return {"mensaje": "API funcionando"}

@app.post("/usuarios")
async def crear_usuario():
    usuario = {"nombre": "Oscar", "edad": 20}
    result = await db.usuarios.insert_one(usuario)
    return {"id": str(result.inserted_id)}

@app.get("/usuarios")
async def obtener_usuarios():
    usuarios = []
    cursor = db.usuarios.find()

    async for doc in cursor:
        doc["_id"] = str(doc["_id"])
        usuarios.append(doc)

    return usuarios