Módulo de Transacciones
======================

El módulo de transacciones es el núcleo del sistema Global Exchange, encargado de gestionar todas las operaciones de compra y venta de divisas.

Modelos Principales
------------------

TipoOperacion
~~~~~~~~~~~~~

Modelo que define los tipos de operaciones disponibles en el sistema.

**Campos principales:**

- ``codigo``: Código único del tipo (COMPRA/VENTA)
- ``nombre``: Nombre descriptivo del tipo de operación
- ``descripcion``: Descripción detallada del tipo
- ``activo``: Indica si el tipo está habilitado
- ``fecha_creacion``: Fecha de creación del registro

**Tipos disponibles:**

- ``COMPRA``: Cliente compra divisas extranjeras con guaraníes
- ``VENTA``: Cliente vende divisas extranjeras por guaraníes

EstadoTransaccion
~~~~~~~~~~~~~~~~~

Modelo que gestiona los estados posibles de una transacción.

**Campos principales:**

- ``codigo``: Código único del estado (PENDIENTE/PAGADA/CANCELADA/ANULADA)
- ``nombre``: Nombre descriptivo del estado
- ``descripcion``: Descripción del estado
- ``es_final``: Indica si es un estado terminal (no puede cambiar)
- ``activo``: Indica si el estado está habilitado

**Estados disponibles:**

- ``PENDIENTE``: Transacción creada, pendiente de pago
- ``PAGADA``: Transacción completada exitosamente
- ``CANCELADA``: Transacción cancelada (por expiración u otros motivos)
- ``ANULADA``: Transacción anulada por el sistema o usuario

Transaccion
~~~~~~~~~~~

Modelo principal que representa una operación de cambio de divisas.

**Identificación:**

- ``id``: Clave primaria autoincremental
- ``id_transaccion``: Identificador único alfanumérico (formato: TXN-YYYYMMDDHHMMSS-XXXXXX)
- ``codigo_verificacion``: Código alfanumérico de 8 caracteres para verificación

**Relaciones:**

- ``cliente``: Cliente asociado (opcional para transacciones casuales)
- ``usuario``: Usuario operador que procesa la transacción
- ``tipo_operacion``: Tipo de operación (compra/venta)
- ``moneda_origen``: Moneda que entrega el cliente
- ``moneda_destino``: Moneda que recibe el cliente
- ``metodo_cobro``: Método por el cual se recibe el dinero
- ``metodo_pago``: Método por el cual se entrega el dinero
- ``estado``: Estado actual de la transacción

**Montos y cálculos:**

- ``monto_origen``: Cantidad en moneda de origen (hasta 15 dígitos, 2 decimales)
- ``monto_destino``: Cantidad en moneda de destino (hasta 15 dígitos, 2 decimales)
- ``tasa_cambio``: Tasa de cambio aplicada (hasta 12 dígitos, 4 decimales)
- ``porcentaje_comision``: Porcentaje de comisión aplicado (hasta 8 dígitos, 4 decimales)
- ``monto_comision``: Monto total de comisión en moneda origen
- ``porcentaje_descuento``: Porcentaje de descuento por tipo de cliente
- ``monto_descuento``: Monto total de descuento aplicado

**Control temporal:**

- ``fecha_creacion``: Fecha y hora de creación (auto_now_add)
- ``fecha_actualizacion``: Fecha y hora de última modificación (auto_now)
- ``fecha_expiracion``: Fecha límite para completar el pago (5 minutos por defecto)
- ``fecha_pago``: Fecha y hora en que se completó el pago

**Auditoría:**

- ``observaciones``: Observaciones adicionales
- ``ip_cliente``: Dirección IP desde donde se originó la transacción

Métodos Principales
-------------------

**Métodos estáticos:**

- ``generar_id_transaccion()``: Genera ID único con timestamp y caracteres aleatorios
- ``generar_codigo_verificacion()``: Genera código alfanumérico de 8 caracteres

**Métodos de instancia:**

- ``esta_expirada()``: Verifica si la transacción ha expirado
- ``puede_cancelar_por_expiracion()``: Verifica si puede cancelarse por expiración
- ``cancelar_por_expiracion()``: Cancela automáticamente transacciones expiradas
- ``calcular_total_final()``: Calcula monto total considerando comisiones y descuentos
- ``get_resumen_financiero()``: Retorna diccionario con resumen financiero básico
- ``get_resumen_detallado()``: Retorna análisis financiero completo con formateo
- ``get_tipo_tasa_utilizada()``: Determina si se usó tasa de compra o venta
- ``get_tasa_base()``: Obtiene la tasa base actual sin ajustes de cliente

Validaciones
------------

El modelo implementa las siguientes validaciones:

- **Monedas diferentes**: La moneda origen debe ser diferente a la destino
- **Cliente activo**: Si se especifica cliente, debe estar activo
- **Tipo de operación activo**: El tipo de operación debe estar habilitado
- **Montos positivos**: Todos los montos deben ser mayor a cero

Índices de Base de Datos
------------------------

Para optimizar consultas frecuentes, se implementan los siguientes índices:

- ``id_transaccion`` (único)
- ``cliente, fecha_creacion`` (descendente)
- ``usuario, fecha_creacion`` (descendente)
- ``estado, fecha_creacion`` (descendente)
- ``fecha_expiracion``
- ``tipo_operacion, fecha_creacion`` (descendente)

Lógica de Negocio
-----------------

**Generación automática:**

- El ID de transacción se genera automáticamente al crear una nueva transacción
- El código de verificación se asigna automáticamente
- La fecha de expiración se establece 5 minutos después de la creación

**Cálculos financieros:**

El sistema implementa una lógica compleja de cálculo que considera:

- Tasa base de la moneda
- Comisiones de métodos de cobro y pago
- Descuentos por tipo de cliente
- Formateo específico por moneda (especialmente para guaraníes)

**Estados y flujo:**

1. **PENDIENTE**: Estado inicial, transacción creada
2. **PAGADA**: Cliente completó el pago exitosamente
3. **CANCELADA**: Cancelada por expiración o solicitud
4. **ANULADA**: Anulada por problemas del sistema

Casos de Uso
------------

**Compra de divisas (PYG → USD):**

1. Cliente entrega guaraníes
2. Sistema calcula USD a entregar según tasa de venta
3. Aplica comisiones de métodos de cobro/pago
4. Aplica descuentos por tipo de cliente
5. Genera comprobante con código de verificación

**Venta de divisas (USD → PYG):**

1. Cliente entrega dólares
2. Sistema calcula guaraníes a entregar según tasa de compra
3. Aplica comisiones y descuentos
4. Genera comprobante con código de verificación

Management Commands
-------------------

**setup_transacciones**

Comando de gestión Django para inicializar datos básicos del módulo:

- Crea tipos de operación (COMPRA/VENTA)
- Crea estados de transacción (PENDIENTE/PAGADA/CANCELADA/ANULADA)
- Configura valores por defecto del sistema

Uso:

.. code-block:: bash

   python manage.py setup_transacciones

Integración con Otros Módulos
------------------------------

El módulo de transacciones se integra estrechamente con:

- **usuarios**: Para operadores que procesan transacciones
- **clientes**: Para asociar transacciones y aplicar descuentos
- **monedas**: Para monedas origen y destino
- **tasa_cambio**: Para obtener tasas actuales
- **metodo_pago**: Para métodos de entrega de dinero
- **metodo_cobro**: Para métodos de recepción de dinero

Consideraciones de Performance
------------------------------

**Optimizaciones implementadas:**

- Índices estratégicos para consultas frecuentes
- Campos calculados almacenados para evitar recálculos
- Validaciones eficientes a nivel de modelo
- Uso de DecimalField para precisión financiera

**Recomendaciones:**

- Usar paginación para listados grandes
- Filtrar por fechas para consultas históricas
- Aprovechar índices en consultas frecuentes
- Considerar archivado de transacciones antiguas