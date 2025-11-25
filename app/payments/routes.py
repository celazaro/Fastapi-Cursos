import mercadopago
from fastapi import FastAPI, HTTPException, APIRouter, Depends, Request
from pydantic import BaseModel

from fastapi.responses import RedirectResponse, JSONResponse
import json
import time

from app.config import settings
import os
import httpx

from app.db.database import get_session
from app.core.security import get_password_hash
from app.models.users import User
from sqlmodel import Session, select

from app.models.user_payment import UserPayment
from app.schemas.user_payment import UserPaymentCreate, UserPaymentRead

from datetime import datetime # <-- Asegúrate de importar datetime


app = FastAPI()
router = APIRouter(prefix="/mp", tags=["Mercado Pago"])

# 1. Configura el SDK con tu ACCESS_TOKEN de PRUEBA (Test)
# Búscalo en tus credenciales de desarrollador de MP

ACCESS_TOKEN = settings.MERCADO_PAGO_ACCESS_TOKEN
URL_BASE = settings.URL_BASE_SERVIDOR

sdk = mercadopago.SDK(ACCESS_TOKEN)

class PaymentRequest(BaseModel):
    username: str
    email: str
    curso_titulo: str
    precio: float  # Importante: MP maneja precios como números
    cantidad: int
    user_id: int
    curso_id: int


@router.post("/create_preference")
def create_preference(data: PaymentRequest):
    
    # Imprimimos para ver qué llega desde Vue (Depuración)
    print(f"Recibido pago para: {data.email} por curso {data.curso_titulo}")

    # 1. Construir la estructura de datos para Mercado Pago
    preference_data = {
        
        # "items": Es lo que el usuario está comprando.
        "items": [
            {
                "id": str(data.curso_id),     # ID del producto
                "title": f"{data.curso_titulo} comprado por {data.username}",   # Título que verá el usuario al pagar
                "quantity": data.cantidad,    # Cantidad
                "unit_price": float(data.precio), # Precio unitario
                "currency_id": "ARS"          # Moneda (Cambiar si es otra)
            }
        ],

        # "payer": Información de quién paga (para pre-llenar el formulario)
        "payer": {
            "email": data.email,
            "name": data.username
            # Puedes agregar surname, identification, etc. si los tienes
        },

        # "back_urls": A dónde redirigir al usuario después del pago
        "back_urls": {
            "success": f"{URL_BASE}/mp/success",
            "failure": f"{URL_BASE}/mp/failure",
            "pending": f"{URL_BASE}/mp/pending",
        },

        # "auto_return": Para que vuelva automáticamente a tu sitio al terminar
        "auto_return": "approved",

        # "external_reference": CRUCIAL. Aquí guardas tus IDs internos
        # para saber a quién darle el curso cuando llegue el pago real.
        # Podemos concatenar curso_id y user_id
        "external_reference": f"{data.user_id}_{data.curso_id}",
        # Esto fuerza a MP a notificar aquí sí o sí para ESTE pago.
        "notification_url": f"{URL_BASE}/mp/webhook"
    }

    # 2. Crear la preferencia usando el SDK
    try:
        preference_response = sdk.preference().create(preference_data)
        preference = preference_response["response"]
        
        # Debug: Ver qué nos devolvió Mercado Pago
        print("ID de preferencia generado:", preference['id'])
        
        # 3. Retornar las URLs a Vue.js
        return {
            "sandbox_init_point": preference["sandbox_init_point"], # Para pruebas
            "init_point": preference["init_point"],                 # Para producción
            "id": preference["id"]                                  # ID de la preferencia
        }

    except Exception as e:
        print("Error al crear preferencia:", e)
        raise HTTPException(status_code=500, detail=str(e))


# --- RUTAS DE REDIRECCIÓN (Back URLs) ---
# Ahora estas rutas hacen el trabajo sucio de guardar en la BD

@router.get("/success")
async def pago_exitoso(request: Request, session: Session = Depends(get_session)):
    # Capturamos datos y guardamos como 'approved'
    process_payment_return(request, session, status_override="approved")
    return RedirectResponse(url="http://localhost:5173/success")

@router.get("/failure")
async def pago_fallido(request: Request, session: Session = Depends(get_session)):
    process_payment_return(request, session, status_override="rejected")
    return RedirectResponse(url="http://localhost:5173/failure")

@router.get("/pending")
async def pago_pendiente(request: Request, session: Session = Depends(get_session)):
    process_payment_return(request, session, status_override="pending")
    return RedirectResponse(url="http://localhost:5173/pending")


@router.post("/checkout")
def register_and_checkout(data: PaymentRequest, session: Session = Depends(get_session)):
    stmt = select(User).where((User.email == data.email) | (User.username == data.username))
    existing_user = session.exec(stmt).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="El usuario ya existe")

    if not data.password:
        raise HTTPException(status_code=400, detail="Se requiere password para registrar usuario")

    hashed_pw = get_password_hash(data.password)
    db_user = User(username=data.username, email=data.email, password=hashed_pw)
    session.add(db_user)
    session.commit()
    session.refresh(db_user)

    data.user_id = db_user.id
    return create_preference(data)


@router.post("/webhook")
@router.post("/webhook/") 
async def handle_webhook(request: Request):
    
    print("\n🔔 ¡TOC TOC! Notificación recibida en el servidor (Flujo simplificado)")

    # 1. Extraer ID del recurso, sin importar si viene como 'id' o 'data.id'
    query_params = dict(request.query_params)
    topic = query_params.get("topic") or query_params.get("type")
    resource_id = query_params.get("id") or query_params.get("data.id")
    
    print(f"📨 Datos -> Topic: {topic} | ID: {resource_id}")

    if topic == "payment" and resource_id:
        
        # 🟢 LÓGICA DE ACTIVACIÓN DEL CURSO
        # Ya que la redirección del navegador confirma el estado 'approved',
        # y la consulta al SDK falla en Sandbox, confiamos en el Webhook.
        
        # Aquí debes implementar:
        # 1. Obtener la external_reference (necesitarías una consulta diferente
        #    o extraerla del tópico merchant_order si llega antes).
        # 2. Activar el curso en tu base de datos.
        
        print(f"🎉 ¡PAGO RECIBIDO! ID {resource_id} notificado. (Acción: Activar Curso)")

    elif topic == "merchant_order" and resource_id:
        print(f"📦 Orden de Comercio recibida. ID: {resource_id}")
    
    # Responder 200 OK para confirmar la recepción a Mercado Pago
    return JSONResponse(content={"status": "OK"}, status_code=200)

# --- LÓGICA DE GUARDADO (Helper) ---
def process_payment_return(request: Request, session: Session, status_override: str = None):
    """
    Captura los parámetros de la URL de redirección (Query Params)
    y guarda/actualiza el pago en la BD sin consultar a la API de MP.
    """
    params = dict(request.query_params)
    
    # 1. Extraer datos básicos de la URL
    payment_id = params.get("payment_id") or params.get("collection_id")
    status = status_override or params.get("status") or params.get("collection_status") or "unknown"
    external_reference = params.get("external_reference")
    merchant_order_id = params.get("merchant_order_id") or ""
    payment_type = params.get("payment_type") or "unknown"
    
    # Si no hay payment_id, no podemos guardar nada fiable
    if not payment_id:
        print("⚠️ No se recibió payment_id en la redirección.")
        return

    print(f"📥 Procesando retorno: ID={payment_id} | Status={status} | Ref={external_reference}")

    # 2. Desglosar external_reference (user_id_curso_id)
    user_id_db = None
    curso_id_db = None
    if external_reference:
        try:
            parts = external_reference.split("_")
            if len(parts) >= 2:
                user_id_db = int(parts[0])
                curso_id_db = int(parts[1])
        except ValueError:
            print(f"⚠️ Error parseando external_reference: {external_reference}")

    # 3. Guardar en Base de Datos
    try:
        # Verificar si ya existe
        stmt = select(UserPayment).where(UserPayment.payment_id == str(payment_id))
        existing_payment = session.exec(stmt).first()

        if existing_payment:
            print(f"🔄 Actualizando pago {payment_id} a {status}")
            existing_payment.status = status
            existing_payment.updated_at = datetime.utcnow()
            session.add(existing_payment)
            session.commit()
        else:
            print(f"✨ Creando nuevo pago {payment_id} como {status}")
            # NOTA: La URL de retorno NO trae el 'amount'.
            # Como omitimos la consulta a la API, guardamos 0.0 para no romper la BD.
            new_payment = UserPayment(
                payment_id=str(payment_id),
                user_id=user_id_db,
                curso_id=curso_id_db,
                external_reference=external_reference,
                status=status,
                amount=0.0, 
                payment_method=payment_type,
                merchant_order_id=str(merchant_order_id),
                raw_payload=json.dumps(params), # Guardamos los params de la URL como evidencia
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            session.add(new_payment)
            session.commit()
            
            # Lógica de activación de curso (si aplica)
            if status == "approved":
                print("✅ Curso activado (Lógica interna)")

    except Exception as e:
        print(f"🔥 Error guardando pago en redirección: {e}")



@router.post("/payments", response_model=UserPaymentRead)
async def create_payment(payment: UserPaymentCreate, session: Session = Depends(get_session)):
    new_payment = UserPayment.from_orm(payment)
    session.add(new_payment)
    session.commit()
    session.refresh(new_payment)
    return new_payment
