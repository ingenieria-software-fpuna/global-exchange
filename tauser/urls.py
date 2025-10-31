from django.urls import path
from . import views

app_name = 'tauser'

urlpatterns = [
    # URLs para Tausers
    path('', views.TauserListView.as_view(), name='tauser_list'),
    path('crear/', views.TauserCreateView.as_view(), name='tauser_create'),
    path('<int:pk>/', views.TauserDetailView.as_view(), name='tauser_detail'),
    path('<int:pk>/editar/', views.TauserUpdateView.as_view(), name='tauser_update'),
    path('<int:pk>/toggle-status/', views.toggle_tauser_status, name='tauser_toggle_status'),
    
    # URLs para Cargar Stock (solo desde tauser)
    path('<int:pk>/cargar-stock/', views.cargar_stock, name='cargar_stock'),
    path('<int:pk>/historial-stock/', views.historial_stock, name='historial_stock'),
    
    # URLs para denominaciones
    path('denominaciones/<str:moneda_id>/', views.obtener_denominaciones, name='obtener_denominaciones'),
    
    # URLs para Simulador de Cajero Automático
    path('simulador/', views.simulador_cajero, name='simulador_cajero'),
    path('validar-transaccion/', views.validar_transaccion_retiro, name='validar_transaccion_retiro'),
    path('verificar-codigo/', views.verificar_codigo_retiro, name='verificar_codigo_retiro'),
    path('procesar-retiro/', views.procesar_retiro, name='procesar_retiro'),
    path('confirmar-recepcion-divisas/', views.confirmar_recepcion_divisas, name='confirmar_recepcion_divisas'),
]
