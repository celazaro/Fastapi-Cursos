# Utilidades para manejar imágenes en el sistema de archivos
# en este caso debe instalarse Cloudinary: pip install cloudinary

from fastapi import UploadFile # type: ignore

import cloudinary.uploader


ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}


async def save_image(file: UploadFile):
    extension = file.filename.split(".")[-1].lower()
    if f".{extension}" not in ALLOWED_EXTENSIONS:
        raise ValueError("Tipo de archivo no permitido")

    result = cloudinary.uploader.upload(
        file.file,
        folder="usuarios",
        resource_type="image"
    )
    return result  # dict con secure_url y public_id


def delete_image(public_id: str):
    """
    Borra una imagen de Cloudinary usando su public_id.
    Ejemplo de public_id: 'usuarios/uuid.jpg'
    """
    result = cloudinary.uploader.destroy(public_id, resource_type="image")
    return result