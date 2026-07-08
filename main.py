import os
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv

# Cargar variables de entorno (OPENAI_API_KEY, DATABASE_URL, etc.)
load_dotenv()

from app.routers import router  # noqa: E402

app = FastAPI(
    title="Sysiphus.io",
    description="Herramienta para pensar mejor y escribir ensayos más profundos.",
)

# Archivos estáticos (CSS, JS, imágenes)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Rutas de la API y vistas web
app.include_router(router)

if __name__ == "__main__":
    import uvicorn
    # Para arrancar el servidor local: python main.py
    # Las migraciones se aplican con: alembic upgrade head
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)
