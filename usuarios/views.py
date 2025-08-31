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