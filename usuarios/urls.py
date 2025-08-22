from django.urls import path
from .views import UsuarioListView, UsuarioCreateView, UsuarioUpdateView, UsuarioDeleteView

app_name = 'usuarios' 
urlpatterns = [
    path('', UsuarioListView.as_view(), name='user_list'),
    path('usuarios/crear/', UsuarioCreateView.as_view(), name='user_create'),
    path('usuarios/editar/<int:pk>/', UsuarioUpdateView.as_view(), name='user_update'),
    path('usuarios/eliminar/<int:pk>/', UsuarioDeleteView.as_view(), name='user_delete'),
]


