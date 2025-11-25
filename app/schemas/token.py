from sqlmodel import SQLModel
from pydantic import EmailStr

class Token(SQLModel):
    access_token: str
    token_type: str = "bearer"


class LoginData(SQLModel):
    email: EmailStr
    password: str