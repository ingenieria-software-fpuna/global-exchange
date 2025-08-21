# # apps/roles/urls.py
# from django.urls import path, include
# from rest_framework.routers import DefaultRouter
# from . import views

# # Router para ViewSets
# router = DefaultRouter()
# router.register(r'modulos', views.ModuloViewSet)
# router.register(r'permisos', views.PermisoViewSet)
# router.register(r'roles', views.RolViewSet)
# router.register(r'usuario-roles', views.UsuarioRolViewSet)

# app_name = 'roles'

# urlpatterns = [
#     # URLs del router
#     path('api/', include(router.urls)),
    
#     # URLs de funciones específicas
#     path('api/mis-permisos/', views.mis_permisos, name='mis-permisos'),
#     path('api/mis-roles/', views.mis_roles, name='mis-roles'),
#     path('api/asignar-rol/', views.asignar_rol_usuario, name='asignar-rol'),
#     path('api/remover-rol/', views.remover_rol_usuario, name='remover-rol'),
#     path('api/estadisticas/', views.estadisticas_roles, name='estadisticas'),
#     path('api/clonar-rol/', views.clonar_rol, name='clonar-rol'),
# ]

# roles/urls.py
from django.urls import path
from .views import (
    RolListView, RolCreateView, RolUpdateView, RolDeleteView,
    PermisoListView, PermisoCreateView, PermisoUpdateView, PermisoDeleteView,
    ModuloListView, ModuloCreateView, ModuloUpdateView, ModuloDeleteView
)

app_name = 'roles'

urlpatterns = [
    # URLs para Roles
    path('roles/', RolListView.as_view(), name='rol_list'),
    path('roles/crear/', RolCreateView.as_view(), name='rol_create'),
    path('roles/editar/<int:pk>/', RolUpdateView.as_view(), name='rol_update'),
    path('roles/eliminar/<int:pk>/', RolDeleteView.as_view(), name='rol_delete'),

    # URLs para Permisos
    path('permisos/', PermisoListView.as_view(), name='permiso_list'),
    path('permisos/crear/', PermisoCreateView.as_view(), name='permiso_create'),
    path('permisos/editar/<int:pk>/', PermisoUpdateView.as_view(), name='permiso_update'),
    path('permisos/eliminar/<int:pk>/', PermisoDeleteView.as_view(), name='permiso_delete'),

    # URLs para Módulos
    path('modulos/', ModuloListView.as_view(), name='modulo_list'),
    path('modulos/crear/', ModuloCreateView.as_view(), name='modulo_create'),
    path('modulos/editar/<int:pk>/', ModuloUpdateView.as_view(), name='modulo_update'),
    path('modulos/eliminar/<int:pk>/', ModuloDeleteView.as_view(), name='modulo_delete'),
]