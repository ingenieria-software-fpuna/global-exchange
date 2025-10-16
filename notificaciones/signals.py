"""
Señales para el módulo de notificaciones.
Detecta cambios en las tasas de cambio y crea notificaciones para los usuarios.
También envía correos electrónicos a usuarios que tienen esta preferencia activada.
"""
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from tasa_cambio.models import TasaCambio
from .models import Notificacion

Usuario = get_user_model()


@receiver(pre_save, sender=TasaCambio)
def capturar_tasa_anterior(sender, instance, **kwargs):
    """
    Captura el precio base anterior antes de guardar una actualización.
    """
    if instance.pk:  # Solo si es una actualización
        try:
            tasa_anterior = TasaCambio.objects.get(pk=instance.pk)
            instance._precio_base_anterior = tasa_anterior.precio_base
        except TasaCambio.DoesNotExist:
            instance._precio_base_anterior = None
    else:
        instance._precio_base_anterior = None


@receiver(post_save, sender=TasaCambio)
def notificar_cambio_tasa(sender, instance, created, **kwargs):
    """
    Crea notificaciones para usuarios con roles Operador y Visitante cuando se crea 
    o actualiza una tasa de cambio activa.
    """
    # Solo notificar si la tasa es activa
    if not instance.es_activa:
        return

    # Obtener el precio anterior si existe
    precio_anterior = getattr(instance, '_precio_base_anterior', None)
    
    # Si es una nueva tasa o hubo cambio en el precio
    if created or (precio_anterior and precio_anterior != instance.precio_base):
        # Obtener usuarios activos que pertenecen a los grupos Operador o Visitante
        usuarios = Usuario.objects.filter(
            es_activo=True, 
            activo=True,
            groups__name__in=['Operador', 'Visitante']
        ).distinct()
        
        # Determinar el tipo de cambio
        if created:
            titulo = f"Nueva cotización: {instance.moneda.nombre}"
            mensaje = (f"Se ha establecido una nueva cotización para {instance.moneda.nombre}. "
                      f"Precio base: {instance.moneda.formatear_monto(instance.precio_base)}")
        else:
            # Es una actualización
            if precio_anterior:
                cambio = instance.precio_base - precio_anterior
                cambio_porcentual = ((cambio / precio_anterior) * 100) if precio_anterior > 0 else 0
                direccion = "aumentó" if cambio > 0 else "disminuyó"
                
                titulo = f"Cambio en cotización: {instance.moneda.nombre}"
                mensaje = (f"La cotización de {instance.moneda.nombre} {direccion}. "
                          f"Precio anterior: {instance.moneda.formatear_monto(precio_anterior)}, "
                          f"Precio nuevo: {instance.moneda.formatear_monto(instance.precio_base)} "
                          f"({cambio_porcentual:+.2f}%)")
            else:
                titulo = f"Actualización de cotización: {instance.moneda.nombre}"
                mensaje = (f"Se actualizó la cotización de {instance.moneda.nombre}. "
                          f"Precio base: {instance.moneda.formatear_monto(instance.precio_base)}")
        
        # Crear notificaciones para todos los usuarios
        notificaciones = []
        for usuario in usuarios:
            notificacion = Notificacion(
                usuario=usuario,
                tipo='tasa_cambio',
                titulo=titulo,
                mensaje=mensaje,
                moneda=instance.moneda,
                precio_base_anterior=precio_anterior,
                precio_base_nuevo=instance.precio_base
            )
            notificaciones.append(notificacion)
        
        # Crear todas las notificaciones en una sola operación
        if notificaciones:
            Notificacion.objects.bulk_create(notificaciones)
            
            # Enviar correos a usuarios que tienen la preferencia activada
            enviar_emails_notificacion(
                usuarios_con_email=usuarios.filter(recibir_notificaciones_email=True),
                moneda=instance.moneda,
                precio_anterior=precio_anterior,
                precio_nuevo=instance.precio_base,
                es_creacion=created
            )


def enviar_emails_notificacion(usuarios_con_email, moneda, precio_anterior, precio_nuevo, es_creacion):
    """
    Envía correos electrónicos a los usuarios que tienen activada la preferencia de notificaciones por email.
    """
    if not usuarios_con_email.exists():
        return
    
    # Calcular cambio porcentual
    if precio_anterior and precio_anterior > 0:
        cambio_porcentual = abs(((precio_nuevo - precio_anterior) / precio_anterior) * 100)
        es_aumento = precio_nuevo > precio_anterior
    else:
        cambio_porcentual = 0
        es_aumento = True
    
    # Determinar el asunto del correo
    if es_creacion:
        asunto = f"🔔 Nueva cotización: {moneda.nombre} ({moneda.codigo})"
    else:
        icono = "📈" if es_aumento else "📉"
        asunto = f"{icono} Cambio en cotización: {moneda.nombre} ({moneda.codigo})"
    
    # URL del sitio (obtener de settings o usar default)
    url_sitio = getattr(settings, 'SITE_URL', 'http://localhost:8000')
    
    # Enviar email a cada usuario
    for usuario in usuarios_con_email:
        try:
            context = {
                'usuario': usuario,
                'moneda': moneda,
                'precio_anterior': precio_anterior or 0,
                'precio_nuevo': precio_nuevo,
                'cambio_porcentual': cambio_porcentual,
                'es_aumento': es_aumento,
                'es_creacion': es_creacion,
                'url_sitio': url_sitio,
                'fecha': TasaCambio.objects.filter(moneda=moneda).first().fecha_actualizacion,
            }
            
            # Renderizar el template HTML
            html_message = render_to_string('notificaciones/email_notificacion.html', context)
            
            # Enviar el correo
            send_mail(
                subject=asunto,
                message='',  # Mensaje en texto plano (vacío porque usamos HTML)
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[usuario.email],
                html_message=html_message,
                fail_silently=True,  # No fallar silenciosamente en producción
            )
        except Exception as e:
            # Log del error (en producción usar logging)
            print(f"Error enviando email a {usuario.email}: {e}")
