from fastapi import APIRouter, Depends, HTTPException, status

from sqlmodel import Session, select
from app.db.database import get_session
from app.models.users import User
from app.core.security import verify_password

from app.schemas.token import  LoginData

from app.auth.auth import create_access_token

from sqlalchemy.orm import selectinload


router = APIRouter()


@router.post("/login")
def login(data: LoginData, session: Session = Depends(get_session)):
    statement = (
        select(User)
        .where(User.email == data.email)
        .options(selectinload(User.profile))  # Cargar perfil si es necesario
    )
    user = session.exec(statement).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario no existente")
    if  not verify_password(data.password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Constraseña incorrecta")

    #return {"message": "Login satisfactorio", "email": user.email, "id": user.id, "username": user.username}
    token = create_access_token({"sub": str(user.id)})
    return {
        "message": "Login satisfactorio", 
        "access_token": token,  
        "token_type": "bearer", 
        "email": user.email, 
        "id": user.id, 
        "username": user.username, 
        "role": user.role, 
        "imagen_url": user.profile.imagen_url if user.profile else None
 }

