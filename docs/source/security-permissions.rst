Seguridad y Permisos
====================

Autenticación y Usuarios
------------------------

- Usuario personalizado ``usuarios.Usuario`` con login por email.
- Campo ``es_activo``: los usuarios desactivados no pueden navegar; el middleware los cierra sesión y muestra un mensaje.
- Restablecimiento de contraseña mediante ``PasswordResetToken`` enviado por email con expiración.

Verificación por Código
-----------------------

- ``CodigoVerificacion`` gestiona códigos de 6 dígitos por tipo: ``login``, ``registro`` y ``reset_password``.
- Los códigos expiran tras unos minutos y se invalidan al usarse.
- ``EmailService`` renderiza plantillas HTML en ``auth/templates/auth/emails/*.html``.

Grupos y Permisos
-----------------

- Los permisos se asignan a grupos estándar de Django.
- ``grupos.Grupo`` agrega el flag ``es_activo``. Cuando un grupo se inactiva, sus permisos dejan de contarse.
- ``grupos.backends.GrupoActivoBackend`` reemplaza la resolución de permisos para filtrar solamente grupos activos.
- Mixins de acceso: ``AdminRequiredMixin`` (miembros del grupo ``Admin``) y ``AdminOrStaffRequiredMixin``.

Buenas Prácticas
----------------

- Mantener el grupo ``Admin`` para tareas administrativas; evitar depender de ``is_superuser``.
- Configurar correo vía variables de entorno y nunca commitear credenciales.
- Usar HTTPS y configurar ``CSRF_TRUSTED_ORIGINS`` y ``ALLOWED_HOSTS`` en producción.

