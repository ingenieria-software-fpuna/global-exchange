# apps/roles/services.py
from django.db import transaction
from django.core.exceptions import ValidationError
from .models import Rol, Permiso, UsuarioRol, RolPermiso

class RolesService:
    """Servicio para manejar la lógica de negocio de roles"""
    
    @staticmethod
    def asignar_rol_usuario(usuario, rol, asignado_por=None):
        """Asigna un rol a un usuario"""
        with transaction.atomic():
            usuario_rol, created = UsuarioRol.objects.get_or_create(
                usuario=usuario,
                rol=rol,
                defaults={
                    'asignado_por': asignado_por or 'sistema',
                    'activo': True
                }
            )
            
            if not created and not usuario_rol.activo:
                usuario_rol.activo = True
                usuario_rol.save()
            
            return usuario_rol
    
    @staticmethod
    def remover_rol_usuario(usuario, rol):
        """Remueve un rol de un usuario"""
        try:
            usuario_rol = UsuarioRol.objects.get(usuario=usuario, rol=rol)
            usuario_rol.activo = False
            usuario_rol.save()
            return True
        except UsuarioRol.DoesNotExist:
            return False
    
    @staticmethod
    def usuario_tiene_permiso(usuario, codigo_permiso):
        """Verifica si un usuario tiene un permiso específico"""
        roles_activos = UsuarioRol.objects.filter(
            usuario=usuario,
            activo=True,
            rol__activo=True
        ).select_related('rol')
        
        for usuario_rol in roles_activos:
            if usuario_rol.rol.tiene_permiso(codigo_permiso):
                return True
        
        return False
    
    @staticmethod
    def obtener_permisos_usuario(usuario):
        """Obtiene todos los permisos de un usuario"""
        roles_activos = UsuarioRol.objects.filter(
            usuario=usuario,
            activo=True,
            rol__activo=True
        ).select_related('rol')
        
        permisos = set()
        for usuario_rol in roles_activos:
            if usuario_rol.rol.es_admin:
                # Si es admin, tiene todos los permisos
                return Permiso.objects.filter(activo=True)
            else:
                permisos.update(
                    usuario_rol.rol.permisos.filter(activo=True).values_list('codigo', flat=True)
                )
        
        return Permiso.objects.filter(codigo__in=permisos, activo=True)
    
    @staticmethod
    def crear_rol_con_permisos(nombre, codigo, permisos_codigos, descripcion='', asignado_por=None):
        """Crea un rol y le asigna permisos"""
        with transaction.atomic():
            rol = Rol.objects.create(
                nombre=nombre,
                codigo=codigo,
                descripcion=descripcion
            )
            
            permisos = Permiso.objects.filter(codigo__in=permisos_codigos, activo=True)
            for permiso in permisos:
                RolPermiso.objects.create(
                    rol=rol,
                    permiso=permiso,
                    asignado_por=asignado_por or 'sistema'
                )
            
            return rol