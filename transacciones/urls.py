from django.urls import path
from . import views

app_name = 'transacciones'

urlpatterns = [
    path('mis-transacciones/', views.MisTransaccionesListView.as_view(), name='mis_transacciones'),
    path('comprar/', views.comprar_divisas, name='comprar_divisas'),
    path('iniciar-compra/', views.iniciar_compra, name='iniciar_compra'),
    path('vender/', views.vender_divisas, name='vender_divisas'),
    path('iniciar-venta/', views.iniciar_venta, name='iniciar_venta'),
    path('api/validar-limites/', views.api_validar_limites, name='api_validar_limites'),
    path('api/calcular-compra-completa/', views.api_calcular_compra_completa, name='api_calcular_compra_completa'),
    path('api/calcular-venta-completa/', views.api_calcular_venta_completa, name='api_calcular_venta_completa'),
    path('api/metodos-cobro-por-moneda/', views.api_metodos_cobro_por_moneda, name='api_metodos_cobro_por_moneda'),
    path('resumen/<str:transaccion_id>/', views.resumen_transaccion, name='resumen_transaccion'),
    path('procesar-pago/<str:transaccion_id>/', views.procesar_pago, name='procesar_pago'),
    path('cancelar/<str:transaccion_id>/', views.cancelar_transaccion, name='cancelar_transaccion'),
    path('cancelar-por-expiracion/<str:transaccion_id>/', views.cancelar_por_expiracion, name='cancelar_por_expiracion'),
]