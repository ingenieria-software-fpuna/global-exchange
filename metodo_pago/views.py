from django.shortcuts import render, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.views.generic import ListView, CreateView, UpdateView
from django.urls import reverse_lazy
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from .models import MetodoPago
from .forms import MetodoPagoForm


class MetodoPagoListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """Lista de métodos de pago"""
    model = MetodoPago
    template_name = 'metodo_pago/metodopago_list.html'
    context_object_name = 'metodos'
    permission_required = 'metodo_pago.view_metodopago'
    paginate_by = 20

    def get_queryset(self):
        queryset = MetodoPago.objects.all()

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
        context['titulo'] = 'Métodos de Pago'
        context['q'] = self.request.GET.get('q', '')
        context['estado'] = self.request.GET.get('estado', '')
        return context


class MetodoPagoCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """Crear método de pago"""
    model = MetodoPago
    form_class = MetodoPagoForm
    template_name = 'metodo_pago/metodopago_form.html'
    success_url = reverse_lazy('metodo_pago:metodopago_list')
    permission_required = 'metodo_pago.add_metodopago'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Crear Método de Pago'
        context['accion'] = 'Crear'
        return context

    def form_valid(self, form):
        messages.success(self.request, f"Método de pago '{form.instance.nombre}' creado correctamente.")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Error al crear el método de pago. Verifique los datos.")
        return super().form_invalid(form)


class MetodoPagoUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """Editar método de pago"""
    model = MetodoPago
    form_class = MetodoPagoForm
    template_name = 'metodo_pago/metodopago_form.html'
    success_url = reverse_lazy('metodo_pago:metodopago_list')
    permission_required = 'metodo_pago.change_metodopago'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = f'Editar Método: {self.object.nombre}'
        context['accion'] = 'Actualizar'
        return context

    def form_valid(self, form):
        messages.success(self.request, f"Método de pago '{form.instance.nombre}' actualizado correctamente.")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Error al actualizar el método de pago. Verifique los datos.")
        return super().form_invalid(form)


@login_required
@permission_required('metodo_pago.change_metodopago', raise_exception=True)
@require_http_methods(["POST"])
def toggle_metodopago_status(request, pk):
    """Cambiar estado activo/inactivo (AJAX)"""
    metodo = get_object_or_404(MetodoPago, pk=pk)
    metodo.es_activo = not metodo.es_activo
    metodo.save()
    return JsonResponse({
        'success': True,
        'nueva_estado': metodo.es_activo,
        'message': f"Método {'activado' if metodo.es_activo else 'desactivado'} correctamente."
    })

