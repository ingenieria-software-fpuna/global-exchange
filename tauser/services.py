from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
import logging
import os

logger = logging.getLogger(__name__)

class EmailServiceRetiro:
    """Servicio para envío de emails de verificación de retiro"""
    
    @staticmethod
    def enviar_codigo_verificacion_retiro(transaccion, codigo_obj, request=None):
        """
        Envía email con código de verificación para retiro usando template HTML
        En modo desarrollo, puede mostrar el código en consola sin enviar email
        """
        # Verificar configuración de 2FA
        enable_2fa = os.environ.get('ENABLE_2FA', 'true').lower() in ['true', '1', 'yes', 'on']
        dev_mode = os.environ.get('ENABLE_2FA_DEV_MODE', 'false').lower() in ['true', '1', 'yes', 'on']

        # Si está deshabilitada la 2FA completamente, no hacer nada
        if not enable_2fa:
            logger.info(f"2FA deshabilitada - no se envía código de retiro para transacción {transaccion.id_transaccion}")
            return True, "2FA deshabilitada"

        # Modo desarrollo: mostrar código en consola y logs sin enviar email
        if dev_mode:
            print(f"\n{'='*60}")
            print(f"🏧 CÓDIGO DE VERIFICACIÓN DE RETIRO - MODO DESARROLLO")
            print(f"{'='*60}")
            print(f"Transacción: {transaccion.id_transaccion}")
            print(f"Código: {codigo_obj.codigo}")
            print(f"Cliente: {transaccion.cliente.nombre_comercial if transaccion.cliente else 'Casual'}")
            print(f"Expira en: 5 minutos")
            print(f"{'='*60}\n")

            logger.info(f"DEV MODE - Código de retiro para {transaccion.id_transaccion}: {codigo_obj.codigo}")
            return True, "Código mostrado en consola (modo desarrollo)"

        try:
            # Calcular tiempo de expiración en minutos
            tiempo_restante = codigo_obj.fecha_expiracion - timezone.now()
            minutos_expiracion = int(tiempo_restante.total_seconds() / 60)
            
            # Contexto para el template
            context = {
                'transaccion': transaccion,
                'codigo': codigo_obj.codigo,
                'codigo_obj': codigo_obj,
                'minutos_expiracion': minutos_expiracion,
                'fecha_expiracion': codigo_obj.fecha_expiracion,
                'ip_address': codigo_obj.ip_address,
                'sitio_web': getattr(settings, 'SITE_NAME', 'Global Exchange'),
                'cliente_nombre': transaccion.cliente.nombre_comercial if transaccion.cliente else 'Cliente Casual',
                'monto_retiro': transaccion.moneda_destino.formatear_monto(transaccion.monto_destino),
                'moneda': transaccion.moneda_destino.nombre,
            }
            
            subject = '🏧 Código de Verificación - Retiro de Efectivo'
            template_name = 'tauser/emails/codigo_retiro.html'
            
            # Renderizar el contenido HTML
            html_content = render_to_string(template_name, context)
            
            # Contenido en texto plano como fallback
            text_content = f"""
{context['sitio_web']} - Verificación de Retiro

Hola {context['cliente_nombre']},

Has solicitado retirar {context['monto_retiro']} en {context['moneda']} de tu transacción {transaccion.id_transaccion}.

Tu código de verificación es: {codigo_obj.codigo}

Este código expirará en {minutos_expiracion} minutos.

Si no solicitaste este retiro, ignora este mensaje.

Saludos,
Equipo de {context['sitio_web']}
            """.strip()
            
            # Crear el mensaje
            msg = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[transaccion.cliente.email if transaccion.cliente else 'casual@example.com'],
            )
            
            # Adjuntar versión HTML
            msg.attach_alternative(html_content, "text/html")
            
            # Enviar email
            msg.send()
            
            logger.info(f"Email de verificación de retiro enviado exitosamente para transacción {transaccion.id_transaccion}")
            return True, "Email enviado exitosamente"
            
        except Exception as e:
            logger.error(f"Error al enviar email de retiro para transacción {transaccion.id_transaccion}: {str(e)}")
            return False, f"Error al enviar email: {str(e)}"
