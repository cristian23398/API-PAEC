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
    imagen: UploadFile = File(...),
    crop_x: float = Form(default=0.5),
    crop_y: float = Form(default=0.5)
):
    if correo_solicitante.lower().strip() not in ADMIN_EMAILS:
        raise HTTPException(status_code=403)

    contenido = await imagen.read()
    es_video = imagen.content_type.startswith("video/")

    if es_video:
        # Comprimir video con ffmpeg si está disponible, si no subir directo
        try:
            import subprocess, tempfile, uuid
            ext = imagen.filename.rsplit(".", 1)[-1].lower()
            tmp_in = f"/tmp/{uuid.uuid4()}.{ext}"
            tmp_out = f"/tmp/{uuid.uuid4()}.mp4"
            with open(tmp_in, "wb") as f:
                f.write(contenido)
            # Comprimir a max 720p, CRF 28
            cmd = [
                "ffmpeg", "-i", tmp_in,
                "-vf", "scale='min(720,iw)':-2",
                "-c:v", "libx264", "-crf", "28",
                "-preset", "fast", "-c:a", "aac",
                "-b:a", "128k", "-y", tmp_out
            ]
            subprocess.run(cmd, capture_output=True, timeout=120)
            with open(tmp_out, "rb") as f:
                contenido = f.read()
            os.remove(tmp_in)
            os.remove(tmp_out)
        except Exception:
            pass  # Si falla ffmpeg, subir original

        resultado = cloudinary.uploader.upload(
            contenido,
            resource_type="video",
            folder="estudiantes",
            public_id=imagen.filename.rsplit(".", 1)[0],
            overwrite=True,
            chunk_size=6000000  # 6MB chunks para videos grandes
        )
    else:
        img = Image.open(io.BytesIO(contenido))
        if img.mode in ("RGBA", "P"):
            img = img.convert("RGB")

        # ✅ Aplicar crop basado en la posición que eligió el admin
        w, h = img.size
        target_ratio = 4 / 3
        current_ratio = w / h

        if current_ratio > target_ratio:
            # Más ancha — recortar lados
            new_w = int(h * target_ratio)
            left = int((w - new_w) * crop_x)
            img = img.crop((left, 0, left + new_w, h))
        else:
            # Más alta — recortar arriba/abajo
            new_h = int(w / target_ratio)
            top = int((h - new_h) * crop_y)
            img = img.crop((0, top, w, top + new_h))

        buffer = io.BytesIO()
        img.save(buffer, format="JPEG", quality=75)
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

@app.post("/cambiar-password")
async def cambiar_password(usuario: str = Form(...), password_nueva: str = Form(...)):
    usuario = usuario.strip().lower()
    if not usuario or not password_nueva:
        raise HTTPException(status_code=400, detail="Datos incompletos")
    if len(password_nueva) < 6:
        raise HTTPException(status_code=400, detail="Mínimo 6 caracteres")
    user_db = await usuarios.find_one({"usuario": usuario})
    if not user_db:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    await usuarios.update_one({"usuario": usuario}, {"$set": {"password": password_nueva}})
    return {"ok": True}

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

# ⚠️ TEMPORAL: borrar después de usarlo una vez
@app.get("/reset-usuarios")
async def reset_usuarios():
    await usuarios.delete_many({})
    return {"mensaje": "Usuarios borrados"}