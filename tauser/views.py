from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.views.generic import ListView, CreateView, UpdateView, DetailView
from django.urls import reverse_lazy
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from .models import Tauser, Stock
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
                'cantidad_minima': stock.cantidad_minima,
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
                'cantidad_minima': stock.cantidad_minima if stock else 0,
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
    """Cargar/agregar stock a un tauser"""
    tauser = get_object_or_404(Tauser, pk=pk)
    
    if request.method == 'POST':
        try:
            moneda_id = request.POST.get('moneda')
            cantidad_agregar = request.POST.get('cantidad_agregar')
            cantidad_minima = request.POST.get('cantidad_minima', 0)
            es_activo = request.POST.get('es_activo') == 'on'
            
            if not moneda_id or not cantidad_agregar:
                messages.error(request, 'Moneda y cantidad son requeridos.')
                return redirect('tauser:tauser_detail', pk=tauser.pk)
            
            from monedas.models import Moneda
            moneda = get_object_or_404(Moneda, pk=moneda_id)
            cantidad_agregar = float(cantidad_agregar)
            cantidad_minima = float(cantidad_minima) if cantidad_minima else 0
            
            if cantidad_agregar <= 0:
                messages.error(request, 'La cantidad debe ser mayor a 0.')
                return redirect('tauser:tauser_detail', pk=tauser.pk)
            
            # Buscar si ya existe stock para esta moneda
            stock_existente = Stock.objects.filter(tauser=tauser, moneda=moneda).first()
            
            if stock_existente:
                # Agregar cantidad al stock existente
                stock_existente.agregar_cantidad(cantidad_agregar)
                if cantidad_minima > 0:
                    stock_existente.cantidad_minima = cantidad_minima
                if es_activo:
                    stock_existente.es_activo = True
                stock_existente.save()
                
                messages.success(request, 
                    f'Se agregaron {moneda.simbolo}{cantidad_agregar:.{moneda.decimales}f} al stock de {moneda.nombre}. '
                    f'Nueva cantidad: {stock_existente.mostrar_cantidad()}')
            else:
                # Crear nuevo stock
                nuevo_stock = Stock.objects.create(
                    tauser=tauser,
                    moneda=moneda,
                    cantidad=cantidad_agregar,
                    cantidad_minima=cantidad_minima,
                    es_activo=es_activo
                )
                
                messages.success(request, 
                    f'Stock creado para {moneda.nombre} con {moneda.simbolo}{cantidad_agregar:.{moneda.decimales}f}')
            
            return redirect('tauser:tauser_detail', pk=tauser.pk)
            
        except (ValueError, TypeError) as e:
            messages.error(request, 'Error en los datos proporcionados.')
            return redirect('tauser:tauser_detail', pk=tauser.pk)
        except Exception as e:
            messages.error(request, f'Error al cargar el stock: {str(e)}')
            return redirect('tauser:tauser_detail', pk=tauser.pk)
    
    return redirect('tauser:tauser_detail', pk=tauser.pk)