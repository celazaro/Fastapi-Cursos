from sqlmodel import SQLModel, Field



class CursoCategoria(SQLModel, table=True):
    curso_id: int = Field(foreign_key="curso.id", primary_key=True)
    categoria_id: int = Field(foreign_key="categoria.id", primary_key=True)