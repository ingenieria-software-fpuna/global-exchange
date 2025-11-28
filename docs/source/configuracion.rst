Módulo de Configuración
=======================

El módulo de configuración gestiona los parámetros globales del sistema Global Exchange, permitiendo establecer límites y restricciones para las operaciones de la casa de cambio.

Descripción General
-------------------

Este módulo implementa un patrón Singleton para mantener una única instancia de configuración del sistema. Permite a los administradores configurar límites operacionales que afectan el comportamiento de todas las transacciones.

Modelos Principales
-------------------

ConfiguracionSistema
~~~~~~~~~~~~~~~~~~~~

Modelo Singleton que almacena la configuración global del sistema.

**Campos principales:**

- ``limite_diario_transacciones``: Monto máximo permitido para transacciones por día (decimal 12,2)
- ``limite_mensual_transacciones``: Monto máximo permitido para transacciones por mes (decimal 12,2)
- ``fecha_creacion``: Fecha y hora de creación del registro (auto_now_add)
- ``fecha_actualizacion``: Fecha y hora de última modificación (auto_now)

**Validaciones:**

- Ambos límites deben ser mayores o iguales a 0 (MinValueValidator)
- El valor 0 indica "sin límite"

**Configuración del modelo:**

- ``verbose_name``: "Configuración del Sistema"
- ``verbose_name_plural``: "Configuraciones del Sistema"
- ``db_table``: 'configuracion_sistema'

Métodos de Clase
----------------

**get_configuracion()**

Método de clase que obtiene la configuración del sistema, creando una instancia por defecto si no existe.

.. code-block:: python

   from configuracion.models import ConfiguracionSistema

   config = ConfiguracionSistema.get_configuracion()
   print(f"Límite diario: {config.limite_diario_transacciones}")
   print(f"Límite mensual: {config.limite_mensual_transacciones}")

**Retorna:**

- Instancia de ``ConfiguracionSistema`` (única en el sistema)

**Comportamiento:**

- Si no existe configuración, crea una con valores por defecto (0, 0)
- Siempre retorna la misma instancia (patrón Singleton)

ContadorDocumentoFactura
~~~~~~~~~~~~~~~~~~~~~~~~

Modelo Singleton que gestiona el contador auto-incremental para números de documentos de facturas electrónicas.

**Campos principales:**

- ``numero_actual``: Número actual del documento (default: 501)
- ``numero_minimo``: Número mínimo permitido del rango (default: 501)
- ``numero_maximo``: Número máximo permitido del rango (default: 550)
- ``formato_longitud``: Cantidad de dígitos para formatear (default: 7)
- ``fecha_creacion``: Fecha de creación del registro
- ``fecha_actualizacion``: Fecha de última actualización

**Validaciones:**

- ``numero_actual`` debe estar entre ``numero_minimo`` y ``numero_maximo``
- ``numero_minimo`` no puede ser mayor que ``numero_maximo``
- Solo puede existir una instancia del contador (Singleton)

**Configuración del modelo:**

- ``verbose_name``: "Contador de Documentos de Factura"
- ``verbose_name_plural``: "Contadores de Documentos de Factura"
- ``db_table``: 'contador_documento_factura'

**Métodos principales:**

get_numero_formateado()
^^^^^^^^^^^^^^^^^^^^^^^

Retorna el número actual formateado con ceros a la izquierda.

.. code-block:: python

   contador = ContadorDocumentoFactura.get_contador()
   numero_fmt = contador.get_numero_formateado()
   # Resultado: "0000501" (si numero_actual=501 y formato_longitud=7)

obtener_siguiente_numero()
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Método de clase thread-safe que obtiene el siguiente número de documento.

**Características:**

- Usa ``select_for_update()`` para bloqueo a nivel de base de datos
- Garantiza thread-safety en entornos concurrentes
- Incrementa automáticamente el contador
- Valida que no se exceda el máximo del rango
- Retorna el número formateado

**Uso:**

.. code-block:: python

   from configuracion.models import ContadorDocumentoFactura
   
   try:
       numero_doc = ContadorDocumentoFactura.obtener_siguiente_numero()
       print(f"Número de documento: {numero_doc}")
       # Resultado: "0000501"
   except ValidationError as e:
       print(f"Error: {e}")
       # Error si se alcanzó el límite máximo

**Excepciones:**

- ``ValidationError``: Si se alcanzó el límite máximo del rango

get_contador()
^^^^^^^^^^^^^^

Método de clase que obtiene el contador actual, creando uno por defecto si no existe.

.. code-block:: python

   contador = ContadorDocumentoFactura.get_contador()
   print(f"Rango: {contador.numero_minimo}-{contador.numero_maximo}")
   print(f"Actual: {contador.numero_actual}")

**Retorna:**

- Instancia de ``ContadorDocumentoFactura``

**Ejemplo de uso en facturación:**

.. code-block:: python

   from configuracion.models import ContadorDocumentoFactura
   from django.core.exceptions import ValidationError
   
   def generar_factura(transaccion, cliente):
       try:
           # Obtener siguiente número de documento
           numero_doc = ContadorDocumentoFactura.obtener_siguiente_numero()
           
           # Usar número en factura
           factura = {
               'numero_documento': numero_doc,
               'transaccion': transaccion,
               'cliente': cliente,
               # ... otros campos
           }
           
           return factura
       except ValidationError:
           # Límite alcanzado - notificar administrador
           raise Exception("Rango de numeración agotado. Contacte al administrador.")

Métodos de Instancia
--------------------

**save()**

Sobrescribe el método save para asegurar el patrón Singleton.

**Comportamiento:**

- Si intenta crear una nueva instancia cuando ya existe una, actualiza la existente
- Garantiza que solo exista una configuración en el sistema
- Preserva los valores históricos de fecha_creacion

.. code-block:: python

   # Primera vez: crea la configuración
   config1 = ConfiguracionSistema()
   config1.limite_diario_transacciones = 100000
   config1.save()

   # Segunda vez: actualiza la existente (no crea nueva)
   config2 = ConfiguracionSistema()
   config2.limite_diario_transacciones = 200000
   config2.save()

   # Verifica que solo hay una instancia
   assert ConfiguracionSistema.objects.count() == 1

Formularios
-----------

ConfiguracionSistemaForm
~~~~~~~~~~~~~~~~~~~~~~~~

Formulario ModelForm para editar la configuración del sistema.

**Campos:**

- ``limite_diario_transacciones``: DecimalField con widget NumberInput
- ``limite_mensual_transacciones``: DecimalField con widget NumberInput

**Validaciones personalizadas:**

- Ambos campos deben ser >= 0
- El límite mensual debe ser >= límite diario (validación en clean())

**Widgets:**

.. code-block:: python

   attrs={
       'class': 'form-control',
       'step': '0.01',
       'min': '0',
       'placeholder': '0.00'
   }

**Ejemplo de uso:**

.. code-block:: python

   from configuracion.forms import ConfiguracionSistemaForm
   from configuracion.models import ConfiguracionSistema

   config = ConfiguracionSistema.get_configuracion()
   form = ConfiguracionSistemaForm(request.POST, instance=config)
   
   if form.is_valid():
       form.save()

**Validación de coherencia:**

Si el límite mensual es menor que el límite diario, el formulario genera un error:

.. code-block:: python

   # Esto generará un error de validación
   form_data = {
       'limite_diario_transacciones': 10000,
       'limite_mensual_transacciones': 5000  # Menor que diario!
   }
   form = ConfiguracionSistemaForm(data=form_data)
   assert not form.is_valid()

Vistas
------

configuracion_view
~~~~~~~~~~~~~~~~~~

Vista funcional para mostrar y actualizar la configuración del sistema.

**Decoradores:**

- ``@login_required``: Requiere autenticación
- ``@permission_required('configuracion.change_configuracionsistema')``: Requiere permiso de cambio

**Parámetros:**

- ``request``: HttpRequest

**Retorna:**

- GET: Renderiza formulario con configuración actual
- POST válido: Guarda cambios, muestra mensaje de éxito y redirige
- POST inválido: Renderiza formulario con errores

**Contexto de template:**

- ``form``: Instancia de ConfiguracionSistemaForm
- ``configuracion``: Instancia actual de ConfiguracionSistema
- ``titulo``: "Configuración del Sistema"

**Flujo de operación:**

.. code-block:: python

   # 1. Obtiene la configuración única del sistema
   configuracion = ConfiguracionSistema.get_configuracion()

   # 2. En POST: valida y guarda
   if request.method == 'POST':
       form = ConfiguracionSistemaForm(request.POST, instance=configuracion)
       if form.is_valid():
           form.save()
           messages.success(request, 'Configuración actualizada correctamente.')
           return redirect('configuracion:configuracion')

   # 3. En GET: muestra formulario
   else:
       form = ConfiguracionSistemaForm(instance=configuracion)

**URLs:**

- Ruta: ``configuracion/``
- Name: ``configuracion:configuracion``

Casos de Uso
------------

**Establecer límites de transacciones**

Configurar límites para controlar el volumen operacional:

.. code-block:: python

   config = ConfiguracionSistema.get_configuracion()
   config.limite_diario_transacciones = 50000.00  # 50,000 PYG
   config.limite_mensual_transacciones = 1000000.00  # 1,000,000 PYG
   config.save()

**Remover límites**

Establecer en 0 para operación sin restricciones:

.. code-block:: python

   config = ConfiguracionSistema.get_configuracion()
   config.limite_diario_transacciones = 0  # Sin límite diario
   config.limite_mensual_transacciones = 0  # Sin límite mensual
   config.save()

**Verificar configuración actual**

.. code-block:: python

   config = ConfiguracionSistema.get_configuracion()
   
   if config.limite_diario_transacciones > 0:
       print(f"Límite diario activo: {config.limite_diario_transacciones}")
   else:
       print("Sin límite diario")

   if config.limite_mensual_transacciones > 0:
       print(f"Límite mensual activo: {config.limite_mensual_transacciones}")
   else:
       print("Sin límite mensual")

Permisos Requeridos
-------------------

**Vista de configuración:**

- ``configuracion.change_configuracionsistema``: Permiso para modificar la configuración

Típicamente asignado a:

- Grupo **Admin**: Configuración completa del sistema
- Usuarios con rol de administración general

Integración con Transacciones
------------------------------

El módulo de transacciones consulta esta configuración para validar límites:

.. code-block:: python

   from configuracion.models import ConfiguracionSistema
   from django.db.models import Sum
   from datetime import date, timedelta

   config = ConfiguracionSistema.get_configuracion()
   
   # Verificar límite diario
   if config.limite_diario_transacciones > 0:
       hoy = date.today()
       total_hoy = Transaccion.objects.filter(
           fecha_creacion__date=hoy
       ).aggregate(Sum('monto_origen'))['monto_origen__sum'] or 0
       
       if total_hoy >= config.limite_diario_transacciones:
           raise ValidationError("Límite diario alcanzado")

   # Verificar límite mensual
   if config.limite_mensual_transacciones > 0:
       inicio_mes = date.today().replace(day=1)
       total_mes = Transaccion.objects.filter(
           fecha_creacion__date__gte=inicio_mes
       ).aggregate(Sum('monto_origen'))['monto_origen__sum'] or 0
       
       if total_mes >= config.limite_mensual_transacciones:
           raise ValidationError("Límite mensual alcanzado")

Consideraciones de Diseño
--------------------------

**Patrón Singleton:**

- Solo existe una instancia de configuración en la base de datos
- El método ``save()`` asegura esta restricción
- ``get_configuracion()`` siempre retorna la misma instancia

**Valores por defecto:**

- Límites en 0 indican "sin restricción"
- Permite operación normal sin configuración explícita

**Auditoría:**

- ``fecha_creacion``: Registra cuándo se creó la configuración inicial
- ``fecha_actualizacion``: Se actualiza automáticamente en cada cambio

**Validación en múltiples capas:**

1. Modelo: MinValueValidator >= 0
2. Formulario: Validación de coherencia entre límites
3. Vista: Permisos de acceso

Plantillas
----------

**configuracion/configuracion.html**

Plantilla que muestra el formulario de configuración del sistema.

**Elementos esperados:**

- Formulario Bootstrap con campos de configuración
- Botón de guardar cambios
- Mensajes de éxito/error (Django messages framework)
- Breadcrumbs de navegación

**Ejemplo de estructura:**

.. code-block:: html

   {% extends "base.html" %}

   {% block content %}
   <h1>{{ titulo }}</h1>
   
   <form method="post">
       {% csrf_token %}
       {{ form.as_p }}
       <button type="submit" class="btn btn-primary">Guardar Cambios</button>
   </form>
   {% endblock %}

Buenas Prácticas
----------------

1. **Siempre usar get_configuracion()**: No crear instancias directamente
2. **Validar antes de aplicar límites**: Verificar que el límite sea > 0
3. **Considerar zona horaria**: Al calcular totales diarios/mensuales
4. **Documentar cambios**: Los cambios de límites pueden afectar operaciones críticas
5. **Notificar usuarios**: Informar a operadores sobre cambios en límites

Pruebas
-------

**Pruebas recomendadas:**

- Creación de configuración única (Singleton)
- Validación de límites negativos (debe fallar)
- Validación de coherencia mensual >= diario
- Permisos de acceso a la vista
- Actualización correcta de valores

**Ejemplo de test:**

.. code-block:: python

   from django.test import TestCase
   from configuracion.models import ConfiguracionSistema

   class ConfiguracionSistemaTest(TestCase):
       def test_singleton_pattern(self):
           """Verifica que solo se crea una instancia"""
           config1 = ConfiguracionSistema.get_configuracion()
           config2 = ConfiguracionSistema.get_configuracion()
           self.assertEqual(config1.pk, config2.pk)
           self.assertEqual(ConfiguracionSistema.objects.count(), 1)

       def test_limite_validacion(self):
           """Verifica validación de límites"""
           config = ConfiguracionSistema.get_configuracion()
           config.limite_diario_transacciones = 100
           config.limite_mensual_transacciones = 50  # Menor que diario
           
           from configuracion.forms import ConfiguracionSistemaForm
           form = ConfiguracionSistemaForm(instance=config, data={
               'limite_diario_transacciones': 100,
               'limite_mensual_transacciones': 50
           })
           self.assertFalse(form.is_valid())
