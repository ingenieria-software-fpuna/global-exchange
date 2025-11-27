from django.urls import path
from . import views
from . import views_reportes

app_name = 'transacciones'

urlpatterns = [
    path('mis-transacciones/', views.MisTransaccionesListView.as_view(), name='mis_transacciones'),
    path('comprar/', views.comprar_divisas, name='comprar_divisas'),
    path('iniciar-compra/', views.iniciar_compra, name='iniciar_compra'),
    path('vender/', views.vender_divisas, name='vender_divisas'),
    path('iniciar-venta/', views.iniciar_venta, name='iniciar_venta'),
    path('api/validar-limites/', views.api_validar_limites, name='api_validar_limites'),
    path('api/validar-stock-tauser/', views.api_validar_stock_tauser, name='api_validar_stock_tauser'),
    path('api/calcular-compra-completa/', views.api_calcular_compra_completa, name='api_calcular_compra_completa'),
    path('api/calcular-venta-completa/', views.api_calcular_venta_completa, name='api_calcular_venta_completa'),
    path('api/metodos-cobro-por-moneda/', views.api_metodos_cobro_por_moneda, name='api_metodos_cobro_por_moneda'),
    path('resumen/<str:transaccion_id>/', views.resumen_transaccion, name='resumen_transaccion'),
    path('procesar-pago/<str:transaccion_id>/', views.procesar_pago, name='procesar_pago'),
    path('cancelar/<str:transaccion_id>/', views.cancelar_transaccion, name='cancelar_transaccion'),
    path('cancelar-por-expiracion/<str:transaccion_id>/', views.cancelar_por_expiracion, name='cancelar_por_expiracion'),
    path('verificar-cambio-cotizacion/<str:transaccion_id>/', views.verificar_cambio_cotizacion, name='verificar_cambio_cotizacion'),
    path('crear-con-nueva-cotizacion/<str:transaccion_id>/', views.crear_con_nueva_cotizacion, name='crear_con_nueva_cotizacion'),
    path('cancelar-por-cambio-cotizacion/<str:transaccion_id>/', views.cancelar_por_cambio_cotizacion, name='cancelar_por_cambio_cotizacion'),
    path('descargar-factura/<str:transaccion_id>/<str:tipo_archivo>/', views.descargar_factura, name='descargar_factura'),
    path('reintentar-factura/<str:transaccion_id>/', views.reintentar_factura, name='reintentar_factura'),
    
    # Reportes
    path('reportes/transacciones/', views_reportes.reporte_transacciones, name='reporte_transacciones'),
    path('reportes/ganancias/', views_reportes.reporte_ganancias, name='reporte_ganancias'),
    path('reportes/transacciones/exportar/excel/', views_reportes.exportar_transacciones_excel, name='exportar_transacciones_excel'),
    path('reportes/transacciones/exportar/pdf/', views_reportes.exportar_transacciones_pdf, name='exportar_transacciones_pdf'),
    path('reportes/ganancias/exportar/excel/', views_reportes.exportar_ganancias_excel, name='exportar_ganancias_excel'),
    path('reportes/ganancias/exportar/pdf/', views_reportes.exportar_ganancias_pdf, name='exportar_ganancias_pdf'),
]
