Módulo de Clientes
==================

El módulo de clientes gestiona la información de clientes corporativos del sistema Global Exchange, incluyendo tipos de cliente, descuentos y asociación con usuarios operadores.

Modelos Principales
------------------

TipoCliente
~~~~~~~~~~~

Define categorías de clientes con descuentos diferenciados.

**Campos principales:**

- ``nombre``: Nombre único del tipo (ej: "Premium", "Corporativo")
- ``descripcion``: Descripción detallada del tipo
- ``descuento``: Porcentaje de descuento (0-100%) con 2 decimales
- ``activo``: Indica si el tipo está habilitado
- ``fecha_creacion``: Fecha de creación del registro
- ``fecha_modificacion``: Fecha de última modificación

**Características:**

- Descuentos personalizados por tipo
- Activación/desactivación sin eliminar datos
- Auditoría automática de cambios

**Uso:**

.. code-block:: python

    tipo_premium = TipoCliente.objects.create(
        nombre='Premium',
        descripcion='Clientes con alto volumen de transacciones',
        descuento=5.00,  # 5% de descuento
        activo=True
    )

Cliente
~~~~~~~

Modelo principal que representa clientes corporativos del sistema.

**Identificación:**

- ``nombre_comercial``: Nombre comercial o razón social
- ``ruc``: Número de RUC único (5-20 dígitos)
- ``dv``: Dígito verificador del RUC (opcional)

**Información de contacto:**

- ``direccion``: Dirección completa
- ``correo_electronico``: Email de contacto
- ``numero_telefono``: Teléfono de contacto

**Relaciones:**

- ``tipo_cliente``: Tipo de cliente (determina descuento)
- ``usuarios_asociados``: Usuarios que pueden operar por el cliente (ManyToMany)

**Control de operaciones:**

- ``monto_limite_transaccion``: Límite máximo por transacción (opcional)
- ``activo``: Indica si el cliente está habilitado
- ``fecha_creacion``: Fecha de creación
- ``fecha_modificacion``: Fecha de última modificación

**Validaciones:**

- RUC: Solo números, 5-20 dígitos, único en el sistema
- DV: Un solo dígito numérico
- Teléfono: Números, espacios, guiones, paréntesis y símbolo +
- Email: Formato válido de email

**Índices optimizados:**

- RUC (búsqueda rápida)
- Nombre comercial (filtrado y búsqueda)
- Tipo de cliente (agrupación)
- Estado activo (filtrado)

**Permisos personalizados:**

- ``can_view_all_clients``: Ver todos los clientes
- ``can_view_sensitive_columns``: Ver datos sensibles (usuarios, estado, fechas)

Signals
-------

gestionar_rol_operador
~~~~~~~~~~~~~~~~~~~~~~

Signal que gestiona automáticamente el rol de Operador basado en asignación de clientes.

**Funcionalidad:**

Cuando se asocia un cliente a un usuario:
  - Usuario recibe automáticamente el rol ``Operador``
  - Permite procesar transacciones en nombre del cliente

Cuando un usuario se queda sin clientes:
  - Se remueve automáticamente el rol ``Operador``
  - Mantiene otros roles asignados

**Eventos que disparan el signal:**

- ``post_add``: Usuario agregado a cliente → Asignar rol Operador
- ``post_remove``: Usuario removido de cliente → Verificar y quitar rol si no tiene más clientes
- ``post_clear``: Todos los usuarios removidos → Verificar cada usuario afectado

**Lógica:**

.. code-block:: python

    # Al asociar usuario a cliente
    cliente.usuarios_asociados.add(usuario)
    # → Signal asigna grupo Operador automáticamente
    
    # Al remover último cliente de un usuario
    cliente.usuarios_asociados.remove(usuario)
    # → Signal verifica y remueve grupo Operador si no tiene más clientes

Vistas (Views)
--------------

El módulo incluye vistas completas para gestión de clientes:

**Listado y búsqueda:**

- ``ClienteListView``: Lista paginada con filtros
- Filtros por: tipo, estado activo, búsqueda por nombre/RUC
- Paginación configurable

**CRUD:**

- ``ClienteCreateView``: Crear nuevo cliente
- ``ClienteDetailView``: Ver detalle completo
- ``ClienteUpdateView``: Editar cliente existente
- ``ClienteDeleteView``: Desactivar cliente (soft delete)

**Gestión de usuarios:**

- ``ClienteUsuariosView``: Asignar/quitar usuarios asociados
- Verificación de permisos por cliente

Formularios
-----------

**ClienteForm**

Formulario completo para crear y editar clientes.

**Validaciones:**

- RUC: Formato válido, único en el sistema
- DV: Un dígito si se proporciona
- Tipo cliente: Debe estar activo
- Teléfono: Formato válido
- Email: Formato válido
- Monto límite: Positivo si se especifica

**Widgets personalizados:**

- Select2 para tipo de cliente
- Select2 múltiple para usuarios asociados
- Máscaras de entrada para RUC y teléfono

**TipoClienteForm**

Formulario para gestionar tipos de cliente.

**Validaciones:**

- Nombre único
- Descuento entre 0 y 100%
- Formato de porcentaje con 2 decimales

Context Processors
------------------

cliente_info
~~~~~~~~~~~~

Agrega información del cliente asociado al contexto de plantillas.

**Variables disponibles:**

- ``cliente_actual``: Cliente asociado al usuario actual
- ``es_operador_cliente``: Boolean indicando si es operador
- ``tipo_cliente_descuento``: Descuento aplicable

**Uso en plantillas:**

.. code-block:: django

    {% if cliente_actual %}
        <div class="cliente-badge">
            <span>Cliente: {{ cliente_actual.nombre_comercial }}</span>
            <span>Descuento: {{ tipo_cliente_descuento }}%</span>
        </div>
    {% endif %}

Widgets Personalizados
-----------------------

El módulo incluye widgets para mejorar UX:

**RUCWidget**

Widget con máscara de entrada para RUC.

- Formato automático de RUC
- Validación en tiempo real
- Separador de DV automático

**TelefonoWidget**

Widget para números de teléfono.

- Formato automático con código de país
- Validación de longitud
- Caracteres permitidos: + ( ) - y espacios

URLs
----

Rutas definidas en ``clientes/urls.py``:

.. code-block:: python

    urlpatterns = [
        path('', ClienteListView.as_view(), name='cliente_list'),
        path('crear/', ClienteCreateView.as_view(), name='cliente_create'),
        path('<int:pk>/', ClienteDetailView.as_view(), name='cliente_detail'),
        path('<int:pk>/editar/', ClienteUpdateView.as_view(), name='cliente_update'),
        path('<int:pk>/eliminar/', ClienteDeleteView.as_view(), name='cliente_delete'),
        path('<int:pk>/usuarios/', ClienteUsuariosView.as_view(), name='cliente_usuarios'),
        
        # Tipos de cliente
        path('tipos/', TipoClienteListView.as_view(), name='tipocliente_list'),
        path('tipos/crear/', TipoClienteCreateView.as_view(), name='tipocliente_create'),
        path('tipos/<int:pk>/editar/', TipoClienteUpdateView.as_view(), name='tipocliente_update'),
    ]

Plantillas
----------

Plantillas ubicadas en ``clientes/templates/clientes/``:

**Clientes:**

- ``cliente_list.html``: Lista con filtros y búsqueda
- ``cliente_detail.html``: Detalle completo del cliente
- ``cliente_form.html``: Formulario crear/editar
- ``cliente_confirm_delete.html``: Confirmación de eliminación

**Tipos de cliente:**

- ``tipocliente_list.html``: Lista de tipos
- ``tipocliente_form.html``: Formulario de tipo

**Componentes:**

- ``_cliente_card.html``: Card de cliente para listados
- ``_usuarios_asociados.html``: Lista de usuarios asociados

Casos de Uso
------------

**Registro de cliente corporativo:**

1. Admin crea tipo de cliente con descuento
2. Admin registra cliente con tipo asignado
3. Admin asocia usuarios operadores al cliente
4. Signal asigna rol Operador automáticamente
5. Usuario puede operar en nombre del cliente

**Transacción con descuento:**

1. Operador asociado procesa transacción
2. Sistema identifica cliente del operador
3. Aplica descuento del tipo de cliente
4. Calcula monto final con descuento

**Gestión de límites:**

1. Admin configura monto límite por transacción
2. Sistema valida monto en cada transacción
3. Rechaza transacciones que excedan el límite
4. Genera alerta para límites alcanzados

Integración con Transacciones
------------------------------

El módulo se integra estrechamente con transacciones:

**Aplicación de descuentos:**

.. code-block:: python

    # En transaccion.calcular_total_final()
    if self.cliente and self.cliente.tipo_cliente:
        descuento = self.cliente.tipo_cliente.descuento
        self.porcentaje_descuento = descuento
        self.monto_descuento = (self.monto_comision * descuento) / 100

**Validación de límites:**

.. code-block:: python

    # En transaccion.clean()
    if self.cliente and self.cliente.monto_limite_transaccion:
        if self.monto_origen > self.cliente.monto_limite_transaccion:
            raise ValidationError('Monto excede límite del cliente')

Reportes y Análisis
-------------------

El módulo soporta generación de reportes:

**Reportes de cliente:**

- Transacciones por período
- Total operado por tipo de cliente
- Descuentos otorgados
- Usuarios activos por cliente

**Métricas:**

- Clientes activos vs inactivos
- Distribución por tipo de cliente
- Promedio de transacciones por cliente
- Descuentos totales aplicados

Seguridad y Permisos
--------------------

**Control de acceso:**

- Solo Admin puede crear/editar clientes
- Operadores solo ven sus clientes asociados
- Permisos granulares para datos sensibles

**Validaciones de seguridad:**

- RUC único en el sistema
- Usuarios asociados deben estar activos
- Tipo de cliente debe estar activo
- Validación de límites de transacción

Pruebas
-------

Pruebas ubicadas en ``clientes/tests.py``:

- Pruebas de modelos y validaciones
- Pruebas de signal de rol Operador
- Pruebas de formularios
- Pruebas de vistas y permisos
- Pruebas de integración con transacciones

Ejecutar pruebas:

.. code-block:: bash

    poetry run python manage.py test clientes

Consideraciones
---------------

**Performance:**

- Índices en campos de búsqueda frecuente
- Optimización de queries con select_related
- Caché de tipos de cliente activos

**Mantenimiento:**

- Revisar periódicamente clientes inactivos
- Auditar cambios de descuentos
- Monitorear usuarios asociados

**Escalabilidad:**

- Sistema preparado para múltiples clientes
- Soporte para jerarquía de tipos de cliente
- Extensible con campos personalizados

Migraciones de Datos
--------------------

Al migrar datos de clientes:

1. Importar tipos de cliente primero
2. Validar RUCs antes de importar
3. Crear clientes sin usuarios asociados
4. Asociar usuarios después de validar
5. Verificar asignación de roles automática

**Script de ejemplo:**

.. code-block:: python

    # scripts/importar_clientes.py
    from clientes.models import Cliente, TipoCliente
    
    tipo_premium = TipoCliente.objects.get(nombre='Premium')
    
    cliente = Cliente.objects.create(
        nombre_comercial='Empresa XYZ',
        ruc='80012345',
        dv='6',
        tipo_cliente=tipo_premium
    )
    
    # Asociar usuarios (dispara signal)
    cliente.usuarios_asociados.add(usuario1, usuario2)
