from django.contrib.auth.models import Permission, Group

def permissions_context(request):
    """
    Context processor que proporciona información de permisos usando Django estándar.
    Reemplaza el sistema personalizado de roles.
    """
    context = {}
    
    if request.user.is_authenticated:
        # Información del usuario
        context['current_user'] = request.user
        
        # Verificar si es administrador del sistema
        admin_group = Group.objects.filter(name='Admin').first()
        context['is_admin'] = admin_group and request.user in admin_group.user_set.all()
        
        # Grupos del usuario (Django estándar)
        context['user_groups'] = request.user.groups.all()
        context['user_group_names'] = [g.name for g in request.user.groups.all()]
        
        # Permisos del usuario (Django estándar)
        if context['is_admin']:
            # Usuario del grupo Admin tiene todos los permisos
            context['user_permissions'] = Permission.objects.all()
            context['user_permission_codes'] = [p.codename for p in Permission.objects.all()]
        else:
            # Obtener permisos del usuario y sus grupos
            user_permissions = request.user.user_permissions.all()
            group_permissions = Permission.objects.filter(group__user=request.user)
            all_permissions = (user_permissions | group_permissions).distinct()
            
            context['user_permissions'] = all_permissions
            context['user_permission_codes'] = [p.codename for p in all_permissions]
        
        # Verificaciones comunes usando permisos de Django
        context['can_manage_users'] = (
            context['is_admin'] or 
            request.user.is_staff or
            request.user.has_perm('usuarios.add_usuario') or
            request.user.has_perm('usuarios.change_usuario') or
            request.user.has_perm('usuarios.delete_usuario')
        )
        
        context['can_manage_groups'] = (
            context['is_admin'] or 
            request.user.is_staff or
            request.user.has_perm('auth.add_group') or
            request.user.has_perm('auth.change_group') or
            request.user.has_perm('auth.delete_group')
        )
        
        context['can_manage_permissions'] = (
            context['is_admin'] or 
            request.user.is_staff or
            request.user.has_perm('auth.change_permission')
        )
        
        context['can_view_admin_dashboard'] = (
            context['is_admin'] or 
            request.user.is_staff or
            context['can_manage_users'] or
            context['can_manage_groups'] or
            context['can_manage_permissions']
        )
        
        # Permisos específicos para clientes
        context['can_view_cliente'] = request.user.has_perm('clientes.view_cliente')
        context['can_create_cliente'] = request.user.has_perm('clientes.add_cliente')
        context['can_edit_cliente'] = request.user.has_perm('clientes.change_cliente')
        context['can_delete_cliente'] = request.user.has_perm('clientes.delete_cliente')
        
        context['can_view_tipocliente'] = request.user.has_perm('clientes.view_tipocliente')
        context['can_create_tipocliente'] = request.user.has_perm('clientes.add_tipocliente')
        context['can_edit_tipocliente'] = request.user.has_perm('clientes.change_tipocliente')
        context['can_delete_tipocliente'] = request.user.has_perm('clientes.delete_tipocliente')
        
        # Permisos para usuarios
        context['can_view_usuarios'] = request.user.has_perm('usuarios.view_usuario')
        context['can_create_usuarios'] = request.user.has_perm('usuarios.add_usuario')
        context['can_edit_usuarios'] = request.user.has_perm('usuarios.change_usuario')
        context['can_delete_usuarios'] = request.user.has_perm('usuarios.delete_usuario')
        
        # Permisos para grupos
        context['can_view_groups'] = request.user.has_perm('auth.view_group')
        context['can_create_groups'] = request.user.has_perm('auth.add_group')
        context['can_edit_groups'] = request.user.has_perm('auth.change_group')
        context['can_delete_groups'] = request.user.has_perm('auth.delete_group')
        
        # Permisos específicos para monedas
        context['can_view_monedas'] = request.user.has_perm('monedas.view_moneda')
        context['can_create_monedas'] = request.user.has_perm('monedas.add_moneda')
        context['can_edit_monedas'] = request.user.has_perm('monedas.change_moneda')
        
        # Permisos específicos para tasas de cambio
        context['can_view_tasacambio'] = request.user.has_perm('tasa_cambio.view_tasacambio')
        context['can_create_tasacambio'] = request.user.has_perm('tasa_cambio.add_tasacambio')
        context['can_edit_tasacambio'] = request.user.has_perm('tasa_cambio.change_tasacambio')
        
        # Permisos específicos para métodos de pago
        context['can_view_metodopago'] = request.user.has_perm('metodo_pago.view_metodopago')
        context['can_create_metodopago'] = request.user.has_perm('metodo_pago.add_metodopago')
        context['can_edit_metodopago'] = request.user.has_perm('metodo_pago.change_metodopago')
        
        # Permisos específicos para métodos de cobro
        context['can_view_metodocobro'] = request.user.has_perm('metodo_cobro.view_metodocobro')
        context['can_create_metodocobro'] = request.user.has_perm('metodo_cobro.add_metodocobro')
        context['can_edit_metodocobro'] = request.user.has_perm('metodo_cobro.change_metodocobro')
        
        # Permisos específicos para transacciones
        context['can_view_transacciones'] = request.user.has_perm('transacciones.view_transaccion')
        context['can_create_transacciones'] = request.user.has_perm('transacciones.add_transaccion')
        context['can_edit_transacciones'] = request.user.has_perm('transacciones.change_transaccion')
        context['can_delete_transacciones'] = request.user.has_perm('transacciones.delete_transaccion')
        context['can_operate'] = request.user.has_perm('transacciones.can_operate')  # Permiso para comprar/vender
        context['can_view_reporte_transacciones'] = request.user.has_perm('transacciones.view_reporte_transacciones')
        context['can_view_reporte_ganancias'] = request.user.has_perm('transacciones.view_reporte_ganancias')
        
        # Permisos específicos para configuración
        context['can_view_configuracion'] = request.user.has_perm('configuracion.change_configuracionsistema')
        
        # Permisos específicos para tauser
        context['can_view_tauser'] = request.user.has_perm('tauser.view_tauser')
        context['can_create_tauser'] = request.user.has_perm('tauser.add_tauser')
        context['can_edit_tauser'] = request.user.has_perm('tauser.change_tauser')
        context['can_delete_tauser'] = request.user.has_perm('tauser.delete_tauser')
        
        # Permisos específicos para stock
        context['can_view_stock'] = request.user.has_perm('tauser.view_stock')
        context['can_create_stock'] = request.user.has_perm('tauser.add_stock')
        context['can_edit_stock'] = request.user.has_perm('tauser.change_stock')
        context['can_delete_stock'] = request.user.has_perm('tauser.delete_stock')
        context['can_manage_stock'] = request.user.has_perm('tauser.manage_stock')
        
        # Dashboard
        context['can_view_dashboard'] = (
            context['is_admin'] or 
            request.user.is_staff or
            context['can_view_usuarios'] or
            context['can_view_groups'] or
            context['can_view_cliente'] or
            context['can_view_monedas'] or
            context['can_view_tasacambio'] or
            context['can_view_metodopago'] or
            context['can_view_metodocobro'] or
            context['can_view_transacciones'] or
            context['can_view_configuracion'] or
            context['can_view_tauser']
        )
        
    else:
        # Usuario no autenticado
        context['current_user'] = None
        context['is_admin'] = False
        context['user_groups'] = []
        context['user_group_names'] = []
        context['user_permissions'] = []
        context['user_permission_codes'] = []
        context['can_manage_users'] = False
        context['can_manage_groups'] = False
        context['can_manage_permissions'] = False
        context['can_view_admin_dashboard'] = False
        context['can_view_cliente'] = False
        context['can_create_cliente'] = False
        context['can_edit_cliente'] = False
        context['can_delete_cliente'] = False
        context['can_view_tipocliente'] = False
        context['can_create_tipocliente'] = False
        context['can_edit_tipocliente'] = False
        context['can_delete_tipocliente'] = False
        context['can_view_usuarios'] = False
        context['can_create_usuarios'] = False
        context['can_edit_usuarios'] = False
        context['can_delete_usuarios'] = False
        context['can_view_groups'] = False
        context['can_create_groups'] = False
        context['can_edit_groups'] = False
        context['can_delete_groups'] = False
        context['can_view_monedas'] = False
        context['can_create_monedas'] = False
        context['can_edit_monedas'] = False
        context['can_view_tasacambio'] = False
        context['can_create_tasacambio'] = False
        context['can_edit_tasacambio'] = False
        context['can_view_dashboard'] = False
        context['can_view_metodopago'] = False
        context['can_create_metodopago'] = False
        context['can_edit_metodopago'] = False
        context['can_view_metodocobro'] = False
        context['can_create_metodocobro'] = False
        context['can_edit_metodocobro'] = False
        context['can_view_transacciones'] = False
        context['can_create_transacciones'] = False
        context['can_edit_transacciones'] = False
        context['can_delete_transacciones'] = False
        context['can_operate'] = False
        context['can_view_reporte_transacciones'] = False
        context['can_view_reporte_ganancias'] = False
        context['can_view_configuracion'] = False
        context['can_view_tauser'] = False
        context['can_create_tauser'] = False
        context['can_edit_tauser'] = False
        context['can_delete_tauser'] = False
        context['can_view_stock'] = False
        context['can_create_stock'] = False
        context['can_edit_stock'] = False
        context['can_delete_stock'] = False
        context['can_manage_stock'] = False
    return context
