from django.urls import path
from .views import (
    GroupListView, GroupCreateView, GroupUpdateView, GroupDeleteView,
    GroupPermissionsView, PermissionListView
)

app_name = 'grupos'

urlpatterns = [
    # URLs para Grupos
    path('', GroupListView.as_view(), name='group_list'),
    path('crear/', GroupCreateView.as_view(), name='group_create'),
    path('editar/<int:pk>/', GroupUpdateView.as_view(), name='group_update'),
    path('eliminar/<int:pk>/', GroupDeleteView.as_view(), name='group_delete'),
    path('permisos/<int:pk>/', GroupPermissionsView.as_view(), name='group_permissions'),
    
    # URLs para Permisos
    path('permisos/', PermissionListView.as_view(), name='permission_list'),
]
