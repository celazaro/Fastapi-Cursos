from fastapi import APIRouter, Depends, HTTPException, File, Form, UploadFile, Request
from sqlmodel import Session, select
from app.db.database import get_session
from app.models.profesores import Profesor  # Importar el modelo correspondiente

from app.utils.image_profesor import save_image_profesor, delete_image_profesor
from app.auth.auth import require_admin

router = APIRouter( prefix="/profesores", tags=["profesores"])

@router.post("/")
async def create_profesor(
    nombre: str = Form(...),
    profesion: str = Form(...),
    imagen: UploadFile = File(None),
    session: Session = Depends(get_session),
    request: Request = None,
    user = Depends(require_admin)
    ):
    
    imagen_url = None
    imagen_id = None
    
    if imagen and imagen.filename:
        try:
            result = await save_image_profesor(imagen)
            imagen_url = result.get("secure_url")
            imagen_id = result.get("public_id")
        
            if not imagen_url or not imagen_id:
                raise HTTPException(status_code=500, detail="Respuesta inesperada de Cloudinary")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al guardar imagen: {e}")
        
    else:
        imagen_url = None
        imagen_id = None
    
    profesor = Profesor(
        name=nombre,
        profesion=profesion,
        imagen_url=imagen_url,
        imagen_id=imagen_id
    )
    
    
    session.add(profesor)
    session.commit()
    session.refresh(profesor)

    return {
            "id": profesor.id,
            "name": profesor.name,
            "profesion": profesor.profesion,
            "imagen_url": imagen_url,  # Devolver la URL de la imagen
        }

@router.get("/")
async def get_profesor(
    session: Session = Depends(get_session)
    ):
    profesores = session.exec(select(Profesor)).all()
    return profesores

@router.get("/{profesor_id}", response_model=Profesor)
async def get_profesor(profesor_id: int, session: Session = Depends(get_session)):
    profesor = session.get(Profesor, profesor_id)
    if not profesor:
        raise HTTPException(status_code=404, detail="Profesor no encontrado")
    return profesor

@router.patch("/{profesor_id}")
async def update_profesor(
    profesor_id: int,
    nombre: str = Form(None),
    profesion: str = Form(None),
    imagen: UploadFile = File(None), 
    session: Session = Depends(get_session),
    user = Depends(require_admin)
):
    profesor = session.exec(
        select(Profesor).where(Profesor.id == profesor_id)
    ).first()
    if not profesor:
        raise HTTPException(status_code=404, detail="Profesor no encontrado")
    # Procesar la imagen solo si se proporciona una nueva
    if imagen and imagen.filename:
        try:
            # Eliminar la imagen anterior si existe
            if profesor.imagen_id:
                delete_image_profesor(profesor.imagen_id)
            # Guardar la nueva imagen
            result = await save_image_profesor(imagen)
            profesor.imagen_url = result["secure_url"]
            profesor.imagen_id = result["public_id"]
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    # Actualizar los campos si se envían
    if nombre is not None and nombre != "string":
        profesor.name = nombre
    if profesion is not None and profesion != "string":
        profesor.profesion = profesion
        
    session.add(profesor)
    session.commit()
    session.refresh(profesor)
    return {
        "id": profesor.id,
        "name": profesor.name,
        "profesion": profesor.profesion,
        "imagen_url": profesor.imagen_url,
    }
    

@router.delete("/{profesor_id}", status_code=202)
def delete_profesor(
    profesor_id: int, 
    session: Session = Depends(get_session),
    user = Depends(require_admin)
    ):
    profesor = session.get(Profesor, profesor_id)
    if not profesor:
        raise HTTPException(status_code=404, detail="Profesor no encontrado")
    
        # Eliminar la imagen anterior si existe
    if profesor.imagen_id:
        delete_image_profesor(profesor.imagen_id)
        
    session.delete(profesor)
    session.commit()
    return {"message": "Profesor eliminado correctamente"}

