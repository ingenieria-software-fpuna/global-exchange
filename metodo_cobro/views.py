from django.shortcuts import render, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.views.generic import ListView, CreateView, UpdateView
from django.urls import reverse_lazy
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from .models import MetodoCobro
from .forms import MetodoCobroForm


class MetodoCobroListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """Lista de métodos de cobro"""
    model = MetodoCobro
    template_name = 'metodo_cobro/metodocobro_list.html'
    context_object_name = 'metodos'
    permission_required = 'metodo_cobro.view_metodocobro'
    paginate_by = 20

    def get_queryset(self):
        queryset = MetodoCobro.objects.prefetch_related('monedas_permitidas').all()

        q = self.request.GET.get('q')
        if q:
            queryset = queryset.filter(
                Q(nombre__icontains=q) | Q(descripcion__icontains=q)
            )

        estado = self.request.GET.get('estado')
        if estado == 'activo':
            queryset = queryset.filter(es_activo=True)
        elif estado == 'inactivo':
            queryset = queryset.filter(es_activo=False)

        return queryset.order_by('nombre')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Métodos de Cobro'
        context['q'] = self.request.GET.get('q', '')
        context['estado'] = self.request.GET.get('estado', '')
        return context


class MetodoCobroCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """Crear método de cobro"""
    model = MetodoCobro
    form_class = MetodoCobroForm
    template_name = 'metodo_cobro/metodocobro_form.html'
    success_url = reverse_lazy('metodo_cobro:metodocobro_list')
    permission_required = 'metodo_cobro.add_metodocobro'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Crear Método de Cobro'
        context['accion'] = 'Crear'
        return context

    def form_valid(self, form):
        messages.success(self.request, f"Método de cobro '{form.instance.nombre}' creado correctamente.")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Error al crear el método de cobro. Verifique los datos.")
        return super().form_invalid(form)


class MetodoCobroUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """Editar método de cobro"""
    model = MetodoCobro
    form_class = MetodoCobroForm
    template_name = 'metodo_cobro/metodocobro_form.html'
    success_url = reverse_lazy('metodo_cobro:metodocobro_list')
    permission_required = 'metodo_cobro.change_metodocobro'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = f'Editar Método: {self.object.nombre}'
        context['accion'] = 'Actualizar'
        return context

    def form_valid(self, form):
        messages.success(self.request, f"Método de cobro '{form.instance.nombre}' actualizado correctamente.")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Error al actualizar el método de cobro. Verifique los datos.")
        return super().form_invalid(form)


@login_required
@permission_required('metodo_cobro.change_metodocobro', raise_exception=True)
@require_http_methods(["POST"])
def toggle_metodocobro_status(request, pk):
    """Cambiar estado activo/inactivo (AJAX)"""
    metodo = get_object_or_404(MetodoCobro, pk=pk)
    metodo.es_activo = not metodo.es_activo
    metodo.save()
    return JsonResponse({
        'success': True,
        'nueva_estado': metodo.es_activo,
        'message': f"Método {'activado' if metodo.es_activo else 'desactivado'} correctamente."
    })