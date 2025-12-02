from sqlmodel import SQLModel, Field, Relationship
from typing import Optional, List


class User(SQLModel, table=True):

    id: Optional[int] = Field(default=None, primary_key=True)
    username: str = Field(index=True, unique=True, nullable=False)
    email: str = Field(index=True, unique=True, nullable=False)
    password: str = Field(nullable=False)
    role: Optional[str] = Field(default="user")  # valores: "user", "admin", "superadmin"

    # Activamos la relación con Profile
    # No es necesario realizar la importación de Profile
    profile: Optional["Profile"] = Relationship(back_populates="user")
    
    payments: List["UserPayment"] = Relationship(back_populates="user")