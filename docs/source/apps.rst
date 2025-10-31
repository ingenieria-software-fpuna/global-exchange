Apps del Sistema
================

Este documento proporciona un resumen de todas las aplicaciones del sistema Global Exchange.

Aplicaciones de Autenticación y Usuarios
-----------------------------------------

auth
~~~~

Sistema de autenticación con verificación de dos factores.

- **Modelos**: ``CodigoVerificacion``, ``PasswordResetToken``
- **Servicios**: ``EmailService`` para envío de códigos
- **Middleware**: ``UsuarioActivoMiddleware`` para validación de usuarios activos
- **Documentación completa**: :doc:`auth`

usuarios
~~~~~~~~

Gestión de usuarios del sistema.

- **Modelo principal**: ``Usuario`` (extiende AbstractBaseUser)
- **Manager**: ``UsuarioManager`` con métodos especializados
- **Autenticación**: Por email (no username)
- **Documentación completa**: :doc:`usuarios`

grupos
~~~~~~

Sistema de roles y permisos basado en grupos de Django.

- **Modelo**: ``Grupo`` (envuelve django.contrib.auth.Group)
- **Backend**: ``GrupoActivoBackend`` para permisos activos
- **Mixins**: Protección de vistas por rol
- **Grupos predeterminados**: Admin, Operador, Visitante
- **Documentación completa**: :doc:`grupos`

Aplicaciones de Negocio Principal
----------------------------------

clientes
~~~~~~~~

Gestión de clientes corporativos con descuentos.

- **Modelos**: ``TipoCliente``, ``Cliente``
- **Características**: RUC, descuentos, usuarios asociados
- **Signal**: Asignación automática de rol Operador
- **Documentación completa**: :doc:`clientes`

monedas
~~~~~~~

Catálogo de divisas y denominaciones.

- **Modelos**: ``Moneda``, ``DenominacionMoneda``
- **Características**: Código ISO, formateo automático
- **Template tags**: Formateo de montos
- **Documentación completa**: :doc:`monedas`

tasa_cambio
~~~~~~~~~~~

Cotizaciones de compra y venta de divisas.

- **Modelo**: ``TasaCambio``
- **Características**: Precio base, comisiones, spread
- **Regla**: Una sola tasa activa por moneda
- **Integración**: Notificaciones automáticas
- **Documentación completa**: :doc:`tasa_cambio`

transacciones
~~~~~~~~~~~~~

Operaciones de cambio de moneda (compra/venta).

- **Modelos**: ``Transaccion``, ``TipoOperacion``, ``EstadoTransaccion``
- **Características**: ID único, código verificación, expiración
- **Cálculos**: Comisiones, descuentos, totales
- **Estados**: PENDIENTE, PAGADA, CANCELADA, ANULADA
- **Documentación completa**: :doc:`transacciones`

Aplicaciones de Métodos de Pago
--------------------------------

metodo_pago
~~~~~~~~~~~

Métodos para entregar dinero al cliente.

- **Modelo**: ``MetodoPago``
- **Características**: Comisión porcentual, estado activo
- **Ejemplos**: Efectivo, Transferencia bancaria
- **Documentación completa**: :doc:`metodo_pago`

metodo_cobro
~~~~~~~~~~~~

Métodos para recibir dinero del cliente.

- **Modelo**: ``MetodoCobro``
- **Características**: Comisión porcentual, estado activo
- **Ejemplos**: Efectivo, Tarjeta, QR
- **Documentación completa**: :doc:`metodo_cobro`

pagos
~~~~~

Integración con pasarelas de pago externas.

- **Modelos**: ``PagoPasarela``
- **Servicios**: ``PasarelaService``, ``StripeService``
- **Características**: Webhooks, estados, procesamiento asíncrono
- **Documentación completa**: :doc:`pagos`

Aplicaciones de Soporte
------------------------

notificaciones
~~~~~~~~~~~~~~

Sistema de notificaciones para usuarios.

- **Modelo**: ``Notificacion``
- **Características**: En plataforma y por email
- **Triggers**: Cambios de tasa, eventos del sistema
- **Context processor**: Contador de no leídas
- **Documentación completa**: :doc:`notificaciones`

configuracion
~~~~~~~~~~~~~

Configuraciones globales del sistema.

- **Modelo**: ``ConfiguracionSistema`` (Singleton)
- **Características**: Límites de transacciones, parámetros del sistema
- **Acceso**: ``ConfiguracionSistema.get_configuracion()``
- **Documentación completa**: :doc:`configuracion`

tauser
~~~~~~

Gestión de puntos de atención y stock.

- **Modelos**: ``Tauser``, ``Stock``, ``StockDenominacion``, ``HistorialStock``
- **Características**: Inventario por moneda, códigos de retiro
- **Auditoría**: Historial completo de movimientos
- **Documentación completa**: :doc:`tauser`

facturacion_service
~~~~~~~~~~~~~~~~~~~

Integración con facturación electrónica SIFEN.

- **Componentes**: ``invoice_generator``, ``factura_utils``, ``inutilizar``
- **Características**: Generación de facturas, CDC, numeración
- **Integración**: SQL-Proxy, sistema de facturación externo
- **Documentación completa**: :doc:`facturacion`

Módulos Deprecados
-------------------

roles
~~~~~

.. warning::
   Módulo deprecado. Funcionalidad migrada a ``grupos``.

La funcionalidad de roles ahora se maneja mediante el módulo ``grupos`` que usa
el sistema nativo de Django ``auth.models.Group``.

Ver documentación de :doc:`grupos` para gestión de roles y permisos.

Resumen de Dependencias
------------------------

**Dependencias principales:**

- ``auth`` → ``usuarios``
- ``usuarios`` → ``grupos``
- ``clientes`` → ``usuarios``, ``grupos``
- ``transacciones`` → ``clientes``, ``monedas``, ``tasa_cambio``, ``metodo_pago``, ``metodo_cobro``
- ``pagos`` → ``transacciones``
- ``notificaciones`` → ``usuarios``, ``tasa_cambio``
- ``tauser`` → ``monedas``, ``transacciones``
- ``facturacion_service`` → ``transacciones``, ``clientes``

Estructura de Carpetas
-----------------------

Cada aplicación sigue la estructura estándar de Django::

    app_name/
    ├── __init__.py
    ├── admin.py           # Configuración del admin de Django
    ├── apps.py            # Configuración de la aplicación
    ├── forms.py           # Formularios de la aplicación
    ├── models.py          # Modelos de datos
    ├── tests.py           # Pruebas unitarias
    ├── urls.py            # Rutas de la aplicación
    ├── views.py           # Vistas (controladores)
    ├── migrations/        # Migraciones de base de datos
    ├── templates/         # Plantillas HTML
    │   └── app_name/
    ├── static/            # Archivos estáticos (CSS, JS, imágenes)
    │   └── app_name/
    └── management/        # Comandos de gestión personalizados
        └── commands/

Convenciones de Código
-----------------------

**Modelos:**

- Nombres en singular (``Usuario``, no ``Usuarios``)
- CamelCase para clases
- ``Meta`` con ``verbose_name`` y ``verbose_name_plural``
- Campos con ``help_text`` descriptivo

**Vistas:**

- Class-Based Views (CBV) preferidas
- Mixins para funcionalidad compartida
- Permisos verificados en la vista

**URLs:**

- Nombres descriptivos (``cliente_list``, ``cliente_detail``)
- Namespace por aplicación
- RESTful donde sea posible

**Templates:**

- Herencia desde ``base.html``
- Bloques bien definidos
- Uso de template tags para lógica compleja

Pruebas
-------

Ejecutar pruebas por aplicación:

.. code-block:: bash

    # Probar una aplicación específica
    poetry run python manage.py test auth
    poetry run python manage.py test usuarios
    poetry run python manage.py test transacciones
    
    # Probar todas las aplicaciones
    poetry run python manage.py test

Management Commands
-------------------

Comandos disponibles por aplicación:

.. code-block:: bash

    # Setup inicial
    python manage.py setup_grupos
    python manage.py setup_transacciones
    python manage.py setup_monedas
    
    # Mantenimiento
    python manage.py clearsessions
    python manage.py cleanup_expired_codes

Referencias Cruzadas
--------------------

Para documentación detallada de cada módulo, consultar:

- :doc:`auth` - Autenticación y verificación
- :doc:`usuarios` - Gestión de usuarios
- :doc:`grupos` - Roles y permisos
- :doc:`clientes` - Clientes corporativos
- :doc:`monedas` - Catálogo de divisas
- :doc:`tasa_cambio` - Cotizaciones
- :doc:`transacciones` - Operaciones de cambio
- :doc:`metodo_pago` - Métodos de pago
- :doc:`metodo_cobro` - Métodos de cobro
- :doc:`pagos` - Pasarelas de pago
- :doc:`notificaciones` - Sistema de notificaciones
- :doc:`configuracion` - Configuración del sistema
- :doc:`tauser` - Puntos de atención
- :doc:`facturacion` - Facturación electrónica

