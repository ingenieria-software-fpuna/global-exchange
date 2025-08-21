# apps/roles/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Router para ViewSets
router = DefaultRouter()
router.register(r'modulos', views.ModuloViewSet)
router.register(r'permisos', views.PermisoViewSet)
router.register(r'roles', views.RolViewSet)
router.register(r'usuario-roles', views.UsuarioRolViewSet)

app_name = 'roles'

urlpatterns = [
    # URLs del router
    path('api/', include(router.urls)),
    
    # URLs de funciones específicas
    path('api/mis-permisos/', views.mis_permisos, name='mis-permisos'),
    path('api/mis-roles/', views.mis_roles, name='mis-roles'),
    path('api/asignar-rol/', views.asignar_rol_usuario, name='asignar-rol'),
    path('api/remover-rol/', views.remover_rol_usuario, name='remover-rol'),
    path('api/estadisticas/', views.estadisticas_roles, name='estadisticas'),
    path('api/clonar-rol/', views.clonar_rol, name='clonar-rol'),
]

