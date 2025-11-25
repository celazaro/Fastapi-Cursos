from sqlmodel import SQLModel, Field, Relationship
from typing import Optional
from datetime import datetime

class UserPayment(SQLModel, table=True):
    __tablename__ = "user_payments"

    id: Optional[int] = Field(default=None, primary_key=True)

    # Relación con el usuario (nullable para permitir pagos sin metadata)
    user_id: Optional[int] = Field(default=None, foreign_key="user.id", index=True)

    # Relación con el curso (nullable para permitir pagos sin metadata)
    curso_id: Optional[int] = Field(default=None, foreign_key="curso.id", index=True)

    # Datos del pago de Mercado Pago
    payment_id: str = Field(index=True, nullable=False, sa_column_kwargs={"unique": True})
    external_reference: Optional[str] = Field(default=None, index=True, nullable=True)

    status: str = Field(nullable=False)                      # Ej: "approved", "pending", "rejected"
    amount: float = Field(nullable=False)                    # Monto del pago
    payment_method: Optional[str] = Field(default=None)      # Tarjeta, débito, etc.
    merchant_order_id: Optional[str] = Field(default=None, index=True)
    raw_payload: Optional[str] = Field(default=None)         # JSON completo/serializado para auditoría

    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    # Relaciones inversas
    user: Optional["User"] = Relationship(back_populates="payments")
    curso: Optional["Curso"] = Relationship(back_populates="payments")