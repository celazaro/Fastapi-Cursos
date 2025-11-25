from fastapi import APIRouter, Depends, HTTPException, File, Form, UploadFile, Request, status
from sqlmodel import Session, select
from app.db.database import get_session
from typing import List  # Import List from typing
from app.models.categorias import Categoria  # Importar el modelo correspondiente
from app.models.users import User
from pathlib import Path

from app.utils.image_categoria import save_image_categoria, delete_image_categoria

from app.db.database import get_session
from app.auth.auth import require_admin

router = APIRouter( prefix="/categorias", tags=["categorias"])


@router.post("/")
async def create_categoria(
    nombre: str = Form(...),
    descripcion: str = Form(...),
    imagen: UploadFile = File(None),
    session: Session = Depends(get_session),
    request: Request = None,
    user = Depends(require_admin)
    ):
    
    imagen_url = None
    
    
    if imagen:
        try:
            ruta_relativa = await save_image_categoria(imagen)
            imagen_url = f"{request.base_url}media/categorias/{Path(ruta_relativa).name}"
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al guardar imagen: {e}")
    
    categoria = Categoria(
        name=nombre,
        descripcion=descripcion,
        imagen_url=ruta_relativa if imagen else None  # Guardar la URL de la imagen
    )
    
    
    session.add(categoria)
    session.commit()
    session.refresh(categoria)

    return {
            "id": categoria.id,
            "name": categoria.name,
            "descripcion": categoria.descripcion,
            "imagen_url": imagen_url,  # Devolver la URL de la imagen
        }

@router.get("/")
async def get_categoria(
    session: Session = Depends(get_session)
    ):
    categorias = session.exec(select(Categoria)).all()
    return categorias


@router.get("/{categoria_id}", response_model=Categoria)
async def get_categoria(
    categoria_id: int, 
    session: Session = Depends(get_session)
    ):
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
            if categoria.imagen_url:
                delete_image_categoria(categoria.imagen_url)
            # Guardar la nueva imagen
            imagen_path = await save_image_categoria(imagen)
            categoria.imagen_url = imagen_path
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
        "profesion": categoria.descripcion,
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
    if categoria.imagen_url:
        delete_image_categoria(categoria.imagen_url)
    
    session.delete(categoria)
    session.commit()
    return {"message": "Categoria eliminada correctamente"}

