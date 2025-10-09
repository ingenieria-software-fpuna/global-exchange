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
    billetera = "billetera"
    transferencia = "transferencia"

class EstadoPago(str, Enum):
    exito = "exito"
    fallo = "fallo"
    pendiente = "pendiente"

def get_db_connection():
    return psycopg2.connect(**DATABASE_CONFIG)

def init_database():
    """Crear tabla si no existe"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
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

class PagoResponse(BaseModel):
    id_pago: str
    estado: EstadoPago
    fecha: datetime

def notificar_webhook(url: str, data: dict):
    try:
        timeout = int(os.getenv("WEBHOOK_TIMEOUT", "5"))
        httpx.post(url, json=data, timeout=timeout)
    except Exception:
        pass

@app.post("/pago", response_model=PagoResponse, summary="Iniciar pago", tags=["Pagos"])
def iniciar_pago(pago: PagoRequest, background_tasks: BackgroundTasks):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    id_pago = str(uuid4())
    fecha_actual = datetime.utcnow()
    
    insert_query = """
    INSERT INTO pagos (id_pago, monto, metodo, moneda, estado, webhook_url, fecha)
    VALUES (%s, %s, %s, %s, %s, %s, %s)
    """
    
    cursor.execute(insert_query, (
        id_pago,
        pago.monto,
        pago.metodo.value,
        pago.moneda,
        pago.escenario.value,
        pago.webhook_url,
        fecha_actual
    ))
    
    conn.commit()
    cursor.close()
    conn.close()
    
    response = PagoResponse(id_pago=id_pago, estado=pago.escenario, fecha=fecha_actual)
    
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
        fecha=pago['fecha']
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
