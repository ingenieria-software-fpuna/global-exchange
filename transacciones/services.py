import logging
from typing import Any, Dict, Optional

from django.utils import timezone

from pagos.services import PasarelaService


logger = logging.getLogger(__name__)


class DepositoSimuladorError(Exception):
    """Error al intentar registrar el depósito en el simulador."""


def generar_referencia_deposito(transaccion_id: str) -> str:
    """
    Genera una referencia para depósitos simulados evitando patrones
    rechazados por la pasarela.
    """
    base = ''.join(ch for ch in str(transaccion_id) if ch.isalnum())
    if len(base) < 6:
        base = (base + 'ABCDEFGH123456789')[:12]
    referencia = f"DEP{base[-12:]}".upper()

    if len(referencia) < 6:
        referencia = (referencia + '123456')[:6]

    while '000' in referencia:
        referencia = referencia.replace('000', '111')

    return referencia[:20]


def _obtener_campos_metodo_pago(transaccion) -> Dict[str, Any]:
    datos_metodo = transaccion.datos_metodo_pago if isinstance(transaccion.datos_metodo_pago, dict) else {}
    campos = datos_metodo.get('campos', [])
    campos_dict: Dict[str, Any] = {}
    for campo in campos:
        nombre = campo.get('nombre')
        if nombre:
            campos_dict[nombre] = campo.get('valor')
    return campos_dict


def preparar_datos_deposito(transaccion) -> Dict[str, Any]:
    """
    Construye los datos necesarios para realizar el depósito según el método de pago.
    """
    metodo_pago = getattr(transaccion, 'metodo_pago', None)
    if not metodo_pago:
        raise DepositoSimuladorError('La transacción no tiene método de pago asignado.')

    datos_metodo = transaccion.datos_metodo_pago if isinstance(transaccion.datos_metodo_pago, dict) else {}
    campos_dict = _obtener_campos_metodo_pago(transaccion)
    metodo_nombre = (metodo_pago.nombre or '').lower()

    metadata = {
        'metodo_pago_id': metodo_pago.id,
        'metodo_pago_nombre': metodo_pago.nombre,
        'campos': datos_metodo.get('campos', []),
    }

    if 'billetera' in metodo_nombre:
        numero_billetera = campos_dict.get('numero_telefono') or campos_dict.get('numero_billetera')
        if not numero_billetera:
            raise DepositoSimuladorError('Falta el número de billetera para realizar el depósito.')

        metadata['destino'] = {
            'tipo': 'billetera',
            'numero_billetera': numero_billetera,
        }
        return {
            'requiere_deposito': True,
            'datos_pasarela': {
                'transaccion_id': transaccion.id_transaccion,
                'tipo_operacion': 'deposito',
                'numero_billetera': numero_billetera,
            },
            'metadata': metadata,
        }

    if 'cuenta bancaria' in metodo_nombre or 'cuenta' in metodo_nombre or 'transferencia' in metodo_nombre:
        numero_cuenta = campos_dict.get('numero_cuenta')
        if not numero_cuenta:
            raise DepositoSimuladorError('Falta el número de cuenta bancaria para realizar el depósito.')

        referencia = generar_referencia_deposito(transaccion.id_transaccion)
        metadata['destino'] = {
            'tipo': 'transferencia',
            'numero_cuenta': numero_cuenta,
            'banco': campos_dict.get('banco'),
            'titular': campos_dict.get('titular'),
            'documento': campos_dict.get('documento'),
        }
        metadata['referencia_transferencia'] = referencia

        return {
            'requiere_deposito': True,
            'datos_pasarela': {
                'transaccion_id': transaccion.id_transaccion,
                'tipo_operacion': 'deposito',
                'numero_comprobante': referencia,
            },
            'metadata': metadata,
        }

    raise DepositoSimuladorError('El método de pago seleccionado no soporta depósitos automáticos.')


def registrar_deposito_en_simulador(
    transaccion,
    usuario_email: Optional[str] = None,
    extra_payload: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """
    Ejecuta el depósito en el simulador para las transacciones con entrega electrónica.
    """
    metodo_pago = getattr(transaccion, 'metodo_pago', None)
    if not metodo_pago:
        return {
            'estado': 'omitido',
            'motivo': 'La transacción no tiene método de pago configurado.',
        }

    if metodo_pago.requiere_retiro_fisico:
        return {
            'estado': 'omitido',
            'motivo': 'El método de pago seleccionado requiere retiro físico.',
        }

    registro_actual = transaccion.registro_deposito if isinstance(transaccion.registro_deposito, dict) else {}
    if registro_actual.get('estado') == 'exito':
        raise DepositoSimuladorError('El depósito ya fue registrado previamente en el simulador.')

    try:
        datos_deposito = preparar_datos_deposito(transaccion)
    except DepositoSimuladorError:
        raise
    except Exception as error:
        raise DepositoSimuladorError(str(error)) from error

    if not datos_deposito.get('requiere_deposito'):
        return {
            'estado': 'omitido',
            'motivo': 'Este método de pago no requiere depósito automático.',
            'metadata': datos_deposito.get('metadata', {}),
        }

    datos_pasarela = datos_deposito['datos_pasarela'].copy()
    if usuario_email:
        datos_pasarela.setdefault('procesado_por', usuario_email)
    if extra_payload:
        datos_pasarela.update(extra_payload)

    pasarela_service = PasarelaService()
    resultado_deposito = pasarela_service.procesar_pago(
        monto=float(transaccion.monto_destino),
        metodo_cobro=metodo_pago.nombre,
        moneda=transaccion.moneda_destino.codigo,
        escenario="exito",
        datos_adicionales=datos_pasarela
    )

    if not resultado_deposito.get('success'):
        raise DepositoSimuladorError(resultado_deposito.get('error', 'No se pudo registrar el depósito en el simulador.'))

    respuesta_pasarela = resultado_deposito.get('data', {})
    estado_pasarela = (respuesta_pasarela.get('estado') or '').lower()
    if estado_pasarela != 'exito':
        motivo = respuesta_pasarela.get('motivo_rechazo', 'El simulador no confirmó el depósito.')
        raise DepositoSimuladorError(motivo)

    return {
        'estado': respuesta_pasarela.get('estado'),
        'id_pago_externo': respuesta_pasarela.get('id_pago'),
        'respuesta': respuesta_pasarela,
        'payload_enviado': {
            'monto': float(transaccion.monto_destino),
            'moneda': transaccion.moneda_destino.codigo,
            'metodo_pasarela': pasarela_service._mapear_metodo(metodo_pago.nombre),
            'datos_pasarela': datos_pasarela,
        },
        'metadata': datos_deposito['metadata'],
        'registrado_en': timezone.now().isoformat(),
    }
