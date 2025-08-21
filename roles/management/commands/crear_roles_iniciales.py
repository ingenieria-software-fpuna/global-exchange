# global-exchange/apps/roles/management/commands/initial_roles_permissions.py
from django.core.management.base import BaseCommand
from roles.models import Modulo, Permiso, Rol
from roles.services import Permisos as ConstantesPermisos

class Command(BaseCommand):
    help = 'Crea los roles y permisos iniciales del sistema.'
    
    def handle(self, *args, **options):
        # Crear módulos si no existen
        modulos_data = [
            {'nombre': 'Usuarios', 'codigo': 'usuarios', 'orden': 1},
            {'nombre': 'Roles', 'codigo': 'roles', 'orden': 2},
            {'nombre': 'Dashboard', 'codigo': 'dashboard', 'orden': 3},
        ]
        
        for modulo_data in modulos_data:
            Modulo.objects.get_or_create(codigo=modulo_data['codigo'], defaults=modulo_data)
        self.stdout.write(self.style.SUCCESS("Módulos iniciales creados o actualizados."))

        # Obtener los módulos creados
        modulo_usuarios = Modulo.objects.get(codigo='usuarios')
        modulo_roles = Modulo.objects.get(codigo='roles')
        modulo_dashboard = Modulo.objects.get(codigo='dashboard')

        # Definir permisos de forma explícita
        permisos_a_crear = [
            # Permisos de Usuarios
            {'nombre': 'Leer Usuarios', 'codigo': ConstantesPermisos.USUARIO_LEER, 'tipo': 'read', 'modulo': modulo_usuarios},
            {'nombre': 'Crear Usuarios', 'codigo': ConstantesPermisos.USUARIO_CREAR, 'tipo': 'create', 'modulo': modulo_usuarios},
            {'nombre': 'Editar Usuarios', 'codigo': ConstantesPermisos.USUARIO_EDITAR, 'tipo': 'update', 'modulo': modulo_usuarios},
            {'nombre': 'Eliminar Usuarios', 'codigo': ConstantesPermisos.USUARIO_ELIMINAR, 'tipo': 'delete', 'modulo': modulo_usuarios},

            # Permisos de Roles y Permisos
            {'nombre': 'Leer Roles', 'codigo': ConstantesPermisos.ROL_LEER, 'tipo': 'read', 'modulo': modulo_roles},
            {'nombre': 'Crear Roles', 'codigo': ConstantesPermisos.ROL_CREAR, 'tipo': 'create', 'modulo': modulo_roles},
            {'nombre': 'Editar Roles', 'codigo': ConstantesPermisos.ROL_EDITAR, 'tipo': 'update', 'modulo': modulo_roles},
            {'nombre': 'Eliminar Roles', 'codigo': ConstantesPermisos.ROL_ELIMINAR, 'tipo': 'delete', 'modulo': modulo_roles},
            {'nombre': 'Leer Permisos', 'codigo': ConstantesPermisos.PERMISO_LEER, 'tipo': 'read', 'modulo': modulo_roles},
            {'nombre': 'Crear Permisos', 'codigo': ConstantesPermisos.PERMISO_CREAR, 'tipo': 'create', 'modulo': modulo_roles},
            {'nombre': 'Editar Permisos', 'codigo': ConstantesPermisos.PERMISO_EDITAR, 'tipo': 'update', 'modulo': modulo_roles},
            {'nombre': 'Eliminar Permisos', 'codigo': ConstantesPermisos.PERMISO_ELIMINAR, 'tipo': 'delete', 'modulo': modulo_roles},
            
            # Permisos del Dashboard (ejemplo de permiso único)
            {'nombre': 'Ver Dashboard', 'codigo': 'dashboard_ver', 'tipo': 'read', 'modulo': modulo_dashboard},
        ]

        # Crear los objetos de Permiso
        for p_data in permisos_a_crear:
            Permiso.objects.get_or_create(codigo=p_data['codigo'], defaults=p_data)
        self.stdout.write(self.style.SUCCESS("Permisos iniciales creados o actualizados."))

        # Crear o actualizar el rol de Administrador
        admin_rol, created = Rol.objects.get_or_create(
            codigo='admin',
            defaults={
                'nombre': 'Administrador',
                'descripcion': 'Rol con todos los permisos del sistema',
                'es_admin': True,
                'activo': True,
            }
        )
        if created:
            self.stdout.write("Rol Administrador creado.")
        
        # Asignar todos los permisos activos al rol de Administrador
        todos_los_permisos = Permiso.objects.filter(activo=True)
        admin_rol.permisos.set(todos_los_permisos)
        self.stdout.write(self.style.SUCCESS(f"Todos los permisos han sido asignados al rol '{admin_rol.nombre}'."))