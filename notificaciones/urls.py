"""
URLs para el módulo de notificaciones.
"""
from django.urls import path
from . import views

app_name = 'notificaciones'

urlpatterns = [
    path('', views.lista_notificaciones, name='lista'),
    path('recientes/', views.notificaciones_recientes, name='recientes'),
    path('preferencias/', views.preferencias_notificaciones, name='preferencias'),
    path('marcar-leida/<int:pk>/', views.marcar_leida, name='marcar_leida'),
    path('marcar-todas-leidas/', views.marcar_todas_leidas, name='marcar_todas_leidas'),
    path('contar-no-leidas/', views.contar_no_leidas, name='contar_no_leidas'),
    path('eliminar/<int:pk>/', views.eliminar_notificacion, name='eliminar'),
]
