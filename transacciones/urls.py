from django.urls import path
from . import views

app_name = 'transacciones'

urlpatterns = [
    path('comprar/', views.comprar_divisas, name='comprar_divisas'),
    path('iniciar-compra/', views.iniciar_compra, name='iniciar_compra'),
    path('api/validar-limites/', views.api_validar_limites, name='api_validar_limites'),
    path('api/calcular-compra-completa/', views.api_calcular_compra_completa, name='api_calcular_compra_completa'),
    path('resumen/<str:transaccion_id>/', views.resumen_transaccion, name='resumen_transaccion'),
    path('procesar-pago/<str:transaccion_id>/', views.procesar_pago, name='procesar_pago'),
    path('cancelar/<str:transaccion_id>/', views.cancelar_transaccion, name='cancelar_transaccion'),
]