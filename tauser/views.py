from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.views.generic import ListView, CreateView, UpdateView, DetailView
from django.urls import reverse_lazy
from django.db.models import Q, Sum
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from django.db import transaction
from django.core.paginator import Paginator
import logging


from .models import Tauser, Stock, HistorialStock, StockDenominacion, HistorialStockDenominacion
from .forms import TauserForm, StockForm
from transacciones.services import registrar_deposito_en_simulador, DepositoSimuladorError


logger = logging.getLogger(__name__)


class TauserListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """Lista de Tausers"""
    model = Tauser
    template_name = 'tauser/tauser_list.html'
    context_object_name = 'tausers'
    permission_required = 'tauser.view_tauser'
    paginate_by = 20

    def get_queryset(self):
        queryset = Tauser.objects.all()

        q = self.request.GET.get('q')
        if q:
            queryset = queryset.filter(
                Q(nombre__icontains=q) | 
                Q(direccion__icontains=q) | 
                Q(horario_atencion__icontains=q)
            )

        estado = self.request.GET.get('estado')
        if estado == 'activo':
            queryset = queryset.filter(es_activo=True)
        elif estado == 'inactivo':
            queryset = queryset.filter(es_activo=False)

        return queryset.order_by('nombre')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Tausers'
        context['q'] = self.request.GET.get('q', '')
        context['estado'] = self.request.GET.get('estado', '')
        return context


class TauserCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """Crear Tauser"""
    model = Tauser
    form_class = TauserForm
    template_name = 'tauser/tauser_form.html'
    success_url = reverse_lazy('tauser:tauser_list')
    permission_required = 'tauser.add_tauser'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Crear Tauser'
        context['accion'] = 'Crear'
        return context

    def form_valid(self, form):
        messages.success(self.request, f"Tauser '{form.instance.nombre}' creado correctamente.")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Error al crear el Tauser. Verifique los datos.")
        return super().form_invalid(form)


class TauserDetailView(LoginRequiredMixin, PermissionRequiredMixin, DetailView):
    """Detalle del Tauser con su stock"""
    model = Tauser
    template_name = 'tauser/tauser_detail.html'
    permission_required = 'tauser.view_tauser'
    context_object_name = 'tauser'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = f'Tauser: {self.object.nombre}'
        context['stocks'] = self.object.stocks.select_related('moneda').all()
        context['can_view_stock'] = self.request.user.has_perm('tauser.view_stock')
        context['can_create_stock'] = self.request.user.has_perm('tauser.add_stock')
        
        # Obtener solo las monedas que tienen stock con cantidad > 0
        from monedas.models import Moneda
        stocks_con_cantidad = context['stocks'].filter(cantidad__gt=0).select_related('moneda')
        
        # Crear lista solo de monedas que tienen stock
        monedas_con_stock = []
        for stock in stocks_con_cantidad:
            monedas_con_stock.append({
                'moneda': stock.moneda,
                'stock': stock,
                'tiene_stock': True,
                'cantidad': stock.cantidad,
                'es_activo': stock.es_activo,
                'esta_bajo_stock': stock.esta_bajo_stock(),
            })
        
        # Para el modal de cargar stock, necesitamos todas las monedas activas
        monedas_activas = Moneda.objects.filter(es_activa=True).order_by('nombre')
        stocks_dict = {stock.moneda_id: stock for stock in context['stocks']}
        
        # Crear lista de todas las monedas para el modal
        todas_las_monedas = []
        for moneda in monedas_activas:
            stock = stocks_dict.get(moneda.id)
            todas_las_monedas.append({
                'moneda': moneda,
                'stock': stock,
                'tiene_stock': stock is not None,
                'cantidad': stock.cantidad if stock else 0,
                'es_activo': stock.es_activo if stock else False,
                'esta_bajo_stock': stock.esta_bajo_stock() if stock else False,
            })
        
        context['monedas_con_stock'] = monedas_con_stock
        context['todas_las_monedas'] = todas_las_monedas
        return context


class TauserUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """Editar Tauser"""
    model = Tauser
    form_class = TauserForm
    template_name = 'tauser/tauser_form.html'
    success_url = reverse_lazy('tauser:tauser_list')
    permission_required = 'tauser.change_tauser'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = f'Editar Tauser: {self.object.nombre}'
        context['accion'] = 'Actualizar'
        return context

    def form_valid(self, form):
        messages.success(self.request, f"Tauser '{form.instance.nombre}' actualizado correctamente.")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Error al actualizar el Tauser. Verifique los datos.")
        return super().form_invalid(form)


@login_required
@permission_required('tauser.change_tauser', raise_exception=True)
@require_http_methods(["POST"])
def toggle_tauser_status(request, pk):
    """Cambiar estado activo/inactivo (AJAX)"""
    tauser = get_object_or_404(Tauser, pk=pk)
    tauser.es_activo = not tauser.es_activo
    tauser.save()
    return JsonResponse({
        'success': True,
        'nueva_estado': tauser.es_activo,
        'message': f"Tauser {'activado' if tauser.es_activo else 'desactivado'} correctamente."
    })


# Solo mantenemos la funcionalidad de cargar stock desde tauser




@login_required
@permission_required('tauser.add_stock', raise_exception=True)
def cargar_stock(request, pk):
    """Cargar/agregar stock a un tauser por denominaciones"""
    tauser = get_object_or_404(Tauser, pk=pk)
    
    if request.method == 'POST':
        try:
            moneda_id = request.POST.get('moneda')
            
            if not moneda_id:
                messages.error(request, 'Moneda es requerida.')
                return redirect('tauser:tauser_detail', pk=tauser.pk)
            
            from monedas.models import Moneda, DenominacionMoneda
            moneda = get_object_or_404(Moneda, pk=moneda_id)
            
            # Obtener solo denominaciones de billetes (no monedas pequeñas)
            denominaciones = DenominacionMoneda.objects.filter(
                moneda=moneda, 
                es_activa=True,
                tipo='BILLETE'  # Solo billetes
            ).order_by('-valor')
            
            if not denominaciones.exists():
                messages.error(request, f'No hay denominaciones de billetes configuradas para {moneda.nombre}.')
                return redirect('tauser:tauser_detail', pk=tauser.pk)
            
            # Procesar cantidades por denominación
            denominaciones_con_cantidad = []
            total_valor = 0
            
            for denominacion in denominaciones:
                cantidad_key = f'cantidad_{denominacion.pk}'
                
                cantidad = int(request.POST.get(cantidad_key, 0) or 0)
                
                if cantidad > 0:
                    valor_total = cantidad * denominacion.valor
                    denominaciones_con_cantidad.append({
                        'denominacion': denominacion,
                        'cantidad': cantidad,
                        'valor_total': valor_total
                    })
                    total_valor += valor_total
            
            if not denominaciones_con_cantidad:
                messages.error(request, 'Debe especificar al menos una cantidad para alguna denominación.')
                return redirect('tauser:tauser_detail', pk=tauser.pk)
            
            # Buscar si ya existe stock para esta moneda
            stock_existente = Stock.objects.filter(tauser=tauser, moneda=moneda).first()
            
            if stock_existente:
                # Actualizar stock existente
                cantidad_anterior = stock_existente.cantidad
                stock_existente.cantidad = stock_existente.cantidad + total_valor
                stock_existente.save()
                
                # Registrar en historial general
                HistorialStock.objects.create(
                    stock=stock_existente,
                    tipo_movimiento='ENTRADA',
                    origen_movimiento='MANUAL',
                    cantidad_movida=total_valor,
                    cantidad_anterior=cantidad_anterior,
                    cantidad_posterior=stock_existente.cantidad,
                    usuario=request.user,
                    observaciones=f'Carga manual por denominaciones - Total: {moneda.simbolo}{total_valor:.{moneda.decimales}f}'
                )
                
                # Procesar cada denominación
                for item in denominaciones_con_cantidad:
                    denominacion = item['denominacion']
                    cantidad = item['cantidad']
                    
                    # Buscar o crear stock por denominación
                    stock_denominacion, created = StockDenominacion.objects.get_or_create(
                        stock=stock_existente,
                        denominacion=denominacion,
                        defaults={
                            'cantidad': cantidad,
                            'es_activo': True
                        }
                    )
                    
                    if not created:
                        # Actualizar stock existente por denominación
                        cantidad_anterior_denom = stock_denominacion.cantidad
                        stock_denominacion.cantidad += cantidad
                        stock_denominacion.save()
                        
                        # Registrar en historial por denominación
                        HistorialStockDenominacion.objects.create(
                            stock_denominacion=stock_denominacion,
                            tipo_movimiento='ENTRADA',
                            origen_movimiento='MANUAL',
                            cantidad_movida=cantidad,
                            cantidad_anterior=cantidad_anterior_denom,
                            cantidad_posterior=stock_denominacion.cantidad,
                            usuario=request.user,
                            observaciones='Carga manual por denominación'
                        )
                    else:
                        # Registrar creación inicial
                        HistorialStockDenominacion.objects.create(
                            stock_denominacion=stock_denominacion,
                            tipo_movimiento='ENTRADA',
                            origen_movimiento='MANUAL',
                            cantidad_movida=cantidad,
                            cantidad_anterior=0,
                            cantidad_posterior=cantidad,
                            usuario=request.user,
                            observaciones='Creación inicial por denominación'
                        )
                
                messages.success(request, 
                    f'Stock actualizado para {moneda.nombre}. Nuevo total: {moneda.simbolo}{stock_existente.cantidad:.{moneda.decimales}f}')
            else:
                # Crear nuevo stock
                nuevo_stock = Stock.objects.create(
                    tauser=tauser,
                    moneda=moneda,
                    cantidad=total_valor,
                    es_activo=True
                )
                
                # Registrar en historial general
                HistorialStock.objects.create(
                    stock=nuevo_stock,
                    tipo_movimiento='ENTRADA',
                    origen_movimiento='MANUAL',
                    cantidad_movida=total_valor,
                    cantidad_anterior=0,
                    cantidad_posterior=total_valor,
                    usuario=request.user,
                    observaciones=f'Creación inicial por denominaciones - Total: {moneda.simbolo}{total_valor:.{moneda.decimales}f}'
                )
                
                # Crear stock por denominación
                for item in denominaciones_con_cantidad:
                    denominacion = item['denominacion']
                    cantidad = item['cantidad']
                    
                    stock_denominacion = StockDenominacion.objects.create(
                        stock=nuevo_stock,
                        denominacion=denominacion,
                        cantidad=cantidad,
                        es_activo=True
                    )
                    
                    # Registrar en historial por denominación
                    HistorialStockDenominacion.objects.create(
                        stock_denominacion=stock_denominacion,
                        tipo_movimiento='ENTRADA',
                        origen_movimiento='MANUAL',
                        cantidad_movida=cantidad,
                        cantidad_anterior=0,
                        cantidad_posterior=cantidad,
                        usuario=request.user,
                        observaciones='Creación inicial por denominación'
                    )
                
                messages.success(request, 
                    f'Stock creado para {moneda.nombre} con {moneda.simbolo}{total_valor:.{moneda.decimales}f}')
            
            # Refrescar el objeto tauser para obtener los datos actualizados
            tauser.refresh_from_db()
            return redirect('tauser:tauser_detail', pk=tauser.pk)
            
        except (ValueError, TypeError) as e:
            messages.error(request, 'Error en los datos proporcionados.')
            return redirect('tauser:tauser_detail', pk=tauser.pk)
        except Exception as e:
            messages.error(request, f'Error al cargar el stock: {str(e)}')
            return redirect('tauser:tauser_detail', pk=tauser.pk)
    
    return redirect('tauser:tauser_detail', pk=tauser.pk)


@login_required
def obtener_denominaciones(request, moneda_id):
    """Vista AJAX para obtener denominaciones de billetes de una moneda por ID o código"""
    try:
        from monedas.models import DenominacionMoneda, Moneda
        
        # Intentar obtener la moneda por ID primero, luego por código
        try:
            if moneda_id.isdigit():
                moneda = Moneda.objects.get(id=int(moneda_id))
            else:
                moneda = Moneda.objects.get(codigo=moneda_id)
        except Moneda.DoesNotExist:
            return JsonResponse({
                'error': 'Moneda no encontrada'
            }, status=404)
        
        denominaciones = DenominacionMoneda.objects.filter(
            moneda=moneda,
            es_activa=True,
            tipo='BILLETE'  # Solo billetes
        ).order_by('-valor')
        
        # Obtener stock disponible por denominación si se proporciona tauser_id
        stock_por_denominacion = {}
        tauser_id = request.GET.get('tauser_id')
        if tauser_id:
            try:
                from .models import Stock, StockDenominacion
                tauser = Tauser.objects.get(pk=tauser_id)
                stock = Stock.objects.filter(tauser=tauser, moneda=moneda).first()
                if stock:
                    stock_denominaciones = StockDenominacion.objects.filter(
                        stock=stock,
                        es_activo=True
                    ).select_related('denominacion')
                    for sd in stock_denominaciones:
                        stock_por_denominacion[sd.denominacion.pk] = sd.cantidad
            except (Tauser.DoesNotExist, ValueError):
                pass
        
        denominaciones_data = []
        for denominacion in denominaciones:
            stock_disponible = stock_por_denominacion.get(denominacion.pk, 0)
            denominaciones_data.append({
                'id': denominacion.pk,
                'valor': float(denominacion.valor),
                'tipo': denominacion.tipo,
                'mostrar_denominacion': denominacion.mostrar_denominacion(),
                'es_activa': denominacion.es_activa,
                'stock_disponible': stock_disponible
            })
        
        return JsonResponse({
            'denominaciones': denominaciones_data
        })
    except Exception as e:
        return JsonResponse({
            'error': str(e)
        }, status=500)


@login_required
def simulador_cajero(request):
    """
    Vista para el simulador de cajero automático.
    Permite a los clientes retirar efectivo usando el ID de transacción.
    """
    # Obtener todos los tausers activos para mostrar en el selector
    tausers_activos = Tauser.objects.filter(es_activo=True).order_by('nombre')
    
    # Obtener tauser preseleccionado si viene en la URL
    tauser_preseleccionado = request.GET.get('tauser_id')
    tauser_seleccionado = None
    if tauser_preseleccionado:
        try:
            tauser_seleccionado = Tauser.objects.get(id=tauser_preseleccionado, es_activo=True)
        except Tauser.DoesNotExist:
            tauser_seleccionado = None
    
    context = {
        'titulo': 'Simulador de Cajero Automático',
        'tausers': tausers_activos,
        'tauser_preseleccionado': tauser_preseleccionado,
        'tauser_seleccionado': tauser_seleccionado,
    }
    
    return render(request, 'tauser/simulador_cajero.html', context)


@login_required
@require_http_methods(["POST"])
def validar_transaccion_retiro(request):
    """
    API endpoint para validar una transacción antes del retiro.
    Verifica que la transacción existe, está pagada y puede ser retirada.
    Maneja tanto compras como ventas con cobro en efectivo.
    """
    try:
        codigo_verificacion = request.POST.get('codigo_verificacion')
        tauser_id = request.POST.get('tauser_id')
        
        if not codigo_verificacion or not tauser_id:
            return JsonResponse({
                'success': False,
                'error': 'Código de verificación y Tauser son requeridos'
            })
        
        # Obtener la transacción
        try:
            from transacciones.models import Transaccion, EstadoTransaccion
            transaccion = Transaccion.objects.select_related(
                'cliente', 'tipo_operacion', 'estado', 'moneda_destino', 'metodo_cobro'
            ).get(codigo_verificacion=codigo_verificacion)
        except Transaccion.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Transacción no encontrada'
            })
        
        # Verificar el tipo de operación
        es_compra = transaccion.tipo_operacion.codigo == 'COMPRA'
        es_venta = transaccion.tipo_operacion.codigo == 'VENTA'
        es_venta_con_efectivo = (
            es_venta and 
            transaccion.metodo_cobro and 
            transaccion.metodo_cobro.nombre.lower().find('efectivo') != -1
        )
        es_venta_otro_metodo = es_venta and not es_venta_con_efectivo
        
        # Verificar si la transacción requiere retiro físico en Tauser
        requiere_retiro_fisico = False
        if es_venta:
            # Para ventas, verificar si el método de cobro requiere retiro físico
            if transaccion.metodo_cobro and transaccion.metodo_cobro.requiere_retiro_fisico:
                requiere_retiro_fisico = True
        elif es_compra:
            # Para compras, siempre requiere retiro físico (cliente retira divisas)
            requiere_retiro_fisico = True
        
        if not requiere_retiro_fisico:
            return JsonResponse({
                'success': False,
                'error': 'Esta transacción no requiere retiro físico en Tauser. El pago se procesó por transferencia.'
            })
        
        # Validar estados según el tipo de transacción
        estado_actual = transaccion.estado.codigo
        
        if es_compra:
            # COMPRA: Debe estar PAGADA (cliente ya pagó, ahora debe retirar divisas)
            if estado_actual == EstadoTransaccion.ENTREGADA:
                return JsonResponse({
                    'success': False,
                    'error': 'Esta transacción ya fue entregada al cliente.'
                })
            elif estado_actual != EstadoTransaccion.PAGADA:
                return JsonResponse({
                    'success': False,
                    'error': f'La transacción debe estar pagada para retirar. Estado actual: {transaccion.estado.nombre}'
                })
        elif es_venta_con_efectivo:
            # VENTA con efectivo: Debe estar PENDIENTE (cliente va a entregar divisas)
            if estado_actual != EstadoTransaccion.PENDIENTE:
                return JsonResponse({
                    'success': False,
                    'error': f'Esta venta con cobro en efectivo debe estar en estado pendiente. Estado actual: {transaccion.estado.nombre}'
                })
        elif es_venta_otro_metodo:
            # VENTA con otro método (transferencia, tarjeta): No debe permitir
            # Estas transacciones no requieren retiro físico y ya están completas
            return JsonResponse({
                'success': False,
                'error': 'Las ventas con métodos de cobro distintos a efectivo no se procesan en Tauser. El pago ya fue procesado por otro medio.'
            })
        
        # Obtener el tauser
        try:
            tauser = Tauser.objects.get(id=tauser_id, es_activo=True)
        except Tauser.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Tauser no válido o inactivo'
            })
        
        # Verificar que el tauser tenga stock de la moneda destino (excepto PYG)
        if transaccion.moneda_destino.codigo != 'PYG':
            try:
                stock = Stock.objects.get(
                    tauser=tauser,
                    moneda=transaccion.moneda_destino,
                    es_activo=True
                )
            except Stock.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': f'No hay stock de {transaccion.moneda_destino.nombre} en {tauser.nombre}'
                })
            
            # Verificar que hay suficiente stock
            if stock.cantidad < transaccion.monto_destino:
                return JsonResponse({
                    'success': False,
                    'error': f'Stock insuficiente. Disponible: {stock.mostrar_cantidad()}, Requerido: {transaccion.moneda_destino.mostrar_monto(transaccion.monto_destino)}'
                })
        else:
            # Para PYG, no validar stock ya que no se maneja en efectivo
            stock = None
        
        # Crear código de verificación para retiro
        from .models import CodigoVerificacionRetiro
        from .services import EmailServiceRetiro
        
        # Limpiar códigos expirados
        CodigoVerificacionRetiro.limpiar_codigos_expirados()
        
        # Crear nuevo código de verificación
        codigo_verificacion = CodigoVerificacionRetiro.crear_codigo(
            transaccion=transaccion,
            request=request,
            minutos_expiracion=5
        )
        
        # Enviar email con código de verificación
        exito, mensaje = EmailServiceRetiro.enviar_codigo_verificacion_retiro(
            transaccion, codigo_verificacion, request, tauser=tauser
        )
        
        if not exito:
            return JsonResponse({
                'success': False,
                'error': f'Error al enviar código de verificación: {mensaje}'
            })
        
        # Preparar datos de la transacción para mostrar
        resumen_detallado = transaccion.get_resumen_detallado()
        
        # Preparar datos adicionales para todas las transacciones
        datos_adicionales = {
            'metodo_cobro': transaccion.metodo_cobro.nombre if transaccion.metodo_cobro else None,
            'metodo_pago': transaccion.metodo_pago.nombre if transaccion.metodo_pago else None,
        }
        
        return JsonResponse({
            'success': True,
            'message': 'Código de verificación enviado por correo',
            'es_compra': es_compra,
            'es_venta': es_venta,
            'es_venta_con_efectivo': es_venta_con_efectivo,
            'transaccion': {
                'id': transaccion.id_transaccion,
                'codigo_verificacion': transaccion.codigo_verificacion,
                'tipo': transaccion.tipo_operacion.nombre,
                'cliente': transaccion.cliente.nombre_comercial if transaccion.cliente else 'Casual',
                'moneda_destino': {
                    'codigo': transaccion.moneda_destino.codigo,
                    'nombre': transaccion.moneda_destino.nombre,
                    'simbolo': transaccion.moneda_destino.simbolo
                },
                'monto_a_retirar': float(transaccion.monto_destino),
                'monto_a_retirar_formateado': resumen_detallado['monto_recibe_formateado'],
                'fecha_creacion': transaccion.fecha_creacion.strftime('%d/%m/%Y %H:%M'),
                'fecha_pago': transaccion.fecha_pago.strftime('%d/%m/%Y %H:%M') if transaccion.fecha_pago else None,
                **datos_adicionales
            },
            'tauser': {
                'id': tauser.id,
                'nombre': tauser.nombre,
                'direccion': tauser.direccion,
            },
            'stock_disponible': {
                'cantidad': float(stock.cantidad) if stock else 0,
                'cantidad_formateada': stock.mostrar_cantidad() if stock else 'N/A',
                'esta_bajo_stock': stock.esta_bajo_stock() if stock else False
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error interno: {str(e)}'
        })


@login_required
@require_http_methods(["POST"])
def procesar_retiro(request):
    """
    Procesa el retiro de efectivo de una transacción.
    Actualiza el stock del tauser y marca la transacción como retirada.
    """
    try:
        codigo_verificacion = request.POST.get('codigo_verificacion')
        tauser_id = request.POST.get('tauser_id')
        
        if not codigo_verificacion or not tauser_id:
            return JsonResponse({
                'success': False,
                'error': 'Código de verificación y Tauser son requeridos'
            })
        
        # Obtener la transacción (forzar recarga desde BD para obtener estado actualizado)
        try:
            from transacciones.models import Transaccion, EstadoTransaccion
            transaccion = Transaccion.objects.select_related(
                'cliente', 'tipo_operacion', 'estado', 'moneda_destino', 'metodo_cobro'
            ).get(codigo_verificacion=codigo_verificacion)
            # Forzar refresco del estado desde la base de datos
            transaccion.refresh_from_db()
        except Transaccion.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Transacción no encontrada'
            })
        # Verificar el tipo de operación
        es_compra = transaccion.tipo_operacion.codigo == 'COMPRA'
        es_venta = transaccion.tipo_operacion.codigo == 'VENTA'
        es_venta_con_efectivo = (
            es_venta and 
            transaccion.metodo_cobro and 
            transaccion.metodo_cobro.nombre.lower().find('efectivo') != -1
        )
        es_venta_otro_metodo = es_venta and not es_venta_con_efectivo
        
        # Verificar si la transacción requiere retiro físico en Tauser
        requiere_retiro_fisico = False
        if es_venta:
            # Para ventas, verificar si el método de cobro requiere retiro físico
            if transaccion.metodo_cobro and transaccion.metodo_cobro.requiere_retiro_fisico:
                requiere_retiro_fisico = True
        elif es_compra:
            # Para compras, siempre requiere retiro físico (cliente retira divisas)
            requiere_retiro_fisico = True
        
        if not requiere_retiro_fisico:
            return JsonResponse({
                'success': False,
                'error': 'Esta transacción no requiere retiro físico en Tauser. El pago se procesó por transferencia.'
            })
        
        # Validar estados según el tipo de transacción
        estado_actual = transaccion.estado.codigo
        
        if es_compra:
            # COMPRA: Debe estar PAGADA para retirar (cambiará a ENTREGADA)
            if estado_actual == EstadoTransaccion.ENTREGADA:
                return JsonResponse({
                    'success': False,
                    'error': 'Esta transacción ya fue entregada al cliente.'
                })
            elif estado_actual != EstadoTransaccion.PAGADA:
                return JsonResponse({
                    'success': False,
                    'error': f'La transacción debe estar pagada para retirar. Estado actual: {transaccion.estado.nombre}'
                })
        elif es_venta_con_efectivo:
            # VENTA con efectivo: 
            # 1. Cliente deposita/entrega sus divisas en Tauser (PENDIENTE → PAGADA) - esto se hace en confirmar_recepcion_divisas
            # 2. Cliente retira sus guaraníes (PAGADA → RETIRADO) - este es el flujo actual
            if estado_actual == EstadoTransaccion.RETIRADO:
                return JsonResponse({
                    'success': False,
                    'error': 'El cliente ya retiró sus guaraníes de esta transacción.'
                })
            elif estado_actual == EstadoTransaccion.PENDIENTE:
                return JsonResponse({
                    'success': False,
                    'error': f'El cliente primero debe entregar sus divisas en el Tauser. Estado actual: {transaccion.estado.nombre}'
                })
            elif estado_actual != EstadoTransaccion.PAGADA:
                return JsonResponse({
                    'success': False,
                    'error': f'Esta venta con cobro en efectivo debe estar pagada (divisas ya entregadas) para retirar guaraníes. Estado actual: {transaccion.estado.nombre}'
                })
        elif es_venta_otro_metodo:
            # VENTA con otro método: No debe permitir
            return JsonResponse({
                'success': False,
                'error': 'Las ventas con métodos de cobro distintos a efectivo no se procesan en Tauser. El pago ya fue procesado por otro medio.'
            })
        
        # Obtener el tauser
        try:
            tauser = Tauser.objects.get(id=tauser_id, es_activo=True)
        except Tauser.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Tauser no válido o inactivo'
            })
        
        # Procesar el retiro con transacción atómica
        with transaction.atomic():
            # Solo procesar stock si no es PYG
            if transaccion.moneda_destino.codigo != 'PYG':
                # Verificar stock nuevamente (por si cambió entre validación y procesamiento)
                try:
                    stock = Stock.objects.select_for_update().get(
                        tauser=tauser,
                        moneda=transaccion.moneda_destino,
                        es_activo=True
                    )
                except Stock.DoesNotExist:
                    return JsonResponse({
                        'success': False,
                        'error': f'No hay stock de {transaccion.moneda_destino.nombre} en {tauser.nombre}'
                    })
                
                # Verificar stock suficiente
                if stock.cantidad < transaccion.monto_destino:
                    return JsonResponse({
                        'success': False,
                        'error': f'Stock insuficiente. Disponible: {stock.mostrar_cantidad()}, Requerido: {transaccion.moneda_destino.mostrar_monto(transaccion.monto_destino)}'
                    })
                
                # Reducir el stock por denominaciones si existen, de lo contrario reducir el stock general
                from monedas.models import DenominacionMoneda
                from .models import StockDenominacion
                from decimal import Decimal
                
                # Obtener denominaciones activas de la moneda ordenadas de mayor a menor
                denominaciones = DenominacionMoneda.objects.filter(
                    moneda=transaccion.moneda_destino,
                    es_activa=True,
                    tipo='BILLETE'
                ).order_by('-valor')
                
                # Obtener stock por denominación
                stock_denominaciones_dict = {}
                if denominaciones.exists():
                    stock_denominaciones = StockDenominacion.objects.filter(
                        stock=stock,
                        es_activo=True
                    ).select_related('denominacion')
                    for sd in stock_denominaciones:
                        stock_denominaciones_dict[sd.denominacion.pk] = sd
                
                # Si hay stock por denominación, actualizar por denominaciones
                if stock_denominaciones_dict:
                    monto_restante = Decimal(str(transaccion.monto_destino))
                    denominaciones_retiradas = []
                    
                    # Algoritmo greedy: empezar con las denominaciones más grandes
                    for denominacion in denominaciones:
                        if monto_restante <= 0:
                            break
                        
                        sd = stock_denominaciones_dict.get(denominacion.pk)
                        if not sd or sd.cantidad == 0:
                            continue
                        
                        # Calcular cuántos billetes de esta denominación necesitamos
                        valor_denominacion = Decimal(str(denominacion.valor))
                        cantidad_necesaria = int(monto_restante / valor_denominacion)
                        
                        # No podemos retirar más de lo que tenemos
                        cantidad_a_retirar = min(cantidad_necesaria, sd.cantidad)
                        
                        if cantidad_a_retirar > 0:
                            # Reducir el stock de esta denominación
                            # Nota: reducir_cantidad de StockDenominacion actualiza automáticamente el stock general
                            if not sd.reducir_cantidad(
                                cantidad_a_retirar,
                                usuario=request.user,
                                transaccion=transaccion,
                                observaciones=f'Retiro por transacción {transaccion.id_transaccion}'
                            ):
                                return JsonResponse({
                                    'success': False,
                                    'error': f'No se pudo reducir el stock de {denominacion.mostrar_denominacion()}'
                                })
                            
                            valor_retirado = cantidad_a_retirar * valor_denominacion
                            monto_restante -= valor_retirado
                            denominaciones_retiradas.append({
                                'denominacion': denominacion.mostrar_denominacion(),
                                'cantidad': cantidad_a_retirar,
                                'valor': float(valor_retirado)
                            })
                    
                    # Si quedó monto sin cubrir, hay un problema
                    if monto_restante > Decimal('0.01'):  # Tolerancia para errores de redondeo
                        return JsonResponse({
                            'success': False,
                            'error': f'No se pudo completar el retiro. Faltan {transaccion.moneda_destino.mostrar_monto(monto_restante)}. Posiblemente no hay denominaciones adecuadas disponibles.'
                        })
                else:
                    # Si no hay stock por denominación, reducir el stock general directamente
                    if not stock.reducir_cantidad(
                        transaccion.monto_destino,
                        usuario=request.user,
                        transaccion=transaccion,
                        observaciones=f'Retiro por transacción {transaccion.id_transaccion}'
                    ):
                        return JsonResponse({
                            'success': False,
                            'error': 'No se pudo reducir el stock'
                        })
            else:
                # Para PYG, no hay stock físico que reducir
                stock = None
            
            # Actualizar la transacción con el tauser y agregar observación
            transaccion.tauser = tauser
            
            # Determinar tipo de transacción y actualizar estado según corresponda
            es_compra = transaccion.tipo_operacion.codigo == 'COMPRA'
            es_venta_con_efectivo = (
                transaccion.tipo_operacion.codigo == 'VENTA' and 
                transaccion.metodo_cobro and 
                transaccion.metodo_cobro.nombre.lower().find('efectivo') != -1
            )
            
            if es_compra:
                # COMPRA: Cliente retira divisas -> Estado ENTREGADA
                estado_entregada, _ = EstadoTransaccion.objects.get_or_create(
                    codigo=EstadoTransaccion.ENTREGADA,
                    defaults={
                        'nombre': 'Entregada',
                        'descripcion': 'Las divisas han sido entregadas al cliente en una transacción de compra',
                        'es_final': True,
                        'activo': True
                    }
                )
                transaccion.estado = estado_entregada
                if transaccion.observaciones:
                    transaccion.observaciones += f"\nDivisas entregadas al cliente en {tauser.nombre} el {timezone.now()} por {request.user.email}"
                else:
                    transaccion.observaciones = f"Divisas entregadas al cliente en {tauser.nombre} el {timezone.now()} por {request.user.email}"
            elif es_venta_con_efectivo:
                # VENTA con efectivo: Cliente retira guaraníes después de haber entregado divisas -> Estado RETIRADO
                # Nota: La entrega de divisas ya marcó la transacción como PAGADA en confirmar_recepcion_divisas
                estado_retirado, _ = EstadoTransaccion.objects.get_or_create(
                    codigo=EstadoTransaccion.RETIRADO,
                    defaults={
                        'nombre': 'Retirado',
                        'descripcion': 'El cliente ha retirado sus guaraníes en una transacción de venta',
                        'es_final': True,
                        'activo': True
                    }
                )
                transaccion.estado = estado_retirado
                if transaccion.observaciones:
                    transaccion.observaciones += f"\nGuaraníes retirados por el cliente en {tauser.nombre} el {timezone.now()} por {request.user.email}"
                else:
                    transaccion.observaciones = f"Guaraníes retirados por el cliente en {tauser.nombre} el {timezone.now()} por {request.user.email}"
            else:
                # Otros casos (no deberían llegar aquí por las validaciones previas)
                transaccion.observaciones += f"\nRetirado en {tauser.nombre} el {timezone.now()} por {request.user.email}"
            
            transaccion.save()
        
        # Preparar respuesta exitosa
        resumen_detallado = transaccion.get_resumen_detallado()
        
        return JsonResponse({
            'success': True,
            'message': 'Retiro procesado exitosamente',
            'transaccion': {
                'id': transaccion.id_transaccion,
                'tipo': transaccion.tipo_operacion.nombre,
                'cliente': transaccion.cliente.nombre_comercial if transaccion.cliente else 'Casual',
                'monto_retirado': float(transaccion.monto_destino),
                'monto_retirado_formateado': resumen_detallado['monto_recibe_formateado'],
                'moneda': transaccion.moneda_destino.nombre,
                'tauser': tauser.nombre,
                'fecha_retiro': timezone.now().strftime('%d/%m/%Y %H:%M'),
            },
            'stock_actualizado': {
                'cantidad_restante': float(stock.cantidad) if stock else 0,
                'cantidad_restante_formateada': stock.mostrar_cantidad() if stock else 'N/A',
                'esta_bajo_stock': stock.esta_bajo_stock() if stock else False
            }
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': f'Error interno: {str(e)}'
        })


@login_required
@permission_required('tauser.view_historial_stock', raise_exception=True)
def historial_stock(request, pk):
    """Vista para mostrar el historial de movimientos de stock de un tauser"""
    tauser = get_object_or_404(Tauser, pk=pk)
    
    # Obtener todos los movimientos de stock del tauser
    historial = HistorialStock.objects.filter(
        stock__tauser=tauser
    ).select_related(
        'stock__moneda', 'usuario', 'transaccion'
    ).order_by('-fecha_movimiento')
    
    # Filtros opcionales
    tipo_movimiento = request.GET.get('tipo_movimiento')
    origen_movimiento = request.GET.get('origen_movimiento')
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    
    if tipo_movimiento:
        historial = historial.filter(tipo_movimiento=tipo_movimiento)
    if origen_movimiento:
        historial = historial.filter(origen_movimiento=origen_movimiento)
    if fecha_desde:
        historial = historial.filter(fecha_movimiento__date__gte=fecha_desde)
    if fecha_hasta:
        historial = historial.filter(fecha_movimiento__date__lte=fecha_hasta)
    
    # Calcular totales (número de movimientos, no suma de cantidades)
    total_entradas = historial.filter(tipo_movimiento='ENTRADA').count()
    total_salidas = historial.filter(tipo_movimiento='SALIDA').count()
    total_manuales = historial.filter(origen_movimiento='MANUAL').count()
    total_transacciones = historial.filter(origen_movimiento='TRANSACCION').count()
    
    # Paginación
    paginator = Paginator(historial, 50)  # 50 registros por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'titulo': f'Historial de Stock - {tauser.nombre}',
        'tauser': tauser,
        'page_obj': page_obj,
        'total_entradas': total_entradas,
        'total_salidas': total_salidas,
        'total_manuales': total_manuales,
        'total_transacciones': total_transacciones,
        'tipo_movimiento_choices': HistorialStock.TIPO_MOVIMIENTO_CHOICES,
        'origen_movimiento_choices': HistorialStock.ORIGEN_MOVIMIENTO_CHOICES,
        'filtros': {
            'tipo_movimiento': tipo_movimiento,
            'origen_movimiento': origen_movimiento,
            'fecha_desde': fecha_desde,
            'fecha_hasta': fecha_hasta,
        }
    }
    
    return render(request, 'tauser/historial_stock.html', context)


@login_required
@require_http_methods(["POST"])
def verificar_codigo_retiro(request):
    """
    Verifica el código de verificación enviado por email antes de proceder con el retiro.
    """
    print("=== INICIO verificar_codigo_retiro ===")
    print(f"Request POST data: {request.POST}")
    
    try:
        codigo_verificacion = request.POST.get('codigo_verificacion')
        tauser_id = request.POST.get('tauser_id')
        codigo_email = request.POST.get('codigo_email')
        
        print(f"Código verificación: {codigo_verificacion}")
        print(f"Tauser ID: {tauser_id}")
        print(f"Código email: {codigo_email}")
        
        if not codigo_verificacion or not tauser_id:
            print("ERROR: Faltan parámetros requeridos")
            return JsonResponse({
                'success': False,
                'error': 'Código de verificación y Tauser son requeridos'
            })
        
        # Obtener la transacción por código de verificación (forzar recarga desde BD)
        try:
            from transacciones.models import Transaccion, EstadoTransaccion
            transaccion = Transaccion.objects.select_related(
                'cliente', 'tipo_operacion', 'estado', 'moneda_destino', 'metodo_cobro'
            ).get(codigo_verificacion=codigo_verificacion)
            # Forzar refresco del estado desde la base de datos para asegurar datos actualizados
            transaccion.refresh_from_db()
            print(f"Transacción encontrada: {transaccion.id_transaccion}")
            print(f"Tipo operación: {transaccion.tipo_operacion.nombre}")
            print(f"Estado: {transaccion.estado.nombre}")
            print(f"Método cobro: {transaccion.metodo_cobro.nombre if transaccion.metodo_cobro else 'None'}")
        except Transaccion.DoesNotExist:
            print("ERROR: Transacción no encontrada")
            return JsonResponse({
                'success': False,
                'error': 'Transacción no encontrada'
            })
        
        # Verificar el tipo de operación
        es_compra = transaccion.tipo_operacion.codigo == 'COMPRA'
        es_venta = transaccion.tipo_operacion.codigo == 'VENTA'
        es_venta_con_efectivo = (
            es_venta and 
            transaccion.metodo_cobro and 
            transaccion.metodo_cobro.nombre.lower().find('efectivo') != -1
        )
        es_venta_otro_metodo = es_venta and not es_venta_con_efectivo
        
        # Validar estados según el tipo de transacción
        estado_actual = transaccion.estado.codigo
        
        if es_compra:
            # COMPRA: Debe estar PAGADA (cliente ya pagó, ahora debe retirar divisas)
            if estado_actual == EstadoTransaccion.ENTREGADA:
                return JsonResponse({
                    'success': False,
                    'error': 'Esta transacción ya fue entregada al cliente.'
                })
            elif estado_actual != EstadoTransaccion.PAGADA:
                return JsonResponse({
                    'success': False,
                    'error': f'La transacción debe estar pagada para retirar. Estado actual: {transaccion.estado.nombre}'
                })
        elif es_venta_con_efectivo:
            # VENTA con efectivo: Debe estar PENDIENTE (cliente va a entregar divisas)
            if estado_actual != EstadoTransaccion.PENDIENTE:
                return JsonResponse({
                    'success': False,
                    'error': f'Esta venta con cobro en efectivo debe estar en estado pendiente. Estado actual: {transaccion.estado.nombre}'
                })
        elif es_venta_otro_metodo:
            # VENTA con otro método (transferencia, tarjeta): No debe permitir
            return JsonResponse({
                'success': False,
                'error': 'Las ventas con métodos de cobro distintos a efectivo no se procesan en Tauser. El pago ya fue procesado por otro medio.'
            })
        
        # Verificar el código de verificación de retiro
        from .models import CodigoVerificacionRetiro
        try:
            codigo_obj = CodigoVerificacionRetiro.objects.get(
                transaccion=transaccion,
                codigo=request.POST.get('codigo_email'),
                tipo='retiro',
                usado=False
            )
            print(f"Código de verificación encontrado: {codigo_obj.codigo}")
        except CodigoVerificacionRetiro.DoesNotExist:
            print("ERROR: Código de verificación no encontrado o ya usado")
            return JsonResponse({
                'success': False,
                'error': 'Código de verificación incorrecto o ya utilizado'
            })
        
        # Verificar que el código no haya expirado
        if not codigo_obj.es_valido():
            return JsonResponse({
                'success': False,
                'error': 'El código de verificación ha expirado. Solicita un nuevo código.'
            })
        
        # Marcar el código como usado
        codigo_obj.usado = True
        codigo_obj.save()
        
        # Obtener el tauser
        try:
            tauser = Tauser.objects.get(id=tauser_id, es_activo=True)
        except Tauser.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Tauser no válido o inactivo'
            })
        
        # Verificar que el tauser tenga stock de la moneda destino (excepto PYG)
        if transaccion.moneda_destino.codigo != 'PYG':
            try:
                stock = Stock.objects.get(
                    tauser=tauser,
                    moneda=transaccion.moneda_destino,
                    es_activo=True
                )
            except Stock.DoesNotExist:
                return JsonResponse({
                    'success': False,
                    'error': f'No hay stock de {transaccion.moneda_destino.nombre} en {tauser.nombre}'
                })
            
            # Verificar que hay suficiente stock
            if stock.cantidad < transaccion.monto_destino:
                return JsonResponse({
                    'success': False,
                    'error': f'Stock insuficiente. Disponible: {stock.mostrar_cantidad()}, Requerido: {transaccion.moneda_destino.mostrar_monto(transaccion.monto_destino)}'
                })
        else:
            # Para PYG, no validar stock ya que no se maneja en efectivo
            stock = None
        
        # Preparar datos de la transacción para mostrar
        resumen_detallado = transaccion.get_resumen_detallado()
        
        # Preparar datos adicionales para todas las transacciones
        datos_adicionales = {
            'metodo_cobro': transaccion.metodo_cobro.nombre if transaccion.metodo_cobro else None,
            'metodo_pago': transaccion.metodo_pago.nombre if transaccion.metodo_pago else None,
        }
        
        if es_venta_con_efectivo:
            datos_adicionales.update({
                'moneda_origen': {
                    'codigo': transaccion.moneda_origen.codigo,
                    'nombre': transaccion.moneda_origen.nombre,
                    'simbolo': transaccion.moneda_origen.simbolo
                } if transaccion.moneda_origen else None,
                'monto_a_entregar': float(transaccion.monto_origen),
                'monto_a_entregar_formateado': f"{transaccion.moneda_origen.simbolo}{transaccion.monto_origen:.{transaccion.moneda_origen.decimales}f}" if transaccion.moneda_origen else None,
                'monto_a_recibir': float(transaccion.monto_destino),
                'monto_a_recibir_formateado': f"{transaccion.moneda_destino.simbolo}{transaccion.monto_destino:.{transaccion.moneda_destino.decimales}f}" if transaccion.moneda_destino else None,
            })
        
        print("=== FIN verificar_codigo_retiro - ÉXITO ===")
        print(f"Datos adicionales: {datos_adicionales}")
        
        # Mensaje según el tipo de transacción
        if es_compra:
            mensaje = 'Código de verificación válido. Puede proceder con el retiro de sus divisas.'
        elif es_venta_con_efectivo:
            mensaje = 'Código de verificación válido. Por favor, entregue las divisas indicadas.'
        else:
            mensaje = 'Código de verificación válido.'
        
        return JsonResponse({
            'success': True,
            'message': mensaje,
            'es_compra': es_compra,
            'es_venta': es_venta,
            'es_venta_con_efectivo': es_venta_con_efectivo,
            'transaccion': {
                'id': transaccion.id_transaccion,
                'codigo_verificacion': transaccion.codigo_verificacion,
                'tipo': transaccion.tipo_operacion.nombre,
                'cliente': transaccion.cliente.nombre_comercial if transaccion.cliente else 'Casual',
                'moneda_destino': {
                    'codigo': transaccion.moneda_destino.codigo,
                    'nombre': transaccion.moneda_destino.nombre,
                    'simbolo': transaccion.moneda_destino.simbolo
                },
                'monto_a_retirar': float(transaccion.monto_destino),
                'monto_a_retirar_formateado': f"{transaccion.moneda_destino.simbolo}{transaccion.monto_destino:.{transaccion.moneda_destino.decimales}f}",
                'fecha_creacion': transaccion.fecha_creacion.strftime('%d/%m/%Y %H:%M'),
                'fecha_pago': transaccion.fecha_pago.strftime('%d/%m/%Y %H:%M') if transaccion.fecha_pago else None,
                **datos_adicionales
            },
            'tauser': {
                'id': tauser.id,
                'nombre': tauser.nombre,
                'direccion': tauser.direccion,
            },
            'stock_disponible': {
                'cantidad': float(stock.cantidad) if stock else 0,
                'cantidad_formateada': stock.mostrar_cantidad() if stock else 'N/A',
                'esta_bajo_stock': stock.esta_bajo_stock() if stock else False
            }
        })
        
    except Exception as e:
        print(f"=== ERROR en verificar_codigo_retiro: {str(e)} ===")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return JsonResponse({
            'success': False,
            'error': f'Error interno: {str(e)}'
        })


@login_required
@require_http_methods(["POST"])
def confirmar_recepcion_divisas(request):
    """
    Confirma la recepción de divisas extranjeras en una venta con cobro en efectivo
    y cambia el estado de la transacción a PAGADA.
    """
    print("=== INICIO confirmar_recepcion_divisas ===")
    print(f"Request POST data: {request.POST}")
    
    try:
        codigo_verificacion = request.POST.get('codigo_verificacion')
        tauser_id = request.POST.get('tauser_id')
        total_recibido = request.POST.get('total_recibido')
        denominaciones_json = request.POST.get('denominaciones')
        
        print(f"Código verificación: {codigo_verificacion}")
        print(f"Tauser ID: {tauser_id}")
        print(f"Total recibido: {total_recibido}")
        print(f"Denominaciones: {denominaciones_json}")
        
        if not all([codigo_verificacion, tauser_id, total_recibido, denominaciones_json]):
            print("ERROR: Faltan parámetros requeridos")
            return JsonResponse({
                'success': False,
                'error': 'Faltan parámetros requeridos'
            })
        
        # Obtener la transacción
        from transacciones.models import Transaccion, EstadoTransaccion
        try:
            transaccion = Transaccion.objects.select_related(
                'cliente', 'tipo_operacion', 'estado', 'moneda_origen', 'moneda_destino', 'metodo_cobro', 'metodo_pago'
            ).get(codigo_verificacion=codigo_verificacion)
            print(f"Transacción encontrada: {transaccion.id_transaccion}")
        except Transaccion.DoesNotExist:
            print("ERROR: Transacción no encontrada")
            return JsonResponse({
                'success': False,
                'error': 'Transacción no encontrada'
            })
        
        # Verificar que es una venta con cobro en efectivo
        es_venta_con_efectivo = (
            transaccion.tipo_operacion.codigo == 'VENTA' and 
            transaccion.metodo_cobro and 
            transaccion.metodo_cobro.nombre.lower().find('efectivo') != -1
        )
        
        if not es_venta_con_efectivo:
            print("ERROR: No es una venta con cobro en efectivo")
            return JsonResponse({
                'success': False,
                'error': 'Esta función solo es válida para ventas con cobro en efectivo'
            })
        
        # Verificar que esté en estado pendiente
        if transaccion.estado.codigo != EstadoTransaccion.PENDIENTE:
            print(f"ERROR: Estado incorrecto: {transaccion.estado.nombre}")
            return JsonResponse({
                'success': False,
                'error': f'La transacción no está en estado pendiente. Estado actual: {transaccion.estado.nombre}'
            })
        
        registro_deposito_actual = transaccion.registro_deposito if isinstance(transaccion.registro_deposito, dict) else {}
        if registro_deposito_actual.get('estado') == 'exito':
            print("ERROR: Depósito ya registrado previamente en el simulador")
            return JsonResponse({
                'success': False,
                'error': 'El depósito ya fue registrado previamente en el simulador para esta transacción.'
            })
        
        # Verificar el monto recibido
        import json
        try:
            denominaciones = json.loads(denominaciones_json)
            total_calculado = sum(item['cantidad'] * item['valor'] for item in denominaciones)
            monto_esperado = float(transaccion.monto_origen)
            
            print(f"Total calculado: {total_calculado}")
            print(f"Monto esperado: {monto_esperado}")
            
            # Verificar que el monto sea exactamente igual (con tolerancia de 1 centavo)
            if abs(total_calculado - monto_esperado) > 0.01:
                print("ERROR: Monto no coincide")
                return JsonResponse({
                    'success': False,
                    'error': f'El monto recibido ({total_calculado:.2f}) no coincide con el esperado ({monto_esperado:.2f})'
                })
        except (json.JSONDecodeError, KeyError, ValueError) as e:
            print(f"ERROR: Error al procesar denominaciones: {e}")
            return JsonResponse({
                'success': False,
                'error': 'Error al procesar las denominaciones recibidas'
            })
        
        # Obtener el tauser
        try:
            tauser = Tauser.objects.get(id=tauser_id, es_activo=True)
        except Tauser.DoesNotExist:
            print("ERROR: Tauser no válido o inactivo")
            return JsonResponse({
                'success': False,
                'error': 'Tauser no válido o inactivo'
            })
        
        # Procesar todo dentro de una transacción atómica
        from django.db import transaction as db_transaction
        from tauser.models import Stock, StockDenominacion, HistorialStockDenominacion
        from monedas.models import DenominacionMoneda
        from decimal import Decimal
        
        deposito_info = None
        with db_transaction.atomic():
            # Obtener o crear el stock de la moneda origen para este tauser
            moneda_origen = transaccion.moneda_origen
            stock, stock_created = Stock.objects.get_or_create(
                tauser=tauser,
                moneda=moneda_origen,
                defaults={
                    'cantidad': Decimal('0'),
                    'es_activo': True
                }
            )
            
            # Procesar las denominaciones recibidas y actualizar stock
            # El método agregar_cantidad de StockDenominacion automáticamente actualiza el stock general
            for item in denominaciones:
                denominacion_id = item.get('denominacion_id')
                cantidad_recibida = Decimal(str(item['cantidad']))
                
                # Obtener la denominación
                try:
                    denominacion = DenominacionMoneda.objects.get(id=denominacion_id, moneda=moneda_origen)
                except DenominacionMoneda.DoesNotExist:
                    print(f"ADVERTENCIA: Denominación {denominacion_id} no encontrada, saltando...")
                    continue
                
                # Obtener o crear el stock por denominación
                stock_denominacion, denom_created = StockDenominacion.objects.get_or_create(
                    stock=stock,
                    denominacion=denominacion,
                    defaults={
                        'cantidad': Decimal('0'),
                        'es_activo': True
                    }
                )
                
                # Usar el método agregar_cantidad que automáticamente:
                # 1. Actualiza la cantidad de la denominación
                # 2. Actualiza el stock general
                # 3. Registra en el historial
                stock_denominacion.agregar_cantidad(
                    cantidad_recibida,
                    usuario=request.user,
                    transaccion=transaccion,
                    observaciones=f'Recepción de divisas - Transacción {transaccion.id_transaccion}'
                )
            
            try:
                deposito_info = registrar_deposito_en_simulador(
                    transaccion,
                    usuario_email=request.user.email,
                    extra_payload={
                        'tauser_id': tauser.id,
                        'tauser_nombre': tauser.nombre,
                    }
                )
            except DepositoSimuladorError as deposito_error:
                logger.error(
                    "Error registrando depósito en simulador para transacción %s: %s",
                    transaccion.id_transaccion,
                    deposito_error,
                    exc_info=True
                )
                raise
            except Exception as deposito_error:
                logger.error(
                    "Error inesperado registrando depósito en simulador para transacción %s: %s",
                    transaccion.id_transaccion,
                    deposito_error,
                    exc_info=True
                )
                raise
            
            # Actualizar la transacción con el tauser, estado y observaciones
            from transacciones.models import EstadoTransaccion
            estado_pagada = EstadoTransaccion.objects.get(codigo=EstadoTransaccion.PAGADA)
            transaccion.tauser = tauser
            transaccion.estado = estado_pagada
            transaccion.fecha_pago = timezone.now()
            if transaccion.observaciones:
                transaccion.observaciones += f"\nDivisas recibidas en {tauser.nombre} el {timezone.now()} por {request.user.email}"
            else:
                transaccion.observaciones = f"Divisas recibidas en {tauser.nombre} el {timezone.now()} por {request.user.email}"
            if deposito_info:
                metadata = deposito_info.get('metadata', {})
                metadata['origen'] = 'tauser'
                deposito_info['metadata'] = metadata
                transaccion.registro_deposito = deposito_info
                if deposito_info.get('estado') == 'exito':
                    transaccion.observaciones += (
                        f"\nDepósito registrado en simulador (ID {deposito_info.get('id_pago_externo')}) "
                        f"el {timezone.now()} por {request.user.email}"
                    )
            transaccion.save()
        
        print("=== FIN confirmar_recepcion_divisas - ÉXITO ===")
        print(f"Transacción {transaccion.id_transaccion} marcada como PAGADA y asignada al Tauser {tauser.nombre}")
        
        return JsonResponse({
            'success': True,
            'message': 'Recepción de divisas confirmada exitosamente',
            'transaccion': {
                'id': transaccion.id_transaccion,
                'estado': transaccion.estado.nombre,
                'fecha_pago': transaccion.fecha_pago.strftime('%d/%m/%Y %H:%M') if transaccion.fecha_pago else None,
                'total_recibido': total_calculado,
                'denominaciones_recibidas': len(denominaciones)
            },
            'deposito': deposito_info or {}
        })
        
    except Exception as e:
        print(f"Error en confirmar_recepcion_divisas: {e}")
        return JsonResponse({
            'success': False,
            'error': f'Error interno: {str(e)}'
        })
