from fastapi import FastAPI, Form, HTTPException, Depends
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from bson import ObjectId
import os

# Importamos desde tu archivo db.py
from db import collection, db, usuarios

app = FastAPI()

# Configuración de estáticos
app.mount("/static", StaticFiles(directory="static"), name="static")

if not os.path.exists("static"):
    os.makedirs("static")

# --- CONFIGURACIÓN DE ROLES ---
# Agrega aquí los correos que quieres que sean Administradores
ADMIN_EMAILS = ["oscar24540@cbtis75.edu.mx"]

# --- RUTAS DE NAVEGACIÓN ---

@app.get("/", response_class=HTMLResponse)
async def login():
    with open("templates/login.html", "r", encoding="utf-8") as f:
        return f.read()

@app.get("/base", response_class=HTMLResponse)
async def actividades():
    with open("templates/base.html", "r", encoding="utf-8") as f:
        return f.read()

# --- LÓGICA DE USUARIOS ---

@app.post("/registro")
async def registro(
    usuario: str = Form(...),
    password: str = Form(...)
):
    usuario = usuario.strip().lower()
    
    # Verificamos si ya existe
    existe = await usuarios.find_one({"usuario": usuario})
    
    if not existe:
        # Determinamos el rol al momento de guardar
        rol = "admin" if usuario in ADMIN_EMAILS else "lector"
        
        await usuarios.insert_one({
            "usuario": usuario,
            "password": password,
            "rol": rol
        })

    # Redirigimos a la base (en un sistema real aquí crearías una cookie de sesión)
    return RedirectResponse(url="/base", status_code=303)

# --- RUTAS DE DATOS (ESTUDIANTES) ---

@app.get("/estudiantes")
async def obtener_estudiantes():
    try:
        datos = []
        cursor = collection.find({})
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            datos.append(doc)
        return datos
    except Exception as e:
        return {"error": str(e)}

@app.post("/agregar")
async def agregar(
    nombre: str = Form(...),
    correo_usuario: str = Form(...) # El frontend debe enviar quién intenta agregar
):
    # VALIDACIÓN DE SEGURIDAD
    if correo_usuario.lower() not in ADMIN_EMAILS:
        raise HTTPException(
            status_code=403, 
            detail="Acceso denegado: Solo administradores pueden agregar."
        )

    nombre = nombre.strip()
    if not nombre:
        raise HTTPException(status_code=400, detail="Nombre vacío")
    
    res = await collection.insert_one({"nombre": nombre})
    return {"id": str(res.inserted_id), "nombre": nombre}

@app.delete("/eliminar/{id}")
async def eliminar(id: str, correo_solicitante: str): # FastAPI leerá esto del Query String (?correo_solicitante=...)
    usuario_clean = correo_solicitante.lower().strip()
    
    if usuario_clean not in ADMIN_EMAILS:
        raise HTTPException(status_code=403, detail="Acceso denegado")

    try:
        obj_id = ObjectId(id)
        await collection.delete_one({"_id": obj_id})
        return {"mensaje": "borrado"}
    except:
        raise HTTPException(status_code=400, detail="ID no válido")