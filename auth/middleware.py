from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse


class UsuarioActivoMiddleware:
    """
    Middleware que verifica si el usuario autenticado está activo (es_activo=True).
    Si no está activo, lo redirige al login con un mensaje de error.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Lista de URLs que no requieren verificación de usuario activo
        excluded_paths = [
            '/auth/login/',
            '/auth/logout/',
            '/auth/registro/',
            '/auth/verificar-registro/',
            '/auth/verify-code/',
            '/welcome/',
            '/admin/',  # Permitir acceso al admin incluso si el usuario está inactivo
        ]
        
        # Verificar si la ruta actual está excluida
        current_path = request.path
        is_excluded = any(current_path.startswith(path) for path in excluded_paths)
        
        # Solo verificar si el usuario está autenticado y la ruta no está excluida
        if (request.user.is_authenticated and 
            not is_excluded and 
            hasattr(request.user, 'es_activo') and 
            not request.user.es_activo):
            
            # Cerrar sesión del usuario inactivo
            from django.contrib.auth import logout
            logout(request)
            
            # Mostrar mensaje de error
            messages.error(request, 'Tu cuenta está desactivada. Contacta al administrador.')
            
            # Redirigir al login
            return redirect('auth:login')
        
        response = self.get_response(request)
        return response
