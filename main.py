import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from app.routers import router

# Cargar variables de entorno para obtener OPENAI_API_KEY
load_dotenv()

from app.database import engine, ensure_sqlite_schema
from app import models

# Crear todas las tablas en la base de datos (SQLite local)
models.Base.metadata.create_all(bind=engine)
ensure_sqlite_schema()

app = FastAPI(
    title="Sysiphus.io",
    description="Herramienta para pensar mejor y escribir ensayos más profundos."
)

# Montar los archivos estáticos en la ruta /static
app.mount("/static", StaticFiles(directory="static"), name="static")

# Añadir enrutador principal para la vista web y la API de IA
app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    # Para arrancar servidor local: python main.py
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
