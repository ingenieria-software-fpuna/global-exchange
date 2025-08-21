# apps/roles/mixins.py
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from .services import RolesService

class PermisoRequeridoMixin:
    """Mixin para CBV que requiere permisos"""
    permiso_requerido = None
    
    def dispatch(self, request, *args, **kwargs):
        if not self.permiso_requerido:
            raise ValueError("Debe especificar 'permiso_requerido'")
        
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        
        if not RolesService.usuario_tiene_permiso(request.user, self.permiso_requerido):
            return self.handle_no_permission()
        
        return super().dispatch(request, *args, **kwargs)
    
    def handle_no_permission(self):
        is_ajax = self.request.META.get('HTTP_X_REQUESTED_WITH') == 'XMLHttpRequest'

        if is_ajax or getattr(self.request, 'content_type', '') == 'application/json':
            return JsonResponse({
                'error': 'No tienes permisos para realizar esta acción'
            }, status=403)
        raise PermissionDenied("No tienes permisos suficientes")