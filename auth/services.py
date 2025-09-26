from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.conf import settings
from django.utils import timezone
import logging
import os

logger = logging.getLogger(__name__)

class EmailService:
    """Servicio para envío de emails de verificación"""
    
    @staticmethod
    def enviar_codigo_verificacion(usuario, codigo_obj, request=None):
        """
        Envía email con código de verificación usando template HTML
        En modo desarrollo, puede mostrar el código en consola sin enviar email
        """
        # Verificar configuración de 2FA
        enable_2fa = os.environ.get('ENABLE_2FA', 'true').lower() in ['true', '1', 'yes', 'on']
        dev_mode = os.environ.get('ENABLE_2FA_DEV_MODE', 'false').lower() in ['true', '1', 'yes', 'on']
        fixed_code = os.environ.get('FIXED_2FA_CODE', '').strip()

        # Si está deshabilitada la 2FA completamente, no hacer nada
        if not enable_2fa:
            logger.info(f"2FA deshabilitada - no se envía código a {usuario.email}")
            return True, "2FA deshabilitada"

        # Modo desarrollo: mostrar código en consola y logs sin enviar email
        if dev_mode:
            print(f"\n{'='*60}")
            print(f"🔐 CÓDIGO DE VERIFICACIÓN 2FA - MODO DESARROLLO")
            print(f"{'='*60}")
            print(f"Usuario: {usuario.email}")
            print(f"Código: {codigo_obj.codigo}")
            print(f"Tipo: {codigo_obj.get_tipo_display()}")
            print(f"Expira en: 5 minutos")
            print(f"{'='*60}\n")

            logger.info(f"DEV MODE - Código 2FA para {usuario.email}: {codigo_obj.codigo}")
            return True, "Código mostrado en consola (modo desarrollo)"

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
        En modo desarrollo, puede mostrar el enlace en consola
        """
        # Verificar configuración de 2FA para reset de contraseña
        enable_2fa = os.environ.get('ENABLE_2FA', 'true').lower() in ['true', '1', 'yes', 'on']
        dev_mode = os.environ.get('ENABLE_2FA_DEV_MODE', 'false').lower() in ['true', '1', 'yes', 'on']

        # Si está deshabilitada la 2FA, no enviar email de reset
        if not enable_2fa:
            logger.info(f"2FA deshabilitada - no se envía enlace de reset a {usuario.email}")
            return True, "2FA deshabilitada"

        # Modo desarrollo: mostrar enlace en consola
        if dev_mode:
            # Generar URL de reset
            if request:
                reset_url = request.build_absolute_uri(
                    f"/auth/reset-contrasena/{token_obj.token}/"
                )
            else:
                base_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')
                reset_url = f"{base_url}/auth/reset-contrasena/{token_obj.token}/"

            print(f"\n{'='*60}")
            print(f"🔑 ENLACE DE RESET DE CONTRASEÑA - MODO DESARROLLO")
            print(f"{'='*60}")
            print(f"Usuario: {usuario.email}")
            print(f"Enlace: {reset_url}")
            print(f"Expira en: {int((token_obj.fecha_expiracion - timezone.now()).total_seconds() / 60)} minutos")
            print(f"{'='*60}\n")

            logger.info(f"DEV MODE - Enlace de reset para {usuario.email}: {reset_url}")
            return True, "Enlace mostrado en consola (modo desarrollo)"

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
