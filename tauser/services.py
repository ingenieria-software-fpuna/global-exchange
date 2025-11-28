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
    def _obtener_destinatarios(transaccion, request=None):
        """
        Determina la lista de destinatarios para el correo de verificación.
        
        Prioriza el correo del usuario autenticado (operador del simulador),
        ya que es quien necesita el código para procesar el retiro.
        """
        destinatarios = []
        
        # PRIORIDAD 1: Usuario autenticado actual (operador del simulador)
        if request and hasattr(request, 'user') and request.user.is_authenticated:
            correo_usuario = getattr(request.user, 'email', None)
            if correo_usuario:
                destinatarios.append(correo_usuario)
                logger.info(f"Usando email del usuario autenticado (operador) como destinatario: {correo_usuario}")
        
        # PRIORIDAD 2: Usuario que procesa la transacción
        if not destinatarios:
            usuario_procesa = getattr(transaccion, 'usuario', None)
            correo_usuario = getattr(usuario_procesa, 'email', None)
            if correo_usuario:
                destinatarios.append(correo_usuario)
                logger.info(f"Usando email del usuario que procesa la transacción: {correo_usuario}")
        
        # PRIORIDAD 3: Cliente (solo como fallback si no hay usuario)
        if not destinatarios:
            cliente = getattr(transaccion, 'cliente', None)
            if cliente:
                correo_cliente = getattr(cliente, 'correo_electronico', None)
                if correo_cliente:
                    destinatarios.append(correo_cliente)
                    logger.info(f"Usando email del cliente como fallback: {correo_cliente}")
                else:
                    # Buscar usuarios asociados al cliente
                    asociados = cliente.usuarios_asociados.filter(email__isnull=False).values_list('email', flat=True)
                    for email in asociados:
                        if email:
                            destinatarios.append(email)
                            logger.info(f"Usando email de usuario asociado al cliente: {email}")
                            break

        # Validar y deduplicar emails
        deduplicados = []
        vistos = set()
        for email in destinatarios:
            if email and email.strip() and '@' in email and email not in vistos:
                # Validar que no sea un email de ejemplo inválido
                if email.lower() not in ['casual@example.com', 'test@example.com', 'example@example.com']:
                    vistos.add(email)
                    deduplicados.append(email.strip())

        # Log para debugging
        if not deduplicados:
            logger.warning(
                f"No se encontraron destinatarios válidos para transacción {transaccion.id_transaccion}",
                extra={
                    'transaccion_id': transaccion.id_transaccion,
                    'tiene_cliente': cliente is not None,
                    'cliente_email': getattr(cliente, 'correo_electronico', None) if cliente else None,
                    'usuario_autenticado': request.user.email if request and hasattr(request, 'user') and request.user.is_authenticated else None
                }
            )

        return deduplicados

    @staticmethod
    def enviar_codigo_verificacion_retiro(transaccion, codigo_obj, request=None, tauser=None):
        """
        Envía email con código de verificación para retiro usando template HTML
        En modo desarrollo, puede mostrar el código en consola sin enviar email
        
        Args:
            transaccion: Objeto Transaccion
            codigo_obj: Objeto CodigoVerificacionRetiro
            request: Objeto request de Django (opcional)
            tauser: Objeto Tauser desde donde se procesa la transacción (opcional)
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
                'tauser_nombre': tauser.nombre if tauser else None,
                'tauser_direccion': tauser.direccion if tauser else None,
            }
            
            subject = '🏧 Código de Verificación - Transacción desde Tauser'
            template_name = 'tauser/emails/codigo_retiro.html'
            
            # Renderizar el contenido HTML
            html_content = render_to_string(template_name, context)
            
            # Contenido en texto plano como fallback
            tauser_info = ""
            if context['tauser_nombre']:
                tauser_info = f"\nTauser: {context['tauser_nombre']}"
                if context['tauser_direccion']:
                    tauser_info += f"\nUbicación: {context['tauser_direccion']}"
            
            text_content = f"""
{context['sitio_web']} - Verificación de Transacción

Hola,

Se ha recibido una solicitud de transacción desde el Tauser.{tauser_info}

ID de Transacción: {transaccion.id_transaccion}
Monto: {context['monto_retiro']} en {context['moneda']}

Tu código de verificación es: {codigo_obj.codigo}

Este código expirará en {minutos_expiracion} minutos.

Si no solicitaste esta transacción, ignora este mensaje.

Saludos,
Equipo de {context['sitio_web']}
            """.strip()
            
            # Crear el mensaje
            destinatarios = EmailServiceRetiro._obtener_destinatarios(transaccion, request)

            if not destinatarios:
                logger.error(
                    f"No se encontró correo electrónico válido para enviar código de retiro - Transacción {transaccion.id_transaccion}",
                    extra={
                        'transaccion_id': transaccion.id_transaccion,
                        'cliente_id': transaccion.cliente.id if transaccion.cliente else None,
                        'usuario_id': request.user.id if request and hasattr(request, 'user') and request.user.is_authenticated else None
                    }
                )
                return False, "No se encontró un correo electrónico válido para enviar el código. Por favor, verifica que el cliente tenga un correo configurado o contacta al administrador."

            msg = EmailMultiAlternatives(
                subject=subject,
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=destinatarios,
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
