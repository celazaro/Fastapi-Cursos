from fastapi import APIRouter, Depends, Form, UploadFile, File, Request, HTTPException, Query 
from sqlmodel import Session, select
from typing import List, Optional  # Import List from typing
from app.db.database import get_session
from app.models.cursos import Curso  # Importar el modelo correspondiente
from app.models.profesores import Profesor  # Importar el modelo correspondiente
from app.models.categorias import Categoria  # Importar el modelo Categorias
from app.models.cursos_categorias import CursoCategoria  # Importar el modelo CursoCategoria

from app.utils.image_curso import save_image_curso, delete_image_curso

from enum import Enum

from app.auth.auth import require_admin

router = APIRouter()

class NivelCursoEnum(str, Enum):
    basico = "Básico"
    intermedio = "Intermedio"
    avanzado = "Avanzado"


# 📌 Crear un curso
from app.schemas.cursos import CursoOut, CategoriaOut, ProfesorOut


@router.post("/", response_model=CursoOut)
async def create_curso(
    titulo: str = Form(...),
    descripcion: str = Form(...),
    duracion: int = Form(...),
    precio: float = Form(...),
    nivel: NivelCursoEnum = Form(...),
    destacado: bool = Form(False),
    profesor_id: int = Form(...),
    categorias_id: List[int] = Form(...),
    imagen: UploadFile = File(None),
    session: Session = Depends(get_session),
    user = Depends(require_admin)
):

    profesor = session.get(Profesor, profesor_id)
    if not profesor:
        raise HTTPException(status_code=404, detail="Profesor no encontrado")

    categorias = []
    for cat_id in categorias_id:
        categoria = session.get(Categoria, cat_id)
        if not categoria:
            raise HTTPException(status_code=404, detail=f"Categoría con ID {cat_id} no existe")
        categorias.append(categoria)
    
    imagen_url = None
    imagen_id = None
    ruta_relativa = None
    
    if imagen and imagen.filename:
        try:
            result = await save_image_curso(imagen)
            imagen_url = result.get("secure_url")
            imagen_id = result.get("public_id")
            if not imagen_url or not imagen_id:
                raise HTTPException(status_code=500, detail="Respuesta inesperada de Cloudinary")
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al guardar imagen: {e}")
    else:
        imagen_url = None
        imagen_id = None

    curso = Curso(
        titulo=titulo,
        descripcion=descripcion,
        duracion=duracion,
        precio=precio,
        nivel=nivel,
        destacado=destacado,
        profesor_id=profesor_id,
        imagen_url=imagen_url,
        imagen_id=imagen_id 
    )
    
    session.add(curso)
    session.flush()  # obtiene curso.id sin cerrar la transacción
    
    # Relacionar el curso con las categorías seleccionadas
    for categoria in categorias:
        curso_categoria = CursoCategoria(curso_id=curso.id, categoria_id=categoria.id)
        session.add(curso_categoria)
    
    session.commit()
    session.refresh(curso)

    # Construir el response enriquecido
    categorias_out = [CategoriaOut(id=c.id, name=c.name) for c in categorias]
    profesor_out = ProfesorOut(id=profesor.id, name=profesor.name, profesion=profesor.profesion,imagen_url=profesor.imagen_url)
    
    # Si tu CursoOut espera 'nivel' como string y no Enum, usa .value
    nivel_out = curso.nivel.value if hasattr(curso.nivel, "value") else curso.nivel

    # Si CursoOut.imagen_url NO es Optional[str], evita None (fallback "")
    imagen_out = curso.imagen_url if curso.imagen_url is not None else None  # o "" si tu schema exige str

    return CursoOut(
        id=curso.id,
        titulo=curso.titulo,
        descripcion=curso.descripcion,
        duracion=curso.duracion,
        precio=curso.precio,
        nivel=nivel_out,
        destacado=curso.destacado,
        imagen_url=imagen_out,
        imagen_id=imagen_id,
        profesor=profesor_out,
        categorias=categorias_out
    )


# 📌 Obtener todos los cursos
@router.get("/", response_model=List[CursoOut])
def listar_cursos(session: Session = Depends(get_session)):
    cursos = session.exec(select(Curso)).all()
    cursos_out = []
    for curso in cursos:
        # Obtener profesor
        profesor = session.get(Profesor, curso.profesor_id)
        profesor_out = ProfesorOut(id=profesor.id, name=profesor.name, profesion=profesor.profesion,imagen_url=profesor.imagen_url) if profesor else None
        # Obtener categorías
        categorias = (
            session.exec(
                select(Categoria)
                .join(CursoCategoria, Categoria.id == CursoCategoria.categoria_id)
                .where(CursoCategoria.curso_id == curso.id)
            ).all()
        )
        categorias_out = [CategoriaOut(id=c.id, name=c.name) for c in categorias]
        cursos_out.append(
            CursoOut(
                id=curso.id,
                titulo=curso.titulo,
                descripcion=curso.descripcion,
                duracion=curso.duracion,
                precio=curso.precio,
                nivel=curso.nivel,
                destacado=curso.destacado,
                imagen_url=getattr(curso, 'imagen_url', None),
                profesor=profesor_out,
                categorias=categorias_out
            )
        )
        
    return cursos_out

# 📌 Obtener cursos destacados
@router.get("/destacados", response_model=List[CursoOut])
def cursos_destacados(session: Session = Depends(get_session)):
    cursos = session.exec(select(Curso).where(Curso.destacado == True)).all()
    cursos_out = []
    for curso in cursos:
        profesor = session.get(Profesor, curso.profesor_id)
        profesor_out = ProfesorOut(id=profesor.id, name=profesor.name, profesion=profesor.profesion, imagen_url=profesor.imagen_url) if profesor else None
        categorias = (
            session.exec(
                select(Categoria)
                .join(CursoCategoria, Categoria.id == CursoCategoria.categoria_id)
                .where(CursoCategoria.curso_id == curso.id)
            ).all()
        )
        categorias_out = [CategoriaOut(id=c.id, name=c.name) for c in categorias]
        cursos_out.append(
            CursoOut(
                id=curso.id,
                titulo=curso.titulo,
                descripcion=curso.descripcion,
                duracion=curso.duracion,
                precio=curso.precio,
                nivel=curso.nivel,
                destacado=curso.destacado,
                imagen_url=getattr(curso, 'imagen_url', None),
                profesor=profesor_out,
                categorias=categorias_out
            )
        )
    return cursos_out


# 📌 Obtener curso por ID
@router.get("/{curso_id}", response_model=CursoOut)
def obtener_curso(curso_id: int, session: Session = Depends(get_session)):
    curso = session.get(Curso, curso_id)
    if not curso:
        raise HTTPException(status_code=404, detail="Curso no encontrado")
    profesor = session.get(Profesor, curso.profesor_id)
    profesor_out = ProfesorOut(id=profesor.id, name=profesor.name, profesion=profesor.profesion, imagen_url=profesor.imagen_url) if profesor else None
    categorias = (
        session.exec(
            select(Categoria)
            .join(CursoCategoria, Categoria.id == CursoCategoria.categoria_id)
            .where(CursoCategoria.curso_id == curso.id)
        ).all()
    )
    categorias_out = [CategoriaOut(id=c.id, name=c.name) for c in categorias]
    return CursoOut(
        id=curso.id,
        titulo=curso.titulo,
        descripcion=curso.descripcion,
        duracion=curso.duracion,
        precio=curso.precio,
        nivel=curso.nivel,
        destacado=curso.destacado,
        imagen_url=getattr(curso, 'imagen_url', None),
        profesor=profesor_out,
        categorias=categorias_out
    )

# 📌 Obtener cursos por profesor
@router.get("/profesor/{profesor_id}", response_model=List[CursoOut])
def cursos_por_profesor(profesor_id: int, session: Session = Depends(get_session)):
    cursos = session.exec(select(Curso).where(Curso.profesor_id == profesor_id)).all()
    profesor = session.get(Profesor, profesor_id)
    profesor_out = ProfesorOut(id=profesor.id, name=profesor.name) if profesor else None
    cursos_out = []
    for curso in cursos:
        categorias = (
            session.exec(
                select(Categoria)
                .join(CursoCategoria, Categoria.id == CursoCategoria.categoria_id)
                .where(CursoCategoria.curso_id == curso.id)
            ).all()
        )
        categorias_out = [CategoriaOut(id=c.id, name=c.name) for c in categorias]
        cursos_out.append(
            CursoOut(
                id=curso.id,
                titulo=curso.titulo,
                descripcion=curso.descripcion,
                duracion=curso.duracion,
                precio=curso.precio,
                nivel=curso.nivel,
                destacado=curso.destacado,
                imagen_url=getattr(curso, 'imagen_url', None),
                profesor=profesor_out,
                categorias=categorias_out
            )
        )
    return cursos_out


# 📌 Obtener cursos por categoría
@router.get("/categoria/{categoria_id}", response_model=List[CursoOut])
def cursos_por_categoria(categoria_id: int, session: Session = Depends(get_session)):
    stmt = (
        select(Curso)
        .join(CursoCategoria)
        .where(CursoCategoria.categoria_id == categoria_id)
    )
    cursos = session.exec(stmt).all()
    cursos_out = []
    for curso in cursos:
        profesor = session.get(Profesor, curso.profesor_id)
        profesor_out = ProfesorOut(id=profesor.id, name=profesor.name) if profesor else None
        categorias = (
            session.exec(
                select(Categoria)
                .join(CursoCategoria, Categoria.id == CursoCategoria.categoria_id)
                .where(CursoCategoria.curso_id == curso.id)
            ).all()
        )
        categorias_out = [CategoriaOut(id=c.id, name=c.name) for c in categorias]
        cursos_out.append(
            CursoOut(
                id=curso.id,
                titulo=curso.titulo,
                descripcion=curso.descripcion,
                duracion=curso.duracion,
                precio=curso.precio,
                nivel=curso.nivel,
                destacado=curso.destacado,
                imagen_url=getattr(curso, 'imagen_url', None),
                profesor=profesor_out,
                categorias=categorias_out
            )
        )
    return cursos_out

# 📌 Actualizar un curso
@router.patch("/{curso_id}", response_model=CursoOut)
async def actualizar_curso(
    curso_id: int,
    titulo: Optional[str] = Form(None),
    descripcion: Optional[str] = Form(None),
    duracion: Optional[int] = Form(None),
    precio: Optional[float] = Form(None),
    nivel: Optional[NivelCursoEnum] = Form(None),
    destacado: Optional[bool] = Form(None),
    profesor_id: Optional[int] = Form(None),
    categorias_id: Optional[List[int]] = Form(None),
    imagen: Optional[UploadFile] = File(None),
    session: Session = Depends(get_session),
    user = Depends(require_admin)
):
    curso = session.get(Curso, curso_id)
    if not curso:
        raise HTTPException(status_code=404, detail="Curso no encontrado")

    # Actualizar campos básicos si se envían
    if titulo is not None and titulo != "string":
        curso.titulo = titulo
    if descripcion is not None and descripcion != "string":
        curso.descripcion = descripcion
    if duracion is not None and duracion != 0:
        curso.duracion = duracion
    if precio is not None and precio != 0:
        curso.precio = precio
    if nivel is not None:
        curso.nivel = nivel
    if destacado is not None:
        curso.destacado = destacado

    # Actualizar profesor si se envía
    if profesor_id is not None and profesor_id != 0:
        profesor = session.get(Profesor, profesor_id)
        if not profesor:
            raise HTTPException(status_code=404, detail="Profesor no encontrado")
        curso.profesor_id = profesor_id
    else:
        profesor = session.get(Profesor, curso.profesor_id)

    # Actualizar imagen si se envía
    if imagen and imagen.filename:
        try:
            # Eliminar la imagen anterior si existe
            if curso.imagen_id:
                delete_image_curso(curso.imagen_id)
            # Guardar la nueva imagen
            result = await save_image_curso(imagen)
            curso.imagen_url = result["secure_url"]
            curso.imagen_id = result["public_id"]
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Error al guardar imagen: {e}")

     # 5) Actualizo categorías manualmente
    if categorias_id is not None:
        # a) Filtrar IDs válidas
        valid_ids = [int(cid) for cid in categorias_id if str(cid).isdigit() and int(cid) > 0]

        # b) Eliminar todas las relaciones previas de este curso
        session.query(CursoCategoria).filter(CursoCategoria.curso_id == curso.id).delete()
        session.commit()

        # c) Insertar nuevas relaciones
        for cid in valid_ids:
            # (opcional) comprobar existencia de cada categoría
            if not session.get(Categoria, cid):
                raise HTTPException(status_code=404, detail=f"Categoría con ID {cid} no existe")
            session.add(CursoCategoria(curso_id=curso.id, categoria_id=cid))
        session.commit()

    # 6) Persisto curso y refresco
    session.add(curso)
    session.commit()
    session.refresh(curso)

    # 7) Vuelvo a leer las categorías para el output
    categorias = session.exec(
        select(Categoria)
        .join(CursoCategoria, Categoria.id == CursoCategoria.categoria_id)
        .where(CursoCategoria.curso_id == curso.id)
    ).all()

    # 8) Construyo los schemas de salida
    profesor_img = getattr(profesor, "imagen_url", None)
    profesor_out = ProfesorOut(
        id=profesor.id,
        name=profesor.name,
        profesion=profesor.profesion,
        imagen_url=profesor_img
    )


    categorias_out = [CategoriaOut(id=c.id, name=c.name) for c in categorias]

    curso_out = CursoOut(
        id=curso.id,
        titulo=curso.titulo,
        descripcion=curso.descripcion,
        duracion=curso.duracion,
        precio=curso.precio,
        nivel=curso.nivel,
        destacado=curso.destacado,
        imagen_url=getattr(curso, 'imagen_url', None),
        profesor=profesor_out,
        categorias=categorias_out
    )
    return curso_out



# 📌 Eliminar un curso
@router.delete("/{curso_id}")
def eliminar_curso(
    curso_id: int, 
    session: Session = Depends(get_session),
    user = Depends(require_admin)
    ):
    curso = session.get(Curso, curso_id)
    if not curso:
        raise HTTPException(status_code=404, detail="Curso no encontrado")
    
    # Eliminar la imagen anterior si existe
    if curso.imagen_url:
        delete_image_curso(curso.imagen_id)
        
    session.delete(curso)
    session.commit()
    return {"ok": True, "mensaje": "Curso eliminado correctamente"}

