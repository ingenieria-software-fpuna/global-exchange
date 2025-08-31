from django.urls import path
from .views import (
    GroupListView, GroupCreateView, GroupUpdateView,
    GroupPermissionsView, PermissionListView, toggle_group_status
)

app_name = 'grupos'

urlpatterns = [
    # URLs para Grupos
    path('', GroupListView.as_view(), name='group_list'),
    path('crear/', GroupCreateView.as_view(), name='group_create'),
    path('editar/<int:pk>/', GroupUpdateView.as_view(), name='group_update'),
    path('permisos/<int:pk>/', GroupPermissionsView.as_view(), name='group_permissions'),
    
    # API AJAX para Grupos
    path('toggle-status/<int:pk>/', toggle_group_status, name='toggle_status'),
    
    # URLs para Permisos
    path('permisos/', PermissionListView.as_view(), name='permission_list'),
]
