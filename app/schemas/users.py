from pydantic import BaseModel, EmailStr, Field
from typing import Optional



# Modelo base sin contraseña
class UserBase(BaseModel):
    username: str
    email: EmailStr
    role: Optional[str] = Field(default="user")


# Modelo para creación (sin ID)
class UserCreate(UserBase):
    password: str

# Modelo para respuesta en listados (con ID, sin contraseña)
class UserRead(UserBase):
    id: int

class ChangePassword(BaseModel):
    current_password: str
    new_password: str
