from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from db import collection
from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI, Form, HTTPException
from bson import ObjectId
import os
from db import collection, db 

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

if not os.path.exists("static"):
    os.makedirs("static")

@app.get("/", response_class=HTMLResponse)
async def home():
    with open("templates/base.html", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/estudiantes")
async def obtener_estudiantes():
    try:
        datos = []

        cursor = collection.find({})

        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            datos.append(doc)

        print(f"Se encontraron {len(datos)} estudiantes")
        return datos

    except Exception as e:
        return {"error": str(e)}
    
@app.post("/agregar")
async def agregar(nombre: str = Form(...)):
    nombre = nombre.strip()
    if not nombre:
        raise HTTPException(status_code=400, detail="Nombre vacío")
    res = await collection.insert_one({"nombre": nombre})
    return {"id": str(res.inserted_id), "nombre": nombre}

@app.delete("/eliminar/{id}")
async def eliminar(id: str):

    try:
        obj_id = ObjectId(id)
    except:
        raise HTTPException(status_code=400, detail="ID inválido")
        
    await collection.delete_one({"_id": obj_id})
    await db.asistencias.delete_many({"estudiante_id": id})
    return {"mensaje": "borrado"}