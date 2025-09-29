from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.views.generic import ListView, CreateView, DetailView
from django.urls import reverse_lazy
from django.db.models import Q
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
import json

from .models import TasaCambio
from clientes.models import Cliente
from .forms import TasaCambioForm, TasaCambioSearchForm
from monedas.models import Moneda
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from metodo_pago.models import MetodoPago
from metodo_cobro.models import MetodoCobro


class TasaCambioListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """Vista para listar las cotizaciones actuales (activas)"""
    model = TasaCambio
    template_name = 'tasa_cambio/tasacambio_list.html'
    context_object_name = 'cotizaciones'
    permission_required = 'tasa_cambio.view_tasacambio'
    paginate_by = 20

    def get_queryset(self):
        # Solo mostrar tasas activas por defecto
        queryset = TasaCambio.objects.select_related('moneda').filter(es_activa=True)

        # Filtro de búsqueda
        q = self.request.GET.get('q')
        if q:
            queryset = queryset.filter(
                Q(moneda__nombre__icontains=q) |
                Q(moneda__codigo__icontains=q) |
                Q(moneda__simbolo__icontains=q)
            )

        # Filtro por moneda específica
        moneda_id = self.request.GET.get('moneda')
        if moneda_id:
            queryset = queryset.filter(moneda_id=moneda_id)

        return queryset.order_by('moneda__nombre')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Gestión de Cotizaciones'
        context['search_form'] = TasaCambioSearchForm(self.request.GET)
        context['q'] = self.request.GET.get('q', '')
        context['moneda'] = self.request.GET.get('moneda', '')
        context['estado'] = self.request.GET.get('estado', '')
        context['fecha_desde'] = self.request.GET.get('fecha_desde', '')
        context['fecha_hasta'] = self.request.GET.get('fecha_hasta', '')
        context['monedas'] = Moneda.objects.filter(es_activa=True).order_by('nombre')
        return context


class TasaCambioHistorialView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """Vista para mostrar el historial de cotizaciones de una moneda específica"""
    model = TasaCambio
    template_name = 'tasa_cambio/tasacambio_historial.html'
    context_object_name = 'historial_tasas'
    permission_required = 'tasa_cambio.view_tasacambio'
    paginate_by = 20

    def get_queryset(self):
        self.moneda = get_object_or_404(Moneda, pk=self.kwargs['moneda_id'])
        queryset = TasaCambio.objects.select_related('moneda').filter(
            moneda=self.moneda
        ).order_by('-fecha_creacion')

        # Filtro por estado activo/inactivo
        estado = self.request.GET.get('estado')
        if estado == 'activo':
            queryset = queryset.filter(es_activa=True)
        elif estado == 'inactivo':
            queryset = queryset.filter(es_activa=False)

        # Filtro por fecha desde
        fecha_desde = self.request.GET.get('fecha_desde')
        if fecha_desde:
            queryset = queryset.filter(fecha_creacion__date__gte=fecha_desde)

        # Filtro por fecha hasta
        fecha_hasta = self.request.GET.get('fecha_hasta')
        if fecha_hasta:
            queryset = queryset.filter(fecha_creacion__date__lte=fecha_hasta)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['moneda'] = self.moneda
        context['titulo'] = f'Historial de {self.moneda.nombre}'
        context['estado'] = self.request.GET.get('estado', '')
        context['fecha_desde'] = self.request.GET.get('fecha_desde', '')
        context['fecha_hasta'] = self.request.GET.get('fecha_hasta', '')

        # Datos para gráficos
        historial_datos = list(self.get_queryset()[:50].values(
            'fecha_creacion', 'precio_base', 'comision_compra',
            'comision_venta', 'es_activa'
        ))

        # Calcular precios de compra y venta para el gráfico
        for item in historial_datos:
            item['precio_compra'] = float(item['precio_base']) - float(item['comision_compra'])
            item['precio_venta'] = float(item['precio_base']) + float(item['comision_venta'])
            item['fecha_str'] = item['fecha_creacion'].strftime('%Y-%m-%d %H:%M')

        context['datos_grafico'] = json.dumps(historial_datos, default=str)
        return context


class TasaCambioCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """Vista para crear una nueva cotización"""
    model = TasaCambio
    form_class = TasaCambioForm
    template_name = 'tasa_cambio/tasacambio_form.html'
    success_url = reverse_lazy('tasa_cambio:tasacambio_list')
    permission_required = 'tasa_cambio.add_tasacambio'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Crear Nueva Cotización'
        context['accion'] = 'Crear'
        return context

    def form_valid(self, form):
        # Verificar si había una cotización anterior para mostrar mensaje informativo
        moneda = form.instance.moneda
        
        # Usar la información del formulario si está disponible
        cotizacion_existente = form.cleaned_data.get('cotizacion_existente')
        
        if cotizacion_existente:
            messages.info(
                self.request,
                f"Ya existía una cotización activa para {moneda.nombre} "
                f"(Compra: {cotizacion_existente.tasa_compra}, "
                f"Venta: {cotizacion_existente.tasa_venta}). "
                f"La cotización anterior ha sido desactivada automáticamente."
            )
        
        messages.success(
            self.request, 
            f"Cotización para {moneda.nombre} creada exitosamente."
        )
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(
            self.request, 
            "Error al crear la cotización. Verifique los datos ingresados."
        )
        return super().form_invalid(form)




@login_required
@permission_required('tasa_cambio.view_tasacambio', raise_exception=True)
def tasacambio_detail_api(request, pk):
    """API para obtener detalles de una cotización (para uso en JavaScript)"""
    try:
        tasacambio = get_object_or_404(TasaCambio, pk=pk)
        data = {
            'id': tasacambio.id,
            'moneda_nombre': tasacambio.moneda.nombre,
            'moneda_codigo': tasacambio.moneda.codigo,
            'moneda_simbolo': tasacambio.moneda.simbolo,
            'tasa_compra': float(tasacambio.tasa_compra),
            'tasa_venta': float(tasacambio.tasa_venta),
            'spread': float(tasacambio.spread),
            'spread_porcentual': round(tasacambio.spread_porcentual, 2),
            'es_activa': tasacambio.es_activa,
            'fecha_creacion': tasacambio.fecha_creacion.strftime('%d/%m/%Y %H:%M'),
            'fecha_actualizacion': tasacambio.fecha_actualizacion.strftime('%d/%m/%Y %H:%M'),
        }
        return JsonResponse({'success': True, 'data': data})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@login_required
# @permission_required('tasa_cambio.view_tasacambio', raise_exception=True)
def dashboard_tasacambio(request):
    """Vista del dashboard específico para cotizaciones"""
    # Monedas activas para el simulador (todas las activas)
    monedas_activas = Moneda.objects.filter(es_activa=True).order_by('nombre')
    # Clientes asociados al usuario
    clientes_usuario = Cliente.objects.filter(
        activo=True,
        usuarios_asociados=request.user
    ).select_related('tipo_cliente').order_by('nombre_comercial')

    context = {
        'titulo': 'Simulador de Cambio',
        'total_cotizaciones': TasaCambio.objects.count(),
        'cotizaciones_activas': TasaCambio.objects.filter(es_activa=True).count(),
        'cotizaciones_inactivas': TasaCambio.objects.filter(es_activa=False).count(),
        'cotizaciones_recientes': TasaCambio.objects.select_related('moneda').order_by('-fecha_creacion')[:5],
        'monedas_con_cotizacion': TasaCambio.objects.filter(es_activa=True).select_related('moneda').count(),
        'monedas': monedas_activas,
        'clientes': clientes_usuario,
        # metodos_pago removidos - el dashboard ahora es solo simulador
    }
    
    return render(request, 'tasa_cambio/dashboard.html', context)


def simular_cambio_api(request):
    """
    API para simular un cambio entre dos monedas usando las tasas activas.

    Reglas:
    - Base operativa: PYG (Guaraní). Si ninguna de las dos es PYG, se cruza vía PYG.
    - De moneda -> PYG: se usa tasa_compra de la moneda origen.
    - De PYG -> moneda: se usa tasa_venta de la moneda destino.
    - De A -> B (ambas distintas de PYG): resultado = monto * tasa_compra_A / tasa_venta_B.
    - Si origen == destino, resultado = monto.
    """
    codigo_origen = request.GET.get('origen')
    codigo_destino = request.GET.get('destino')
    monto_str = request.GET.get('monto')
    cliente_id = request.GET.get('cliente_id')
    metodo_pago_id = request.GET.get('metodo_pago_id')

    if not codigo_origen or not codigo_destino or not monto_str:
        return JsonResponse({'success': False, 'message': 'Parámetros requeridos: origen, destino, monto.'}, status=400)

    try:
        monto = Decimal(monto_str)
        if monto <= 0:
            raise InvalidOperation
    except Exception:
        return JsonResponse({'success': False, 'message': 'Monto inválido.'}, status=400)

    BASE = 'PYG'

    # Validar que exactamente uno de los dos sea PYG
    origen_es_pyg = codigo_origen.upper() == BASE
    destino_es_pyg = codigo_destino.upper() == BASE
    if origen_es_pyg and destino_es_pyg:
        return JsonResponse({'success': False, 'message': 'Seleccione una moneda distinta de PYG en uno de los lados.'}, status=400)
    if not origen_es_pyg and not destino_es_pyg:
        return JsonResponse({'success': False, 'message': 'No se permiten cruces entre monedas. Use PYG como origen o destino.'}, status=400)

    # Cargar la moneda no-PYG desde BD
    otro_codigo = codigo_destino if origen_es_pyg else codigo_origen
    try:
        moneda_no_pyg = Moneda.objects.get(codigo__iexact=otro_codigo, es_activa=True)
    except Moneda.DoesNotExist:
        return JsonResponse({'success': False, 'message': f'Moneda {otro_codigo.upper()} no encontrada o inactiva.'}, status=404)

    # Helper para obtener la tasa activa de una moneda
    def get_tasa_activa(moneda: Moneda):
        return TasaCambio.objects.filter(moneda=moneda, es_activa=True).first()

    # Si se especifica cliente, validar asociación y obtener descuento
    from decimal import Decimal as D
    descuento_pct = D('0')
    cliente_info = None
    if cliente_id:
        if not request.user.is_authenticated:
            return JsonResponse({'success': False, 'message': 'Autenticación requerida para usar cliente.'}, status=401)
        try:
            cliente = Cliente.objects.select_related('tipo_cliente').get(
                pk=cliente_id, activo=True, usuarios_asociados=request.user
            )
            descuento_pct = D(str(cliente.tipo_cliente.descuento or 0))
            cliente_info = {
                'id': cliente.id,
                'nombre': cliente.nombre_comercial,
                'tipo': cliente.tipo_cliente.nombre,
                'descuento': float(descuento_pct),
            }
        except Cliente.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Cliente inválido o no asociado.'}, status=403)

    # Conversión según combinaciones
    detalle = ''
    tasa_origen_usada = None
    tasa_destino_usada = None
    resultado = Decimal('0')
    resultado_formateado = ''

    # Resolver método de pago y comisión
    metodo_info = None
    comision_pct = Decimal('0')
    if metodo_pago_id:
        try:
            mp = MetodoPago.objects.get(pk=metodo_pago_id, es_activo=True)
            comision_pct = Decimal(str(mp.comision))
            metodo_info = {
                'id': mp.id,
                'nombre': mp.nombre,
                'comision': float(comision_pct),
            }
        except MetodoPago.DoesNotExist:
            return JsonResponse({'success': False, 'message': 'Método de pago inválido o inactivo.'}, status=404)

    # Caso: origen es PYG
    if origen_es_pyg:
        destino = moneda_no_pyg
        tasa_destino = get_tasa_activa(destino)
        if not tasa_destino:
            return JsonResponse({'success': False, 'message': f'No hay tasa activa para {destino.codigo}.'}, status=404)

        # Calcular comisión de venta ajustada por descuento
        comision_venta_ajustada = Decimal(tasa_destino.comision_venta)
        if descuento_pct > 0:
            comision_venta_ajustada = comision_venta_ajustada * (D('1') - (descuento_pct / D('100')))
        
        # Calcular precio de venta: precio_base + comision_venta_ajustada
        precio_venta = Decimal(tasa_destino.precio_base) + comision_venta_ajustada
            
        # De PYG a destino: usar precio de venta calculado
        resultado = (monto / precio_venta).quantize(Decimal('1.' + '0'*max(destino.decimales, 0)), rounding=ROUND_HALF_UP)
        tasa_destino_usada = {
            'moneda': destino.codigo,
            'tipo': 'venta' + (' (ajustada)' if descuento_pct > 0 else ''),
            'valor': float(precio_venta),
        }
        detalle = f"PYG -> {destino.codigo} usando precio de venta"
        if descuento_pct > 0:
            detalle += f" con descuento {descuento_pct}% en comisión"
        resultado_formateado = destino.mostrar_monto(resultado)
        # Calcular comisión y total neto sobre la moneda destino
        subtotal = resultado
        comision_monto = (subtotal * (comision_pct / Decimal('100'))).quantize(Decimal('1.' + '0'*max(destino.decimales, 0)), rounding=ROUND_HALF_UP)
        total_neto = (subtotal - comision_monto).quantize(Decimal('1.' + '0'*max(destino.decimales, 0)), rounding=ROUND_HALF_UP)
        subtotal_formateado = destino.mostrar_monto(subtotal)
        comision_formateada = destino.mostrar_monto(comision_monto)
        total_formateado = destino.mostrar_monto(total_neto)

    else:
        # destino_es_pyg
        origen = moneda_no_pyg
        tasa_origen = get_tasa_activa(origen)
        if not tasa_origen:
            return JsonResponse({'success': False, 'message': f'No hay tasa activa para {origen.codigo}.'}, status=404)
        
        # Calcular comisión de compra ajustada por descuento
        comision_compra_ajustada = Decimal(tasa_origen.comision_compra)
        if descuento_pct > 0:
            comision_compra_ajustada = comision_compra_ajustada * (D('1') - (descuento_pct / D('100')))
        
        # Calcular precio de compra: precio_base - comision_compra_ajustada
        precio_compra = Decimal(tasa_origen.precio_base) - comision_compra_ajustada
        
        # De origen a PYG: usar precio de compra calculado
        resultado = (monto * precio_compra).quantize(Decimal('1'), rounding=ROUND_HALF_UP)
        tasa_origen_usada = {
            'moneda': origen.codigo,
            'tipo': 'compra' + (' (ajustada)' if descuento_pct > 0 else ''),
            'valor': float(precio_compra),
        }
        detalle = f"{origen.codigo} -> PYG usando precio de compra"
        if descuento_pct > 0:
            detalle += f" con descuento {descuento_pct}% en comisión"
        resultado_formateado = f"PYG {int(resultado)}"
        # Calcular comisión y total neto sobre PYG
        subtotal = resultado
        comision_monto = (subtotal * (comision_pct / Decimal('100'))).quantize(Decimal('1'), rounding=ROUND_HALF_UP)
        total_neto = (subtotal - comision_monto).quantize(Decimal('1'), rounding=ROUND_HALF_UP)
        subtotal_formateado = f"PYG {int(subtotal)}"
        comision_formateada = f"PYG {int(comision_monto)}"
        total_formateado = f"PYG {int(total_neto)}"

    # Si hay método de pago, usar total neto como resultado principal
    if comision_pct > 0:
        resultado = total_neto
        resultado_formateado = total_formateado

    return JsonResponse({
        'success': True,
        'data': {
            'resultado': float(resultado),
            'resultado_formateado': resultado_formateado,
            'detalle': detalle,
            'tasa_origen': tasa_origen_usada,
            'tasa_destino': tasa_destino_usada,
            'cliente': cliente_info,
            'metodo_pago': metodo_info,
            'subtotal': float(subtotal),
            'subtotal_formateado': subtotal_formateado,
            'comision_pct': float(comision_pct),
            'comision_monto': float(comision_monto),
            'comision_monto_formateado': comision_formateada,
            'total_neto': float(total_neto),
            'total_neto_formateado': total_formateado,
        }
    })
