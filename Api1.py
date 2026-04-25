import os
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from db import collection  # Esto conecta con tu archivo db.py

app = FastAPI()

# Configuración para que funcione en Local y en Render
base_dir = os.path.dirname(os.path.realpath(__file__))
templates = Jinja2Templates(directory=os.path.join(base_dir, "templates"))

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    # El diccionario {"request": request} es OBLIGATORIO para Jinja2
    return templates.TemplateResponse("base.html", {"request": request})

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