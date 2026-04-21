from fastapi import FastAPI
from db import collection 

app = FastAPI()

@app.get("/estudiantes")
async def estudiantes():
    datos = []
    cursor = collection.find()

    async for doc in cursor:
        doc["_id"] = str(doc["_id"])
        datos.append(doc)

    return datos
