from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, Http404
from django.urls import reverse
from django.views.decorators.http import require_http_methods
from django.views.generic import ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from django.db import transaction
from django.db.models import Q, Count
from decimal import Decimal, ROUND_HALF_UP
import json
from datetime import datetime, date

from .models import Transaccion, TipoOperacion, EstadoTransaccion
from monedas.models import Moneda
from metodo_pago.models import MetodoPago
from metodo_cobro.models import MetodoCobro
from clientes.models import Cliente
from tasa_cambio.models import TasaCambio
from configuracion.models import ConfiguracionSistema
from django.db.models import Sum
from datetime import datetime, timedelta


def validar_limites_transaccion(monto_origen, moneda_origen, cliente=None, usuario=None):
    """
    Valida todos los límites para una transacción:
    1. Límite por transacción del cliente
    2. Límite por transacción de la moneda
    3. Límites diarios y mensuales globales
    
    Returns:
        dict: {
            'valido': bool,
            'mensaje': str,
            'limites_aplicados': list
        }
    """
    limites_aplicados = []
    errores = []
    
    # 1. Validar límite por transacción del cliente
    if cliente and cliente.monto_limite_transaccion:
        if monto_origen > cliente.monto_limite_transaccion:
            errores.append(f'El monto excede el límite por transacción del cliente: {cliente.monto_limite_transaccion}')
        limites_aplicados.append(f'Cliente: máx. {cliente.monto_limite_transaccion} PYG')
    
    # 2. Validar límite por transacción de la moneda
    if moneda_origen.monto_limite_transaccion:
        if monto_origen > moneda_origen.monto_limite_transaccion:
            errores.append(f'El monto excede el límite por transacción de la moneda {moneda_origen.codigo}: {moneda_origen.monto_limite_transaccion}')
        limites_aplicados.append(f'Moneda {moneda_origen.codigo}: máx. {moneda_origen.monto_limite_transaccion}')
    
    # 3. Validar límites diarios y mensuales
    config = ConfiguracionSistema.get_configuracion()
    
    # Obtener transacciones del usuario para calcular acumulados
    hoy = timezone.now().date()
    inicio_mes = hoy.replace(day=1)
    
    # Solo validar límites diarios/mensuales si hay cliente seleccionado
    # Sin cliente no se puede procesar la transacción de todas formas
    if usuario and cliente:
        # IMPORTANTE: Los límites son POR CLIENTE, no por usuario
        
        # Transacciones del día para este cliente específico
        transacciones_hoy_queryset = Transaccion.objects.filter(
            usuario=usuario,
            cliente=cliente,
            fecha_creacion__date=hoy,
            estado__codigo__in=['PAGADA', 'PENDIENTE']  # Solo transacciones válidas
        )
        
        # Transacciones del mes para este cliente específico
        transacciones_mes_queryset = Transaccion.objects.filter(
            usuario=usuario,
            cliente=cliente,
            fecha_creacion__date__gte=inicio_mes,
            estado__codigo__in=['PAGADA', 'PENDIENTE']
        )
        
        # Calcular totales
        transacciones_hoy = transacciones_hoy_queryset.aggregate(total=Sum('monto_origen'))['total'] or Decimal('0')
        transacciones_mes = transacciones_mes_queryset.aggregate(total=Sum('monto_origen'))['total'] or Decimal('0')
        
        # Validar límite diario
        if config.limite_diario_transacciones > 0:
            total_dia_con_nueva = transacciones_hoy + monto_origen
            if total_dia_con_nueva > config.limite_diario_transacciones:
                disponible_hoy = config.limite_diario_transacciones - transacciones_hoy
                errores.append(f'Excede el límite diario para {cliente.nombre_comercial}: {config.limite_diario_transacciones} (ya usado: {transacciones_hoy}, disponible: {disponible_hoy})')
            
            limites_aplicados.append(f'Límite diario ({cliente.nombre_comercial}): {config.limite_diario_transacciones} (usado: {transacciones_hoy})')
        
        # Validar límite mensual
        if config.limite_mensual_transacciones > 0:
            total_mes_con_nueva = transacciones_mes + monto_origen
            if total_mes_con_nueva > config.limite_mensual_transacciones:
                disponible_mes = config.limite_mensual_transacciones - transacciones_mes
                errores.append(f'Excede el límite mensual para {cliente.nombre_comercial}: {config.limite_mensual_transacciones} (ya usado: {transacciones_mes}, disponible: {disponible_mes})')
            
            limites_aplicados.append(f'Límite mensual ({cliente.nombre_comercial}): {config.limite_mensual_transacciones} (usado: {transacciones_mes})')
    
    elif usuario and not cliente:
        # Sin cliente: no validar límites diarios/mensuales, pero informar que se requiere cliente
        limites_aplicados.append('Seleccione un cliente para aplicar límites diarios/mensuales')
    
    return {
        'valido': len(errores) == 0,
        'mensaje': '; '.join(errores) if errores else 'Validación exitosa',
        'limites_aplicados': limites_aplicados
    }


@login_required
@require_http_methods(["POST"])
def iniciar_compra(request):
    """
    Inicia el proceso de compra de divisas creando una transacción pendiente.
    """
    try:
        # Obtener datos del formulario
        monto = Decimal(request.POST.get('monto', '0'))
        moneda_origen_codigo = request.POST.get('moneda_origen')
        moneda_destino_codigo = request.POST.get('moneda_destino')
        cliente_id = request.POST.get('cliente_id')
        
        # Verificar si viene metodo_cobro_id (nueva pantalla) o metodo_pago_id (dashboard antiguo)
        metodo_cobro_id = request.POST.get('metodo_cobro_id')
        metodo_pago_id = request.POST.get('metodo_pago_id')
        
        # Validaciones básicas
        if monto <= 0:
            messages.error(request, 'El monto debe ser mayor a cero.')
            return redirect('tasa_cambio:dashboard')
        
        # Obtener objetos del modelo
        try:
            moneda_origen = Moneda.objects.get(codigo=moneda_origen_codigo, es_activa=True)
            moneda_destino = Moneda.objects.get(codigo=moneda_destino_codigo, es_activa=True)
        except Moneda.DoesNotExist:
            messages.error(request, 'Las monedas seleccionadas no son válidas.')
            return redirect('tasa_cambio:dashboard')
        
        cliente = None
        if cliente_id:
            try:
                cliente = Cliente.objects.get(id=cliente_id, activo=True)
                # Verificar que el usuario puede operar con este cliente
                if not cliente.usuarios_asociados.filter(id=request.user.id).exists():
                    messages.error(request, 'No tiene permisos para operar con este cliente.')
                    return redirect('tasa_cambio:dashboard')
            except Cliente.DoesNotExist:
                messages.error(request, 'El cliente seleccionado no es válido.')
                return redirect('tasa_cambio:dashboard')
        
        # Manejar métodos de cobro (para compras) o métodos de pago (compatibilidad)
        metodo_cobro = None
        metodo_pago = None
        
        if metodo_cobro_id:
            # Nueva pantalla de compras - usa métodos de cobro Y métodos de pago
            # REQUERIR cliente para compras
            if not cliente_id:
                messages.error(request, 'Las compras de divisas requieren seleccionar un cliente.')
                return redirect('transacciones:comprar_divisas')
            
            try:
                metodo_cobro = MetodoCobro.objects.get(id=metodo_cobro_id, es_activo=True)
            except MetodoCobro.DoesNotExist:
                messages.error(request, 'El método de cobro seleccionado no es válido.')
                return redirect('transacciones:comprar_divisas')
            
            # Para la nueva pantalla también necesitamos método de pago (entrega)
            if not metodo_pago_id:
                messages.error(request, 'Debe seleccionar un método de entrega.')
                return redirect('transacciones:comprar_divisas')
                
            try:
                metodo_pago = MetodoPago.objects.get(id=metodo_pago_id, es_activo=True)
            except MetodoPago.DoesNotExist:
                messages.error(request, 'El método de entrega seleccionado no es válido.')
                return redirect('transacciones:comprar_divisas')
                
        elif metodo_pago_id:
            # Dashboard antiguo - usa métodos de pago (mantener compatibilidad)
            try:
                metodo_pago = MetodoPago.objects.get(id=metodo_pago_id, es_activo=True)
            except MetodoPago.DoesNotExist:
                messages.error(request, 'El método de pago seleccionado no es válido.')
                return redirect('tasa_cambio:dashboard')
        
        # Validar límites de transacción
        # Para compras: validar el monto que el cliente va a pagar contra el límite de la moneda que se compra
        validacion_limites = validar_limites_transaccion(
            monto_origen=monto,
            moneda_origen=moneda_destino,  # Moneda que se compra (AUD) para validar su límite
            cliente=cliente,
            usuario=request.user
        )
        
        if not validacion_limites['valido']:
            messages.error(request, f'Transacción rechazada: {validacion_limites["mensaje"]}')
            # Redirigir según desde donde vino
            if metodo_cobro_id:
                return redirect('transacciones:comprar_divisas')
            else:
                return redirect('tasa_cambio:dashboard')
        
        # Calcular la transacción usando la NUEVA lógica (igual que la vista previa)
        resultado = calcular_transaccion_completa(
            monto=monto,
            moneda_origen=moneda_origen,
            moneda_destino=moneda_destino,
            cliente=cliente,
            metodo_cobro=metodo_cobro,
            metodo_pago=metodo_pago
        )
        
        if not resultado['success']:
            error_msg = resultado.get('error', 'Error desconocido en el cálculo')
            messages.error(request, f'Error en el cálculo: {error_msg}')
            return redirect('tasa_cambio:dashboard')
        
        # Crear la transacción
        with transaction.atomic():
            tipo_compra = TipoOperacion.objects.get(codigo=TipoOperacion.COMPRA)
            estado_pendiente = EstadoTransaccion.objects.get(codigo=EstadoTransaccion.PENDIENTE)
            
            # Usar los datos de la nueva función de cálculo
            data = resultado['data']
            
            # Calcular porcentajes de comisión correctos
            porcentaje_comision_total = Decimal('0')
            if monto > 0:
                porcentaje_comision_total = (Decimal(str(data.get('comision_total', 0))) / monto * Decimal('100')).quantize(Decimal('0.0001'))
            
            nueva_transaccion = Transaccion(
                cliente=cliente,
                usuario=request.user,
                tipo_operacion=tipo_compra,
                moneda_origen=moneda_origen,
                moneda_destino=moneda_destino,
                monto_origen=monto,  # Lo que el cliente pagará
                monto_destino=Decimal(str(data['resultado'])),  # Lo que recibirá
                metodo_cobro=metodo_cobro,  # Para compras, usamos método de cobro
                metodo_pago=metodo_pago,    # Para compatibilidad con dashboard antiguo
                tasa_cambio=Decimal(str(data['precio_usado'])),  # Tasa ajustada con descuento
                porcentaje_comision=porcentaje_comision_total,  # Porcentaje calculado correctamente
                monto_comision=Decimal(str(data.get('comision_total', 0))),  # Monto total de comisión
                porcentaje_descuento=Decimal(str(data.get('descuento_pct', 0))),  # Porcentaje de descuento del cliente
                monto_descuento=Decimal(str(data.get('descuento_aplicado', 0))),  # Monto de descuento aplicado
                estado=estado_pendiente,
                ip_cliente=get_client_ip(request)
            )
            nueva_transaccion.save()
        
        messages.success(request, f'Transacción creada exitosamente: {nueva_transaccion.id_transaccion}')
        return redirect('transacciones:resumen_transaccion', transaccion_id=nueva_transaccion.id_transaccion)
        
    except Exception as e:
        messages.error(request, f'Error al crear la transacción: {str(e)}')
        return redirect('tasa_cambio:dashboard')


@login_required
def resumen_transaccion(request, transaccion_id):
    """
    Muestra el resumen detallado de una transacción antes del pago.
    """
    transaccion = get_object_or_404(
        Transaccion.objects.select_related(
            'cliente', 'cliente__tipo_cliente', 'usuario', 'tipo_operacion', 'estado',
            'moneda_origen', 'moneda_destino', 'metodo_pago', 'metodo_cobro'
        ),
        id_transaccion=transaccion_id
    )
    
    # Verificar que el usuario puede ver esta transacción
    if transaccion.usuario != request.user:
        # Si hay cliente, verificar que el usuario esté asociado
        if transaccion.cliente and not transaccion.cliente.usuarios_asociados.filter(id=request.user.id).exists():
            raise Http404("Transacción no encontrada")
    
    # Verificar si la transacción está expirada y debe cancelarse automáticamente
    if transaccion.estado.codigo == EstadoTransaccion.PENDIENTE and transaccion.esta_expirada():
        transaccion.cancelar_por_expiracion()
        messages.warning(request, 'Esta transacción ha expirado y fue cancelada automáticamente.')
    
    context = {
        'transaccion': transaccion,
        'resumen_financiero': transaccion.get_resumen_financiero(),  # Mantener compatibilidad
        'resumen_detallado': transaccion.get_resumen_detallado(),    # Nuevo resumen detallado
        'puede_pagar': transaccion.estado.codigo == EstadoTransaccion.PENDIENTE and not transaccion.esta_expirada(),
        'tiempo_restante': (transaccion.fecha_expiracion - timezone.now()).total_seconds() if not transaccion.esta_expirada() else 0,
    }
    
    return render(request, 'transacciones/resumen_transaccion.html', context)


@login_required
@require_http_methods(["POST"])
def procesar_pago(request, transaccion_id):
    """
    Redirige a la pantalla de pago específica según el método de cobro seleccionado.
    """
    transaccion = get_object_or_404(Transaccion, id_transaccion=transaccion_id)
    
    # Verificar permisos
    if transaccion.usuario != request.user:
        if transaccion.cliente and not transaccion.cliente.usuarios_asociados.filter(id=request.user.id).exists():
            raise Http404("Transacción no encontrada")
    
    # Verificar que se puede procesar el pago
    if transaccion.estado.codigo != EstadoTransaccion.PENDIENTE:
        messages.error(request, 'Esta transacción ya no se puede procesar.')
        return redirect('transacciones:resumen_transaccion', transaccion_id=transaccion_id)

    if transaccion.esta_expirada():
        # Marcar como cancelada automáticamente
        transaccion.cancelar_por_expiracion()
        messages.error(request, 'La transacción ha expirado y fue cancelada automáticamente.')
        return redirect('transacciones:resumen_transaccion', transaccion_id=transaccion_id)

    # Redirigir según el método de cobro
    metodo_cobro = transaccion.metodo_cobro.nombre.lower()
    
    if 'billetera electrónica' in metodo_cobro or 'billetera electronica' in metodo_cobro:
        return redirect('pagos:pago_billetera_electronica', transaccion_id=transaccion_id)
    elif 'tarjeta de débito' in metodo_cobro or 'tarjeta de debito' in metodo_cobro:
        return redirect('pagos:pago_tarjeta_debito', transaccion_id=transaccion_id)
    elif 'tarjeta de crédito local' in metodo_cobro or 'tarjeta de credito local' in metodo_cobro:
        return redirect('pagos:pago_tarjeta_credito_local', transaccion_id=transaccion_id)
    elif 'transferencia bancaria' in metodo_cobro:
        return redirect('pagos:pago_transferencia_bancaria', transaccion_id=transaccion_id)
    else:
        # Para otros métodos de cobro no implementados, procesar directamente
        try:
            with transaction.atomic():
                estado_pagada = EstadoTransaccion.objects.get(codigo=EstadoTransaccion.PAGADA)
                transaccion.estado = estado_pagada
                transaccion.fecha_pago = timezone.now()
                transaccion.observaciones += f"\nPago procesado el {timezone.now()} por {request.user.email}"
                transaccion.save()
                
            messages.success(request, '¡Pago procesado exitosamente! La transacción ha sido completada.')
            return redirect('transacciones:resumen_transaccion', transaccion_id=transaccion_id)
            
        except Exception as e:
            messages.error(request, f'Error al procesar el pago: {str(e)}')
            return redirect('transacciones:resumen_transaccion', transaccion_id=transaccion_id)


@login_required
@require_http_methods(["POST"])
def cancelar_transaccion(request, transaccion_id):
    """
    Cancela una transacción pendiente.
    """
    transaccion = get_object_or_404(Transaccion, id_transaccion=transaccion_id)
    
    # Verificar permisos
    if transaccion.usuario != request.user:
        if transaccion.cliente and not transaccion.cliente.usuarios_asociados.filter(id=request.user.id).exists():
            raise Http404("Transacción no encontrada")
    
    # Verificar que se puede cancelar
    if transaccion.estado.codigo != EstadoTransaccion.PENDIENTE:
        messages.error(request, 'Esta transacción ya no se puede cancelar.')
        return redirect('transacciones:resumen_transaccion', transaccion_id=transaccion_id)
    
    try:
        with transaction.atomic():
            estado_cancelada = EstadoTransaccion.objects.get(codigo=EstadoTransaccion.CANCELADA)
            transaccion.estado = estado_cancelada
            transaccion.observaciones += f"\nCancelada manualmente el {timezone.now()} por {request.user.email}"
            transaccion.save()
            
        messages.success(request, 'La transacción ha sido cancelada exitosamente.')
        return redirect('transacciones:resumen_transaccion', transaccion_id=transaccion_id)
        
    except Exception as e:
        messages.error(request, f'Error al cancelar la transacción: {str(e)}')
        return redirect('transacciones:resumen_transaccion', transaccion_id=transaccion_id)


@login_required
@require_http_methods(["POST"])
def cancelar_por_expiracion(request, transaccion_id):
    """
    API endpoint para cancelar una transacción automáticamente por expiración.
    """
    try:
        transaccion = get_object_or_404(Transaccion, id_transaccion=transaccion_id)
        
        # Verificar permisos
        if transaccion.usuario != request.user:
            if transaccion.cliente and not transaccion.cliente.usuarios_asociados.filter(id=request.user.id).exists():
                return JsonResponse({'success': False, 'error': 'Sin permisos'})
        
        # Verificar que esté pendiente y expirada
        if transaccion.estado.codigo != EstadoTransaccion.PENDIENTE:
            return JsonResponse({'success': False, 'error': 'Transacción ya no está pendiente'})
        
        if not transaccion.esta_expirada():
            return JsonResponse({'success': False, 'error': 'Transacción aún no ha expirado'})
        
        # Cancelar por expiración
        if transaccion.cancelar_por_expiracion():
            return JsonResponse({
                'success': True, 
                'message': 'Transacción cancelada automáticamente por expiración'
            })
        else:
            return JsonResponse({'success': False, 'error': 'No se pudo cancelar la transacción'})
            
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Error interno: {str(e)}'})


@login_required
@require_http_methods(["POST"])
def verificar_cambio_cotizacion(request, transaccion_id):
    """
    API endpoint para verificar si hay cambio de cotización en una transacción.
    """
    try:
        transaccion = get_object_or_404(Transaccion, id_transaccion=transaccion_id)
        
        # Debug: Log información de la transacción (se puede quitar en producción)
        # print(f"DEBUG: Transacción {transaccion_id} - Estado: {transaccion.estado.codigo} - Usuario: {transaccion.usuario.email}")
        
        # Verificar permisos
        if transaccion.usuario != request.user:
            if transaccion.cliente and not transaccion.cliente.usuarios_asociados.filter(id=request.user.id).exists():
                return JsonResponse({'success': False, 'error': 'Sin permisos'})
        
        # Verificar que esté pendiente o cancelada por cambio de tasa
        if transaccion.estado.codigo not in ['PENDIENTE', 'CANCELADA']:
            return JsonResponse({
                'success': False, 
                'error': f'Transacción ya no se puede procesar. Estado actual: {transaccion.estado.codigo}'
            })
            
        # Verificar expiración
        if transaccion.esta_expirada():
            return JsonResponse({'success': False, 'error': 'Transacción expirada'})
        
        # Verificar si hay cambio de cotización
        hay_cambio = not transaccion.tiene_tasa_actualizada()
        
        if not hay_cambio:          
            return JsonResponse({
                'success': True,
                'hay_cambio': False,
                'message': 'No hay cambio de cotización'
            })
        
        # Hay cambio, calcular nueva cotización
        try:
            # Determinar si es compra o venta y usar la función correcta
            if transaccion.moneda_origen.codigo == 'PYG':
                # COMPRA: PYG → otra moneda
                nueva_cotizacion = calcular_transaccion_completa(
                    monto=transaccion.monto_origen,
                    moneda_origen=transaccion.moneda_origen,
                    moneda_destino=transaccion.moneda_destino,
                    cliente=transaccion.cliente,
                    metodo_cobro=transaccion.metodo_cobro,
                    metodo_pago=transaccion.metodo_pago
                )
            else:
                # VENTA: otra moneda → PYG
                nueva_cotizacion = calcular_venta_completa(
                    monto=transaccion.monto_origen,
                    moneda_origen=transaccion.moneda_origen,
                    moneda_destino=transaccion.moneda_destino,
                    cliente=transaccion.cliente,
                    metodo_cobro=transaccion.metodo_cobro,
                    metodo_pago=transaccion.metodo_pago
                )
            
            if not nueva_cotizacion['success']:
                return JsonResponse({
                    'success': False,
                    'error': f'Error al calcular nueva cotización: {nueva_cotizacion["error"]}'
                })
            
            # Extraer datos del resultado
            datos = nueva_cotizacion['data']
            
            # Preparar datos para el modal
            response_data = {
                'success': True,
                'hay_cambio': True,
                'moneda_nombre': transaccion.moneda_destino.nombre,
                'moneda_simbolo': transaccion.moneda_destino.simbolo,
                # Datos originales
                'tasa_original': f"{transaccion.tasa_cambio:,.2f}",
                'monto_origen_original': f"{transaccion.monto_origen:,.0f}",
                'monto_destino_original': f"{transaccion.monto_destino:,.2f}",
                # Datos nuevos
                'tasa_nueva': f"{datos['precio_usado']:,.2f}",
                'monto_origen_nuevo': f"{datos['total']:,.0f}",
                'monto_destino_nuevo': f"{datos['resultado']:,.2f}",
                # Datos para crear nueva transacción
                'nueva_transaccion_datos': {
                    'monto_origen': str(datos['total']),
                    'monto_destino': str(datos['resultado']),
                    'tasa_cambio': str(datos['precio_usado']),
                    'total_comisiones': str(datos['comision_total']),
                    'descuento_aplicado': str(datos['descuento_aplicado']),
                    'detalle_calculo': datos.get('detalle', ''),
                }
            }
            
            return JsonResponse(response_data)
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Error al calcular nueva cotización: {str(e)}'
            })
            
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Error interno: {str(e)}'})


@login_required
@require_http_methods(["POST"])
def crear_con_nueva_cotizacion(request, transaccion_id):
    """
    API endpoint para crear una nueva transacción con la cotización actualizada.
    """
    try:
        transaccion_original = get_object_or_404(Transaccion, id_transaccion=transaccion_id)
        
        # Verificar permisos
        if transaccion_original.usuario != request.user:
            if transaccion_original.cliente and not transaccion_original.cliente.usuarios_asociados.filter(id=request.user.id).exists():
                return JsonResponse({'success': False, 'error': 'Sin permisos'})
        
        # Verificar que esté pendiente
        if transaccion_original.estado.codigo != 'PENDIENTE':
            return JsonResponse({'success': False, 'error': 'Transacción original ya no está pendiente'})
        
        # Obtener datos del cuerpo de la petición
        import json
        datos = json.loads(request.body)
        
        # Recalcular los datos completos para obtener información adicional
        if transaccion_original.moneda_origen.codigo == 'PYG':
            # COMPRA: PYG → otra moneda
            nueva_cotizacion = calcular_transaccion_completa(
                monto=transaccion_original.monto_origen,
                moneda_origen=transaccion_original.moneda_origen,
                moneda_destino=transaccion_original.moneda_destino,
                cliente=transaccion_original.cliente,
                metodo_cobro=transaccion_original.metodo_cobro,
                metodo_pago=transaccion_original.metodo_pago
            )
        else:
            # VENTA: otra moneda → PYG
            nueva_cotizacion = calcular_venta_completa(
                monto=transaccion_original.monto_origen,
                moneda_origen=transaccion_original.moneda_origen,
                moneda_destino=transaccion_original.moneda_destino,
                cliente=transaccion_original.cliente,
                metodo_cobro=transaccion_original.metodo_cobro,
                metodo_pago=transaccion_original.metodo_pago
            )
        
        if not nueva_cotizacion['success']:
            return JsonResponse({
                'success': False,
                'error': f'Error al calcular nueva cotización: {nueva_cotizacion["error"]}'
            })
        
        # Extraer datos completos
        datos_completos = nueva_cotizacion['data']
        
        # Extraer datos de comisión y descuento
        monto_comision = Decimal(str(datos_completos['comision_total']))
        porcentaje_descuento = Decimal(str(datos_completos.get('descuento_pct', 0)))
        
        # El monto de descuento ahora viene correctamente calculado desde las funciones
        monto_descuento = Decimal(str(datos_completos.get('descuento_aplicado', 0)))
        
        # Calcular porcentaje de comisión correctamente según el tipo de operación
        if transaccion_original.moneda_origen.codigo == 'PYG':
            # COMPRA: PYG → otra moneda
            # El porcentaje se calcula sobre el monto en PYG que el cliente paga
            monto_base_comision = transaccion_original.monto_origen
        else:
            # VENTA: otra moneda → PYG  
            # El porcentaje se calcula sobre el monto en PYG que el cliente recibe (subtotal)
            monto_base_comision = Decimal(str(datos_completos['subtotal']))
        
        porcentaje_comision = (monto_comision / monto_base_comision * 100) if monto_base_comision > 0 else Decimal('0')
        
        # Cancelar la transacción original
        with transaction.atomic():
            # Cancelar transacción original
            transaccion_original.cancelar_por_cambio_tasa()
            
            # Crear nueva transacción
            estado_pendiente = EstadoTransaccion.objects.get(codigo='PENDIENTE')
            
            nueva_transaccion = Transaccion.objects.create(
                usuario=transaccion_original.usuario,
                cliente=transaccion_original.cliente,
                tipo_operacion=transaccion_original.tipo_operacion,
                moneda_origen=transaccion_original.moneda_origen,
                moneda_destino=transaccion_original.moneda_destino,
                monto_origen=transaccion_original.monto_origen,
                monto_destino=Decimal(str(datos_completos['resultado'])),
                tasa_cambio=Decimal(str(datos_completos['precio_usado'])),
                # Agregar campos de comisiones y descuentos
                porcentaje_comision=porcentaje_comision,
                monto_comision=monto_comision,
                porcentaje_descuento=porcentaje_descuento,
                monto_descuento=monto_descuento,
                metodo_cobro=transaccion_original.metodo_cobro,
                metodo_pago=transaccion_original.metodo_pago,
                estado=estado_pendiente,
                observaciones=f"Transacción creada con nueva cotización (reemplaza a {transaccion_original.id_transaccion}). {datos_completos.get('detalle', '')}"
            )
            
            print(f"DEBUG: Nueva transacción creada con ID: {nueva_transaccion.id_transaccion}")
            
            return JsonResponse({
                'success': True,
                'message': 'Nueva transacción creada exitosamente',
                'redirect_url': reverse('transacciones:resumen_transaccion', kwargs={'transaccion_id': nueva_transaccion.id_transaccion})
            })
            
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Error interno: {str(e)}'})


@login_required
@require_http_methods(["POST"])
def cancelar_por_cambio_cotizacion(request, transaccion_id):
    """
    Cancela una transacción específicamente debido a cambio de cotización desde el modal.
    """
    try:
        transaccion = get_object_or_404(Transaccion, id_transaccion=transaccion_id)
        
        # Verificar permisos
        if transaccion.usuario != request.user:
            if transaccion.cliente and not transaccion.cliente.usuarios_asociados.filter(id=request.user.id).exists():
                return JsonResponse({'success': False, 'error': 'Sin permisos'})
        
        # Verificar que se puede cancelar
        if transaccion.estado.codigo not in ['PENDIENTE', 'CANCELADA']:
            return JsonResponse({'success': False, 'error': 'Esta transacción ya no se puede cancelar'})
        
        with transaction.atomic():
            estado_cancelada = EstadoTransaccion.objects.get(codigo='CANCELADA')
            transaccion.estado = estado_cancelada
            transaccion.observaciones += f"\nCancelada por cambio de cotización el {timezone.now()} por {request.user.email}"
            transaccion.save()
            
        return JsonResponse({
            'success': True,
            'message': 'Transacción cancelada por cambio de cotización'
        })
        
    except Exception as e:
        return JsonResponse({'success': False, 'error': f'Error interno: {str(e)}'})


def calcular_transaccion(monto, moneda_origen, moneda_destino, cliente=None, metodo_pago=None):
    """
    Calcula los detalles de una transacción usando la misma lógica del simulador.
    Reutiliza la lógica de tasa_cambio.views.simular_cambio_api
    """
    from tasa_cambio.views import simular_cambio_api
    from django.http import QueryDict
    
    # Simular una request para reutilizar la lógica existente
    class MockRequest:
        def __init__(self):
            self.GET = QueryDict(mutable=True)
            self.GET['monto'] = str(monto)
            self.GET['origen'] = moneda_origen.codigo
            self.GET['destino'] = moneda_destino.codigo
            if cliente:
                self.GET['cliente_id'] = str(cliente.id)
            if metodo_pago:
                self.GET['metodo_pago_id'] = str(metodo_pago.id)
            
            # Usar el primer usuario disponible como mock user
            from usuarios.models import Usuario
            self.user = Usuario.objects.first()
    
    mock_request = MockRequest()
    response = simular_cambio_api(mock_request)
    
    # Convertir la respuesta JSON a diccionario
    if hasattr(response, 'content'):
        content = json.loads(response.content.decode())
        if content.get('success'):
            # Agregar campos adicionales necesarios para la transacción
            data = content['data']
            # Usar 'resultado' si 'resultado_numerico' no existe
            data['monto_destino'] = Decimal(str(data.get('resultado_numerico', data.get('resultado', 0))))
            # Usar tasa_destino si tasa_origen es None
            tasa_origen = data.get('tasa_origen')
            if tasa_origen:
                data['tasa_utilizada'] = Decimal(str(tasa_origen.get('valor', 0)))
            else:
                tasa_destino = data.get('tasa_destino') or {}
                data['tasa_utilizada'] = Decimal(str(tasa_destino.get('valor', 0)))
            data['porcentaje_comision'] = Decimal(str(data.get('comision_pct', 0)))
            data['monto_comision'] = Decimal(str(data.get('comision_monto', 0)))
            # Manejar caso donde cliente puede ser None
            cliente_data = data.get('cliente') or {}
            data['porcentaje_descuento'] = Decimal(str(cliente_data.get('descuento', 0)))
            data['monto_descuento'] = Decimal(str(data.get('descuento_monto', 0)))
        return content
    
    return {'success': False, 'message': 'Error al calcular la transacción'}


@login_required
def comprar_divisas(request):
    """
    Vista para la pantalla dedicada de compra de divisas.
    Muestra un formulario específico para compras con métodos de cobro.
    """
    # Monedas activas para el selector
    monedas_activas = Moneda.objects.filter(es_activa=True).order_by('nombre')
    
    # Clientes asociados al usuario
    clientes_usuario = Cliente.objects.filter(
        activo=True,
        usuarios_asociados=request.user
    ).select_related('tipo_cliente').order_by('nombre_comercial')
    
    # Métodos de cobro activos (para recibir pago del cliente)
    metodos_cobro = MetodoCobro.objects.filter(es_activo=True).order_by('nombre')
    
    # Métodos de pago activos (para entregar divisas al cliente)
    metodos_pago = MetodoPago.objects.filter(es_activo=True).order_by('nombre')
    
    # Obtener parámetros de URL para pre-poblar el formulario (desde el simulador)
    moneda_origen_id = request.GET.get('moneda_origen')
    moneda_destino_id = request.GET.get('moneda_destino')
    cantidad = request.GET.get('cantidad')
    cliente_id = request.GET.get('cliente_id')
    
    context = {
        'titulo': 'Comprar Divisas',
        'monedas': monedas_activas,
        'clientes': clientes_usuario,
        'metodos_cobro': metodos_cobro,
        'metodos_pago': metodos_pago,
        'moneda_origen_preseleccionada': moneda_origen_id,
        'moneda_destino_preseleccionada': moneda_destino_id,
        'cantidad_preseleccionada': cantidad,
        'cliente_preseleccionado': cliente_id,
    }
    
    return render(request, 'transacciones/comprar_divisas.html', context)


@login_required
def api_validar_limites(request):
    """
    API endpoint para validar límites de transacción desde JavaScript
    """
    if request.method == 'GET':
        try:
            monto = Decimal(request.GET.get('monto', '0'))
            moneda_origen_codigo = request.GET.get('moneda_origen')
            cliente_id = request.GET.get('cliente_id')
            
            if monto <= 0 or not moneda_origen_codigo:
                return JsonResponse({
                    'valido': False,
                    'mensaje': 'Parámetros inválidos'
                })
            
            # Obtener objetos
            try:
                moneda_origen = Moneda.objects.get(codigo=moneda_origen_codigo, es_activa=True)
            except Moneda.DoesNotExist:
                return JsonResponse({
                    'valido': False,
                    'mensaje': 'Moneda no válida'
                })
            
            cliente = None
            if cliente_id:
                try:
                    cliente = Cliente.objects.get(id=cliente_id, activo=True)
                    # Verificar permisos
                    if not cliente.usuarios_asociados.filter(id=request.user.id).exists():
                        return JsonResponse({
                            'valido': False,
                            'mensaje': 'Sin permisos para este cliente'
                        })
                except Cliente.DoesNotExist:
                    return JsonResponse({
                        'valido': False,
                        'mensaje': 'Cliente no válido'
                    })
            
            # Validar límites
            validacion = validar_limites_transaccion(
                monto_origen=monto,
                moneda_origen=moneda_origen,
                cliente=cliente,
                usuario=request.user
            )
            
            return JsonResponse(validacion)
            
        except Exception as e:
            return JsonResponse({
                'valido': False,
                'mensaje': f'Error interno: {str(e)}'
            })
    
    return JsonResponse({'valido': False, 'mensaje': 'Método no permitido'})


def get_client_ip(request):
    """Obtiene la IP del cliente desde la request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip


def calcular_transaccion_completa(monto, moneda_origen, moneda_destino, cliente=None, metodo_cobro=None, metodo_pago=None):
    """
    Calcula el resultado completo de una transacción incluyendo:
    - Conversión usando tasas de cambio con descuento del cliente aplicado
    - Comisiones de método de cobro
    - Comisiones de método de pago/entrega
    - Descuentos de cliente
    - Total final
    
    Returns:
        dict: Diccionario con todos los datos de la transacción o error
    """
    try:
        # Validaciones iniciales
        if monto <= 0:
            return {'success': False, 'error': 'El monto debe ser mayor a cero'}
        
        # Obtener descuento del cliente
        descuento_pct = Decimal('0')
        if cliente and cliente.tipo_cliente and cliente.tipo_cliente.activo and cliente.tipo_cliente.descuento > 0:
            descuento_pct = Decimal(str(cliente.tipo_cliente.descuento))
        
        # LÓGICA :Cliente ingresa cuánto quiere PAGAR, sistema calcula cuánto RECIBE
        if moneda_origen.codigo != 'PYG':
            return {'success': False, 'error': 'Las compras solo se realizan con PYG como moneda origen'}
        
        # Obtener tasa de la divisa que va a comprar
        try:
            tasa_destino = TasaCambio.objects.get(moneda=moneda_destino, es_activa=True)
        except TasaCambio.DoesNotExist:
            return {'success': False, 'error': f'Tasa de cambio no disponible para {moneda_destino.codigo}'}
        
        # Aplicar descuento del cliente a la comisión de venta (como hace el simulador)
        comision_venta_ajustada = Decimal(str(tasa_destino.comision_venta))
        if descuento_pct > 0:
            comision_venta_ajustada = comision_venta_ajustada * (Decimal('1') - (descuento_pct / Decimal('100')))
        
        # Calcular precio de venta ajustado: precio_base + comision_venta_ajustada
        precio_usado = Decimal(str(tasa_destino.precio_base)) + comision_venta_ajustada
        tipo_operacion = 'venta' + (' (ajustada)' if descuento_pct > 0 else '')
        
        # LÓGICA DE CÁLCULO PARA COMPRAS:
        # 1. El monto ingresado es lo que el cliente quiere PAGAR (en PYG)
        monto_a_pagar = monto
        
        # 2. Calcular comisiones de métodos SOBRE el monto que va a pagar
        comision_cobro = Decimal('0')
        comision_pago = Decimal('0')
        
        if metodo_cobro and metodo_cobro.comision > 0:
            comision_cobro = monto_a_pagar * (Decimal(str(metodo_cobro.comision)) / Decimal('100'))
        
        if metodo_pago and metodo_pago.comision > 0:
            comision_pago = monto_a_pagar * (Decimal(str(metodo_pago.comision)) / Decimal('100'))
        
        comision_total = comision_cobro + comision_pago
        
        # 3. Calcular el monto neto disponible para la conversión (después de comisiones)
        monto_neto_conversion = monto_a_pagar - comision_total
        
        # 4. Convertir el monto neto a la divisa destino usando la tasa ajustada
        resultado_final = (monto_neto_conversion / precio_usado).quantize(
            Decimal('1.' + '0' * max(moneda_destino.decimales, 0)), 
            rounding=ROUND_HALF_UP
        )
        
        # 5. Calcular el monto real del descuento aplicado
        # El descuento es el ahorro en PYG que obtiene el cliente sobre la comisión de cambio
        descuento_aplicado = Decimal('0')
        if descuento_pct > 0:
            # El descuento se aplica sobre la comisión de venta
            comision_original = Decimal(str(tasa_destino.comision_venta))
            comision_con_descuento = comision_venta_ajustada
            descuento_en_comision = comision_original - comision_con_descuento
            
            # El descuento en PYG es: (descuento en comisión) × (cantidad de divisa que obtiene)
            cantidad_divisa_obtenida = resultado_final
            descuento_aplicado = descuento_en_comision * cantidad_divisa_obtenida
        
        # 6. Valores para mostrar
        subtotal = monto_a_pagar  # Lo que ingresó el cliente
        total_origen = monto_a_pagar  # El cliente paga exactamente lo que ingresó
        
        # Formatear montos
        def formatear_monto(valor, moneda):
            if moneda.codigo == 'PYG':
                return f"₲ {valor:,.0f}"
            else:
                return f"{moneda.simbolo} {valor:,.2f}"
        
        return {
            'success': True,
            'data': {
                # Datos originales
                'monto_original': monto,
                'moneda_origen': {
                    'id': moneda_origen.id, 
                    'codigo': moneda_origen.codigo,
                    'nombre': moneda_origen.nombre,
                    'simbolo': moneda_origen.simbolo
                },
                'moneda_destino': {
                    'id': moneda_destino.id,
                    'codigo': moneda_destino.codigo, 
                    'nombre': moneda_destino.nombre,
                    'simbolo': moneda_destino.simbolo
                },
                
                # Tasas y precio usado (con descuento aplicado)
                'precio_usado': float(precio_usado),
                'tipo_operacion': tipo_operacion,
                'tasa_origen': None if moneda_origen.codigo == 'PYG' else {
                    'moneda': moneda_origen.codigo,
                    'tipo': tipo_operacion,
                    'valor': float(precio_usado),
                },
                'tasa_destino': None if moneda_origen.codigo != 'PYG' else {
                    'moneda': moneda_destino.codigo,
                    'tipo': tipo_operacion, 
                    'valor': float(precio_usado),
                },
                
                # Tasas para mostrar en el preview
                'tasa_base': float(Decimal(str(tasa_destino.precio_base)) + Decimal(str(tasa_destino.comision_venta))),
                'tasa_ajustada': float(precio_usado),
                
                # Cálculos
                'subtotal': float(subtotal),
                'subtotal_formateado': formatear_monto(subtotal, moneda_origen),
                
                'comision_cobro': float(comision_cobro),
                'comision_cobro_formateado': formatear_monto(comision_cobro, moneda_origen),
                
                'comision_pago': float(comision_pago), 
                'comision_pago_formateado': formatear_monto(comision_pago, moneda_origen),
                
                'comision_total': float(comision_total),
                'comision_total_formateado': formatear_monto(comision_total, moneda_origen),
                
                'total': float(total_origen),
                'total_formateado': formatear_monto(total_origen, moneda_origen),
                
                'resultado': float(resultado_final),
                'resultado_formateado': formatear_monto(resultado_final, moneda_destino),
                
                # Información de descuentos
                'descuento_pct': float(descuento_pct),
                'descuento_aplicado': float(descuento_aplicado),
                'descuento_aplicado_formateado': formatear_monto(descuento_aplicado, moneda_origen),
                
                # Información de métodos
                'metodo_cobro': {
                    'id': metodo_cobro.id if metodo_cobro else None,
                    'nombre': metodo_cobro.nombre if metodo_cobro else None,
                    'comision': float(metodo_cobro.comision) if metodo_cobro else 0
                } if metodo_cobro else None,
                
                'metodo_pago': {
                    'id': metodo_pago.id if metodo_pago else None,
                    'nombre': metodo_pago.nombre if metodo_pago else None,
                    'comision': float(metodo_pago.comision) if metodo_pago else 0
                } if metodo_pago else None,
                
                # Información del cliente
                'cliente': {
                    'id': cliente.id,
                    'nombre': cliente.nombre_comercial,
                    'tipo': cliente.tipo_cliente.nombre,
                    'descuento': float(descuento_pct),
                } if cliente else None,
                
                # Detalle explicativo
                'detalle': (f"PYG -> {moneda_destino.codigo} usando precio de venta" + 
                           (f" con descuento {descuento_pct}% en comisión" if descuento_pct > 0 else "")) if moneda_origen.codigo == 'PYG' 
                           else (f"{moneda_origen.codigo} -> PYG usando precio de compra" + 
                                (f" con descuento {descuento_pct}% en comisión" if descuento_pct > 0 else ""))
            }
        }
        
    except Exception as e:
        return {'success': False, 'error': f'Error en el cálculo: {str(e)}'}


def calcular_venta_completa(monto, moneda_origen, moneda_destino, cliente=None, metodo_cobro=None, metodo_pago=None):
    """
    Calcula el resultado completo de una VENTA de divisas incluyendo:
    - Conversión de divisa extranjera → PYG usando tasas de compra con descuento del cliente
    - Comisiones de método de cobro (como recibimos la divisa)
    - Comisiones de método de pago (como entregamos PYG)
    - Descuentos de cliente aplicados a la tasa
    - Total final en PYG
    
    Args:
        monto: Cantidad de divisa extranjera que el cliente quiere vender
        moneda_origen: Divisa extranjera que se vende
        moneda_destino: PYG (siempre)
        cliente: Cliente que realiza la venta
        metodo_cobro: Cómo recibimos la divisa extranjera
        metodo_pago: Cómo entregamos los PYG al cliente
    
    Returns:
        dict: Diccionario con todos los datos de la venta o error
    """
    try:
        # Validaciones iniciales
        if monto <= 0:
            return {'success': False, 'error': 'El monto debe ser mayor a cero'}
        
        # LÓGICA ESPECÍFICA PARA VENTAS (divisa extranjera → PYG)
        if moneda_destino.codigo != 'PYG':
            return {'success': False, 'error': 'Las ventas solo se realizan hacia PYG como moneda destino'}
        
        if moneda_origen.codigo == 'PYG':
            return {'success': False, 'error': 'No se puede vender PYG por PYG'}
        
        # Obtener descuento del cliente
        descuento_pct = Decimal('0')
        if cliente and cliente.tipo_cliente and cliente.tipo_cliente.activo and cliente.tipo_cliente.descuento > 0:
            descuento_pct = Decimal(str(cliente.tipo_cliente.descuento))
        
        # Obtener tasa de la divisa que va a vender
        try:
            tasa_origen = TasaCambio.objects.get(moneda=moneda_origen, es_activa=True)
        except TasaCambio.DoesNotExist:
            return {'success': False, 'error': f'Tasa de cambio no disponible para {moneda_origen.codigo}'}
        
        # Para ventas: aplicar descuento a la comisión de compra
        comision_compra_ajustada = Decimal(str(tasa_origen.comision_compra))
        if descuento_pct > 0:
            # El descuento reduce la comisión de compra (cliente recibe más PYG)
            comision_compra_ajustada = comision_compra_ajustada * (Decimal('1') - (descuento_pct / Decimal('100')))
            tipo_operacion = 'compra (con descuento)'
        else:
            tipo_operacion = 'compra'
        
        # Calcular precio de compra ajustado: precio_base - comision_compra_ajustada
        precio_usado = Decimal(str(tasa_origen.precio_base)) - comision_compra_ajustada
        
        # LÓGICA DE CÁLCULO PARA VENTAS:
        # 1. El monto ingresado es cuánta divisa extranjera quiere VENDER
        monto_a_vender = monto
        
        # 2. Convertir a PYG usando precio de compra ajustado
        monto_pyg_bruto = monto_a_vender * precio_usado
        
        # 3. Calcular comisiones de métodos SOBRE el monto en PYG
        comision_cobro = Decimal('0')
        comision_pago = Decimal('0')
        
        if metodo_cobro and metodo_cobro.comision > 0:
            comision_cobro = monto_pyg_bruto * (Decimal(str(metodo_cobro.comision)) / Decimal('100'))
        
        if metodo_pago and metodo_pago.comision > 0:
            comision_pago = monto_pyg_bruto * (Decimal(str(metodo_pago.comision)) / Decimal('100'))
        
        comision_total = comision_cobro + comision_pago
        
        # 4. Resultado final: PYG bruto menos comisiones de métodos
        resultado_final = (monto_pyg_bruto - comision_total).quantize(
            Decimal('1.00'), 
            rounding=ROUND_HALF_UP
        )
        
        # 5. Calcular el monto real del descuento aplicado
        # El descuento es el PYG adicional que recibe el cliente sobre la comisión de cambio
        descuento_aplicado = Decimal('0')
        if descuento_pct > 0:
            # El descuento se aplica sobre la comisión de compra
            comision_original = Decimal(str(tasa_origen.comision_compra))
            comision_con_descuento = comision_compra_ajustada
            descuento_en_comision = comision_original - comision_con_descuento
            
            # El descuento en PYG es: (descuento en comisión) × (cantidad de divisa que vende)
            descuento_aplicado = descuento_en_comision * monto_a_vender
        
        # 6. Valores para mostrar
        subtotal = monto_pyg_bruto  # PYG bruto de la conversión
        total_origen = monto_a_vender  # Divisa extranjera que entrega el cliente
        
        # Formatear montos
        def formatear_monto(valor, moneda):
            if moneda.codigo == 'PYG':
                return f"₲ {valor:,.0f}"
            else:
                return f"{moneda.simbolo} {valor:,.2f}"
        
        return {
            'success': True,
            'data': {
                # Datos originales
                'monto_original': monto,
                'moneda_origen': {
                    'id': moneda_origen.id, 
                    'codigo': moneda_origen.codigo,
                    'nombre': moneda_origen.nombre,
                    'simbolo': moneda_origen.simbolo
                },
                'moneda_destino': {
                    'id': moneda_destino.id,
                    'codigo': moneda_destino.codigo, 
                    'nombre': moneda_destino.nombre,
                    'simbolo': moneda_destino.simbolo
                },
                
                # Tasas y precio usado (con descuento aplicado)
                'precio_usado': float(precio_usado),
                'tipo_operacion': tipo_operacion,
                'tasa_origen': {
                    'moneda': moneda_origen.codigo,
                    'tipo': tipo_operacion,
                    'valor': float(precio_usado),
                },
                'tasa_destino': None,  # Para ventas, la tasa relevante es la de origen
                
                # Tasas para mostrar en el preview
                'tasa_base': float(Decimal(str(tasa_origen.precio_base)) - Decimal(str(tasa_origen.comision_compra))),
                'tasa_ajustada': float(precio_usado),
                
                # Cálculos
                'subtotal': float(subtotal),
                'subtotal_formateado': formatear_monto(subtotal, moneda_destino),
                
                'comision_cobro': float(comision_cobro),
                'comision_cobro_formateado': formatear_monto(comision_cobro, moneda_destino),
                
                'comision_pago': float(comision_pago), 
                'comision_pago_formateado': formatear_monto(comision_pago, moneda_destino),
                
                'comision_total': float(comision_total),
                'comision_total_formateado': formatear_monto(comision_total, moneda_destino),
                
                'total': float(total_origen),
                'total_formateado': formatear_monto(total_origen, moneda_origen),
                
                'resultado': float(resultado_final),
                'resultado_formateado': formatear_monto(resultado_final, moneda_destino),
                
                # Información de descuentos
                'descuento_pct': float(descuento_pct),
                'descuento_aplicado': float(descuento_aplicado),
                'descuento_aplicado_formateado': formatear_monto(descuento_aplicado, moneda_destino),
                
                # Información de métodos
                'metodo_cobro': {
                    'id': metodo_cobro.id if metodo_cobro else None,
                    'nombre': metodo_cobro.nombre if metodo_cobro else None,
                    'comision': float(metodo_cobro.comision) if metodo_cobro else 0
                } if metodo_cobro else None,
                
                'metodo_pago': {
                    'id': metodo_pago.id if metodo_pago else None,
                    'nombre': metodo_pago.nombre if metodo_pago else None,
                    'comision': float(metodo_pago.comision) if metodo_pago else 0
                } if metodo_pago else None,
                
                # Información del cliente
                'cliente': {
                    'id': cliente.id,
                    'nombre': cliente.nombre_comercial,
                    'tipo': cliente.tipo_cliente.nombre,
                    'descuento': float(descuento_pct),
                } if cliente else None,
                
                # Detalle explicativo
                'detalle': f"{moneda_origen.codigo} -> PYG usando precio de compra" + 
                          (f" con descuento {descuento_pct}% en comisión" if descuento_pct > 0 else "")
            }
        }
        
    except Exception as e:
        return {'success': False, 'error': f'Error en el cálculo de venta: {str(e)}'}


@login_required
def vender_divisas(request):
    """
    Vista para mostrar el formulario de venta de divisas.
    El cliente vende una divisa extranjera y recibe PYG.
    """
    # Obtener parámetros de la URL (desde el simulador)
    moneda_origen_codigo = request.GET.get('moneda_origen')
    moneda_destino_codigo = request.GET.get('moneda_destino', 'PYG')
    cantidad_preseleccionada = request.GET.get('cantidad')
    cliente_preseleccionado = request.GET.get('cliente_id')
    
    # Obtener monedas activas (excluyendo PYG para origen)
    monedas_origen = Moneda.objects.filter(es_activa=True).exclude(codigo='PYG').order_by('nombre')
    
    # Obtener clientes asociados al usuario
    clientes = Cliente.objects.filter(
        usuarios_asociados=request.user,
        activo=True
    ).select_related('tipo_cliente').order_by('nombre_comercial')
    
    # Obtener métodos de cobro activos - inicialmente vacío, se llena por JavaScript según moneda seleccionada
    metodos_cobro = MetodoCobro.objects.filter(es_activo=True).order_by('nombre')
    
    # Obtener métodos de pago activos (cómo entregamos PYG)
    metodos_pago = MetodoPago.objects.filter(
        es_activo=True,
        monedas_permitidas__codigo='PYG'
    ).distinct().order_by('nombre')
    
    context = {
        'titulo': 'Vender Divisas',
        'monedas_origen': monedas_origen,
        'moneda_origen_preseleccionada': moneda_origen_codigo,
        'cantidad_preseleccionada': cantidad_preseleccionada,
        'cliente_preseleccionado': cliente_preseleccionado,
        'clientes': clientes,
        'metodos_cobro': metodos_cobro,
        'metodos_pago': metodos_pago,
    }
    
    return render(request, 'transacciones/vender_divisas.html', context)


@login_required
def api_calcular_compra_completa(request):
    """
    API endpoint para calcular compra completa con comisiones desde JavaScript
    """
    if request.method == 'GET':
        try:
            # Obtener parámetros
            monto = Decimal(request.GET.get('monto', '0'))
            moneda_origen_codigo = request.GET.get('origen')
            moneda_destino_codigo = request.GET.get('destino')
            cliente_id = request.GET.get('cliente_id')
            metodo_cobro_id = request.GET.get('metodo_cobro_id')
            metodo_pago_id = request.GET.get('metodo_pago_id')
            
            # Validaciones básicas
            if monto <= 0 or not moneda_origen_codigo or not moneda_destino_codigo:
                return JsonResponse({
                    'success': False,
                    'error': 'Parámetros inválidos'
                })
            
            # Obtener objetos
            try:
                moneda_origen = Moneda.objects.get(codigo=moneda_origen_codigo, es_activa=True)
                moneda_destino = Moneda.objects.get(codigo=moneda_destino_codigo, es_activa=True)
            except Moneda.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': 'Monedas no válidas'
                })
            
            # Cliente opcional
            cliente = None
            if cliente_id:
                try:
                    cliente = Cliente.objects.get(id=cliente_id, activo=True)
                    # Verificar permisos
                    if not cliente.usuarios_asociados.filter(id=request.user.id).exists():
                        return JsonResponse({
                            'success': False,
                            'error': 'Sin permisos para este cliente'
                        })
                except Cliente.DoesNotExist:
                    return JsonResponse({
                        'success': False,
                        'error': 'Cliente no válido'
                    })
            
            # Métodos opcionales
            metodo_cobro = None
            if metodo_cobro_id:
                try:
                    metodo_cobro = MetodoCobro.objects.get(id=metodo_cobro_id, es_activo=True)
                except MetodoCobro.DoesNotExist:
                    return JsonResponse({
                        'success': False,
                        'error': 'Método de cobro no válido'
                    })
            
            metodo_pago = None
            if metodo_pago_id:
                try:
                    metodo_pago = MetodoPago.objects.get(id=metodo_pago_id, es_activo=True)
                except MetodoPago.DoesNotExist:
                    return JsonResponse({
                        'success': False,
                        'error': 'Método de pago no válido'
                    })
            
            # Realizar el cálculo completo
            resultado = calcular_transaccion_completa(
                monto=monto,
                moneda_origen=moneda_origen,
                moneda_destino=moneda_destino,
                cliente=cliente,
                metodo_cobro=metodo_cobro,
                metodo_pago=metodo_pago
            )
            
            return JsonResponse(resultado)
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Error interno: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'})


@login_required
def api_calcular_venta_completa(request):
    """
    API endpoint para calcular venta completa con comisiones desde JavaScript
    """
    if request.method == 'GET':
        try:
            # Obtener parámetros
            monto = Decimal(request.GET.get('monto', '0'))
            moneda_origen_codigo = request.GET.get('origen')
            moneda_destino_codigo = request.GET.get('destino')
            cliente_id = request.GET.get('cliente_id')
            metodo_cobro_id = request.GET.get('metodo_cobro_id')
            metodo_pago_id = request.GET.get('metodo_pago_id')
            
            # Validaciones básicas
            if monto <= 0 or not moneda_origen_codigo or not moneda_destino_codigo:
                return JsonResponse({
                    'success': False,
                    'error': 'Parámetros inválidos'
                })
            
            # Obtener objetos
            try:
                moneda_origen = Moneda.objects.get(codigo=moneda_origen_codigo, es_activa=True)
                moneda_destino = Moneda.objects.get(codigo=moneda_destino_codigo, es_activa=True)
            except Moneda.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': 'Monedas no válidas'
                })
            
            # Cliente opcional
            cliente = None
            if cliente_id:
                try:
                    cliente = Cliente.objects.get(id=cliente_id, activo=True)
                    # Verificar permisos
                    if not cliente.usuarios_asociados.filter(id=request.user.id).exists():
                        return JsonResponse({
                            'success': False,
                            'error': 'Sin permisos para este cliente'
                        })
                except Cliente.DoesNotExist:
                    return JsonResponse({
                        'success': False,
                        'error': 'Cliente no válido'
                    })
            
            # Métodos opcionales
            metodo_cobro = None
            if metodo_cobro_id:
                try:
                    metodo_cobro = MetodoCobro.objects.get(id=metodo_cobro_id, es_activo=True)
                except MetodoCobro.DoesNotExist:
                    return JsonResponse({
                        'success': False,
                        'error': 'Método de cobro no válido'
                    })
            
            metodo_pago = None
            if metodo_pago_id:
                try:
                    metodo_pago = MetodoPago.objects.get(id=metodo_pago_id, es_activo=True)
                except MetodoPago.DoesNotExist:
                    return JsonResponse({
                        'success': False,
                        'error': 'Método de pago no válido'
                    })
            
            # Realizar el cálculo completo de VENTA
            resultado = calcular_venta_completa(
                monto=monto,
                moneda_origen=moneda_origen,
                moneda_destino=moneda_destino,
                cliente=cliente,
                metodo_cobro=metodo_cobro,
                metodo_pago=metodo_pago
            )
            
            return JsonResponse(resultado)
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Error interno: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'})


@login_required
def api_metodos_cobro_por_moneda(request):
    """
    API endpoint para obtener métodos de cobro disponibles para una moneda específica
    """
    if request.method == 'GET':
        try:
            moneda_codigo = request.GET.get('moneda_codigo')
            
            if not moneda_codigo:
                return JsonResponse({
                    'success': False,
                    'error': 'Código de moneda requerido'
                })
            
            # Verificar que la moneda existe y está activa
            try:
                moneda = Moneda.objects.get(codigo=moneda_codigo, es_activa=True)
            except Moneda.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': 'Moneda no válida'
                })
            
            # Obtener métodos de cobro que permiten esta moneda
            metodos_cobro = MetodoCobro.objects.filter(
                es_activo=True,
                monedas_permitidas=moneda
            ).order_by('nombre')
            
            # Convertir a lista de diccionarios
            metodos_data = []
            for metodo in metodos_cobro:
                metodos_data.append({
                    'id': metodo.id,
                    'nombre': metodo.nombre,
                    'comision': float(metodo.comision),
                    'descripcion': metodo.descripcion or ''
                })
            
            return JsonResponse({
                'success': True,
                'metodos_cobro': metodos_data
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': f'Error interno: {str(e)}'
            })
    
    return JsonResponse({'success': False, 'error': 'Método no permitido'})


@login_required
@require_http_methods(["POST"])
def iniciar_venta(request):
    """
    Vista para procesar el formulario de venta de divisas y crear la transacción.
    El usuario ingresa la cantidad de divisa extranjera que quiere vender
    y recibe Guaraníes a cambio.
    """
    try:
        # Obtener datos del formulario
        monto = Decimal(request.POST.get('monto', '0'))
        moneda_origen_codigo = request.POST.get('moneda_origen', 'USD')  # Por defecto USD
        moneda_destino_codigo = request.POST.get('moneda_destino', 'PYG')  # Siempre PYG para ventas
        cliente_id = request.POST.get('cliente_id')
        metodo_cobro_id = request.POST.get('metodo_cobro_id')
        metodo_pago_id = request.POST.get('metodo_pago_id')
        
        # Validaciones básicas
        if monto <= 0:
            messages.error(request, 'El monto debe ser mayor a cero.')
            return redirect('transacciones:vender_divisas')
        
        # Validar monedas
        try:
            moneda_origen = Moneda.objects.get(codigo=moneda_origen_codigo, es_activa=True)
            moneda_destino = Moneda.objects.get(codigo=moneda_destino_codigo, es_activa=True)
        except Moneda.DoesNotExist:
            messages.error(request, 'Moneda seleccionada no válida o inactiva.')
            return redirect('transacciones:vender_divisas')
        
        # Validar que destino sea PYG
        if moneda_destino.codigo != 'PYG':
            messages.error(request, 'Las ventas solo se realizan hacia Guaraníes (PYG).')
            return redirect('transacciones:vender_divisas')
        
        # Cliente (requerido para ventas)
        cliente = None
        if cliente_id:
            try:
                cliente = Cliente.objects.get(id=cliente_id, activo=True)
                # Verificar permisos
                if not cliente.usuarios_asociados.filter(id=request.user.id).exists():
                    messages.error(request, 'No tiene permisos para realizar transacciones con este cliente.')
                    return redirect('transacciones:vender_divisas')
            except Cliente.DoesNotExist:
                messages.error(request, 'Cliente seleccionado no válido.')
                return redirect('transacciones:vender_divisas')
        
        # Métodos opcionales
        metodo_cobro = None
        if metodo_cobro_id:
            try:
                metodo_cobro = MetodoCobro.objects.get(id=metodo_cobro_id, es_activo=True)
            except MetodoCobro.DoesNotExist:
                messages.error(request, 'Método de cobro seleccionado no válido.')
                return redirect('transacciones:vender_divisas')
        
        metodo_pago = None
        if metodo_pago_id:
            try:
                metodo_pago = MetodoPago.objects.get(id=metodo_pago_id, es_activo=True)
            except MetodoPago.DoesNotExist:
                messages.error(request, 'Método de pago seleccionado no válido.')
                return redirect('transacciones:vender_divisas')
        
        # Calcular la transacción
        resultado_calculo = calcular_venta_completa(
            monto=monto,
            moneda_origen=moneda_origen,
            moneda_destino=moneda_destino,
            cliente=cliente,
            metodo_cobro=metodo_cobro,
            metodo_pago=metodo_pago
        )
        
        if not resultado_calculo['success']:
            messages.error(request, f'Error en el cálculo: {resultado_calculo["error"]}')
            return redirect('transacciones:vender_divisas')
        
        monto_pyg_equivalente = Decimal(str(resultado_calculo['data']['subtotal']))
        
        # Validar límites de transacción
        # Para ventas: validar el monto que el cliente va a recibir contra el límite de la moneda que se vende
        monto_a_recibir = Decimal(str(resultado_calculo['data']['resultado']))
        validacion_limites = validar_limites_transaccion(
            monto_origen=monto_a_recibir,
            moneda_origen=moneda_origen,  # Moneda que se vende (AUD) para validar su límite
            cliente=cliente,
            usuario=request.user
        )
        
        if not validacion_limites['valido']:
            messages.error(request, f'Límites excedidos: {validacion_limites["mensaje"]}')
            return redirect('transacciones:vender_divisas')
        
        # Crear la transacción
        with transaction.atomic():
            tipo_venta = TipoOperacion.objects.get(codigo=TipoOperacion.VENTA)
            estado_pendiente = EstadoTransaccion.objects.get(codigo=EstadoTransaccion.PENDIENTE)
            
            # Usar los datos de la función de cálculo de venta
            data = resultado_calculo['data']
            
            # Calcular porcentajes de comisión correctos
            porcentaje_comision_total = Decimal('0')
            if monto_pyg_equivalente > 0:
                porcentaje_comision_total = (Decimal(str(data.get('comision_total', 0))) / monto_pyg_equivalente * Decimal('100')).quantize(Decimal('0.0001'))
            
            nueva_transaccion = Transaccion(
                cliente=cliente,
                usuario=request.user,
                tipo_operacion=tipo_venta,
                moneda_origen=moneda_origen,
                moneda_destino=moneda_destino,
                monto_origen=monto,  # Divisa extranjera que el cliente vende
                monto_destino=Decimal(str(data['resultado'])),  # PYG que recibirá
                metodo_cobro=metodo_cobro,  # Cómo recibimos la divisa extranjera
                metodo_pago=metodo_pago,    # Cómo entregamos PYG
                tasa_cambio=Decimal(str(data['precio_usado'])),  # Tasa ajustada con descuento
                porcentaje_comision=porcentaje_comision_total,  # Porcentaje calculado correctamente
                monto_comision=Decimal(str(data.get('comision_total', 0))),  # Monto total de comisión
                porcentaje_descuento=Decimal(str(data.get('descuento_pct', 0))),  # Porcentaje de descuento del cliente
                monto_descuento=Decimal(str(data.get('descuento_aplicado', 0))),  # Monto de descuento aplicado
                estado=estado_pendiente,
                ip_cliente=get_client_ip(request)
            )
            nueva_transaccion.save()
        
        messages.success(request, f'Transacción de venta creada exitosamente: {nueva_transaccion.id_transaccion}')
        return redirect('transacciones:resumen_transaccion', transaccion_id=nueva_transaccion.id_transaccion)
        
    except Exception as e:
        print(f"EXCEPCIÓN EN INICIAR_VENTA: {str(e)}")
        import traceback
        print(f"TRACEBACK: {traceback.format_exc()}")
        messages.error(request, f'Error al crear la transacción de venta: {str(e)}')
        return redirect('tasa_cambio:dashboard')


class MisTransaccionesListView(LoginRequiredMixin, ListView):
    """
    Vista para mostrar las transacciones del usuario con filtros y estadísticas
    """
    model = Transaccion
    template_name = 'transacciones/mis_transacciones.html'
    context_object_name = 'transacciones'
    paginate_by = 20

    def get_queryset(self):
        """
        Filtrar transacciones del usuario actual con filtros opcionales
        """
        queryset = Transaccion.objects.filter(
            usuario=self.request.user
        ).select_related(
            'cliente',
            'tipo_operacion',
            'estado',
            'moneda_origen',
            'moneda_destino'
        ).order_by('-fecha_creacion')

        # Aplicar filtros
        fecha_desde = self.request.GET.get('fecha_desde')
        fecha_hasta = self.request.GET.get('fecha_hasta')
        tipo = self.request.GET.get('tipo')
        estado = self.request.GET.get('estado')
        cliente = self.request.GET.get('cliente')

        if fecha_desde:
            try:
                fecha_desde_obj = datetime.strptime(fecha_desde, '%Y-%m-%d').date()
                queryset = queryset.filter(fecha_creacion__date__gte=fecha_desde_obj)
            except ValueError:
                pass

        if fecha_hasta:
            try:
                fecha_hasta_obj = datetime.strptime(fecha_hasta, '%Y-%m-%d').date()
                queryset = queryset.filter(fecha_creacion__date__lte=fecha_hasta_obj)
            except ValueError:
                pass

        if tipo:
            queryset = queryset.filter(tipo_operacion__pk=tipo)

        if estado:
            queryset = queryset.filter(estado__pk=estado)

        if cliente:
            queryset = queryset.filter(cliente__pk=cliente)

        return queryset

    def get_context_data(self, **kwargs):
        """
        Agregar datos adicionales para filtros y estadísticas
        """
        context = super().get_context_data(**kwargs)

        # Datos para filtros
        context['tipos_operacion'] = TipoOperacion.objects.filter(activo=True)
        context['estados_transaccion'] = EstadoTransaccion.objects.filter(activo=True)

        # Clientes asociados al usuario
        context['clientes'] = Cliente.objects.filter(
            usuarios_asociados=self.request.user,
            activo=True
        ).order_by('nombre_comercial')

        # Preservar filtros en el contexto
        context['filtros'] = {
            'fecha_desde': self.request.GET.get('fecha_desde', ''),
            'fecha_hasta': self.request.GET.get('fecha_hasta', ''),
            'tipo': self.request.GET.get('tipo', ''),
            'estado': self.request.GET.get('estado', ''),
            'cliente': self.request.GET.get('cliente', ''),
        }

        # Estadísticas
        todas_transacciones = self.get_queryset()

        context['estadisticas'] = {
            'total_transacciones': todas_transacciones.count(),
            'pendientes': todas_transacciones.filter(estado__codigo='PENDIENTE').count(),
            'pagadas': todas_transacciones.filter(estado__codigo='PAGADA').count(),
            'canceladas': todas_transacciones.filter(estado__codigo='CANCELADA').count(),
            'anuladas': todas_transacciones.filter(estado__codigo='ANULADA').count(),
        }

        # Estadísticas por tipo de operación
        context['estadisticas_tipo'] = {
            'compras': todas_transacciones.filter(tipo_operacion__codigo='COMPRA').count(),
            'ventas': todas_transacciones.filter(tipo_operacion__codigo='VENTA').count(),
        }

        # Datos para gráficos - usar las mismas transacciones filtradas
        # pero agrupar por fecha para mostrar tendencia
        transacciones_para_grafico = todas_transacciones.order_by('fecha_creacion')

        # Si no hay filtros de fecha, usar últimos 30 días
        if not self.request.GET.get('fecha_desde') and not self.request.GET.get('fecha_hasta'):
            desde_30_dias = timezone.now().date() - timedelta(days=30)
            transacciones_para_grafico = transacciones_para_grafico.filter(
                fecha_creacion__date__gte=desde_30_dias
            )
            fecha_inicio = desde_30_dias
            fecha_fin = timezone.now().date()
        else:
            # Usar el rango de fechas de los filtros o de los datos disponibles
            if transacciones_para_grafico.exists():
                fecha_inicio = transacciones_para_grafico.first().fecha_creacion.date()
                fecha_fin = transacciones_para_grafico.last().fecha_creacion.date()

                # Asegurar un rango mínimo de 7 días para el gráfico
                if (fecha_fin - fecha_inicio).days < 7:
                    fecha_inicio = fecha_fin - timedelta(days=7)
            else:
                # Si no hay datos, mostrar últimos 7 días
                fecha_fin = timezone.now().date()
                fecha_inicio = fecha_fin - timedelta(days=7)

        # Crear diccionario de fechas con valores 0
        fechas_datos = {}
        fecha_actual = fecha_inicio
        while fecha_actual <= fecha_fin:
            fechas_datos[fecha_actual.isoformat()] = 0
            fecha_actual += timedelta(days=1)

        # Contar transacciones por fecha
        for transaccion in transacciones_para_grafico:
            fecha_str = transaccion.fecha_creacion.date().isoformat()
            if fecha_str in fechas_datos:
                fechas_datos[fecha_str] += 1

        # Preparar datos para el gráfico
        fechas_ordenadas = sorted(fechas_datos.keys())
        context['datos_grafico'] = json.dumps({
            'fechas': fechas_ordenadas,
            'cantidades': [fechas_datos[fecha] for fecha in fechas_ordenadas]
        })

        return context


# ============================================================================
# FUNCIONES DE PAGOS MOVIDAS A LA APP 'pagos'
# ============================================================================
# Las funciones de procesamiento de pagos ahora están en pagos/views.py
# - _procesar_pago_con_pasarela()
# - pago_billetera_electronica()
# - pago_tarjeta_debito() 
# - pago_transferencia_bancaria()
# - webhook_pago()
#
# Esta app solo maneja la lógica de transacciones.
# ============================================================================