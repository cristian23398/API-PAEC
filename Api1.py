from fastapi import FastAPI
from fastapi.responses import HTMLResponse
from db import collection

app = FastAPI()

# Ruta principal
@app.get("/", response_class=HTMLResponse)
async def home():
    with open("base.html", "r", encoding="utf-8") as f:
        return f.read()

# API de estudiantes
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