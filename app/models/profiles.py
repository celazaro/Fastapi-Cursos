from sqlmodel import SQLModel, Field, Relationship
from typing import Optional


class ProfileBase(SQLModel):
    id: Optional[int] = Field(default=None, primary_key=True)
    nombre: Optional[str] = Field(default=None)
    apellido: Optional[str] = Field(default=None)
    imagen_url: Optional[str] = Field(default=None) # solo se guarda la url de la imagen
    direccion: Optional[str] = Field(default=None)
    departamento: Optional[str] = Field(default=None)
    provincia: Optional[str] = Field(default=None)
    bio: Optional[str] = Field(default=None)
    is_active: bool = Field(default=True)


class Profile(ProfileBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    user_id: int = Field(default=None, foreign_key="user.id")

    # No es necsaria la importación de User
    user: Optional["User"] = Relationship(back_populates="profile")