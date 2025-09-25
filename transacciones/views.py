from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse, Http404
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.db import transaction
from decimal import Decimal
import json

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
        limites_aplicados.append(f'Cliente: máx. {cliente.monto_limite_transaccion} {moneda_origen.codigo}')
    
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
    
    if usuario:
        # Transacciones del día
        transacciones_hoy = Transaccion.objects.filter(
            usuario=usuario,
            fecha_creacion__date=hoy,
            estado__nombre__in=['COMPLETADA', 'PENDIENTE']  # Solo transacciones válidas
        ).aggregate(total=Sum('monto_origen'))['total'] or Decimal('0')
        
        # Transacciones del mes
        transacciones_mes = Transaccion.objects.filter(
            usuario=usuario,
            fecha_creacion__date__gte=inicio_mes,
            estado__nombre__in=['COMPLETADA', 'PENDIENTE']
        ).aggregate(total=Sum('monto_origen'))['total'] or Decimal('0')
        
        # Validar límite diario
        if config.limite_diario_transacciones > 0:
            total_dia_con_nueva = transacciones_hoy + monto_origen
            if total_dia_con_nueva > config.limite_diario_transacciones:
                errores.append(f'Excede el límite diario: {config.limite_diario_transacciones} (ya usado: {transacciones_hoy})')
            limites_aplicados.append(f'Límite diario: {config.limite_diario_transacciones} (usado: {transacciones_hoy})')
        
        # Validar límite mensual
        if config.limite_mensual_transacciones > 0:
            total_mes_con_nueva = transacciones_mes + monto_origen
            if total_mes_con_nueva > config.limite_mensual_transacciones:
                errores.append(f'Excede el límite mensual: {config.limite_mensual_transacciones} (ya usado: {transacciones_mes})')
            limites_aplicados.append(f'Límite mensual: {config.limite_mensual_transacciones} (usado: {transacciones_mes})')
    
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
        # Debug: imprimir datos recibidos
        print("=== DEBUG INICIAR COMPRA ===")
        print("POST data:", dict(request.POST))
        
        # Obtener datos del formulario
        monto = Decimal(request.POST.get('monto', '0'))
        moneda_origen_codigo = request.POST.get('moneda_origen')
        moneda_destino_codigo = request.POST.get('moneda_destino')
        cliente_id = request.POST.get('cliente_id')
        
        # Verificar si viene metodo_cobro_id (nueva pantalla) o metodo_pago_id (dashboard antiguo)
        metodo_cobro_id = request.POST.get('metodo_cobro_id')
        metodo_pago_id = request.POST.get('metodo_pago_id')
        
        print(f"Datos parseados: monto={monto}, origen={moneda_origen_codigo}, destino={moneda_destino_codigo}, cliente={cliente_id}, metodo_cobro={metodo_cobro_id}, metodo_pago={metodo_pago_id}")
        
        # Validaciones básicas
        if monto <= 0:
            messages.error(request, 'El monto debe ser mayor a cero.')
            print("ERROR: Monto <= 0")
            return redirect('tasa_cambio:dashboard')
        
        # Obtener objetos del modelo
        try:
            moneda_origen = Moneda.objects.get(codigo=moneda_origen_codigo, es_activa=True)
            moneda_destino = Moneda.objects.get(codigo=moneda_destino_codigo, es_activa=True)
            print(f"Monedas encontradas: {moneda_origen} -> {moneda_destino}")
        except Moneda.DoesNotExist:
            messages.error(request, 'Las monedas seleccionadas no son válidas.')
            print("ERROR: Monedas no válidas")
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
            # Nueva pantalla de compras - usa métodos de cobro
            # REQUERIR cliente para compras
            if not cliente_id:
                messages.error(request, 'Las compras de divisas requieren seleccionar un cliente.')
                return redirect('transacciones:comprar_divisas')
            
            try:
                metodo_cobro = MetodoCobro.objects.get(id=metodo_cobro_id, es_activo=True)
            except MetodoCobro.DoesNotExist:
                messages.error(request, 'El método de cobro seleccionado no es válido.')
                return redirect('transacciones:comprar_divisas')
        elif metodo_pago_id:
            # Dashboard antiguo - usa métodos de pago (mantener compatibilidad)
            try:
                metodo_pago = MetodoPago.objects.get(id=metodo_pago_id, es_activo=True)
            except MetodoPago.DoesNotExist:
                messages.error(request, 'El método de pago seleccionado no es válido.')
                return redirect('tasa_cambio:dashboard')
        
        # Validar límites de transacción
        print("Validando límites...")
        validacion_limites = validar_limites_transaccion(
            monto_origen=monto,
            moneda_origen=moneda_origen,
            cliente=cliente,
            usuario=request.user
        )
        
        if not validacion_limites['valido']:
            messages.error(request, f'Transacción rechazada: {validacion_limites["mensaje"]}')
            print(f"ERROR: Límites excedidos: {validacion_limites['mensaje']}")
            # Redirigir según desde donde vino
            if metodo_cobro_id:
                return redirect('transacciones:comprar_divisas')
            else:
                return redirect('tasa_cambio:dashboard')
        
        print(f"Límites validados exitosamente: {validacion_limites['limites_aplicados']}")
        
        # Calcular la transacción usando la misma lógica del simulador
        print("Calculando transacción...")
        # Para el cálculo, usar metodo_pago (la API existente espera metodo_pago)
        metodo_para_calculo = metodo_pago if metodo_pago else metodo_cobro
        resultado = calcular_transaccion(
            monto=monto,
            moneda_origen=moneda_origen,
            moneda_destino=moneda_destino,
            cliente=cliente,
            metodo_pago=metodo_para_calculo  # La función existente espera metodo_pago
        )
        
        print(f"Resultado del cálculo: {resultado}")
        
        if not resultado['success']:
            messages.error(request, resultado['message'])
            print(f"ERROR en cálculo: {resultado['message']}")
            return redirect('tasa_cambio:dashboard')
        
        # Crear la transacción
        print("Creando transacción...")
        with transaction.atomic():
            tipo_compra = TipoOperacion.objects.get(codigo=TipoOperacion.COMPRA)
            estado_pendiente = EstadoTransaccion.objects.get(codigo=EstadoTransaccion.PENDIENTE)
            
            nueva_transaccion = Transaccion(
                cliente=cliente,
                usuario=request.user,
                tipo_operacion=tipo_compra,
                moneda_origen=moneda_origen,
                moneda_destino=moneda_destino,
                monto_origen=monto,
                monto_destino=resultado['data']['monto_destino'],
                metodo_cobro=metodo_cobro,  # Para compras, usamos método de cobro
                metodo_pago=metodo_pago,    # Para compatibilidad con dashboard antiguo
                tasa_cambio=resultado['data']['tasa_utilizada'],
                porcentaje_comision=resultado['data']['porcentaje_comision'],
                monto_comision=resultado['data']['monto_comision'],
                porcentaje_descuento=resultado['data']['porcentaje_descuento'],
                monto_descuento=resultado['data']['monto_descuento'],
                estado=estado_pendiente,
                ip_cliente=get_client_ip(request)
            )
            nueva_transaccion.save()
        
        print(f"Transacción creada: {nueva_transaccion.id_transaccion}")
        messages.success(request, f'Transacción creada exitosamente: {nueva_transaccion.id_transaccion}')
        return redirect('transacciones:resumen_transaccion', transaccion_id=nueva_transaccion.id_transaccion)
        
    except Exception as e:
        print(f"EXCEPCIÓN: {str(e)}")
        import traceback
        traceback.print_exc()
        messages.error(request, f'Error al crear la transacción: {str(e)}')
        return redirect('tasa_cambio:dashboard')


@login_required
def resumen_transaccion(request, transaccion_id):
    """
    Muestra el resumen detallado de una transacción antes del pago.
    """
    transaccion = get_object_or_404(
        Transaccion.objects.select_related(
            'cliente', 'usuario', 'tipo_operacion', 'estado',
            'moneda_origen', 'moneda_destino', 'metodo_pago'
        ),
        id_transaccion=transaccion_id
    )
    
    # Verificar que el usuario puede ver esta transacción
    if transaccion.usuario != request.user:
        # Si hay cliente, verificar que el usuario esté asociado
        if transaccion.cliente and not transaccion.cliente.usuarios_asociados.filter(id=request.user.id).exists():
            raise Http404("Transacción no encontrada")
    
    context = {
        'transaccion': transaccion,
        'resumen_financiero': transaccion.get_resumen_financiero(),
        'puede_pagar': transaccion.estado.codigo == EstadoTransaccion.PENDIENTE and not transaccion.esta_expirada(),
        'tiempo_restante': (transaccion.fecha_expiracion - timezone.now()).total_seconds() if not transaccion.esta_expirada() else 0,
    }
    
    return render(request, 'transacciones/resumen_transaccion.html', context)


@login_required
@require_http_methods(["POST"])
def procesar_pago(request, transaccion_id):
    """
    Procesa el 'pago' de una transacción (simulado por ahora).
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
    
    # Procesar el 'pago' (por ahora solo cambiar estado)
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
    
    # Métodos de cobro activos (para COMPRAS)
    metodos_cobro = MetodoCobro.objects.filter(es_activo=True).order_by('nombre')
    
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
