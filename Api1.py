from fastapi import FastAPI
from db import collection

app = FastAPI()

@app.get("/estudiantes")
async def obtener_estudiantes():
    try:
        datos = []
        # Agregamos un log para ver en Render si el cursor encuentra algo
        cursor = collection.find({}) 
        
        async for doc in cursor:
            doc["_id"] = str(doc["_id"])
            datos.append(doc)
            
        print(f"Se encontraron {len(datos)} estudiantes") # Esto se verá en los logs de Render
        return datos
    except Exception as e:
        return {"error": str(e)}