# API de Integración - Simulador de Pasarela de Pago

## URL Base
```
http://localhost:3001
```

## Endpoints

### 1. Iniciar Pago
```http
POST /pago
Content-Type: application/json

{
  "monto": 100.50,
  "metodo": "tarjeta",
  "moneda": "USD",
  "escenario": "exito",
  "webhook_url": "http://tu-app:8000/webhook-pago"
}
```

**Respuesta:**
```json
{
  "id_pago": "uuid-generado",
  "estado": "exito",
  "fecha": "2025-10-07T10:30:00"
}
```

### 2. Consultar Estado
```http
GET /pago/{id_pago}
```

**Respuesta:**
```json
{
  "id_pago": "uuid-generado",
  "estado": "exito",
  "fecha": "2025-10-07T10:30:00"
}
```

## Métodos de Pago Soportados
- `tarjeta`: Simulación de pago con tarjeta debito
- `billetera`: Simulación de pago en billetera
- `transferencia`: Simulación de transferencia bancaria

## Estados Posibles
- `exito`: Pago exitoso
- `fallo`: Pago fallido
- `pendiente`: Pago en proceso

## Ejemplo de Uso desde Global Exchange

### En tu proyecto Django (puerto 8000):
```python
# views.py
import httpx
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json

def procesar_pago(request):
    # Enviar pago al simulador
    response = httpx.post("http://localhost:3001/pago", json={
        "monto": 100.50,
        "metodo": "tarjeta",
        "moneda": "USD",
        "escenario": "exito",
        "webhook_url": "http://localhost:8000/webhook-pago"
    })
    
    pago = response.json()
    return JsonResponse({"pago_id": pago['id_pago'], "estado": pago['estado']})

@csrf_exempt
def webhook_pago(request):
    """Endpoint para recibir notificaciones del simulador"""
    if request.method == 'POST':
        data = json.loads(request.body)
        # Actualizar tu modelo/BD con el resultado del pago
        print(f"Pago recibido: {data['id_pago']}, Estado: {data['estado']}")
        return JsonResponse({"status": "ok"})
```

### En urls.py:
```python
urlpatterns = [
    path('procesar-pago/', procesar_pago, name='procesar_pago'),
    path('webhook-pago/', webhook_pago, name='webhook_pago'),
]
```

## Webhooks
Si proporcionas una `webhook_url`, el simulador enviará una notificación POST con los datos del pago a esa URL.

## Admin Panel
Accede a `http://localhost:3001/admin` para ver todos los pagos registrados.

## Documentación Interactiva
FastAPI genera documentación automática en `http://localhost:3001/docs`