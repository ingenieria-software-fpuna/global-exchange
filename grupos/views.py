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
from .forms import GrupoCreationForm, GrupoUpdateForm

# Vista para listar grupos
class GroupListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Grupo
    template_name = 'grupos/group_list.html'
    context_object_name = 'grupos'
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
        context['estado'] = self.request.GET.get('estado', '')
        return context

# Vista para crear grupo
class GroupCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Grupo
    form_class = GrupoCreationForm
    template_name = 'grupos/group_form.html'
    success_url = reverse_lazy('grupos:group_list')
    permission_required = 'auth.add_group'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Crear Nuevo Grupo'
        context['accion'] = 'Crear'
        return context

    def form_valid(self, form):
        messages.success(self.request, "Grupo creado exitosamente.")
        return super().form_valid(form)

# Vista para editar grupo
class GroupUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Grupo
    form_class = GrupoUpdateForm
    template_name = 'grupos/group_form.html'
    success_url = reverse_lazy('grupos:group_list')
    permission_required = 'auth.change_group'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = f'Editar Grupo: {self.object.group.name}'
        context['accion'] = 'Actualizar'
        return context

    def form_valid(self, form):
        messages.success(self.request, "Grupo actualizado exitosamente.")
        return super().form_valid(form)



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
