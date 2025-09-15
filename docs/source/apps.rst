Apps del Sistema
================

auth
----

- Modelos: ``CodigoVerificacion`` (códigos 6 dígitos con expiración), ``PasswordResetToken`` (token 64 chars, 1h por defecto).
- Servicios: ``EmailService`` para enviar códigos de login/registro y enlaces de reset vía plantillas HTML.
- Middleware: ``UsuarioActivoMiddleware`` fuerza cierre de sesión si ``usuario.es_activo`` es falso.

usuarios
--------

- ``Usuario`` extiende ``AbstractBaseUser`` + ``PermissionsMixin``. Login por ``email``. Campos clave: ``cedula``, ``nombre``, ``fecha_nacimiento``, ``es_activo``, ``is_staff``. Manager con ``create_admin_user`` que asigna grupo ``Admin``.

grupos
------

- ``Grupo`` envuelve un ``django.contrib.auth.models.Group`` y agrega ``es_activo`` para activar/desactivar permisos del grupo.
- Backend ``GrupoActivoBackend``: solo considera permisos de grupos activos al resolver ``has_perm`` y ``has_module_perms``.
- Mixins: ``AdminRequiredMixin`` y ``AdminOrStaffRequiredMixin`` para CBVs.

clientes
--------

- ``TipoCliente``: nombre único, descuento porcentual y ``activo``.
- ``Cliente``: RUC validado, tipo de cliente (solo activos), usuarios asociados, ``activo`` y metadatos.

monedas
-------

- ``Moneda``: ``codigo`` ISO 4217, ``decimales``, ``es_activa``, helpers para formateo/visualización de montos con símbolo.

tasa_cambio
-----------

- ``TasaCambio``: compra/venta con 8 decimales, ``es_activa`` único por ``moneda``. La lógica de ``save`` desactiva otras tasas activas de la misma moneda.

metodo_pago
-----------

- ``MetodoPago``: nombre único, ``comision`` 0–100%, ``es_activo``.

