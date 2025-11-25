from fastapi import FastAPI
from app.db.database import create_db_and_tables
from app.router import users, auth, private, profiles
from app.router import profesores, categorias, cursos, user_payments

from app.payments.routes import router as mp_router

from fastapi.middleware.cors import CORSMiddleware

from fastapi.staticfiles import StaticFiles
import os

from .config import settings

app = FastAPI()

# Configurar CORS si es necesario
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    create_db_and_tables()

@app.get("/") 
async def root():
    return {"message": settings.APP_NAME,}  

# Obtener ruta absoluta a la carpeta 'media'
ruta_media = os.path.join(os.path.dirname(os.path.dirname(__file__)), "media")

# Montar la carpeta 'media' en la ruta '/media', esto es útil para servir archivos estáticos como imágenes de perfil desde el sistema de archivos a través de la API

app.mount("/media", StaticFiles(directory=ruta_media), name="media")


# Include the router from the users module

app.include_router(users.router, prefix="/users", tags=["users"])
app.include_router(auth.router)

# Incluir endpoints protegidos, como /me
app.include_router(private.router, tags=["private"])

app.include_router(profiles.router, prefix="/profile", tags=["profiles"])

app.include_router(profesores.router)
app.include_router(categorias.router)
app.include_router(cursos.router, prefix="/cursos", tags=["cursos"])

app.include_router(mp_router)
app.include_router(user_payments.router)

