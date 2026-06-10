from fastapi import FastAPI, Form, HTTPException, File, UploadFile
from fastapi.responses import HTMLResponse, JSONResponse
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
async def inicio():
    with open("templates/base.html", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/login", response_class=HTMLResponse)
async def login():
    with open("templates/login.html", "r", encoding="utf-8") as f:
        return f.read()

# ✅ Registro con contraseña obligatoria
@app.post("/registro")
async def registro(usuario: str = Form(...), password: str = Form(...)):
    usuario = usuario.strip().lower()
    if not usuario or not password:
        raise HTTPException(status_code=400, detail="Correo y contraseña son obligatorios")
    user_db = await usuarios.find_one({"usuario": usuario})
    if user_db:
        raise HTTPException(status_code=409, detail="El correo ya está registrado")
    rol = "admin" if usuario in ADMIN_EMAILS else "lector"
    await usuarios.insert_one({"usuario": usuario, "password": password, "rol": rol})
    return {"ok": True, "usuario": usuario, "rol": rol}

# ✅ Login verificando contraseña en el backend
@app.post("/login-check")
async def login_check(usuario: str = Form(...), password: str = Form(...)):
    usuario = usuario.strip().lower()
    user_db = await usuarios.find_one({"usuario": usuario})
    if not user_db:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    if user_db["password"] != password:
        raise HTTPException(status_code=401, detail="Contraseña incorrecta")
    return {"ok": True, "usuario": usuario, "rol": user_db.get("rol", "lector")}

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
    seccion: str = Form(...),
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
        "tipo": "video" if es_video else "imagen",
        "seccion": seccion,
        "likes": [],
        "comentarios": []
    })
    return {"id": str(res.inserted_id)}

# ✅ Like toggle
@app.post("/like/{id}")
async def toggle_like(id: str, usuario: str = Form(...)):
    doc = await collection.find_one({"_id": ObjectId(id)})
    if not doc:
        raise HTTPException(status_code=404)
    likes = doc.get("likes", [])
    if usuario in likes:
        likes.remove(usuario)
    else:
        likes.append(usuario)
    await collection.update_one({"_id": ObjectId(id)}, {"$set": {"likes": likes}})
    return {"likes": len(likes), "liked": usuario in likes}

# ✅ Agregar comentario
@app.post("/comentar/{id}")
async def comentar(id: str, usuario: str = Form(...), texto: str = Form(...)):
    if not texto.strip():
        raise HTTPException(status_code=400, detail="Comentario vacío")
    comentario = {"usuario": usuario.split("@")[0], "texto": texto.strip()}
    await collection.update_one(
        {"_id": ObjectId(id)},
        {"$push": {"comentarios": comentario}}
    )
    return {"ok": True, "comentario": comentario}

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
@app.get("/reset-usuarios")
async def reset_usuarios():
    await usuarios.delete_many({})
    return {"mensaje": "Usuarios borrados. Ya puedes registrarte de nuevo."}