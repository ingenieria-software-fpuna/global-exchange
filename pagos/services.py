import httpx
import logging
import stripe
from django.conf import settings
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

# Configure Stripe API key
stripe.api_key = settings.STRIPE_SECRET_KEY


class PasarelaService:
    """
    Servicio para integrar con la API simulada de pasarela de pagos.
    """
    
    # URL base del simulador de pasarela
    BASE_URL = "http://localhost:3001"
    
    # Mapeo de métodos de cobro de Django a métodos de la pasarela
    METODO_MAPPING = {
        'billetera electrónica': 'billetera',  
        'billetera electronica': 'billetera',
        'tarjeta de débito': 'tarjeta',
        'tarjeta de debito': 'tarjeta',
        'tarjeta de crédito local': 'tarjeta_credito_local',
        'tarjeta de credito local': 'tarjeta_credito_local',
        'pago en cuenta bancaria': 'transferencia',
        'cuenta bancaria': 'transferencia',
        'transferencia bancaria': 'transferencia',
    }
    
    def __init__(self, timeout: int = 30):
        """
        Inicializa el servicio de pasarela.
        
        Args:
            timeout: Tiempo de espera en segundos para las peticiones HTTP
        """
        self.timeout = timeout
        self.webhook_url = f"http://localhost:8000/pagos/webhook-pago/"
    
    def _mapear_metodo(self, metodo_cobro: str) -> str:
        """
        Mapea el método de cobro de Django al formato esperado por la pasarela.
        
        Args:
            metodo_cobro: Nombre del método de cobro desde Django
            
        Returns:
            str: Método de pago para la pasarela
        """
        metodo_lower = metodo_cobro.lower()
        return self.METODO_MAPPING.get(metodo_lower, 'tarjeta')
    
    def procesar_pago(
        self, 
        monto: float, 
        metodo_cobro: str, 
        moneda: str = "USD",
        escenario: str = "exito",
        datos_adicionales: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Envía una solicitud de pago a la pasarela.
        
        Args:
            monto: Monto del pago
            metodo_cobro: Método de cobro (ej: "Tarjeta de débito")
            moneda: Código de moneda (USD, PYG, etc.)
            escenario: Escenario de simulación (exito, fallo, pendiente)
            datos_adicionales: Datos adicionales del pago
            
        Returns:
            Dict con la respuesta de la pasarela o error
        """
        try:
            # Mapear método de cobro
            metodo_pasarela = self._mapear_metodo(metodo_cobro)
            
            # Preparar payload base
            payload = {
                "monto": float(monto),
                "metodo": metodo_pasarela,
                "moneda": moneda,
                "escenario": escenario,
                "webhook_url": self.webhook_url
            }
            
            # Agregar datos específicos según el método de pago
            if datos_adicionales:
                # Para métodos de tarjeta (débito y crédito local), agregar número de tarjeta
                if metodo_pasarela in ['tarjeta', 'tarjeta_credito_local']:
                    # Extraer el número de tarjeta sin enmascarar de los datos del formulario
                    numero_tarjeta = datos_adicionales.get('numero_tarjeta')
                    if numero_tarjeta:
                        payload['numero_tarjeta'] = numero_tarjeta.replace(' ', '')
                
                # Para billetera electrónica, agregar número de teléfono
                elif metodo_pasarela == 'billetera':
                    telefono = datos_adicionales.get('telefono')
                    if telefono:
                        payload['numero_billetera'] = telefono
                
                # Para transferencia bancaria, agregar número de comprobante
                elif metodo_pasarela == 'transferencia':
                    comprobante = datos_adicionales.get('numero_comprobante')
                    if comprobante:
                        payload['numero_comprobante'] = comprobante
            
            logger.info(f"Enviando pago a pasarela: {payload}")
            
            # Realizar petición HTTP
            with httpx.Client(timeout=self.timeout) as client:
                response = client.post(f"{self.BASE_URL}/pago", json=payload)
                response.raise_for_status()
                
                resultado = response.json()
                logger.info(f"Respuesta de pasarela: {resultado}")
                
                return {
                    'success': True,
                    'data': resultado
                }
                
        except httpx.TimeoutException:
            error_msg = "Timeout al comunicarse con la pasarela de pagos"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'error_type': 'timeout'
            }
            
        except httpx.HTTPStatusError as e:
            error_msg = f"Error HTTP de la pasarela: {e.response.status_code}"
            logger.error(f"{error_msg} - {e.response.text}")
            return {
                'success': False,
                'error': error_msg,
                'error_type': 'http_error',
                'status_code': e.response.status_code
            }
            
        except httpx.RequestError as e:
            error_msg = f"Error de conexión con la pasarela: {str(e)}"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'error_type': 'connection_error'
            }
            
        except Exception as e:
            error_msg = f"Error inesperado: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {
                'success': False,
                'error': error_msg,
                'error_type': 'unexpected_error'
            }
    
    def consultar_pago(self, id_pago: str) -> Dict[str, Any]:
        """
        Consulta el estado de un pago en la pasarela.
        
        Args:
            id_pago: ID del pago en la pasarela
            
        Returns:
            Dict con el estado del pago o error
        """
        try:
            logger.info(f"Consultando pago en pasarela: {id_pago}")
            
            with httpx.Client(timeout=self.timeout) as client:
                response = client.get(f"{self.BASE_URL}/pago/{id_pago}")
                response.raise_for_status()
                
                resultado = response.json()
                logger.info(f"Estado del pago {id_pago}: {resultado}")
                
                return {
                    'success': True,
                    'data': resultado
                }
                
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 404:
                return {
                    'success': False,
                    'error': 'Pago no encontrado',
                    'error_type': 'not_found'
                }
            else:
                error_msg = f"Error HTTP al consultar pago: {e.response.status_code}"
                logger.error(f"{error_msg} - {e.response.text}")
                return {
                    'success': False,
                    'error': error_msg,
                    'error_type': 'http_error'
                }
                
        except Exception as e:
            error_msg = f"Error al consultar pago: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {
                'success': False,
                'error': error_msg,
                'error_type': 'unexpected_error'
            }
    
    def esta_disponible(self) -> bool:
        """
        Verifica si la pasarela de pagos está disponible.
        
        Returns:
            bool: True si la pasarela está disponible
        """
        try:
            with httpx.Client(timeout=5) as client:
                response = client.get(f"{self.BASE_URL}/docs")  # Endpoint de health check
                return response.status_code == 200
        except:
            return False


class StripeService:
    """
    Servicio para integrar con Stripe Checkout.
    """

    def __init__(self):
        """
        Inicializa el servicio de Stripe.
        """
        self.api_key = settings.STRIPE_SECRET_KEY
        self.webhook_secret = settings.STRIPE_WEBHOOK_SECRET
        stripe.api_key = self.api_key

    def crear_sesion_checkout(
        self,
        monto: float,
        moneda: str,
        transaccion_id: str,
        descripcion: str = "Compra de moneda",
        success_url: str = None,
        cancel_url: str = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Crea una sesión de Stripe Checkout.

        Args:
            monto: Monto del pago
            moneda: Código de moneda (usd, pyg, etc.)
            transaccion_id: ID de la transacción en el sistema
            descripcion: Descripción del producto/servicio
            success_url: URL de retorno cuando el pago es exitoso
            cancel_url: URL de retorno cuando el pago es cancelado
            metadata: Metadatos adicionales para asociar con el pago

        Returns:
            Dict con la sesión creada o error
        """
        try:
            # Convertir el monto a la unidad más pequeña de la moneda (centavos)
            # Stripe requiere montos en la unidad más pequeña (ej: centavos para USD)
            # Para PYG, no hay centavos, así que se usa el monto directamente
            moneda_lower = moneda.lower()

            # Monedas sin decimales (zero-decimal currencies)
            monedas_sin_decimales = ['pyg', 'jpy', 'krw', 'clp', 'vnd']

            if moneda_lower in monedas_sin_decimales:
                unit_amount = int(monto)
            else:
                # Para monedas con decimales, multiplicar por 100
                unit_amount = int(monto * 100)

            # Preparar metadata
            session_metadata = metadata or {}
            session_metadata['transaccion_id'] = transaccion_id

            # URLs por defecto
            if not success_url:
                success_url = f"{settings.SITE_URL}/pagos/stripe/success?session_id={{CHECKOUT_SESSION_ID}}"
            if not cancel_url:
                cancel_url = f"{settings.SITE_URL}/pagos/stripe/cancel"

            logger.info(f"Creando sesión Stripe - Transacción: {transaccion_id}, Monto: {unit_amount} {moneda}")

            # Crear sesión de checkout
            checkout_session = stripe.checkout.Session.create(
                line_items=[
                    {
                        'price_data': {
                            'currency': moneda_lower,
                            'product_data': {
                                'name': 'Transacción Global Exchange',
                                'description': descripcion,
                            },
                            'unit_amount': unit_amount,
                        },
                        'quantity': 1,
                    },
                ],
                mode='payment',
                success_url=success_url,
                cancel_url=cancel_url,
                metadata=session_metadata,
                payment_intent_data={
                    'metadata': session_metadata,
                },
            )

            logger.info(f"Sesión Stripe creada exitosamente - ID: {checkout_session.id}")

            return {
                'success': True,
                'session_id': checkout_session.id,
                'url': checkout_session.url,
                'payment_intent': checkout_session.payment_intent,
            }

        except stripe.error.InvalidRequestError as e:
            error_msg = f"Solicitud inválida a Stripe: {str(e)}"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'error_type': 'invalid_request'
            }

        except stripe.error.AuthenticationError as e:
            error_msg = "Error de autenticación con Stripe (verificar API key)"
            logger.error(f"{error_msg}: {str(e)}")
            return {
                'success': False,
                'error': error_msg,
                'error_type': 'authentication_error'
            }

        except stripe.error.APIConnectionError as e:
            error_msg = "Error de conexión con Stripe"
            logger.error(f"{error_msg}: {str(e)}")
            return {
                'success': False,
                'error': error_msg,
                'error_type': 'connection_error'
            }

        except stripe.error.StripeError as e:
            error_msg = f"Error de Stripe: {str(e)}"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'error_type': 'stripe_error'
            }

        except Exception as e:
            error_msg = f"Error inesperado: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {
                'success': False,
                'error': error_msg,
                'error_type': 'unexpected_error'
            }

    def recuperar_sesion(self, session_id: str) -> Dict[str, Any]:
        """
        Recupera información de una sesión de checkout.

        Args:
            session_id: ID de la sesión de Stripe

        Returns:
            Dict con la información de la sesión o error
        """
        try:
            logger.info(f"Recuperando sesión Stripe: {session_id}")

            session = stripe.checkout.Session.retrieve(session_id)

            return {
                'success': True,
                'session': session,
                'payment_status': session.payment_status,
                'payment_intent': session.payment_intent,
            }

        except stripe.error.StripeError as e:
            error_msg = f"Error al recuperar sesión: {str(e)}"
            logger.error(error_msg)
            return {
                'success': False,
                'error': error_msg,
                'error_type': 'stripe_error'
            }

        except Exception as e:
            error_msg = f"Error inesperado: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {
                'success': False,
                'error': error_msg,
                'error_type': 'unexpected_error'
            }

    def verificar_webhook(self, payload: bytes, sig_header: str) -> Dict[str, Any]:
        """
        Verifica y procesa un evento de webhook de Stripe.

        Args:
            payload: Cuerpo de la solicitud del webhook
            sig_header: Header de firma de Stripe

        Returns:
            Dict con el evento verificado o error
        """
        try:
            event = stripe.Webhook.construct_event(
                payload, sig_header, self.webhook_secret
            )

            logger.info(f"Webhook Stripe verificado - Tipo: {event['type']}")

            return {
                'success': True,
                'event': event,
                'type': event['type'],
            }

        except ValueError as e:
            error_msg = "Payload inválido del webhook"
            logger.error(f"{error_msg}: {str(e)}")
            return {
                'success': False,
                'error': error_msg,
                'error_type': 'invalid_payload'
            }

        except stripe.error.SignatureVerificationError as e:
            error_msg = "Firma del webhook inválida"
            logger.error(f"{error_msg}: {str(e)}")
            return {
                'success': False,
                'error': error_msg,
                'error_type': 'invalid_signature'
            }

        except Exception as e:
            error_msg = f"Error al verificar webhook: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return {
                'success': False,
                'error': error_msg,
                'error_type': 'unexpected_error'
            }

    def esta_disponible(self) -> bool:
        """
        Verifica si el servicio de Stripe está configurado correctamente.

        Returns:
            bool: True si Stripe está configurado
        """
        return bool(self.api_key and self.api_key.startswith('sk_'))
