from fastapi import FastAPI
from db import collection

app = FastAPI()

@app.get("/")
def home():
    return {"mensaje": "API conectada a MongoDB"}

@app.get("/estudiantes")
async def obtener_estudiantes():
    datos = []

    cursor = collection.find()

    async for doc in cursor:
        doc["_id"] = str(doc["_id"])
        datos.append(doc)

    return datos