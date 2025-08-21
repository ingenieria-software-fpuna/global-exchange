# apps/roles/decorators.py
from functools import wraps
from django.http import JsonResponse
from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required
from .services import RolesService

def requiere_permiso(codigo_permiso):
    """Decorador que requiere un permiso específico"""
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            if not RolesService.usuario_tiene_permiso(request.user, codigo_permiso):
                if request.is_ajax() or request.content_type == 'application/json':
                    return JsonResponse({
                        'error': 'No tienes permisos para realizar esta acción'
                    }, status=403)
                raise PermissionDenied("No tienes permisos para acceder a esta página")
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator

def requiere_rol(codigo_rol):
    """Decorador que requiere un rol específico"""
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            tiene_rol = UsuarioRol.objects.filter(
                usuario=request.user,
                rol__codigo=codigo_rol,
                activo=True,
                rol__activo=True
            ).exists()
            
            if not tiene_rol:
                if request.is_ajax() or request.content_type == 'application/json':
                    return JsonResponse({
                        'error': f'Necesitas el rol {codigo_rol} para realizar esta acción'
                    }, status=403)
                raise PermissionDenied("No tienes el rol necesario")
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator