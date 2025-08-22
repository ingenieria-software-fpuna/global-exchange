from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.db.models import Q
from .models import TipoCliente, Cliente
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

# Vistas para Clientes
class ClienteListView(LoginRequiredMixin, ListView):
    model = Cliente
    template_name = 'clientes/cliente_list.html'
    context_object_name = 'clientes'
    paginate_by = 10
    
    def dispatch(self, request, *args, **kwargs):
        if not RolesService.usuario_tiene_permiso(request.user, 'cliente_leer'):
            raise PermissionDenied("No tienes permisos para ver clientes")
        return super().dispatch(request, *args, **kwargs)
    
    def get_queryset(self):
        queryset = Cliente.objects.select_related('tipo_cliente').prefetch_related('usuarios_asociados')
        
        # Filtro de búsqueda
        q = self.request.GET.get('q')
        if q:
            queryset = queryset.filter(
                Q(nombre_comercial__icontains=q) |
                Q(ruc__icontains=q) |
                Q(correo_electronico__icontains=q) |
                Q(tipo_cliente__nombre__icontains=q)
            )
        
        # Filtro por tipo de cliente
        tipo_cliente = self.request.GET.get('tipo_cliente')
        if tipo_cliente:
            queryset = queryset.filter(tipo_cliente_id=tipo_cliente)
        
        # Filtro por estado
        estado = self.request.GET.get('estado')
        if estado in ['activo', 'inactivo']:
            queryset = queryset.filter(activo=(estado == 'activo'))
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tipos_cliente'] = TipoCliente.objects.filter(activo=True)
        context['q'] = self.request.GET.get('q', '')
        context['tipo_cliente_filter'] = self.request.GET.get('tipo_cliente', '')
        context['estado_filter'] = self.request.GET.get('estado', '')
        return context

class ClienteCreateView(LoginRequiredMixin, CreateView):
    model = Cliente
    template_name = 'clientes/cliente_form.html'
    fields = [
        'nombre_comercial', 'ruc', 'direccion', 'correo_electronico', 
        'numero_telefono', 'tipo_cliente', 'usuarios_asociados', 'activo'
    ]
    success_url = reverse_lazy('clientes:cliente_list')
    
    def dispatch(self, request, *args, **kwargs):
        if not RolesService.usuario_tiene_permiso(request.user, 'cliente_crear'):
            raise PermissionDenied("No tienes permisos para crear clientes")
        return super().dispatch(request, *args, **kwargs)
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Solo mostrar tipos de cliente activos
        form.fields['tipo_cliente'].queryset = TipoCliente.objects.filter(activo=True)
        # Solo mostrar usuarios activos
        form.fields['usuarios_asociados'].queryset = self.request.user.__class__.objects.filter(activo=True)
        return form
    
    def form_valid(self, form):
        messages.success(self.request, 'Cliente creado exitosamente.')
        return super().form_valid(form)

class ClienteUpdateView(LoginRequiredMixin, UpdateView):
    model = Cliente
    template_name = 'clientes/cliente_form.html'
    fields = [
        'nombre_comercial', 'ruc', 'direccion', 'correo_electronico', 
        'numero_telefono', 'tipo_cliente', 'usuarios_asociados', 'activo'
    ]
    success_url = reverse_lazy('clientes:cliente_list')
    
    def dispatch(self, request, *args, **kwargs):
        if not RolesService.usuario_tiene_permiso(request.user, 'cliente_editar'):
            raise PermissionDenied("No tienes permisos para editar clientes")
        return super().dispatch(request, *args, **kwargs)
    
    def get_form(self, form_class=None):
        form = super().get_form(form_class)
        # Solo mostrar tipos de cliente activos
        form.fields['tipo_cliente'].queryset = TipoCliente.objects.filter(activo=True)
        # Solo mostrar usuarios activos
        form.fields['usuarios_asociados'].queryset = self.request.user.__class__.objects.filter(activo=True)
        return form
    
    def form_valid(self, form):
        messages.success(self.request, 'Cliente actualizado exitosamente.')
        return super().form_valid(form)

class ClienteDeleteView(LoginRequiredMixin, DeleteView):
    model = Cliente
    template_name = 'clientes/cliente_confirm_delete.html'
    success_url = reverse_lazy('clientes:cliente_list')
    
    def dispatch(self, request, *args, **kwargs):
        if not RolesService.usuario_tiene_permiso(request.user, 'cliente_eliminar'):
            raise PermissionDenied("No tienes permisos para eliminar clientes")
        return super().dispatch(request, *args, **kwargs)
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Cliente eliminado exitosamente.')
        return super().delete(request, *args, **kwargs)
