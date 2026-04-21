from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def home():
    return {"Mensaje": "¡FastAPI está vivo!"}
