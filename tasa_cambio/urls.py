from django.urls import path
from .views import (
    TasaCambioListView, TasaCambioCreateView, TasaCambioHistorialView,
    tasacambio_detail_api, dashboard_tasacambio,
    simular_cambio_api,
)

app_name = 'tasa_cambio'

urlpatterns = [
    path('dashboard/', dashboard_tasacambio, name='dashboard'),

    path('', TasaCambioListView.as_view(), name='tasacambio_list'),
    path('crear/', TasaCambioCreateView.as_view(), name='tasacambio_create'),
    path('historial/<int:moneda_id>/', TasaCambioHistorialView.as_view(), name='tasacambio_historial'),

    # APIs AJAX
    path('api/detalle/<int:pk>/', tasacambio_detail_api, name='tasacambio_detail_api'),
    path('api/simular/', simular_cambio_api, name='simular_cambio_api'),
]
