Configuración
=============

Variables de Entorno
--------------------

Base de datos
^^^^^^^^^^^^^

- ``DB_NAME``: nombre de la base (por defecto ``glx_db``).
- ``DB_USER``: usuario (``admin`` por defecto).
- ``DB_PASSWORD``: contraseña (``1234`` por defecto).
- ``DB_HOST``: host de PostgreSQL (``localhost`` en dev).
- ``DB_PORT``: puerto (``5432`` por defecto).

Email
^^^^^

- ``EMAIL_HOST``: host SMTP (``smtp.gmail.com`` por defecto).
- ``EMAIL_PORT``: puerto (``587`` por defecto).
- ``EMAIL_USE_TLS``: ``true``/``false``.
- ``EMAIL_HOST_USER``: usuario de envío.
- ``EMAIL_HOST_PASSWORD``: contraseña de envío.
- ``DEFAULT_FROM_EMAIL``: remitente por defecto.

Sitio
^^^^^

- ``SITE_NAME``: nombre a mostrar en emails (``Global Exchange`` por defecto).
- ``ALLOWED_HOSTS``: lista separada por comas.
- ``CSRF_TRUSTED_ORIGINS``: orígenes confiables con esquema.
- ``DEBUG``: ``true``/``false``.

Archivos y Directorios
----------------------

- ``.env``: ejemplo en ``.env.example``. Se carga automáticamente si ``python-dotenv`` está instalado.
- Logs: ``logs/``; el logger ``auth.services`` escribe en ``logs/auth.log`` y consola.
- Documentación: ``docs/_build/html`` se agrega a ``STATICFILES_DIRS`` para servir ``/docs``.

Comandos Útiles
---------------

- ``make app-setup``: levanta DB (Docker), migra y carga permisos.
- ``make app-run``: inicia servidor Django.
- ``make app-migrate``: aplica migraciones.
- ``make db-up`` / ``make db-clean``: gestiona contenedor de PostgreSQL.
- ``make -C docs html``: genera documentación.

