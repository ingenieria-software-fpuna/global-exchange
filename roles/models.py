from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError

class Modulo(models.Model):
    """Representa los diferentes módulos del sistema"""
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True)
    codigo = models.CharField(max_length=50, unique=True)
    activo = models.BooleanField(default=True)
    orden = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'roles_modulos'
        ordering = ['orden', 'nombre']
        verbose_name = 'Módulo'
        verbose_name_plural = 'Módulos'
    
    def __str__(self):
        return self.nombre

class Permiso(models.Model):
    """Permisos específicos del sistema"""
    TIPOS_PERMISO = [
        ('create', 'Crear'),
        ('read', 'Leer'),
        ('update', 'Actualizar'),
        ('delete', 'Eliminar'),
        ('custom', 'Personalizado'),
    ]
    
    nombre = models.CharField(max_length=100)
    codigo = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True)
    tipo = models.CharField(max_length=20, choices=TIPOS_PERMISO)
    modulo = models.ForeignKey(Modulo, on_delete=models.CASCADE, related_name='permisos')
    activo = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'roles_permisos'
        ordering = ['modulo', 'tipo', 'nombre']
        verbose_name = 'Permiso'
        verbose_name_plural = 'Permisos'
        unique_together = ['codigo', 'modulo']
    
    def __str__(self):
        return f"{self.modulo.nombre} - {self.nombre}"

class Rol(models.Model):
    """Roles del sistema"""
    nombre = models.CharField(max_length=100, unique=True)
    descripcion = models.TextField(blank=True)
    codigo = models.CharField(max_length=50, unique=True)
    es_admin = models.BooleanField(default=False, help_text="Rol con todos los permisos")
    activo = models.BooleanField(default=True)
    
    # Permisos asignados al rol
    permisos = models.ManyToManyField(Permiso, through='RolPermiso', related_name='roles')
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'roles_roles'
        ordering = ['nombre']
        verbose_name = 'Rol'
        verbose_name_plural = 'Roles'
    
    def __str__(self):
        return self.nombre
    
    def clean(self):
        if self.es_admin and not self.activo:
            raise ValidationError("Un rol administrador no puede estar inactivo")
    
    def tiene_permiso(self, codigo_permiso):
        """Verifica si el rol tiene un permiso específico"""
        if self.es_admin:
            return True
        return self.permisos.filter(codigo=codigo_permiso, activo=True).exists()
    
    def get_permisos_por_modulo(self):
        """Obtiene los permisos agrupados por módulo"""
        from django.db.models import Prefetch
        return self.permisos.prefetch_related(
            Prefetch('modulo')
        ).select_related('modulo').order_by('modulo__nombre', 'tipo')

class RolPermiso(models.Model):
    """Tabla intermedia para roles y permisos con metadatos adicionales"""
    rol = models.ForeignKey(Rol, on_delete=models.CASCADE)
    permiso = models.ForeignKey(Permiso, on_delete=models.CASCADE)
    asignado_por = models.CharField(max_length=100, blank=True)  # Usuario que asignó
    fecha_asignacion = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'roles_rol_permisos'
        unique_together = ['rol', 'permiso']
        verbose_name = 'Rol-Permiso'
        verbose_name_plural = 'Roles-Permisos'
    
    def __str__(self):
        return f"{self.rol.nombre} - {self.permiso.codigo}"

class UsuarioRol(models.Model):
    """Relación entre usuarios y roles"""
    # Importación lazy para evitar dependencias circulares
    usuario = models.ForeignKey(
        'usuarios.Usuario',  
        on_delete=models.CASCADE,
        related_name='usuario_roles'
    )
    rol = models.ForeignKey(Rol, on_delete=models.CASCADE, related_name='usuario_roles')
    asignado_por = models.CharField(max_length=100, blank=True)
    fecha_asignacion = models.DateTimeField(auto_now_add=True)
    activo = models.BooleanField(default=True)
    
    class Meta:
        db_table = 'roles_usuario_roles'
        unique_together = ['usuario', 'rol']
        verbose_name = 'Usuario-Rol'
        verbose_name_plural = 'Usuarios-Roles'
    
    def __str__(self):
        return f"{self.usuario} - {self.rol.nombre}"