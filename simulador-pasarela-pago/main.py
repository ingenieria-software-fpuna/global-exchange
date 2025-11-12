from fastapi import FastAPI, HTTPException, Request, Form, BackgroundTasks
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from enum import Enum
from uuid import uuid4
from typing import Optional
from datetime import datetime
import httpx
import os
import psycopg2
from psycopg2.extras import RealDictCursor
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

app = FastAPI(title="Simulador Pasarela de Pago", description="API para simular una pasarela de pago con métodos múltiples, webhooks y logs.")
templates = Jinja2Templates(directory="templates")

# Database setup 
DATABASE_CONFIG = {
    'host': os.getenv("DB_HOST", "localhost"),
    'port': int(os.getenv("DB_PORT", "5433")),
    'database': os.getenv("DB_NAME", "simulador_pagos"),
    'user': os.getenv("DB_USER", "simulador"),
    'password': os.getenv("DB_PASSWORD", "simulador123")
}

class MetodoPago(str, Enum):
    tarjeta = "tarjeta"
    tarjeta_credito_local = "tarjeta_credito_local"
    billetera = "billetera"
    transferencia = "transferencia"

class EstadoPago(str, Enum):
    exito = "exito"
    fallo = "fallo"
    pendiente = "pendiente"

def get_db_connection():
    return psycopg2.connect(**DATABASE_CONFIG)

def init_database():
    """Crear tabla si no existe y agregar columnas nuevas"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Crear tabla básica si no existe
    create_table_query = """
    CREATE TABLE IF NOT EXISTS pagos (
        id_pago VARCHAR(255) PRIMARY KEY,
        monto DECIMAL(10,2),
        metodo VARCHAR(50),
        moneda VARCHAR(10),
        estado VARCHAR(50),
        webhook_url VARCHAR(500),
        fecha TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """
    cursor.execute(create_table_query)
    
    # Agregar nuevas columnas si no existen
    new_columns = [
        "ALTER TABLE pagos ADD COLUMN IF NOT EXISTS numero_tarjeta VARCHAR(20);",
        "ALTER TABLE pagos ADD COLUMN IF NOT EXISTS numero_billetera VARCHAR(20);",
        "ALTER TABLE pagos ADD COLUMN IF NOT EXISTS numero_comprobante VARCHAR(50);",
        "ALTER TABLE pagos ADD COLUMN IF NOT EXISTS motivo_rechazo VARCHAR(200);",
        "ALTER TABLE pagos ADD COLUMN IF NOT EXISTS id_transaccion VARCHAR(255);"
    ]
    
    for query in new_columns:
        try:
            cursor.execute(query)
        except Exception as e:
            print(f"Error agregando columna: {e}")
    
    conn.commit()
    cursor.close()
    conn.close()

# Inicializar la base de datos al arrancar
init_database()

class PagoRequest(BaseModel):
    monto: float
    metodo: MetodoPago
    moneda: str
    escenario: EstadoPago = EstadoPago.exito
    webhook_url: Optional[str] = None
    id_transaccion: Optional[str] = None  # ID de la transacción desde el sistema principal
    # Campos específicos por método de pago
    numero_tarjeta: Optional[str] = None  # Para tarjeta y tarjeta_credito_local
    numero_billetera: Optional[str] = None  # Para billetera
    numero_comprobante: Optional[str] = None  # Para transferencia

class PagoResponse(BaseModel):
    id_pago: str
    estado: EstadoPago
    fecha: datetime
    motivo_rechazo: Optional[str] = None

def es_primo(n):
    """Verifica si un número es primo"""
    if n < 2:
        return False
    for i in range(2, int(n**0.5) + 1):
        if n % i == 0:
            return False
    return True

def validar_pago(pago: PagoRequest):
    """Valida el pago según las reglas de negocio y retorna estado y motivo"""
    
    # Si el escenario ya está definido como fallo, respetarlo
    if pago.escenario == EstadoPago.fallo:
        return EstadoPago.fallo, "Error simulado por configuración"
    
    motivo_rechazo = None
    estado_final = pago.escenario
    
    if pago.metodo in [MetodoPago.tarjeta, MetodoPago.tarjeta_credito_local]:
        if not pago.numero_tarjeta:
            return EstadoPago.fallo, "Número de tarjeta requerido"
        
        # Verificar si los últimos 2 dígitos son primos
        try:
            ultimos_digitos = int(pago.numero_tarjeta[-2:])
            if es_primo(ultimos_digitos):
                if pago.metodo == MetodoPago.tarjeta:
                    return EstadoPago.fallo, f"Transacción declinada: fondos insuficientes en la cuenta asociada"
                else:  # tarjeta_credito_local
                    return EstadoPago.fallo, f"Tarjeta bloqueada: límite de crédito excedido, contacte a su banco"
        except (ValueError, IndexError):
            return EstadoPago.fallo, "Número de tarjeta inválido"
    
    elif pago.metodo == MetodoPago.billetera:
        if not pago.numero_billetera:
            return EstadoPago.fallo, "Número de billetera requerido"
            
        # Verificar si los últimos 2 dígitos son primos
        try:
            ultimos_digitos = int(pago.numero_billetera[-2:])
            if es_primo(ultimos_digitos):
                return EstadoPago.fallo, f"Billetera rechazada: cuenta suspendida temporalmente"
        except (ValueError, IndexError):
            return EstadoPago.fallo, "Número de billetera inválido"
    
    elif pago.metodo == MetodoPago.transferencia:
        if not pago.numero_comprobante:
            return EstadoPago.fallo, "Número de comprobante requerido"
            
        # Rechazar si el comprobante contiene "000" (simulando problema bancario)
        if "000" in pago.numero_comprobante:
            return EstadoPago.fallo, "Transferencia rechazada: operación no autorizada por el banco origen"
        
        # Rechazar si tiene menos de 6 caracteres
        if len(pago.numero_comprobante) < 6:
            return EstadoPago.fallo, "Transferencia rechazada: número de comprobante inválido o incompleto"
    
    return estado_final, motivo_rechazo

def notificar_webhook(url: str, data: dict):
    try:
        timeout = int(os.getenv("WEBHOOK_TIMEOUT", "5"))
        httpx.post(url, json=data, timeout=timeout)
    except Exception:
        pass

@app.post("/pago", response_model=PagoResponse, summary="Iniciar pago", tags=["Pagos"])
def iniciar_pago(pago: PagoRequest, background_tasks: BackgroundTasks):
    # Validar el pago según las reglas de negocio
    estado_final, motivo_rechazo = validar_pago(pago)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    id_pago = str(uuid4())
    fecha_actual = datetime.utcnow()
    
    insert_query = """
    INSERT INTO pagos (id_pago, monto, metodo, moneda, estado, webhook_url, 
                      numero_tarjeta, numero_billetera, numero_comprobante, motivo_rechazo, id_transaccion, fecha)
    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
    """
    
    cursor.execute(insert_query, (
        id_pago,
        pago.monto,
        pago.metodo.value,
        pago.moneda,
        estado_final.value,
        pago.webhook_url,
        pago.numero_tarjeta,
        pago.numero_billetera,
        pago.numero_comprobante,
        motivo_rechazo,
        pago.id_transaccion,
        fecha_actual
    ))
    
    conn.commit()
    cursor.close()
    conn.close()
    
    response = PagoResponse(
        id_pago=id_pago, 
        estado=estado_final, 
        fecha=fecha_actual,
        motivo_rechazo=motivo_rechazo
    )
    
    # Notificar webhook si corresponde
    if pago.webhook_url:
        background_tasks.add_task(notificar_webhook, pago.webhook_url, response.dict())
    
    return response

@app.get("/pago/{id_pago}", response_model=PagoResponse, summary="Consultar estado de pago", tags=["Pagos"])
def consultar_pago(id_pago: str):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    select_query = "SELECT * FROM pagos WHERE id_pago = %s"
    cursor.execute(select_query, (id_pago,))
    pago = cursor.fetchone()
    
    cursor.close()
    conn.close()
    
    if not pago:
        raise HTTPException(status_code=404, detail="Pago no encontrado")
    
    return PagoResponse(
        id_pago=pago['id_pago'], 
        estado=EstadoPago(pago['estado']), 
        fecha=pago['fecha'],
        motivo_rechazo=pago['motivo_rechazo']
    )

@app.get("/pago/transaccion/{id_transaccion}", response_model=PagoResponse, summary="Consultar pago por ID de transacción", tags=["Pagos"])
def consultar_pago_por_transaccion(id_transaccion: str):
    """Consultar el estado de un pago usando el ID de transacción del sistema principal"""
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    select_query = "SELECT * FROM pagos WHERE id_transaccion = %s ORDER BY fecha DESC LIMIT 1"
    cursor.execute(select_query, (id_transaccion,))
    pago = cursor.fetchone()
    
    cursor.close()
    conn.close()
    
    if not pago:
        raise HTTPException(status_code=404, detail="Pago no encontrado para esta transacción")
    
    return PagoResponse(
        id_pago=pago['id_pago'], 
        estado=EstadoPago(pago['estado']), 
        fecha=pago['fecha'],
        motivo_rechazo=pago['motivo_rechazo']
    )

# Admin interface
@app.get("/admin", response_class=HTMLResponse, summary="Panel de administración", tags=["Admin"])
def admin_panel(request: Request):
    conn = get_db_connection()
    cursor = conn.cursor(cursor_factory=RealDictCursor)
    
    select_query = "SELECT * FROM pagos ORDER BY fecha DESC"
    cursor.execute(select_query)
    pagos = cursor.fetchall()
    
    cursor.close()
    conn.close()
    
    return templates.TemplateResponse("admin.html", {"request": request, "pagos": pagos})

# Webhook test endpoint
@app.post("/webhook-test", summary="Simular recepción de webhook", tags=["Webhooks"])
async def webhook_test(payload: dict):
    return {"received": payload}

# Home
@app.get("/", response_class=HTMLResponse, include_in_schema=False)
def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})
