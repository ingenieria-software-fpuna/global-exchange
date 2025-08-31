from django.contrib.auth.backends import ModelBackend
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from grupos.models import Grupo


class GrupoActivoBackend(ModelBackend):
    """
    Backend de autenticación personalizado que considera solo los permisos
    de grupos activos al verificar permisos de usuario.
    """
    
    def get_user_permissions(self, user_obj, obj=None):
        """
        Obtiene los permisos directos del usuario (no a través de grupos).
        """
        return super().get_user_permissions(user_obj, obj)
    
    def get_group_permissions(self, user_obj, obj=None):
        """
        Obtiene los permisos del usuario a través de grupos, pero solo
        considera grupos activos.
        """
        if not user_obj.is_active or user_obj.is_anonymous:
            return set()
        
        # Obtener todos los grupos del usuario
        user_groups = user_obj.groups.all()
        
        # Filtrar solo grupos activos usando nuestro modelo personalizado
        grupos_activos = []
        for group in user_groups:
            try:
                grupo_extension = Grupo.objects.get(group=group)
                if grupo_extension.es_activo:
                    grupos_activos.append(group)
            except Grupo.DoesNotExist:
                # Si no existe la extensión, considerar el grupo como activo por defecto
                # (para compatibilidad con grupos creados antes de la migración)
                grupos_activos.append(group)
        
        # Obtener permisos solo de grupos activos
        permissions = set()
        for group in grupos_activos:
            permissions.update(group.permissions.all())
        
        return permissions
    
    def get_all_permissions(self, user_obj, obj=None):
        """
        Obtiene todos los permisos del usuario (directos + de grupos activos).
        """
        if not user_obj.is_active or user_obj.is_anonymous:
            return set()
        
        # Permisos directos del usuario
        user_permissions = self.get_user_permissions(user_obj, obj)
        
        # Permisos de grupos activos
        group_permissions = self.get_group_permissions(user_obj, obj)
        
        # Combinar ambos conjuntos
        all_permissions = user_permissions | group_permissions
        
        return all_permissions
    
    def has_perm(self, user_obj, perm, obj=None):
        """
        Verifica si el usuario tiene un permiso específico.
        Solo considera permisos de grupos activos.
        """
        if not user_obj.is_active:
            return False
        
        # Verificar permisos directos del usuario
        if super().has_perm(user_obj, perm, obj):
            return True
        
        # Verificar permisos de grupos activos
        all_permissions = self.get_all_permissions(user_obj, obj)
        
        # Convertir el permiso a string si es un objeto Permission
        if hasattr(perm, 'codename'):
            perm_str = f"{perm.content_type.app_label}.{perm.codename}"
        else:
            perm_str = perm
        
        # Verificar si el permiso está en la lista de permisos del usuario
        for permission in all_permissions:
            if f"{permission.content_type.app_label}.{permission.codename}" == perm_str:
                return True
        
        return False
    
    def has_module_perms(self, user_obj, app_label):
        """
        Verifica si el usuario tiene permisos en un módulo específico.
        Solo considera permisos de grupos activos.
        """
        if not user_obj.is_active:
            return False
        
        all_permissions = self.get_all_permissions(user_obj)
        
        # Verificar si hay algún permiso para este módulo
        for permission in all_permissions:
            if permission.content_type.app_label == app_label:
                return True
        
        return False
