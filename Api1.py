from fastapi import FastAPI, Form, HTTPException, File, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from bson import ObjectId
import os
import cloudinary
import cloudinary.uploader
from PIL import Image
import io

from db import collection, db, usuarios

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

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
    imagen: UploadFile = File(...)
):
    if correo_solicitante.lower().strip() not in ADMIN_EMAILS:
        raise HTTPException(status_code=403)

    contenido = await imagen.read()
    es_video = imagen.content_type.startswith("video/")

    if es_video:
        resultado = cloudinary.uploader.upload(
            contenido,
            resource_type="video",
            folder="estudiantes",
            public_id=imagen.filename.rsplit(".", 1)[0],
            overwrite=True
        )
    else:
        img = Image.open(io.BytesIO(contenido))
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")
        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=70)
        buffer.seek(0)
        contenido_comprimido = buffer.read()

        resultado = cloudinary.uploader.upload(
            contenido_comprimido,
            resource_type="image",
            folder="estudiantes",
            public_id=imagen.filename.rsplit(".", 1)[0],
            overwrite=True
        )

    imagen_url = resultado["secure_url"]
    res = await collection.insert_one({
        "nombre": nombre,
        "imagen_url": imagen_url,
        "cloudinary_id": resultado["public_id"],
        "tipo": "video" if es_video else "imagen"
    })
    return {"id": str(res.inserted_id)}

@app.delete("/eliminar/{id}")
async def eliminar(id: str, correo_solicitante: str):
    if correo_solicitante.lower().strip() not in ADMIN_EMAILS:
        raise HTTPException(status_code=403)

    doc = await collection.find_one({"_id": ObjectId(id)})
    if doc and "cloudinary_id" in doc:
        resource_type = "video" if doc.get("tipo") == "video" else "image"
        cloudinary.uploader.destroy(doc["cloudinary_id"], resource_type=resource_type)

    await collection.delete_one({"_id": ObjectId(id)})
    return {"mensaje": "borrado"}