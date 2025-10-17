Módulo de Pagos
===============

El módulo de pagos gestiona la integración con pasarelas de pago externas para procesar transacciones de la casa de cambio.

Descripción General
-------------------

Este módulo implementa:

- Integración con pasarela de pagos simulada (local)
- Integración con Stripe Checkout para pagos reales
- Registro y trazabilidad de pagos procesados
- Webhooks para notificaciones asíncronas
- Soporte para múltiples métodos de pago
- Manejo robusto de errores y timeouts

Modelo Principal
----------------

PagoPasarela
~~~~~~~~~~~~

Modelo que registra los pagos procesados a través de pasarelas externas.

**Identificación:**

- ``id``: Clave primaria autoincremental
- ``id_pago_externo``: ID único del pago en la pasarela externa (varchar 100, unique)

**Relaciones:**

- ``transaccion``: ForeignKey a Transaccion (CASCADE)

**Información del pago:**

- ``monto``: DecimalField (15,2) - Monto procesado
- ``moneda``: CharField (10) - Código de moneda (USD, PYG, EUR)
- ``metodo_pasarela``: CharField (50) - Método según la pasarela

**Estado:**

- ``estado``: CharField con choices:
  
  - ``'exito'``: Pago completado exitosamente
  - ``'fallo'``: Pago rechazado o fallido
  - ``'pendiente'``: Pago en proceso

**Datos estructurados:**

- ``datos_pago``: JSONField - Datos del pago (default: dict)
- ``respuesta_pasarela``: JSONField - Respuesta completa de la pasarela (default: dict)

**Control temporal:**

- ``fecha_creacion``: DateTimeField (auto_now_add)
- ``fecha_actualizacion``: DateTimeField (auto_now)
- ``fecha_procesamiento``: DateTimeField nullable - Cuándo se procesó en la pasarela

**Errores:**

- ``mensaje_error``: TextField blank - Mensaje de error si el pago falló

**Configuración del modelo:**

- ``verbose_name``: "Pago de Pasarela"
- ``verbose_name_plural``: "Pagos de Pasarela"
- ``ordering``: ['-fecha_creacion']
- ``db_table``: 'pagos_pagopassarela'

**Índices:**

.. code-block:: python

   indexes = [
       models.Index(fields=['id_pago_externo']),
       models.Index(fields=['transaccion', '-fecha_creacion']),
       models.Index(fields=['estado', '-fecha_creacion']),
   ]

Métodos de Instancia
--------------------

**es_exitoso()**

Verifica si el pago fue exitoso.

.. code-block:: python

   pago = PagoPasarela.objects.get(id_pago_externo='PAY-123')
   if pago.es_exitoso():
       print("Pago completado")

**Retorna:**

- ``bool``: True si ``estado == 'exito'``

**es_fallido()**

Verifica si el pago falló.

.. code-block:: python

   if pago.es_fallido():
       print(f"Error: {pago.mensaje_error}")

**Retorna:**

- ``bool``: True si ``estado == 'fallo'``

**es_pendiente()**

Verifica si el pago está pendiente.

.. code-block:: python

   if pago.es_pendiente():
       print("Esperando confirmación de la pasarela")

**Retorna:**

- ``bool``: True si ``estado == 'pendiente'``

Servicios de Integración
-------------------------

PasarelaService
~~~~~~~~~~~~~~~

Servicio para integrar con la API simulada de pasarela de pagos.

**Configuración:**

.. code-block:: python

   class PasarelaService:
       BASE_URL = "http://localhost:3001"
       
       METODO_MAPPING = {
           'billetera electrónica': 'billetera',
           'billetera electronica': 'billetera',
           'tarjeta de débito': 'tarjeta',
           'tarjeta de debito': 'tarjeta',
           'tarjeta de crédito local': 'tarjeta_credito_local',
           'tarjeta de credito local': 'tarjeta_credito_local',
           'transferencia bancaria': 'transferencia',
       }

**Inicialización:**

.. code-block:: python

   pasarela = PasarelaService(timeout=30)  # timeout en segundos

**Métodos principales:**

**procesar_pago()**

Envía una solicitud de pago a la pasarela.

.. code-block:: python

   resultado = pasarela.procesar_pago(
       monto=150000,
       metodo_cobro="Tarjeta de débito",
       moneda="PYG",
       escenario="exito",
       datos_adicionales={
           'numero_tarjeta': '4111111111111111',
           'transaccion_id': 'TXN-20251017120000-ABC123'
       }
   )
   
   if resultado['success']:
       pago_id = resultado['data']['id_pago']
       estado = resultado['data']['estado']
       print(f"Pago creado: {pago_id}, Estado: {estado}")
   else:
       print(f"Error: {resultado['error']}")

**Parámetros:**

- ``monto`` (float): Monto del pago
- ``metodo_cobro`` (str): Método desde Django (se mapea automáticamente)
- ``moneda`` (str): Código de moneda (default: "USD")
- ``escenario`` (str): "exito", "fallo", "pendiente" (default: "exito")
- ``datos_adicionales`` (dict, optional): Datos extra

**Retorna:**

.. code-block:: python

   # Éxito
   {
       'success': True,
       'data': {
           'id_pago': 'PAY-123456',
           'estado': 'exito',
           'mensaje': 'Pago procesado correctamente',
           'fecha_procesamiento': '2025-10-17T12:00:00Z',
           ...
       }
   }
   
   # Error
   {
       'success': False,
       'error': 'Timeout al comunicarse con la pasarela',
       'error_type': 'timeout'
   }

**Tipos de error:**

- ``'timeout'``: Timeout en la comunicación
- ``'http_error'``: Error HTTP de la pasarela
- ``'connection_error'``: Error de conexión
- ``'unexpected_error'``: Error inesperado

**consultar_pago()**

Consulta el estado de un pago en la pasarela.

.. code-block:: python

   resultado = pasarela.consultar_pago('PAY-123456')
   
   if resultado['success']:
       estado_actual = resultado['data']['estado']
       print(f"Estado del pago: {estado_actual}")

**Parámetros:**

- ``id_pago`` (str): ID del pago en la pasarela

**Retorna:**

.. code-block:: python

   # Éxito
   {
       'success': True,
       'data': {
           'id_pago': 'PAY-123456',
           'estado': 'exito',
           'monto': 150000,
           ...
       }
   }
   
   # Pago no encontrado
   {
       'success': False,
       'error': 'Pago no encontrado',
       'error_type': 'not_found'
   }

**esta_disponible()**

Verifica si la pasarela está disponible.

.. code-block:: python

   if pasarela.esta_disponible():
       print("Pasarela operativa")
   else:
       print("Pasarela no disponible")

**Retorna:**

- ``bool``: True si la pasarela responde

**Métodos privados:**

**_mapear_metodo()**

Mapea métodos de cobro de Django al formato de la pasarela.

.. code-block:: python

   metodo_pasarela = pasarela._mapear_metodo("Tarjeta de débito")
   # Retorna: "tarjeta"

StripeService
~~~~~~~~~~~~~

Servicio para integrar con Stripe Checkout.

**Configuración:**

Requiere variables en ``settings.py``:

.. code-block:: python

   STRIPE_SECRET_KEY = 'sk_test_...'
   STRIPE_WEBHOOK_SECRET = 'whsec_...'
   SITE_URL = 'http://localhost:8000'

**Inicialización:**

.. code-block:: python

   stripe_service = StripeService()

**Métodos principales:**

**crear_sesion_checkout()**

Crea una sesión de Stripe Checkout.

.. code-block:: python

   resultado = stripe_service.crear_sesion_checkout(
       monto=150.00,
       moneda='USD',
       transaccion_id='TXN-20251017120000-ABC123',
       descripcion='Compra de USD',
       metadata={
           'cliente_id': '123',
           'tipo_operacion': 'COMPRA'
       }
   )
   
   if resultado['success']:
       # Redirigir al usuario a la URL de Stripe
       checkout_url = resultado['url']
       session_id = resultado['session_id']

**Parámetros:**

- ``monto`` (float): Monto del pago
- ``moneda`` (str): Código de moneda (usd, pyg, eur)
- ``transaccion_id`` (str): ID de transacción en el sistema
- ``descripcion`` (str): Descripción del pago (default: "Compra de moneda")
- ``success_url`` (str, optional): URL de retorno exitoso
- ``cancel_url`` (str, optional): URL de cancelación
- ``metadata`` (dict, optional): Metadatos adicionales

**Retorna:**

.. code-block:: python

   # Éxito
   {
       'success': True,
       'session_id': 'cs_test_...',
       'url': 'https://checkout.stripe.com/c/pay/cs_test_...',
       'payment_intent': 'pi_...'
   }
   
   # Error
   {
       'success': False,
       'error': 'Error de autenticación con Stripe',
       'error_type': 'authentication_error'
   }

**Manejo de monedas:**

- **Zero-decimal currencies** (PYG, JPY, KRW): Usa monto directamente
- **Monedas con decimales** (USD, EUR): Multiplica por 100 (centavos)

.. code-block:: python

   # PYG: 150000 -> 150000 (sin cambios)
   # USD: 150.00 -> 15000 (centavos)

**recuperar_sesion()**

Recupera información de una sesión de checkout.

.. code-block:: python

   resultado = stripe_service.recuperar_sesion('cs_test_...')
   
   if resultado['success']:
       session = resultado['session']
       payment_status = resultado['payment_status']  # 'paid', 'unpaid'
       payment_intent = resultado['payment_intent']

**verificar_webhook()**

Verifica y procesa eventos de webhook de Stripe.

.. code-block:: python

   # En la vista de webhook
   payload = request.body
   sig_header = request.META['HTTP_STRIPE_SIGNATURE']
   
   resultado = stripe_service.verificar_webhook(payload, sig_header)
   
   if resultado['success']:
       event = resultado['event']
       event_type = resultado['type']  # 'checkout.session.completed', etc.

**esta_disponible()**

Verifica si Stripe está configurado correctamente.

.. code-block:: python

   if stripe_service.esta_disponible():
       print("Stripe configurado")

**Retorna:**

- ``bool``: True si API key está configurada y es válida

Formularios
-----------

El módulo incluye formularios especializados para diferentes métodos de pago:

BilleteraElectronicaForm
~~~~~~~~~~~~~~~~~~~~~~~~

Formulario para pagos con billetera electrónica.

**Campos:**

- ``telefono``: CharField - Número de teléfono asociado a la billetera

.. code-block:: python

   form = BilleteraElectronicaForm(request.POST)
   if form.is_valid():
       telefono = form.cleaned_data['telefono']

TarjetaDebitoForm
~~~~~~~~~~~~~~~~~

Formulario para pagos con tarjeta de débito.

**Campos:**

- ``numero_tarjeta``: CharField - Número de tarjeta (enmascarado en vista)
- ``nombre_titular``: CharField - Nombre del titular
- ``fecha_expiracion``: CharField - MM/YY
- ``cvv``: CharField - Código de seguridad

.. code-block:: python

   form = TarjetaDebitoForm(request.POST)
   if form.is_valid():
       numero_tarjeta = form.cleaned_data['numero_tarjeta']
       # Procesar pago...

TarjetaCreditoLocalForm
~~~~~~~~~~~~~~~~~~~~~~~

Formulario para pagos con tarjeta de crédito local.

**Campos:** (similares a TarjetaDebitoForm)

- ``numero_tarjeta``
- ``nombre_titular``
- ``fecha_expiracion``
- ``cvv``

TransferenciaBancariaForm
~~~~~~~~~~~~~~~~~~~~~~~~~

Formulario para pagos con transferencia bancaria.

**Campos:**

- ``numero_comprobante``: CharField - Número de comprobante de transferencia
- ``banco_origen``: CharField - Banco desde donde se transfirió

.. code-block:: python

   form = TransferenciaBancariaForm(request.POST)
   if form.is_valid():
       comprobante = form.cleaned_data['numero_comprobante']
       banco = form.cleaned_data['banco_origen']

Vistas Principales
------------------

_procesar_pago_con_pasarela
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Función auxiliar privada para procesar pagos a través de la pasarela simulada.

**Parámetros:**

- ``request``: HttpRequest
- ``transaccion``: Instancia de Transaccion
- ``datos_formulario``: Datos validados del formulario
- ``nombre_metodo``: Nombre del método de pago
- ``datos_adicionales``: Datos adicionales (dict, optional)

**Comportamiento:**

1. Determina el monto según el tipo de operación:
   
   - **VENTA**: Cliente paga ``monto_destino`` (PYG)
   - **COMPRA**: Cliente paga ``monto_origen`` (PYG)

2. Prepara datos del pago
3. Envía pago a la pasarela usando ``PasarelaService``
4. Crea registro ``PagoPasarela``
5. Actualiza estado de transacción según resultado:
   
   - **'exito'**: Marca transacción como PAGADA
   - **'pendiente'**: Mantiene como PENDIENTE
   - **'fallo'**: Marca como CANCELADA

6. Registra logs detallados

**Retorna:**

- Redirect a resumen de transacción o template con error

**Uso:**

.. code-block:: python

   return _procesar_pago_con_pasarela(
       request=request,
       transaccion=transaccion,
       datos_formulario=form.cleaned_data,
       nombre_metodo="Billetera Electrónica",
       datos_adicionales={
           'telefono': form.cleaned_data['telefono']
       }
   )

Webhooks
--------

La pasarela de pagos puede enviar notificaciones asíncronas sobre cambios de estado.

**Endpoint de webhook:**

.. code-block:: python

   url_webhook = "http://localhost:8000/pagos/webhook-pago/"

**Configuración en PasarelaService:**

.. code-block:: python

   def __init__(self, timeout: int = 30):
       self.webhook_url = f"http://localhost:8000/pagos/webhook-pago/"

**Procesamiento de webhook:**

El webhook recibe notificaciones cuando el estado de un pago cambia en la pasarela externa.

.. code-block:: python

   @csrf_exempt
   def webhook_pago(request):
       if request.method == 'POST':
           payload = json.loads(request.body)
           id_pago = payload['id_pago']
           nuevo_estado = payload['estado']
           
           # Buscar pago y actualizar
           pago = PagoPasarela.objects.get(id_pago_externo=id_pago)
           pago.estado = nuevo_estado
           pago.save()
           
           # Actualizar transacción asociada
           if nuevo_estado == 'exito':
               pago.transaccion.estado = EstadoTransaccion.objects.get(codigo='PAGADA')
               pago.transaccion.fecha_pago = timezone.now()
               pago.transaccion.save()

**Seguridad de webhook:**

- Validar firma o token de autenticación
- Verificar IP de origen
- Idempotencia: Manejar notificaciones duplicadas

Casos de Uso
------------

**Caso 1: Pago con billetera electrónica**

1. Usuario selecciona "Billetera Electrónica" como método de cobro
2. Completa formulario con número de teléfono
3. Sistema envía pago a pasarela:
   
   .. code-block:: python

      pasarela.procesar_pago(
          monto=150000,
          metodo_cobro="Billetera Electrónica",
          moneda="PYG",
          datos_adicionales={'telefono': '0981123456'}
      )

4. Pasarela simula procesamiento y retorna éxito
5. Sistema crea ``PagoPasarela`` con estado 'exito'
6. Transacción se marca como PAGADA
7. Usuario ve resumen de transacción completada

**Caso 2: Pago con Stripe (tarjeta internacional)**

1. Usuario selecciona método que requiere Stripe
2. Sistema crea sesión de Stripe Checkout:
   
   .. code-block:: python

      stripe_service.crear_sesion_checkout(
          monto=150.00,
          moneda='USD',
          transaccion_id='TXN-...'
      )

3. Usuario es redirigido a Stripe para ingresar datos de tarjeta
4. Stripe procesa el pago y redirige de vuelta
5. Sistema recibe confirmación vía success_url o webhook
6. Transacción se marca como PAGADA

**Caso 3: Pago fallido**

1. Usuario intenta pago con tarjeta inválida
2. Pasarela retorna estado 'fallo':
   
   .. code-block:: python

      {
          'success': True,
          'data': {
              'estado': 'fallo',
              'mensaje': 'Tarjeta rechazada por el banco'
          }
      }

3. Sistema crea ``PagoPasarela`` con estado 'fallo'
4. Transacción se marca como CANCELADA
5. Usuario ve mensaje de error y puede intentar nuevamente

**Caso 4: Pago pendiente con webhook**

1. Usuario inicia transferencia bancaria
2. Pasarela retorna estado 'pendiente'
3. Sistema mantiene transacción como PENDIENTE
4. Horas después, banco confirma la transferencia
5. Pasarela envía webhook con estado 'exito'
6. Sistema procesa webhook y actualiza a PAGADA
7. Usuario (opcional) recibe notificación de confirmación

Integración con Transacciones
------------------------------

El módulo de pagos se integra estrechamente con el módulo de transacciones:

**Flujo completo:**

.. code-block:: python

   from transacciones.models import Transaccion, EstadoTransaccion
   from pagos.services import PasarelaService
   from pagos.models import PagoPasarela
   
   # 1. Crear transacción
   transaccion = Transaccion.objects.create(
       cliente=cliente,
       usuario=operador,
       tipo_operacion=tipo_compra,
       monto_origen=150000,
       moneda_origen=pyg,
       moneda_destino=usd,
       estado=estado_pendiente,
       ...
   )
   
   # 2. Procesar pago
   pasarela = PasarelaService()
   resultado = pasarela.procesar_pago(
       monto=float(transaccion.monto_origen),
       metodo_cobro=transaccion.metodo_cobro.nombre,
       moneda=transaccion.moneda_origen.codigo
   )
   
   # 3. Registrar pago
   if resultado['success']:
       pago = PagoPasarela.objects.create(
           transaccion=transaccion,
           id_pago_externo=resultado['data']['id_pago'],
           monto=transaccion.monto_origen,
           estado=resultado['data']['estado'],
           ...
       )
       
       # 4. Actualizar transacción
       if resultado['data']['estado'] == 'exito':
           transaccion.estado = EstadoTransaccion.objects.get(codigo='PAGADA')
           transaccion.fecha_pago = timezone.now()
           transaccion.save()

Manejo de Errores
-----------------

**Timeouts:**

.. code-block:: python

   try:
       resultado = pasarela.procesar_pago(...)
       if not resultado['success'] and resultado['error_type'] == 'timeout':
           messages.error(request, 
               "La pasarela está tardando mucho. Intenta nuevamente.")
   except Exception as e:
       logger.error(f"Error crítico: {e}")
       messages.error(request, "Error inesperado al procesar pago")

**Pasarela no disponible:**

.. code-block:: python

   if not pasarela.esta_disponible():
       messages.warning(request,
           "La pasarela está temporalmente fuera de servicio.")
       # Mostrar métodos alternativos (efectivo, etc.)

**Validación de respuesta:**

.. code-block:: python

   if resultado['success']:
       # Verificar que la respuesta tenga los campos esperados
       if 'id_pago' not in resultado['data']:
           logger.error("Respuesta de pasarela incompleta")
           raise ValueError("Respuesta inválida de la pasarela")

Configuración Requerida
-----------------------

**settings.py:**

.. code-block:: python

   # Stripe
   STRIPE_SECRET_KEY = env('STRIPE_SECRET_KEY', default='')
   STRIPE_WEBHOOK_SECRET = env('STRIPE_WEBHOOK_SECRET', default='')
   
   # URL del sitio (para redirects)
   SITE_URL = env('SITE_URL', default='http://localhost:8000')
   
   # Logging
   LOGGING = {
       'version': 1,
       'loggers': {
           'pagos': {
               'handlers': ['console', 'file'],
               'level': 'INFO',
           },
       },
   }

**URLs:**

.. code-block:: python

   # pagos/urls.py
   urlpatterns = [
       path('webhook-pago/', webhook_pago, name='webhook_pago'),
       path('stripe/success/', stripe_success, name='stripe_success'),
       path('stripe/cancel/', stripe_cancel, name='stripe_cancel'),
       path('stripe/webhook/', stripe_webhook, name='stripe_webhook'),
   ]

Seguridad
---------

**Datos sensibles:**

- Números de tarjeta: Nunca almacenar completos, solo enmascarados
- CVV: Nunca almacenar, solo usar en tránsito
- API keys: Usar variables de entorno, nunca en código

**Ejemplo de enmascaramiento:**

.. code-block:: python

   def enmascarar_tarjeta(numero):
       return f"****-****-****-{numero[-4:]}"
   
   tarjeta_enmascarada = enmascarar_tarjeta("4111111111111111")
   # Resultado: "****-****-****-1111"

**HTTPS:**

- En producción, forzar HTTPS para todas las rutas de pago
- Verificar certificados SSL en llamadas a APIs externas

**CSRF:**

- Proteger todas las vistas POST excepto webhooks
- Webhooks: Usar ``@csrf_exempt`` pero validar firma

**PCI Compliance:**

- No almacenar datos completos de tarjeta
- Usar Stripe o pasarelas certificadas PCI para tarjetas internacionales
- Implementar tokens de un solo uso

Logging y Auditoría
-------------------

**Registros importantes:**

.. code-block:: python

   import logging
   logger = logging.getLogger('pagos')
   
   # Inicio de pago
   logger.info(f"Iniciando pago - Transacción: {transaccion_id}, "
               f"Método: {metodo}, Monto: {monto}")
   
   # Resultado exitoso
   logger.info(f"Pago exitoso - ID Pago: {pago_id}, "
               f"Transacción: {transaccion_id}")
   
   # Error
   logger.error(f"Error en pago - Transacción: {transaccion_id}, "
                f"Error: {error_msg}", exc_info=True)
   
   # Webhook recibido
   logger.info(f"Webhook recibido - ID Pago: {pago_id}, "
               f"Estado: {nuevo_estado}")

**Campos auditables:**

- ``PagoPasarela.datos_pago``: Metadatos del pago
- ``PagoPasarela.respuesta_pasarela``: Respuesta completa
- ``PagoPasarela.fecha_procesamiento``: Timestamp de procesamiento
- ``PagoPasarela.mensaje_error``: Errores para análisis

Pruebas
-------

**Pruebas unitarias:**

.. code-block:: python

   from django.test import TestCase
   from pagos.services import PasarelaService
   from unittest.mock import patch, MagicMock

   class PasarelaServiceTest(TestCase):
       def test_procesar_pago_exitoso(self):
           service = PasarelaService()
           
           with patch('httpx.Client.post') as mock_post:
               mock_response = MagicMock()
               mock_response.json.return_value = {
                   'id_pago': 'PAY-123',
                   'estado': 'exito'
               }
               mock_post.return_value = mock_response
               
               resultado = service.procesar_pago(
                   monto=100.0,
                   metodo_cobro='Tarjeta',
                   moneda='USD'
               )
               
               self.assertTrue(resultado['success'])
               self.assertEqual(resultado['data']['id_pago'], 'PAY-123')

**Pruebas de integración:**

.. code-block:: python

   def test_flujo_completo_pago(self):
       # Crear transacción
       transaccion = crear_transaccion_test()
       
       # Procesar pago
       response = self.client.post(
           f'/pagos/billetera/{transaccion.id}/',
           {'telefono': '0981123456'}
       )
       
       # Verificar registro de pago
       pago = PagoPasarela.objects.get(transaccion=transaccion)
       self.assertEqual(pago.estado, 'exito')
       
       # Verificar transacción actualizada
       transaccion.refresh_from_db()
       self.assertEqual(transaccion.estado.codigo, 'PAGADA')

**Mock de Stripe:**

.. code-block:: python

   @patch('stripe.checkout.Session.create')
   def test_crear_sesion_stripe(self, mock_create):
       mock_create.return_value = MagicMock(
           id='cs_test_123',
           url='https://checkout.stripe.com/...'
       )
       
       service = StripeService()
       resultado = service.crear_sesion_checkout(
           monto=100.0,
           moneda='USD',
           transaccion_id='TXN-123'
       )
       
       self.assertTrue(resultado['success'])
       self.assertEqual(resultado['session_id'], 'cs_test_123')

Buenas Prácticas
----------------

1. **Idempotencia:** Los webhooks pueden llegar duplicados, manejar correctamente
2. **Timeouts:** Configurar timeouts apropiados para evitar bloqueos
3. **Retry logic:** Implementar reintentos con backoff exponencial
4. **Logging detallado:** Registrar todos los pasos para debugging
5. **Validación de montos:** Verificar que montos coincidan entre sistema y pasarela
6. **Testing exhaustivo:** Probar todos los escenarios (éxito, fallo, timeout)
7. **Monitoreo:** Alertas para tasas de fallo altas
8. **Documentación:** Mantener docs actualizadas con cambios de API
