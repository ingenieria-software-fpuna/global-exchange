from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

class EmailService:
    """Servicio para envío de emails de verificación"""
    
    @staticmethod
    def enviar_codigo_verificacion(usuario, codigo_obj, request=None):
        """
        Envía email con código de verificación usando template HTML
        """
        try:
            # Calcular tiempo de expiración en minutos
            tiempo_restante = codigo_obj.fecha_expiracion - timezone.now()
            minutos_expiracion = int(tiempo_restante.total_seconds() / 60)
            
            # Contexto para el template
            context = {
                'usuario': usuario,
                'codigo': codigo_obj.codigo,
                'codigo_obj': codigo_obj,  # Objeto completo para acceder a fecha_creacion
                'tipo': codigo_obj.get_tipo_display(),
                'minutos_expiracion': minutos_expiracion,
                'fecha_expiracion': codigo_obj.fecha_expiracion,
                'ip_address': codigo_obj.ip_address,
                'sitio_web': getattr(settings, 'SITE_NAME', 'Global Exchange'),
            }
            
            # Determinar subject y template según el tipo
            if codigo_obj.tipo == 'login':
                subject = '🔐 Código de Verificación - Inicio de Sesión'
                template_name = 'auth/emails/codigo_login.html'
            elif codigo_obj.tipo == 'registro':
                subject = '🎉 Código de Verificación - Registro de Cuenta'
                template_name = 'auth/emails/codigo_registro.html'
            else:
                raise ValueError(f"Tipo de código no soportado: {codigo_obj.tipo}")
            
            # Renderizar el contenido HTML
            html_content = render_to_string(template_name, context)
            
            # Contenido en texto plano como fallback
            text_content = f"""
{context['sitio_web']} - {context['tipo']}

Hola {usuario.nombre},

Tu código de verificación es: {codigo_obj.codigo}

Este código expirará en {minutos_expiracion} minutos.

Si no solicitaste este código, ignora este mensaje.

Saludos,
Equipo de {context['sitio_web']}
            """.strip()
            
            # Crear el mensaje
            msg = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[usuario.email],
            )
            
            # Adjuntar versión HTML
            msg.attach_alternative(html_content, "text/html")
            
            # Enviar email
            msg.send()
            
            logger.info(f"Email de verificación enviado exitosamente a {usuario.email}")
            return True, "Email enviado exitosamente"
            
        except Exception as e:
            logger.error(f"Error al enviar email a {usuario.email}: {str(e)}")
            return False, f"Error al enviar email: {str(e)}"

    @staticmethod
    def enviar_reset_password(usuario, token_obj, request=None):
        """
        Envía email con enlace de reset de contraseña
        """
        try:
            # Calcular tiempo de expiración en minutos
            tiempo_restante = token_obj.fecha_expiracion - timezone.now()
            minutos_expiracion = int(tiempo_restante.total_seconds() / 60)
            
            # Generar URL de reset
            if request:
                reset_url = request.build_absolute_uri(
                    f"/auth/reset-contrasena/{token_obj.token}/"
                )
            else:
                # Fallback URL (configurable en settings)
                base_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')
                reset_url = f"{base_url}/auth/reset-contrasena/{token_obj.token}/"
            
            # Contexto para el template
            context = {
                'usuario': usuario,
                'token': token_obj.token,
                'reset_url': reset_url,
                'minutos_expiracion': minutos_expiracion,
                'fecha_expiracion': token_obj.fecha_expiracion,
                'ip_address': token_obj.ip_address,
                'sitio_web': getattr(settings, 'SITE_NAME', 'Global Exchange'),
            }
            
            subject = '🔑 Restablecimiento de Contraseña - Global Exchange'
            template_name = 'auth/emails/reset_password.html'
            
            # Renderizar el contenido HTML
            html_content = render_to_string(template_name, context)
            
            # Contenido en texto plano como fallback
            text_content = f"""
{context['sitio_web']} - Restablecimiento de Contraseña

Hola {usuario.nombre},

Has solicitado restablecer tu contraseña. Haz clic en el siguiente enlace para crear una nueva contraseña:

{reset_url}

Este enlace expirará en {minutos_expiracion} minutos.

Si no solicitaste este restablecimiento, ignora este mensaje y tu contraseña permanecerá sin cambios.

Saludos,
Equipo de {context['sitio_web']}
            """.strip()
            
            # Crear el mensaje
            msg = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[usuario.email],
            )
            
            # Adjuntar versión HTML
            msg.attach_alternative(html_content, "text/html")
            
            # Enviar email
            msg.send()
            
            logger.info(f"Email de reset de contraseña enviado exitosamente a {usuario.email}")
            return True, "Email enviado exitosamente"
            
        except Exception as e:
            logger.error(f"Error al enviar email de reset a {usuario.email}: {str(e)}")
            return False, f"Error al enviar email: {str(e)}"
