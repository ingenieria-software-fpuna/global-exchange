
from django.urls import path
from . import views

app_name = 'auth'

urlpatterns = [
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('verify-code/', views.verify_code_view, name='verify_code'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('registro/', views.registro_view, name='registro'),
    path('verificar-registro/', views.verificar_registro_view, name='verificar_registro'),
    path('reenviar-codigo/', views.reenviar_codigo_view, name='reenviar_codigo'),
]