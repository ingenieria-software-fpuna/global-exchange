Módulo de Métodos de Pago
=========================

El módulo de métodos de pago gestiona las formas en que la casa de cambio puede entregar dinero a los clientes durante las transacciones.

Descripción General
-------------------

Los métodos de pago representan los diferentes canales o medios por los cuales la casa de cambio entrega dinero a los clientes. Cada método puede tener comisiones específicas y estar restringido a ciertas monedas, complementando los métodos de cobro para completar el flujo transaccional.

Modelos Principales
-------------------

Campo
~~~~~

Modelo genérico para definir campos personalizados de métodos de pago.

**Descripción:**

Permite definir campos dinámicos que se pueden asociar a métodos de pago específicos, como número de cuenta bancaria, número de teléfono, etc.

**Campos principales:**

- ``nombre``: Nombre único del campo (ej: "numero_telefono", "documento")
- ``etiqueta``: Etiqueta a mostrar en el formulario (ej: "Número de Teléfono")
- ``tipo``: Tipo de campo HTML (text, number, email, phone, select, textarea)
- ``es_obligatorio``: Indica si el campo es obligatorio
- ``max_length``: Longitud máxima del campo (opcional)
- ``regex_validacion``: Expresión regular para validación (opcional)
- ``placeholder``: Texto de ayuda para el campo
- ``opciones``: Opciones para campos de selección (una por línea)
- ``es_activo``: Indica si el campo está activo
- ``fecha_creacion``: Fecha de creación del registro

**Tipos de campo disponibles:**

.. code-block:: python

    TIPOS_CAMPO = [
        ('text', 'Texto'),
        ('number', 'Número'),
        ('email', 'Email'),
        ('phone', 'Teléfono'),
        ('select', 'Selección'),
        ('textarea', 'Área de texto'),
    ]

**Métodos:**

get_opciones_list()
^^^^^^^^^^^^^^^^^^^

Retorna las opciones como lista.

.. code-block:: python

   campo = Campo.objects.get(nombre='banco')
   opciones = campo.get_opciones_list()
   # Retorna: ['Banco A', 'Banco B', 'Banco C']

**Configuración del modelo:**

- ``verbose_name``: "Campo"
- ``verbose_name_plural``: "Campos"
- ``ordering``: Ordenado alfabéticamente por nombre
- ``db_table``: 'metodo_pago_campo'

**Ejemplo de uso:**

.. code-block:: python

   # Crear campo de número de cuenta bancaria
   campo_cuenta = Campo.objects.create(
       nombre='numero_cuenta',
       etiqueta='Número de Cuenta',
       tipo='text',
       es_obligatorio=True,
       max_length=20,
       regex_validacion=r'^\d{10,20}$',
       placeholder='Ingrese su número de cuenta (10-20 dígitos)',
       es_activo=True
   )
   
   # Crear campo de selección de banco
   campo_banco = Campo.objects.create(
       nombre='banco',
       etiqueta='Banco',
       tipo='select',
       es_obligatorio=True,
       opciones='Banco Continental\nItaú\nBNF\nVision Banco',
       es_activo=True
   )

**Casos de uso comunes:**

1. **Transferencia bancaria:**
   
   - Número de cuenta
   - Banco
   - Tipo de cuenta (ahorro/corriente)
   - Titular de la cuenta

2. **Billetera digital:**
   
   - Número de teléfono
   - Nombre de usuario
   - Email asociado

3. **Tarjeta de crédito:**
   
   - Últimos 4 dígitos
   - Banco emisor
   - Nombre del titular

MetodoPago
~~~~~~~~~~

Modelo que define los métodos disponibles para entregar dinero a clientes.

**Campos principales:**

- ``nombre``: Nombre único del método (ej: "Efectivo", "Tarjeta de Crédito")
- ``descripcion``: Descripción detallada del método de pago
- ``comision``: Porcentaje de comisión aplicado (0 a 100%)
- ``es_activo``: Indica si el método está disponible para uso
- ``monedas_permitidas``: Relación ManyToMany con monedas habilitadas
- ``fecha_creacion``: Fecha y hora de creación del registro
- ``fecha_actualizacion``: Fecha y hora de última modificación (auto_now)

**Validaciones:**

- ``nombre``: Debe ser único en el sistema
- ``comision``: Debe estar entre 0 y 100 (validadores MinValueValidator y MaxValueValidator)

**Configuración del modelo:**

- ``verbose_name``: "Método de Pago"
- ``verbose_name_plural``: "Métodos de Pago"
- ``ordering``: Ordenado alfabéticamente por nombre
- ``db_table``: 'metodo_pago_metodopago'

Métodos de Instancia
--------------------

**get_monedas_permitidas_str()**

Retorna las monedas permitidas como string separado por comas.

.. code-block:: python

   metodo = MetodoPago.objects.get(nombre="Efectivo")
   print(metodo.get_monedas_permitidas_str())
   # Salida: "PYG, USD, EUR"

**permite_moneda(moneda)**

Verifica si el método permite una moneda específica.

.. code-block:: python

   from monedas.models import Moneda

   usd = Moneda.objects.get(codigo="USD")
   metodo = MetodoPago.objects.get(nombre="Efectivo")

   if metodo.permite_moneda(usd):
       print("El método permite USD")

**Parámetros:**

- ``moneda``: Instancia del modelo Moneda a verificar

**Retorna:**

- ``bool``: True si el método permite la moneda, False en caso contrario

Relaciones con Otros Modelos
-----------------------------

**Con Moneda (ManyToManyField):**

- Un método de pago puede estar disponible para múltiples monedas
- Una moneda puede ser compatible con múltiples métodos de pago
- La relación permite configurar granularmente qué métodos funcionan con qué divisas

**Con Transaccion (ForeignKey desde Transaccion):**

- Una transacción puede tener un método de pago asociado
- Un método de pago puede ser usado en múltiples transacciones
- Relación opcional (null=True, blank=True) para flexibilidad

Casos de Uso Comunes
---------------------

**Efectivo**

- Comisión típica: 0%
- Monedas permitidas: PYG, USD, EUR
- Descripción: "Entrega de dinero en efectivo en oficina"

**Transferencia Bancaria**

- Comisión típica: 0.5-1%
- Monedas permitidas: PYG, USD
- Descripción: "Transferencia directa a cuenta bancaria del cliente"

**Tarjeta de Crédito**

- Comisión típica: 3-5%
- Monedas permitidas: PYG, USD
- Descripción: "Abono a tarjeta de crédito del cliente"

**Cheque**

- Comisión típica: 1-2%
- Monedas permitidas: PYG, USD
- Descripción: "Emisión de cheque bancario a favor del cliente"

**Billetera Digital**

- Comisión típica: 1-2%
- Monedas permitidas: PYG
- Descripción: "Transferencia a aplicaciones móviles de pago del cliente"

Diferencias con Métodos de Cobro
---------------------------------

**Propósito:**

- **Métodos de Cobro**: Como la casa de cambio **recibe** dinero del cliente
- **Métodos de Pago**: Como la casa de cambio **entrega** dinero al cliente

**Flujo transaccional:**

1. Cliente entrega dinero via **método de cobro**
2. Sistema procesa la transacción
3. Casa de cambio entrega dinero via **método de pago**

**Consideraciones operativas:**

- Los métodos de pago pueden tener comisiones más altas debido a costos operativos
- Algunos métodos solo funcionan como pago (ej: cheques)
- Otros solo como cobro (ej: débito en POS)

Formularios y Widgets
---------------------

El módulo incluye formularios especializados:

**MetodoPagoForm**

Formulario para crear y editar métodos de pago con validaciones personalizadas y widgets específicos.

**Características:**

- Widget personalizado para selección múltiple de monedas
- Validación de rangos de comisión
- Interfaz user-friendly para gestión de permisos por moneda
- Validaciones específicas para métodos de entrega

Vistas y URLs
-------------

**Vistas implementadas:**

- ``MetodoPagoListView``: Listado paginado de métodos de pago
- ``MetodoPagoCreateView``: Creación de nuevos métodos
- ``MetodoPagoUpdateView``: Edición de métodos existentes
- ``MetodoPagoDeleteView``: Eliminación lógica (cambio a inactivo)

**URLs disponibles:**

- ``/metodo-pago/``: Listado
- ``/metodo-pago/nuevo/``: Crear
- ``/metodo-pago/<id>/editar/``: Editar
- ``/metodo-pago/<id>/eliminar/``: Eliminar

Templates
---------

**Plantillas incluidas:**

- ``metodopago_list.html``: Tabla responsive con filtros y paginación
- ``metodopago_form.html``: Formulario de creación/edición

**Características de las plantillas:**

- Diseño responsive Bootstrap
- Filtros por estado activo/inactivo
- Indicadores visuales de comisiones
- Etiquetas de monedas permitidas
- Diferenciación visual con métodos de cobro

Tests
-----

El módulo incluye tests comprehensivos que cubren:

**Modelos:**

- Creación y validación de métodos de pago
- Relaciones con monedas
- Métodos de instancia
- Validaciones de comisiones

**Vistas:**

- CRUD completo
- Permisos de acceso
- Validación de formularios
- Respuestas correctas

**Integración:**

- Uso en transacciones
- Cálculo de comisiones de entrega
- Filtros por moneda de destino

Permisos y Seguridad
--------------------

**Permisos requeridos:**

- ``metodo_pago.view_metodopago``: Ver métodos de pago
- ``metodo_pago.add_metodopago``: Crear métodos de pago
- ``metodo_pago.change_metodopago``: Modificar métodos de pago
- ``metodo_pago.delete_metodopago``: Eliminar métodos de pago

**Consideraciones de seguridad:**

- Solo usuarios con permisos apropiados pueden gestionar métodos
- Eliminación lógica para preservar integridad referencial
- Validación de datos en frontend y backend
- Controles adicionales para métodos de alto riesgo

Admin Interface
---------------

El modelo está registrado en Django Admin con:

**Configuraciones personalizadas:**

- Lista de campos mostrados
- Filtros por estado activo y monedas
- Búsqueda por nombre y descripción
- Acciones masivas para activar/desactivar

**Campos inline:**

- Gestión de monedas permitidas directamente desde la vista principal

Integración con Transacciones
------------------------------

**Cálculo de comisiones:**

Cuando se selecciona un método de pago en una transacción, el sistema:

1. Verifica compatibilidad con la moneda de destino
2. Calcula la comisión basada en el porcentaje configurado
3. Incluye la comisión en el cálculo total de la transacción
4. Muestra el desglose detallado al cliente

**Validaciones en tiempo real:**

- Verificación de disponibilidad del método
- Validación de monedas permitidas
- Cálculo automático de costos adicionales

Consideraciones Operativas
--------------------------

**Gestión de liquidez:**

- Métodos de pago en efectivo requieren disponibilidad física
- Transferencias necesitan fondos en cuentas bancarias
- Cheques requieren chequeras y límites de emisión

**Costos operativos:**

- Transferencias bancarias tienen costos de comisiones bancarias
- Tarjetas de crédito implican costos de procesamiento
- Efectivo requiere manejo y custodia segura

**Tiempos de procesamiento:**

- Efectivo: Inmediato
- Transferencias: 1-2 días hábiles
- Cheques: Según política bancaria
- Billeteras digitales: Inmediato a pocas horas

API Considerations
------------------

Para futuras implementaciones de API REST:

**Endpoints sugeridos:**

- ``GET /api/metodos-pago/``: Listar métodos activos
- ``GET /api/metodos-pago/{id}/``: Detalle de método
- ``GET /api/metodos-pago/por-moneda/{codigo}/``: Filtrar por moneda
- ``POST /api/metodos-pago/calcular-comision/``: Calcular comisión

**Serialización:**

- Incluir información de monedas permitidas
- Calcular comisiones en tiempo real
- Incluir tiempos estimados de procesamiento
- Filtrar por estado activo por defecto

Mejores Prácticas
-----------------

**Configuración inicial:**

- Definir métodos básicos (Efectivo, Transferencia) durante setup
- Configurar comisiones realistas según costos operativos
- Establecer límites operativos por método

**Gestión continua:**

- Revisar y actualizar comisiones periódicamente
- Monitorear liquidez disponible por método
- Mantener métodos inactivos en lugar de eliminarlos

**En transacciones:**

- Verificar disponibilidad antes de procesar
- Validar compatibilidad con moneda de destino
- Informar claramente tiempos de procesamiento al cliente
- Documentar todas las comisiones aplicadas

**Auditoría:**

- Llevar registro de cambios en comisiones
- Monitorear uso por método para optimización
- Evaluar rentabilidad de cada método de pago