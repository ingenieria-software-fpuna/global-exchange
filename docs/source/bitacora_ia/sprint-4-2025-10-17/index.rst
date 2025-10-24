Sprint 4 - 17 de Octubre 2025
==============================

Sesiones de IA del cuarto sprint del proyecto Global Exchange.

Descripción
-----------

Este sprint se enfocó en:

- Implementación del módulo de notificaciones de cambios en tasas de cambio
- Integración con pasarelas de pago (simulador y Stripe)
- Mejoras en la configuración del sistema
- Refactoring y optimización de código existente

Conversaciones y Prompts
-------------------------

.. toctree::
   :maxdepth: 1

   Crear una App de Notificaciones
   simulador-pago

Resumen de Sesiones
--------------------

Crear una App de Notificaciones
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Fecha:** 17 de Octubre 2025

**Objetivo:** Implementar un sistema completo de notificaciones para alertar a usuarios sobre cambios en las tasas de cambio.

**Temas cubiertos:**

- Diseño del modelo ``Notificacion`` con campos de contexto de tasa de cambio
- Implementación de Django signals (``pre_save`` y ``post_save``) para detectar cambios
- Sistema de envío de correos electrónicos transaccionales
- Context processor para agregar contador de notificaciones no leídas
- Vistas con control de acceso basado en roles (Operador y Visitante)
- Integración con el módulo de tasas de cambio
- Optimización con índices de base de datos y bulk operations

**Resultados:**

- Módulo ``notificaciones/`` completamente funcional
- Notificaciones automáticas en tiempo real
- Emails HTML con información detallada de cambios
- Interfaz de usuario para gestionar notificaciones
- Sistema de permisos granular

simulador-pago
~~~~~~~~~~~~~~

**Fecha:** 17 de Octubre 2025

**Objetivo:** Integrar el sistema de transacciones con pasarelas de pago externas.

**Temas cubiertos:**

- Integración con API simulada de pasarela de pagos (Node.js)
- Implementación del servicio ``PasarelaService`` con manejo de errores
- Integración con Stripe Checkout para pagos internacionales
- Modelo ``PagoPasarela`` para registro de transacciones externas
- Formularios específicos por método de pago (tarjeta, billetera, transferencia)
- Sistema de webhooks para notificaciones asíncronas
- Mapeo de métodos de cobro entre sistemas
- Manejo robusto de timeouts y errores de conexión

**Resultados:**

- Módulo ``pagos/`` con doble integración (simulador + Stripe)
- Soporte para múltiples métodos de pago
- Trazabilidad completa de pagos procesados
- Webhooks funcionales para actualizaciones asíncronas
- Logging detallado para auditoría

Tecnologías Utilizadas
-----------------------

**Backend:**

- Django Signals (pre_save, post_save)
- Django email framework (send_mail, render_to_string)
- httpx para llamadas HTTP asíncronas
- Stripe Python SDK
- JSONField para datos estructurados

**Frontend:**

- AJAX para operaciones sin recarga
- Bootstrap para formularios y UI
- JavaScript para interactividad

**Infraestructura:**

- Pasarela simulada en Node.js (localhost:3001)
- Stripe Checkout (production-ready)
- SMTP para envío de emails

Lecciones Aprendidas
---------------------

1. **Signals de Django:** Potentes para lógica cross-cutting como notificaciones
2. **Bulk operations:** Esenciales para performance al crear múltiples registros
3. **Manejo de errores:** Timeouts y conexiones deben manejarse gracefully
4. **Idempotencia:** Webhooks pueden llegar duplicados, diseñar para ello
5. **Context processors:** Convenientes para datos globales de UI
6. **Índices de BD:** Críticos para queries frecuentes (usuario + fecha)
7. **Mapeo de datos:** Necesario cuando se integra con sistemas externos
8. **Logging detallado:** Invaluable para debugging de integraciones

Mejores Prácticas Aplicadas
----------------------------

- **Separación de concerns:** Servicios dedicados para lógica de negocio
- **DRY:** Funciones auxiliares reutilizables (_procesar_pago_con_pasarela)
- **Validación en capas:** Modelo, formulario, vista
- **Seguridad:** CSRF protection, validación de webhooks, datos sensibles
- **Testing:** Mocks para servicios externos (Stripe, pasarela)
- **Documentación:** Docstrings completas y ejemplos de uso
- **Observabilidad:** Logs estructurados con niveles apropiados
- **Fail gracefully:** Errores no bloquean operación completa del sistema

Desafíos Técnicos
-----------------

**Challenge 1: Capturar valores anteriores en signals**

*Problema:* En ``post_save``, la instancia anterior ya no está en memoria.

*Solución:* Usar ``pre_save`` para capturar y almacenar temporalmente en atributos de instancia.

.. code-block:: python

   @receiver(pre_save, sender=TasaCambio)
   def capturar_tasa_anterior(sender, instance, **kwargs):
       if instance.pk:
           tasa_anterior = TasaCambio.objects.get(pk=instance.pk)
           instance._precio_base_anterior = tasa_anterior.precio_base

**Challenge 2: Mapeo de métodos de pago**

*Problema:* Nombres de métodos difieren entre Django y la pasarela.

*Solución:* Diccionario de mapeo normalizado.

.. code-block:: python

   METODO_MAPPING = {
       'billetera electrónica': 'billetera',
       'tarjeta de débito': 'tarjeta',
       ...
   }

**Challenge 3: Monedas zero-decimal en Stripe**

*Problema:* PYG no tiene centavos, pero USD sí.

*Solución:* Detectar y manejar según tipo de moneda.

.. code-block:: python

   if moneda_lower in ['pyg', 'jpy', 'krw']:
       unit_amount = int(monto)
   else:
       unit_amount = int(monto * 100)

Próximos Pasos
--------------

- Implementar reintentos automáticos para pagos fallidos
- Dashboard de analíticas de pagos
- Pruebas de carga para notificaciones masivas
- Integración con más pasarelas de pago (PayPal, MercadoPago)
- Sistema de preferencias granulares de notificaciones (por moneda)
- Notificaciones push para aplicación móvil futura

Referencias
-----------

- `Django Signals Documentation <https://docs.djangoproject.com/en/stable/topics/signals/>`_
- `Stripe Checkout Documentation <https://stripe.com/docs/checkout>`_
- `httpx Library <https://www.python-httpx.org/>`_
- `Django Email Framework <https://docs.djangoproject.com/en/stable/topics/email/>`_
