from roles.services import RolesService

def permisos_cliente(request):
    """Procesador de contexto que proporciona permisos de cliente a las plantillas"""
    if request.user.is_authenticated:
        return {
            'perms': {
                'clientes': {
                    'tipocliente_leer': RolesService.usuario_tiene_permiso(request.user, 'tipocliente_leer'),
                    'tipocliente_crear': RolesService.usuario_tiene_permiso(request.user, 'tipocliente_crear'),
                    'tipocliente_editar': RolesService.usuario_tiene_permiso(request.user, 'tipocliente_editar'),
                    'tipocliente_eliminar': RolesService.usuario_tiene_permiso(request.user, 'tipocliente_eliminar'),
                }
            }
        }
    return {'perms': {}}
