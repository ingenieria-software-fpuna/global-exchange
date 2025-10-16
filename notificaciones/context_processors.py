"""
Context processors para notificaciones.
"""
from .models import Notificacion


def notificaciones_no_leidas(request):
    """
    Agrega el conteo de notificaciones no leídas al contexto.
    Solo para usuarios con roles Operador o Visitante.
    """
    if request.user.is_authenticated:
        # Verificar si el usuario tiene uno de los roles permitidos
        tiene_permiso = request.user.groups.filter(name__in=['Operador', 'Visitante']).exists()
        
        if tiene_permiso:
            count = Notificacion.objects.filter(
                usuario=request.user,
                leida=False
            ).count()
            return {
                'notificaciones_no_leidas_count': count,
                'puede_ver_notificaciones': True
            }
    
    return {
        'notificaciones_no_leidas_count': 0,
        'puede_ver_notificaciones': False
    }
