Módulo de Notificaciones
========================

El módulo de notificaciones gestiona alertas automáticas sobre cambios en las tasas de cambio para usuarios con roles Operador y Visitante.

Descripción General
-------------------

Este módulo implementa un sistema completo de notificaciones que:

- Detecta cambios en tasas de cambio mediante señales Django
- Crea notificaciones en tiempo real para usuarios autorizados
- Envía correos electrónicos a usuarios con preferencias activadas
- Proporciona interfaz para gestionar notificaciones
- Controla acceso basado en roles (Operador y Visitante)

Modelo Principal
----------------

Notificacion
~~~~~~~~~~~~

Modelo que representa una notificación de cambio de tasa de cambio.

**Campos de identificación:**

- ``tipo``: Tipo de notificación ('tasa_cambio' actualmente)
- ``titulo``: Título descriptivo de la notificación (max 200 chars)
- ``mensaje``: Mensaje detallado en texto

**Relaciones:**

- ``usuario``: ForeignKey a Usuario que recibe la notificación
- ``moneda``: ForeignKey opcional a Moneda relacionada

**Campos de estado:**

- ``leida``: Boolean, indica si fue leída (default: False)
- ``fecha_creacion``: DateTime de creación (default: timezone.now)
- ``fecha_lectura``: DateTime nullable de cuándo se leyó

**Campos de contexto de tasa de cambio:**

- ``precio_base_anterior``: PositiveIntegerField nullable
- ``precio_base_nuevo``: PositiveIntegerField nullable
- ``comision_compra_anterior``: PositiveIntegerField nullable
- ``comision_compra_nueva``: PositiveIntegerField nullable
- ``comision_venta_anterior``: PositiveIntegerField nullable
- ``comision_venta_nueva``: PositiveIntegerField nullable

**Configuración del modelo:**

- ``verbose_name``: "Notificación"
- ``verbose_name_plural``: "Notificaciones"
- ``ordering``: ['-fecha_creacion'] (más recientes primero)
- ``db_table``: 'notificaciones_notificacion'

**Índices:**

.. code-block:: python

   indexes = [
       models.Index(fields=['usuario', '-fecha_creacion']),
       models.Index(fields=['usuario', 'leida']),
   ]

Métodos de Instancia
--------------------

**marcar_como_leida()**

Marca la notificación como leída y registra la fecha de lectura.

.. code-block:: python

   notificacion = Notificacion.objects.get(pk=1)
   notificacion.marcar_como_leida()
   
   assert notificacion.leida == True
   assert notificacion.fecha_lectura is not None

**Comportamiento:**

- Solo actualiza si no estaba leída previamente
- Establece ``leida = True``
- Registra ``fecha_lectura = timezone.now()``
- Usa ``update_fields`` para eficiencia

Propiedades Calculadas
----------------------

**cambio_porcentual**

Calcula el cambio porcentual entre precio anterior y nuevo.

.. code-block:: python

   notificacion = Notificacion.objects.get(pk=1)
   cambio = notificacion.cambio_porcentual
   # Retorna: 2.5 (para un aumento del 2.5%)
   #         -1.2 (para una disminución del 1.2%)
   #         None (si no hay datos suficientes)

**Retorna:**

- ``float``: Porcentaje de cambio (positivo o negativo)
- ``None``: Si faltan datos de precio anterior o nuevo

**es_aumento**

Determina si el cambio fue un aumento o disminución.

.. code-block:: python

   if notificacion.es_aumento:
       icono = "📈"
   elif notificacion.es_aumento is False:
       icono = "📉"
   else:
       icono = "➖"  # Sin cambio o datos insuficientes

**Retorna:**

- ``True``: Precio nuevo > precio anterior
- ``False``: Precio nuevo < precio anterior
- ``None``: Si faltan datos

**tasa_compra_anterior / tasa_compra_nueva**

Calculan las tasas de compra (precio base - comisión compra).

.. code-block:: python

   tasa_ant = notificacion.tasa_compra_anterior  # precio_base - comision_compra
   tasa_nue = notificacion.tasa_compra_nueva

**tasa_venta_anterior / tasa_venta_nueva**

Calculan las tasas de venta (precio base + comisión venta).

.. code-block:: python

   tasa_ant = notificacion.tasa_venta_anterior  # precio_base + comision_venta
   tasa_nue = notificacion.tasa_venta_nueva

Sistema de Señales
------------------

El módulo utiliza Django signals para detectar automáticamente cambios en tasas de cambio.

capturar_tasa_anterior
~~~~~~~~~~~~~~~~~~~~~~

Signal ``pre_save`` que captura valores anteriores antes de actualizar.

**Decorador:**

.. code-block:: python

   @receiver(pre_save, sender=TasaCambio)
   def capturar_tasa_anterior(sender, instance, **kwargs):
       ...

**Funcionamiento:**

1. Verifica si es una actualización (``instance.pk`` existe)
2. Recupera la instancia anterior de la base de datos
3. Almacena valores en atributos temporales:
   - ``instance._precio_base_anterior``
   - ``instance._comision_compra_anterior``
   - ``instance._comision_venta_anterior``

**Uso:**

Estos valores temporales son usados por ``notificar_cambio_tasa`` para comparar.

notificar_cambio_tasa
~~~~~~~~~~~~~~~~~~~~~

Signal ``post_save`` que crea notificaciones tras guardar una tasa de cambio.

**Decorador:**

.. code-block:: python

   @receiver(post_save, sender=TasaCambio)
   def notificar_cambio_tasa(sender, instance, created, **kwargs):
       ...

**Condiciones de activación:**

- Solo si ``instance.es_activa == True``
- Si es creación (``created=True``) O si hubo cambio en precio base

**Usuarios notificados:**

.. code-block:: python

   usuarios = Usuario.objects.filter(
       es_activo=True,
       activo=True,
       groups__name__in=['Operador', 'Visitante']
   ).distinct()

**Proceso de notificación:**

1. Calcula tasas de compra y venta:

   .. code-block:: python

      tasa_compra = precio_base - comision_compra
      tasa_venta = precio_base + comision_venta

2. Genera título y mensaje descriptivos:

   - Nueva tasa: "Nueva cotización: USD"
   - Actualización: "Cambio en cotización: USD (aumentó +2.5%)"

3. Crea notificaciones masivamente con ``bulk_create``

4. Envía emails a usuarios con ``recibir_notificaciones_email=True``

**Ejemplo de mensaje generado:**

.. code-block:: text

   Título: "Cambio en cotización: Dólar Estadounidense"
   Mensaje: "La cotización de Dólar Estadounidense aumentó. 
            Compra: 7200 → 7350, Venta: 7400 → 7550 (+2.08%)"

enviar_emails_notificacion
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Función auxiliar que envía correos electrónicos de notificación.

**Parámetros:**

- ``usuarios_con_email``: QuerySet de usuarios con preferencia activada
- ``moneda``: Instancia de Moneda
- ``precio_anterior``, ``precio_nuevo``: Valores de precio base
- ``comision_*_anterior``, ``comision_*_nueva``: Comisiones
- ``es_creacion``: Boolean indicando si es nueva tasa

**Funcionamiento:**

1. Calcula tasas finales y cambio porcentual
2. Genera asunto contextual:
   - Nueva: "🔔 Nueva cotización: USD"
   - Aumento: "📈 Cambio en cotización: USD"
   - Disminución: "📉 Cambio en cotización: USD"

3. Renderiza template HTML ``notificaciones/email_notificacion.html``
4. Envía email usando ``send_mail`` con ``html_message``
5. Maneja errores con ``fail_silently=True``

**Contexto del template:**

.. code-block:: python

   context = {
       'usuario': usuario,
       'moneda': moneda,
       'tasa_compra_anterior': ...,
       'tasa_compra_nueva': ...,
       'tasa_venta_anterior': ...,
       'tasa_venta_nueva': ...,
       'cambio_porcentual': 2.5,
       'es_aumento': True,
       'es_creacion': False,
       'url_sitio': 'http://localhost:8000',
       'fecha': timezone.now()
   }

Vistas
------

tiene_permiso_notificaciones
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Función helper que verifica permisos de acceso.

.. code-block:: python

   def tiene_permiso_notificaciones(user):
       return user.groups.filter(name__in=['Operador', 'Visitante']).exists()

**Retorna:**

- ``True``: Usuario pertenece a grupo Operador o Visitante
- ``False``: Usuario no tiene acceso

lista_notificaciones
~~~~~~~~~~~~~~~~~~~~

Vista funcional que lista notificaciones del usuario actual.

**Decorador:**

- ``@login_required``

**Parámetros GET:**

- ``filtro``: 'todas' (default), 'leidas', 'no_leidas'
- ``page``: Número de página para paginación

**Comportamiento:**

1. Verifica permisos (retorna 403 si no tiene acceso)
2. Filtra notificaciones según parámetro ``filtro``
3. Aplica paginación (20 notificaciones por página)
4. Cuenta notificaciones no leídas para badge

**Contexto:**

.. code-block:: python

   context = {
       'page_obj': page_obj,
       'filtro': 'todas',
       'no_leidas': 5
   }

**Template:** ``notificaciones/lista.html``

**Ejemplo de uso:**

.. code-block:: python

   # Ver todas
   /notificaciones/
   
   # Ver solo no leídas
   /notificaciones/?filtro=no_leidas
   
   # Página 2
   /notificaciones/?page=2

marcar_leida
~~~~~~~~~~~~

Vista funcional para marcar una notificación como leída.

**Decorador:**

- ``@login_required``

**Parámetros URL:**

- ``pk``: ID de la notificación

**Comportamiento:**

1. Verifica permisos (403 si no autorizado)
2. Obtiene notificación o retorna 404
3. Verifica que pertenezca al usuario actual
4. Marca como leída usando ``marcar_como_leida()``
5. Retorna JSON si es AJAX, redirige si es request normal

**Ejemplo AJAX:**

.. code-block:: javascript

   fetch('/notificaciones/1/marcar-leida/', {
       method: 'POST',
       headers: {
           'X-Requested-With': 'XMLHttpRequest',
           'X-CSRFToken': getCookie('csrftoken')
       }
   })
   .then(response => response.json())
   .then(data => console.log(data.success));  // true

marcar_todas_leidas
~~~~~~~~~~~~~~~~~~~

Vista funcional para marcar todas las notificaciones como leídas.

**Decorador:**

- ``@login_required``

**Método:**

- POST (protección CSRF)

**Comportamiento:**

1. Verifica permisos
2. Actualiza masivamente todas las no leídas:

   .. code-block:: python

      Notificacion.objects.filter(
          usuario=request.user,
          leida=False
      ).update(leida=True)

3. Retorna JSON si AJAX, redirige si no

**Uso desde JavaScript:**

.. code-block:: javascript

   document.getElementById('marcar-todas').addEventListener('click', function() {
       fetch('/notificaciones/marcar-todas-leidas/', {
           method: 'POST',
           headers: {
               'X-Requested-With': 'XMLHttpRequest',
               'X-CSRFToken': getCookie('csrftoken')
           }
       })
       .then(response => response.json())
       .then(data => location.reload());
   });

Context Processor
-----------------

notificaciones_no_leidas
~~~~~~~~~~~~~~~~~~~~~~~~~

Context processor que agrega información de notificaciones al contexto global.

**Ubicación:** ``notificaciones/context_processors.py``

**Configuración en settings.py:**

.. code-block:: python

   TEMPLATES = [{
       'OPTIONS': {
           'context_processors': [
               # ... otros context processors
               'notificaciones.context_processors.notificaciones_no_leidas',
           ],
       },
   }]

**Variables agregadas al contexto:**

- ``notificaciones_no_leidas_count``: Número de notificaciones no leídas
- ``puede_ver_notificaciones``: Boolean indicando si tiene acceso

**Lógica:**

.. code-block:: python

   def notificaciones_no_leidas(request):
       if request.user.is_authenticated:
           tiene_permiso = request.user.groups.filter(
               name__in=['Operador', 'Visitante']
           ).exists()
           
           if tiene_permiso:
               count = Notificacion.objects.filter(
                   usuario=request.user,
                   leida=False
               ).count()
               return {
                   'notificaciones_no_leidas_count': count,
                   'puede_ver_notificaciones': True
               }
       
       return {
           'notificaciones_no_leidas_count': 0,
           'puede_ver_notificaciones': False
       }

**Uso en templates:**

.. code-block:: html

   {% if puede_ver_notificaciones %}
       <a href="{% url 'notificaciones:lista' %}">
           <i class="fas fa-bell"></i>
           {% if notificaciones_no_leidas_count > 0 %}
               <span class="badge badge-danger">
                   {{ notificaciones_no_leidas_count }}
               </span>
           {% endif %}
       </a>
   {% endif %}

Formularios
-----------

PreferenciasNotificacionesForm
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Formulario para configurar preferencias de notificaciones de usuario.

**Campo:**

- ``recibir_notificaciones_email``: BooleanField

**Widget:**

.. code-block:: python

   widget=forms.CheckboxInput(attrs={
       'class': 'form-check-input'
   })

**Uso:**

.. code-block:: python

   from notificaciones.forms import PreferenciasNotificacionesForm

   if request.method == 'POST':
       form = PreferenciasNotificacionesForm(
           request.POST, 
           instance=request.user
       )
       if form.is_valid():
           form.save()

URLs
----

**Configuración de rutas:**

.. code-block:: python

   app_name = 'notificaciones'
   
   urlpatterns = [
       path('', lista_notificaciones, name='lista'),
       path('<int:pk>/marcar-leida/', marcar_leida, name='marcar_leida'),
       path('marcar-todas-leidas/', marcar_todas_leidas, name='marcar_todas_leidas'),
   ]

**Rutas completas:**

- ``/notificaciones/``: Lista de notificaciones
- ``/notificaciones/5/marcar-leida/``: Marcar notificación 5 como leída
- ``/notificaciones/marcar-todas-leidas/``: Marcar todas como leídas

Casos de Uso
------------

**Escenario 1: Operador recibe notificación de cambio de tasa**

1. Admin actualiza tasa de cambio del USD
2. Signal ``pre_save`` captura valores anteriores
3. Signal ``post_save`` detecta el cambio
4. Sistema crea notificaciones para todos los Operadores y Visitantes
5. Operador ve badge con número de notificaciones no leídas
6. Operador accede a lista y revisa cambios
7. Operador hace clic en notificación para marcarla como leída

**Escenario 2: Usuario con notificaciones por email**

1. Usuario activa ``recibir_notificaciones_email`` en preferencias
2. Admin crea nueva tasa de cambio para EUR
3. Sistema crea notificaciones en base de datos
4. Sistema envía email con detalles del cambio
5. Usuario recibe email: "🔔 Nueva cotización: EUR"
6. Email incluye tasas de compra y venta
7. Usuario hace clic en link del email para ver más detalles

**Escenario 3: Visitante revisa histórico de notificaciones**

1. Visitante accede a ``/notificaciones/``
2. Ve lista paginada de notificaciones
3. Filtra por "No leídas" para ver pendientes
4. Hace clic en "Marcar todas como leídas"
5. Todas las notificaciones se marcan sin recarga de página (AJAX)

Permisos y Seguridad
--------------------

**Control de acceso:**

- **Grupos autorizados:** Operador, Visitante
- **Admin:** NO recibe notificaciones (asume que ya conoce los cambios)
- **Verificación en vistas:** ``tiene_permiso_notificaciones()``
- **Context processor:** Solo agrega datos si tiene permiso

**Seguridad:**

- Notificaciones filtradas por usuario (no puede ver de otros)
- Protección CSRF en acciones POST
- Validación de permisos en cada vista
- Índices en BD para consultas eficientes

**Ejemplo de verificación:**

.. code-block:: python

   if not tiene_permiso_notificaciones(request.user):
       return HttpResponseForbidden(
           "No tienes permiso para ver notificaciones."
       )

Integración con Otros Módulos
------------------------------

**Con tasa_cambio:**

- Escucha señales de ``TasaCambio``
- Captura cambios en tiempo real
- Accede a precios y comisiones

**Con usuarios:**

- Filtra por grupos (Operador, Visitante)
- Verifica campo ``recibir_notificaciones_email``
- Respeta estados ``es_activo`` y ``activo``

**Con monedas:**

- Relaciona notificación con moneda afectada
- Usa métodos de formateo de moneda

**Con email (Django mail):**

- Envía notificaciones por correo
- Usa templates HTML
- Configura remitente desde settings

Configuración Requerida
-----------------------

**settings.py:**

.. code-block:: python

   # Context processor
   TEMPLATES = [{
       'OPTIONS': {
           'context_processors': [
               'notificaciones.context_processors.notificaciones_no_leidas',
           ],
       },
   }]

   # Email (para notificaciones por correo)
   EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
   EMAIL_HOST = 'smtp.gmail.com'
   EMAIL_PORT = 587
   EMAIL_USE_TLS = True
   EMAIL_HOST_USER = 'tu_email@example.com'
   EMAIL_HOST_PASSWORD = 'tu_password'
   DEFAULT_FROM_EMAIL = 'Global Exchange <noreply@globalexchange.com>'
   
   # URL del sitio (para links en emails)
   SITE_URL = 'https://tu-dominio.com'

**apps.py:**

.. code-block:: python

   class NotificacionesConfig(AppConfig):
       default_auto_field = 'django.db.models.BigAutoField'
       name = 'notificaciones'

       def ready(self):
           import notificaciones.signals  # Registrar señales

Plantillas
----------

**notificaciones/lista.html**

Template principal que muestra la lista de notificaciones.

**Elementos esperados:**

- Filtros (todas/leídas/no leídas)
- Lista paginada de notificaciones
- Badge con contador de no leídas
- Botón "Marcar todas como leídas"
- Indicador visual de leída/no leída

**notificaciones/email_notificacion.html**

Template HTML para emails de notificación.

**Variables de contexto:**

- ``usuario``: Instancia de Usuario
- ``moneda``: Instancia de Moneda
- ``tasa_compra_anterior``, ``tasa_compra_nueva``
- ``tasa_venta_anterior``, ``tasa_venta_nueva``
- ``cambio_porcentual``: Float
- ``es_aumento``: Boolean
- ``es_creacion``: Boolean
- ``url_sitio``: URL base del sitio
- ``fecha``: DateTime del cambio

Optimizaciones de Performance
------------------------------

**Índices de base de datos:**

.. code-block:: python

   indexes = [
       models.Index(fields=['usuario', '-fecha_creacion']),
       models.Index(fields=['usuario', 'leida']),
   ]

**Bulk operations:**

- ``bulk_create()`` para crear múltiples notificaciones
- ``update()`` para marcar todas como leídas

**Select related:**

.. code-block:: python

   notificaciones = Notificacion.objects.filter(
       usuario=request.user
   ).select_related('moneda')

**Paginación:**

- 20 notificaciones por página
- Reduce carga en lista larga

Pruebas Recomendadas
--------------------

**Tests de modelos:**

.. code-block:: python

   def test_marcar_como_leida():
       notif = Notificacion.objects.create(...)
       assert not notif.leida
       notif.marcar_como_leida()
       assert notif.leida
       assert notif.fecha_lectura is not None

**Tests de señales:**

.. code-block:: python

   def test_notificacion_creada_al_cambiar_tasa():
       usuarios = Usuario.objects.filter(groups__name='Operador')
       count_inicial = Notificacion.objects.count()
       
       tasa = TasaCambio.objects.create(...)
       
       count_final = Notificacion.objects.count()
       assert count_final == count_inicial + usuarios.count()

**Tests de permisos:**

.. code-block:: python

   def test_visitante_no_puede_ver_notificaciones_de_admin():
       response = self.client.get('/notificaciones/')
       assert response.status_code == 403  # Si no es Operador/Visitante

**Tests de vistas:**

.. code-block:: python

   def test_marcar_todas_leidas():
       self.client.login(...)
       response = self.client.post('/notificaciones/marcar-todas-leidas/')
       
       no_leidas = Notificacion.objects.filter(
           usuario=self.user,
           leida=False
       ).count()
       assert no_leidas == 0

Buenas Prácticas
----------------

1. **Limitar notificaciones:** Considerar agrupar cambios rápidos
2. **Email transaccional:** Usar servicio confiable (SendGrid, AWS SES)
3. **Limpieza periódica:** Archivar notificaciones antiguas
4. **Logs de envío:** Registrar fallos de email para debugging
5. **Rate limiting:** Evitar spam de notificaciones
6. **Preferencias granulares:** Permitir elegir qué monedas notificar
7. **Testing con mocks:** Mockear ``send_mail`` en tests
8. **Performance:** Monitorear queries N+1 en lista de notificaciones
