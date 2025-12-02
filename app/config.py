# app/config.py

import cloudinary

from pydantic import PostgresDsn,  Field, AnyUrl # Importa SecretStr para la clave sensible
from pydantic_settings import BaseSettings # type: ignore


class Settings(BaseSettings):
    # El valor por defecto se usa si la variable no se encuentra en el .env
    APP_NAME: str = "API de Cursos CLA"
    
    # ----------------------------------------
    # Conexión a la Base de Datos
    # ----------------------------------------
    
    # URL de Conexión a la Base de Datos
    DATABASE_URL: PostgresDsn = Field(
        ..., # Indica que es obligatoria
        description="URL de conexión completa a la base de datos."
    )
    
    # ----------------------------------------
    # Token de Seguridad de Mercado Pago
    # ----------------------------------------
    
    # Token de Seguridad
    MERCADO_PAGO_ACCESS_TOKEN: str 
    
    URL_BASE_SERVIDOR: str
    
    # Campos para Cloudinary
    CLOUDINARY_CLOUD_NAME: str
    CLOUDINARY_API_KEY: str
    CLOUDINARY_API_SECRET: str
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


# Crea la instancia única de la configuración
settings = Settings()       
        
# Inicializar Cloudinary con settings
cloudinary.config(
    cloud_name=settings.CLOUDINARY_CLOUD_NAME,
    api_key=settings.CLOUDINARY_API_KEY,
    api_secret=settings.CLOUDINARY_API_SECRET
)

