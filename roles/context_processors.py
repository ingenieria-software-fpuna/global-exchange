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

    can_view_tipocliente = False

    return {
        'can_view_usuarios': can_view_usuarios,
        'can_view_roles': can_view_roles,
        'can_view_tipocliente': can_view_tipocliente,
        'can_view_dashboard': RolesService.usuario_tiene_permiso(user, Permisos.DASHBOARD_VER) or RolesService.usuario_es_admin(user),
        'is_admin_role': RolesService.usuario_es_admin(user),
    }
