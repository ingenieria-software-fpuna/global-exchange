Modelo de Datos
===============

Usuarios y Seguridad
--------------------

- ``usuarios.Usuario``: email como identificador, ``es_activo`` para control de acceso, ``is_staff`` para administración; manager con ``create_admin_user`` que agrega al grupo ``Admin``.
- ``auth.CodigoVerificacion``: código 6 dígitos, ``tipo``, expiración y metadatos (IP, user agent). Métodos: ``crear_codigo``, ``verificar_codigo`` y ``limpiar_codigos_expirados``.
- ``auth.PasswordResetToken``: token único con expiración y helpers para limpieza y validación.

Clientes
--------

- ``clientes.TipoCliente``: define descuento (%) y estado ``activo``.
- ``clientes.Cliente``: RUC validado, tipo de cliente (solo activos), usuarios asociados, ``activo`` y metadatos. Validación personalizada en ``clean``.

Monedas y Tasas de Cambio
-------------------------

- ``monedas.Moneda``: ``codigo`` ISO 4217 en mayúsculas, ``decimales`` por moneda, helpers ``formatear_monto`` y ``mostrar_monto``.
- ``tasa_cambio.TasaCambio``: ``tasa_compra``/``tasa_venta`` con 8 decimales, ``es_activa`` y lógica transaccional en ``save`` para dejar solo una tasa activa por moneda. Propiedades ``spread`` y ``spread_porcentual``.

Métodos de Pago
---------------

- ``metodo_pago.MetodoPago``: ``comision`` % entre 0 y 100, ``es_activo`` y metadatos.

Grupos y Permisos
-----------------

- ``grupos.Grupo``: envuelve ``auth.Group`` agregando ``es_activo`` y relaciones de conveniencia; controla la activación de permisos por grupo.

Relaciones Relevantes
---------------------

- ``Cliente.usuarios_asociados``: M2M con ``usuarios.Usuario``.
- ``TasaCambio.moneda``: FK a ``Moneda``.
- ``Grupo.group``: OneToOne con ``auth.Group`` estándar.

