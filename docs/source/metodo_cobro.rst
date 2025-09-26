Módulo de Métodos de Cobro
==========================

El módulo de métodos de cobro gestiona las formas en que la casa de cambio puede recibir dinero de los clientes durante las transacciones.

Descripción General
-------------------

Los métodos de cobro representan los diferentes canales o medios por los cuales los clientes pueden entregar dinero a la casa de cambio. Cada método puede tener comisiones específicas y estar restringido a ciertas monedas.

Modelo Principal
----------------

MetodoCobro
~~~~~~~~~~~

Modelo que define los métodos disponibles para recibir pagos de clientes.

**Campos principales:**

- ``nombre``: Nombre único del método (ej: "Efectivo", "Transferencia bancaria")
- ``descripcion``: Descripción detallada del método de cobro
- ``comision``: Porcentaje de comisión aplicado (0 a 100%)
- ``es_activo``: Indica si el método está disponible para uso
- ``monedas_permitidas``: Relación ManyToMany con monedas habilitadas
- ``fecha_creacion``: Fecha y hora de creación del registro
- ``fecha_actualizacion``: Fecha y hora de última modificación (auto_now)

**Validaciones:**

- ``nombre``: Debe ser único en el sistema
- ``comision``: Debe estar entre 0 y 100 (validadores MinValueValidator y MaxValueValidator)

**Configuración del modelo:**

- ``verbose_name``: "Método de Cobro"
- ``verbose_name_plural``: "Métodos de Cobro"
- ``ordering``: Ordenado alfabéticamente por nombre
- ``db_table``: 'metodo_cobro_metodocobro'

Métodos de Instancia
--------------------

**get_monedas_permitidas_str()**

Retorna las monedas permitidas como string separado por comas.

.. code-block:: python

   metodo = MetodoCobro.objects.get(nombre="Efectivo")
   print(metodo.get_monedas_permitidas_str())
   # Salida: "PYG, USD, EUR"

**permite_moneda(moneda)**

Verifica si el método permite una moneda específica.

.. code-block:: python

   from monedas.models import Moneda

   usd = Moneda.objects.get(codigo="USD")
   metodo = MetodoCobro.objects.get(nombre="Efectivo")

   if metodo.permite_moneda(usd):
       print("El método permite USD")

**Parámetros:**

- ``moneda``: Instancia del modelo Moneda a verificar

**Retorna:**

- ``bool``: True si el método permite la moneda, False en caso contrario

Relaciones con Otros Modelos
-----------------------------

**Con Moneda (ManyToManyField):**

- Un método de cobro puede estar disponible para múltiples monedas
- Una moneda puede ser compatible con múltiples métodos de cobro
- La relación permite configurar granularmente qué métodos funcionan con qué divisas

**Con Transaccion (ForeignKey desde Transaccion):**

- Una transacción puede tener un método de cobro asociado
- Un método de cobro puede ser usado en múltiples transacciones
- Relación opcional (null=True, blank=True) para flexibilidad

Casos de Uso Comunes
---------------------

**Efectivo**

- Comisión típica: 0%
- Monedas permitidas: PYG, USD, EUR
- Descripción: "Recepción de dinero en efectivo en oficina"

**Transferencia Bancaria**

- Comisión típica: 0.5-1%
- Monedas permitidas: PYG, USD
- Descripción: "Transferencia directa a cuenta bancaria de la empresa"

**Tarjeta de Débito**

- Comisión típica: 2-3%
- Monedas permitidas: PYG
- Descripción: "Pago mediante tarjeta de débito a través de POS"

**Billetera Digital**

- Comisión típica: 1-2%
- Monedas permitidas: PYG
- Descripción: "Pago a través de aplicaciones móviles de pago"

Formularios y Widgets
---------------------

El módulo incluye formularios especializados:

**MetodoCobroForm**

Formulario para crear y editar métodos de cobro con validaciones personalizadas y widgets específicos para la selección de monedas.

**Características:**

- Widget personalizado para selección múltiple de monedas
- Validación de rangos de comisión
- Interfaz user-friendly para gestión de permisos por moneda

Vistas y URLs
-------------

**Vistas implementadas:**

- ``MetodoCobroListView``: Listado paginado de métodos de cobro
- ``MetodoCobroCreateView``: Creación de nuevos métodos
- ``MetodoCobroUpdateView``: Edición de métodos existentes
- ``MetodoCobroDeleteView``: Eliminación lógica (cambio a inactivo)

**URLs disponibles:**

- ``/metodo-cobro/``: Listado
- ``/metodo-cobro/nuevo/``: Crear
- ``/metodo-cobro/<id>/editar/``: Editar
- ``/metodo-cobro/<id>/eliminar/``: Eliminar

Templates
---------

**Plantillas incluidas:**

- ``metodocobro_list.html``: Tabla responsive con filtros y paginación
- ``metodocobro_form.html``: Formulario de creación/edición

**Características de las plantillas:**

- Diseño responsive Bootstrap
- Filtros por estado activo/inactivo
- Indicadores visuales de comisiones
- Etiquetas de monedas permitidas

Tests
-----

El módulo incluye tests comprehensivos que cubren:

**Modelos:**

- Creación y validación de métodos de cobro
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
- Cálculo de comisiones
- Filtros por moneda

Permisos y Seguridad
--------------------

**Permisos requeridos:**

- ``metodo_cobro.view_metodocobro``: Ver métodos de cobro
- ``metodo_cobro.add_metodocobro``: Crear métodos de cobro
- ``metodo_cobro.change_metodocobro``: Modificar métodos de cobro
- ``metodo_cobro.delete_metodocobro``: Eliminar métodos de cobro

**Consideraciones de seguridad:**

- Solo usuarios con permisos apropiados pueden gestionar métodos
- Eliminación lógica para preservar integridad referencial
- Validación de datos en frontend y backend

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

API Considerations
------------------

Para futuras implementaciones de API REST:

**Endpoints sugeridos:**

- ``GET /api/metodos-cobro/``: Listar métodos activos
- ``GET /api/metodos-cobro/{id}/``: Detalle de método
- ``GET /api/metodos-cobro/por-moneda/{codigo}/``: Filtrar por moneda

**Serialización:**

- Incluir información de monedas permitidas
- Calcular comisiones en tiempo real
- Filtrar por estado activo por defecto

Mejores Prácticas
-----------------

**Configuración:**

- Definir métodos básicos (Efectivo, Transferencia) durante setup inicial
- Configurar comisiones realistas según costos operativos
- Mantener métodos inactivos en lugar de eliminarlos

**Uso en transacciones:**

- Verificar disponibilidad del método antes de procesar
- Validar compatibilidad con la moneda de origen
- Calcular comisiones de manera consistente

**Mantenimiento:**

- Revisar y actualizar comisiones periódicamente
- Monitorear uso de cada método para optimización
- Mantener descripciones claras y actualizadas