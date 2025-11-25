from fastapi import APIRouter, Depends, HTTPException, status, Request
from sqlmodel import Session, select
from app.models.users import User
from app.schemas.users import UserCreate, UserRead
from app.db.database import get_session
from app.auth.auth import require_admin

from app.schemas.users import ChangePassword
from app.core.security import verify_password, get_password_hash
from app.auth.auth import get_current_user  # importa las funciones de autentificación

from pydantic import BaseModel

router = APIRouter()


@router.get("/", response_model=list[UserRead])
def list_users(
    session: Session = Depends(get_session), 
    #current_user: dict = Depends(get_current_user)  # Protección con autenticación
    ):  
    users = session.exec(select(User)).all()
     
    return [user.model_dump() for user in users]  # Convertir SQLModel → Pydantic


@router.post("/", response_model=UserRead, status_code=201)
def create_user(user: UserCreate, session: Session = Depends(get_session)):
    
    # Verificamos si el email o username ya existe
    statement = select(User).where((User.email == user.email) | (User.username == user.username))
    existing_user = session.exec(statement).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="El usuario ya existe")
    
    hashed_pw = get_password_hash(user.password)
    db_user = User(**user.model_dump(exclude={"password"}))  # Convertir Pydantic → SQLModel y Excluir contraseña en texto plano
    db_user.password = hashed_pw  # Guardar la versión encriptada

    
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user  # Se convierte automáticamente en UserRead


@router.get("/{user_id}", response_model=UserRead, status_code=200)
def get_user(
    user_id: int, 
    session: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user)  # Protección con autenticación
    ):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Este usuario no existe")
    return user.model_dump()    # Convertir SQLModel → Pydantic 


@router.delete("/{user_id}", status_code=202)
def delete_user(
    user_id: int, 
    session: Session = Depends(get_session),
    admin: User = Depends(require_admin)  # ✅ Solo admins/superadmins
    ):
    user = session.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Este usuario no existe")
    session.delete(user)
    session.commit()
    
    return {"detail": "Usuario eliminado correctamente"}  # Mensaje de éxito


@router.put("/{user_id}", response_model=UserRead, status_code=200)
def update_user(
    user_id: int, 
    user: UserCreate, session: Session = Depends(get_session),
    current_user: dict = Depends(get_current_user)  # Protección con autenticación
    ):
    
    # Verificar si el email o username ya existe (si se están actualizando)
    if user.email or user.username:
        statement = select(User).where(
            (User.id != user_id) &  # Excluir el usuario actual
            ((User.email == user.email) | (User.username == user.username))
        )
        existing_user = session.exec(statement).first()
        if existing_user:
            raise HTTPException(
                status_code=400,
                detail="El email o username ya está en uso"
            )
            
    hashed_pw = get_password_hash(user.password)  # Encriptar la nueva contraseña
    db_user = session.get(User, user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="Este usuario no existe")
        
    for key, value in user.model_dump(exclude={"password"}).items():  # Excluir el password en texto plano
        setattr(db_user, key, value)  # Actualizar los campos del usuario

    db_user.password = hashed_pw  # Guardar la versión encriptada de la contraseña

    session.add(db_user)
    session.commit()  
    session.refresh(db_user)
    
    return db_user.model_dump()  # Convertir SQLModel → Pydantic      


@router.patch("/change-password", status_code=status.HTTP_200_OK)
def change_password(
    payload: ChangePassword,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    user = session.get(User, current_user.id)
    if not user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    if not verify_password(payload.current_password, user.password):
        raise HTTPException(
            status_code=401,
            detail="Contraseña actual incorrecta"
        )

    user.password = get_password_hash(payload.new_password)
    session.add(user)
    session.commit()
    session.refresh(user)

    return {"detail": "Contraseña actualizada correctamente"}

class RoleUpdate(BaseModel):
    new_role: str


@router.patch("/{user_id}/role", status_code=200)
def update_user_role(
    user_id: int,
    payload: RoleUpdate,  # 👈 body esperado
    session: Session = Depends(get_session),
    admin: User = Depends(require_admin)  # ✅ Solo admins/superadmins
):
    db_user = session.get(User, user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    db_user.role = payload.new_role
    session.add(db_user)
    session.commit()
    session.refresh(db_user)

    return {"detail": f"Rol actualizado a {payload.new_role}"}

