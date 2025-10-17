Módulo de Roles
===============

El módulo de roles es una estructura placeholder que ha sido reemplazada por el sistema de grupos de Django integrado en el módulo ``grupos``.

Descripción General
-------------------

Históricamente, este módulo contenía la gestión de roles del sistema. Sin embargo, el proyecto evolucionó para utilizar el sistema nativo de grupos y permisos de Django, centralizado en la app ``grupos``.

Estado Actual
-------------

El directorio ``roles/`` existe principalmente para:

- Mantener compatibilidad con referencias históricas en el código
- Posibles migraciones de datos legacy
- Estructura de comandos de management (actualmente vacía)

Funcionalidad Migrada
---------------------

La funcionalidad que anteriormente residía en este módulo ahora se encuentra en:

**Módulo grupos**
~~~~~~~~~~~~~~~~~

- ``grupos.models.Grupo``: Modelo que envuelve ``django.contrib.auth.models.Group``
- ``grupos.backends.GrupoActivoBackend``: Backend de autenticación personalizado
- ``grupos.mixins``: Mixins para control de acceso basado en grupos

**Roles del Sistema**
~~~~~~~~~~~~~~~~~~~~~

Los roles principales del sistema son:

- **Admin**: Acceso total al sistema
- **Staff**: Personal con permisos intermedios
- **Operador**: Usuarios operativos con permisos de transacciones
- **Visitante**: Usuarios con acceso de solo lectura

**Gestión de Permisos**
~~~~~~~~~~~~~~~~~~~~~~~

Los permisos se gestionan mediante:

.. code-block:: python

   from django.contrib.auth.models import Group, Permission

   # Obtener grupo
   admin_group = Group.objects.get(name='Admin')
   
   # Asignar permisos
   admin_group.permissions.add(permiso)

**Verificación de Permisos**
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

.. code-block:: python

   # En vistas
   from grupos.mixins import AdminRequiredMixin
   
   class MiVista(AdminRequiredMixin, View):
       ...
   
   # En templates
   {% if user.groups.filter(name='Admin').exists %}
       <!-- Contenido para admins -->
   {% endif %}

Referencias en el Código
-------------------------

El módulo ``roles`` aparece mencionado en:

- ``AGENTS.md``: Documentación de agentes IA
- Fixtures históricos (si existen)
- Comandos de management legacy

Sin embargo, toda la funcionalidad activa está en ``grupos/``.

Migración a Grupos
------------------

Si encuentras código que importa de ``roles``, debes migrarlo a ``grupos``:

**Antes:**

.. code-block:: python

   from roles.services import RolesService
   
   if RolesService.usuario_tiene_permiso(user, 'tipocliente_leer'):
       ...

**Después:**

.. code-block:: python

   if user.has_perm('clientes.view_tipocliente'):
       ...

O usando el sistema de grupos:

.. code-block:: python

   if user.groups.filter(name__in=['Admin', 'Operador']).exists():
       ...

Comandos de Management
----------------------

El directorio ``roles/management/commands/`` está vacío actualmente. Comandos relacionados con roles y grupos se encuentran en:

- ``grupos/management/commands/``: Comandos para gestión de grupos

Recomendaciones
---------------

1. **No agregar nueva funcionalidad aquí**: Usar el módulo ``grupos`` en su lugar
2. **Deprecar referencias**: Actualizar código que aún referencie ``roles``
3. **Documentar migraciones**: Si hay datos legacy, documentar proceso de migración
4. **Considerar eliminación**: Si no hay dependencias, considerar remover el módulo

Consultar Documentación de Grupos
----------------------------------

Para información detallada sobre gestión de roles y permisos, consultar:

- :doc:`apps`: Sección de **grupos**
- :doc:`security-permissions`: Permisos y control de acceso
- Django documentation: ``django.contrib.auth.models.Group``

Notas Históricas
----------------

Este módulo existe por razones de compatibilidad y estructura del proyecto. La decisión de migrar a grupos de Django se tomó para:

- Aprovechar el sistema robusto y probado de Django
- Reducir código custom y mantenimiento
- Mejorar integración con el admin de Django
- Facilitar testing y documentación

**Fecha de migración**: Sprint 1-2 (2025)

**Estado**: Deprecated - Usar ``grupos`` en su lugar
