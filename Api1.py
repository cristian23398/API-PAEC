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

@app.get("/estudiantes")
async def estudiantes():
    datos = []
    cursor = db.usuarios.find() # Cambié 'collection' por 'db.usuarios' para que coincida
    async for doc in cursor:
        doc["_id"] = str(doc["_id"])
        datos.append(doc)
    return datos
