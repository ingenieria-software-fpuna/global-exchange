from django.urls import path
from .views import (
    MetodoCobroListView, MetodoCobroCreateView, MetodoCobroUpdateView,
    toggle_metodocobro_status, api_campos_metodo_cobro,
)

app_name = 'metodo_cobro'

urlpatterns = [
    path('', MetodoCobroListView.as_view(), name='metodocobro_list'),
    path('crear/', MetodoCobroCreateView.as_view(), name='metodocobro_create'),
    path('editar/<int:pk>/', MetodoCobroUpdateView.as_view(), name='metodocobro_update'),

    # API AJAX
    path('toggle-status/<int:pk>/', toggle_metodocobro_status, name='toggle_status'),
    path('api/campos/', api_campos_metodo_cobro, name='api_campos_metodo_cobro'),
]