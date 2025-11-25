# schemas/curso.py

from pydantic import BaseModel
from typing import List, Optional

class CategoriaOut(BaseModel):
    id: int
    name: str

    class Config:
        orm_mode = True

class ProfesorOut(BaseModel):
    id: int
    name: str
    profesion: str
    imagen_url: Optional[str] = None

    class Config:
        orm_mode = True

class CursoOut(BaseModel):
    id: int
    titulo: str
    descripcion: str
    duracion: int
    precio: float
    nivel: str
    destacado: bool
    imagen_url: Optional[str] = None
    profesor: ProfesorOut
    categorias: List[CategoriaOut]

    class Config:
        from_attributes = True
        

