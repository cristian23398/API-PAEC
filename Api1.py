from fastapi import FastAPI
from db import db


app = FastAPI()

@app.get("/")
def home():
    return {"Mensaje": "¡FastAPI está vivo!"}

app = FastAPI()
