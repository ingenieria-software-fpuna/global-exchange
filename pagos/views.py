from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, Http404
from django.urls import reverse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from django.db import transaction
from django.db.models import Q, Count
from decimal import Decimal, ROUND_HALF_UP
import json
from datetime import datetime, date
import logging

from transacciones.models import Transaccion, TipoOperacion, EstadoTransaccion
from .models import PagoPasarela
from .forms import BilleteraElectronicaForm, TarjetaDebitoForm, TransferenciaBancariaForm, TarjetaCreditoLocalForm
from .services import PasarelaService, StripeService
from monedas.models import Moneda
from metodo_pago.models import MetodoPago
from metodo_cobro.models import MetodoCobro
from clientes.models import Cliente
from tasa_cambio.models import TasaCambio
from configuracion.models import ConfiguracionSistema
from django.db.models import Sum
from datetime import datetime, timedelta
from notificaciones.signals import notificar_pago_exitoso

logger = logging.getLogger(__name__)

# ============================================================================
# FUNCIONES AUXILIARES PARA PAGOS CON PASARELA
# ============================================================================

def _procesar_pago_con_pasarela(request, transaccion, datos_formulario, nombre_metodo, datos_adicionales=None):
    """
    Función auxiliar para procesar pagos a través de la pasarela.
    
    Args:
        request: HttpRequest objeto
        transaccion: Objeto Transaccion
        datos_formulario: Datos del formulario validado
        nombre_metodo: Nombre del método de pago (ej: "Billetera Electrónica")
        datos_adicionales: Datos adicionales para enviar a la pasarela
        
    Returns:
        HttpResponse: Redirección al resumen o template con error
    """
    try:
        with transaction.atomic():
            # Inicializar servicio de pasarela
            pasarela_service = PasarelaService()
            
            # Determinar el monto según el tipo de operación
            if transaccion.tipo_operacion.codigo == 'VENTA':
                # En ventas, el cliente paga el monto en PYG (moneda_destino)
                monto_pago = float(transaccion.monto_destino)
                moneda_pago = transaccion.moneda_destino.codigo
            else:
                # En compras, el cliente paga el monto en PYG (moneda_origen)
                monto_pago = float(transaccion.monto_origen)
                moneda_pago = transaccion.moneda_origen.codigo
            
            # Preparar datos adicionales
            datos_pago = datos_adicionales or {}
            datos_pago.update({
                'transaccion_id': transaccion.id_transaccion,
                'metodo_cobro_original': nombre_metodo,
                'procesado_por': request.user.email,
            })
            
            # Enviar pago a la pasarela
            logger.info(f"Enviando pago a pasarela - Transacción: {transaccion.id_transaccion}, Método: {nombre_metodo}")
            resultado = pasarela_service.procesar_pago(
                monto=monto_pago,
                metodo_cobro=transaccion.metodo_cobro.nombre,
                moneda=moneda_pago,
                escenario="exito",  # Por defecto, simular éxito
                datos_adicionales=datos_pago
            )
            logger.info(f"Respuesta de pasarela - Transacción: {transaccion.id_transaccion}, Resultado: {resultado}")
            
            if resultado['success']:
                # Crear registro del pago en pasarela
                pago_pasarela = PagoPasarela.objects.create(
                    transaccion=transaccion,
                    id_pago_externo=resultado['data']['id_pago'],
                    monto=monto_pago,
                    metodo_pasarela=pasarela_service._mapear_metodo(transaccion.metodo_cobro.nombre),
                    moneda=moneda_pago,
                    estado=resultado['data']['estado'],
                    datos_pago=datos_pago,
                    respuesta_pasarela=resultado['data'],
                    fecha_procesamiento=timezone.now()
                )
                
                # Manejar el resultado según el estado
                if resultado['data']['estado'].lower() == 'exito':
                    # Pago exitoso
                    estado_pagada = EstadoTransaccion.objects.get(codigo=EstadoTransaccion.PAGADA)
                    transaccion.estado = estado_pagada
                    transaccion.fecha_pago = timezone.now()
                    
                    # Agregar información a las observaciones
                    transaccion.observaciones += f"\nPago procesado con {nombre_metodo} el {timezone.now()} por {request.user.email}"
                    transaccion.observaciones += f"\nID Pago Pasarela: {resultado['data']['id_pago']}"
                    if datos_adicionales:
                        for key, value in datos_adicionales.items():
                            if key not in ['pin_autorizado', 'numero_tarjeta']:  # Excluir datos sensibles
                                transaccion.observaciones += f"\n{key}: {value}"
                    
                    transaccion.save()
                    
                    # Crear notificación de pago exitoso
                    notificar_pago_exitoso(
                        transaccion=transaccion,
                        monto_pago=monto_pago,
                        moneda_pago=moneda_pago,
                        metodo_pago=nombre_metodo
                    )
                    
                    messages.success(request, f'¡Pago procesado exitosamente con {nombre_metodo.lower()}!')
                    return redirect('transacciones:resumen_transaccion', transaccion_id=transaccion.id_transaccion)
                
                elif resultado['data']['estado'].lower() == 'fallo':
                    # Pago fallido - mostrar el motivo específico del rechazo
                    motivo_rechazo = resultado['data'].get('motivo_rechazo', 'Pago rechazado por la pasarela')
                    logger.warning(f"Pago fallido - Transacción: {transaccion.id_transaccion}, Motivo: {motivo_rechazo}")
                    
                    # Agregar información del fallo a las observaciones
                    transaccion.observaciones += f"\nIntento de pago fallido con {nombre_metodo} el {timezone.now()}"
                    transaccion.observaciones += f"\nID Pago Pasarela: {resultado['data']['id_pago']}"
                    transaccion.observaciones += f"\nMotivo del rechazo: {motivo_rechazo}"
                    transaccion.save()
                    
                    messages.error(request, f'Pago rechazado: {motivo_rechazo}')
                    # No redirigir, permitir que el usuario intente nuevamente
                    return None
                
                else:
                    # Pago pendiente u otro estado
                    messages.warning(request, f'El pago está {resultado["data"]["estado"]}. Se le notificará cuando se complete.')
                    return redirect('transacciones:resumen_transaccion', transaccion_id=transaccion.id_transaccion)
                
            else:
                # Error en la pasarela
                error_msg = resultado.get('error', 'Error desconocido en la pasarela')
                
                # Crear registro del intento fallido
                PagoPasarela.objects.create(
                    transaccion=transaccion,
                    id_pago_externo=f"ERROR-{timezone.now().strftime('%Y%m%d%H%M%S')}",
                    monto=monto_pago,
                    metodo_pasarela=pasarela_service._mapear_metodo(transaccion.metodo_cobro.nombre),
                    moneda=moneda_pago,
                    estado='fallo',
                    datos_pago=datos_pago,
                    mensaje_error=error_msg
                )
                
                if resultado.get('error_type') == 'connection_error':
                    messages.error(request, 'No se pudo conectar con la pasarela de pagos. Por favor, intente más tarde.')
                elif resultado.get('error_type') == 'timeout':
                    messages.error(request, 'La pasarela de pagos no respondió a tiempo. Por favor, intente más tarde.')
                else:
                    messages.error(request, f'Error al procesar el pago: {error_msg}')
                
                # No redirigir, permanecer en la página para reintento
                return None
                
    except Exception as e:
        messages.error(request, f'Error inesperado al procesar el pago: {str(e)}')
        return None


# ============================================================================
# VISTAS PARA PROCESAMIENTO DE PAGOS POR MÉTODO DE COBRO
# ============================================================================

@login_required
def pago_billetera_electronica(request, transaccion_id):
    """
    Vista para procesar pago con billetera electrónica.
    """
    transaccion = get_object_or_404(
        Transaccion.objects.select_related(
            'cliente', 'usuario', 'metodo_cobro', 'moneda_origen', 'moneda_destino'
        ),
        id_transaccion=transaccion_id
    )
    
    # Verificar permisos
    if transaccion.usuario != request.user:
        if transaccion.cliente and not transaccion.cliente.usuarios_asociados.filter(id=request.user.id).exists():
            raise Http404("Transacción no encontrada")
    
    # Verificar que la transacción esté pendiente
    if transaccion.estado.codigo != EstadoTransaccion.PENDIENTE:
        messages.error(request, 'Esta transacción ya no se puede procesar.')
        return redirect('transacciones:resumen_transaccion', transaccion_id=transaccion_id)
    
    if transaccion.esta_expirada():
        transaccion.cancelar_por_expiracion()
        messages.error(request, 'La transacción ha expirado y fue cancelada automáticamente.')
        return redirect('transacciones:resumen_transaccion', transaccion_id=transaccion_id)

    if request.method == 'POST':
        form = BilleteraElectronicaForm(request.POST)
        if form.is_valid():
            # Procesar el pago a través de la pasarela
            resultado = _procesar_pago_con_pasarela(
                request, 
                transaccion, 
                form.cleaned_data, 
                'Billetera Electrónica',
                datos_adicionales={
                    'telefono': form.cleaned_data['numero_telefono'],
                    'pin_autorizado': True  # No enviamos el PIN real por seguridad
                }
            )
            
            # Si hay resultado, redirigir (éxito) - si es None, continuar para mostrar formulario con mensajes de error
            if resultado:
                return resultado
    else:
        form = BilleteraElectronicaForm()
    
    context = {
        'transaccion': transaccion,
        'form': form,
        'tiempo_restante': (transaccion.fecha_expiracion - timezone.now()).total_seconds() if not transaccion.esta_expirada() else 0,
    }
    
    return render(request, 'pagos/pago_billetera_electronica.html', context)


@login_required
def pago_tarjeta_debito(request, transaccion_id):
    """
    Vista para procesar pago con tarjeta de débito.
    """
    transaccion = get_object_or_404(
        Transaccion.objects.select_related(
            'cliente', 'usuario', 'metodo_cobro', 'moneda_origen', 'moneda_destino'
        ),
        id_transaccion=transaccion_id
    )
    
    # Verificar permisos
    if transaccion.usuario != request.user:
        if transaccion.cliente and not transaccion.cliente.usuarios_asociados.filter(id=request.user.id).exists():
            raise Http404("Transacción no encontrada")
    
    # Verificar que la transacción esté pendiente
    if transaccion.estado.codigo != EstadoTransaccion.PENDIENTE:
        messages.error(request, 'Esta transacción ya no se puede procesar.')
        return redirect('transacciones:resumen_transaccion', transaccion_id=transaccion_id)
    
    if transaccion.esta_expirada():
        transaccion.cancelar_por_expiracion()
        messages.error(request, 'La transacción ha expirado y fue cancelada automáticamente.')
        return redirect('transacciones:resumen_transaccion', transaccion_id=transaccion_id)

    if request.method == 'POST':
        form = TarjetaDebitoForm(request.POST)
        if form.is_valid():
            # Enmascarar datos sensibles para el log
            numero_tarjeta = form.cleaned_data['numero_tarjeta'].replace(' ', '')
            numero_enmascarado = '**** **** **** ' + numero_tarjeta[-4:] if len(numero_tarjeta) >= 4 else '****'
            
            # Procesar el pago a través de la pasarela
            resultado = _procesar_pago_con_pasarela(
                request, 
                transaccion, 
                form.cleaned_data, 
                'Tarjeta de Débito',
                datos_adicionales={
                    'numero_tarjeta': numero_tarjeta,  # Número sin enmascarar para la pasarela
                    'numero_tarjeta_enmascarado': numero_enmascarado,
                    'nombre_titular': form.cleaned_data['nombre_titular'],
                    'fecha_vencimiento': form.cleaned_data['fecha_vencimiento']
                    # No incluimos CVV por seguridad
                }
            )
            
            # Si hay resultado, redirigir (éxito) - si es None, continuar para mostrar formulario con mensajes de error
            if resultado:
                return resultado
    else:
        form = TarjetaDebitoForm()
    
    context = {
        'transaccion': transaccion,
        'form': form,
        'tiempo_restante': (transaccion.fecha_expiracion - timezone.now()).total_seconds() if not transaccion.esta_expirada() else 0,
    }
    
    return render(request, 'pagos/pago_tarjeta_debito.html', context)


@login_required
def pago_transferencia_bancaria(request, transaccion_id):
    """
    Vista para procesar pago con transferencia bancaria.
    Muestra los datos de la cuenta destino y permite ingresar el comprobante.
    """
    transaccion = get_object_or_404(
        Transaccion.objects.select_related(
            'cliente', 'usuario', 'metodo_cobro', 'moneda_origen', 'moneda_destino'
        ),
        id_transaccion=transaccion_id
    )
    
    # Verificar permisos
    if transaccion.usuario != request.user:
        if transaccion.cliente and not transaccion.cliente.usuarios_asociados.filter(id=request.user.id).exists():
            raise Http404("Transacción no encontrada")
    
    # Verificar que la transacción esté pendiente
    if transaccion.estado.codigo != EstadoTransaccion.PENDIENTE:
        messages.error(request, 'Esta transacción ya no se puede procesar.')
        return redirect('transacciones:resumen_transaccion', transaccion_id=transaccion_id)
    
    if transaccion.esta_expirada():
        transaccion.cancelar_por_expiracion()
        messages.error(request, 'La transacción ha expirado y fue cancelada automáticamente.')
        return redirect('transacciones:resumen_transaccion', transaccion_id=transaccion_id)
    
    # Datos de cuenta bancaria de la empresa (esto podría venir de configuración)
    datos_cuenta = {
        'banco': 'Banco Global Exchange',
        'titular': 'Global Exchange S.A.',
        'numero_cuenta': '1234567890',
        'tipo_cuenta': 'Cuenta Corriente',
        'ruc': '80123456-7',
        'moneda': transaccion.moneda_destino.codigo if transaccion.tipo_operacion.codigo == 'COMPRA' else transaccion.moneda_origen.codigo
    }

    if request.method == 'POST':
        form = TransferenciaBancariaForm(request.POST)
        if form.is_valid():
            # Procesar el pago a través de la pasarela
            resultado = _procesar_pago_con_pasarela(
                request, 
                transaccion, 
                form.cleaned_data, 
                'Transferencia Bancaria',
                datos_adicionales={
                    'numero_comprobante': form.cleaned_data['numero_comprobante'],
                    'banco_origen': form.cleaned_data['banco_origen'],
                    'fecha_transferencia': form.cleaned_data['fecha_transferencia'].isoformat(),
                    'observaciones': form.cleaned_data.get('observaciones', ''),
                    'cuenta_destino': datos_cuenta['numero_cuenta']
                }
            )
            
            # Si hay resultado, redirigir (éxito) - si es None, continuar para mostrar formulario con mensajes de error
            if resultado:
                return resultado
    else:
        form = TransferenciaBancariaForm()
    
    context = {
        'transaccion': transaccion,
        'form': form,
        'datos_cuenta': datos_cuenta,
        'tiempo_restante': (transaccion.fecha_expiracion - timezone.now()).total_seconds() if not transaccion.esta_expirada() else 0,
    }
    
    return render(request, 'pagos/pago_transferencia_bancaria.html', context)


# ============================================================================
# WEBHOOK PARA RECIBIR NOTIFICACIONES DE LA PASARELA
# ============================================================================

@csrf_exempt
@require_http_methods(["POST"])
def webhook_pago(request):
    """
    Webhook para recibir notificaciones de la pasarela de pagos.
    """
    try:
        # Obtener datos del webhook
        data = json.loads(request.body)
        
        id_pago = data.get('id_pago')
        estado = data.get('estado')
        
        if not id_pago or not estado:
            return JsonResponse({'error': 'Datos incompletos'}, status=400)
        
        # Buscar el pago en nuestra base de datos
        try:
            pago_pasarela = PagoPasarela.objects.get(id_pago_externo=id_pago)
        except PagoPasarela.DoesNotExist:
            return JsonResponse({'error': 'Pago no encontrado'}, status=404)
        
        # Actualizar el estado del pago
        with transaction.atomic():
            pago_pasarela.estado = estado
            pago_pasarela.respuesta_pasarela.update(data)
            pago_pasarela.save()
            
            # Si el pago fue exitoso y la transacción aún está pendiente, actualizarla
            if estado.lower() == 'exito' and pago_pasarela.transaccion.estado.codigo == EstadoTransaccion.PENDIENTE:
                estado_pagada = EstadoTransaccion.objects.get(codigo=EstadoTransaccion.PAGADA)
                pago_pasarela.transaccion.estado = estado_pagada
                pago_pasarela.transaccion.fecha_pago = timezone.now()
                pago_pasarela.transaccion.observaciones += f"\nPago confirmado por webhook el {timezone.now()}"
                pago_pasarela.transaccion.save()
                
                # Crear notificación de pago exitoso
                notificar_pago_exitoso(
                    transaccion=pago_pasarela.transaccion,
                    monto_pago=pago_pasarela.monto,
                    moneda_pago=pago_pasarela.moneda,
                    metodo_pago=pago_pasarela.metodo_pasarela
                )
                
            elif estado.lower() == 'fallo':
                # Si el pago falló, agregar información del motivo
                motivo_rechazo = data.get('motivo_rechazo', 'Fallo reportado por la pasarela')
                pago_pasarela.transaccion.observaciones += f"\nPago fallido reportado por webhook el {timezone.now()}"
                pago_pasarela.transaccion.observaciones += f"\nMotivo del rechazo: {motivo_rechazo}"
                pago_pasarela.transaccion.save()
        
        return JsonResponse({'status': 'ok'})
        
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON inválido'}, status=400)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def pago_tarjeta_credito_local(request, transaccion_id):
    """
    Vista para procesar pago con tarjeta de crédito local (Panal, Cabal).
    """
    transaccion = get_object_or_404(
        Transaccion.objects.select_related(
            'cliente', 'usuario', 'metodo_cobro', 'moneda_origen', 'moneda_destino'
        ),
        id_transaccion=transaccion_id
    )
    
    # Verificar permisos
    if transaccion.usuario != request.user:
        if transaccion.cliente and not transaccion.cliente.usuarios_asociados.filter(id=request.user.id).exists():
            raise Http404("Transacción no encontrada")
    
    # Verificar que la transacción esté pendiente
    if transaccion.estado.codigo != EstadoTransaccion.PENDIENTE:
        messages.error(request, 'Esta transacción ya no se puede procesar.')
        return redirect('transacciones:resumen_transaccion', transaccion_id=transaccion_id)
    
    if transaccion.esta_expirada():
        transaccion.cancelar_por_expiracion()
        messages.error(request, 'La transacción ha expirado y fue cancelada automáticamente.')
        return redirect('transacciones:resumen_transaccion', transaccion_id=transaccion_id)

    if request.method == 'POST':
        form = TarjetaCreditoLocalForm(request.POST)
        if form.is_valid():
            # Enmascarar datos sensibles para el log
            numero_tarjeta = form.cleaned_data['numero_tarjeta'].replace(' ', '')
            numero_enmascarado = '**** **** **** ' + numero_tarjeta[-4:] if len(numero_tarjeta) >= 4 else '****'
            
            # Calcular información de cuotas
            cuotas = int(form.cleaned_data['cuotas'])
            tipo_tarjeta = form.cleaned_data['tipo_tarjeta']
            
            # Procesar el pago a través de la pasarela
            resultado = _procesar_pago_con_pasarela(
                request, 
                transaccion, 
                form.cleaned_data, 
                'Tarjeta de Crédito Local',
                datos_adicionales={
                    'numero_tarjeta': numero_tarjeta,  # Número sin enmascarar para la pasarela
                    'numero_tarjeta_enmascarado': numero_enmascarado,
                    'nombre_titular': form.cleaned_data['nombre_titular'],
                    'fecha_vencimiento': form.cleaned_data['fecha_vencimiento'],
                    'tipo_tarjeta': tipo_tarjeta.title(),
                    'cuotas': cuotas,
                    'es_tarjeta_local': True,
                    'red_procesamiento': tipo_tarjeta
                    # No incluimos CVV por seguridad
                }
            )
            
            # Si hay resultado, redirigir (éxito) - si es None, continuar para mostrar formulario con mensajes de error
            if resultado:
                return resultado
    else:
        form = TarjetaCreditoLocalForm()
    
    # Calcular información de cuotas para mostrar al usuario
    if transaccion.tipo_operacion.codigo == 'VENTA':
        monto_total = float(transaccion.monto_destino)
    else:
        monto_total = float(transaccion.monto_origen)
    
    context = {
        'transaccion': transaccion,
        'form': form,
        'monto_total': monto_total,
        'tiempo_restante': (transaccion.fecha_expiracion - timezone.now()).total_seconds() if not transaccion.esta_expirada() else 0,
    }

    return render(request, 'pagos/pago_tarjeta_credito_local.html', context)


# ============================================================================
# VISTAS PARA STRIPE CHECKOUT
# ============================================================================

@login_required
def pago_stripe(request, transaccion_id):
    """
    Vista para procesar pago con Stripe Checkout.
    Crea una sesión de checkout y redirige al usuario a Stripe.
    """
    transaccion = get_object_or_404(
        Transaccion.objects.select_related(
            'cliente', 'usuario', 'metodo_cobro', 'moneda_origen', 'moneda_destino', 'tipo_operacion'
        ),
        id_transaccion=transaccion_id
    )

    # Verificar permisos
    if transaccion.usuario != request.user:
        if transaccion.cliente and not transaccion.cliente.usuarios_asociados.filter(id=request.user.id).exists():
            raise Http404("Transacción no encontrada")

    # Verificar que la transacción esté pendiente
    if transaccion.estado.codigo != EstadoTransaccion.PENDIENTE:
        messages.error(request, 'Esta transacción ya no se puede procesar.')
        return redirect('transacciones:resumen_transaccion', transaccion_id=transaccion_id)

    if transaccion.esta_expirada():
        transaccion.cancelar_por_expiracion()
        messages.error(request, 'La transacción ha expirado y fue cancelada automáticamente.')
        return redirect('transacciones:resumen_transaccion', transaccion_id=transaccion_id)

    # Determinar el monto según el tipo de operación
    if transaccion.tipo_operacion.codigo == 'VENTA':
        # En ventas, el cliente paga el monto en la moneda destino
        monto_pago = float(transaccion.monto_destino)
        moneda_pago = transaccion.moneda_destino.codigo
    else:
        # En compras, el cliente paga el monto en la moneda origen
        monto_pago = float(transaccion.monto_origen)
        moneda_pago = transaccion.moneda_origen.codigo

    # Inicializar servicio de Stripe
    stripe_service = StripeService()

    # Verificar que Stripe esté configurado
    if not stripe_service.esta_disponible():
        messages.error(request, 'El servicio de Stripe no está configurado correctamente.')
        return redirect('transacciones:resumen_transaccion', transaccion_id=transaccion_id)

    # Crear descripción del pago
    if transaccion.tipo_operacion.codigo == 'VENTA':
        descripcion = f"Venta de {transaccion.monto_origen} {transaccion.moneda_origen.codigo}"
    else:
        descripcion = f"Compra de {transaccion.monto_destino} {transaccion.moneda_destino.codigo}"

    # Crear sesión de checkout
    logger.info(f"Creando sesión Stripe para transacción: {transaccion.id_transaccion}")
    resultado = stripe_service.crear_sesion_checkout(
        monto=monto_pago,
        moneda=moneda_pago,
        transaccion_id=transaccion.id_transaccion,
        descripcion=descripcion,
        metadata={
            'usuario_email': request.user.email,
            'cliente_id': str(transaccion.cliente.id) if transaccion.cliente else '',
            'tipo_operacion': transaccion.tipo_operacion.codigo,
        }
    )

    if resultado['success']:
        # Crear registro del pago con estado pendiente
        try:
            with transaction.atomic():
                PagoPasarela.objects.create(
                    transaccion=transaccion,
                    id_pago_externo=resultado['session_id'],
                    monto=monto_pago,
                    metodo_pasarela='stripe',
                    moneda=moneda_pago,
                    estado='pendiente',
                    datos_pago={
                        'session_id': resultado['session_id'],
                        'descripcion': descripcion,
                        'procesado_por': request.user.email,
                    },
                    respuesta_pasarela={
                        'session_id': resultado['session_id'],
                        'payment_intent': resultado.get('payment_intent'),
                    }
                )

                # Agregar información a las observaciones
                transaccion.observaciones += f"\nSesión Stripe creada el {timezone.now()} por {request.user.email}"
                transaccion.observaciones += f"\nSession ID: {resultado['session_id']}"
                transaccion.save()

                logger.info(f"Redirigiendo a Stripe Checkout - Session ID: {resultado['session_id']}")
                # Redirigir al usuario a Stripe Checkout
                return redirect(resultado['url'])

        except Exception as e:
            logger.error(f"Error al crear registro de pago Stripe: {str(e)}")
            messages.error(request, f'Error al crear sesión de pago: {str(e)}')
            return redirect('transacciones:resumen_transaccion', transaccion_id=transaccion_id)
    else:
        # Error al crear la sesión
        error_msg = resultado.get('error', 'Error desconocido')
        error_type = resultado.get('error_type', 'unknown')

        logger.error(f"Error al crear sesión Stripe: {error_msg} (tipo: {error_type})")

        if error_type == 'authentication_error':
            messages.error(request, 'Error de configuración de Stripe. Por favor, contacte al administrador.')
        elif error_type == 'connection_error':
            messages.error(request, 'No se pudo conectar con Stripe. Por favor, intente más tarde.')
        else:
            messages.error(request, f'Error al procesar el pago: {error_msg}')

        return redirect('transacciones:resumen_transaccion', transaccion_id=transaccion_id)


def stripe_success(request):
    """
    Vista para manejar el retorno exitoso desde Stripe Checkout.
    No requiere @login_required porque el usuario viene de una redirección externa.
    """
    session_id = request.GET.get('session_id')

    if not session_id:
        # Si no hay usuario logueado, redirigir al login
        if not request.user.is_authenticated:
            messages.warning(request, 'Por favor inicie sesión para ver el resultado del pago.')
            return redirect(f'{settings.LOGIN_URL}?next=/pagos/stripe/success/?session_id={session_id}')
        messages.error(request, 'Sesión de pago no encontrada.')
        return redirect('tasa_cambio:dashboard')

    # Buscar el pago en nuestra base de datos
    try:
        pago_pasarela = PagoPasarela.objects.get(id_pago_externo=session_id)
        transaccion = pago_pasarela.transaccion

        # Verificar permisos solo si el usuario está autenticado
        if request.user.is_authenticated:
            if transaccion.usuario != request.user:
                if transaccion.cliente and not transaccion.cliente.usuarios_asociados.filter(id=request.user.id).exists():
                    raise Http404("Transacción no encontrada")
        else:
            # Si no está autenticado, guardar la URL y redirigir al login
            login_url = f'{settings.LOGIN_URL}?next=/pagos/stripe/success/?session_id={session_id}'
            return redirect(login_url)

        # Recuperar información de la sesión de Stripe
        stripe_service = StripeService()
        resultado = stripe_service.recuperar_sesion(session_id)

        if resultado['success']:
            session = resultado['session']
            payment_status = resultado['payment_status']

            # Actualizar el estado del pago
            with transaction.atomic():
                if payment_status == 'paid':
                    pago_pasarela.estado = 'exito'
                    pago_pasarela.respuesta_pasarela.update({
                        'payment_status': payment_status,
                        'payment_intent': resultado['payment_intent'],
                    })
                    pago_pasarela.fecha_procesamiento = timezone.now()
                    pago_pasarela.save()

                    # Actualizar el estado de la transacción si aún está pendiente
                    if transaccion.estado.codigo == EstadoTransaccion.PENDIENTE:
                        estado_pagada = EstadoTransaccion.objects.get(codigo=EstadoTransaccion.PAGADA)
                        transaccion.estado = estado_pagada
                        transaccion.fecha_pago = timezone.now()
                        transaccion.observaciones += f"\nPago confirmado con Stripe el {timezone.now()}"
                        transaccion.observaciones += f"\nPayment Intent: {resultado['payment_intent']}"
                        transaccion.save()
                        
                        # Crear notificación de pago exitoso
                        notificar_pago_exitoso(
                            transaccion=transaccion,
                            monto_pago=pago_pasarela.monto,
                            moneda_pago=pago_pasarela.moneda,
                            metodo_pago='Stripe'
                        )

                        messages.success(request, '¡Pago procesado exitosamente con Stripe!')
                    else:
                        messages.info(request, 'El pago ya fue procesado anteriormente.')

                elif payment_status == 'unpaid':
                    pago_pasarela.estado = 'pendiente'
                    pago_pasarela.save()
                    messages.warning(request, 'El pago aún está pendiente.')
                else:
                    messages.info(request, f'Estado del pago: {payment_status}')
        else:
            messages.error(request, 'No se pudo verificar el estado del pago.')

        return redirect('transacciones:resumen_transaccion', transaccion_id=transaccion.id_transaccion)

    except PagoPasarela.DoesNotExist:
        messages.error(request, 'Pago no encontrado.')
        return redirect('transacciones:mis_transacciones')
    except Exception as e:
        logger.error(f"Error al procesar retorno de Stripe: {str(e)}")
        messages.error(request, f'Error al procesar el pago: {str(e)}')
        return redirect('transacciones:mis_transacciones')


def stripe_cancel(request):
    """
    Vista para manejar la cancelación del pago en Stripe Checkout.
    No requiere @login_required porque el usuario viene de una redirección externa.
    """
    # Verificar si el usuario está autenticado
    if not request.user.is_authenticated:
        messages.warning(request, 'Pago cancelado. Por favor inicie sesión.')
        return redirect(settings.LOGIN_URL)

    messages.warning(request, 'El pago fue cancelado. Puede intentar nuevamente.')

    # Redirigir al dashboard
    return redirect('tasa_cambio:dashboard')


@csrf_exempt
@require_http_methods(["POST"])
def stripe_webhook(request):
    """
    Webhook para recibir notificaciones de eventos de Stripe.
    """
    payload = request.body
    sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')

    # En desarrollo local sin Stripe CLI, permitir webhooks sin firma
    # IMPORTANTE: Nunca usar esto en producción
    if settings.DEBUG and not sig_header and not settings.STRIPE_WEBHOOK_SECRET:
        logger.warning("Webhook sin verificación - solo para desarrollo local")
        try:
            event = json.loads(payload)
            event_type = event.get('type')
        except json.JSONDecodeError:
            return JsonResponse({'error': 'JSON inválido'}, status=400)
    else:
        # Verificación normal con firma
        if not sig_header:
            logger.error("Webhook Stripe sin firma")
            return JsonResponse({'error': 'Firma ausente'}, status=400)

        # Verificar el webhook
        stripe_service = StripeService()
        resultado = stripe_service.verificar_webhook(payload, sig_header)

        if not resultado['success']:
            logger.error(f"Error al verificar webhook Stripe: {resultado.get('error')}")
            return JsonResponse({'error': resultado.get('error')}, status=400)

        event = resultado['event']
        event_type = resultado['type']

    logger.info(f"Webhook Stripe recibido - Tipo: {event_type}")

    try:
        # Manejar diferentes tipos de eventos
        if event_type == 'checkout.session.completed':
            session = event['data']['object']
            session_id = session['id']
            payment_status = session.get('payment_status')

            # Buscar el pago en nuestra base de datos
            try:
                pago_pasarela = PagoPasarela.objects.get(id_pago_externo=session_id)

                with transaction.atomic():
                    if payment_status == 'paid':
                        pago_pasarela.estado = 'exito'
                        pago_pasarela.respuesta_pasarela.update(session)
                        pago_pasarela.fecha_procesamiento = timezone.now()
                        pago_pasarela.save()

                        # Actualizar transacción si aún está pendiente
                        if pago_pasarela.transaccion.estado.codigo == EstadoTransaccion.PENDIENTE:
                            estado_pagada = EstadoTransaccion.objects.get(codigo=EstadoTransaccion.PAGADA)
                            pago_pasarela.transaccion.estado = estado_pagada
                            pago_pasarela.transaccion.fecha_pago = timezone.now()
                            pago_pasarela.transaccion.observaciones += f"\nPago confirmado por webhook Stripe el {timezone.now()}"
                            pago_pasarela.transaccion.save()
                            
                            # Crear notificación de pago exitoso
                            notificar_pago_exitoso(
                                transaccion=pago_pasarela.transaccion,
                                monto_pago=pago_pasarela.monto,
                                moneda_pago=pago_pasarela.moneda,
                                metodo_pago='Stripe'
                            )

                            logger.info(f"Transacción {pago_pasarela.transaccion.id_transaccion} marcada como pagada")

            except PagoPasarela.DoesNotExist:
                logger.warning(f"Pago no encontrado para session_id: {session_id}")

        elif event_type == 'payment_intent.payment_failed':
            payment_intent = event['data']['object']
            payment_intent_id = payment_intent['id']

            # Buscar el pago por payment_intent
            try:
                pago_pasarela = PagoPasarela.objects.filter(
                    respuesta_pasarela__payment_intent=payment_intent_id
                ).first()

                if pago_pasarela:
                    with transaction.atomic():
                        pago_pasarela.estado = 'fallo'
                        pago_pasarela.mensaje_error = payment_intent.get('last_payment_error', {}).get('message', 'Pago fallido')
                        pago_pasarela.respuesta_pasarela.update(payment_intent)
                        pago_pasarela.save()

                        # Agregar información del fallo a la transacción
                        pago_pasarela.transaccion.observaciones += f"\nPago fallido reportado por Stripe el {timezone.now()}"
                        pago_pasarela.transaccion.observaciones += f"\nMotivo: {pago_pasarela.mensaje_error}"
                        pago_pasarela.transaccion.save()

                        logger.warning(f"Pago fallido para transacción {pago_pasarela.transaccion.id_transaccion}")

            except Exception as e:
                logger.error(f"Error al procesar payment_intent.payment_failed: {str(e)}")

        return JsonResponse({'status': 'success'})

    except Exception as e:
        logger.error(f"Error al procesar webhook Stripe: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)