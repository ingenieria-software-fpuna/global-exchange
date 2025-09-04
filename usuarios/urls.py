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


