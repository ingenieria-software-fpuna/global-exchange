Arquitectura
============

Capas y Componentes
-------------------

- Presentación: plantillas en ``templates/`` + plantillas por app (``app/templates/app/...``). Vista de bienvenida ``welcome_view`` muestra tasas activas.
- Aplicación: vistas por app, formularios y validaciones de modelo. Middleware ``auth.middleware.UsuarioActivoMiddleware`` fuerza que solo usuarios activos pueden navegar.
- Acceso y permisos: backend ``grupos.backends.GrupoActivoBackend`` filtra permisos a través de grupos con ``es_activo=True``.
- Persistencia: modelos Django en apps de dominio; PostgreSQL como base de datos por defecto.

Entradas Principales
--------------------

- ``global_exchange/urls.py``: enruta a apps: ``auth/``, ``usuarios/``, ``grupos/``, ``clientes/``, ``monedas/``, ``tasa-cambio/``, ``metodos-pago/`` y documentación ``/docs``.
- ``global_exchange/settings.py``:
  - Carga opcional de ``.env`` mediante ``python-dotenv``.
  - ``AUTH_USER_MODEL='usuarios.Usuario'``.
  - ``AUTHENTICATION_BACKENDS`` incluye ``grupos.backends.GrupoActivoBackend``.
  - ``STATICFILES_DIRS`` sirve ``docs/_build/html`` para documentación.
  - Configuración de email por variables de entorno.

Documentación Servida en Desarrollo
----------------------------------

- Vista ``docs_view`` sirve archivos estáticos generados por Sphinx desde ``docs/_build/html`` bajo ``/docs``. Generar con ``make -C docs html``.

Plantillas Base
---------------

- ``templates/base.html``: layout base.
- ``templates/welcome.html``: página inicial con tasas activas por moneda.

Context Processors y Middleware
-------------------------------

- ``grupos.context_processors.permissions_context``: expone permisos al template.
- ``auth.middleware.UsuarioActivoMiddleware``: desconecta usuarios con ``es_activo=False`` y muestra mensaje.

