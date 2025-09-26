from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.decorators import login_required, permission_required
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .models import TipoCliente, Cliente
from .forms import ClienteForm, ClienteUpdateForm, TipoClienteForm, TipoClienteUpdateForm

# Create your views here.

class TipoClienteListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = TipoCliente
    template_name = 'clientes/tipocliente_list.html'
    context_object_name = 'tipos'
    paginate_by = 10
    permission_required = 'clientes.view_tipocliente'

    def get_queryset(self):
        queryset = TipoCliente.objects.all()
        
        # Filtro de búsqueda
        q = self.request.GET.get('q')
        if q:
            queryset = queryset.filter(
                Q(nombre__icontains=q) |
                Q(descripcion__icontains=q)
            )
        
        # Filtro por estado
        estado = self.request.GET.get('estado')
        if estado == 'activo':
            queryset = queryset.filter(activo=True)
        elif estado == 'inactivo':
            queryset = queryset.filter(activo=False)
        
        return queryset.order_by('nombre')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['q'] = self.request.GET.get('q', '')
        context['estado'] = self.request.GET.get('estado', '')
        context['can_create_tipocliente'] = self.request.user.has_perm('clientes.add_tipocliente')
        context['can_edit_tipocliente'] = self.request.user.has_perm('clientes.change_tipocliente')
        return context

class TipoClienteCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = TipoCliente
    form_class = TipoClienteForm
    template_name = 'clientes/tipocliente_form.html'
    success_url = reverse_lazy('clientes:tipocliente_list')
    permission_required = 'clientes.add_tipocliente'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Crear Tipo de Cliente'
        context['accion'] = 'Crear'
        return context

    def form_valid(self, form):
        messages.success(self.request, 'Tipo de cliente creado exitosamente.')
        return super().form_valid(form)

class TipoClienteUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = TipoCliente
    form_class = TipoClienteUpdateForm
    template_name = 'clientes/tipocliente_form.html'
    success_url = reverse_lazy('clientes:tipocliente_list')
    permission_required = 'clientes.change_tipocliente'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = f'Editar Tipo de Cliente: {self.object.nombre}'
        context['accion'] = 'Actualizar'
        return context

    def form_valid(self, form):
        messages.success(self.request, 'Tipo de cliente actualizado exitosamente.')
        return super().form_valid(form)

class TipoClienteDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = TipoCliente
    template_name = 'clientes/tipocliente_confirm_delete.html'
    success_url = reverse_lazy('clientes:tipocliente_list')
    permission_required = 'clientes.delete_tipocliente'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Eliminar Tipo de Cliente'
        return context


# Vistas para Clientes
class ClienteListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Cliente
    template_name = 'clientes/cliente_list.html'
    context_object_name = 'clientes'
    paginate_by = 10
    permission_required = 'clientes.view_cliente'
    
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
        context['can_create_cliente'] = self.request.user.has_perm('clientes.add_cliente')
        context['can_edit_cliente'] = self.request.user.has_perm('clientes.change_cliente')
        return context

class ClienteCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Cliente
    form_class = ClienteForm
    template_name = 'clientes/cliente_form.html'
    success_url = reverse_lazy('clientes:cliente_list')
    permission_required = 'clientes.add_cliente'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Crear Cliente'
        context['accion'] = 'Crear'
        return context
    
    def form_valid(self, form):
        response = super().form_valid(form)
        
        # Verificar si el cliente se creó sin usuarios asociados
        usuarios_asociados = form.cleaned_data.get('usuarios_asociados', [])
        if not usuarios_asociados:
            messages.warning(
                self.request, 
                'ATENCIÓN: El cliente se ha creado sin usuarios asociados. '
                'Ningún usuario podrá operar en nombre de este cliente hasta que se asignen usuarios.'
            )
        else:
            messages.success(self.request, 'Cliente creado exitosamente.')
        
        return response

class ClienteUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Cliente
    form_class = ClienteUpdateForm
    template_name = 'clientes/cliente_form.html'
    success_url = reverse_lazy('clientes:cliente_list')
    permission_required = 'clientes.change_cliente'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = f'Editar Cliente: {self.object.nombre_comercial}'
        context['accion'] = 'Actualizar'
        return context
    
    def form_valid(self, form):
        response = super().form_valid(form)
        
        # Verificar si el cliente se actualizó sin usuarios asociados
        usuarios_asociados = form.cleaned_data.get('usuarios_asociados', [])
        if not usuarios_asociados:
            messages.warning(
                self.request, 
                'ATENCIÓN: El cliente se ha actualizado sin usuarios asociados. '
                'Ningún usuario podrá operar en nombre de este cliente hasta que se asignen usuarios.'
            )
        else:
            messages.success(self.request, 'Cliente actualizado exitosamente.')
        
        return response




@login_required
@permission_required('clientes.view_cliente', raise_exception=True)
def get_cliente_relations(request, pk):
    """API para obtener información sobre las relaciones de un cliente"""
    try:
        cliente = get_object_or_404(Cliente, pk=pk)
        
        # Contar usuarios asociados
        usuarios_count = cliente.usuarios_asociados.count()
        
        relations_info = []
        if usuarios_count > 0:
            relations_info.append(f"Este cliente tiene {usuarios_count} usuario{'s' if usuarios_count != 1 else ''} asociado{'s' if usuarios_count != 1 else ''}")
        
        return JsonResponse({
            'success': True,
            'relations': relations_info,
            'has_relations': len(relations_info) > 0
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error al obtener relaciones: {str(e)}'
        })

@login_required
@permission_required('clientes.view_tipocliente', raise_exception=True)
def get_tipocliente_relations(request, pk):
    """API para obtener información sobre las relaciones de un tipo de cliente"""
    try:
        tipo_cliente = get_object_or_404(TipoCliente, pk=pk)
        
        # Contar clientes asociados
        clientes_count = tipo_cliente.cliente_set.count()
        
        relations_info = []
        if clientes_count > 0:
            relations_info.append(f"Este tipo de cliente tiene {clientes_count} cliente{'s' if clientes_count != 1 else ''} asociado{'s' if clientes_count != 1 else ''}")
        
        return JsonResponse({
            'success': True,
            'relations': relations_info,
            'has_relations': len(relations_info) > 0
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error al obtener relaciones: {str(e)}'
        })

@login_required
@permission_required('clientes.change_cliente', raise_exception=True)
@require_http_methods(["POST"])
def toggle_cliente_status(request, pk):
    """Vista AJAX para cambiar el estado activo/inactivo de un cliente"""
    try:
        cliente = get_object_or_404(Cliente, pk=pk)
        
        cliente.activo = not cliente.activo
        cliente.save()
        
        status_text = "activado" if cliente.activo else "desactivado"
        return JsonResponse({
            'success': True,
            'message': f'Cliente {status_text} exitosamente.',
            'nueva_estado': cliente.activo
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error al cambiar el estado: {str(e)}'
        })


@login_required
@permission_required('clientes.change_tipocliente', raise_exception=True)
@require_http_methods(["POST"])
def toggle_tipocliente_status(request, pk):
    """Vista AJAX para cambiar el estado activo/inactivo de un tipo de cliente"""
    try:
        tipo_cliente = get_object_or_404(TipoCliente, pk=pk)
        
        tipo_cliente.activo = not tipo_cliente.activo
        tipo_cliente.save()
        
        status_text = "activado" if tipo_cliente.activo else "desactivado"
        return JsonResponse({
            'success': True,
            'message': f'Tipo de cliente {status_text} exitosamente.',
            'nueva_estado': tipo_cliente.activo
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error al cambiar el estado: {str(e)}'
        })
