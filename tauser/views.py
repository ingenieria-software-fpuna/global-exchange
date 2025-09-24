from django.shortcuts import render, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.views.generic import ListView, CreateView, UpdateView
from django.urls import reverse_lazy
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from .models import Tauser
from .forms import TauserForm


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