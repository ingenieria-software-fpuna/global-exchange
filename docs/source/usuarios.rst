Módulo de Usuarios
==================

El módulo de usuarios gestiona la información y autenticación de los usuarios del sistema Global Exchange.

Modelo Principal
----------------

Usuario
~~~~~~~

Modelo personalizado que extiende ``AbstractBaseUser`` y ``PermissionsMixin`` de Django.

**Campos principales:**

- ``email``: Correo electrónico único (usado como username)
- ``cedula``: Cédula de identidad única
- ``nombre``: Nombre del usuario
- ``apellido``: Apellido del usuario
- ``fecha_nacimiento``: Fecha de nacimiento
- ``activo``: Indica si el correo está verificado
- ``es_activo``: Indica si el usuario está activo en el sistema
- ``is_staff``: Indica si puede acceder al admin de Django
- ``recibir_notificaciones_email``: Preferencia de notificaciones
- ``fecha_creacion``: Fecha de creación del registro
- ``fecha_actualizacion``: Fecha de última actualización

**Características especiales:**

- Autenticación por email (no por username)
- Campos obligatorios: email, nombre, cedula, fecha_nacimiento
- Sistema de grupos y permisos integrado
- Auditoría automática de cambios

Manager Personalizado
---------------------

UsuarioManager
~~~~~~~~~~~~~~

Manager personalizado con métodos especializados para creación de usuarios.

**Métodos principales:**

.. code-block:: python

    # Crear usuario regular
    usuario = Usuario.objects.create_user(
        email='usuario@example.com',
        password='contraseña_segura',
        nombre='Juan',
        apellido='Pérez',
        cedula='1234567',
        fecha_nacimiento='1990-01-01'
    )
    
    # Crear usuario administrador
    admin = Usuario.objects.create_admin_user(
        email='admin@example.com',
        password='admin_password',
        nombre='Admin',
        apellido='Sistema',
        cedula='7654321',
        fecha_nacimiento='1985-01-01'
    )

**create_user(email, password, **extra_fields)**

Crea un usuario regular del sistema.

- Normaliza el email
- Encripta la contraseña automáticamente
- Valida que el email esté presente
- Guarda el usuario en la base de datos

**create_admin_user(email, password, **extra_fields)**

Crea un usuario administrador con permisos especiales.

- Crea el usuario con ``is_staff=True``
- Lo asigna automáticamente al grupo ``Admin``
- No usa ``is_superuser`` (se prefiere gestión por grupos)
- Retorna el usuario creado con permisos de administración

Señales (Signals)
-----------------

asignar_grupo_visitante
~~~~~~~~~~~~~~~~~~~~~~~

Signal que se ejecuta automáticamente después de crear un usuario.

**Funcionalidad:**

- Se activa con ``post_save`` del modelo Usuario
- Solo actúa cuando se crea un usuario nuevo (``created=True``)
- Asigna automáticamente el grupo ``Visitante`` si el usuario no tiene grupos
- Registra la asignación en logs

**Flujo:**

1. Usuario es creado
2. Signal verifica que es creación nueva
3. Busca o crea grupo ``Visitante``
4. Verifica que usuario no tenga grupos
5. Asigna grupo ``Visitante`` automáticamente

Vistas (Views)
--------------

El módulo incluye vistas para gestión de usuarios:

**Listado y detalle:**

- ``UsuarioListView``: Lista paginada de usuarios
- ``UsuarioDetailView``: Detalle de un usuario específico

**CRUD:**

- ``UsuarioCreateView``: Crear nuevo usuario
- ``UsuarioUpdateView``: Editar usuario existente
- ``UsuarioDeleteView``: Desactivar usuario (soft delete)

**Perfil:**

- ``PerfilView``: Ver y editar perfil del usuario actual
- ``CambiarPasswordView``: Cambio de contraseña seguro

Formularios
-----------

**UsuarioCreationForm**

Formulario para crear nuevos usuarios con validaciones.

- Validación de formato de email
- Validación de formato de cédula
- Confirmación de contraseña
- Validación de edad mínima (18 años)

**UsuarioUpdateForm**

Formulario para actualizar datos de usuario existente.

- Campos editables: nombre, apellido, fecha_nacimiento
- Validaciones de integridad
- Protección contra cambios no autorizados

**CambiarPasswordForm**

Formulario para cambio seguro de contraseña.

- Validación de contraseña actual
- Confirmación de nueva contraseña
- Validación de complejidad de contraseña

Permisos y Grupos
-----------------

El sistema de usuarios se integra con el módulo de grupos:

**Grupos predeterminados:**

- ``Admin``: Acceso completo al sistema
- ``Operador``: Procesar transacciones
- ``Visitante``: Acceso limitado, consultas

**Verificación de permisos:**

.. code-block:: python

    # Verificar si usuario tiene permiso
    if usuario.has_perm('usuarios.add_usuario'):
        # Permitir acción
        pass
    
    # Verificar si usuario pertenece a un grupo
    if usuario.groups.filter(name='Admin').exists():
        # Usuario es administrador
        pass

URLs
----

Rutas definidas en ``usuarios/urls.py``:

.. code-block:: python

    urlpatterns = [
        path('', UsuarioListView.as_view(), name='usuario_list'),
        path('<int:pk>/', UsuarioDetailView.as_view(), name='usuario_detail'),
        path('crear/', UsuarioCreateView.as_view(), name='usuario_create'),
        path('<int:pk>/editar/', UsuarioUpdateView.as_view(), name='usuario_update'),
        path('<int:pk>/eliminar/', UsuarioDeleteView.as_view(), name='usuario_delete'),
        path('perfil/', PerfilView.as_view(), name='perfil'),
        path('cambiar-password/', CambiarPasswordView.as_view(), name='cambiar_password'),
    ]

Plantillas
----------

Plantillas ubicadas en ``usuarios/templates/usuarios/``:

- ``usuario_list.html``: Lista de usuarios
- ``usuario_detail.html``: Detalle de usuario
- ``usuario_form.html``: Formulario crear/editar
- ``perfil.html``: Perfil del usuario actual
- ``cambiar_password.html``: Formulario de cambio de contraseña

Validaciones
------------

**Validaciones de modelo:**

- Email único en el sistema
- Cédula única y formato válido
- Fecha de nacimiento obligatoria
- Edad mínima de 18 años para registro

**Validaciones de negocio:**

- Usuario debe estar activo para iniciar sesión
- Email debe estar verificado para operaciones críticas
- Cambio de contraseña requiere contraseña actual

Seguridad
---------

**Medidas implementadas:**

- Contraseñas encriptadas con PBKDF2
- Validación de complejidad de contraseñas
- Protección contra enumeración de usuarios
- Cierre automático de sesión si usuario se desactiva
- Registro de auditoría de cambios

**Configuración recomendada:**

.. code-block:: python

    # En settings.py
    
    AUTH_USER_MODEL = 'usuarios.Usuario'
    
    # Validadores de contraseña
    AUTH_PASSWORD_VALIDATORS = [
        {
            'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
        },
        {
            'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
            'OPTIONS': {'min_length': 8}
        },
        {
            'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
        },
        {
            'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
        },
    ]

Pruebas
-------

Pruebas ubicadas en ``usuarios/tests.py``:

- Pruebas de creación de usuarios
- Pruebas de autenticación
- Pruebas de managers personalizados
- Pruebas de signals
- Pruebas de validaciones
- Pruebas de permisos

Ejecutar pruebas:

.. code-block:: bash

    poetry run python manage.py test usuarios

Management Commands
-------------------

El módulo puede incluir comandos de gestión:

**create_admin**

Crear usuario administrador desde línea de comandos:

.. code-block:: bash

    python manage.py create_admin

Integración con Otros Módulos
------------------------------

**Relaciones principales:**

- ``auth``: Autenticación y verificación
- ``grupos``: Permisos y roles
- ``clientes``: Usuario puede estar asociado a cliente
- ``transacciones``: Usuario operador procesa transacciones
- ``notificaciones``: Usuario recibe notificaciones

Consideraciones
---------------

**Performance:**

- Índices en email y cedula (búsquedas frecuentes)
- Caché de permisos de usuario
- Paginación en listados

**Mantenimiento:**

- Revisar periódicamente usuarios inactivos
- Auditar cambios de permisos
- Monitorear intentos de acceso fallidos

**Extensibilidad:**

El modelo Usuario puede extenderse con:

- Campos adicionales según necesidades
- Métodos personalizados para lógica de negocio
- Integración con sistemas externos (LDAP, OAuth)
