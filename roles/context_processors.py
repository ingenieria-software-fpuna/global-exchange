from .services import RolesService, Permisos


def permissions_context(request):
    """Expone banderas de visibilidad de módulos basadas en permisos del usuario.

    Esto permite ocultar ítems de menú y tarjetas del dashboard según permisos.
    """
    if not getattr(request, 'user', None) or not request.user.is_authenticated:
        return {}

    user = request.user

    can_view_usuarios = RolesService.usuario_tiene_permiso(user, Permisos.USUARIO_LEER)
    can_view_roles = (
        RolesService.usuario_tiene_permiso(user, Permisos.ROL_LEER)
        or RolesService.usuario_tiene_permiso(user, Permisos.PERMISO_LEER)
    )

    can_view_tipocliente = RolesService.usuario_tiene_permiso(user, Permisos.TIPOCLIENTE_LEER)
    can_view_cliente = RolesService.usuario_tiene_permiso(user, Permisos.CLIENTE_LEER)
    
    # Permisos específicos para clientes
    can_create_cliente = RolesService.usuario_tiene_permiso(user, Permisos.CLIENTE_CREAR)
    can_edit_cliente = RolesService.usuario_tiene_permiso(user, Permisos.CLIENTE_EDITAR)
    can_delete_cliente = RolesService.usuario_tiene_permiso(user, Permisos.CLIENTE_ELIMINAR)
    
    # Permisos específicos para tipos de cliente
    can_create_tipocliente = RolesService.usuario_tiene_permiso(user, Permisos.TIPOCLIENTE_CREAR)
    can_edit_tipocliente = RolesService.usuario_tiene_permiso(user, Permisos.TIPOCLIENTE_EDITAR)
    can_delete_tipocliente = RolesService.usuario_tiene_permiso(user, Permisos.TIPOCLIENTE_ELIMINAR)

    return {
        'can_view_usuarios': can_view_usuarios,
        'can_view_roles': can_view_roles,
        'can_view_tipocliente': can_view_tipocliente,
        'can_view_cliente': can_view_cliente,
        'can_create_cliente': can_create_cliente,
        'can_edit_cliente': can_edit_cliente,
        'can_delete_cliente': can_delete_cliente,
        'can_create_tipocliente': can_create_tipocliente,
        'can_edit_tipocliente': can_edit_tipocliente,
        'can_delete_tipocliente': can_delete_tipocliente,
        'can_view_dashboard': RolesService.usuario_tiene_permiso(user, Permisos.DASHBOARD_VER) or RolesService.usuario_es_admin(user),
        'is_admin_role': RolesService.usuario_es_admin(user),
    }
