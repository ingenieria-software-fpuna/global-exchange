Visión General
==============

Global Exchange es una aplicación web en Django 5 para gestionar entidades y operaciones básicas de una casa de cambios. El sistema incluye administración de usuarios, grupos y permisos, clientes, monedas, tasas de cambio y métodos de pago. La interfaz es server‑rendered con plantillas Django y los permisos se controlan mediante un backend personalizado que solo considera grupos activos.

Características Clave
---------------------

- Autenticación por correo: verificación por código y restablecimiento de contraseña por email.
- Usuarios y grupos: modelo de usuario personalizado y control de acceso por grupos activos.
- Gestión de clientes: tipos de cliente con descuentos y validaciones.
- Monedas y cotizaciones: manejo de decimales por moneda y una única tasa activa por moneda.
- Métodos de pago: comisiones porcentuales y activación/desactivación.
- Documentación integrada: Sphinx sirve HTML bajo la ruta ``/docs`` en desarrollo.

Tecnologías
-----------

- Python 3.13, Django 5.
- PostgreSQL (Docker en desarrollo).
- Poetry para dependencias y Makefile para tareas.
- Sphinx para documentación (``docs/``).

Estructura Alta‑Nivel
---------------------

- ``global_exchange/``: settings, urls, ASGI/WSGI.
- ``auth/``: emails y flujo de verificación y reset de contraseña.
- ``usuarios/``: modelo de usuario personalizado y CRUD básico.
- ``grupos/``: backend de permisos por grupos activos, mixins de acceso.
- ``clientes/``: tipos de cliente y clientes con validaciones.
- ``monedas/``: catálogo de monedas y decimales por moneda.
- ``tasa_cambio/``: cotizaciones con una activa por moneda.
- ``metodo_pago/``: métodos de pago con comisión.
- ``templates/``: base y vistas server‑rendered.
- ``tests/``: pruebas por app y paquete global.

