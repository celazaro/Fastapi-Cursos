from pydantic import BaseModel

# Modelo base sin contraseña
class ProfileCreate(BaseModel):

    nombre: str
    apellido: str
    imagen: str
    direccion: str
    departamento: str
    provincia: str
    bio: str
    

