# app/core/security.py

# Se deben instalar las dependencias necesarias:
# pip install passlib[bcrypt]

from passlib.context import CryptContext

# bcrypt es el algoritmo que usaremos (seguro y probado)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)