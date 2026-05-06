from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from db import collection
from fastapi.staticfiles import StaticFiles
import os

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