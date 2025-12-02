from sqlmodel import SQLModel, Field, Relationship
from typing import List, Optional


# 📌 Modelo Profesor (Un profesor tiene muchos cursos)

class Profesor(SQLModel, table=True):
    __tablename__ = "profesor"
    id: int = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    profesion: str = Field(max_length=100, nullable=False)
    imagen_url: Optional[str] = Field(default=None, nullable=True)  # URL de la imagen del profesor

    # Identificador interno (public_id) en Cloudinary
    imagen_id: Optional[str] = None
    
    # Relación con Curso 
    curso: List["Curso"] = Relationship(back_populates="profesor"
)
