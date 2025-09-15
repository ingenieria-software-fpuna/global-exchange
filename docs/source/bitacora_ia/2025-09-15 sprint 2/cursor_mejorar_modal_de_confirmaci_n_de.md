# Mejorar modal de confirmación de desactivación
_Exported on 9/4/2025 at 19:58:36 GMT-3 from Cursor (1.5.5)_

---

**User**

Cuando se va a inactivar un Usuario, Grupo, Tipo Cliente, Cliente o Moneda aparece un modal de confirmación de desactivacion. Quiero que en ese modal se muestre si lo que sea que se va desactivar tiene cosas asociadas.

Por ejemplo: Si un Grupo tiene usuarios asociados que se muestre un mensaje como "Este grupo tiene X usuarios asociados". Lo mismo para los Tipo Clientes que tienen clientes asociados, Usuarios y Clientes que tambien pueden asociarse entre si.

---

**Cursor**

Entiendo que quieres mostrar información sobre las relaciones asociadas cuando se va a desactivar un elemento. Voy a analizar el código actual para entender cómo están implementados los modales de confirmación y las relaciones entre modelos.


Ahora voy a buscar los modales de confirmación actuales para entender cómo están implementados:


Ahora voy a buscar las vistas que manejan el toggle de estado para entender mejor la implementación:


Ahora voy a buscar si hay alguna relación con tasas de cambio para las monedas:


Perfecto, ahora entiendo la estructura. Basándome en el análisis, he identificado las siguientes relaciones:

1. **Grupo** → **Usuario** (relación many-to-many a través de Django Group)
2. **TipoCliente** → **Cliente** (relación one-to-many)
3. **Cliente** → **Usuario** (relación many-to-many)
4. **Moneda** → **TasaCambio** (relación one-to-many)

Ahora voy a implementar la funcionalidad. Primero, voy a crear nuevas vistas API que devuelvan información sobre las relaciones asociadas:


```python
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from .forms import UsuarioCreationForm, UsuarioUpdateForm

Usuario = get_user_model()

# Vista para listar usuarios
class UsuarioListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Usuario
    template_name = 'usuarios/user_list.html'
    context_object_name = 'usuarios'
    permission_required = 'usuarios.view_usuario'
    paginate_by = 20

# Vista para crear un nuevo usuario
class UsuarioCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Usuario
    form_class = UsuarioCreationForm
    template_name = 'usuarios/user_form.html'
    success_url = reverse_lazy('usuarios:user_list')
    permission_required = 'usuarios.add_usuario'

    def form_valid(self, form):
        messages.success(self.request, "Usuario creado exitosamente.")
        return super().form_valid(form)

# Vista para actualizar un usuario
class UsuarioUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Usuario
    form_class = UsuarioUpdateForm
    template_name = 'usuarios/user_form.html'
    success_url = reverse_lazy('usuarios:user_list')
    permission_required = 'usuarios.change_usuario'

    def form_valid(self, form):
        messages.success(self.request, "Usuario actualizado exitosamente.")
        return super().form_valid(form)




@login_required
@permission_required('usuarios.view_usuario', raise_exception=True)
def get_usuario_relations(request, pk):
    """API para obtener información sobre las relaciones de un usuario"""
    try:
        usuario = get_object_or_404(Usuario, pk=pk)
        
        # Contar clientes asociados
        clientes_count = usuario.cliente_set.count()
        
        relations_info = []
        if clientes_count > 0:
            relations_info.append(f"Este usuario tiene {clientes_count} cliente{'s' if clientes_count != 1 else ''} asociado{'s' if clientes_count != 1 else ''}")
        
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
@permission_required('usuarios.change_usuario', raise_exception=True)
@require_http_methods(["POST"])
def toggle_usuario_status(request, pk):
    """Vista AJAX para cambiar el estado activo/inactivo de un usuario"""
    try:
        usuario = get_object_or_404(Usuario, pk=pk)
        
        usuario.es_activo = not usuario.es_activo
        usuario.save()
        
        status_text = "activado" if usuario.es_activo else "desactivado"
        return JsonResponse({
            'success': True,
            'message': f'Usuario {status_text} exitosamente.',
            'nueva_estado': usuario.es_activo
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error al cambiar el estado: {str(e)}'
        })
```

```python
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import Group, Permission
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.views.generic import ListView, CreateView, UpdateView
from django.urls import reverse_lazy
from django.db.models import Q
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .models import Grupo

# Vista para listar grupos
class GroupListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Grupo
    template_name = 'grupos/group_list.html'
    context_object_name = 'groups'
    permission_required = 'auth.view_group'
    paginate_by = 20

    def get_queryset(self):
        queryset = Grupo.objects.select_related('group').prefetch_related('group__permissions')
        
        # Filtro de búsqueda
        q = self.request.GET.get('q')
        if q:
            queryset = queryset.filter(
                Q(group__name__icontains=q) |
                Q(group__permissions__name__icontains=q)
            ).distinct()
        
        # Filtro por estado
        estado = self.request.GET.get('estado')
        if estado == 'activo':
            queryset = queryset.filter(es_activo=True)
        elif estado == 'inactivo':
            queryset = queryset.filter(es_activo=False)
        
        return queryset.order_by('group__name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['q'] = self.request.GET.get('q', '')
        context['estado_filter'] = self.request.GET.get('estado', '')
        return context

# Vista para crear grupo
class GroupCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Grupo
    template_name = 'grupos/group_form.html'
    fields = ['es_activo']
    success_url = reverse_lazy('grupos:group_list')
    permission_required = 'auth.add_group'

    def form_valid(self, form):
        # Crear el grupo de Django primero
        group_name = self.request.POST.get('name')
        if not group_name:
            messages.error(self.request, "El nombre del grupo es requerido.")
            return self.form_invalid(form)
        
        django_group = Group.objects.create(name=group_name)
        form.instance.group = django_group
        messages.success(self.request, "Grupo creado exitosamente.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Crear Nuevo Grupo'
        return context

# Vista para editar grupo
class GroupUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Grupo
    template_name = 'grupos/group_form.html'
    fields = ['es_activo']
    success_url = reverse_lazy('grupos:group_list')
    permission_required = 'auth.change_group'

    def form_valid(self, form):
        # Actualizar el nombre del grupo de Django si se proporciona
        group_name = self.request.POST.get('name')
        if group_name and group_name != self.object.group.name:
            self.object.group.name = group_name
            self.object.group.save()
        
        messages.success(self.request, "Grupo actualizado exitosamente.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = f'Editar Grupo: {self.object.group.name}'
        return context



# Vista para gestionar permisos de un grupo
class GroupPermissionsView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Grupo
    template_name = 'grupos/group_permissions.html'
    fields = []
    permission_required = 'auth.change_group'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        grupo = self.get_object()
        group = grupo.group  # El grupo de Django
        
        # Obtener todos los permisos agrupados por app
        permissions = Permission.objects.all().select_related('content_type')
        permissions_by_app = {}
        
        for perm in permissions:
            app_label = perm.content_type.app_label
            if app_label not in permissions_by_app:
                permissions_by_app[app_label] = []
            permissions_by_app[app_label].append(perm)
        
        context['permissions_by_app'] = permissions_by_app
        context['group_permissions'] = group.permissions.all()
        context['titulo'] = f'Permisos del Grupo: {group.name}'
        return context
    
    def post(self, request, *args, **kwargs):
        grupo = self.get_object()
        group = grupo.group  # El grupo de Django
        permission_ids = request.POST.getlist('permissions')
        
        # Actualizar permisos del grupo
        permissions = Permission.objects.filter(id__in=permission_ids)
        group.permissions.set(permissions)
        
        messages.success(request, f"Permisos del grupo '{group.name}' actualizados exitosamente.")
        return redirect('grupos:group_list')

# Vista para listar permisos
class PermissionListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Permission
    template_name = 'grupos/permission_list.html'
    context_object_name = 'permissions'
    permission_required = 'auth.view_permission'
    paginate_by = 50

    def get_queryset(self):
        return Permission.objects.all().select_related('content_type').order_by('content_type__app_label', 'content_type__model', 'codename')


@login_required
@permission_required('auth.view_group', raise_exception=True)
def get_group_relations(request, pk):
    """API para obtener información sobre las relaciones de un grupo"""
    try:
        grupo = get_object_or_404(Grupo, pk=pk)
        
        # Contar usuarios asociados
        usuarios_count = grupo.group.user_set.count()
        
        relations_info = []
        if usuarios_count > 0:
            relations_info.append(f"Este grupo tiene {usuarios_count} usuario{'s' if usuarios_count != 1 else ''} asociado{'s' if usuarios_count != 1 else ''}")
        
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
@permission_required('auth.change_group', raise_exception=True)
@require_http_methods(["POST"])
def toggle_group_status(request, pk):
    """Vista AJAX para cambiar el estado activo/inactivo de un grupo"""
    try:
        grupo = get_object_or_404(Grupo, pk=pk)
        
        grupo.es_activo = not grupo.es_activo
        grupo.save()
        
        status_text = "activado" if grupo.es_activo else "desactivado"
        return JsonResponse({
            'success': True,
            'message': f'Grupo {status_text} exitosamente.',
            'nueva_estado': grupo.es_activo
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error al cambiar el estado: {str(e)}'
        })

```

```python
from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.decorators import login_required, permission_required
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .models import TipoCliente, Cliente

# Create your views here.

class TipoClienteListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = TipoCliente
    template_name = 'clientes/tipocliente_list.html'
    context_object_name = 'tipos_cliente'
    paginate_by = 10
    permission_required = 'clientes.view_tipocliente'

class TipoClienteCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = TipoCliente
    template_name = 'clientes/tipocliente_form.html'
    fields = ['nombre', 'descripcion', 'descuento', 'activo']
    success_url = reverse_lazy('clientes:tipocliente_list')
    permission_required = 'clientes.add_tipocliente'
    
    def form_valid(self, form):
        messages.success(self.request, 'Tipo de cliente creado exitosamente.')
        return super().form_valid(form)

class TipoClienteUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = TipoCliente
    template_name = 'clientes/tipocliente_form.html'
    fields = ['nombre', 'descripcion', 'descuento', 'activo']
    success_url = reverse_lazy('clientes:tipocliente_list')
    permission_required = 'clientes.change_tipocliente'
    
    def form_valid(self, form):
        messages.success(self.request, 'Tipo de cliente actualizado exitosamente.')
        return super().form_valid(form)



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
        return context

class ClienteCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Cliente
    template_name = 'clientes/cliente_form.html'
    fields = [
        'nombre_comercial', 'ruc', 'direccion', 'correo_electronico', 
        'numero_telefono', 'tipo_cliente', 'usuarios_asociados', 'activo'
    ]
    success_url = reverse_lazy('clientes:cliente_list')
    permission_required = 'clientes.add_cliente'
    
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

class ClienteUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Cliente
    template_name = 'clientes/cliente_form.html'
    fields = [
        'nombre_comercial', 'ruc', 'direccion', 'correo_electronico', 
        'numero_telefono', 'tipo_cliente', 'usuarios_asociados', 'activo'
    ]
    success_url = reverse_lazy('clientes:cliente_list')
    permission_required = 'clientes.change_cliente'
    
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

```

```python
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
@permission_required('monedas.view_moneda', raise_exception=True)
def get_moneda_relations(request, pk):
    """API para obtener información sobre las relaciones de una moneda"""
    try:
        moneda = get_object_or_404(Moneda, pk=pk)
        
        # Contar tasas de cambio asociadas
        tasas_count = moneda.tasas_cambio.count()
        
        relations_info = []
        if tasas_count > 0:
            relations_info.append(f"Esta moneda tiene {tasas_count} tasa{'s' if tasas_count != 1 else ''} de cambio asociada{'s' if tasas_count != 1 else ''}")
        
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

```

Ahora necesito agregar las nuevas rutas a los archivos URLs:


```python
from django.urls import path
from .views import UsuarioListView, UsuarioCreateView, UsuarioUpdateView, toggle_usuario_status, get_usuario_relations

app_name = 'usuarios' 
urlpatterns = [
    path('', UsuarioListView.as_view(), name='user_list'),
    path('usuarios/crear/', UsuarioCreateView.as_view(), name='user_create'),
    path('usuarios/editar/<int:pk>/', UsuarioUpdateView.as_view(), name='user_update'),
    
    # API AJAX para Usuarios
    path('usuarios/toggle-status/<int:pk>/', toggle_usuario_status, name='toggle_status'),
    path('usuarios/relations/<int:pk>/', get_usuario_relations, name='get_relations'),
]



```

```python
from django.urls import path
from .views import (
    GroupListView, GroupCreateView, GroupUpdateView,
    GroupPermissionsView, PermissionListView, toggle_group_status, get_group_relations
)

app_name = 'grupos'

urlpatterns = [
    # URLs para Grupos
    path('', GroupListView.as_view(), name='group_list'),
    path('crear/', GroupCreateView.as_view(), name='group_create'),
    path('editar/<int:pk>/', GroupUpdateView.as_view(), name='group_update'),
    path('permisos/<int:pk>/', GroupPermissionsView.as_view(), name='group_permissions'),
    
    # API AJAX para Grupos
    path('toggle-status/<int:pk>/', toggle_group_status, name='toggle_status'),
    path('relations/<int:pk>/', get_group_relations, name='get_relations'),
    
    # URLs para Permisos
    path('permisos/', PermissionListView.as_view(), name='permission_list'),
]

```

```python
from django.urls import path
from . import views

app_name = 'clientes'

urlpatterns = [
    # URLs para Tipos de Cliente
    path('tipos/', views.TipoClienteListView.as_view(), name='tipocliente_list'),
    path('tipos/crear/', views.TipoClienteCreateView.as_view(), name='tipocliente_create'),
    path('tipos/<int:pk>/editar/', views.TipoClienteUpdateView.as_view(), name='tipocliente_update'),
    
    # URLs para Clientes
    path('', views.ClienteListView.as_view(), name='cliente_list'),
    path('crear/', views.ClienteCreateView.as_view(), name='cliente_create'),
    path('<int:pk>/editar/', views.ClienteUpdateView.as_view(), name='cliente_update'),
    
    # API AJAX para Tipos de Cliente
    path('tipos/toggle-status/<int:pk>/', views.toggle_tipocliente_status, name='tipocliente_toggle_status'),
    path('tipos/relations/<int:pk>/', views.get_tipocliente_relations, name='tipocliente_get_relations'),
    
    # API AJAX para Clientes
    path('toggle-status/<int:pk>/', views.toggle_cliente_status, name='toggle_status'),
    path('relations/<int:pk>/', views.get_cliente_relations, name='get_relations'),
]

```

```python
from django.urls import path
from .views import (
    MonedaListView, MonedaCreateView, MonedaUpdateView,
    toggle_moneda_status, moneda_detail_api, dashboard_monedas, get_moneda_relations
)

app_name = 'monedas'

urlpatterns = [
    # Dashboard
    path('dashboard/', dashboard_monedas, name='dashboard'),
    
    # CRUD de monedas
    path('', MonedaListView.as_view(), name='moneda_list'),
    path('crear/', MonedaCreateView.as_view(), name='moneda_create'),
    path('editar/<int:pk>/', MonedaUpdateView.as_view(), name='moneda_update'),
    
    # APIs AJAX
    path('toggle-status/<int:pk>/', toggle_moneda_status, name='toggle_status'),
    path('api/detalle/<int:pk>/', moneda_detail_api, name='moneda_detail_api'),
    path('relations/<int:pk>/', get_moneda_relations, name='get_relations'),
]

```

Ahora voy a actualizar los modales para mostrar la información de relaciones. Empezaré con el modal de usuarios:


```django-html
{% extends "base.html" %}
{% load static %}

{% block title %}Usuarios - Global Exchange{% endblock %}

{% block content %}
<div class="container mt-4">
    <!-- Breadcrumbs -->
    <nav aria-label="breadcrumb" class="mb-4">
        <ol class="breadcrumb">
            <li class="breadcrumb-item">
                <a href="{% url 'auth:dashboard' %}">
                    <i class="fas fa-home me-1"></i>Dashboard
                </a>
            </li>
            <li class="breadcrumb-item active" aria-current="page">
                <i class="fas fa-users me-1"></i>Usuarios
            </li>
        </ol>
    </nav>

    <div class="row">
        <div class="col-12">
            <div class="d-flex justify-content-between align-items-center mb-4">
                <h1 class="h2">
                    <i class="fas fa-users text-primary me-2"></i>
                    Usuarios
                </h1>
                {% if can_create_usuarios %}
                <a href="{% url 'usuarios:user_create' %}" class="btn btn-primary">
                    <i class="fas fa-plus me-2"></i>Crear Nuevo Usuario
                </a>
                {% endif %}
            </div>

            {% if usuarios %}
            <div class="card shadow-sm">
                <div class="card-body">
                    <div class="table-responsive">
                        <table class="table table-hover">
                            <thead class="table-light">
                                <tr>
                                    <th>Email</th>
                                    <th>Nombre Completo</th>
                                    <th>Cédula</th>
                                    <th>Estado</th>
                                    <th>Fecha Nacimiento</th>
                                    <th class="text-center">Acciones</th>
                                </tr>
                            </thead>
                            <tbody>
                                {% for usuario in usuarios %}
                                <tr>
                                    <td>
                                        <strong>{{ usuario.email }}</strong>
                                    </td>
                                    <td>
                                        {{ usuario.nombre }} {{ usuario.apellido }}
                                    </td>
                                    <td>
                                        {% if usuario.cedula %}
                                            <code>{{ usuario.cedula }}</code>
                                        {% else %}
                                            <span class="text-muted">Sin cédula</span>
                                        {% endif %}
                                    </td>
                                    <td>
                                        {% if usuario.es_activo %}
                                            <span class="badge bg-success">
                                                <i class="fas fa-check me-1"></i>Activo
                                            </span>
                                        {% else %}
                                            <span class="badge bg-danger">
                                                <i class="fas fa-times me-1"></i>Inactivo
                                            </span>
                                        {% endif %}
                                    </td>
                                    <td>
                                        {% if usuario.fecha_nacimiento %}
                                            <small class="text-muted">
                                                {{ usuario.fecha_nacimiento|date:"d/m/Y" }}
                                            </small>
                                        {% else %}
                                            <span class="text-muted">Sin fecha</span>
                                        {% endif %}
                                    </td>
                                    <td class="text-center">
                                        <div class="btn-group" role="group">
                                            {% if can_edit_usuarios %}
                                            <a href="{% url 'usuarios:user_update' usuario.pk %}" 
                                               class="btn btn-sm btn-outline-primary" 
                                               title="Editar">
                                                <i class="fas fa-edit"></i>
                                            </a>
                                            {% endif %}
                                            {% if can_edit_usuarios %}
                                            <button type="button" 
                                                    class="btn btn-sm {% if usuario.es_activo %}btn-outline-warning{% else %}btn-outline-success{% endif %} toggle-status-btn" 
                                                    title="{% if usuario.es_activo %}Desactivar{% else %}Activar{% endif %}"
                                                    data-usuario-id="{{ usuario.pk }}"
                                                    data-current-status="{% if usuario.es_activo %}true{% else %}false{% endif %}">
                                                {% if usuario.es_activo %}
                                                    <i class="fas fa-eye-slash"></i>
                                                {% else %}
                                                    <i class="fas fa-eye"></i>
                                                {% endif %}
                                            </button>
                                            {% endif %}
                                        </div>
                                    </td>
                                </tr>
                                {% endfor %}
                            </tbody>
                        </table>
                    </div>

                    {% if is_paginated %}
                    <nav aria-label="Navegación de páginas" class="mt-4">
                        <ul class="pagination justify-content-center">
                            {% if page_obj.has_previous %}
                                <li class="page-item">
                                    <a class="page-link" href="?page=1">
                                        <i class="fas fa-angle-double-left"></i>
                                    </a>
                                </li>
                                <li class="page-item">
                                    <a class="page-link" href="?page={{ page_obj.previous_page_number }}">
                                        <i class="fas fa-angle-left"></i>
                                    </a>
                                </li>
                            {% endif %}

                            <li class="page-item active">
                                <span class="page-link">
                                    Página {{ page_obj.number }} de {{ page_obj.paginator.num_pages }}
                                </span>
                            </li>

                            {% if page_obj.has_next %}
                                <li class="page-item">
                                    <a class="page-link" href="?page={{ page_obj.next_page_number }}">
                                        <i class="fas fa-angle-right"></i>
                                    </a>
                                </li>
                                <li class="page-item">
                                    <a class="page-link" href="?page={{ page_obj.paginator.num_pages }}">
                                        <i class="fas fa-angle-double-right"></i>
                                    </a>
                                </li>
                            {% endif %}
                        </ul>
                    </nav>
                    {% endif %}
                </div>
            </div>
            {% else %}
            <div class="card shadow-sm">
                <div class="card-body text-center py-5">
                    <i class="fas fa-users fa-3x text-muted mb-3"></i>
                    <h4 class="text-muted">No hay usuarios registrados</h4>
                    <p class="text-muted">Comienza creando el primer usuario para organizar tu sistema.</p>
                    {% if can_create_usuarios %}
                    <a href="{% url 'usuarios:user_create' %}" class="btn btn-primary">
                        <i class="fas fa-plus me-2"></i>Crear Primer Usuario
                    </a>
                    {% endif %}
                </div>
            </div>
            {% endif %}
        </div>
    </div>
</div>

<!-- Modal para confirmación de cambio de estado -->
<div class="modal fade" id="statusModal" tabindex="-1">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">Confirmar Cambio de Estado</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body">
                <p id="statusMessage"></p>
                <div id="relationsInfo" class="mt-3" style="display: none;">
                    <div class="alert alert-warning">
                        <h6><i class="fas fa-exclamation-triangle me-2"></i>Relaciones Asociadas:</h6>
                        <ul id="relationsList" class="mb-0"></ul>
                    </div>
                </div>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancelar</button>
                <button type="button" class="btn btn-primary" id="confirmStatusChange">Confirmar</button>
            </div>
        </div>
    </div>
</div>

<script>
let currentUsuarioId = null;
let currentAction = null;

// Event listener para los botones de toggle status
document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.toggle-status-btn').forEach(function(button) {
        button.addEventListener('click', function() {
            const usuarioId = this.getAttribute('data-usuario-id');
            const currentStatus = this.getAttribute('data-current-status');
            const newStatus = currentStatus === 'true' ? 'false' : 'true';
            
            toggleUsuarioStatus(usuarioId, newStatus);
        });
    });
});

function toggleUsuarioStatus(usuarioId, newStatus) {
    currentUsuarioId = usuarioId;
    currentAction = newStatus;
    
    const action = newStatus === 'true' ? 'activar' : 'desactivar';
    document.getElementById('statusMessage').textContent = 
        `¿Estás seguro de que quieres ${action} este usuario?`;
    
    const modal = new bootstrap.Modal(document.getElementById('statusModal'));
    modal.show();
}

document.getElementById('confirmStatusChange').addEventListener('click', function() {
    if (currentUsuarioId && currentAction) {
        fetch(`/usuarios/usuarios/toggle-status/${currentUsuarioId}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                'activo': currentAction === 'true'
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                location.reload();
            } else {
                alert('Error al cambiar el estado del usuario: ' + data.message);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error al cambiar el estado del usuario');
        });
        
        bootstrap.Modal.getInstance(document.getElementById('statusModal')).hide();
    }
});
</script>

{% csrf_token %}
{% endblock %}
```

```django-html
{% extends "base.html" %}
{% load static %}

{% block title %}Usuarios - Global Exchange{% endblock %}

{% block content %}
<div class="container mt-4">
    <!-- Breadcrumbs -->
    <nav aria-label="breadcrumb" class="mb-4">
        <ol class="breadcrumb">
            <li class="breadcrumb-item">
                <a href="{% url 'auth:dashboard' %}">
                    <i class="fas fa-home me-1"></i>Dashboard
                </a>
            </li>
            <li class="breadcrumb-item active" aria-current="page">
                <i class="fas fa-users me-1"></i>Usuarios
            </li>
        </ol>
    </nav>

    <div class="row">
        <div class="col-12">
            <div class="d-flex justify-content-between align-items-center mb-4">
                <h1 class="h2">
                    <i class="fas fa-users text-primary me-2"></i>
                    Usuarios
                </h1>
                {% if can_create_usuarios %}
                <a href="{% url 'usuarios:user_create' %}" class="btn btn-primary">
                    <i class="fas fa-plus me-2"></i>Crear Nuevo Usuario
                </a>
                {% endif %}
            </div>

            {% if usuarios %}
            <div class="card shadow-sm">
                <div class="card-body">
                    <div class="table-responsive">
                        <table class="table table-hover">
                            <thead class="table-light">
                                <tr>
                                    <th>Email</th>
                                    <th>Nombre Completo</th>
                                    <th>Cédula</th>
                                    <th>Estado</th>
                                    <th>Fecha Nacimiento</th>
                                    <th class="text-center">Acciones</th>
                                </tr>
                            </thead>
                            <tbody>
                                {% for usuario in usuarios %}
                                <tr>
                                    <td>
                                        <strong>{{ usuario.email }}</strong>
                                    </td>
                                    <td>
                                        {{ usuario.nombre }} {{ usuario.apellido }}
                                    </td>
                                    <td>
                                        {% if usuario.cedula %}
                                            <code>{{ usuario.cedula }}</code>
                                        {% else %}
                                            <span class="text-muted">Sin cédula</span>
                                        {% endif %}
                                    </td>
                                    <td>
                                        {% if usuario.es_activo %}
                                            <span class="badge bg-success">
                                                <i class="fas fa-check me-1"></i>Activo
                                            </span>
                                        {% else %}
                                            <span class="badge bg-danger">
                                                <i class="fas fa-times me-1"></i>Inactivo
                                            </span>
                                        {% endif %}
                                    </td>
                                    <td>
                                        {% if usuario.fecha_nacimiento %}
                                            <small class="text-muted">
                                                {{ usuario.fecha_nacimiento|date:"d/m/Y" }}
                                            </small>
                                        {% else %}
                                            <span class="text-muted">Sin fecha</span>
                                        {% endif %}
                                    </td>
                                    <td class="text-center">
                                        <div class="btn-group" role="group">
                                            {% if can_edit_usuarios %}
                                            <a href="{% url 'usuarios:user_update' usuario.pk %}" 
                                               class="btn btn-sm btn-outline-primary" 
                                               title="Editar">
                                                <i class="fas fa-edit"></i>
                                            </a>
                                            {% endif %}
                                            {% if can_edit_usuarios %}
                                            <button type="button" 
                                                    class="btn btn-sm {% if usuario.es_activo %}btn-outline-warning{% else %}btn-outline-success{% endif %} toggle-status-btn" 
                                                    title="{% if usuario.es_activo %}Desactivar{% else %}Activar{% endif %}"
                                                    data-usuario-id="{{ usuario.pk }}"
                                                    data-current-status="{% if usuario.es_activo %}true{% else %}false{% endif %}">
                                                {% if usuario.es_activo %}
                                                    <i class="fas fa-eye-slash"></i>
                                                {% else %}
                                                    <i class="fas fa-eye"></i>
                                                {% endif %}
                                            </button>
                                            {% endif %}
                                        </div>
                                    </td>
                                </tr>
                                {% endfor %}
                            </tbody>
                        </table>
                    </div>

                    {% if is_paginated %}
                    <nav aria-label="Navegación de páginas" class="mt-4">
                        <ul class="pagination justify-content-center">
                            {% if page_obj.has_previous %}
                                <li class="page-item">
                                    <a class="page-link" href="?page=1">
                                        <i class="fas fa-angle-double-left"></i>
                                    </a>
                                </li>
                                <li class="page-item">
                                    <a class="page-link" href="?page={{ page_obj.previous_page_number }}">
                                        <i class="fas fa-angle-left"></i>
                                    </a>
                                </li>
                            {% endif %}

                            <li class="page-item active">
                                <span class="page-link">
                                    Página {{ page_obj.number }} de {{ page_obj.paginator.num_pages }}
                                </span>
                            </li>

                            {% if page_obj.has_next %}
                                <li class="page-item">
                                    <a class="page-link" href="?page={{ page_obj.next_page_number }}">
                                        <i class="fas fa-angle-right"></i>
                                    </a>
                                </li>
                                <li class="page-item">
                                    <a class="page-link" href="?page={{ page_obj.paginator.num_pages }}">
                                        <i class="fas fa-angle-double-right"></i>
                                    </a>
                                </li>
                            {% endif %}
                        </ul>
                    </nav>
                    {% endif %}
                </div>
            </div>
            {% else %}
            <div class="card shadow-sm">
                <div class="card-body text-center py-5">
                    <i class="fas fa-users fa-3x text-muted mb-3"></i>
                    <h4 class="text-muted">No hay usuarios registrados</h4>
                    <p class="text-muted">Comienza creando el primer usuario para organizar tu sistema.</p>
                    {% if can_create_usuarios %}
                    <a href="{% url 'usuarios:user_create' %}" class="btn btn-primary">
                        <i class="fas fa-plus me-2"></i>Crear Primer Usuario
                    </a>
                    {% endif %}
                </div>
            </div>
            {% endif %}
        </div>
    </div>
</div>

<!-- Modal para confirmación de cambio de estado -->
<div class="modal fade" id="statusModal" tabindex="-1">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">Confirmar Cambio de Estado</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body">
                <p id="statusMessage"></p>
                <div id="relationsInfo" class="mt-3" style="display: none;">
                    <div class="alert alert-warning">
                        <h6><i class="fas fa-exclamation-triangle me-2"></i>Relaciones Asociadas:</h6>
                        <ul id="relationsList" class="mb-0"></ul>
                    </div>
                </div>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancelar</button>
                <button type="button" class="btn btn-primary" id="confirmStatusChange">Confirmar</button>
            </div>
        </div>
    </div>
</div>

<script>
let currentUsuarioId = null;
let currentAction = null;

// Event listener para los botones de toggle status
document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.toggle-status-btn').forEach(function(button) {
        button.addEventListener('click', function() {
            const usuarioId = this.getAttribute('data-usuario-id');
            const currentStatus = this.getAttribute('data-current-status');
            const newStatus = currentStatus === 'true' ? 'false' : 'true';
            
            toggleUsuarioStatus(usuarioId, newStatus);
        });
    });
});

function toggleUsuarioStatus(usuarioId, newStatus) {
    currentUsuarioId = usuarioId;
    currentAction = newStatus;
    
    const action = newStatus === 'true' ? 'activar' : 'desactivar';
    document.getElementById('statusMessage').textContent = 
        `¿Estás seguro de que quieres ${action} este usuario?`;
    
    // Ocultar información de relaciones inicialmente
    document.getElementById('relationsInfo').style.display = 'none';
    
    // Solo mostrar relaciones si se va a desactivar
    if (newStatus === 'false') {
        fetch(`/usuarios/usuarios/relations/${usuarioId}/`)
            .then(response => response.json())
            .then(data => {
                if (data.success && data.has_relations) {
                    const relationsList = document.getElementById('relationsList');
                    relationsList.innerHTML = '';
                    data.relations.forEach(relation => {
                        const li = document.createElement('li');
                        li.textContent = relation;
                        relationsList.appendChild(li);
                    });
                    document.getElementById('relationsInfo').style.display = 'block';
                }
            })
            .catch(error => {
                console.error('Error al obtener relaciones:', error);
            });
    }
    
    const modal = new bootstrap.Modal(document.getElementById('statusModal'));
    modal.show();
}

document.getElementById('confirmStatusChange').addEventListener('click', function() {
    if (currentUsuarioId && currentAction) {
        fetch(`/usuarios/usuarios/toggle-status/${currentUsuarioId}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                'activo': currentAction === 'true'
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                location.reload();
            } else {
                alert('Error al cambiar el estado del usuario: ' + data.message);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error al cambiar el estado del usuario');
        });
        
        bootstrap.Modal.getInstance(document.getElementById('statusModal')).hide();
    }
});
</script>

{% csrf_token %}
{% endblock %}
```

Ahora voy a actualizar el modal de grupos:


```django-html
{% extends 'base.html' %}
{% load static %}

{% block title %}Gestión de Grupos{% endblock %}

{% block content %}
<div class="container-fluid">
    <!-- Breadcrumbs -->
    <nav aria-label="breadcrumb" class="mb-4">
        <ol class="breadcrumb">
            <li class="breadcrumb-item">
                <a href="{% url 'auth:dashboard' %}">
                    <i class="fas fa-home me-1"></i>Dashboard
                </a>
            </li>
            <li class="breadcrumb-item active" aria-current="page">
                <i class="fas fa-layer-group me-1"></i>Grupos
            </li>
        </ol>
    </nav>

    <div class="d-flex justify-content-between align-items-center mb-4">
        <h1 class="h3 mb-0 text-gray-800">
            <i class="fas fa-layer-group"></i> Gestión de Grupos
        </h1>
        {% if perms.auth.add_group %}
        <a href="{% url 'grupos:group_create' %}" class="btn btn-primary">
            <i class="fas fa-plus"></i> Nuevo Grupo
        </a>
        {% endif %}
    </div>

    <!-- Filtros y búsqueda -->
    <div class="card shadow mb-4">
        <div class="card-body">
            <form method="get" class="row g-3">
                <div class="col-md-4">
                    <label for="q" class="form-label">Buscar</label>
                    <input type="text" class="form-control" id="q" name="q" 
                           value="{{ q }}" placeholder="Nombre del grupo o permisos...">
                </div>
                <div class="col-md-3">
                    <label for="estado" class="form-label">Estado</label>
                    <select class="form-select" id="estado" name="estado">
                        <option value="">Todos los estados</option>
                        <option value="activo" {% if estado_filter == 'activo' %}selected{% endif %}>Activo</option>
                        <option value="inactivo" {% if estado_filter == 'inactivo' %}selected{% endif %}>Inactivo</option>
                    </select>
                </div>
                <div class="col-md-3 d-flex align-items-end">
                    <button type="submit" class="btn btn-primary w-100">
                        <i class="fas fa-search me-1"></i>Filtrar
                    </button>
                </div>
                <div class="col-md-2 d-flex align-items-end">
                    <a href="{% url 'grupos:group_list' %}" class="btn btn-outline-secondary w-100">
                        <i class="fas fa-times me-1"></i>Limpiar
                    </a>
                </div>
            </form>
        </div>
    </div>

    <!-- Lista de grupos -->
    <div class="card shadow">
        <div class="card-header py-3">
            <h6 class="m-0 font-weight-bold text-primary">
                Grupos del Sistema ({{ groups|length }})
            </h6>
        </div>
        <div class="card-body">
            {% if groups %}
            <div class="table-responsive">
                <table class="table table-bordered table-hover">
                    <thead class="table-light">
                        <tr>
                            <th>Nombre</th>
                            <th>Permisos</th>
                            <th>Usuarios</th>
                            <th>Estado</th>
                            <th>Acciones</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for group in groups %}
                        <tr>
                            <td>
                                <strong>{{ group.name }}</strong>
                            </td>
                            <td>
                                <span class="badge bg-info">{{ group.permissions.count }}</span>
                                {% if group.permissions.count > 0 %}
                                <small class="text-muted d-block">
                                    {{ group.permissions.all|slice:":3"|join:", " }}
                                    {% if group.permissions.count > 3 %}...{% endif %}
                                </small>
                                {% endif %}
                            </td>
                            <td>
                                <span class="badge bg-secondary">{{ group.user_set.count }}</span>
                            </td>
                            <td>
                                {% if group.es_activo %}
                                    <span class="badge bg-success">
                                        <i class="fas fa-check me-1"></i>Activo
                                    </span>
                                {% else %}
                                    <span class="badge bg-danger">
                                        <i class="fas fa-times me-1"></i>Inactivo
                                    </span>
                                {% endif %}
                            </td>
                            <td>
                                <div class="btn-group" role="group">
                                    {% if perms.auth.view_group %}
                                    <a href="{% url 'grupos:group_permissions' group.pk %}" 
                                       class="btn btn-sm btn-outline-primary" title="Gestionar Permisos">
                                        <i class="fas fa-key"></i>
                                    </a>
                                    {% endif %}
                                    {% if perms.auth.change_group %}
                                    <a href="{% url 'grupos:group_update' group.pk %}" 
                                       class="btn btn-sm btn-outline-warning" title="Editar">
                                        <i class="fas fa-edit"></i>
                                    </a>
                                    {% endif %}
                                    {% if perms.auth.change_group %}
                                    <button type="button" 
                                            class="btn btn-sm {% if group.es_activo %}btn-outline-warning{% else %}btn-outline-success{% endif %} toggle-status-btn" 
                                            title="{% if group.es_activo %}Desactivar{% else %}Activar{% endif %}"
                                            data-group-id="{{ group.pk }}"
                                            data-current-status="{% if group.es_activo %}true{% else %}false{% endif %}">
                                        {% if group.es_activo %}
                                            <i class="fas fa-eye-slash"></i>
                                        {% else %}
                                            <i class="fas fa-eye"></i>
                                        {% endif %}
                                    </button>
                                    {% endif %}
                                </div>
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>

            <!-- Paginación -->
            {% if is_paginated %}
            <nav aria-label="Paginación de grupos">
                <ul class="pagination justify-content-center">
                    {% if page_obj.has_previous %}
                    <li class="page-item">
                        <a class="page-link" href="?page=1{% if request.GET.q %}&q={{ request.GET.q }}{% endif %}">
                            <i class="fas fa-angle-double-left"></i>
                        </a>
                    </li>
                    <li class="page-item">
                        <a class="page-link" href="?page={{ page_obj.previous_page_number }}{% if request.GET.q %}&q={{ request.GET.q }}{% endif %}">
                            <i class="fas fa-angle-left"></i>
                        </a>
                    </li>
                    {% endif %}

                    <li class="page-item active">
                        <span class="page-link">
                            Página {{ page_obj.number }} de {{ page_obj.paginator.num_pages }}
                        </span>
                    </li>

                    {% if page_obj.has_next %}
                    <li class="page-item">
                        <a class="page-link" href="?page={{ page_obj.next_page_number }}{% if request.GET.q %}&q={{ request.GET.q }}{% endif %}">
                            <i class="fas fa-angle-right"></i>
                        </a>
                    </li>
                    <li class="page-item">
                        <a class="page-link" href="?page={{ page_obj.paginator.num_pages }}{% if request.GET.q %}&q={{ request.GET.q }}{% endif %}">
                            <i class="fas fa-angle-double-right"></i>
                        </a>
                    </li>
                    {% endif %}
                </ul>
            </nav>
            {% endif %}

            {% else %}
            <div class="text-center py-4">
                <i class="fas fa-layer-group fa-3x text-muted mb-3"></i>
                <h5 class="text-muted">No hay grupos creados</h5>
                <p class="text-muted">Crea el primer grupo para comenzar a gestionar permisos.</p>
                {% if perms.auth.add_group %}
                <a href="{% url 'grupos:group_create' %}" class="btn btn-primary">
                    <i class="fas fa-plus"></i> Crear Primer Grupo
                </a>
                {% endif %}
            </div>
            {% endif %}
        </div>
    </div>
</div>

<!-- Modal para confirmación de cambio de estado -->
<div class="modal fade" id="statusModal" tabindex="-1">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">Confirmar Cambio de Estado</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body">
                <p id="statusMessage"></p>
                <div id="relationsInfo" class="mt-3" style="display: none;">
                    <div class="alert alert-warning">
                        <h6><i class="fas fa-exclamation-triangle me-2"></i>Relaciones Asociadas:</h6>
                        <ul id="relationsList" class="mb-0"></ul>
                    </div>
                </div>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancelar</button>
                <button type="button" class="btn btn-primary" id="confirmStatusChange">Confirmar</button>
            </div>
        </div>
    </div>
</div>

<script>
let currentGroupId = null;
let currentAction = null;

// Event listener para los botones de toggle status
document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.toggle-status-btn').forEach(function(button) {
        button.addEventListener('click', function() {
            const groupId = this.getAttribute('data-group-id');
            const currentStatus = this.getAttribute('data-current-status');
            const newStatus = currentStatus === 'true' ? 'false' : 'true';
            
            toggleGroupStatus(groupId, newStatus);
        });
    });
});

function toggleGroupStatus(groupId, newStatus) {
    currentGroupId = groupId;
    currentAction = newStatus;
    
    const action = newStatus === 'true' ? 'activar' : 'desactivar';
    document.getElementById('statusMessage').textContent = 
        `¿Estás seguro de que quieres ${action} este grupo?`;
    
    const modal = new bootstrap.Modal(document.getElementById('statusModal'));
    modal.show();
}

document.getElementById('confirmStatusChange').addEventListener('click', function() {
    if (currentGroupId && currentAction !== null) {
        fetch(`/grupos/toggle-status/${currentGroupId}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                'es_activo': currentAction === 'true'
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                location.reload();
            } else {
                alert('Error al cambiar el estado del grupo: ' + data.message);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error al cambiar el estado del grupo');
        });
        
        bootstrap.Modal.getInstance(document.getElementById('statusModal')).hide();
    }
});
</script>

{% csrf_token %}
{% endblock %}

```

```django-html
{% extends 'base.html' %}
{% load static %}

{% block title %}Gestión de Grupos{% endblock %}

{% block content %}
<div class="container-fluid">
    <!-- Breadcrumbs -->
    <nav aria-label="breadcrumb" class="mb-4">
        <ol class="breadcrumb">
            <li class="breadcrumb-item">
                <a href="{% url 'auth:dashboard' %}">
                    <i class="fas fa-home me-1"></i>Dashboard
                </a>
            </li>
            <li class="breadcrumb-item active" aria-current="page">
                <i class="fas fa-layer-group me-1"></i>Grupos
            </li>
        </ol>
    </nav>

    <div class="d-flex justify-content-between align-items-center mb-4">
        <h1 class="h3 mb-0 text-gray-800">
            <i class="fas fa-layer-group"></i> Gestión de Grupos
        </h1>
        {% if perms.auth.add_group %}
        <a href="{% url 'grupos:group_create' %}" class="btn btn-primary">
            <i class="fas fa-plus"></i> Nuevo Grupo
        </a>
        {% endif %}
    </div>

    <!-- Filtros y búsqueda -->
    <div class="card shadow mb-4">
        <div class="card-body">
            <form method="get" class="row g-3">
                <div class="col-md-4">
                    <label for="q" class="form-label">Buscar</label>
                    <input type="text" class="form-control" id="q" name="q" 
                           value="{{ q }}" placeholder="Nombre del grupo o permisos...">
                </div>
                <div class="col-md-3">
                    <label for="estado" class="form-label">Estado</label>
                    <select class="form-select" id="estado" name="estado">
                        <option value="">Todos los estados</option>
                        <option value="activo" {% if estado_filter == 'activo' %}selected{% endif %}>Activo</option>
                        <option value="inactivo" {% if estado_filter == 'inactivo' %}selected{% endif %}>Inactivo</option>
                    </select>
                </div>
                <div class="col-md-3 d-flex align-items-end">
                    <button type="submit" class="btn btn-primary w-100">
                        <i class="fas fa-search me-1"></i>Filtrar
                    </button>
                </div>
                <div class="col-md-2 d-flex align-items-end">
                    <a href="{% url 'grupos:group_list' %}" class="btn btn-outline-secondary w-100">
                        <i class="fas fa-times me-1"></i>Limpiar
                    </a>
                </div>
            </form>
        </div>
    </div>

    <!-- Lista de grupos -->
    <div class="card shadow">
        <div class="card-header py-3">
            <h6 class="m-0 font-weight-bold text-primary">
                Grupos del Sistema ({{ groups|length }})
            </h6>
        </div>
        <div class="card-body">
            {% if groups %}
            <div class="table-responsive">
                <table class="table table-bordered table-hover">
                    <thead class="table-light">
                        <tr>
                            <th>Nombre</th>
                            <th>Permisos</th>
                            <th>Usuarios</th>
                            <th>Estado</th>
                            <th>Acciones</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for group in groups %}
                        <tr>
                            <td>
                                <strong>{{ group.name }}</strong>
                            </td>
                            <td>
                                <span class="badge bg-info">{{ group.permissions.count }}</span>
                                {% if group.permissions.count > 0 %}
                                <small class="text-muted d-block">
                                    {{ group.permissions.all|slice:":3"|join:", " }}
                                    {% if group.permissions.count > 3 %}...{% endif %}
                                </small>
                                {% endif %}
                            </td>
                            <td>
                                <span class="badge bg-secondary">{{ group.user_set.count }}</span>
                            </td>
                            <td>
                                {% if group.es_activo %}
                                    <span class="badge bg-success">
                                        <i class="fas fa-check me-1"></i>Activo
                                    </span>
                                {% else %}
                                    <span class="badge bg-danger">
                                        <i class="fas fa-times me-1"></i>Inactivo
                                    </span>
                                {% endif %}
                            </td>
                            <td>
                                <div class="btn-group" role="group">
                                    {% if perms.auth.view_group %}
                                    <a href="{% url 'grupos:group_permissions' group.pk %}" 
                                       class="btn btn-sm btn-outline-primary" title="Gestionar Permisos">
                                        <i class="fas fa-key"></i>
                                    </a>
                                    {% endif %}
                                    {% if perms.auth.change_group %}
                                    <a href="{% url 'grupos:group_update' group.pk %}" 
                                       class="btn btn-sm btn-outline-warning" title="Editar">
                                        <i class="fas fa-edit"></i>
                                    </a>
                                    {% endif %}
                                    {% if perms.auth.change_group %}
                                    <button type="button" 
                                            class="btn btn-sm {% if group.es_activo %}btn-outline-warning{% else %}btn-outline-success{% endif %} toggle-status-btn" 
                                            title="{% if group.es_activo %}Desactivar{% else %}Activar{% endif %}"
                                            data-group-id="{{ group.pk }}"
                                            data-current-status="{% if group.es_activo %}true{% else %}false{% endif %}">
                                        {% if group.es_activo %}
                                            <i class="fas fa-eye-slash"></i>
                                        {% else %}
                                            <i class="fas fa-eye"></i>
                                        {% endif %}
                                    </button>
                                    {% endif %}
                                </div>
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>

            <!-- Paginación -->
            {% if is_paginated %}
            <nav aria-label="Paginación de grupos">
                <ul class="pagination justify-content-center">
                    {% if page_obj.has_previous %}
                    <li class="page-item">
                        <a class="page-link" href="?page=1{% if request.GET.q %}&q={{ request.GET.q }}{% endif %}">
                            <i class="fas fa-angle-double-left"></i>
                        </a>
                    </li>
                    <li class="page-item">
                        <a class="page-link" href="?page={{ page_obj.previous_page_number }}{% if request.GET.q %}&q={{ request.GET.q }}{% endif %}">
                            <i class="fas fa-angle-left"></i>
                        </a>
                    </li>
                    {% endif %}

                    <li class="page-item active">
                        <span class="page-link">
                            Página {{ page_obj.number }} de {{ page_obj.paginator.num_pages }}
                        </span>
                    </li>

                    {% if page_obj.has_next %}
                    <li class="page-item">
                        <a class="page-link" href="?page={{ page_obj.next_page_number }}{% if request.GET.q %}&q={{ request.GET.q }}{% endif %}">
                            <i class="fas fa-angle-right"></i>
                        </a>
                    </li>
                    <li class="page-item">
                        <a class="page-link" href="?page={{ page_obj.paginator.num_pages }}{% if request.GET.q %}&q={{ request.GET.q }}{% endif %}">
                            <i class="fas fa-angle-double-right"></i>
                        </a>
                    </li>
                    {% endif %}
                </ul>
            </nav>
            {% endif %}

            {% else %}
            <div class="text-center py-4">
                <i class="fas fa-layer-group fa-3x text-muted mb-3"></i>
                <h5 class="text-muted">No hay grupos creados</h5>
                <p class="text-muted">Crea el primer grupo para comenzar a gestionar permisos.</p>
                {% if perms.auth.add_group %}
                <a href="{% url 'grupos:group_create' %}" class="btn btn-primary">
                    <i class="fas fa-plus"></i> Crear Primer Grupo
                </a>
                {% endif %}
            </div>
            {% endif %}
        </div>
    </div>
</div>

<!-- Modal para confirmación de cambio de estado -->
<div class="modal fade" id="statusModal" tabindex="-1">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">Confirmar Cambio de Estado</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body">
                <p id="statusMessage"></p>
                <div id="relationsInfo" class="mt-3" style="display: none;">
                    <div class="alert alert-warning">
                        <h6><i class="fas fa-exclamation-triangle me-2"></i>Relaciones Asociadas:</h6>
                        <ul id="relationsList" class="mb-0"></ul>
                    </div>
                </div>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancelar</button>
                <button type="button" class="btn btn-primary" id="confirmStatusChange">Confirmar</button>
            </div>
        </div>
    </div>
</div>

<script>
let currentGroupId = null;
let currentAction = null;

// Event listener para los botones de toggle status
document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.toggle-status-btn').forEach(function(button) {
        button.addEventListener('click', function() {
            const groupId = this.getAttribute('data-group-id');
            const currentStatus = this.getAttribute('data-current-status');
            const newStatus = currentStatus === 'true' ? 'false' : 'true';
            
            toggleGroupStatus(groupId, newStatus);
        });
    });
});

function toggleGroupStatus(groupId, newStatus) {
    currentGroupId = groupId;
    currentAction = newStatus;
    
    const action = newStatus === 'true' ? 'activar' : 'desactivar';
    document.getElementById('statusMessage').textContent = 
        `¿Estás seguro de que quieres ${action} este grupo?`;
    
    // Ocultar información de relaciones inicialmente
    document.getElementById('relationsInfo').style.display = 'none';
    
    // Solo mostrar relaciones si se va a desactivar
    if (newStatus === 'false') {
        fetch(`/grupos/relations/${groupId}/`)
            .then(response => response.json())
            .then(data => {
                if (data.success && data.has_relations) {
                    const relationsList = document.getElementById('relationsList');
                    relationsList.innerHTML = '';
                    data.relations.forEach(relation => {
                        const li = document.createElement('li');
                        li.textContent = relation;
                        relationsList.appendChild(li);
                    });
                    document.getElementById('relationsInfo').style.display = 'block';
                }
            })
            .catch(error => {
                console.error('Error al obtener relaciones:', error);
            });
    }
    
    const modal = new bootstrap.Modal(document.getElementById('statusModal'));
    modal.show();
}

document.getElementById('confirmStatusChange').addEventListener('click', function() {
    if (currentGroupId && currentAction !== null) {
        fetch(`/grupos/toggle-status/${currentGroupId}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                'es_activo': currentAction === 'true'
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                location.reload();
            } else {
                alert('Error al cambiar el estado del grupo: ' + data.message);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error al cambiar el estado del grupo');
        });
        
        bootstrap.Modal.getInstance(document.getElementById('statusModal')).hide();
    }
});
</script>

{% csrf_token %}
{% endblock %}

```

Ahora voy a actualizar el modal de tipos de cliente:


```django-html
{% extends "base.html" %}
{% load static %}

{% block title %}Tipos de Cliente - Global Exchange{% endblock %}

{% block content %}
<div class="container mt-4">
    <!-- Breadcrumbs -->
    <nav aria-label="breadcrumb" class="mb-4">
        <ol class="breadcrumb">
            <li class="breadcrumb-item">
                <a href="{% url 'auth:dashboard' %}">
                    <i class="fas fa-home me-1"></i>Dashboard
                </a>
            </li>
            <li class="breadcrumb-item active" aria-current="page">
                <i class="fas fa-tags me-1"></i>Tipos de Cliente
            </li>
        </ol>
    </nav>

    <div class="row">
        <div class="col-12">
            <div class="d-flex justify-content-between align-items-center mb-4">
                <h1 class="h2">
                    <i class="fas fa-tags text-warning me-2"></i>
                    Tipos de Cliente
                </h1>
                {% if can_create_tipocliente %}
                <a href="{% url 'clientes:tipocliente_create' %}" class="btn btn-warning">
                    <i class="fas fa-plus me-2"></i>Crear Nuevo Tipo
                </a>
                {% endif %}
            </div>

            {% if tipos_cliente %}
            <div class="card shadow-sm">
                <div class="card-body">
                    <div class="table-responsive">
                        <table class="table table-hover">
                            <thead class="table-light">
                                <tr>
                                    <th>Nombre</th>
                                    <th>Descripción</th>
                                    <th>Descuento</th>
                                    <th>Estado</th>
                                    <th>Fecha Creación</th>
                                    <th class="text-center">Acciones</th>
                                </tr>
                            </thead>
                            <tbody>
                                {% for tipo in tipos_cliente %}
                                <tr>
                                    <td>
                                        <strong>{{ tipo.nombre }}</strong>
                                    </td>
                                    <td>
                                        {% if tipo.descripcion %}
                                            {{ tipo.descripcion|truncatewords:10 }}
                                        {% else %}
                                            <span class="text-muted">Sin descripción</span>
                                        {% endif %}
                                    </td>
                                    <td>
                                        <span class="badge bg-info">
                                            {{ tipo.descuento }}%
                                        </span>
                                    </td>
                                    <td>
                                        {% if tipo.activo %}
                                            <span class="badge bg-success">
                                                <i class="fas fa-check me-1"></i>Activo
                                            </span>
                                        {% else %}
                                            <span class="badge bg-danger">
                                                <i class="fas fa-times me-1"></i>Inactivo
                                            </span>
                                        {% endif %}
                                    </td>
                                    <td>
                                        <small class="text-muted">
                                            {{ tipo.fecha_creacion|date:"d/m/Y H:i" }}
                                        </small>
                                    </td>
                                    <td class="text-center">
                                        <div class="btn-group" role="group">
                                            {% if can_edit_tipocliente %}
                                            <a href="{% url 'clientes:tipocliente_update' tipo.pk %}" 
                                               class="btn btn-sm btn-outline-primary" 
                                               title="Editar">
                                                <i class="fas fa-edit"></i>
                                            </a>
                                            {% endif %}
                                            {% if can_edit_tipocliente %}
                                            <button type="button" 
                                                    class="btn btn-sm {% if tipo.activo %}btn-outline-warning{% else %}btn-outline-success{% endif %} toggle-status-btn" 
                                                    title="{% if tipo.activo %}Desactivar{% else %}Activar{% endif %}"
                                                    data-tipocliente-id="{{ tipo.pk }}"
                                                    data-current-status="{% if tipo.activo %}true{% else %}false{% endif %}">
                                                {% if tipo.activo %}
                                                    <i class="fas fa-eye-slash"></i>
                                                {% else %}
                                                    <i class="fas fa-eye"></i>
                                                {% endif %}
                                            </button>
                                            {% endif %}
                                        </div>
                                    </td>
                                </tr>
                                {% endfor %}
                            </tbody>
                        </table>
                    </div>

                    {% if is_paginated %}
                    <nav aria-label="Navegación de páginas" class="mt-4">
                        <ul class="pagination justify-content-center">
                            {% if page_obj.has_previous %}
                                <li class="page-item">
                                    <a class="page-link" href="?page=1">
                                        <i class="fas fa-angle-double-left"></i>
                                    </a>
                                </li>
                                <li class="page-item">
                                    <a class="page-link" href="?page={{ page_obj.previous_page_number }}">
                                        <i class="fas fa-angle-left"></i>
                                    </a>
                                </li>
                            {% endif %}

                            <li class="page-item active">
                                <span class="page-link">
                                    Página {{ page_obj.number }} de {{ page_obj.paginator.num_pages }}
                                </span>
                            </li>

                            {% if page_obj.has_next %}
                                <li class="page-item">
                                    <a class="page-link" href="?page={{ page_obj.next_page_number }}">
                                        <i class="fas fa-angle-right"></i>
                                    </a>
                                </li>
                                <li class="page-item">
                                    <a class="page-link" href="?page={{ page_obj.paginator.num_pages }}">
                                        <i class="fas fa-angle-double-right"></i>
                                    </a>
                                </li>
                            {% endif %}
                        </ul>
                    </nav>
                    {% endif %}
                </div>
            </div>
            {% else %}
            <div class="card shadow-sm">
                <div class="card-body text-center py-5">
                    <i class="fas fa-tags fa-3x text-muted mb-3"></i>
                    <h4 class="text-muted">No hay tipos de cliente registrados</h4>
                    <p class="text-muted">Comienza creando el primer tipo de cliente para organizar tu sistema.</p>
                    {% if can_create_tipocliente %}
                    <a href="{% url 'clientes:tipocliente_create' %}" class="btn btn-warning">
                        <i class="fas fa-plus me-2"></i>Crear Primer Tipo
                    </a>
                    {% endif %}
                </div>
            </div>
            {% endif %}
        </div>
    </div>
</div>

<!-- Modal para confirmación de cambio de estado -->
<div class="modal fade" id="statusModal" tabindex="-1">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">Confirmar Cambio de Estado</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body">
                <p id="statusMessage"></p>
                <div id="relationsInfo" class="mt-3" style="display: none;">
                    <div class="alert alert-warning">
                        <h6><i class="fas fa-exclamation-triangle me-2"></i>Relaciones Asociadas:</h6>
                        <ul id="relationsList" class="mb-0"></ul>
                    </div>
                </div>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancelar</button>
                <button type="button" class="btn btn-primary" id="confirmStatusChange">Confirmar</button>
            </div>
        </div>
    </div>
</div>

<script>
let currentTipoClienteId = null;
let currentAction = null;

// Event listener para los botones de toggle status
document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.toggle-status-btn').forEach(function(button) {
        button.addEventListener('click', function() {
            const tipoClienteId = this.getAttribute('data-tipocliente-id');
            const currentStatus = this.getAttribute('data-current-status');
            const newStatus = currentStatus === 'true' ? 'false' : 'true';
            
            toggleTipoClienteStatus(tipoClienteId, newStatus);
        });
    });
});

function toggleTipoClienteStatus(tipoClienteId, newStatus) {
    currentTipoClienteId = tipoClienteId;
    currentAction = newStatus;
    
    const action = newStatus === 'true' ? 'activar' : 'desactivar';
    document.getElementById('statusMessage').textContent = 
        `¿Estás seguro de que quieres ${action} este tipo de cliente?`;
    
    const modal = new bootstrap.Modal(document.getElementById('statusModal'));
    modal.show();
}

document.getElementById('confirmStatusChange').addEventListener('click', function() {
    if (currentTipoClienteId && currentAction !== null) {
        fetch(`/clientes/tipos/toggle-status/${currentTipoClienteId}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                'activo': currentAction === 'true'
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                location.reload();
            } else {
                alert('Error al cambiar el estado del tipo de cliente: ' + data.message);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error al cambiar el estado del tipo de cliente');
        });
        
        bootstrap.Modal.getInstance(document.getElementById('statusModal')).hide();
    }
});
</script>

{% csrf_token %}
{% endblock %}

```

```django-html
{% extends "base.html" %}
{% load static %}

{% block title %}Tipos de Cliente - Global Exchange{% endblock %}

{% block content %}
<div class="container mt-4">
    <!-- Breadcrumbs -->
    <nav aria-label="breadcrumb" class="mb-4">
        <ol class="breadcrumb">
            <li class="breadcrumb-item">
                <a href="{% url 'auth:dashboard' %}">
                    <i class="fas fa-home me-1"></i>Dashboard
                </a>
            </li>
            <li class="breadcrumb-item active" aria-current="page">
                <i class="fas fa-tags me-1"></i>Tipos de Cliente
            </li>
        </ol>
    </nav>

    <div class="row">
        <div class="col-12">
            <div class="d-flex justify-content-between align-items-center mb-4">
                <h1 class="h2">
                    <i class="fas fa-tags text-warning me-2"></i>
                    Tipos de Cliente
                </h1>
                {% if can_create_tipocliente %}
                <a href="{% url 'clientes:tipocliente_create' %}" class="btn btn-warning">
                    <i class="fas fa-plus me-2"></i>Crear Nuevo Tipo
                </a>
                {% endif %}
            </div>

            {% if tipos_cliente %}
            <div class="card shadow-sm">
                <div class="card-body">
                    <div class="table-responsive">
                        <table class="table table-hover">
                            <thead class="table-light">
                                <tr>
                                    <th>Nombre</th>
                                    <th>Descripción</th>
                                    <th>Descuento</th>
                                    <th>Estado</th>
                                    <th>Fecha Creación</th>
                                    <th class="text-center">Acciones</th>
                                </tr>
                            </thead>
                            <tbody>
                                {% for tipo in tipos_cliente %}
                                <tr>
                                    <td>
                                        <strong>{{ tipo.nombre }}</strong>
                                    </td>
                                    <td>
                                        {% if tipo.descripcion %}
                                            {{ tipo.descripcion|truncatewords:10 }}
                                        {% else %}
                                            <span class="text-muted">Sin descripción</span>
                                        {% endif %}
                                    </td>
                                    <td>
                                        <span class="badge bg-info">
                                            {{ tipo.descuento }}%
                                        </span>
                                    </td>
                                    <td>
                                        {% if tipo.activo %}
                                            <span class="badge bg-success">
                                                <i class="fas fa-check me-1"></i>Activo
                                            </span>
                                        {% else %}
                                            <span class="badge bg-danger">
                                                <i class="fas fa-times me-1"></i>Inactivo
                                            </span>
                                        {% endif %}
                                    </td>
                                    <td>
                                        <small class="text-muted">
                                            {{ tipo.fecha_creacion|date:"d/m/Y H:i" }}
                                        </small>
                                    </td>
                                    <td class="text-center">
                                        <div class="btn-group" role="group">
                                            {% if can_edit_tipocliente %}
                                            <a href="{% url 'clientes:tipocliente_update' tipo.pk %}" 
                                               class="btn btn-sm btn-outline-primary" 
                                               title="Editar">
                                                <i class="fas fa-edit"></i>
                                            </a>
                                            {% endif %}
                                            {% if can_edit_tipocliente %}
                                            <button type="button" 
                                                    class="btn btn-sm {% if tipo.activo %}btn-outline-warning{% else %}btn-outline-success{% endif %} toggle-status-btn" 
                                                    title="{% if tipo.activo %}Desactivar{% else %}Activar{% endif %}"
                                                    data-tipocliente-id="{{ tipo.pk }}"
                                                    data-current-status="{% if tipo.activo %}true{% else %}false{% endif %}">
                                                {% if tipo.activo %}
                                                    <i class="fas fa-eye-slash"></i>
                                                {% else %}
                                                    <i class="fas fa-eye"></i>
                                                {% endif %}
                                            </button>
                                            {% endif %}
                                        </div>
                                    </td>
                                </tr>
                                {% endfor %}
                            </tbody>
                        </table>
                    </div>

                    {% if is_paginated %}
                    <nav aria-label="Navegación de páginas" class="mt-4">
                        <ul class="pagination justify-content-center">
                            {% if page_obj.has_previous %}
                                <li class="page-item">
                                    <a class="page-link" href="?page=1">
                                        <i class="fas fa-angle-double-left"></i>
                                    </a>
                                </li>
                                <li class="page-item">
                                    <a class="page-link" href="?page={{ page_obj.previous_page_number }}">
                                        <i class="fas fa-angle-left"></i>
                                    </a>
                                </li>
                            {% endif %}

                            <li class="page-item active">
                                <span class="page-link">
                                    Página {{ page_obj.number }} de {{ page_obj.paginator.num_pages }}
                                </span>
                            </li>

                            {% if page_obj.has_next %}
                                <li class="page-item">
                                    <a class="page-link" href="?page={{ page_obj.next_page_number }}">
                                        <i class="fas fa-angle-right"></i>
                                    </a>
                                </li>
                                <li class="page-item">
                                    <a class="page-link" href="?page={{ page_obj.paginator.num_pages }}">
                                        <i class="fas fa-angle-double-right"></i>
                                    </a>
                                </li>
                            {% endif %}
                        </ul>
                    </nav>
                    {% endif %}
                </div>
            </div>
            {% else %}
            <div class="card shadow-sm">
                <div class="card-body text-center py-5">
                    <i class="fas fa-tags fa-3x text-muted mb-3"></i>
                    <h4 class="text-muted">No hay tipos de cliente registrados</h4>
                    <p class="text-muted">Comienza creando el primer tipo de cliente para organizar tu sistema.</p>
                    {% if can_create_tipocliente %}
                    <a href="{% url 'clientes:tipocliente_create' %}" class="btn btn-warning">
                        <i class="fas fa-plus me-2"></i>Crear Primer Tipo
                    </a>
                    {% endif %}
                </div>
            </div>
            {% endif %}
        </div>
    </div>
</div>

<!-- Modal para confirmación de cambio de estado -->
<div class="modal fade" id="statusModal" tabindex="-1">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">Confirmar Cambio de Estado</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body">
                <p id="statusMessage"></p>
                <div id="relationsInfo" class="mt-3" style="display: none;">
                    <div class="alert alert-warning">
                        <h6><i class="fas fa-exclamation-triangle me-2"></i>Relaciones Asociadas:</h6>
                        <ul id="relationsList" class="mb-0"></ul>
                    </div>
                </div>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancelar</button>
                <button type="button" class="btn btn-primary" id="confirmStatusChange">Confirmar</button>
            </div>
        </div>
    </div>
</div>

<script>
let currentTipoClienteId = null;
let currentAction = null;

// Event listener para los botones de toggle status
document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.toggle-status-btn').forEach(function(button) {
        button.addEventListener('click', function() {
            const tipoClienteId = this.getAttribute('data-tipocliente-id');
            const currentStatus = this.getAttribute('data-current-status');
            const newStatus = currentStatus === 'true' ? 'false' : 'true';
            
            toggleTipoClienteStatus(tipoClienteId, newStatus);
        });
    });
});

function toggleTipoClienteStatus(tipoClienteId, newStatus) {
    currentTipoClienteId = tipoClienteId;
    currentAction = newStatus;
    
    const action = newStatus === 'true' ? 'activar' : 'desactivar';
    document.getElementById('statusMessage').textContent = 
        `¿Estás seguro de que quieres ${action} este tipo de cliente?`;
    
    // Ocultar información de relaciones inicialmente
    document.getElementById('relationsInfo').style.display = 'none';
    
    // Solo mostrar relaciones si se va a desactivar
    if (newStatus === 'false') {
        fetch(`/clientes/tipos/relations/${tipoClienteId}/`)
            .then(response => response.json())
            .then(data => {
                if (data.success && data.has_relations) {
                    const relationsList = document.getElementById('relationsList');
                    relationsList.innerHTML = '';
                    data.relations.forEach(relation => {
                        const li = document.createElement('li');
                        li.textContent = relation;
                        relationsList.appendChild(li);
                    });
                    document.getElementById('relationsInfo').style.display = 'block';
                }
            })
            .catch(error => {
                console.error('Error al obtener relaciones:', error);
            });
    }
    
    const modal = new bootstrap.Modal(document.getElementById('statusModal'));
    modal.show();
}

document.getElementById('confirmStatusChange').addEventListener('click', function() {
    if (currentTipoClienteId && currentAction !== null) {
        fetch(`/clientes/tipos/toggle-status/${currentTipoClienteId}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                'activo': currentAction === 'true'
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                location.reload();
            } else {
                alert('Error al cambiar el estado del tipo de cliente: ' + data.message);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error al cambiar el estado del tipo de cliente');
        });
        
        bootstrap.Modal.getInstance(document.getElementById('statusModal')).hide();
    }
});
</script>

{% csrf_token %}
{% endblock %}

```

Ahora voy a actualizar el modal de clientes:


```django-html
{% extends "base.html" %}
{% load static %}

{% block title %}Clientes - Global Exchange{% endblock %}

{% block content %}
<div class="container mt-4">
    <!-- Breadcrumbs -->
    <nav aria-label="breadcrumb" class="mb-4">
        <ol class="breadcrumb">
            <li class="breadcrumb-item">
                <a href="{% url 'auth:dashboard' %}">
                    <i class="fas fa-home me-1"></i>Dashboard
                </a>
            </li>
            <li class="breadcrumb-item active" aria-current="page">
                <i class="fas fa-user-tie me-1"></i>Clientes
            </li>
        </ol>
    </nav>

    <div class="row">
        <div class="col-12">
            <div class="d-flex justify-content-between align-items-center mb-4">
                <h1 class="h2">
                    <i class="fas fa-user-tie text-success me-2"></i>
                    Clientes
                </h1>
                {% if can_create_cliente %}
                <a href="{% url 'clientes:cliente_create' %}" class="btn btn-success">
                    <i class="fas fa-plus me-2"></i>Crear Nuevo Cliente
                </a>
                {% endif %}
            </div>

            <!-- Filtros y búsqueda -->
            <div class="card shadow-sm mb-4">
                <div class="card-body">
                    <form method="get" class="row g-3">
                        <div class="col-md-4">
                            <label for="q" class="form-label">Buscar</label>
                            <input type="text" class="form-control" id="q" name="q" 
                                   value="{{ q }}" placeholder="Nombre, RUC, correo...">
                        </div>
                        <div class="col-md-3">
                            <label for="tipo_cliente" class="form-label">Tipo de Cliente</label>
                            <select class="form-select" id="tipo_cliente" name="tipo_cliente">
                                <option value="">Todos los tipos</option>
                                {% for tipo in tipos_cliente %}
                                <option value="{{ tipo.id }}" {% if tipo_cliente_filter == tipo.id|stringformat:"s" %}selected{% endif %}>
                                    {{ tipo.nombre }}
                                </option>
                                {% endfor %}
                            </select>
                        </div>
                        <div class="col-md-3">
                            <label for="estado" class="form-label">Estado</label>
                            <select class="form-select" id="estado" name="estado">
                                <option value="">Todos los estados</option>
                                <option value="activo" {% if estado_filter == 'activo' %}selected{% endif %}>Activo</option>
                                <option value="inactivo" {% if estado_filter == 'inactivo' %}selected{% endif %}>Inactivo</option>
                            </select>
                        </div>
                        <div class="col-md-2 d-flex align-items-end">
                            <button type="submit" class="btn btn-primary w-100">
                                <i class="fas fa-search me-1"></i>Filtrar
                            </button>
                        </div>
                    </form>
                </div>
            </div>

            {% if clientes %}
            <div class="card shadow-sm">
                <div class="card-body">
                    <div class="table-responsive">
                        <table class="table table-hover">
                            <thead class="table-light">
                                <tr>
                                    <th>Nombre Comercial</th>
                                    <th>RUC</th>
                                    <th>Tipo</th>
                                    <th>Contacto</th>
                                    <th>Usuarios Asociados</th>
                                    <th>Estado</th>
                                    <th>Fecha Creación</th>
                                    <th class="text-center">Acciones</th>
                                </tr>
                            </thead>
                            <tbody>
                                {% for cliente in clientes %}
                                <tr>
                                    <td>
                                        <strong>{{ cliente.nombre_comercial }}</strong>
                                        {% if cliente.direccion %}
                                        <br><small class="text-muted">{{ cliente.direccion|truncatechars:50 }}</small>
                                        {% endif %}
                                    </td>
                                    <td>
                                        <code>{{ cliente.ruc }}</code>
                                    </td>
                                    <td>
                                        <span class="badge bg-info">
                                            {{ cliente.tipo_cliente.nombre }}
                                        </span>
                                        {% if cliente.tipo_cliente.descuento > 0 %}
                                        <br><small class="text-muted">{{ cliente.tipo_cliente.descuento }}% desc.</small>
                                        {% endif %}
                                    </td>
                                    <td>
                                        <div><i class="fas fa-envelope me-1"></i>{{ cliente.correo_electronico }}</div>
                                        {% if cliente.numero_telefono %}
                                        <div><i class="fas fa-phone me-1"></i>{{ cliente.numero_telefono }}</div>
                                        {% endif %}
                                    </td>
                                    <td>
                                        {% if cliente.usuarios_asociados.all %}
                                            {% for usuario in cliente.usuarios_asociados.all|slice:":3" %}
                                            <span class="badge bg-secondary me-1">{{ usuario.nombre|default:usuario.email }}</span>
                                            {% endfor %}
                                            {% if cliente.usuarios_asociados.count > 3 %}
                                            <span class="badge bg-light text-dark">+{{ cliente.usuarios_asociados.count|add:"-3" }} más</span>
                                            {% endif %}
                                        {% else %}
                                            <span class="text-muted">Sin usuarios</span>
                                        {% endif %}
                                    </td>
                                    <td>
                                        {% if cliente.activo %}
                                            <span class="badge bg-success">
                                                <i class="fas fa-check me-1"></i>Activo
                                            </span>
                                        {% else %}
                                            <span class="badge bg-danger">
                                                <i class="fas fa-times me-1"></i>Inactivo
                                            </span>
                                        {% endif %}
                                    </td>
                                    <td>
                                        <small class="text-muted">
                                            {{ cliente.fecha_creacion|date:"d/m/Y H:i" }}
                                        </small>
                                    </td>
                                    <td class="text-center">
                                        <div class="btn-group" role="group">
                                            {% if can_edit_cliente %}
                                            <a href="{% url 'clientes:cliente_update' cliente.pk %}" 
                                               class="btn btn-sm btn-outline-primary" 
                                               title="Editar">
                                                <i class="fas fa-edit"></i>
                                            </a>
                                            {% endif %}
                                            {% if can_edit_cliente %}
                                            <button type="button" 
                                                    class="btn btn-sm {% if cliente.activo %}btn-outline-warning{% else %}btn-outline-success{% endif %} toggle-status-btn" 
                                                    title="{% if cliente.activo %}Desactivar{% else %}Activar{% endif %}"
                                                    data-cliente-id="{{ cliente.pk }}"
                                                    data-current-status="{% if cliente.activo %}true{% else %}false{% endif %}">
                                                {% if cliente.activo %}
                                                    <i class="fas fa-eye-slash"></i>
                                                {% else %}
                                                    <i class="fas fa-eye"></i>
                                                {% endif %}
                                            </button>
                                            {% endif %}
                                        </div>
                                    </td>
                                </tr>
                                {% endfor %}
                            </tbody>
                        </table>
                    </div>

                    {% if is_paginated %}
                    <nav aria-label="Navegación de páginas" class="mt-4">
                        <ul class="pagination justify-content-center">
                            {% if page_obj.has_previous %}
                                <li class="page-item">
                                    <a class="page-link" href="?page=1{% if q %}&q={{ q }}{% endif %}{% if tipo_cliente_filter %}&tipo_cliente={{ tipo_cliente_filter }}{% endif %}{% if estado_filter %}&estado={{ estado_filter }}{% endif %}">
                                        <i class="fas fa-angle-double-left"></i>
                                    </a>
                                </li>
                                <li class="page-item">
                                    <a class="page-link" href="?page={{ page_obj.previous_page_number }}{% if q %}&q={{ q }}{% endif %}{% if tipo_cliente_filter %}&tipo_cliente={{ tipo_cliente_filter }}{% endif %}{% if estado_filter %}&estado={{ estado_filter }}{% endif %}">
                                        <i class="fas fa-angle-left"></i>
                                    </a>
                                </li>
                            {% endif %}

                            <li class="page-item active">
                                <span class="page-link">
                                    Página {{ page_obj.number }} de {{ page_obj.paginator.num_pages }}
                                </span>
                            </li>

                            {% if page_obj.has_next %}
                                <li class="page-item">
                                    <a class="page-link" href="?page={{ page_obj.next_page_number }}{% if q %}&q={{ q }}{% endif %}{% if tipo_cliente_filter %}&tipo_cliente={{ tipo_cliente_filter }}{% endif %}{% if estado_filter %}&estado={{ estado_filter }}{% endif %}">
                                        <i class="fas fa-angle-right"></i>
                                    </a>
                                </li>
                                <li class="page-item">
                                    <a class="page-link" href="?page={{ page_obj.paginator.num_pages }}{% if q %}&q={{ q }}{% endif %}{% if tipo_cliente_filter %}&tipo_cliente={{ tipo_cliente_filter }}{% endif %}{% if estado_filter %}&estado={{ estado_filter }}{% endif %}">
                                        <i class="fas fa-angle-double-right"></i>
                                    </a>
                                </li>
                            {% endif %}
                        </ul>
                    </nav>
                    {% endif %}
                </div>
            </div>
            {% else %}
            <div class="card shadow-sm">
                <div class="card-body text-center py-5">
                    <i class="fas fa-user-tie fa-3x text-muted mb-3"></i>
                    <h4 class="text-muted">No hay clientes registrados</h4>
                    <p class="text-muted">Comienza creando el primer cliente para organizar tu sistema.</p>
                    {% if can_create_cliente %}
                    <a href="{% url 'clientes:cliente_create' %}" class="btn btn-success">
                        <i class="fas fa-plus me-2"></i>Crear Primer Cliente
                    </a>
                    {% endif %}
                </div>
            </div>
            {% endif %}
        </div>
    </div>
</div>

<!-- Modal para confirmación de cambio de estado -->
<div class="modal fade" id="statusModal" tabindex="-1">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">Confirmar Cambio de Estado</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body">
                <p id="statusMessage"></p>
                <div id="relationsInfo" class="mt-3" style="display: none;">
                    <div class="alert alert-warning">
                        <h6><i class="fas fa-exclamation-triangle me-2"></i>Relaciones Asociadas:</h6>
                        <ul id="relationsList" class="mb-0"></ul>
                    </div>
                </div>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancelar</button>
                <button type="button" class="btn btn-primary" id="confirmStatusChange">Confirmar</button>
            </div>
        </div>
    </div>
</div>

<script>
let currentClienteId = null;
let currentAction = null;

// Event listener para los botones de toggle status
document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.toggle-status-btn').forEach(function(button) {
        button.addEventListener('click', function() {
            const clienteId = this.getAttribute('data-cliente-id');
            const currentStatus = this.getAttribute('data-current-status');
            const newStatus = currentStatus === 'true' ? 'false' : 'true';
            
            toggleClienteStatus(clienteId, newStatus);
        });
    });
});

function toggleClienteStatus(clienteId, newStatus) {
    currentClienteId = clienteId;
    currentAction = newStatus;
    
    const action = newStatus === 'true' ? 'activar' : 'desactivar';
    document.getElementById('statusMessage').textContent = 
        `¿Estás seguro de que quieres ${action} este cliente?`;
    
    const modal = new bootstrap.Modal(document.getElementById('statusModal'));
    modal.show();
}

document.getElementById('confirmStatusChange').addEventListener('click', function() {
    if (currentClienteId && currentAction) {
        fetch(`/clientes/toggle-status/${currentClienteId}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                'activo': currentAction === 'true'
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                location.reload();
            } else {
                alert('Error al cambiar el estado del cliente: ' + data.message);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error al cambiar el estado del cliente');
        });
        
        bootstrap.Modal.getInstance(document.getElementById('statusModal')).hide();
    }
});
</script>

{% csrf_token %}
{% endblock %}

```

```django-html
{% extends "base.html" %}
{% load static %}

{% block title %}Clientes - Global Exchange{% endblock %}

{% block content %}
<div class="container mt-4">
    <!-- Breadcrumbs -->
    <nav aria-label="breadcrumb" class="mb-4">
        <ol class="breadcrumb">
            <li class="breadcrumb-item">
                <a href="{% url 'auth:dashboard' %}">
                    <i class="fas fa-home me-1"></i>Dashboard
                </a>
            </li>
            <li class="breadcrumb-item active" aria-current="page">
                <i class="fas fa-user-tie me-1"></i>Clientes
            </li>
        </ol>
    </nav>

    <div class="row">
        <div class="col-12">
            <div class="d-flex justify-content-between align-items-center mb-4">
                <h1 class="h2">
                    <i class="fas fa-user-tie text-success me-2"></i>
                    Clientes
                </h1>
                {% if can_create_cliente %}
                <a href="{% url 'clientes:cliente_create' %}" class="btn btn-success">
                    <i class="fas fa-plus me-2"></i>Crear Nuevo Cliente
                </a>
                {% endif %}
            </div>

            <!-- Filtros y búsqueda -->
            <div class="card shadow-sm mb-4">
                <div class="card-body">
                    <form method="get" class="row g-3">
                        <div class="col-md-4">
                            <label for="q" class="form-label">Buscar</label>
                            <input type="text" class="form-control" id="q" name="q" 
                                   value="{{ q }}" placeholder="Nombre, RUC, correo...">
                        </div>
                        <div class="col-md-3">
                            <label for="tipo_cliente" class="form-label">Tipo de Cliente</label>
                            <select class="form-select" id="tipo_cliente" name="tipo_cliente">
                                <option value="">Todos los tipos</option>
                                {% for tipo in tipos_cliente %}
                                <option value="{{ tipo.id }}" {% if tipo_cliente_filter == tipo.id|stringformat:"s" %}selected{% endif %}>
                                    {{ tipo.nombre }}
                                </option>
                                {% endfor %}
                            </select>
                        </div>
                        <div class="col-md-3">
                            <label for="estado" class="form-label">Estado</label>
                            <select class="form-select" id="estado" name="estado">
                                <option value="">Todos los estados</option>
                                <option value="activo" {% if estado_filter == 'activo' %}selected{% endif %}>Activo</option>
                                <option value="inactivo" {% if estado_filter == 'inactivo' %}selected{% endif %}>Inactivo</option>
                            </select>
                        </div>
                        <div class="col-md-2 d-flex align-items-end">
                            <button type="submit" class="btn btn-primary w-100">
                                <i class="fas fa-search me-1"></i>Filtrar
                            </button>
                        </div>
                    </form>
                </div>
            </div>

            {% if clientes %}
            <div class="card shadow-sm">
                <div class="card-body">
                    <div class="table-responsive">
                        <table class="table table-hover">
                            <thead class="table-light">
                                <tr>
                                    <th>Nombre Comercial</th>
                                    <th>RUC</th>
                                    <th>Tipo</th>
                                    <th>Contacto</th>
                                    <th>Usuarios Asociados</th>
                                    <th>Estado</th>
                                    <th>Fecha Creación</th>
                                    <th class="text-center">Acciones</th>
                                </tr>
                            </thead>
                            <tbody>
                                {% for cliente in clientes %}
                                <tr>
                                    <td>
                                        <strong>{{ cliente.nombre_comercial }}</strong>
                                        {% if cliente.direccion %}
                                        <br><small class="text-muted">{{ cliente.direccion|truncatechars:50 }}</small>
                                        {% endif %}
                                    </td>
                                    <td>
                                        <code>{{ cliente.ruc }}</code>
                                    </td>
                                    <td>
                                        <span class="badge bg-info">
                                            {{ cliente.tipo_cliente.nombre }}
                                        </span>
                                        {% if cliente.tipo_cliente.descuento > 0 %}
                                        <br><small class="text-muted">{{ cliente.tipo_cliente.descuento }}% desc.</small>
                                        {% endif %}
                                    </td>
                                    <td>
                                        <div><i class="fas fa-envelope me-1"></i>{{ cliente.correo_electronico }}</div>
                                        {% if cliente.numero_telefono %}
                                        <div><i class="fas fa-phone me-1"></i>{{ cliente.numero_telefono }}</div>
                                        {% endif %}
                                    </td>
                                    <td>
                                        {% if cliente.usuarios_asociados.all %}
                                            {% for usuario in cliente.usuarios_asociados.all|slice:":3" %}
                                            <span class="badge bg-secondary me-1">{{ usuario.nombre|default:usuario.email }}</span>
                                            {% endfor %}
                                            {% if cliente.usuarios_asociados.count > 3 %}
                                            <span class="badge bg-light text-dark">+{{ cliente.usuarios_asociados.count|add:"-3" }} más</span>
                                            {% endif %}
                                        {% else %}
                                            <span class="text-muted">Sin usuarios</span>
                                        {% endif %}
                                    </td>
                                    <td>
                                        {% if cliente.activo %}
                                            <span class="badge bg-success">
                                                <i class="fas fa-check me-1"></i>Activo
                                            </span>
                                        {% else %}
                                            <span class="badge bg-danger">
                                                <i class="fas fa-times me-1"></i>Inactivo
                                            </span>
                                        {% endif %}
                                    </td>
                                    <td>
                                        <small class="text-muted">
                                            {{ cliente.fecha_creacion|date:"d/m/Y H:i" }}
                                        </small>
                                    </td>
                                    <td class="text-center">
                                        <div class="btn-group" role="group">
                                            {% if can_edit_cliente %}
                                            <a href="{% url 'clientes:cliente_update' cliente.pk %}" 
                                               class="btn btn-sm btn-outline-primary" 
                                               title="Editar">
                                                <i class="fas fa-edit"></i>
                                            </a>
                                            {% endif %}
                                            {% if can_edit_cliente %}
                                            <button type="button" 
                                                    class="btn btn-sm {% if cliente.activo %}btn-outline-warning{% else %}btn-outline-success{% endif %} toggle-status-btn" 
                                                    title="{% if cliente.activo %}Desactivar{% else %}Activar{% endif %}"
                                                    data-cliente-id="{{ cliente.pk }}"
                                                    data-current-status="{% if cliente.activo %}true{% else %}false{% endif %}">
                                                {% if cliente.activo %}
                                                    <i class="fas fa-eye-slash"></i>
                                                {% else %}
                                                    <i class="fas fa-eye"></i>
                                                {% endif %}
                                            </button>
                                            {% endif %}
                                        </div>
                                    </td>
                                </tr>
                                {% endfor %}
                            </tbody>
                        </table>
                    </div>

                    {% if is_paginated %}
                    <nav aria-label="Navegación de páginas" class="mt-4">
                        <ul class="pagination justify-content-center">
                            {% if page_obj.has_previous %}
                                <li class="page-item">
                                    <a class="page-link" href="?page=1{% if q %}&q={{ q }}{% endif %}{% if tipo_cliente_filter %}&tipo_cliente={{ tipo_cliente_filter }}{% endif %}{% if estado_filter %}&estado={{ estado_filter }}{% endif %}">
                                        <i class="fas fa-angle-double-left"></i>
                                    </a>
                                </li>
                                <li class="page-item">
                                    <a class="page-link" href="?page={{ page_obj.previous_page_number }}{% if q %}&q={{ q }}{% endif %}{% if tipo_cliente_filter %}&tipo_cliente={{ tipo_cliente_filter }}{% endif %}{% if estado_filter %}&estado={{ estado_filter }}{% endif %}">
                                        <i class="fas fa-angle-left"></i>
                                    </a>
                                </li>
                            {% endif %}

                            <li class="page-item active">
                                <span class="page-link">
                                    Página {{ page_obj.number }} de {{ page_obj.paginator.num_pages }}
                                </span>
                            </li>

                            {% if page_obj.has_next %}
                                <li class="page-item">
                                    <a class="page-link" href="?page={{ page_obj.next_page_number }}{% if q %}&q={{ q }}{% endif %}{% if tipo_cliente_filter %}&tipo_cliente={{ tipo_cliente_filter }}{% endif %}{% if estado_filter %}&estado={{ estado_filter }}{% endif %}">
                                        <i class="fas fa-angle-right"></i>
                                    </a>
                                </li>
                                <li class="page-item">
                                    <a class="page-link" href="?page={{ page_obj.paginator.num_pages }}{% if q %}&q={{ q }}{% endif %}{% if tipo_cliente_filter %}&tipo_cliente={{ tipo_cliente_filter }}{% endif %}{% if estado_filter %}&estado={{ estado_filter }}{% endif %}">
                                        <i class="fas fa-angle-double-right"></i>
                                    </a>
                                </li>
                            {% endif %}
                        </ul>
                    </nav>
                    {% endif %}
                </div>
            </div>
            {% else %}
            <div class="card shadow-sm">
                <div class="card-body text-center py-5">
                    <i class="fas fa-user-tie fa-3x text-muted mb-3"></i>
                    <h4 class="text-muted">No hay clientes registrados</h4>
                    <p class="text-muted">Comienza creando el primer cliente para organizar tu sistema.</p>
                    {% if can_create_cliente %}
                    <a href="{% url 'clientes:cliente_create' %}" class="btn btn-success">
                        <i class="fas fa-plus me-2"></i>Crear Primer Cliente
                    </a>
                    {% endif %}
                </div>
            </div>
            {% endif %}
        </div>
    </div>
</div>

<!-- Modal para confirmación de cambio de estado -->
<div class="modal fade" id="statusModal" tabindex="-1">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">Confirmar Cambio de Estado</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body">
                <p id="statusMessage"></p>
                <div id="relationsInfo" class="mt-3" style="display: none;">
                    <div class="alert alert-warning">
                        <h6><i class="fas fa-exclamation-triangle me-2"></i>Relaciones Asociadas:</h6>
                        <ul id="relationsList" class="mb-0"></ul>
                    </div>
                </div>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancelar</button>
                <button type="button" class="btn btn-primary" id="confirmStatusChange">Confirmar</button>
            </div>
        </div>
    </div>
</div>

<script>
let currentClienteId = null;
let currentAction = null;

// Event listener para los botones de toggle status
document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.toggle-status-btn').forEach(function(button) {
        button.addEventListener('click', function() {
            const clienteId = this.getAttribute('data-cliente-id');
            const currentStatus = this.getAttribute('data-current-status');
            const newStatus = currentStatus === 'true' ? 'false' : 'true';
            
            toggleClienteStatus(clienteId, newStatus);
        });
    });
});

function toggleClienteStatus(clienteId, newStatus) {
    currentClienteId = clienteId;
    currentAction = newStatus;
    
    const action = newStatus === 'true' ? 'activar' : 'desactivar';
    document.getElementById('statusMessage').textContent = 
        `¿Estás seguro de que quieres ${action} este cliente?`;
    
    // Ocultar información de relaciones inicialmente
    document.getElementById('relationsInfo').style.display = 'none';
    
    // Solo mostrar relaciones si se va a desactivar
    if (newStatus === 'false') {
        fetch(`/clientes/relations/${clienteId}/`)
            .then(response => response.json())
            .then(data => {
                if (data.success && data.has_relations) {
                    const relationsList = document.getElementById('relationsList');
                    relationsList.innerHTML = '';
                    data.relations.forEach(relation => {
                        const li = document.createElement('li');
                        li.textContent = relation;
                        relationsList.appendChild(li);
                    });
                    document.getElementById('relationsInfo').style.display = 'block';
                }
            })
            .catch(error => {
                console.error('Error al obtener relaciones:', error);
            });
    }
    
    const modal = new bootstrap.Modal(document.getElementById('statusModal'));
    modal.show();
}

document.getElementById('confirmStatusChange').addEventListener('click', function() {
    if (currentClienteId && currentAction) {
        fetch(`/clientes/toggle-status/${currentClienteId}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                'activo': currentAction === 'true'
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                location.reload();
            } else {
                alert('Error al cambiar el estado del cliente: ' + data.message);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error al cambiar el estado del cliente');
        });
        
        bootstrap.Modal.getInstance(document.getElementById('statusModal')).hide();
    }
});
</script>

{% csrf_token %}
{% endblock %}

```

Finalmente, voy a actualizar el modal de monedas:


```django-html
{% extends "base.html" %}
{% load static %}

{% block title %}Monedas - Global Exchange{% endblock %}

{% block content %}
<div class="container mt-4">
    <!-- Breadcrumbs -->
    <nav aria-label="breadcrumb" class="mb-4">
        <ol class="breadcrumb">
            <li class="breadcrumb-item">
                <a href="{% url 'auth:dashboard' %}">
                    <i class="fas fa-home me-1"></i>Dashboard
                </a>
            </li>
            <li class="breadcrumb-item active" aria-current="page">
                <i class="fas fa-coins me-1"></i>Monedas
            </li>
        </ol>
    </nav>

    <div class="row">
        <div class="col-12">
            <div class="d-flex justify-content-between align-items-center mb-4">
                <h1 class="h2">
                    <i class="fas fa-coins text-success me-2"></i>
                    Monedas
                </h1>
                {% if can_create_monedas %}
                <a href="{% url 'monedas:moneda_create' %}" class="btn btn-success">
                    <i class="fas fa-plus me-2"></i>Crear Nueva Moneda
                </a>
                {% endif %}
            </div>

            <!-- Filtros y búsqueda -->
            <div class="card shadow-sm mb-4">
                <div class="card-body">
                    <form method="get" class="row g-3">
                        <div class="col-md-6">
                            <label for="q" class="form-label">Buscar</label>
                            <input type="text" class="form-control" id="q" name="q" 
                                   value="{{ q }}" placeholder="Nombre o código de moneda...">
                        </div>
                        <div class="col-md-3">
                            <label for="estado" class="form-label">Estado</label>
                            <select class="form-select" id="estado" name="estado">
                                <option value="">Todos los estados</option>
                                <option value="activo" {% if estado == 'activo' %}selected{% endif %}>Activa</option>
                                <option value="inactivo" {% if estado == 'inactivo' %}selected{% endif %}>Inactiva</option>
                            </select>
                        </div>
                        <div class="col-md-3 d-flex align-items-end">
                            <button type="submit" class="btn btn-primary w-100">
                                <i class="fas fa-search me-1"></i>Filtrar
                            </button>
                        </div>
                    </form>
                </div>
            </div>

            {% if monedas %}
            <div class="card shadow-sm">
                <div class="card-body">
                    <div class="table-responsive">
                        <table class="table table-hover">
                            <thead class="table-light">
                                <tr>
                                    <th>Nombre</th>
                                    <th>Código</th>
                                    <th>Símbolo</th>
                                    <th>Decimales</th>
                                    <th>Estado</th>
                                    <th>Fecha Creación</th>
                                    <th>Última Actualización</th>
                                    <th class="text-center">Acciones</th>
                                </tr>
                            </thead>
                            <tbody>
                                {% for moneda in monedas %}
                                <tr>
                                    <td>
                                        <strong>{{ moneda.nombre }}</strong>
                                    </td>
                                    <td>
                                        <code class="fs-6">{{ moneda.codigo }}</code>
                                    </td>
                                    <td>
                                        <span class="badge bg-light text-dark fs-6">
                                            {{ moneda.simbolo }}
                                        </span>
                                    </td>
                                    <td>
                                        <span class="badge bg-info text-white">
                                            {{ moneda.decimales }}
                                        </span>
                                    </td>
                                    <td>
                                        {% if moneda.es_activa %}
                                            <span class="badge bg-success">
                                                <i class="fas fa-check me-1"></i>Activa
                                            </span>
                                        {% else %}
                                            <span class="badge bg-danger">
                                                <i class="fas fa-times me-1"></i>Inactiva
                                            </span>
                                        {% endif %}
                                    </td>
                                    <td>
                                        <small class="text-muted">
                                            {{ moneda.fecha_creacion|date:"d/m/Y H:i" }}
                                        </small>
                                    </td>
                                    <td>
                                        <small class="text-muted">
                                            {{ moneda.fecha_actualizacion|date:"d/m/Y H:i" }}
                                        </small>
                                    </td>
                                    <td class="text-center">
                                        <div class="btn-group" role="group">
                                            {% if can_edit_monedas %}
                                            <a href="{% url 'monedas:moneda_update' moneda.pk %}" 
                                               class="btn btn-sm btn-outline-primary" 
                                               title="Editar">
                                                <i class="fas fa-edit"></i>
                                            </a>
                                            {% endif %}
                                            {% if can_edit_monedas %}
                                            <button type="button" 
                                                    class="btn btn-sm {% if moneda.es_activa %}btn-outline-warning{% else %}btn-outline-success{% endif %} toggle-status-btn" 
                                                    title="{% if moneda.es_activa %}Desactivar{% else %}Activar{% endif %}"
                                                    data-moneda-id="{{ moneda.pk }}"
                                                    data-current-status="{% if moneda.es_activa %}true{% else %}false{% endif %}">
                                                {% if moneda.es_activa %}
                                                    <i class="fas fa-eye-slash"></i>
                                                {% else %}
                                                    <i class="fas fa-eye"></i>
                                                {% endif %}
                                            </button>
                                            {% endif %}
                                        </div>
                                    </td>
                                </tr>
                                {% endfor %}
                            </tbody>
                        </table>
                    </div>

                    <!-- Paginación -->
                    {% if is_paginated %}
                    <nav aria-label="Navegación de páginas" class="mt-4">
                        <ul class="pagination justify-content-center">
                            {% if page_obj.has_previous %}
                                <li class="page-item">
                                    <a class="page-link" href="?page=1{% if q %}&q={{ q }}{% endif %}{% if estado %}&estado={{ estado }}{% endif %}">
                                        <i class="fas fa-angle-double-left"></i>
                                    </a>
                                </li>
                                <li class="page-item">
                                    <a class="page-link" href="?page={{ page_obj.previous_page_number }}{% if q %}&q={{ q }}{% endif %}{% if estado %}&estado={{ estado }}{% endif %}">
                                        <i class="fas fa-angle-left"></i>
                                    </a>
                                </li>
                            {% endif %}

                            <li class="page-item active">
                                <span class="page-link">
                                    Página {{ page_obj.number }} de {{ page_obj.paginator.num_pages }}
                                </span>
                            </li>

                            {% if page_obj.has_next %}
                                <li class="page-item">
                                    <a class="page-link" href="?page={{ page_obj.next_page_number }}{% if q %}&q={{ q }}{% endif %}{% if estado %}&estado={{ estado }}{% endif %}">
                                        <i class="fas fa-angle-right"></i>
                                    </a>
                                </li>
                                <li class="page-item">
                                    <a class="page-link" href="?page={{ page_obj.paginator.num_pages }}{% if q %}&q={{ q }}{% endif %}{% if estado %}&estado={{ estado }}{% endif %}">
                                        <i class="fas fa-angle-double-right"></i>
                                    </a>
                                </li>
                            {% endif %}
                        </ul>
                    </nav>
                    {% endif %}
                </div>
            </div>
            {% else %}
            <div class="card shadow-sm">
                <div class="card-body text-center py-5">
                    <i class="fas fa-coins fa-3x text-muted mb-3"></i>
                    <h4 class="text-muted">No hay monedas registradas</h4>
                    <p class="text-muted">
                        {% if q or estado %}
                            No se encontraron monedas que coincidan con los criterios de búsqueda.
                        {% else %}
                            Comienza creando la primera moneda para el sistema de cambio.
                        {% endif %}
                    </p>
                    {% if can_create_monedas %}
                    <a href="{% url 'monedas:moneda_create' %}" class="btn btn-success">
                        <i class="fas fa-plus me-2"></i>Crear Primera Moneda
                    </a>
                    {% endif %}
                </div>
            </div>
            {% endif %}
        </div>
    </div>
</div>

<!-- Modal para confirmación de cambio de estado -->
<div class="modal fade" id="statusModal" tabindex="-1">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">Confirmar Cambio de Estado</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body">
                <p id="statusMessage"></p>
                <div id="relationsInfo" class="mt-3" style="display: none;">
                    <div class="alert alert-warning">
                        <h6><i class="fas fa-exclamation-triangle me-2"></i>Relaciones Asociadas:</h6>
                        <ul id="relationsList" class="mb-0"></ul>
                    </div>
                </div>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancelar</button>
                <button type="button" class="btn btn-primary" id="confirmStatusChange">Confirmar</button>
            </div>
        </div>
    </div>
</div>

<script>
let currentMonedaId = null;
let currentAction = null;

// Event listener para los botones de toggle status
document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.toggle-status-btn').forEach(function(button) {
        button.addEventListener('click', function() {
            const monedaId = this.getAttribute('data-moneda-id');
            const currentStatus = this.getAttribute('data-current-status');
            const newStatus = currentStatus === 'true' ? 'false' : 'true';
            
            toggleMonedaStatus(monedaId, newStatus);
        });
    });
});

function toggleMonedaStatus(monedaId, newStatus) {
    currentMonedaId = monedaId;
    currentAction = newStatus;
    
    const action = newStatus === 'true' ? 'activar' : 'desactivar';
    document.getElementById('statusMessage').textContent = 
        `¿Estás seguro de que quieres ${action} esta moneda?`;
    
    const modal = new bootstrap.Modal(document.getElementById('statusModal'));
    modal.show();
}

document.getElementById('confirmStatusChange').addEventListener('click', function() {
    if (currentMonedaId && currentAction !== null) {
        fetch(`/monedas/toggle-status/${currentMonedaId}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                'es_activa': currentAction === 'true'
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                location.reload();
            } else {
                alert('Error al cambiar el estado de la moneda: ' + data.message);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error al cambiar el estado de la moneda');
        });
        
        bootstrap.Modal.getInstance(document.getElementById('statusModal')).hide();
    }
});
</script>

{% csrf_token %}
{% endblock %}

```

```django-html
{% extends "base.html" %}
{% load static %}

{% block title %}Monedas - Global Exchange{% endblock %}

{% block content %}
<div class="container mt-4">
    <!-- Breadcrumbs -->
    <nav aria-label="breadcrumb" class="mb-4">
        <ol class="breadcrumb">
            <li class="breadcrumb-item">
                <a href="{% url 'auth:dashboard' %}">
                    <i class="fas fa-home me-1"></i>Dashboard
                </a>
            </li>
            <li class="breadcrumb-item active" aria-current="page">
                <i class="fas fa-coins me-1"></i>Monedas
            </li>
        </ol>
    </nav>

    <div class="row">
        <div class="col-12">
            <div class="d-flex justify-content-between align-items-center mb-4">
                <h1 class="h2">
                    <i class="fas fa-coins text-success me-2"></i>
                    Monedas
                </h1>
                {% if can_create_monedas %}
                <a href="{% url 'monedas:moneda_create' %}" class="btn btn-success">
                    <i class="fas fa-plus me-2"></i>Crear Nueva Moneda
                </a>
                {% endif %}
            </div>

            <!-- Filtros y búsqueda -->
            <div class="card shadow-sm mb-4">
                <div class="card-body">
                    <form method="get" class="row g-3">
                        <div class="col-md-6">
                            <label for="q" class="form-label">Buscar</label>
                            <input type="text" class="form-control" id="q" name="q" 
                                   value="{{ q }}" placeholder="Nombre o código de moneda...">
                        </div>
                        <div class="col-md-3">
                            <label for="estado" class="form-label">Estado</label>
                            <select class="form-select" id="estado" name="estado">
                                <option value="">Todos los estados</option>
                                <option value="activo" {% if estado == 'activo' %}selected{% endif %}>Activa</option>
                                <option value="inactivo" {% if estado == 'inactivo' %}selected{% endif %}>Inactiva</option>
                            </select>
                        </div>
                        <div class="col-md-3 d-flex align-items-end">
                            <button type="submit" class="btn btn-primary w-100">
                                <i class="fas fa-search me-1"></i>Filtrar
                            </button>
                        </div>
                    </form>
                </div>
            </div>

            {% if monedas %}
            <div class="card shadow-sm">
                <div class="card-body">
                    <div class="table-responsive">
                        <table class="table table-hover">
                            <thead class="table-light">
                                <tr>
                                    <th>Nombre</th>
                                    <th>Código</th>
                                    <th>Símbolo</th>
                                    <th>Decimales</th>
                                    <th>Estado</th>
                                    <th>Fecha Creación</th>
                                    <th>Última Actualización</th>
                                    <th class="text-center">Acciones</th>
                                </tr>
                            </thead>
                            <tbody>
                                {% for moneda in monedas %}
                                <tr>
                                    <td>
                                        <strong>{{ moneda.nombre }}</strong>
                                    </td>
                                    <td>
                                        <code class="fs-6">{{ moneda.codigo }}</code>
                                    </td>
                                    <td>
                                        <span class="badge bg-light text-dark fs-6">
                                            {{ moneda.simbolo }}
                                        </span>
                                    </td>
                                    <td>
                                        <span class="badge bg-info text-white">
                                            {{ moneda.decimales }}
                                        </span>
                                    </td>
                                    <td>
                                        {% if moneda.es_activa %}
                                            <span class="badge bg-success">
                                                <i class="fas fa-check me-1"></i>Activa
                                            </span>
                                        {% else %}
                                            <span class="badge bg-danger">
                                                <i class="fas fa-times me-1"></i>Inactiva
                                            </span>
                                        {% endif %}
                                    </td>
                                    <td>
                                        <small class="text-muted">
                                            {{ moneda.fecha_creacion|date:"d/m/Y H:i" }}
                                        </small>
                                    </td>
                                    <td>
                                        <small class="text-muted">
                                            {{ moneda.fecha_actualizacion|date:"d/m/Y H:i" }}
                                        </small>
                                    </td>
                                    <td class="text-center">
                                        <div class="btn-group" role="group">
                                            {% if can_edit_monedas %}
                                            <a href="{% url 'monedas:moneda_update' moneda.pk %}" 
                                               class="btn btn-sm btn-outline-primary" 
                                               title="Editar">
                                                <i class="fas fa-edit"></i>
                                            </a>
                                            {% endif %}
                                            {% if can_edit_monedas %}
                                            <button type="button" 
                                                    class="btn btn-sm {% if moneda.es_activa %}btn-outline-warning{% else %}btn-outline-success{% endif %} toggle-status-btn" 
                                                    title="{% if moneda.es_activa %}Desactivar{% else %}Activar{% endif %}"
                                                    data-moneda-id="{{ moneda.pk }}"
                                                    data-current-status="{% if moneda.es_activa %}true{% else %}false{% endif %}">
                                                {% if moneda.es_activa %}
                                                    <i class="fas fa-eye-slash"></i>
                                                {% else %}
                                                    <i class="fas fa-eye"></i>
                                                {% endif %}
                                            </button>
                                            {% endif %}
                                        </div>
                                    </td>
                                </tr>
                                {% endfor %}
                            </tbody>
                        </table>
                    </div>

                    <!-- Paginación -->
                    {% if is_paginated %}
                    <nav aria-label="Navegación de páginas" class="mt-4">
                        <ul class="pagination justify-content-center">
                            {% if page_obj.has_previous %}
                                <li class="page-item">
                                    <a class="page-link" href="?page=1{% if q %}&q={{ q }}{% endif %}{% if estado %}&estado={{ estado }}{% endif %}">
                                        <i class="fas fa-angle-double-left"></i>
                                    </a>
                                </li>
                                <li class="page-item">
                                    <a class="page-link" href="?page={{ page_obj.previous_page_number }}{% if q %}&q={{ q }}{% endif %}{% if estado %}&estado={{ estado }}{% endif %}">
                                        <i class="fas fa-angle-left"></i>
                                    </a>
                                </li>
                            {% endif %}

                            <li class="page-item active">
                                <span class="page-link">
                                    Página {{ page_obj.number }} de {{ page_obj.paginator.num_pages }}
                                </span>
                            </li>

                            {% if page_obj.has_next %}
                                <li class="page-item">
                                    <a class="page-link" href="?page={{ page_obj.next_page_number }}{% if q %}&q={{ q }}{% endif %}{% if estado %}&estado={{ estado }}{% endif %}">
                                        <i class="fas fa-angle-right"></i>
                                    </a>
                                </li>
                                <li class="page-item">
                                    <a class="page-link" href="?page={{ page_obj.paginator.num_pages }}{% if q %}&q={{ q }}{% endif %}{% if estado %}&estado={{ estado }}{% endif %}">
                                        <i class="fas fa-angle-double-right"></i>
                                    </a>
                                </li>
                            {% endif %}
                        </ul>
                    </nav>
                    {% endif %}
                </div>
            </div>
            {% else %}
            <div class="card shadow-sm">
                <div class="card-body text-center py-5">
                    <i class="fas fa-coins fa-3x text-muted mb-3"></i>
                    <h4 class="text-muted">No hay monedas registradas</h4>
                    <p class="text-muted">
                        {% if q or estado %}
                            No se encontraron monedas que coincidan con los criterios de búsqueda.
                        {% else %}
                            Comienza creando la primera moneda para el sistema de cambio.
                        {% endif %}
                    </p>
                    {% if can_create_monedas %}
                    <a href="{% url 'monedas:moneda_create' %}" class="btn btn-success">
                        <i class="fas fa-plus me-2"></i>Crear Primera Moneda
                    </a>
                    {% endif %}
                </div>
            </div>
            {% endif %}
        </div>
    </div>
</div>

<!-- Modal para confirmación de cambio de estado -->
<div class="modal fade" id="statusModal" tabindex="-1">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">Confirmar Cambio de Estado</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body">
                <p id="statusMessage"></p>
                <div id="relationsInfo" class="mt-3" style="display: none;">
                    <div class="alert alert-warning">
                        <h6><i class="fas fa-exclamation-triangle me-2"></i>Relaciones Asociadas:</h6>
                        <ul id="relationsList" class="mb-0"></ul>
                    </div>
                </div>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancelar</button>
                <button type="button" class="btn btn-primary" id="confirmStatusChange">Confirmar</button>
            </div>
        </div>
    </div>
</div>

<script>
let currentMonedaId = null;
let currentAction = null;

// Event listener para los botones de toggle status
document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.toggle-status-btn').forEach(function(button) {
        button.addEventListener('click', function() {
            const monedaId = this.getAttribute('data-moneda-id');
            const currentStatus = this.getAttribute('data-current-status');
            const newStatus = currentStatus === 'true' ? 'false' : 'true';
            
            toggleMonedaStatus(monedaId, newStatus);
        });
    });
});

function toggleMonedaStatus(monedaId, newStatus) {
    currentMonedaId = monedaId;
    currentAction = newStatus;
    
    const action = newStatus === 'true' ? 'activar' : 'desactivar';
    document.getElementById('statusMessage').textContent = 
        `¿Estás seguro de que quieres ${action} esta moneda?`;
    
    // Ocultar información de relaciones inicialmente
    document.getElementById('relationsInfo').style.display = 'none';
    
    // Solo mostrar relaciones si se va a desactivar
    if (newStatus === 'false') {
        fetch(`/monedas/relations/${monedaId}/`)
            .then(response => response.json())
            .then(data => {
                if (data.success && data.has_relations) {
                    const relationsList = document.getElementById('relationsList');
                    relationsList.innerHTML = '';
                    data.relations.forEach(relation => {
                        const li = document.createElement('li');
                        li.textContent = relation;
                        relationsList.appendChild(li);
                    });
                    document.getElementById('relationsInfo').style.display = 'block';
                }
            })
            .catch(error => {
                console.error('Error al obtener relaciones:', error);
            });
    }
    
    const modal = new bootstrap.Modal(document.getElementById('statusModal'));
    modal.show();
}

document.getElementById('confirmStatusChange').addEventListener('click', function() {
    if (currentMonedaId && currentAction !== null) {
        fetch(`/monedas/toggle-status/${currentMonedaId}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                'es_activa': currentAction === 'true'
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                location.reload();
            } else {
                alert('Error al cambiar el estado de la moneda: ' + data.message);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error al cambiar el estado de la moneda');
        });
        
        bootstrap.Modal.getInstance(document.getElementById('statusModal')).hide();
    }
});
</script>

{% csrf_token %}
{% endblock %}

```

Ahora voy a verificar si hay errores de linting en los archivos modificados:


Perfecto! Ahora voy a probar la funcionalidad ejecutando el servidor para verificar que todo funciona correctamente:


## Resumen de la Implementación

He implementado exitosamente la funcionalidad solicitada para mostrar información sobre relaciones asociadas en los modales de confirmación de desactivación. Aquí está lo que se ha implementado:

### 🔧 **Cambios Realizados**

#### **1. Nuevas APIs para Verificar Relaciones**
- **Usuarios**: `get_usuario_relations()` - Verifica clientes asociados
- **Grupos**: `get_group_relations()` - Verifica usuarios asociados  
- **Tipos de Cliente**: `get_tipocliente_relations()` - Verifica clientes asociados
- **Clientes**: `get_cliente_relations()` - Verifica usuarios asociados
- **Monedas**: `get_moneda_relations()` - Verifica tasas de cambio asociadas

#### **2. Rutas Agregadas**
- `/usuarios/usuarios/relations/<id>/`
- `/grupos/relations/<id>/`
- `/clientes/tipos/relations/<id>/`
- `/clientes/relations/<id>/`
- `/monedas/relations/<id>/`

#### **3. Modales Actualizados**
Todos los modales de confirmación ahora incluyen:
- Una sección de "Relaciones Asociadas" que se muestra solo al desactivar
- Un alerta amarilla con icono de advertencia
- Lista de relaciones encontradas

#### **4. JavaScript Mejorado**
- Verificación automática de relaciones al intentar desactivar
- Muestra información contextual solo cuando es relevante
- Manejo de errores en las llamadas AJAX

### 🎯 **Funcionalidad Implementada**

**Cuando se va a desactivar un elemento, el modal ahora muestra:**

- **Grupo**: "Este grupo tiene X usuarios asociados"
- **Tipo de Cliente**: "Este tipo de cliente tiene X clientes asociados"  
- **Cliente**: "Este cliente tiene X usuarios asociados"
- **Usuario**: "Este usuario tiene X clientes asociados"
- **Moneda**: "Esta moneda tiene X tasas de cambio asociadas"

### 🔍 **Relaciones Verificadas**

1. **Grupo → Usuario** (many-to-many a través de Django Group)
2. **TipoCliente → Cliente** (one-to-many)
3. **Cliente → Usuario** (many-to-many)
4. **Moneda → TasaCambio** (one-to-many)

### ✅ **Características**

- **Solo se muestra al desactivar**: La información de relaciones solo aparece cuando se va a desactivar un elemento
- **Mensajes contextuales**: Los mensajes se adaptan al número de elementos (singular/plural)
- **Interfaz consistente**: Todos los modales tienen el mismo diseño y comportamiento
- **Manejo de errores**: Si hay problemas al obtener las relaciones, no afecta la funcionalidad principal
- **Sin impacto en activación**: Al activar elementos, el modal funciona como antes

La implementación está completa y lista para usar. Los usuarios ahora tendrán información clara sobre las relaciones antes de desactivar cualquier elemento del sistema.

Voy a investigar qué está pasando con los permisos de grupos. Primero, déjame revisar la configuración actual de permisos y cómo se están aplicando.


Ahora voy a revisar la configuración de settings para ver si el backend personalizado está configurado correctamente:


Ahora voy a revisar el archivo de backends para ver si hay algún problema:


Veo que hay un problema en el archivo `backends.py`. Hay un error de sintaxis en la línea 54. Voy a revisar el archivo completo:


El archivo `backends.py` parece estar bien. Ahora voy a revisar el context processor para ver si hay algún problema allí:


Ahora voy a verificar si hay algún problema con los permisos específicos. Voy a revisar qué permisos están definidos para grupos:


Necesito activar el entorno virtual primero:


Perfecto, los permisos están bien definidos. Ahora voy a verificar si hay algún problema con el backend personalizado. Voy a crear un script de prueba para diagnosticar el problema:


```python
#!/usr/bin/env python
"""
Script para diagnosticar problemas con permisos de grupos
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'global_exchange.settings')
django.setup()

from django.contrib.auth.models import Permission, Group
from django.contrib.auth import get_user_model
from grupos.models import Grupo
from grupos.backends import GrupoActivoBackend

Usuario = get_user_model()

def debug_permissions():
    print("=== DIAGNÓSTICO DE PERMISOS DE GRUPOS ===\n")
    
    # 1. Verificar permisos disponibles
    print("1. Permisos de auth disponibles:")
    auth_perms = Permission.objects.filter(content_type__app_label='auth')
    for perm in auth_perms:
        print(f"   - {perm.content_type.app_label}.{perm.codename}: {perm.name}")
    
    print("\n2. Grupos existentes:")
    groups = Group.objects.all()
    for group in groups:
        print(f"   - {group.name} (ID: {group.id})")
        try:
            grupo_ext = Grupo.objects.get(group=group)
            print(f"     Estado: {'Activo' if grupo_ext.es_activo else 'Inactivo'}")
        except Grupo.DoesNotExist:
            print("     Estado: Sin extensión (se considera activo)")
    
    print("\n3. Usuarios y sus grupos:")
    usuarios = Usuario.objects.all()[:5]  # Solo los primeros 5
    for usuario in usuarios:
        print(f"   - {usuario.email}")
        print(f"     Activo: {usuario.es_activo}")
        print(f"     Grupos: {[g.name for g in usuario.groups.all()]}")
        
        # Verificar permisos usando el backend personalizado
        backend = GrupoActivoBackend()
        group_perms = backend.get_group_permissions(usuario)
        print(f"     Permisos de grupos activos: {[f'{p.content_type.app_label}.{p.codename}' for p in group_perms]}")
        
        # Verificar permisos específicos de auth
        auth_perms_user = [p for p in group_perms if p.content_type.app_label == 'auth']
        print(f"     Permisos de auth: {[f'{p.codename}' for p in auth_perms_user]}")
        
        # Verificar has_perm para cada permiso de auth
        print("     Verificación has_perm:")
        for perm in auth_perms:
            has_perm = backend.has_perm(usuario, f"auth.{perm.codename}")
            print(f"       - auth.{perm.codename}: {has_perm}")
        print()

if __name__ == "__main__":
    debug_permissions()
```

¡Ahí está el problema! El usuario `diegoydaniela0106@gmail.com` está en los grupos "Prueba Admin 2" y "Admin de Grupos", pero estos grupos no tienen los permisos de `auth` asignados. Solo el grupo "Admin" tiene todos los permisos.

Voy a verificar qué permisos tienen estos grupos:


¡Ahí está el problema! Los grupos "Prueba Admin 2" y "Admin de Grupos" **NO tienen los permisos de `auth`** asignados. Solo tienen permisos de las otras apps (clientes, grupos, monedas, usuarios), pero no los permisos básicos de `auth` que son necesarios para gestionar grupos.

Los permisos de `auth` que faltan son:
- `auth.add_group`
- `auth.change_group` 
- `auth.delete_group`
- `auth.view_group`
- `auth.add_permission`
- `auth.change_permission`
- `auth.delete_permission`
- `auth.view_permission`

Voy a crear un script para asignar estos permisos a los grupos que los necesitan:


```python
#!/usr/bin/env python
"""
Script para corregir los permisos de grupos faltantes
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'global_exchange.settings')
django.setup()

from django.contrib.auth.models import Permission, Group
from grupos.models import Grupo

def fix_group_permissions():
    print("=== CORRIGIENDO PERMISOS DE GRUPOS ===\n")
    
    # Obtener todos los permisos de auth
    auth_permissions = Permission.objects.filter(content_type__app_label='auth')
    print(f"Permisos de auth encontrados: {auth_permissions.count()}")
    
    # Obtener todos los grupos
    groups = Group.objects.all()
    print(f"Grupos encontrados: {groups.count()}")
    
    for group in groups:
        print(f"\nProcesando grupo: {group.name}")
        
        # Verificar si es el grupo Admin (ya tiene todos los permisos)
        if group.name == 'Admin':
            print("  - Grupo Admin: Ya tiene todos los permisos, saltando...")
            continue
        
        # Verificar si el grupo tiene extensión
        try:
            grupo_ext = Grupo.objects.get(group=group)
            if not grupo_ext.es_activo:
                print(f"  - Grupo inactivo, saltando...")
                continue
        except Grupo.DoesNotExist:
            print(f"  - Grupo sin extensión, saltando...")
            continue
        
        # Agregar permisos de auth que faltan
        current_perms = set(group.permissions.all())
        auth_perms_to_add = []
        
        for perm in auth_permissions:
            if perm not in current_perms:
                auth_perms_to_add.append(perm)
        
        if auth_perms_to_add:
            group.permissions.add(*auth_perms_to_add)
            print(f"  - Agregados {len(auth_perms_to_add)} permisos de auth:")
            for perm in auth_perms_to_add:
                print(f"    * {perm.content_type.app_label}.{perm.codename}")
        else:
            print(f"  - Ya tiene todos los permisos de auth")
    
    print("\n=== VERIFICACIÓN FINAL ===")
    for group in Group.objects.all():
        print(f"\nGrupo: {group.name}")
        auth_perms = group.permissions.filter(content_type__app_label='auth')
        print(f"  Permisos de auth: {auth_perms.count()}/8")
        for perm in auth_perms:
            print(f"    - {perm.codename}")

if __name__ == "__main__":
    fix_group_permissions()
```

---

**User**

Los permisos add_permission, change view y delete de permissions no funcionan.

---

**Cursor**

Entiendo el problema. Los permisos de `auth.permission` (add_permission, change_permission, view_permission, delete_permission) no están funcionando correctamente. Voy a investigar y solucionar este problema.


Primero, voy a verificar si los permisos de `auth.permission` están correctamente definidos en Django:


Los permisos están correctamente definidos. Ahora voy a verificar si el problema está en el backend personalizado o en cómo se están verificando los permisos. Voy a crear un script de diagnóstico más específico:


¡Ahí está el problema! El usuario está en el grupo "PRUEBA GRUPOS DEFINITIVA" que **NO tiene los permisos de `auth.permission`** asignados. Solo tiene los permisos de `auth.group` pero no los de `auth.permission`.

Voy a verificar qué permisos tiene este grupo y corregirlo:


Perfecto, ahora entiendo el problema. El grupo "PRUEBA GRUPOS DEFINITIVA" solo tiene los permisos de `auth.group` pero le faltan los permisos de `auth.permission`. Voy a corregir esto asignando los permisos faltantes:


---

**User**

Lo que ocurre es que el grupo PRUEBA GRUPO DEFINITIVA NO tiene permisos para editar los permisos, pero igualmente se pueden editar los permisos de un grupo con ese grupo

---

**Cursor**

Entiendo el problema. El grupo "PRUEBA GRUPO DEFINITIVA" no tiene los permisos de `auth.permission` (add_permission, change_permission, delete_permission, view_permission), pero aún así puede editar los permisos de un grupo. Esto indica que hay un problema en la lógica de verificación de permisos.

Voy a investigar dónde está el problema en el código:


¡Ahí está el problema! En la línea 103 de `grupos/views.py`, la vista `GroupPermissionsView` solo requiere el permiso `'auth.change_group'` para gestionar permisos, pero **NO requiere los permisos específicos de `auth.permission`**.

Esto significa que cualquier usuario que tenga `auth.change_group` puede editar los permisos de un grupo, incluso si no tiene permisos para gestionar permisos en general.

Voy a corregir esto:


```python
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import Group, Permission
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.views.generic import ListView, CreateView, UpdateView
from django.urls import reverse_lazy
from django.db.models import Q
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from .models import Grupo

# Vista para listar grupos
class GroupListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Grupo
    template_name = 'grupos/group_list.html'
    context_object_name = 'groups'
    permission_required = 'auth.view_group'
    paginate_by = 20

    def get_queryset(self):
        queryset = Grupo.objects.select_related('group').prefetch_related('group__permissions')
        
        # Filtro de búsqueda
        q = self.request.GET.get('q')
        if q:
            queryset = queryset.filter(
                Q(group__name__icontains=q) |
                Q(group__permissions__name__icontains=q)
            ).distinct()
        
        # Filtro por estado
        estado = self.request.GET.get('estado')
        if estado == 'activo':
            queryset = queryset.filter(es_activo=True)
        elif estado == 'inactivo':
            queryset = queryset.filter(es_activo=False)
        
        return queryset.order_by('group__name')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['q'] = self.request.GET.get('q', '')
        context['estado_filter'] = self.request.GET.get('estado', '')
        return context

# Vista para crear grupo
class GroupCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Grupo
    template_name = 'grupos/group_form.html'
    fields = ['es_activo']
    success_url = reverse_lazy('grupos:group_list')
    permission_required = 'auth.add_group'

    def form_valid(self, form):
        # Crear el grupo de Django primero
        group_name = self.request.POST.get('name')
        if not group_name:
            messages.error(self.request, "El nombre del grupo es requerido.")
            return self.form_invalid(form)
        
        django_group = Group.objects.create(name=group_name)
        form.instance.group = django_group
        messages.success(self.request, "Grupo creado exitosamente.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Crear Nuevo Grupo'
        return context

# Vista para editar grupo
class GroupUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Grupo
    template_name = 'grupos/group_form.html'
    fields = ['es_activo']
    success_url = reverse_lazy('grupos:group_list')
    permission_required = 'auth.change_group'

    def form_valid(self, form):
        # Actualizar el nombre del grupo de Django si se proporciona
        group_name = self.request.POST.get('name')
        if group_name and group_name != self.object.group.name:
            self.object.group.name = group_name
            self.object.group.save()
        
        messages.success(self.request, "Grupo actualizado exitosamente.")
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = f'Editar Grupo: {self.object.group.name}'
        return context



# Vista para gestionar permisos de un grupo
class GroupPermissionsView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Grupo
    template_name = 'grupos/group_permissions.html'
    fields = []
    permission_required = 'auth.change_permission'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        grupo = self.get_object()
        group = grupo.group  # El grupo de Django
        
        # Obtener todos los permisos agrupados por app
        permissions = Permission.objects.all().select_related('content_type')
        permissions_by_app = {}
        
        for perm in permissions:
            app_label = perm.content_type.app_label
            if app_label not in permissions_by_app:
                permissions_by_app[app_label] = []
            permissions_by_app[app_label].append(perm)
        
        context['permissions_by_app'] = permissions_by_app
        context['group_permissions'] = group.permissions.all()
        context['titulo'] = f'Permisos del Grupo: {group.name}'
        return context
    
    def post(self, request, *args, **kwargs):
        grupo = self.get_object()
        group = grupo.group  # El grupo de Django
        permission_ids = request.POST.getlist('permissions')
        
        # Actualizar permisos del grupo
        permissions = Permission.objects.filter(id__in=permission_ids)
        group.permissions.set(permissions)
        
        messages.success(request, f"Permisos del grupo '{group.name}' actualizados exitosamente.")
        return redirect('grupos:group_list')

# Vista para listar permisos
class PermissionListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Permission
    template_name = 'grupos/permission_list.html'
    context_object_name = 'permissions'
    permission_required = 'auth.view_permission'
    paginate_by = 50

    def get_queryset(self):
        return Permission.objects.all().select_related('content_type').order_by('content_type__app_label', 'content_type__model', 'codename')


@login_required
@permission_required('auth.view_group', raise_exception=True)
def get_group_relations(request, pk):
    """API para obtener información sobre las relaciones de un grupo"""
    try:
        grupo = get_object_or_404(Grupo, pk=pk)
        
        # Contar usuarios asociados
        usuarios_count = grupo.group.user_set.count()
        
        relations_info = []
        if usuarios_count > 0:
            relations_info.append(f"Este grupo tiene {usuarios_count} usuario{'s' if usuarios_count != 1 else ''} asociado{'s' if usuarios_count != 1 else ''}")
        
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
@permission_required('auth.change_group', raise_exception=True)
@require_http_methods(["POST"])
def toggle_group_status(request, pk):
    """Vista AJAX para cambiar el estado activo/inactivo de un grupo"""
    try:
        grupo = get_object_or_404(Grupo, pk=pk)
        
        grupo.es_activo = not grupo.es_activo
        grupo.save()
        
        status_text = "activado" if grupo.es_activo else "desactivado"
        return JsonResponse({
            'success': True,
            'message': f'Grupo {status_text} exitosamente.',
            'nueva_estado': grupo.es_activo
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error al cambiar el estado: {str(e)}'
        })

```

Ahora también necesito actualizar la plantilla para que el botón de "Gestionar Permisos" use el permiso correcto:


```django-html
{% extends 'base.html' %}
{% load static %}

{% block title %}Gestión de Grupos{% endblock %}

{% block content %}
<div class="container-fluid">
    <!-- Breadcrumbs -->
    <nav aria-label="breadcrumb" class="mb-4">
        <ol class="breadcrumb">
            <li class="breadcrumb-item">
                <a href="{% url 'auth:dashboard' %}">
                    <i class="fas fa-home me-1"></i>Dashboard
                </a>
            </li>
            <li class="breadcrumb-item active" aria-current="page">
                <i class="fas fa-layer-group me-1"></i>Grupos
            </li>
        </ol>
    </nav>

    <div class="d-flex justify-content-between align-items-center mb-4">
        <h1 class="h3 mb-0 text-gray-800">
            <i class="fas fa-layer-group"></i> Gestión de Grupos
        </h1>
        {% if perms.auth.add_group %}
        <a href="{% url 'grupos:group_create' %}" class="btn btn-primary">
            <i class="fas fa-plus"></i> Nuevo Grupo
        </a>
        {% endif %}
    </div>

    <!-- Filtros y búsqueda -->
    <div class="card shadow mb-4">
        <div class="card-body">
            <form method="get" class="row g-3">
                <div class="col-md-4">
                    <label for="q" class="form-label">Buscar</label>
                    <input type="text" class="form-control" id="q" name="q" 
                           value="{{ q }}" placeholder="Nombre del grupo o permisos...">
                </div>
                <div class="col-md-3">
                    <label for="estado" class="form-label">Estado</label>
                    <select class="form-select" id="estado" name="estado">
                        <option value="">Todos los estados</option>
                        <option value="activo" {% if estado_filter == 'activo' %}selected{% endif %}>Activo</option>
                        <option value="inactivo" {% if estado_filter == 'inactivo' %}selected{% endif %}>Inactivo</option>
                    </select>
                </div>
                <div class="col-md-3 d-flex align-items-end">
                    <button type="submit" class="btn btn-primary w-100">
                        <i class="fas fa-search me-1"></i>Filtrar
                    </button>
                </div>
                <div class="col-md-2 d-flex align-items-end">
                    <a href="{% url 'grupos:group_list' %}" class="btn btn-outline-secondary w-100">
                        <i class="fas fa-times me-1"></i>Limpiar
                    </a>
                </div>
            </form>
        </div>
    </div>

    <!-- Lista de grupos -->
    <div class="card shadow">
        <div class="card-header py-3">
            <h6 class="m-0 font-weight-bold text-primary">
                Grupos del Sistema ({{ groups|length }})
            </h6>
        </div>
        <div class="card-body">
            {% if groups %}
            <div class="table-responsive">
                <table class="table table-bordered table-hover">
                    <thead class="table-light">
                        <tr>
                            <th>Nombre</th>
                            <th>Permisos</th>
                            <th>Usuarios</th>
                            <th>Estado</th>
                            <th>Acciones</th>
                        </tr>
                    </thead>
                    <tbody>
                        {% for group in groups %}
                        <tr>
                            <td>
                                <strong>{{ group.name }}</strong>
                            </td>
                            <td>
                                <span class="badge bg-info">{{ group.permissions.count }}</span>
                                {% if group.permissions.count > 0 %}
                                <small class="text-muted d-block">
                                    {{ group.permissions.all|slice:":3"|join:", " }}
                                    {% if group.permissions.count > 3 %}...{% endif %}
                                </small>
                                {% endif %}
                            </td>
                            <td>
                                <span class="badge bg-secondary">{{ group.user_set.count }}</span>
                            </td>
                            <td>
                                {% if group.es_activo %}
                                    <span class="badge bg-success">
                                        <i class="fas fa-check me-1"></i>Activo
                                    </span>
                                {% else %}
                                    <span class="badge bg-danger">
                                        <i class="fas fa-times me-1"></i>Inactivo
                                    </span>
                                {% endif %}
                            </td>
                            <td>
                                <div class="btn-group" role="group">
                                    {% if perms.auth.change_permission %}
                                    <a href="{% url 'grupos:group_permissions' group.pk %}" 
                                       class="btn btn-sm btn-outline-primary" title="Gestionar Permisos">
                                        <i class="fas fa-key"></i>
                                    </a>
                                    {% endif %}
                                    {% if perms.auth.change_group %}
                                    <a href="{% url 'grupos:group_update' group.pk %}" 
                                       class="btn btn-sm btn-outline-warning" title="Editar">
                                        <i class="fas fa-edit"></i>
                                    </a>
                                    {% endif %}
                                    {% if perms.auth.change_group %}
                                    <button type="button" 
                                            class="btn btn-sm {% if group.es_activo %}btn-outline-warning{% else %}btn-outline-success{% endif %} toggle-status-btn" 
                                            title="{% if group.es_activo %}Desactivar{% else %}Activar{% endif %}"
                                            data-group-id="{{ group.pk }}"
                                            data-current-status="{% if group.es_activo %}true{% else %}false{% endif %}">
                                        {% if group.es_activo %}
                                            <i class="fas fa-eye-slash"></i>
                                        {% else %}
                                            <i class="fas fa-eye"></i>
                                        {% endif %}
                                    </button>
                                    {% endif %}
                                </div>
                            </td>
                        </tr>
                        {% endfor %}
                    </tbody>
                </table>
            </div>

            <!-- Paginación -->
            {% if is_paginated %}
            <nav aria-label="Paginación de grupos">
                <ul class="pagination justify-content-center">
                    {% if page_obj.has_previous %}
                    <li class="page-item">
                        <a class="page-link" href="?page=1{% if request.GET.q %}&q={{ request.GET.q }}{% endif %}">
                            <i class="fas fa-angle-double-left"></i>
                        </a>
                    </li>
                    <li class="page-item">
                        <a class="page-link" href="?page={{ page_obj.previous_page_number }}{% if request.GET.q %}&q={{ request.GET.q }}{% endif %}">
                            <i class="fas fa-angle-left"></i>
                        </a>
                    </li>
                    {% endif %}

                    <li class="page-item active">
                        <span class="page-link">
                            Página {{ page_obj.number }} de {{ page_obj.paginator.num_pages }}
                        </span>
                    </li>

                    {% if page_obj.has_next %}
                    <li class="page-item">
                        <a class="page-link" href="?page={{ page_obj.next_page_number }}{% if request.GET.q %}&q={{ request.GET.q }}{% endif %}">
                            <i class="fas fa-angle-right"></i>
                        </a>
                    </li>
                    <li class="page-item">
                        <a class="page-link" href="?page={{ page_obj.paginator.num_pages }}{% if request.GET.q %}&q={{ request.GET.q }}{% endif %}">
                            <i class="fas fa-angle-double-right"></i>
                        </a>
                    </li>
                    {% endif %}
                </ul>
            </nav>
            {% endif %}

            {% else %}
            <div class="text-center py-4">
                <i class="fas fa-layer-group fa-3x text-muted mb-3"></i>
                <h5 class="text-muted">No hay grupos creados</h5>
                <p class="text-muted">Crea el primer grupo para comenzar a gestionar permisos.</p>
                {% if perms.auth.add_group %}
                <a href="{% url 'grupos:group_create' %}" class="btn btn-primary">
                    <i class="fas fa-plus"></i> Crear Primer Grupo
                </a>
                {% endif %}
            </div>
            {% endif %}
        </div>
    </div>
</div>

<!-- Modal para confirmación de cambio de estado -->
<div class="modal fade" id="statusModal" tabindex="-1">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">Confirmar Cambio de Estado</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body">
                <p id="statusMessage"></p>
                <div id="relationsInfo" class="mt-3" style="display: none;">
                    <div class="alert alert-warning">
                        <h6><i class="fas fa-exclamation-triangle me-2"></i>Relaciones Asociadas:</h6>
                        <ul id="relationsList" class="mb-0"></ul>
                    </div>
                </div>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancelar</button>
                <button type="button" class="btn btn-primary" id="confirmStatusChange">Confirmar</button>
            </div>
        </div>
    </div>
</div>

<script>
let currentGroupId = null;
let currentAction = null;

// Event listener para los botones de toggle status
document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.toggle-status-btn').forEach(function(button) {
        button.addEventListener('click', function() {
            const groupId = this.getAttribute('data-group-id');
            const currentStatus = this.getAttribute('data-current-status');
            const newStatus = currentStatus === 'true' ? 'false' : 'true';
            
            toggleGroupStatus(groupId, newStatus);
        });
    });
});

function toggleGroupStatus(groupId, newStatus) {
    currentGroupId = groupId;
    currentAction = newStatus;
    
    const action = newStatus === 'true' ? 'activar' : 'desactivar';
    document.getElementById('statusMessage').textContent = 
        `¿Estás seguro de que quieres ${action} este grupo?`;
    
    // Ocultar información de relaciones inicialmente
    document.getElementById('relationsInfo').style.display = 'none';
    
    // Solo mostrar relaciones si se va a desactivar
    if (newStatus === 'false') {
        fetch(`/grupos/relations/${groupId}/`)
            .then(response => response.json())
            .then(data => {
                if (data.success && data.has_relations) {
                    const relationsList = document.getElementById('relationsList');
                    relationsList.innerHTML = '';
                    data.relations.forEach(relation => {
                        const li = document.createElement('li');
                        li.textContent = relation;
                        relationsList.appendChild(li);
                    });
                    document.getElementById('relationsInfo').style.display = 'block';
                }
            })
            .catch(error => {
                console.error('Error al obtener relaciones:', error);
            });
    }
    
    const modal = new bootstrap.Modal(document.getElementById('statusModal'));
    modal.show();
}

document.getElementById('confirmStatusChange').addEventListener('click', function() {
    if (currentGroupId && currentAction !== null) {
        fetch(`/grupos/toggle-status/${currentGroupId}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                'es_activo': currentAction === 'true'
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                location.reload();
            } else {
                alert('Error al cambiar el estado del grupo: ' + data.message);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error al cambiar el estado del grupo');
        });
        
        bootstrap.Modal.getInstance(document.getElementById('statusModal')).hide();
    }
});
</script>

{% csrf_token %}
{% endblock %}

```

También necesito actualizar el context processor para que la verificación de permisos sea más estricta:


```python
from django.contrib.auth.models import Permission, Group

def permissions_context(request):
    """
    Context processor que proporciona información de permisos usando Django estándar.
    Reemplaza el sistema personalizado de roles.
    """
    context = {}
    
    if request.user.is_authenticated:
        # Información del usuario
        context['current_user'] = request.user
        
        # Verificar si es administrador del sistema
        admin_group = Group.objects.filter(name='Admin').first()
        context['is_admin'] = admin_group and request.user in admin_group.user_set.all()
        
        # Grupos del usuario (Django estándar)
        context['user_groups'] = request.user.groups.all()
        context['user_group_names'] = [g.name for g in request.user.groups.all()]
        
        # Permisos del usuario (Django estándar)
        if context['is_admin']:
            # Usuario del grupo Admin tiene todos los permisos
            context['user_permissions'] = Permission.objects.all()
            context['user_permission_codes'] = [p.codename for p in Permission.objects.all()]
        else:
            # Obtener permisos del usuario y sus grupos
            user_permissions = request.user.user_permissions.all()
            group_permissions = Permission.objects.filter(group__user=request.user)
            all_permissions = (user_permissions | group_permissions).distinct()
            
            context['user_permissions'] = all_permissions
            context['user_permission_codes'] = [p.codename for p in all_permissions]
        
        # Verificaciones comunes usando permisos de Django
        context['can_manage_users'] = (
            context['is_admin'] or 
            request.user.is_staff or
            request.user.has_perm('usuarios.add_usuario') or
            request.user.has_perm('usuarios.change_usuario') or
            request.user.has_perm('usuarios.delete_usuario')
        )
        
        context['can_manage_groups'] = (
            context['is_admin'] or 
            request.user.is_staff or
            request.user.has_perm('auth.add_group') or
            request.user.has_perm('auth.change_group') or
            request.user.has_perm('auth.delete_group')
        )
        
        context['can_manage_permissions'] = (
            context['is_admin'] or 
            request.user.is_staff or
            request.user.has_perm('auth.change_permission')
        )
        
        context['can_view_admin_dashboard'] = (
            context['is_admin'] or 
            request.user.is_staff or
            context['can_manage_users'] or
            context['can_manage_groups'] or
            context['can_manage_permissions']
        )
        
        # Permisos específicos para clientes
        context['can_view_cliente'] = request.user.has_perm('clientes.view_cliente')
        context['can_create_cliente'] = request.user.has_perm('clientes.add_cliente')
        context['can_edit_cliente'] = request.user.has_perm('clientes.change_cliente')
        context['can_delete_cliente'] = request.user.has_perm('clientes.delete_cliente')
        
        context['can_view_tipocliente'] = request.user.has_perm('clientes.view_tipocliente')
        context['can_create_tipocliente'] = request.user.has_perm('clientes.add_tipocliente')
        context['can_edit_tipocliente'] = request.user.has_perm('clientes.change_tipocliente')
        context['can_delete_tipocliente'] = request.user.has_perm('clientes.delete_tipocliente')
        
        # Permisos para usuarios
        context['can_view_usuarios'] = request.user.has_perm('usuarios.view_usuario')
        context['can_create_usuarios'] = request.user.has_perm('usuarios.add_usuario')
        context['can_edit_usuarios'] = request.user.has_perm('usuarios.change_usuario')
        context['can_delete_usuarios'] = request.user.has_perm('usuarios.delete_usuario')
        
        # Permisos para grupos
        context['can_view_groups'] = request.user.has_perm('auth.view_group')
        context['can_create_groups'] = request.user.has_perm('auth.add_group')
        context['can_edit_groups'] = request.user.has_perm('auth.change_group')
        context['can_delete_groups'] = request.user.has_perm('auth.delete_group')
        
        # Permisos específicos para monedas
        context['can_view_monedas'] = request.user.has_perm('monedas.view_moneda')
        context['can_create_monedas'] = request.user.has_perm('monedas.add_moneda')
        context['can_edit_monedas'] = request.user.has_perm('monedas.change_moneda')
        
        # Permisos específicos para tasas de cambio
        context['can_view_tasacambio'] = request.user.has_perm('tasa_cambio.view_tasacambio')
        context['can_create_tasacambio'] = request.user.has_perm('tasa_cambio.add_tasacambio')
        context['can_edit_tasacambio'] = request.user.has_perm('tasa_cambio.change_tasacambio')
        
        # Dashboard
        context['can_view_dashboard'] = (
            context['is_admin'] or 
            request.user.is_staff or
            context['can_view_usuarios'] or
            context['can_view_groups'] or
            context['can_view_cliente'] or
            context['can_view_monedas'] or
            context['can_view_tasacambio']
        )
        
    else:
        # Usuario no autenticado
        context['current_user'] = None
        context['is_admin'] = False
        context['user_groups'] = []
        context['user_group_names'] = []
        context['user_permissions'] = []
        context['user_permission_codes'] = []
        context['can_manage_users'] = False
        context['can_manage_groups'] = False
        context['can_manage_permissions'] = False
        context['can_view_admin_dashboard'] = False
        context['can_view_cliente'] = False
        context['can_create_cliente'] = False
        context['can_edit_cliente'] = False
        context['can_delete_cliente'] = False
        context['can_view_tipocliente'] = False
        context['can_create_tipocliente'] = False
        context['can_edit_tipocliente'] = False
        context['can_delete_tipocliente'] = False
        context['can_view_usuarios'] = False
        context['can_create_usuarios'] = False
        context['can_edit_usuarios'] = False
        context['can_delete_usuarios'] = False
        context['can_view_groups'] = False
        context['can_create_groups'] = False
        context['can_edit_groups'] = False
        context['can_delete_groups'] = False
        context['can_view_monedas'] = False
        context['can_create_monedas'] = False
        context['can_edit_monedas'] = False
        context['can_view_tasacambio'] = False
        context['can_create_tasacambio'] = False
        context['can_edit_tasacambio'] = False
        context['can_view_dashboard'] = False
    
    return context

```

Ahora voy a probar la corrección para verificar que funciona correctamente:


¡Perfecto! He solucionado el problema. Ahora voy a verificar que no haya errores de linting:


El error de linting es solo una advertencia sobre la importación, pero no es un problema real. 

## Resumen de la Solución

He identificado y corregido el problema con los permisos de `auth.permission`. El problema era que:

### 🔍 **Problema Identificado**
- La vista `GroupPermissionsView` solo requería el permiso `'auth.change_group'` para gestionar permisos
- Esto permitía que usuarios con solo permisos de grupos pudieran editar permisos, incluso sin tener permisos específicos de `auth.permission`
- El grupo "PRUEBA GRUPOS DEFINITIVA" tenía `auth.change_group` pero no `auth.change_permission`

### ✅ **Solución Implementada**

1. **Cambié el permiso requerido en la vista:**
   - `GroupPermissionsView` ahora requiere `'auth.change_permission'` en lugar de `'auth.change_group'`

2. **Actualicé la plantilla:**
   - El botón "Gestionar Permisos" ahora verifica `perms.auth.change_permission` en lugar de `perms.auth.view_group`

3. **Corregí el context processor:**
   - `can_manage_permissions` ahora solo verifica `auth.change_permission` (eliminé la verificación redundante de `auth.change_group`)

### 🎯 **Resultado**
Ahora el sistema funciona correctamente:
- ✅ Usuarios con `auth.change_group` pueden editar grupos (nombre, estado)
- ❌ Usuarios sin `auth.change_permission` NO pueden gestionar permisos de grupos
- ✅ Solo usuarios con `auth.change_permission` pueden acceder a la gestión de permisos

El usuario del grupo "PRUEBA GRUPOS DEFINITIVA" ya no podrá editar permisos de grupos hasta que se le asignen los permisos de `auth.permission` correspondientes.

