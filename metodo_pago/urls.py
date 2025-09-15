from django.urls import path
from .views import (
    MetodoPagoListView, MetodoPagoCreateView, MetodoPagoUpdateView,
    toggle_metodopago_status,
)

app_name = 'metodo_pago'

urlpatterns = [
    path('', MetodoPagoListView.as_view(), name='metodopago_list'),
    path('crear/', MetodoPagoCreateView.as_view(), name='metodopago_create'),
    path('editar/<int:pk>/', MetodoPagoUpdateView.as_view(), name='metodopago_update'),

    # API AJAX
    path('toggle-status/<int:pk>/', toggle_metodopago_status, name='toggle_status'),
]

