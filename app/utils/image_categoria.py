# Utilidades para manejar imágenes en el sistema de archivos
# en este caso debe instalarse Pillow: pip install Pillow

import os
from fastapi import UploadFile # type: ignore
from PIL import Image
from pathlib import Path
import shutil
import uuid

import cloudinary.uploader


ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}


async def save_image_categoria(file: UploadFile):
    extension = file.filename.split(".")[-1].lower()
    if f".{extension}" not in ALLOWED_EXTENSIONS:
        raise ValueError("Tipo de archivo no permitido")

    result = cloudinary.uploader.upload(
        file.file,
        folder="categorias",
        resource_type="image"
    )
    return result  # dict con secure_url y public_id

def delete_image_categoria(public_id: str):
    """
    Borra una imagen de Cloudinary usando su public_id.
    Ejemplo de public_id: 'categorias/uuid.jpg'
    """
    result = cloudinary.uploader.destroy(public_id, resource_type="image")
    return result