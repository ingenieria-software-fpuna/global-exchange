# Guía de Roles y Permisos en Django

## 13. Templates HTML

### Base Template
```html
<!-- apps/roles/templates/roles/base.html -->
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}Sistema de Roles{% endblock %}</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <link href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css" rel="stylesheet">
</head>
<body>
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
        <div class="container">
            <a class="navbar-brand" href="{% url 'roles:dashboard'# Módulo de Roles y Permisos en Django

## 1. Estructura del Proyecto

```
global-exchange/
├── global_exchange/
│   ├── settings.py
│   ├── urls.py
│   └── ...
├── apps/
│   ├── roles/          # Nueva app de roles
│   ├── usuarios/       # Tu app de usuarios
│   └── ...
└── manage.py
```

## 2. Creación de la App de Roles

```bash
# Crear la app
python manage.py startapp roles

# Mover a la carpeta apps (si usas esa estructura)
mv roles apps/
```

## 3. Configuración en settings.py

```python
# settings.py
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Apps del proyecto
    'apps.roles',
    'apps.usuarios',
]
```

## 4. Modelos de la App Roles (models.py)

```python
# apps/roles/models.py
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
        'usuarios.Usuario',  # Asumiendo que tu modelo de usuario se llama Usuario
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
```

## 5. NOTA: Sin Admin de Django
Como no usamos el admin de Django, crearemos interfaces propias para la gestión.

## 6. Serializers (serializers.py)

```python
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
```

## 7. Servicios de Negocio (services.py)

```python
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
```

## 8. Decoradores para Permisos (decorators.py)

```python
# apps/roles/decorators.py
from functools import wraps
from django.http import JsonResponse
from django.core.exceptions import PermissionDenied
from django.contrib.auth.decorators import login_required
from .services import RolesService

def requiere_permiso(codigo_permiso):
    """Decorador que requiere un permiso específico"""
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            if not RolesService.usuario_tiene_permiso(request.user, codigo_permiso):
                if request.is_ajax() or request.content_type == 'application/json':
                    return JsonResponse({
                        'error': 'No tienes permisos para realizar esta acción'
                    }, status=403)
                raise PermissionDenied("No tienes permisos para acceder a esta página")
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator

def requiere_rol(codigo_rol):
    """Decorador que requiere un rol específico"""
    def decorator(view_func):
        @wraps(view_func)
        @login_required
        def wrapper(request, *args, **kwargs):
            tiene_rol = UsuarioRol.objects.filter(
                usuario=request.user,
                rol__codigo=codigo_rol,
                activo=True,
                rol__activo=True
            ).exists()
            
            if not tiene_rol:
                if request.is_ajax() or request.content_type == 'application/json':
                    return JsonResponse({
                        'error': f'Necesitas el rol {codigo_rol} para realizar esta acción'
                    }, status=403)
                raise PermissionDenied("No tienes el rol necesario")
            
            return view_func(request, *args, **kwargs)
        return wrapper
    return decorator
```

## 9. Mixins para Class-Based Views (mixins.py)

```python
# apps/roles/mixins.py
from django.core.exceptions import PermissionDenied
from django.http import JsonResponse
from .services import RolesService

class PermisoRequeridoMixin:
    """Mixin para CBV que requiere permisos"""
    permiso_requerido = None
    
    def dispatch(self, request, *args, **kwargs):
        if not self.permiso_requerido:
            raise ValueError("Debe especificar 'permiso_requerido'")
        
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        
        if not RolesService.usuario_tiene_permiso(request.user, self.permiso_requerido):
            return self.handle_no_permission()
        
        return super().dispatch(request, *args, **kwargs)
    
    def handle_no_permission(self):
        if self.request.is_ajax() or getattr(self.request, 'content_type', '') == 'application/json':
            return JsonResponse({
                'error': 'No tienes permisos para realizar esta acción'
            }, status=403)
        raise PermissionDenied("No tienes permisos suficientes")
```

## 10. Vistas API Completas (views.py)

```python
# apps/roles/views.py
from rest_framework import generics, status, viewsets
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.db.models import Q, Count
from django.core.paginator import Paginator
from .models import Rol, Permiso, Modulo, UsuarioRol
from .serializers import (
    RolSerializer, PermisoSerializer, ModuloSerializer, 
    UsuarioRolSerializer, RolSimpleSerializer
)
from .services import RolesService
from .decorators import requiere_permiso

# ViewSets para CRUD completo
class ModuloViewSet(viewsets.ModelViewSet):
    queryset = Modulo.objects.all()
    serializer_class = ModuloSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = Modulo.objects.all()
        activo = self.request.query_params.get('activo', None)
        if activo is not None:
            queryset = queryset.filter(activo=activo.lower() == 'true')
        return queryset.order_by('orden', 'nombre')

class PermisoViewSet(viewsets.ModelViewSet):
    queryset = Permiso.objects.select_related('modulo')
    serializer_class = PermisoSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = Permiso.objects.select_related('modulo')
        modulo = self.request.query_params.get('modulo', None)
        tipo = self.request.query_params.get('tipo', None)
        activo = self.request.query_params.get('activo', None)
        
        if modulo:
            queryset = queryset.filter(modulo__codigo=modulo)
        if tipo:
            queryset = queryset.filter(tipo=tipo)
        if activo is not None:
            queryset = queryset.filter(activo=activo.lower() == 'true')
            
        return queryset.order_by('modulo__orden', 'tipo', 'nombre')

class RolViewSet(viewsets.ModelViewSet):
    queryset = Rol.objects.prefetch_related('permisos__modulo')
    serializer_class = RolSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = Rol.objects.prefetch_related('permisos__modulo')
        activo = self.request.query_params.get('activo', None)
        if activo is not None:
            queryset = queryset.filter(activo=activo.lower() == 'true')
        return queryset.annotate(count_permisos=Count('permisos')).order_by('nombre')
    
    @action(detail=True, methods=['post'])
    def asignar_permisos(self, request, pk=None):
        """Asigna múltiples permisos a un rol"""
        rol = self.get_object()
        permisos_ids = request.data.get('permisos_ids', [])
        
        try:
            permisos = Permiso.objects.filter(id__in=permisos_ids, activo=True)
            rol.permisos.set(permisos)
            
            return Response({
                'message': f'Se asignaron {len(permisos)} permisos al rol {rol.nombre}',
                'permisos_asignados': len(permisos)
            })
        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def usuarios_con_rol(self, request, pk=None):
        """Obtiene usuarios que tienen este rol"""
        rol = self.get_object()
        usuarios_roles = UsuarioRol.objects.filter(rol=rol, activo=True).select_related('usuario')
        serializer = UsuarioRolSerializer(usuarios_roles, many=True)
        return Response(serializer.data)

class UsuarioRolViewSet(viewsets.ModelViewSet):
    queryset = UsuarioRol.objects.select_related('usuario', 'rol')
    serializer_class = UsuarioRolSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = UsuarioRol.objects.select_related('usuario', 'rol')
        usuario_id = self.request.query_params.get('usuario', None)
        rol_id = self.request.query_params.get('rol', None)
        activo = self.request.query_params.get('activo', None)
        
        if usuario_id:
            queryset = queryset.filter(usuario_id=usuario_id)
        if rol_id:
            queryset = queryset.filter(rol_id=rol_id)
        if activo is not None:
            queryset = queryset.filter(activo=activo.lower() == 'true')
            
        return queryset.order_by('-fecha_asignacion')

# API Views específicas
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def mis_permisos(request):
    """Obtiene los permisos del usuario autenticado"""
    permisos = RolesService.obtener_permisos_usuario(request.user)
    serializer = PermisoSerializer(permisos, many=True)
    return Response({
        'permisos': serializer.data,
        'total': permisos.count()
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def mis_roles(request):
    """Obtiene los roles del usuario autenticado"""
    roles_usuario = UsuarioRol.objects.filter(
        usuario=request.user,
        activo=True,
        rol__activo=True
    ).select_related('rol')
    
    roles = [ur.rol for ur in roles_usuario]
    serializer = RolSimpleSerializer(roles, many=True)
    return Response({
        'roles': serializer.data,
        'total': len(roles)
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def asignar_rol_usuario(request):
    """Asigna un rol a un usuario"""
    usuario_id = request.data.get('usuario_id')
    rol_id = request.data.get('rol_id')
    
    if not usuario_id or not rol_id:
        return Response({
            'error': 'usuario_id y rol_id son requeridos'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        # Importa aquí para evitar dependencias circulares
        from apps.usuarios.models import Usuario
        
        usuario = Usuario.objects.get(id=usuario_id)
        rol = get_object_or_404(Rol, id=rol_id, activo=True)
        
        usuario_rol = RolesService.asignar_rol_usuario(
            usuario=usuario,
            rol=rol,
            asignado_por=str(request.user)
        )
        
        serializer = UsuarioRolSerializer(usuario_rol)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
        
    except Usuario.DoesNotExist:
        return Response({
            'error': 'Usuario no encontrado'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def remover_rol_usuario(request):
    """Remueve un rol de un usuario"""
    usuario_id = request.data.get('usuario_id')
    rol_id = request.data.get('rol_id')
    
    if not usuario_id or not rol_id:
        return Response({
            'error': 'usuario_id y rol_id son requeridos'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        from apps.usuarios.models import Usuario
        
        usuario = Usuario.objects.get(id=usuario_id)
        rol = get_object_or_404(Rol, id=rol_id)
        
        success = RolesService.remover_rol_usuario(usuario, rol)
        
        if success:
            return Response({'message': 'Rol removido exitosamente'})
        else:
            return Response({
                'error': 'El usuario no tiene asignado este rol'
            }, status=status.HTTP_404_NOT_FOUND)
            
    except Usuario.DoesNotExist:
        return Response({
            'error': 'Usuario no encontrado'
        }, status=status.HTTP_404_NOT_FOUND)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def estadisticas_roles(request):
    """Estadísticas del sistema de roles"""
    stats = {
        'total_roles': Rol.objects.filter(activo=True).count(),
        'total_permisos': Permiso.objects.filter(activo=True).count(),
        'total_modulos': Modulo.objects.filter(activo=True).count(),
        'roles_mas_usados': [],
        'modulos_con_mas_permisos': []
    }
    
    # Roles más usados
    roles_populares = UsuarioRol.objects.filter(
        activo=True,
        rol__activo=True
    ).values(
        'rol__nombre', 'rol__id'
    ).annotate(
        usuarios_count=Count('usuario')
    ).order_by('-usuarios_count')[:5]
    
    stats['roles_mas_usados'] = list(roles_populares)
    
    # Módulos con más permisos
    modulos_permisos = Modulo.objects.filter(
        activo=True
    ).annotate(
        permisos_count=Count('permisos', filter=Q(permisos__activo=True))
    ).order_by('-permisos_count')[:5]
    
    stats['modulos_con_mas_permisos'] = [
        {
            'modulo': m.nombre,
            'permisos_count': m.permisos_count
        } for m in modulos_permisos
    ]
    
    return Response(stats)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def clonar_rol(request):
    """Clona un rol existente con nuevos datos"""
    rol_origen_id = request.data.get('rol_origen_id')
    nuevo_nombre = request.data.get('nombre')
    nuevo_codigo = request.data.get('codigo')
    descripcion = request.data.get('descripcion', '')
    
    if not all([rol_origen_id, nuevo_nombre, nuevo_codigo]):
        return Response({
            'error': 'rol_origen_id, nombre y codigo son requeridos'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        rol_origen = get_object_or_404(Rol, id=rol_origen_id)
        permisos_codigos = list(rol_origen.permisos.values_list('codigo', flat=True))
        
        nuevo_rol = RolesService.crear_rol_con_permisos(
            nombre=nuevo_nombre,
            codigo=nuevo_codigo,
            permisos_codigos=permisos_codigos,
            descripcion=descripcion,
            asignado_por=str(request.user)
        )
        
        serializer = RolSerializer(nuevo_rol)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response({
            'error': str(e)
        }, status=status.HTTP_400_BAD_REQUEST)
```

## 11. URLs Completas (urls.py)

```python
# apps/roles/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Router para ViewSets
router = DefaultRouter()
router.register(r'modulos', views.ModuloViewSet)
router.register(r'permisos', views.PermisoViewSet)
router.register(r'roles', views.RolViewSet)
router.register(r'usuario-roles', views.UsuarioRolViewSet)

app_name = 'roles'

urlpatterns = [
    # URLs del router
    path('api/', include(router.urls)),
    
    # URLs de funciones específicas
    path('api/mis-permisos/', views.mis_permisos, name='mis-permisos'),
    path('api/mis-roles/', views.mis_roles, name='mis-roles'),
    path('api/asignar-rol/', views.asignar_rol_usuario, name='asignar-rol'),
    path('api/remover-rol/', views.remover_rol_usuario, name='remover-rol'),
    path('api/estadisticas/', views.estadisticas_roles, name='estadisticas'),
    path('api/clonar-rol/', views.clonar_rol, name='clonar-rol'),
]

# URLs principales en urls.py del proyecto
# from django.urls import path, include
# 
# urlpatterns = [
#     path('roles/', include('apps.roles.urls')),
# ]
```

## 12. Interface Web de Administración (templates y vistas HTML)

### Views HTML para la gestión

```python
# apps/roles/html_views.py
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Rol, Permiso, Modulo, UsuarioRol
from .services import RolesService
from .decorators import requiere_permiso
from .forms import RolForm, ModuloForm, PermisoForm

@login_required
@requiere_permiso('roles_read')
def lista_roles(request):
    """Vista para listar roles"""
    query = request.GET.get('q', '')
    roles = Rol.objects.filter(activo=True)
    
    if query:
        roles = roles.filter(
            Q(nombre__icontains=query) | 
            Q(codigo__icontains=query) |
            Q(descripcion__icontains=query)
        )
    
    paginator = Paginator(roles.order_by('nombre'), 10)
    page = request.GET.get('page')
    roles_paginated = paginator.get_page(page)
    
    return render(request, 'roles/lista_roles.html', {
        'roles': roles_paginated,
        'query': query
    })

@login_required
@requiere_permiso('roles_create')
def crear_rol(request):
    """Vista para crear un nuevo rol"""
    if request.method == 'POST':
        form = RolForm(request.POST)
        if form.is_valid():
            rol = form.save()
            messages.success(request, f'Rol "{rol.nombre}" creado exitosamente.')
            return redirect('roles:lista-roles')
    else:
        form = RolForm()
    
    return render(request, 'roles/crear_rol.html', {
        'form': form,
        'titulo': 'Crear Rol'
    })

@login_required
@requiere_permiso('roles_update')
def editar_rol(request, rol_id):
    """Vista para editar un rol"""
    rol = get_object_or_404(Rol, id=rol_id)
    
    if request.method == 'POST':
        form = RolForm(request.POST, instance=rol)
        if form.is_valid():
            rol = form.save()
            messages.success(request, f'Rol "{rol.nombre}" actualizado exitosamente.')
            return redirect('roles:lista-roles')
    else:
        form = RolForm(instance=rol)
    
    return render(request, 'roles/crear_rol.html', {
        'form': form,
        'titulo': f'Editar Rol: {rol.nombre}',
        'rol': rol
    })

@login_required
@requiere_permiso('roles_read')
def detalle_rol(request, rol_id):
    """Vista para ver detalles de un rol"""
    rol = get_object_or_404(Rol, id=rol_id)
    permisos_por_modulo = {}
    
    for permiso in rol.permisos.select_related('modulo').filter(activo=True):
        modulo = permiso.modulo.nombre
        if modulo not in permisos_por_modulo:
            permisos_por_modulo[modulo] = []
        permisos_por_modulo[modulo].append(permiso)
    
    # Usuarios con este rol
    usuarios_con_rol = UsuarioRol.objects.filter(
        rol=rol, activo=True
    ).select_related('usuario')[:10]
    
    return render(request, 'roles/detalle_rol.html', {
        'rol': rol,
        'permisos_por_modulo': permisos_por_modulo,
        'usuarios_con_rol': usuarios_con_rol
    })

@login_required
@requiere_permiso('roles_update')
def gestionar_permisos_rol(request, rol_id):
    """Vista para gestionar permisos de un rol"""
    rol = get_object_or_404(Rol, id=rol_id)
    
    if request.method == 'POST':
        permisos_ids = request.POST.getlist('permisos')
        permisos = Permiso.objects.filter(id__in=permisos_ids, activo=True)
        rol.permisos.set(permisos)
        
        messages.success(request, f'Permisos del rol "{rol.nombre}" actualizados exitosamente.')
        return redirect('roles:detalle-rol', rol_id=rol.id)
    
    # Agrupar permisos por módulo
    modulos = Modulo.objects.filter(activo=True).prefetch_related('permisos')
    permisos_asignados = set(rol.permisos.values_list('id', flat=True))
    
    return render(request, 'roles/gestionar_permisos.html', {
        'rol': rol,
        'modulos': modulos,
        'permisos_asignados': permisos_asignados
    })

@login_required
def dashboard_roles(request):
    """Dashboard principal del sistema de roles"""
    stats = {
        'total_roles': Rol.objects.filter(activo=True).count(),
        'total_permisos': Permiso.objects.filter(activo=True).count(),
        'total_modulos': Modulo.objects.filter(activo=True).count(),
        'roles_recientes': Rol.objects.filter(activo=True).order_by('-created_at')[:5],
        'usuarios_con_mas_roles': UsuarioRol.objects.filter(activo=True).values('usuario').annotate(count=Count('rol')).order_by('-count')[:5]
    }
    
    return render(request, 'roles/dashboard.html', stats)
```

### Forms para la gestión

```python
# apps/roles/forms.py
from django import forms
from .models import Rol, Modulo, Permiso

class RolForm(forms.ModelForm):
    class Meta:
        model = Rol
        fields = ['nombre', 'codigo', 'descripcion', 'es_admin', 'activo']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre del rol'
            }),
            'codigo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Código único del rol'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descripción del rol'
            }),
            'es_admin': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'activo': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
    
    def clean_codigo(self):
        codigo = self.cleaned_data['codigo'].lower().replace(' ', '_')
        # Validar que no exista otro rol con el mismo código
        if Rol.objects.filter(codigo=codigo).exclude(pk=self.instance.pk if self.instance else None).exists():
            raise forms.ValidationError('Ya existe un rol con este código.')
        return codigo

class ModuloForm(forms.ModelForm):
    class Meta:
        model = Modulo
        fields = ['nombre', 'codigo', 'descripcion', 'orden', 'activo']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'codigo': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'orden': forms.NumberInput(attrs={'class': 'form-control'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class PermisoForm(forms.ModelForm):
    class Meta:
        model = Permiso
        fields = ['nombre', 'codigo', 'descripcion', 'tipo', 'modulo', 'activo']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'codigo': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'tipo': forms.Select(attrs={'class': 'form-control'}),
            'modulo': forms.Select(attrs={'class': 'form-control'}),
            'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

class AsignarRolUsuarioForm(forms.Form):
    usuario = forms.ModelChoiceField(
        queryset=None,  # Se define en __init__
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Usuario'
    )
    rol = forms.ModelChoiceField(
        queryset=Rol.objects.filter(activo=True),
        widget=forms.Select(attrs={'class': 'form-control'}),
        label='Rol'
    )
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Importa aquí para evitar dependencias circulares
        from apps.usuarios.models import Usuario
        self.fields['usuario'].queryset = Usuario.objects.filter(activo=True)
```

## 12. Migraciones y Datos Iniciales

```bash
# Crear migraciones
python manage.py makemigrations roles

# Aplicar migraciones
python manage.py migrate
```

## 13. Comando para Datos Iniciales (management/commands/crear_roles_iniciales.py)

```python
# apps/roles/management/commands/crear_roles_iniciales.py
from django.core.management.base import BaseCommand
from apps.roles.models import Modulo, Permiso, Rol
from apps.roles.services import RolesService

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
```

## 14. Ejemplo de Uso en Vistas

```python
# Ejemplo en una vista de tu app principal
from apps.roles.decorators import requiere_permiso
from apps.roles.mixins import PermisoRequeridoMixin

# Con decorador
@requiere_permiso('usuarios_create')
def crear_usuario(request):
    # Lógica para crear usuario
    pass

# Con CBV
class CrearUsuarioView(PermisoRequeridoMixin, CreateView):
    permiso_requerido = 'usuarios_create'
    # ... resto de la vista
```

## 15. Comandos Útiles

```bash
# Crear roles y permisos iniciales
python manage.py crear_roles_iniciales

# Crear superusuario (opcional)
python manage.py createsuperuser

# Ver migraciones
python manage.py showmigrations roles
```

Esta estructura te proporciona un sistema completo de roles y permisos que es:
- **Escalable**: Fácil agregar nuevos módulos y permisos
- **Flexible**: Soporte para roles complejos y permisos granulares
- **Mantenible**: Código organizado y bien estructurado
- **Reutilizable**: Independiente de otras apps