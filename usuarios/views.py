from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib import messages
from django.contrib.auth import get_user_model

from roles.mixins import PermisoRequeridoMixin
from roles.services import Permisos
from .forms import UsuarioCreationForm, UsuarioUpdateForm

Usuario = get_user_model()

# Vista para listar usuarios
class UsuarioListView(PermisoRequeridoMixin, ListView):
    model = Usuario
    template_name = 'usuarios/user_list.html'
    context_object_name = 'usuarios'
    permiso_requerido = Permisos.USUARIO_LEER

# Vista para crear un nuevo usuario
class UsuarioCreateView(PermisoRequeridoMixin, CreateView):
    model = Usuario
    form_class = UsuarioCreationForm
    template_name = 'usuarios/user_form.html'
    success_url = reverse_lazy('usuarios:user_list')
    permiso_requerido = Permisos.USUARIO_CREAR

    def form_valid(self, form):
        messages.success(self.request, "Usuario creado exitosamente.")
        return super().form_valid(form)

# Vista para actualizar un usuario
class UsuarioUpdateView(PermisoRequeridoMixin, UpdateView):
    model = Usuario
    form_class = UsuarioUpdateForm
    template_name = 'usuarios/user_form.html'
    success_url = reverse_lazy('usuarios:user_list')
    permiso_requerido = Permisos.USUARIO_EDITAR

    def form_valid(self, form):
        messages.success(self.request, "Usuario actualizado exitosamente.")
        return super().form_valid(form)

# Vista para eliminar un usuario
class UsuarioDeleteView(PermisoRequeridoMixin, DeleteView):
    model = Usuario
    template_name = 'usuarios/user_confirm_delete.html'
    success_url = reverse_lazy('usuarios:user_list')
    permiso_requerido = Permisos.USUARIO_ELIMINAR

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = f'Eliminar usuario {self.object.email}'
        return context