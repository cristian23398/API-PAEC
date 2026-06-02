from fastapi import FastAPI, Form, HTTPException, File, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from bson import ObjectId
import os
import cloudinary
import cloudinary.uploader

from db import collection, db, usuarios

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

# ✅ Configurar Cloudinary con variables de entorno
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

ADMIN_EMAILS = ["oscar24540@cbtis75.edu.mx"]

# ... tus rutas GET sin cambios ...

@app.post("/agregar")
async def agregar(
    nombre: str = Form(...),
    correo_solicitante: str = Form(...),
    imagen: UploadFile = File(...)
):
    if correo_solicitante.lower().strip() not in ADMIN_EMAILS:
        raise HTTPException(status_code=403)

    # ✅ Subir imagen a Cloudinary en lugar del disco local
    contenido = await imagen.read()
    resultado = cloudinary.uploader.upload(
        contenido,
        folder="estudiantes",          # carpeta opcional en Cloudinary
        public_id=imagen.filename.rsplit(".", 1)[0],  # nombre sin extensión
        overwrite=True
    )

    # Guardamos la URL permanente que devuelve Cloudinary
    imagen_url = resultado["secure_url"]

    res = await collection.insert_one({
        "nombre": nombre,
        "imagen_url": imagen_url,
        "cloudinary_id": resultado["public_id"]  # ✅ guardamos el ID para poder borrarla
    })
    return {"id": str(res.inserted_id)}


@app.delete("/eliminar/{id}")
async def eliminar(id: str, correo_solicitante: str):
    if correo_solicitante.lower().strip() not in ADMIN_EMAILS:
        raise HTTPException(status_code=403)

    # ✅ Buscar el documento para obtener el cloudinary_id
    doc = await collection.find_one({"_id": ObjectId(id)})
    if doc and "cloudinary_id" in doc:
        cloudinary.uploader.destroy(doc["cloudinary_id"])  # borra de Cloudinary

    await collection.delete_one({"_id": ObjectId(id)})
    return {"mensaje": "borrado"}