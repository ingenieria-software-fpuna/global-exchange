Módulo de Monedas
=================

El módulo de monedas gestiona las divisas soportadas por el sistema Global Exchange, incluyendo sus propiedades, denominaciones y formateo.

Modelos Principales
------------------

Moneda
~~~~~~

Modelo que representa una divisa en el sistema.

**Campos principales:**

- ``nombre``: Nombre completo de la moneda (ej: "Dólar Estadounidense")
- ``codigo``: Código ISO 4217 de 3 letras (ej: USD, EUR, PYG) - único
- ``simbolo``: Símbolo de la moneda (ej: $, €, ₲)
- ``decimales``: Número de decimales (0-255, por defecto 2)
- ``monto_limite_transaccion``: Límite máximo por transacción (opcional)
- ``es_activa``: Indica si está habilitada para operaciones
- ``fecha_creacion``: Fecha de creación del registro
- ``fecha_actualizacion``: Fecha de última actualización

**Características especiales:**

- Código ISO automáticamente convertido a mayúsculas
- Soporte para monedas sin decimales (ej: Yen Japonés)
- Soporte para monedas con muchos decimales (ej: criptomonedas)
- Formateo automático según decimales de la moneda

**Métodos principales:**

.. code-block:: python

    # Crear moneda
    usd = Moneda.objects.create(
        nombre='Dólar Estadounidense',
        codigo='USD',
        simbolo='$',
        decimales=2,
        es_activa=True
    )
    
    # Formatear monto
    monto_formateado = usd.formatear_monto(1234.56)
    # Resultado: "1234.56"
    
    # Mostrar monto con símbolo
    monto_con_simbolo = usd.mostrar_monto(1234.56)
    # Resultado: "$1234.56"

**formatear_monto(monto)**

Formatea un monto según el número de decimales de la moneda.

- Respeta los decimales configurados
- Redondea automáticamente
- Retorna string formateado

**mostrar_monto(monto)**

Muestra un monto con el símbolo y formato apropiado.

- Incluye símbolo de la moneda
- Usa formateo de decimales
- Ideal para mostrar en UI

DenominacionMoneda
~~~~~~~~~~~~~~~~~~

Modelo que representa billetes y monedas físicas de cada divisa.

**Campos principales:**

- ``moneda``: Moneda a la que pertenece (ForeignKey)
- ``valor``: Valor de la denominación (ej: 1000, 500, 50)
- ``tipo``: BILLETE o MONEDA
- ``es_activa``: Indica si está en circulación
- ``orden``: Orden de visualización (mayor a menor)
- ``fecha_creacion``: Fecha de creación
- ``fecha_actualizacion``: Fecha de última actualización

**Tipos de denominación:**

- ``BILLETE``: Papel moneda
- ``MONEDA``: Moneda metálica

**Características:**

- Única combinación de moneda, valor y tipo
- Orden automático si no se especifica
- Formateo según decimales de la moneda

**Uso:**

.. code-block:: python

    # Crear denominaciones para PYG
    pyg = Moneda.objects.get(codigo='PYG')
    
    DenominacionMoneda.objects.create(
        moneda=pyg,
        valor=100000,
        tipo='BILLETE',
        es_activa=True
    )
    
    DenominacionMoneda.objects.create(
        moneda=pyg,
        valor=50000,
        tipo='BILLETE',
        es_activa=True
    )
    
    # Obtener denominaciones activas ordenadas
    denominaciones = pyg.denominaciones.filter(
        es_activa=True
    ).order_by('-valor')

**Métodos:**

- ``formatear_valor()``: Formatea el valor según decimales de la moneda
- ``mostrar_denominacion()``: Muestra denominación con símbolo y tipo

Vistas (Views)
--------------

El módulo incluye vistas para gestión de monedas:

**Listado:**

- ``MonedaListView``: Lista de monedas con estado
- Filtros por activa/inactiva
- Búsqueda por nombre y código

**CRUD:**

- ``MonedaCreateView``: Crear nueva moneda
- ``MonedaDetailView``: Detalle de moneda con denominaciones
- ``MonedaUpdateView``: Editar moneda existente
- ``MonedaToggleActiveView``: Activar/desactivar moneda

**Denominaciones:**

- ``DenominacionListView``: Lista de denominaciones por moneda
- ``DenominacionCreateView``: Agregar denominación
- ``DenominacionUpdateView``: Editar denominación
- ``DenominacionDeleteView``: Desactivar denominación

Formularios
-----------

**MonedaForm**

Formulario para crear y editar monedas.

**Validaciones:**

- Código: 3 letras, único, mayúsculas automáticas
- Nombre: Único en el sistema
- Decimales: Valor positivo (0-255)
- Límite transacción: Positivo si se especifica
- Símbolo: Longitud máxima 5 caracteres

**DenominacionForm**

Formulario para gestionar denominaciones.

**Validaciones:**

- Valor: Positivo, formato decimal
- Tipo: BILLETE o MONEDA
- Combinación única: moneda + valor + tipo

Template Tags
-------------

monedas_tags
~~~~~~~~~~~~

Tags personalizados para trabajar con monedas en plantillas.

**formatear_moneda**

Formatea un monto según una moneda específica.

.. code-block:: django

    {% load monedas_tags %}
    
    <p>Monto: {{ monto|formatear_moneda:moneda }}</p>
    <!-- Si monto=1234.56 y moneda=USD → "$1234.56" -->

**simbolo_moneda**

Obtiene el símbolo de una moneda.

.. code-block:: django

    {% load monedas_tags %}
    
    <span>{{ moneda|simbolo_moneda }}</span>
    <!-- Si moneda=EUR → "€" -->

**formato_guaranies**

Formatea guaraníes sin decimales.

.. code-block:: django

    {% load monedas_tags %}
    
    <p>Total: {{ monto|formato_guaranies }}</p>
    <!-- Si monto=1500000 → "₲1.500.000" -->

URLs
----

Rutas definidas en ``monedas/urls.py``:

.. code-block:: python

    urlpatterns = [
        path('', MonedaListView.as_view(), name='moneda_list'),
        path('crear/', MonedaCreateView.as_view(), name='moneda_create'),
        path('<int:pk>/', MonedaDetailView.as_view(), name='moneda_detail'),
        path('<int:pk>/editar/', MonedaUpdateView.as_view(), name='moneda_update'),
        path('<int:pk>/toggle/', MonedaToggleActiveView.as_view(), name='moneda_toggle'),
        
        # Denominaciones
        path('<int:moneda_pk>/denominaciones/', DenominacionListView.as_view(), name='denominacion_list'),
        path('<int:moneda_pk>/denominaciones/crear/', DenominacionCreateView.as_view(), name='denominacion_create'),
        path('denominaciones/<int:pk>/editar/', DenominacionUpdateView.as_view(), name='denominacion_update'),
    ]

Plantillas
----------

Plantillas ubicadas en ``monedas/templates/monedas/``:

- ``moneda_list.html``: Lista de monedas
- ``moneda_detail.html``: Detalle con denominaciones
- ``moneda_form.html``: Formulario crear/editar
- ``denominacion_list.html``: Lista de denominaciones
- ``denominacion_form.html``: Formulario de denominación

Monedas Predeterminadas
------------------------

El sistema soporta monedas comunes:

**PYG - Guaraní Paraguayo**

.. code-block:: python

    Moneda.objects.create(
        nombre='Guaraní Paraguayo',
        codigo='PYG',
        simbolo='₲',
        decimales=0,  # Sin decimales
        es_activa=True
    )

**USD - Dólar Estadounidense**

.. code-block:: python

    Moneda.objects.create(
        nombre='Dólar Estadounidense',
        codigo='USD',
        simbolo='$',
        decimales=2,
        es_activa=True
    )

**EUR - Euro**

.. code-block:: python

    Moneda.objects.create(
        nombre='Euro',
        codigo='EUR',
        simbolo='€',
        decimales=2,
        es_activa=True
    )

**BRL - Real Brasileño**

.. code-block:: python

    Moneda.objects.create(
        nombre='Real Brasileño',
        codigo='BRL',
        simbolo='R$',
        decimales=2,
        es_activa=True
    )

Denominaciones Típicas
-----------------------

**Guaraníes (PYG):**

Billetes: 100.000, 50.000, 20.000, 10.000, 5.000, 2.000
Monedas: 1.000, 500, 100, 50

**Dólares (USD):**

Billetes: 100, 50, 20, 10, 5, 2, 1
Monedas: 1, 0.50, 0.25, 0.10, 0.05, 0.01

Casos de Uso
------------

**Conversión de moneda:**

.. code-block:: python

    from monedas.models import Moneda
    
    usd = Moneda.objects.get(codigo='USD')
    pyg = Moneda.objects.get(codigo='PYG')
    
    # Monto en USD
    monto_usd = 100.00
    
    # Obtener tasa de cambio
    tasa = pyg.tasas_cambio.filter(es_activa=True).first()
    
    # Calcular equivalente en PYG
    monto_pyg = monto_usd * tasa.tasa_venta
    
    # Formatear resultado
    resultado = pyg.mostrar_monto(monto_pyg)

**Calculadora de denominaciones:**

.. code-block:: python

    def calcular_denominaciones(moneda, monto_total):
        """
        Calcula cantidad de billetes/monedas necesarios
        para un monto dado
        """
        denominaciones = moneda.denominaciones.filter(
            es_activa=True
        ).order_by('-valor')
        
        resultado = {}
        monto_restante = monto_total
        
        for denom in denominaciones:
            if monto_restante >= denom.valor:
                cantidad = int(monto_restante // denom.valor)
                resultado[denom] = cantidad
                monto_restante -= cantidad * denom.valor
        
        return resultado, monto_restante

Validaciones y Reglas
---------------------

**Validaciones de negocio:**

- Al desactivar moneda, se desactivan sus tasas de cambio
- No se puede eliminar moneda con transacciones asociadas
- Código ISO debe ser mayúsculas (conversión automática)
- Decimales deben ser apropiados para la moneda

**Restricciones:**

- Mínimo 0 decimales, máximo 255
- Código de 3 letras exactamente
- Nombre y código únicos en el sistema

Integración con Transacciones
------------------------------

Las monedas se integran con el módulo de transacciones:

**Moneda origen/destino:**

.. code-block:: python

    transaccion = Transaccion.objects.create(
        moneda_origen=pyg,
        moneda_destino=usd,
        monto_origen=7500000,
        # Sistema calcula monto_destino según tasa
    )

**Formateo en reportes:**

.. code-block:: python

    # En reporte de transacciones
    for tx in transacciones:
        origen_fmt = tx.moneda_origen.mostrar_monto(tx.monto_origen)
        destino_fmt = tx.moneda_destino.mostrar_monto(tx.monto_destino)

Seguridad y Permisos
--------------------

**Control de acceso:**

- Solo Admin puede crear/editar monedas
- Operadores pueden ver monedas activas
- Visitantes ven monedas públicas

**Auditoría:**

- Registro de cambios de estado
- Tracking de activación/desactivación
- Historial de modificaciones

Pruebas
-------

Pruebas ubicadas en ``monedas/tests.py``:

- Pruebas de creación y validación
- Pruebas de formateo de montos
- Pruebas de denominaciones
- Pruebas de conversión
- Pruebas de template tags

Ejecutar pruebas:

.. code-block:: bash

    poetry run python manage.py test monedas

Management Commands
-------------------

setup_monedas
~~~~~~~~~~~~~

Comando para inicializar monedas predeterminadas.

.. code-block:: bash

    python manage.py setup_monedas

**Funcionalidad:**

- Crea monedas comunes (PYG, USD, EUR, BRL)
- Configura denominaciones estándar
- Es idempotente (no duplica datos)

Consideraciones
---------------

**Performance:**

- Caché de monedas activas
- Índices en código y nombre
- Queries optimizadas para tasas

**Mantenimiento:**

- Revisar monedas obsoletas
- Actualizar denominaciones según circulación
- Monitorear límites de transacción

**Internacionalización:**

- Soporte para múltiples monedas
- Formateo según locale
- Símbolos Unicode correctos

**Extensibilidad:**

El modelo soporta:

- Criptomonedas con muchos decimales
- Monedas históricas o descontinuadas
- Configuración personalizada por país
