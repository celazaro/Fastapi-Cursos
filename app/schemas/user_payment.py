from pydantic import BaseModel
from datetime import datetime
from typing import Optional

class UserPaymentBase(BaseModel):
    user_id: Optional[int] = None
    curso_id: Optional[int] = None
    payment_id: str
    external_reference: Optional[str] = None
    status: str
    amount: float
    payment_method: Optional[str] = None
    merchant_order_id: Optional[str] = None

class UserPaymentCreate(UserPaymentBase):
    pass

class UserPaymentRead(UserPaymentBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
        

class UserPaymentStatusUpdate(BaseModel):
    status: str