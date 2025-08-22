from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from .models import TipoCliente
from roles.decorators import requiere_permiso
from roles.services import RolesService

# Create your views here.

class TipoClienteListView(LoginRequiredMixin, ListView):
    model = TipoCliente
    template_name = 'clientes/tipocliente_list.html'
    context_object_name = 'tipos_cliente'
    paginate_by = 10
    
    def dispatch(self, request, *args, **kwargs):
        if not RolesService.usuario_tiene_permiso(request.user, 'tipocliente_leer'):
            raise PermissionDenied("No tienes permisos para ver tipos de cliente")
        return super().dispatch(request, *args, **kwargs)

class TipoClienteCreateView(LoginRequiredMixin, CreateView):
    model = TipoCliente
    template_name = 'clientes/tipocliente_form.html'
    fields = ['nombre', 'descripcion', 'descuento', 'activo']
    success_url = reverse_lazy('clientes:tipocliente_list')
    
    def dispatch(self, request, *args, **kwargs):
        if not RolesService.usuario_tiene_permiso(request.user, 'tipocliente_crear'):
            raise PermissionDenied("No tienes permisos para crear tipos de cliente")
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        messages.success(self.request, 'Tipo de cliente creado exitosamente.')
        return super().form_valid(form)

class TipoClienteUpdateView(LoginRequiredMixin, UpdateView):
    model = TipoCliente
    template_name = 'clientes/tipocliente_form.html'
    fields = ['nombre', 'descripcion', 'descuento', 'activo']
    success_url = reverse_lazy('clientes:tipocliente_list')
    
    def dispatch(self, request, *args, **kwargs):
        if not RolesService.usuario_tiene_permiso(request.user, 'tipocliente_editar'):
            raise PermissionDenied("No tienes permisos para editar tipos de cliente")
        return super().dispatch(request, *args, **kwargs)
    
    def form_valid(self, form):
        messages.success(self.request, 'Tipo de cliente actualizado exitosamente.')
        return super().form_valid(form)

class TipoClienteDeleteView(LoginRequiredMixin, DeleteView):
    model = TipoCliente
    template_name = 'clientes/tipocliente_confirm_delete.html'
    success_url = reverse_lazy('clientes:tipocliente_list')
    
    def dispatch(self, request, *args, **kwargs):
        if not RolesService.usuario_tiene_permiso(request.user, 'tipocliente_eliminar'):
            raise PermissionDenied("No tienes permisos para eliminar tipos de cliente")
        return super().dispatch(request, *args, **kwargs)
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Tipo de cliente eliminado exitosamente.')
        return super().delete(request, *args, **kwargs)
