from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, Request
from sqlmodel import Session, select
from app.models.profiles import Profile
from app.models.users import User
from app.auth.auth import get_current_user, get_session
from app.utils.image_handler import save_image, delete_image


router = APIRouter()

@router.post("/")
async def create_profile(
    nombre: str = Form(...),
    apellido: str = Form(...),
    imagen: UploadFile = File(None),
    direccion: str = Form(None),
    departamento: str = Form(None),
    provincia: str = Form(None),
    bio: str = Form(None),
    request: Request = None,
    session: Session = Depends(get_session),
    current_user = Depends(get_current_user)
):
    # Comprobar si el usuario ya tiene perfil
    existing = session.exec(
        select(Profile).where(Profile.user_id == current_user.id)
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Ya tienes un perfil")

    imagen_url = None
    imagen_id = None
    
    if imagen and imagen.filename:
        try:
            result = await save_image(imagen)
            imagen_url = result.get("secure_url")
            imagen_id = result.get("public_id")
            if not imagen_url or not imagen_id:
                raise HTTPException(status_code=500, detail="Respuesta inesperada de Cloudinary")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al guardar imagen: {e}")
    else:
        imagen_url = None
        imagen_id = None

    profile = Profile(
        nombre=nombre,
        apellido=apellido,
        imagen_url=imagen_url,
        imagen_id=imagen_id,
        direccion=direccion,
        departamento=departamento,
        provincia=provincia,
        bio=bio,
        user_id=current_user.id
    )

    session.add(profile)
    session.commit()
    session.refresh(profile)

    # Devuelves la URL pública en la respuesta
    return {
        "id": profile.id,
        "nombre": profile.nombre,
        "apellido": profile.apellido,
        "imagen_url": imagen_url,
        "direccion": profile.direccion,
        "departamento": profile.departamento,
        "provincia": profile.provincia,
        "bio": profile.bio,
        "is_active": profile.is_active,
    }


@router.get("/")
async def get_profile(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    profile = session.exec(
        select(Profile).where(Profile.user_id == current_user.id)
    ).first()

    if not profile:
        raise HTTPException(status_code=404, detail="Perfil no encontrado")

    return profile


@router.delete("/")
async def delete_profile(
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    profile = session.exec(
        select(Profile).where(Profile.user_id == current_user.id)
    ).first()

    if not profile:
        raise HTTPException(status_code=404, detail="Perfil no encontrado")

    # Eliminar la imagen anterior si existe
    if profile.imagen_url:
        delete_image(profile.imagen_url)
               
    session.delete(profile)
    session.commit()

    return {"message": "Perfil eliminado correctamente"}


@router.patch("/")
async def update_profile(
    nombre: str = Form(None),
    apellido: str = Form(None),
    direccion: str = Form(None),
    departamento: str = Form(None),
    provincia: str = Form(None),
    bio: str = Form(None),
    imagen: UploadFile = File(None),
    current_user: User = Depends(get_current_user),
    session: Session = Depends(get_session)
):
    profile = session.exec(
        select(Profile).where(Profile.user_id == current_user.id)
    ).first()

    if not profile:
        raise HTTPException(status_code=404, detail="Perfil no encontrado")

    # Procesar la imagen solo si se proporciona una nueva
    if imagen and imagen.filename:
        try:
            # Eliminar la imagen anterior si existe
            if profile.imagen_url:
                delete_image(profile.imagen_url)
            # Guardar la nueva imagen
            result = await save_image(imagen)
            profile.imagen_url = result["secure_url"]
            profile.imagen_id = result["public_id"]
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    # Actualizar los campos si se envían
    if nombre is not None and nombre != "string":
        profile.nombre = nombre
    if apellido is not None and apellido != "string":
        profile.apellido = apellido
    if direccion is not None and direccion != "string":
        profile.direccion = direccion
    if departamento is not None and departamento != "string":
        profile.departamento = departamento
    if provincia is not None and provincia != "string":
        profile.provincia = provincia
    if bio is not None and bio != "string":
        profile.bio = bio


    session.add(profile)
    session.commit()
    session.refresh(profile)
    return profile


@router.get("/listperfiles")
async def get_perfiles(
    session: Session = Depends(get_session)
    ):
    perfiles = session.exec(select(Profile)).all()
    return perfiles