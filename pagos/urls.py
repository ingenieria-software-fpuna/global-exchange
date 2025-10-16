from django.urls import path
from . import views

app_name = 'pagos'

urlpatterns = [
    # Vistas de procesamiento de pagos
    path('<str:transaccion_id>/billetera/', views.pago_billetera_electronica, name='pago_billetera_electronica'),
    path('<str:transaccion_id>/tarjeta/', views.pago_tarjeta_debito, name='pago_tarjeta_debito'),
    path('<str:transaccion_id>/tarjeta-credito-local/', views.pago_tarjeta_credito_local, name='pago_tarjeta_credito_local'),
    path('<str:transaccion_id>/transferencia/', views.pago_transferencia_bancaria, name='pago_transferencia_bancaria'),
    
    # Webhook para notificaciones de la pasarela
    path('webhook/', views.webhook_pago, name='webhook_pago'),
]