Módulo de Grupos
================

El módulo de grupos gestiona roles y permisos en el sistema Global Exchange, extendiendo la funcionalidad nativa de Django con características de activación/desactivación.

Modelo Principal
----------------

Grupo
~~~~~

Modelo personalizado que extiende ``django.contrib.auth.models.Group`` con funcionalidad adicional.

**Campos principales:**

- ``group``: Relación uno a uno con ``django.contrib.auth.models.Group``
- ``es_activo``: Indica si el grupo está activo en el sistema
- ``fecha_creacion``: Fecha de creación del grupo
- ``fecha_modificacion``: Fecha de última modificación

**Propiedades:**

- ``name``: Acceso al nombre del grupo de Django
- ``permissions``: Acceso a los permisos del grupo
- ``user_set``: Acceso a los usuarios del grupo

**Características:**

- Herencia de permisos de Django
- Control de activación/desactivación de permisos
- Auditoría de cambios automática
- Compatibilidad con sistema nativo de permisos

Backend de Autenticación
------------------------

GrupoActivoBackend
~~~~~~~~~~~~~~~~~~

Backend personalizado que solo considera permisos de grupos activos.

**Funcionalidad:**

Sobrescribe los métodos de verificación de permisos para filtrar solo grupos activos:

.. code-block:: python

    from grupos.backends import GrupoActivoBackend
    
    # El backend verifica automáticamente
    if usuario.has_perm('transacciones.add_transaccion'):
        # Solo retorna True si el permiso viene de un grupo activo
        pass

**Métodos implementados:**

- ``has_perm(user_obj, perm, obj=None)``: Verifica permiso específico
- ``has_module_perms(user_obj, app_label)``: Verifica permisos de módulo

**Configuración:**

Agregar en ``settings.py``:

.. code-block:: python

    AUTHENTICATION_BACKENDS = [
        'grupos.backends.GrupoActivoBackend',
        'django.contrib.auth.backends.ModelBackend',
    ]

Mixins para Vistas
------------------

AdminRequiredMixin
~~~~~~~~~~~~~~~~~~

Mixin que requiere que el usuario pertenezca al grupo ``Admin``.

**Uso:**

.. code-block:: python

    from grupos.mixins import AdminRequiredMixin
    from django.views.generic import ListView
    
    class MiVistaProtegida(AdminRequiredMixin, ListView):
        model = MiModelo
        # Solo usuarios del grupo Admin pueden acceder

**Características:**

- Verifica membresía en grupo Admin
- Redirige a login si no autenticado
- Redirige a página de error si no autorizado
- Mensaje de error personalizable

AdminOrStaffRequiredMixin
~~~~~~~~~~~~~~~~~~~~~~~~~

Mixin que requiere que el usuario sea Admin o Operador (staff).

**Uso:**

.. code-block:: python

    from grupos.mixins import AdminOrStaffRequiredMixin
    from django.views.generic import CreateView
    
    class CrearTransaccionView(AdminOrStaffRequiredMixin, CreateView):
        model = Transaccion
        # Admin u Operador pueden crear transacciones

**Características:**

- Verifica membresía en grupo Admin o is_staff=True
- Más flexible que AdminRequiredMixin
- Ideal para operaciones que requieren privilegios elevados

Decoradores
-----------

El módulo proporciona decoradores para vistas basadas en funciones:

grupo_requerido
~~~~~~~~~~~~~~~

.. code-block:: python

    from grupos.decorators import grupo_requerido
    
    @grupo_requerido('Admin')
    def mi_vista_protegida(request):
        # Solo usuarios del grupo Admin pueden acceder
        pass
    
    @grupo_requerido(['Admin', 'Operador'])
    def procesar_transaccion(request):
        # Admin u Operador pueden acceder
        pass

Grupos Predeterminados
----------------------

El sistema define tres grupos principales:

Admin
~~~~~

**Descripción:** Administradores del sistema con acceso completo.

**Permisos típicos:**

- Todos los permisos del sistema
- Gestión de usuarios y grupos
- Configuración del sistema
- Acceso a todas las transacciones
- Gestión de tasas de cambio

**Creación automática:**

Los usuarios creados con ``create_admin_user`` se asignan automáticamente a este grupo.

Operador
~~~~~~~~

**Descripción:** Usuarios que procesan transacciones y operaciones diarias.

**Permisos típicos:**

- Crear y editar transacciones
- Ver clientes y sus datos
- Procesar pagos
- Ver tasas de cambio
- Acceder a reportes operativos

**Restricciones:**

- No puede gestionar usuarios
- No puede cambiar configuración del sistema
- No puede ver todos los registros

Visitante
~~~~~~~~~

**Descripción:** Usuarios con acceso limitado de solo lectura.

**Permisos típicos:**

- Ver tasas de cambio públicas
- Consultar monedas disponibles
- Ver su propio perfil
- Recibir notificaciones de cambios en tasas

**Asignación automática:**

Los usuarios nuevos se asignan automáticamente al grupo Visitante mediante signal.

Vistas (Views)
--------------

El módulo incluye vistas para gestión de grupos:

**Listado:**

- ``GrupoListView``: Lista de grupos con estado
- Filtros por activo/inactivo
- Búsqueda por nombre

**CRUD:**

- ``GrupoCreateView``: Crear nuevo grupo
- ``GrupoUpdateView``: Editar grupo existente
- ``GrupoDeleteView``: Desactivar grupo (soft delete)

**Gestión de permisos:**

- ``GrupoPermissionsView``: Asignar/quitar permisos a grupo
- ``GrupoUsuariosView``: Ver y gestionar usuarios del grupo

Formularios
-----------

**GrupoForm**

Formulario para crear y editar grupos.

.. code-block:: python

    from grupos.forms import GrupoForm
    
    form = GrupoForm(data={
        'name': 'Analista',
        'es_activo': True
    })

**GrupoPermissionsForm**

Formulario para asignar permisos a un grupo.

- Muestra permisos agrupados por aplicación
- Permite selección múltiple
- Validación de permisos válidos

Context Processors
------------------

user_groups
~~~~~~~~~~~

Context processor que agrega información de grupos al contexto de plantillas.

**Uso en plantillas:**

.. code-block:: django

    {% if user in grupos_admin %}
        <a href="{% url 'admin_panel' %}">Panel Admin</a>
    {% endif %}
    
    {% if user in grupos_operador %}
        <a href="{% url 'transacciones' %}">Transacciones</a>
    {% endif %}

**Configuración:**

.. code-block:: python

    TEMPLATES = [
        {
            'OPTIONS': {
                'context_processors': [
                    # ...
                    'grupos.context_processors.user_groups',
                ],
            },
        },
    ]

Template Tags
-------------

El módulo incluye template tags útiles:

has_grupo
~~~~~~~~~

.. code-block:: django

    {% load grupos_tags %}
    
    {% if request.user|has_grupo:"Admin" %}
        <div class="admin-panel">...</div>
    {% endif %}

is_admin
~~~~~~~~

.. code-block:: django

    {% load grupos_tags %}
    
    {% if request.user|is_admin %}
        <button>Configuración</button>
    {% endif %}

URLs
----

Rutas definidas en ``grupos/urls.py``:

.. code-block:: python

    urlpatterns = [
        path('', GrupoListView.as_view(), name='grupo_list'),
        path('crear/', GrupoCreateView.as_view(), name='grupo_create'),
        path('<int:pk>/', GrupoDetailView.as_view(), name='grupo_detail'),
        path('<int:pk>/editar/', GrupoUpdateView.as_view(), name='grupo_update'),
        path('<int:pk>/permisos/', GrupoPermissionsView.as_view(), name='grupo_permissions'),
        path('<int:pk>/usuarios/', GrupoUsuariosView.as_view(), name='grupo_usuarios'),
    ]

Management Commands
-------------------

setup_grupos
~~~~~~~~~~~~

Comando para inicializar grupos predeterminados del sistema.

.. code-block:: bash

    python manage.py setup_grupos

**Funcionalidad:**

- Crea grupos Admin, Operador y Visitante
- Asigna permisos predeterminados a cada grupo
- Es idempotente (puede ejecutarse múltiples veces)
- Registra en logs las acciones realizadas

Permisos Granulares
-------------------

El sistema utiliza los permisos nativos de Django organizados por aplicación:

**Permisos de transacciones:**

- ``transacciones.add_transaccion``
- ``transacciones.change_transaccion``
- ``transacciones.delete_transaccion``
- ``transacciones.view_transaccion``

**Permisos de usuarios:**

- ``usuarios.add_usuario``
- ``usuarios.change_usuario``
- ``usuarios.delete_usuario``
- ``usuarios.view_usuario``

**Permisos de configuración:**

- ``configuracion.change_configuracionsistema``
- ``configuracion.view_configuracionsistema``

Pruebas
-------

Pruebas ubicadas en ``grupos/tests.py``:

- Pruebas de creación de grupos
- Pruebas de backend de permisos
- Pruebas de mixins
- Pruebas de decoradores
- Pruebas de asignación automática
- Pruebas de activación/desactivación

Ejecutar pruebas:

.. code-block:: bash

    poetry run python manage.py test grupos

Seguridad
---------

**Consideraciones:**

- Desactivar un grupo suspende todos sus permisos inmediatamente
- Los usuarios mantienen su asociación al grupo desactivado
- El backend filtra automáticamente grupos inactivos
- Auditoría de cambios en permisos

**Mejores prácticas:**

- Usar grupos en lugar de permisos directos a usuarios
- Revisar periódicamente permisos asignados
- Documentar cambios en permisos de grupos
- Probar permisos en entorno de desarrollo

Integración
-----------

El módulo se integra con:

- ``usuarios``: Gestión de usuarios y sus grupos
- ``auth``: Backend de autenticación y permisos
- Todas las apps: Control de acceso granular

Migración desde Roles
---------------------

Este módulo reemplaza el módulo ``roles`` deprecated:

**Cambios principales:**

- Uso de grupos nativos de Django
- Backend personalizado para filtrado
- Sistema más robusto y mantenible
- Mejor integración con admin de Django

**Guía de migración:**

Si tu proyecto usaba ``roles``, debes:

1. Migrar roles a grupos equivalentes
2. Actualizar referencias en código
3. Cambiar decoradores y mixins
4. Actualizar plantillas
5. Probar exhaustivamente permisos

Consideraciones
---------------

**Performance:**

- Caché de permisos por usuario
- Índices en campos de búsqueda
- Queries optimizadas para verificación de permisos

**Mantenimiento:**

- Revisar grupos activos periódicamente
- Auditar cambios de permisos
- Documentar política de permisos
- Mantener grupos predeterminados sincronizados

**Extensibilidad:**

Puede extenderse con:

- Grupos dinámicos basados en reglas
- Permisos basados en objetos (object-level)
- Integración con LDAP o Active Directory
- Jerarquía de grupos
