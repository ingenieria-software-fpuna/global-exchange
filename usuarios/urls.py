from django.urls import path
from .views import UsuarioListView, UsuarioCreateView, UsuarioUpdateView, UsuarioDeleteView, toggle_usuario_status

app_name = 'usuarios' 
urlpatterns = [
    path('', UsuarioListView.as_view(), name='user_list'),
    path('usuarios/crear/', UsuarioCreateView.as_view(), name='user_create'),
    path('usuarios/editar/<int:pk>/', UsuarioUpdateView.as_view(), name='user_update'),
    path('usuarios/eliminar/<int:pk>/', UsuarioDeleteView.as_view(), name='user_delete'),
    
    # API AJAX para Usuarios
    path('usuarios/toggle-status/<int:pk>/', toggle_usuario_status, name='toggle_status'),
]


