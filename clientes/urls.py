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
