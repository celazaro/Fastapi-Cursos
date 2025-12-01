from sqlmodel import SQLModel, Field, Relationship
from typing import List, Optional
from app.models.cursos_categorias import CursoCategoria


class Categoria(SQLModel, table=True):
    id: int = Field(default=None, primary_key=True)
    name: str = Field(index=True)
    descripcion: str = Field(max_length=100, nullable=False)
    
    # URL pública de la imagen en Cloudinary
    imagen_url: Optional[str] = None

    # Identificador interno (public_id) en Cloudinary
    imagen_id: Optional[str] = None
    
    curso: List["Curso"] = Relationship(back_populates="categoria", link_model=CursoCategoria)

