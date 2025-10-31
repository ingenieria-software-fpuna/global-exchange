Módulo Tauser (Puntos de Atención)
===================================

El módulo tauser gestiona los puntos de atención físicos del sistema, su inventario de monedas y el historial de movimientos.

Modelos Principales
------------------

Tauser
~~~~~~

Representa un punto de atención o sucursal del negocio de cambio.

**Campos:**

- ``nombre``: Nombre del punto de atención
- ``direccion``: Dirección física del local
- ``horario_atencion``: Horario de funcionamiento
- ``es_activo``: Estado del punto (activo/inactivo)
- ``fecha_instalacion``: Fecha de apertura del punto
- ``fecha_creacion``: Auditoría - creación del registro
- ``fecha_actualizacion``: Auditoría - última modificación

**Métodos:**

- ``toggle_activo()``: Cambia el estado activo/inactivo

Stock
~~~~~

Controla el inventario de cada moneda en un punto de atención específico.

**Campos:**

- ``tauser``: Punto de atención (ForeignKey)
- ``moneda``: Moneda del inventario (ForeignKey)
- ``cantidad``: Cantidad disponible (15 dígitos, 2 decimales)
- ``es_activo``: Estado del stock
- Unique together: (tauser, moneda)

**Métodos principales:**

.. code-block:: python

    # Agregar stock (entrada)
    stock.agregar_cantidad(
        cantidad=10000,
        usuario=operador,
        transaccion=tx,
        observaciones='Reposición semanal'
    )
    
    # Reducir stock (salida)
    stock.reducir_cantidad(
        cantidad=5000,
        usuario=operador,
        transaccion=tx,
        observaciones='Venta a cliente'
    )
    
    # Verificar disponibilidad
    if stock.esta_bajo_stock():
        # Alertar reposición necesaria
        pass

**Funciones de formateo:**

- ``formatear_cantidad()``: Formatea según decimales de la moneda
- ``mostrar_cantidad()``: Incluye símbolo de la moneda

StockDenominacion
~~~~~~~~~~~~~~~~~

Gestiona el inventario de billetes y monedas por denominación específica.

**Campos:**

- ``stock``: Stock general al que pertenece
- ``denominacion``: Denominación específica (billete/moneda)
- ``cantidad``: Número de billetes/monedas (entero positivo)
- ``es_activo``: Estado
- Unique together: (stock, denominacion)

**Métodos:**

.. code-block:: python

    # Agregar denominación específica
    stock_denom.agregar_cantidad(
        cantidad=50,  # 50 billetes de esta denominación
        usuario=operador,
        observaciones='Entrada de caja fuerte'
    )
    
    # Reducir denominación específica
    stock_denom.reducir_cantidad(
        cantidad=20,  # 20 billetes entregados
        usuario=operador,
        transaccion=tx
    )
    
    # Calcular valor total
    valor = stock_denom.valor_total()  # cantidad * valor_denominacion
    valor_fmt = stock_denom.mostrar_valor_total()  # Con símbolo

**Actualización automática:**

Los métodos de StockDenominacion actualizan automáticamente el Stock general.

HistorialStock
~~~~~~~~~~~~~~

Registro de auditoría de todos los movimientos de stock.

**Campos:**

- ``stock``: Stock afectado
- ``tipo_movimiento``: ENTRADA o SALIDA
- ``origen_movimiento``: MANUAL o TRANSACCION
- ``cantidad_movida``: Cantidad del movimiento
- ``cantidad_anterior``: Stock antes del movimiento
- ``cantidad_posterior``: Stock después del movimiento
- ``usuario``: Usuario que realizó el movimiento (opcional)
- ``transaccion``: Transacción asociada (opcional)
- ``observaciones``: Notas adicionales
- ``fecha_movimiento``: Timestamp automático

**Uso:**

El historial se crea automáticamente al usar ``agregar_cantidad()`` o ``reducir_cantidad()``.

HistorialStockDenominacion
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Similar a HistorialStock pero para movimientos por denominación específica.

Mantiene trazabilidad de billetes y monedas individuales.

CodigoVerificacionRetiro
~~~~~~~~~~~~~~~~~~~~~~~~~

Códigos de 6 dígitos para validar retiros de efectivo en puntos de atención.

**Funcionalidad:**

1. Cliente realiza transacción online
2. Sistema genera código de 6 dígitos con expiración (5 minutos por defecto)
3. Cliente presenta código en el Tauser
4. Operador valida código y entrega efectivo
5. Sistema marca código como usado y actualiza stock

**Métodos:**

.. code-block:: python

    # Crear código para retiro
    codigo_obj = CodigoVerificacionRetiro.crear_codigo(
        transaccion=transaccion,
        request=request,
        minutos_expiracion=5
    )
    
    # Verificar validez
    if codigo_obj.es_valido():
        # Procesar retiro
        codigo_obj.usado = True
        codigo_obj.save()
    
    # Limpiar códigos expirados
    CodigoVerificacionRetiro.limpiar_codigos_expirados()

Flujo de Trabajo
----------------

**Apertura de Tauser:**

1. Admin crea registro de Tauser
2. Define datos de ubicación y horarios
3. Inicializa stock de cada moneda soportada
4. Configura denominaciones disponibles

**Transacción con retiro en Tauser:**

1. Cliente inicia transacción (puede ser online)
2. Sistema genera código de verificación
3. Cliente va al Tauser con el código
4. Operador verifica código en sistema
5. Sistema valida stock disponible
6. Operador entrega efectivo
7. Sistema reduce stock y registra en historial
8. Marca código como usado

**Reposición de stock:**

1. Admin/Operador accede a gestión de stock
2. Registra entrada de dinero
3. Especifica cantidad por denominación
4. Sistema actualiza stock y crea historial
5. Stock disponible para transacciones

Vistas y URLs
-------------

El módulo incluye vistas para:

- CRUD de Tausers
- Gestión de stock por Tauser
- Consulta de historial de movimientos
- Validación de códigos de retiro
- Reportes de inventario

Permisos
--------

**Permisos personalizados:**

- ``deactivate_tauser``: Desactivar punto de atención
- ``manage_stock``: Gestionar inventario
- ``manage_stock_denominacion``: Gestionar denominaciones
- ``view_historial_stock``: Ver historial de movimientos
- ``view_historial_stock_denominacion``: Ver historial por denominación

Integración
-----------

**Con transacciones:**

Al completar transacción con entrega en Tauser:

.. code-block:: python

    # Reducir stock del Tauser
    stock = Stock.objects.get(
        tauser=tauser_seleccionado,
        moneda=transaccion.moneda_destino
    )
    
    stock.reducir_cantidad(
        cantidad=transaccion.monto_destino,
        usuario=operador,
        transaccion=transaccion,
        observaciones=f'Entrega transacción {transaccion.id_transaccion}'
    )

**Con notificaciones:**

Sistema notifica cuando:

- Stock bajo umbral mínimo
- Código de retiro expira sin usar
- Movimiento manual de stock significativo

Reportes
--------

El módulo soporta generación de:

- Stock actual por Tauser y moneda
- Movimientos de stock por período
- Denominaciones disponibles
- Códigos de retiro pendientes/usados/expirados
- Análisis de rotación de inventario

Consideraciones
---------------

**Seguridad:**

- Solo Admin y Operadores autorizados gestionan stock
- Historial inmutable de movimientos
- Validación de stock disponible antes de transacciones
- Códigos de retiro con expiración

**Performance:**

- Índices en (tauser, moneda) para queries rápidos
- Unique constraints previenen duplicados
- Historial separado para no afectar queries de stock

**Auditoría:**

- Cada movimiento registrado con usuario y timestamp
- Trazabilidad completa de inventario
- Observaciones para contexto adicional

Pruebas
-------

.. code-block:: bash

    poetry run python manage.py test tauser
