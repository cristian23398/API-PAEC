from fastapi import FastAPI, Form, HTTPException, File, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from bson import ObjectId
import os
import shutil # Para guardar la imagen en el disco

from db import collection, db, usuarios

app = FastAPI()

# Carpeta para guardar las imágenes subidas
UPLOAD_DIR = "static/uploads"
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

app.mount("/static", StaticFiles(directory="static"), name="static")

ADMIN_EMAILS = ["oscar24540@cbtis75.edu.mx"]

@app.get("/", response_class=HTMLResponse)
async def login():
    with open("templates/login.html", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/base", response_class=HTMLResponse)
async def actividades():
    with open("templates/base.html", "r", encoding="utf-8") as f:
        return f.read()

@app.post("/registro")
async def registro(usuario: str = Form(...), password: str = Form(...)):
    usuario = usuario.strip().lower()
    user_db = await usuarios.find_one({"usuario": usuario})
    if not user_db:
        rol = "admin" if usuario in ADMIN_EMAILS else "lector"
        await usuarios.insert_one({"usuario": usuario, "password": password, "rol": rol})
    return RedirectResponse(url="/base", status_code=303)

@app.get("/estudiantes")
async def obtener_estudiantes():
    datos = []
    async for doc in collection.find({}):
        doc["_id"] = str(doc["_id"])
        datos.append(doc)
    return datos

@app.post("/agregar")
async def agregar(
    nombre: str = Form(...), 
    correo_solicitante: str = Form(...),
    imagen: UploadFile = File(...) # Recibimos el archivo
):
    if correo_solicitante.lower().strip() not in ADMIN_EMAILS:
        raise HTTPException(status_code=403)

    # Guardar la imagen físicamente
    file_path = f"{UPLOAD_DIR}/{imagen.filename}"
    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(imagen.file, buffer)
    
    # Guardar en la base de datos la ruta de la imagen
    res = await collection.insert_one({
        "nombre": nombre,
        "imagen_url": f"/static/uploads/{imagen.filename}"
    })
    return {"id": str(res.inserted_id)}

@app.delete("/eliminar/{id}")
async def eliminar(id: str, correo_solicitante: str):
    if correo_solicitante.lower().strip() not in ADMIN_EMAILS:
        raise HTTPException(status_code=403)
    
    # Opcional: Podrías buscar el documento y borrar el archivo de /static/uploads antes de borrar el doc
    await collection.delete_one({"_id": ObjectId(id)})
    return {"mensaje": "borrado"}