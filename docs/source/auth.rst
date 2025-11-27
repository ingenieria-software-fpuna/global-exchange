Módulo de Autenticación (auth)
==============================

El módulo de autenticación proporciona funcionalidades de seguridad, verificación de usuarios y gestión de contraseñas para el sistema Global Exchange.

Modelos Principales
------------------

CodigoVerificacion
~~~~~~~~~~~~~~~~~~

Modelo para almacenar códigos de verificación temporales con expiración automática.

**Campos principales:**

- ``usuario``: Usuario asociado al código (ForeignKey)
- ``codigo``: Código de verificación de 6 dígitos
- ``tipo``: Tipo de verificación (login, registro, reset_password)
- ``fecha_creacion``: Fecha y hora de creación del código
- ``fecha_expiracion``: Fecha y hora límite de validez
- ``usado``: Indica si el código ya fue utilizado
- ``ip_address``: Dirección IP desde donde se solicitó el código
- ``user_agent``: Información del navegador/cliente

**Tipos de verificación:**

- ``login``: Código para inicio de sesión de dos factores
- ``registro``: Código para verificar email en registro
- ``reset_password``: Código para validar reseteo de contraseña

**Métodos principales:**

.. code-block:: python

    # Generar un código de 6 dígitos
    codigo = CodigoVerificacion.generar_codigo()
    
    # Crear un código para un usuario
    codigo_obj = CodigoVerificacion.crear_codigo(
        usuario=usuario,
        tipo='login',
        request=request,
        minutos_expiracion=5
    )
    
    # Verificar un código
    es_valido, codigo_obj = CodigoVerificacion.verificar_codigo(
        usuario=usuario,
        codigo='123456',
        tipo='login'
    )
    
    # Limpiar códigos expirados
    CodigoVerificacion.limpiar_codigos_expirados()

**Características:**

- Generación automática de códigos numéricos de 6 dígitos
- Invalidación automática de códigos anteriores del mismo tipo
- Expiración configurable (por defecto 5 minutos)
- Registro de IP y User Agent para auditoría
- Limpieza automática de códigos expirados y usados

PasswordResetToken
~~~~~~~~~~~~~~~~~~

Modelo para gestionar tokens de reseteo de contraseña con mayor duración.

**Campos principales:**

- ``usuario``: Usuario asociado al token
- ``token``: Token único de 64 caracteres alfanuméricos
- ``fecha_creacion``: Fecha y hora de creación
- ``fecha_expiracion``: Fecha límite de validez (1 hora por defecto)
- ``usado``: Indica si el token ya fue utilizado
- ``ip_address``: IP desde donde se solicitó el reset

**Métodos principales:**

.. code-block:: python

    # Crear un token de reset
    token_obj = PasswordResetToken.crear_token(
        usuario=usuario,
        request=request
    )
    
    # Verificar validez
    if token_obj.es_valido():
        # Procesar reset de contraseña
        token_obj.marcar_como_usado()
    
    # Limpiar tokens expirados
    PasswordResetToken.limpiar_tokens_expirados()

**Características:**

- Tokens únicos de 64 caracteres para mayor seguridad
- Validez de 1 hora por defecto
- Un solo token activo por usuario (se eliminan anteriores)
- Limpieza automática de tokens expirados después de 24 horas

Servicios
---------

EmailService
~~~~~~~~~~~~

Servicio para envío de correos electrónicos relacionados con autenticación.

**Funcionalidades:**

- Envío de códigos de verificación para login
- Envío de códigos de verificación para registro
- Envío de enlaces de reseteo de contraseña
- Plantillas HTML personalizadas por tipo de correo
- Gestión de errores de envío

**Uso:**

.. code-block:: python

    from auth.services import EmailService
    
    # Enviar código de login
    EmailService.enviar_codigo_login(usuario, codigo)
    
    # Enviar código de registro
    EmailService.enviar_codigo_registro(usuario, codigo)
    
    # Enviar enlace de reset
    EmailService.enviar_reset_password(usuario, token)

Middleware
----------

UsuarioActivoMiddleware
~~~~~~~~~~~~~~~~~~~~~~~

Middleware que verifica el estado de activación del usuario en cada petición.

**Funcionalidad:**

- Verifica que ``usuario.es_activo == True``
- Si el usuario está inactivo, cierra la sesión automáticamente
- Excluye rutas públicas (login, logout, registro)
- Permite acceso a rutas de autenticación

**Configuración:**

Agregar en ``settings.py``:

.. code-block:: python

    MIDDLEWARE = [
        # ... otros middleware
        'auth.middleware.UsuarioActivoMiddleware',
        # ... otros middleware
    ]

Vistas (Views)
--------------

El módulo incluye las siguientes vistas principales:

**Autenticación básica:**

- ``LoginView``: Inicio de sesión con verificación de código
- ``LogoutView``: Cierre de sesión
- ``VerifyCodeView``: Verificación de códigos de dos factores

**Registro:**

- ``RegisterView``: Registro de nuevos usuarios
- ``VerifyEmailView``: Verificación de email con código

**Reseteo de contraseña:**

- ``PasswordResetRequestView``: Solicitud de reset
- ``PasswordResetConfirmView``: Confirmación con token
- ``PasswordResetCompleteView``: Finalización del proceso

Formularios
-----------

El módulo proporciona formularios especializados:

- ``LoginForm``: Formulario de inicio de sesión
- ``VerificationCodeForm``: Formulario para códigos de verificación
- ``RegisterForm``: Formulario de registro con validaciones
- ``PasswordResetRequestForm``: Solicitud de reset
- ``PasswordResetForm``: Establecimiento de nueva contraseña

Plantillas
----------

Plantillas HTML ubicadas en ``auth/templates/auth/``:

- ``login.html``: Página de inicio de sesión
- ``verify_code.html``: Verificación de código
- ``register.html``: Registro de usuario
- ``password_reset_request.html``: Solicitud de reset
- ``password_reset_confirm.html``: Confirmación de reset

**Plantillas de email:**

- ``auth/emails/codigo_login.html``
- ``auth/emails/codigo_registro.html``
- ``auth/emails/reset_password.html``

URLs
----

Las rutas del módulo están en ``auth/urls.py``:

.. code-block:: python

    urlpatterns = [
        path('login/', LoginView.as_view(), name='login'),
        path('logout/', LogoutView.as_view(), name='logout'),
        path('register/', RegisterView.as_view(), name='register'),
        path('verify-code/', VerifyCodeView.as_view(), name='verify_code'),
        path('password-reset/', PasswordResetRequestView.as_view(), name='password_reset'),
        path('password-reset/<str:token>/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    ]

Seguridad
---------

**Medidas implementadas:**

- Códigos de verificación de un solo uso
- Expiración automática de códigos y tokens
- Registro de IP y User Agent para auditoría
- Invalidación de códigos anteriores al generar nuevos
- Protección contra fuerza bruta con límite de intentos
- Limpieza automática de datos sensibles

**Configuración recomendada:**

.. code-block:: python

    # En settings.py
    
    # Configuración de email
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = os.getenv('EMAIL_HOST')
    EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
    EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True') == 'True'
    EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
    EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
    DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL')
    
    # Tiempo de expiración de sesión
    SESSION_COOKIE_AGE = 3600  # 1 hora
    SESSION_SAVE_EVERY_REQUEST = True

Pruebas
-------

El módulo incluye pruebas exhaustivas en ``auth/tests.py``:

- Pruebas de generación de códigos y tokens
- Pruebas de verificación y validación
- Pruebas de expiración automática
- Pruebas de envío de emails
- Pruebas de middleware
- Pruebas de vistas y formularios

Ejecutar pruebas:

.. code-block:: bash

    poetry run python manage.py test auth

Consideraciones
---------------

**Performance:**

- Índices en campos de búsqueda frecuente (codigo, tipo, usuario)
- Limpieza periódica de registros expirados
- Caché de consultas frecuentes

**Mantenimiento:**

- Ejecutar regularmente ``limpiar_codigos_expirados()``
- Monitorear tasas de fallo de envío de emails
- Revisar logs de autenticación

**Integración:**

El módulo se integra con:

- ``usuarios``: Para gestión de usuarios
- ``grupos``: Para permisos y roles
- Sistema de notificaciones para alertas de seguridad
