from django.core.management.base import BaseCommand
from roles.models import Modulo, Permiso, Rol
from roles.services import RolesService

class Command(BaseCommand):
    help = 'Crea los roles y permisos iniciales del sistema'
    
    def handle(self, *args, **options):
        # Crear módulos
        modulos_data = [
            {'nombre': 'Usuarios', 'codigo': 'usuarios', 'orden': 1},
            {'nombre': 'Roles', 'codigo': 'roles', 'orden': 2},
            {'nombre': 'Dashboard', 'codigo': 'dashboard', 'orden': 3},
        ]
        
        for modulo_data in modulos_data:
            modulo, created = Modulo.objects.get_or_create(
                codigo=modulo_data['codigo'],
                defaults=modulo_data
            )
            if created:
                self.stdout.write(f"Módulo creado: {modulo.nombre}")
        
        # Crear permisos básicos para cada módulo
        permisos_base = ['create', 'read', 'update', 'delete']
        
        for modulo in Modulo.objects.all():
            for tipo_permiso in permisos_base:
                codigo = f"{modulo.codigo}_{tipo_permiso}"
                permiso, created = Permiso.objects.get_or_create(
                    codigo=codigo,
                    modulo=modulo,
                    defaults={
                        'nombre': f"{tipo_permiso.title()} {modulo.nombre}",
                        'tipo': tipo_permiso,
                    }
                )
                if created:
                    self.stdout.write(f"Permiso creado: {permiso.codigo}")
        
        # Crear rol de administrador
        admin_rol, created = Rol.objects.get_or_create(
            codigo='admin',
            defaults={
                'nombre': 'Administrador',
                'descripcion': 'Rol con todos los permisos del sistema',
                'es_admin': True,
            }
        )
        
        if created:
            self.stdout.write("Rol Administrador creado")
        
        self.stdout.write(self.style.SUCCESS('Roles y permisos iniciales creados exitosamente'))