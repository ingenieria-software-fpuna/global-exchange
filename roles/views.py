# roles/views.py
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib import messages
from .models import Rol, Permiso, Modulo
from .forms import RolForm, PermisoForm, ModuloForm
from .mixins import PermisoRequeridoMixin
from .services import Permisos

# Vistas para Roles
class RolListView(PermisoRequeridoMixin, ListView):
    model = Rol
    template_name = 'roles/rol_list.html'
    context_object_name = 'roles'
    permiso_requerido = Permisos.ROL_LEER

class RolCreateView(PermisoRequeridoMixin, CreateView):
    model = Rol
    form_class = RolForm
    template_name = 'roles/rol_form.html'
    success_url = reverse_lazy('roles:rol_list')
    permiso_requerido = Permisos.ROL_CREAR
    def form_valid(self, form):
        messages.success(self.request, "Rol creado exitosamente.")
        return super().form_valid(form)

class RolUpdateView(PermisoRequeridoMixin, UpdateView):
    model = Rol
    form_class = RolForm
    template_name = 'roles/rol_form.html'
    success_url = reverse_lazy('roles:rol_list')
    permiso_requerido = Permisos.ROL_EDITAR
    def form_valid(self, form):
        messages.success(self.request, "Rol actualizado exitosamente.")
        return super().form_valid(form)

class RolDeleteView(PermisoRequeridoMixin, DeleteView):
    model = Rol
    template_name = 'roles/rol_confirm_delete.html'
    success_url = reverse_lazy('roles:rol_list')
    permiso_requerido = Permisos.ROL_ELIMINAR
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = f"Eliminar Rol {self.object.nombre}"
        return context

# Vistas para Permisos
class PermisoListView(PermisoRequeridoMixin, ListView):
    model = Permiso
    template_name = 'roles/permiso_list.html'
    context_object_name = 'permisos'
    permiso_requerido = Permisos.PERMISO_LEER

class PermisoCreateView(PermisoRequeridoMixin, CreateView):
    model = Permiso
    form_class = PermisoForm
    template_name = 'roles/permiso_form.html'
    success_url = reverse_lazy('roles:permiso_list')
    permiso_requerido = Permisos.PERMISO_CREAR
    def form_valid(self, form):
        messages.success(self.request, "Permiso creado exitosamente.")
        return super().form_valid(form)

class PermisoUpdateView(PermisoRequeridoMixin, UpdateView):
    model = Permiso
    form_class = PermisoForm
    template_name = 'roles/permiso_form.html'
    success_url = reverse_lazy('roles:permiso_list')
    permiso_requerido = Permisos.PERMISO_EDITAR
    def form_valid(self, form):
        messages.success(self.request, "Permiso actualizado exitosamente.")
        return super().form_valid(form)

class PermisoDeleteView(PermisoRequeridoMixin, DeleteView):
    model = Permiso
    template_name = 'roles/permiso_confirm_delete.html'
    success_url = reverse_lazy('roles:permiso_list')
    permiso_requerido = Permisos.PERMISO_ELIMINAR
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = f"Eliminar Permiso {self.object.nombre}"
        return context

# Vistas para Módulos (CRUD completo por si no lo tienes)
class ModuloListView(PermisoRequeridoMixin, ListView):
    model = Modulo
    template_name = 'roles/modulo_list.html'
    context_object_name = 'modulos'
    permiso_requerido = Permisos.PERMISO_LEER # Se asume que leer permisos incluye leer modulos

class ModuloCreateView(PermisoRequeridoMixin, CreateView):
    model = Modulo
    form_class = ModuloForm
    template_name = 'roles/modulo_form.html'
    success_url = reverse_lazy('roles:modulo_list')
    permiso_requerido = Permisos.PERMISO_CREAR
    def form_valid(self, form):
        messages.success(self.request, "Módulo creado exitosamente.")
        return super().form_valid(form)

class ModuloUpdateView(PermisoRequeridoMixin, UpdateView):
    model = Modulo
    form_class = ModuloForm
    template_name = 'roles/modulo_form.html'
    success_url = reverse_lazy('roles:modulo_list')
    permiso_requerido = Permisos.PERMISO_EDITAR
    def form_valid(self, form):
        messages.success(self.request, "Módulo actualizado exitosamente.")
        return super().form_valid(form)

class ModuloDeleteView(PermisoRequeridoMixin, DeleteView):
    model = Modulo
    template_name = 'roles/modulo_confirm_delete.html'
    success_url = reverse_lazy('roles:modulo_list')
    permiso_requerido = Permisos.PERMISO_ELIMINAR
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = f"Eliminar Módulo {self.object.nombre}"
        return context