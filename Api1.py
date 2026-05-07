from fastapi import FastAPI, Form, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from bson import ObjectId
from db import collection, db
import os
from fastapi.responses import HTMLResponse, RedirectResponse
from db import usuarios

app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")

if not os.path.exists("static"):
    os.makedirs("static")

@app.get("/", response_class=HTMLResponse)
async def login():

    with open("templates/login.html", "r", encoding="utf-8") as f:
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

@app.post("/registro")
async def registro(
    usuario: str = Form(...),
    password: str = Form(...)
):

    existe = await usuarios.find_one({
        "usuario": usuario
    })

    if not existe:

        await usuarios.insert_one({
            "usuario": usuario,
            "password": password
        })

    return RedirectResponse(
        url="/actividades",
        status_code=303
    )

@app.get("/base", response_class=HTMLResponse)
async def actividades():

    with open(
        "templates/base.html",
        "r",
        encoding="utf-8"
    ) as f:

        return f.read()