from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List
from app.models.cursos_categorias import CursoCategoria


# 📌 Modelo Curso (Cada cursot tiene un solo profesor y múltiples categorías)


class Curso(SQLModel, table=True):
    __tablename__ = "curso"
    id: int | None = Field(default=None, primary_key=True)
    titulo: str = Field(max_length=100, nullable=False)
    descripcion: str = Field(max_length=500, nullable=False)
    duracion: int = Field(default=0, nullable=False)  # Duración en minutos
    precio: float = Field(default=0.0, nullable=False)  # Precio del curso
    imagen_url: Optional[str] = Field(default=None, nullable=True)  # URL de la imagen del curso
    nivel: str = Field(default="Básico", nullable=False)  # Nivel del curso
    destacado: bool = Field(default=False, nullable=False)  # Indica si el curso es destacado
    
    profesor_id: int = Field(foreign_key="profesor.id")  # Clave foránea a Profesor

    # Identificador interno (public_id) en Cloudinary
    imagen_id: Optional[str] = None
    
     # Relación  con Profesores y Categorías
    profesor: Optional["Profesor"] = Relationship(back_populates="curso")
    categoria: List["Categoria"] = Relationship(back_populates="curso", link_model=CursoCategoria)
    
    payments: List["UserPayment"] = Relationship(back_populates="curso")