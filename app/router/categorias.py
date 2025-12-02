from fastapi import APIRouter, Depends, HTTPException, File, Form, UploadFile, Request, status
from sqlmodel import Session, select
from app.db.database import get_session
from typing import List
from app.models.categorias import Categoria
from app.models.users import User

from app.utils.image_categoria import save_image_categoria, delete_image_categoria
from app.auth.auth import require_admin

router = APIRouter(prefix="/categorias", tags=["categorias"])

#from app.config import settings

#CLOUDINARY_CLOUD_NAME=settings.CLOUDINARY_CLOUD_NAME
#CLOUDINARY_API_KEY=settings.CLOUDINARY_API_KEY
#CLOUDINARY_API_SECRET=settings.CLOUDINARY_API_SECRET

@router.post("/")
async def create_categoria(
    nombre: str = Form(...),
    descripcion: str = Form(...),
    imagen: UploadFile = File(None),
    session: Session = Depends(get_session),
    #user = Depends(require_admin)
):

    imagen_url = None
    imagen_id = None
    
    if imagen and imagen.filename:
        try:
            result = await save_image_categoria(imagen)
            imagen_url = result.get("secure_url")
            imagen_id = result.get("public_id")
            if not imagen_url or not imagen_id:
                raise HTTPException(status_code=500, detail="Respuesta inesperada de Cloudinary")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al guardar imagen: {e}")
    else:
        imagen_url = None
        imagen_id = None

    categoria = Categoria(
        name=nombre,
        descripcion=descripcion,
        imagen_url=imagen_url,
        imagen_id=imagen_id
    )
    
       # Persistir en la base de datos
    session.add(categoria)
    session.commit()
    session.refresh(categoria)

    # Devolver respuesta al frontend
    return {
        "id": categoria.id,
        "name": categoria.name,
        "descripcion": categoria.descripcion,
        "imagen_url": categoria.imagen_url,
    }

@router.get("/")
async def get_categoria(session: Session = Depends(get_session)):
    categorias = session.exec(select(Categoria)).all()
    return categorias


@router.get("/{categoria_id}", response_model=Categoria)
async def get_categoria(categoria_id: int, session: Session = Depends(get_session)):
    categoria = session.get(Categoria, categoria_id)
    if not categoria:
        raise HTTPException(status_code=404, detail="Categoria no encontrada")
    return categoria


@router.patch("/{categoria_id}")
async def update_categoria(
    categoria_id: int,
    nombre: str = Form(None),
    descripcion: str = Form(None),
    imagen: UploadFile = File(None),
    session: Session = Depends(get_session),
    user = Depends(require_admin)
):
    categoria = session.exec(
        select(Categoria).where(Categoria.id == categoria_id)
    ).first()
    if not categoria:
        raise HTTPException(status_code=404, detail="Categoria no encontrada")

    # Procesar la imagen solo si se proporciona una nueva
    if imagen and imagen.filename:
        try:
            # Eliminar la imagen anterior si existe
            if categoria.imagen_id:
                delete_image_categoria(categoria.imagen_id)

            # Guardar la nueva imagen
            result = await save_image_categoria(imagen)
            categoria.imagen_url = result["secure_url"]
            categoria.imagen_id = result["public_id"]
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    # Actualizar los campos si se envían
    if nombre is not None and nombre != "string":
        categoria.name = nombre
    if descripcion is not None and descripcion != "string":
        categoria.descripcion = descripcion

    session.add(categoria)
    session.commit()
    session.refresh(categoria)
    return {
        "id": categoria.id,
        "name": categoria.name,
        "descripcion": categoria.descripcion,
        "imagen_url": categoria.imagen_url,
    }


@router.delete("/{categoria_id}", status_code=202)
def delete_categoria(
    categoria_id: int,
    session: Session = Depends(get_session),
    user = Depends(require_admin)
):
    categoria = session.get(Categoria, categoria_id)
    if not categoria:
        raise HTTPException(status_code=404, detail="Categoria no encontrada")

    # Eliminar la imagen anterior si existe
    if categoria.imagen_id:
        delete_image_categoria(categoria.imagen_id)

    session.delete(categoria)
    session.commit()
    return {"message": "Categoria eliminada correctamente"}
