from fastapi import FastAPI
from db import db

app = FastAPI()

@app.get("/")
def home():
    return {"Mensaje": "¡FastAPI está vivo y funcionando!"}

@app.post("/usuarios")
async def crear_usuario():
    usuario = {"nombre": "Oscar", "edad": 20}
    result = await db.usuarios.insert_one(usuario)
    return {"id": str(result.inserted_id)}
