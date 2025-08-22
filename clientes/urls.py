from django.urls import path
from . import views

app_name = 'clientes'

urlpatterns = [
    path('tipos/', views.TipoClienteListView.as_view(), name='tipocliente_list'),
    path('tipos/crear/', views.TipoClienteCreateView.as_view(), name='tipocliente_create'),
    path('tipos/<int:pk>/editar/', views.TipoClienteUpdateView.as_view(), name='tipocliente_update'),
    path('tipos/<int:pk>/eliminar/', views.TipoClienteDeleteView.as_view(), name='tipocliente_delete'),
]
