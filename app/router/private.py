from fastapi import APIRouter, Depends
from app.auth.auth import get_current_user
from app.schemas.users import UserRead

router = APIRouter()

@router.get("/me", response_model=UserRead)
def read_current_user(current_user: UserRead = Depends(get_current_user)):
    """
    Endpoint protegido que devuelve la información del usuario autenticado.
    Para acceder, debes incluir el token JWT en el header 'Authorization'
    en el formato 'Bearer <token>'.
    """
    return current_user