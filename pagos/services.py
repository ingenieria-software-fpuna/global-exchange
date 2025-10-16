import httpx
import logging
from django.conf import settings
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


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