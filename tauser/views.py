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


from .models import Tauser, Stock, HistorialStock, StockDenominacion, HistorialStockDenominacion
from .forms import TauserForm, StockForm


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
            
            # Obtener todas las denominaciones de la moneda seleccionada
            denominaciones = DenominacionMoneda.objects.filter(
                moneda=moneda, 
                es_activa=True
            ).order_by('-valor', 'tipo')
            
            if not denominaciones.exists():
                messages.error(request, f'No hay denominaciones configuradas para {moneda.nombre}.')
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
    """Vista AJAX para obtener denominaciones de una moneda"""
    try:
        from monedas.models import DenominacionMoneda
        
        denominaciones = DenominacionMoneda.objects.filter(
            moneda_id=moneda_id,
            es_activa=True
        ).order_by('-valor', 'tipo')
        
        denominaciones_data = []
        for denominacion in denominaciones:
            denominaciones_data.append({
                'id': denominacion.pk,
                'valor': float(denominacion.valor),
                'tipo': denominacion.tipo,
                'mostrar_denominacion': denominacion.mostrar_denominacion(),
                'es_activa': denominacion.es_activa
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
        
        # Verificar que esté pagada
        if transaccion.estado.codigo != EstadoTransaccion.PAGADA:
            return JsonResponse({
                'success': False,
                'error': f'La transacción no está pagada. Estado actual: {transaccion.estado.nombre}'
            })
        
        # Verificar si la transacción requiere retiro físico en Tauser
        requiere_retiro_fisico = False
        if transaccion.tipo_operacion.codigo == 'VENTA':
            # Para ventas, verificar si el método de cobro requiere retiro físico
            if transaccion.metodo_cobro and transaccion.metodo_cobro.requiere_retiro_fisico:
                requiere_retiro_fisico = True
        elif transaccion.tipo_operacion.codigo == 'COMPRA':
            # Para compras, siempre requiere retiro físico (cliente retira divisas)
            requiere_retiro_fisico = True
        
        if not requiere_retiro_fisico:
            return JsonResponse({
                'success': False,
                'error': 'Esta transacción no requiere retiro físico en Tauser. El pago se procesó por transferencia.'
            })
        
        # Obtener el tauser
        try:
            tauser = Tauser.objects.get(id=tauser_id, es_activo=True)
        except Tauser.DoesNotExist:
            return JsonResponse({
                'success': False,
                'error': 'Tauser no válido o inactivo'
            })
        
        # Verificar que el tauser tenga stock de la moneda destino
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
        
        # Preparar datos de la transacción para mostrar
        resumen_detallado = transaccion.get_resumen_detallado()
        
        return JsonResponse({
            'success': True,
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
            },
            'tauser': {
                'id': tauser.id,
                'nombre': tauser.nombre,
                'direccion': tauser.direccion,
            },
            'stock_disponible': {
                'cantidad': float(stock.cantidad),
                'cantidad_formateada': stock.mostrar_cantidad(),
                'esta_bajo_stock': stock.esta_bajo_stock()
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
        
        # Verificar que esté pagada
        if transaccion.estado.codigo != EstadoTransaccion.PAGADA:
            return JsonResponse({
                'success': False,
                'error': f'La transacción no está pagada. Estado actual: {transaccion.estado.nombre}'
            })
        
        # Verificar si la transacción requiere retiro físico en Tauser
        requiere_retiro_fisico = False
        if transaccion.tipo_operacion.codigo == 'VENTA':
            # Para ventas, verificar si el método de cobro requiere retiro físico
            if transaccion.metodo_cobro and transaccion.metodo_cobro.requiere_retiro_fisico:
                requiere_retiro_fisico = True
        elif transaccion.tipo_operacion.codigo == 'COMPRA':
            # Para compras, siempre requiere retiro físico (cliente retira divisas)
            requiere_retiro_fisico = True
        
        if not requiere_retiro_fisico:
            return JsonResponse({
                'success': False,
                'error': 'Esta transacción no requiere retiro físico en Tauser. El pago se procesó por transferencia.'
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
            
            # Reducir el stock
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
            
            # Actualizar la transacción con el tauser y agregar observación
            transaccion.tauser = tauser
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
                'cantidad_restante': float(stock.cantidad),
                'cantidad_restante_formateada': stock.mostrar_cantidad(),
                'esta_bajo_stock': stock.esta_bajo_stock()
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