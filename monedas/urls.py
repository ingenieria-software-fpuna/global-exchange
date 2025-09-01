from django.urls import path
from .views import (
    MonedaListView, MonedaCreateView, MonedaUpdateView,
    toggle_moneda_status, moneda_detail_api, dashboard_monedas
)

app_name = 'monedas'

urlpatterns = [
    # Dashboard
    path('dashboard/', dashboard_monedas, name='dashboard'),
    
    # CRUD de monedas
    path('', MonedaListView.as_view(), name='moneda_list'),
    path('crear/', MonedaCreateView.as_view(), name='moneda_create'),
    path('editar/<int:pk>/', MonedaUpdateView.as_view(), name='moneda_update'),
    
    # APIs AJAX
    path('toggle-status/<int:pk>/', toggle_moneda_status, name='toggle_status'),
    path('api/detalle/<int:pk>/', moneda_detail_api, name='moneda_detail_api'),
]
