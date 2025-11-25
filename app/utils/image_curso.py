# Utilidades para manejar imágenes en el sistema de archivos
# en este caso debe instalarse Pillow: pip install Pillow

import os
from fastapi import UploadFile # type: ignore
from PIL import Image
from pathlib import Path
import shutil
import uuid


# Crear directorio media si no existe

MEDIA_DIR = Path("media/cursos")
MEDIA_DIR.mkdir(parents=True, exist_ok=True)


ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}


async def save_image_curso(file: UploadFile) -> str:
    extension = Path(file.filename).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise ValueError("Tipo de archivo no permitido")

    filename = f"{uuid.uuid4()}{extension}"
    filepath = MEDIA_DIR / filename

    with filepath.open("wb") as buffer:
        shutil.copyfileobj(file.file, buffer)
        
    # Optimizar la imagen
    with Image.open(filepath) as img:
        # Mantener una calidad razonable pero optimizada
        img.save(filepath, optimize=True, quality=85)

    return f"media/cursos/{filename}"  # Ruta relativa para guardar en DB


def delete_image_curso(image_url: str):
    if image_url:
        # Esto debe funcionar si imagen_url es algo como "media/profesores/archivo.jpg"
        path = Path(image_url)
        if path.exists() and path.is_file():
            path.unlink()
            print("✅ Imagen eliminada:", path)
        else:
            print("⚠ Archivo no encontrado en:", path)