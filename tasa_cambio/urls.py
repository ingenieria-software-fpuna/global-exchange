from django.urls import path
from .views import (
    TasaCambioListView, TasaCambioCreateView,
    toggle_tasacambio_status, tasacambio_detail_api, dashboard_tasacambio
)

app_name = 'tasa_cambio'

urlpatterns = [
    path('dashboard/', dashboard_tasacambio, name='dashboard'),
    
    path('', TasaCambioListView.as_view(), name='tasacambio_list'),
    path('crear/', TasaCambioCreateView.as_view(), name='tasacambio_create'),
    
    # APIs AJAX
    path('toggle-status/<int:pk>/', toggle_tasacambio_status, name='toggle_status'),
    path('api/detalle/<int:pk>/', tasacambio_detail_api, name='tasacambio_detail_api'),
]
