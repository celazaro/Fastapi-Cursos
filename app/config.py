# app/config.py

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
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

# Crea la instancia única de la configuración
settings = Settings() 

