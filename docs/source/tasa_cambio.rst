Módulo de Tasa de Cambio
=========================

El módulo de tasa de cambio gestiona las cotizaciones de divisas del sistema Global Exchange, incluyendo precios de compra, venta y comisiones.

Modelo Principal
----------------

TasaCambio
~~~~~~~~~~

Modelo que representa las cotizaciones de divisas.

**Campos principales:**

- ``moneda``: Moneda para la cual se establece la cotización (ForeignKey)
- ``precio_base``: Precio base en guaraníes (valor entero, mínimo 1)
- ``comision_compra``: Comisión en guaraníes que se resta al precio base (entero, mínimo 0)
- ``comision_venta``: Comisión en guaraníes que se suma al precio base (entero, mínimo 0)
- ``es_activa``: Indica si la cotización está activa
- ``fecha_creacion``: Fecha y hora de creación
- ``fecha_actualizacion``: Fecha y hora de última actualización

**Propiedades calculadas:**

.. code-block:: python

    # tasa_compra: Precio al que compramos la divisa del cliente
    tasa_compra = precio_base - comision_compra
    
    # tasa_venta: Precio al que vendemos la divisa al cliente
    tasa_venta = precio_base + comision_venta
    
    # spread: Diferencia entre venta y compra
    spread = tasa_venta - tasa_compra
    
    # spread_porcentual: Spread como porcentaje
    spread_porcentual = ((tasa_venta - tasa_compra) / tasa_compra) * 100
    
    # margen_total: Suma de comisiones
    margen_total = comision_compra + comision_venta
    
    # margen_porcentual: Margen como porcentaje del precio base
    margen_porcentual = (margen_total / precio_base) * 100

**Ejemplo de configuración:**

.. code-block:: python

    # Crear tasa de cambio para USD
    tasa_usd = TasaCambio.objects.create(
        moneda=usd,
        precio_base=7500,      # Gs. 7.500
        comision_compra=100,   # Gs. 100
        comision_venta=100,    # Gs. 100
        es_activa=True
    )
    
    # Precios resultantes:
    # Compra: 7.500 - 100 = Gs. 7.400 (compramos USD del cliente)
    # Venta: 7.500 + 100 = Gs. 7.600 (vendemos USD al cliente)
    # Spread: 7.600 - 7.400 = Gs. 200

Lógica de Activación
---------------------

**Regla de unicidad:**

Solo puede haber **una tasa activa por moneda** en cualquier momento.

**Desactivación automática:**

Al activar o crear una nueva tasa:

1. Sistema busca tasas activas de la misma moneda
2. Desactiva automáticamente tasas anteriores
3. Activa la nueva tasa
4. Todo en una transacción atómica

.. code-block:: python

    def save(self, *args, **kwargs):
        with transaction.atomic():
            # Desactivar tasas anteriores de la misma moneda
            if not self.pk or (self.pk and self.es_activa):
                TasaCambio.objects.filter(
                    moneda=self.moneda,
                    es_activa=True
                ).exclude(pk=self.pk).update(es_activa=False)
            
            super().save(*args, **kwargs)

Métodos de Formateo
-------------------

**formatear_precio_base()**

Formatea el precio base según decimales de la moneda.

.. code-block:: python

    tasa = TasaCambio.objects.get(moneda__codigo='USD', es_activa=True)
    precio_fmt = tasa.formatear_precio_base()
    # Resultado: "7500.00" (si USD tiene 2 decimales)

**formatear_tasa_compra()**

Formatea la tasa de compra (precio_base - comision_compra).

.. code-block:: python

    compra_fmt = tasa.formatear_tasa_compra()
    # Resultado: "7400.00"

**formatear_tasa_venta()**

Formatea la tasa de venta (precio_base + comision_venta).

.. code-block:: python

    venta_fmt = tasa.formatear_tasa_venta()
    # Resultado: "7600.00"

Vistas (Views)
--------------

El módulo incluye vistas completas para gestión de tasas:

**Listado:**

- ``TasaCambioListView``: Lista de tasas con estado
- Filtros por moneda, estado activo
- Muestra tasa de compra, venta y spread

**CRUD:**

- ``TasaCambioCreateView``: Crear nueva tasa
- ``TasaCambioDetailView``: Detalle de tasa con análisis
- ``TasaCambioUpdateView``: Editar tasa existente
- ``TasaCambioToggleActiveView``: Activar/desactivar tasa

**Consultas públicas:**

- ``TasaCambioPublicView``: Vista pública de tasas activas
- Sin autenticación requerida
- Solo muestra tasas de monedas activas

Formularios
-----------

**TasaCambioForm**

Formulario para crear y editar tasas de cambio.

**Validaciones:**

- Precio base: Entero positivo mayor a 0
- Comisión compra: Entero no negativo
- Comisión venta: Entero no negativo
- Comisión compra no puede ser mayor al precio base
- Moneda: Debe estar activa

**Widgets personalizados:**

- Input numérico para precio base
- Input numérico para comisiones
- Select con monedas activas
- Vista previa de cálculos en tiempo real

**Validación de spread:**

.. code-block:: python

    def clean(self):
        cleaned_data = super().clean()
        precio_base = cleaned_data.get('precio_base')
        comision_compra = cleaned_data.get('comision_compra')
        
        if comision_compra and precio_base:
            if comision_compra >= precio_base:
                raise ValidationError(
                    'Comisión de compra no puede ser mayor o igual al precio base'
                )
        
        return cleaned_data

Integración con Notificaciones
-------------------------------

El módulo se integra con el sistema de notificaciones:

**Notificación automática:**

Al activar una nueva tasa de cambio:

1. Sistema detecta cambio de tasa activa
2. Identifica usuarios suscritos a notificaciones
3. Envía notificación en la plataforma
4. Envía email a usuarios que lo tienen habilitado

**Signal de notificación:**

.. code-block:: python

    from django.db.models.signals import post_save
    from notificaciones.models import Notificacion
    
    @receiver(post_save, sender=TasaCambio)
    def notificar_cambio_tasa(sender, instance, created, **kwargs):
        if instance.es_activa:
            # Crear notificación para usuarios suscritos
            Notificacion.crear_notificacion_tasa_cambio(
                tasa=instance,
                tipo='creacion' if created else 'actualizacion'
            )

URLs
----

Rutas definidas en ``tasa_cambio/urls.py``:

.. code-block:: python

    urlpatterns = [
        path('', TasaCambioListView.as_view(), name='tasacambio_list'),
        path('publica/', TasaCambioPublicView.as_view(), name='tasacambio_public'),
        path('crear/', TasaCambioCreateView.as_view(), name='tasacambio_create'),
        path('<int:pk>/', TasaCambioDetailView.as_view(), name='tasacambio_detail'),
        path('<int:pk>/editar/', TasaCambioUpdateView.as_view(), name='tasacambio_update'),
        path('<int:pk>/toggle/', TasaCambioToggleActiveView.as_view(), name='tasacambio_toggle'),
        
        # API para consultas
        path('api/activa/<str:codigo_moneda>/', obtener_tasa_activa, name='tasacambio_api_activa'),
    ]

Plantillas
----------

Plantillas ubicadas en ``tasa_cambio/templates/tasa_cambio/``:

- ``tasacambio_list.html``: Lista de tasas con análisis
- ``tasacambio_public.html``: Vista pública de tasas
- ``tasacambio_detail.html``: Detalle con gráficos
- ``tasacambio_form.html``: Formulario crear/editar

**Componentes:**

- ``_tasa_card.html``: Card de tasa para listados
- ``_spread_chart.html``: Gráfico de spread
- ``_historial_tasas.html``: Historial de cambios

Casos de Uso
------------

**Actualización de tasa:**

1. Admin accede a gestión de tasas
2. Crea nueva tasa con precio actual
3. Sistema desactiva tasa anterior automáticamente
4. Notifica a usuarios suscritos
5. Transacciones nuevas usan la tasa actualizada

**Cálculo de transacción - Compra de USD:**

Cliente entrega PYG, recibe USD:

.. code-block:: python

    # Cliente quiere comprar USD 100
    tasa = TasaCambio.objects.get(moneda__codigo='USD', es_activa=True)
    
    monto_usd = 100
    # Usamos tasa de venta (vendemos USD al cliente)
    total_pyg = monto_usd * tasa.tasa_venta
    
    # Si tasa_venta = 7600
    # total_pyg = 100 * 7600 = Gs. 760.000

**Cálculo de transacción - Venta de USD:**

Cliente entrega USD, recibe PYG:

.. code-block:: python

    # Cliente vende USD 100
    tasa = TasaCambio.objects.get(moneda__codigo='USD', es_activa=True)
    
    monto_usd = 100
    # Usamos tasa de compra (compramos USD del cliente)
    total_pyg = monto_usd * tasa.tasa_compra
    
    # Si tasa_compra = 7400
    # total_pyg = 100 * 7400 = Gs. 740.000

Análisis y Reportes
-------------------

**Análisis de spread:**

.. code-block:: python

    # Spread absoluto
    spread = tasa.spread  # Gs. 200
    
    # Spread porcentual
    spread_pct = tasa.spread_porcentual  # 2.70%
    
    # Margen total
    margen = tasa.margen_total  # Gs. 200
    
    # Margen porcentual
    margen_pct = tasa.margen_porcentual  # 2.67%

**Historial de tasas:**

.. code-block:: python

    # Obtener historial de una moneda
    historial = TasaCambio.objects.filter(
        moneda__codigo='USD'
    ).order_by('-fecha_creacion')[:30]
    
    # Análisis de volatilidad
    precios = [t.precio_base for t in historial]
    promedio = sum(precios) / len(precios)
    max_precio = max(precios)
    min_precio = min(precios)
    volatilidad = max_precio - min_precio

Permisos y Seguridad
--------------------

**Permisos personalizados:**

- ``can_view_sensitive_columns``: Ver datos sensibles (precios, comisiones, spread)

**Control de acceso:**

- Admin: CRUD completo de tasas
- Operador: Ver tasas activas
- Visitante: Ver tasas públicas limitadas

**Protección de datos:**

Usuarios sin permiso ``can_view_sensitive_columns`` solo ven:
- Moneda
- Estado (activa/inactiva)
- Fecha de creación

Usuarios con permiso ven además:
- Precio base
- Comisiones
- Spread y márgenes
- Detalles de cálculo

API REST
--------

El módulo expone endpoints para consultas:

**GET /api/activa/<codigo_moneda>/**

Retorna la tasa activa de una moneda.

.. code-block:: json

    {
        "moneda": "USD",
        "precio_base": 7500,
        "tasa_compra": 7400,
        "tasa_venta": 7600,
        "spread": 200,
        "fecha_actualizacion": "2025-10-31T10:30:00Z"
    }

Pruebas
-------

Pruebas ubicadas en ``tasa_cambio/tests.py``:

- Pruebas de creación y validación
- Pruebas de desactivación automática
- Pruebas de cálculos (spread, márgenes)
- Pruebas de notificaciones
- Pruebas de permisos
- Pruebas de API

Ejecutar pruebas:

.. code-block:: bash

    poetry run python manage.py test tasa_cambio

Management Commands
-------------------

setup_tasas_cambio
~~~~~~~~~~~~~~~~~~

Comando para inicializar tasas de cambio predeterminadas.

.. code-block:: bash

    python manage.py setup_tasas_cambio

**Funcionalidad:**

- Crea tasas para monedas activas
- Configura precios de mercado actuales
- Es idempotente

Consideraciones
---------------

**Performance:**

- Solo una tasa activa por moneda (índice único)
- Caché de tasas activas
- Queries optimizadas para transacciones

**Mantenimiento:**

- Actualizar tasas regularmente según mercado
- Revisar spreads periódicamente
- Auditar cambios de tasas
- Monitorear volatilidad

**Reglas de negocio:**

- Precio base siempre positivo
- Comisiones no negativas
- Spread debe ser rentable
- Tasa de compra < Tasa de venta

**Integración:**

Se integra con:

- ``monedas``: Para obtener propiedades de moneda
- ``transacciones``: Para cálculo de montos
- ``notificaciones``: Para alertar cambios
- ``usuarios``: Para permisos y suscripciones

Mejores Prácticas
-----------------

**Actualización de tasas:**

1. Consultar precio de mercado actual
2. Calcular spread deseado (ej: 2-3%)
3. Distribuir spread entre comisiones
4. Crear nueva tasa (desactiva anterior automáticamente)
5. Verificar notificaciones enviadas

**Monitoreo:**

- Revisar tasas diariamente
- Comparar con mercado
- Ajustar según volumen de transacciones
- Analizar rentabilidad por moneda

**Auditoría:**

- Registrar todos los cambios de tasa
- Documentar motivo de actualización
- Revisar impacto en transacciones activas
- Monitorear quejas de clientes
