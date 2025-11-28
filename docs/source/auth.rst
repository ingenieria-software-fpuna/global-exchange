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

**Configuración de 2FA:**

El servicio respeta tres variables de entorno:

- ``ENABLE_2FA``: (true/false) Habilita o deshabilita completamente el 2FA
- ``ENABLE_2FA_DEV_MODE``: (true/false) Modo desarrollo que muestra códigos en consola sin enviar emails
- ``FIXED_2FA_CODE``: Código fijo para desarrollo/testing

**Método principal:**

enviar_codigo_verificacion(usuario, codigo_obj, request=None)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Envía email con código de verificación usando template HTML.

**Parámetros:**

- ``usuario``: Instancia de Usuario que recibirá el código
- ``codigo_obj``: Instancia de CodigoVerificacion con el código generado
- ``request``: Request de Django (opcional, para obtener IP)

**Comportamiento según configuración:**

1. **Si ENABLE_2FA=False:**
   
   - No envía email
   - Retorna (True, "2FA deshabilitada")
   - El sistema hace login directo

2. **Si ENABLE_2FA_DEV_MODE=True:**
   
   - Muestra código en consola con formato destacado
   - Registra en logs
   - No envía email real
   - Retorna (True, "Código mostrado en consola")

3. **Si está en modo producción:**
   
   - Renderiza template HTML según tipo (login/registro)
   - Crea EmailMultiAlternatives con versión texto plano
   - Envía email con código
   - Retorna (True, "Email enviado") o (False, mensaje_error)

**Templates utilizados:**

- ``auth/emails/codigo_login.html``: Para códigos de login
- ``auth/emails/codigo_registro.html``: Para códigos de registro

**Contexto pasado al template:**

.. code-block:: python

    context = {
        'usuario': usuario,
        'codigo': codigo_obj.codigo,
        'codigo_obj': codigo_obj,
        'tipo': codigo_obj.get_tipo_display(),
        'minutos_expiracion': 5,
        'fecha_expiracion': codigo_obj.fecha_expiracion,
        'ip_address': codigo_obj.ip_address,
        'sitio_web': 'Global Exchange',
    }

**Ejemplo de uso completo:**

.. code-block:: python

    from auth.services import EmailService
    from auth.models import CodigoVerificacion
    
    # Crear código
    codigo_obj = CodigoVerificacion.crear_codigo(
        usuario=user,
        tipo='login',
        request=request,
        minutos_expiracion=5
    )
    
    # Enviar email
    exito, mensaje = EmailService.enviar_codigo_verificacion(
        usuario=user,
        codigo_obj=codigo_obj,
        request=request
    )
    
    if exito:
        print("Email enviado exitosamente")
    else:
        print(f"Error: {mensaje}")

**Manejo de errores:**

- Captura excepciones de SMTP
- Registra errores en logs
- Retorna tupla (False, mensaje_error)
- No interrumpe el flujo de la aplicación

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

El módulo incluye las siguientes vistas principales (todas basadas en funciones):

**Autenticación básica:**

login_view
~~~~~~~~~~

Vista principal de inicio de sesión.

**Funcionalidad:**

- Autentica usuario con email y contraseña
- Verifica estado del usuario (activo y email verificado)
- Si 2FA está habilitado: genera código de verificación y redirige a verificación
- Si 2FA está deshabilitado: realiza login directo
- Envía código de verificación por email
- Maneja usuarios no verificados mostrando opción de reenvío

**Configuración 2FA:**

- Variable de entorno: ``ENABLE_2FA`` (true/false)
- Si está deshabilitada, el login es directo sin código
- Si está habilitada, envía código de 6 dígitos con expiración de 5 minutos

logout_view
~~~~~~~~~~~

Cierra la sesión del usuario actual.

- Limpia sesión de Django
- Redirige a página de login
- Muestra mensaje de confirmación

verify_code_view
~~~~~~~~~~~~~~~~

Verifica códigos de verificación de dos factores.

**Funcionalidad:**

- Valida código ingresado contra código almacenado
- Verifica tipo de verificación (login, registro, reset_password)
- Comprueba expiración del código
- Marca código como usado al validar
- Realiza login automático si es código de login
- Activa cuenta si es código de registro

dashboard_view
~~~~~~~~~~~~~~

Vista principal del dashboard (requiere login).

**Registro de usuarios:**

registro_view
~~~~~~~~~~~~~

Formulario de registro de nuevos usuarios.

**Validaciones:**

- Email único
- Cédula única
- Formato de contraseña segura
- Edad mínima (18 años)
- Campos requeridos: email, cédula, nombre, fecha_nacimiento, password

**Proceso:**

1. Valida datos del formulario
2. Crea usuario con ``activo=False`` y ``es_activo=True``
3. Genera código de verificación de 6 dígitos
4. Envía email con código
5. Guarda user_id en sesión para verificación posterior
6. Redirige a página de verificación

verificar_registro_view
~~~~~~~~~~~~~~~~~~~~~~~

Verifica código enviado al email durante el registro.

**Funcionalidad:**

- Valida código de 6 dígitos
- Marca usuario como ``activo=True`` (email verificado)
- Realiza login automático después de verificar
- Redirige al dashboard

reenviar_codigo_view
~~~~~~~~~~~~~~~~~~~~

Reenvía código de verificación de registro.

- Verifica que el usuario existe y no está verificado
- Genera nuevo código
- Invalida códigos anteriores
- Envía nuevo email

reenviar_verificacion_login_view
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Reenvía código de verificación desde pantalla de login.

- Similar a reenviar_codigo_view
- Usado cuando usuario intenta login sin verificar email

**Reseteo de contraseña:**

password_reset_request_view
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Solicitud de reseteo de contraseña.

**Proceso:**

1. Usuario ingresa su email
2. Sistema verifica que el email existe
3. Genera token único de 64 caracteres
4. Envía email con enlace que contiene el token
5. Token válido por 1 hora

**Características:**

- Genera PasswordResetToken con expiración de 1 hora
- Invalida tokens anteriores del mismo usuario
- Envía email con enlace de reseteo
- Muestra mensaje de éxito sin revelar si el email existe (seguridad)

password_reset_confirm_view
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Confirmación de reseteo con token desde el email.

**Parámetros:**

- ``token``: Token de 64 caracteres de la URL

**Proceso:**

1. Valida que el token existe y no ha expirado
2. Verifica que no ha sido usado
3. Muestra formulario para nueva contraseña
4. Valida que las contraseñas coincidan
5. Actualiza contraseña del usuario
6. Marca token como usado
7. Redirige a página de completado

password_reset_complete_view
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Vista de confirmación después de reseteo exitoso.

- Muestra mensaje de éxito
- Proporciona enlace para iniciar sesión

Formularios
-----------

El módulo proporciona formularios especializados:

LoginForm
~~~~~~~~~

Formulario para autenticación de usuarios.

**Campos:**

- ``email``: EmailField con placeholder
- ``password``: PasswordField

**Validaciones personalizadas:**

.. code-block:: python

    def clean(self):
        # 1. Verifica que el email existe
        # 2. Verifica que la contraseña es correcta
        # 3. Verifica que el usuario está activo (es_activo=True)
        # 4. Verifica que el email está verificado (activo=True)
        
**Métodos:**

- ``get_user()``: Retorna usuario autenticado o None
- ``get_unverified_user()``: Retorna usuario no verificado si existe

**Comportamiento:**

- Si el usuario no está activo (``es_activo=False``): error "cuenta desactivada"
- Si el email no está verificado (``activo=False``): error con opción de reenviar código
- Si la contraseña es incorrecta: error "contraseña incorrecta"
- Si el email no existe: error "email no existe"

VerificationCodeForm
~~~~~~~~~~~~~~~~~~~~

Formulario simple para ingresar códigos de verificación.

**Campos:**

- ``code``: CharField, max 6 caracteres
- Widget con placeholder "Código de verificación"

RegistroForm
~~~~~~~~~~~~

Formulario extendido de UserCreationForm para registro de usuarios.

**Campos:**

- ``email``: EmailField requerido
- ``cedula``: CharField (max 20), requerido
- ``nombre``: CharField (max 100), requerido
- ``apellido``: CharField (max 100), opcional
- ``fecha_nacimiento``: DateField con widget date picker, requerido
- ``password1``: PasswordField
- ``password2``: PasswordField (confirmación)

**Validaciones automáticas:**

- Email único en el sistema
- Cédula única en el sistema
- Edad mínima de 18 años (calculada desde fecha_nacimiento)
- Las dos contraseñas deben coincidir
- Contraseña debe cumplir requisitos de seguridad de Django

**Ejemplo de uso:**

.. code-block:: python

    form = RegistroForm(request.POST)
    if form.is_valid():
        usuario = form.save(commit=False)
        usuario.activo = False  # Email no verificado aún
        usuario.es_activo = True  # Usuario habilitado
        usuario.save()
        
        # Generar y enviar código de verificación
        codigo = CodigoVerificacion.crear_codigo(
            usuario=usuario,
            tipo='registro',
            request=request
        )

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
