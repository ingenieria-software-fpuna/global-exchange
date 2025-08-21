# apps/roles/serializers.py
from rest_framework import serializers
from .models import Modulo, Permiso, Rol, UsuarioRol

class ModuloSerializer(serializers.ModelSerializer):
    class Meta:
        model = Modulo
        fields = ['id', 'nombre', 'descripcion', 'codigo', 'activo', 'orden']

class PermisoSerializer(serializers.ModelSerializer):
    modulo_nombre = serializers.CharField(source='modulo.nombre', read_only=True)
    
    class Meta:
        model = Permiso
        fields = ['id', 'nombre', 'codigo', 'descripcion', 'tipo', 'modulo', 'modulo_nombre', 'activo']

class RolSerializer(serializers.ModelSerializer):
    permisos = PermisoSerializer(many=True, read_only=True)
    count_permisos = serializers.SerializerMethodField()
    
    class Meta:
        model = Rol
        fields = ['id', 'nombre', 'descripcion', 'codigo', 'es_admin', 'activo', 'permisos', 'count_permisos']
    
    def get_count_permisos(self, obj):
        return obj.permisos.count()

class RolSimpleSerializer(serializers.ModelSerializer):
    """Serializer simplificado para listados"""
    class Meta:
        model = Rol
        fields = ['id', 'nombre', 'codigo', 'es_admin']

class UsuarioRolSerializer(serializers.ModelSerializer):
    rol_nombre = serializers.CharField(source='rol.nombre', read_only=True)
    usuario_email = serializers.CharField(source='usuario.email', read_only=True)
    
    class Meta:
        model = UsuarioRol
        fields = ['id', 'usuario', 'usuario_email', 'rol', 'rol_nombre', 'activo', 'fecha_asignacion']