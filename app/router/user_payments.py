
from fastapi import APIRouter, HTTPException, Request, Query
from typing import Optional
from pydantic import BaseModel

from app.models.user_payment import UserPayment
from app.schemas.user_payment import UserPaymentRead, UserPaymentStatusUpdate

from sqlmodel import select


router = APIRouter(prefix="/userpayments", tags=["userpayments"])

from fastapi import Depends
from sqlmodel import Session, select
from app.db.database import get_session



@router.get("/user_payments", response_model=list[UserPaymentRead])
def list_user_payments(
    user_id: int | None = Query(default=None),
    status: str | None = Query(default=None),
    curso_id: int | None = Query(default=None),
    session: Session = Depends(get_session)
):
    query = select(UserPayment)

    if user_id is not None:
        query = query.where(UserPayment.user_id == user_id)
    if status is not None:
        query = query.where(UserPayment.status == status)
    if curso_id is not None:
        query = query.where(UserPayment.curso_id == curso_id)

    user_payments = session.exec(query).all()
    return user_payments


@router.patch("/{payment_id}/status", response_model=UserPaymentRead)
def update_payment_status(
    payment_id: int,
    update_data: UserPaymentStatusUpdate,
    session: Session = Depends(get_session),
):
    # Buscar el pago
    statement = select(UserPayment).where(UserPayment.id == payment_id)
    payment = session.exec(statement).first()

    if not payment:
        raise HTTPException(status_code=404, detail="Pago no encontrado")

    # Actualizar solo el status
    payment.status = update_data.status
    session.add(payment)
    session.commit()
    session.refresh(payment)

    return payment

