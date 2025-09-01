from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.views.generic import ListView, CreateView, UpdateView
from django.urls import reverse_lazy
from django.db.models import Q
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
import json

from .models import Moneda
from .forms import MonedaForm


class MonedaListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """Vista para listar todas las monedas"""
    model = Moneda
    template_name = 'monedas/moneda_list.html'
    context_object_name = 'monedas'
    permission_required = 'monedas.view_moneda'
    paginate_by = 20

    def get_queryset(self):
        queryset = Moneda.objects.all()
        
        # Filtro de búsqueda
        q = self.request.GET.get('q')
        if q:
            queryset = queryset.filter(
                Q(nombre__icontains=q) |
                Q(codigo__icontains=q) |
                Q(simbolo__icontains=q)
            )
        
        # Filtro por estado activo/inactivo
        estado = self.request.GET.get('estado')
        if estado == 'activo':
            queryset = queryset.filter(es_activa=True)
        elif estado == 'inactivo':
            queryset = queryset.filter(es_activa=False)
        
        return queryset.order_by('nombre')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Gestión de Monedas'
        context['q'] = self.request.GET.get('q', '')
        context['estado'] = self.request.GET.get('estado', '')
        return context


class MonedaCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """Vista para crear una nueva moneda"""
    model = Moneda
    form_class = MonedaForm
    template_name = 'monedas/moneda_form.html'
    success_url = reverse_lazy('monedas:moneda_list')
    permission_required = 'monedas.add_moneda'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Crear Nueva Moneda'
        context['accion'] = 'Crear'
        return context

    def form_valid(self, form):
        messages.success(self.request, f"Moneda '{form.instance.nombre}' creada exitosamente.")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Error al crear la moneda. Verifique los datos ingresados.")
        return super().form_invalid(form)


class MonedaUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """Vista para editar una moneda existente"""
    model = Moneda
    form_class = MonedaForm
    template_name = 'monedas/moneda_form.html'
    success_url = reverse_lazy('monedas:moneda_list')
    permission_required = 'monedas.change_moneda'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = f'Editar Moneda: {self.object.nombre}'
        context['accion'] = 'Actualizar'
        return context

    def form_valid(self, form):
        messages.success(self.request, f"Moneda '{form.instance.nombre}' actualizada exitosamente.")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Error al actualizar la moneda. Verifique los datos ingresados.")
        return super().form_invalid(form)


@login_required
@permission_required('monedas.change_moneda', raise_exception=True)
@require_http_methods(["POST"])
def toggle_moneda_status(request, pk):
    """Vista AJAX para cambiar el estado activo/inactivo de una moneda"""
    try:
        moneda = get_object_or_404(Moneda, pk=pk)
        
        moneda.es_activa = not moneda.es_activa
        moneda.save()
        
        status_text = "activada" if moneda.es_activa else "desactivada"
        return JsonResponse({
            'success': True,
            'message': f'Moneda {status_text} exitosamente.',
            'nueva_estado': moneda.es_activa
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error al cambiar el estado: {str(e)}'
        })


@login_required
@permission_required('monedas.view_moneda', raise_exception=True)
def moneda_detail_api(request, pk):
    """API para obtener detalles de una moneda (para uso en JavaScript)"""
    try:
        moneda = get_object_or_404(Moneda, pk=pk)
        data = {
            'id': moneda.id,
            'nombre': moneda.nombre,
            'codigo': moneda.codigo,
            'simbolo': moneda.simbolo,
            'es_activa': moneda.es_activa,
            'fecha_creacion': moneda.fecha_creacion.strftime('%d/%m/%Y %H:%M'),
            'fecha_actualizacion': moneda.fecha_actualizacion.strftime('%d/%m/%Y %H:%M'),
        }
        return JsonResponse({'success': True, 'data': data})
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)})


@login_required
@permission_required('monedas.view_moneda', raise_exception=True) 
def dashboard_monedas(request):
    """Vista del dashboard específico para monedas"""
    context = {
        'titulo': 'Dashboard de Monedas',
        'total_monedas': Moneda.objects.count(),
        'monedas_activas': Moneda.objects.filter(es_activa=True).count(),
        'monedas_inactivas': Moneda.objects.filter(es_activa=False).count(),
        'monedas_recientes': Moneda.objects.order_by('-fecha_creacion')[:5],
    }
    
    return render(request, 'monedas/dashboard.html', context)
