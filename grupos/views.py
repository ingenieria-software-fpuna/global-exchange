from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import Group, Permission
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib import messages
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.db.models import Q
from django.core.paginator import Paginator

# Vista para listar grupos
class GroupListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Group
    template_name = 'grupos/group_list.html'
    context_object_name = 'groups'
    permission_required = 'auth.view_group'
    paginate_by = 20

    def get_queryset(self):
        queryset = Group.objects.all().prefetch_related('permissions')
        
        # Filtro de búsqueda
        q = self.request.GET.get('q')
        if q:
            queryset = queryset.filter(
                Q(name__icontains=q) |
                Q(permissions__name__icontains=q)
            ).distinct()
        
        return queryset.order_by('name')

# Vista para crear grupo
class GroupCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Group
    template_name = 'grupos/group_form.html'
    fields = ['name']
    success_url = reverse_lazy('grupos:group_list')
    permission_required = 'auth.add_group'

    def form_valid(self, form):
        messages.success(self.request, "Grupo creado exitosamente.")
        return super().form_valid(form)

# Vista para editar grupo
class GroupUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Group
    template_name = 'grupos/group_form.html'
    fields = ['name']
    success_url = reverse_lazy('grupos:group_list')
    permission_required = 'auth.change_group'

    def form_valid(self, form):
        messages.success(self.request, "Grupo actualizado exitosamente.")
        return super().form_valid(form)

# Vista para eliminar grupo
class GroupDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Group
    template_name = 'grupos/group_confirm_delete.html'
    success_url = reverse_lazy('grupos:group_list')
    permission_required = 'auth.delete_group'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = f'Eliminar grupo {self.object.name}'
        return context

# Vista para gestionar permisos de un grupo
class GroupPermissionsView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Group
    template_name = 'grupos/group_permissions.html'
    fields = []
    permission_required = 'auth.change_group'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        group = self.get_object()
        
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
        return context
    
    def post(self, request, *args, **kwargs):
        group = self.get_object()
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
