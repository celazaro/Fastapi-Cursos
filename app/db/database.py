from sqlmodel import SQLModel, create_engine, Session 
from app.models.users import User
from app.models.profiles import Profile

from app.models.profesores import Profesor  
from app.models.cursos import Curso      
from app.models.categorias import Categoria 
from app.models.cursos_categorias import CursoCategoria

# ⚠️ Importa la instancia de configuración segura
from app.config import settings 

# Convertimos el Dsn (Data Source Name) a string para usarlo con create_engine
# Aunque SQLModel/SQLAlchemy generalmente aceptan el Dsn directamente, 
# la conversión explícita a str es a veces necesaria.

database_url = str(settings.DATABASE_URL) 

# Crear el engine
engine = create_engine(database_url, echo=True)


def create_db_and_tables():
    SQLModel.metadata.create_all(engine)


# Dependencia para obtener la sesión
def get_session():
    with Session(engine) as session:
        yield session