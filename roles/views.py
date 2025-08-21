# # apps/roles/views.py
# from rest_framework import generics, status, viewsets
# from rest_framework.response import Response
# from rest_framework.decorators import api_view, permission_classes, action
# from rest_framework.permissions import IsAuthenticated
# from django.shortcuts import get_object_or_404
# from django.db.models import Q, Count
# from django.core.paginator import Paginator
# from .models import Rol, Permiso, Modulo, UsuarioRol
# from .serializers import (
#     RolSerializer, PermisoSerializer, ModuloSerializer, 
#     UsuarioRolSerializer, RolSimpleSerializer
# )
# from .services import RolesService
# from .decorators import requiere_permiso

# # ViewSets para CRUD completo
# class ModuloViewSet(viewsets.ModelViewSet):
#     queryset = Modulo.objects.all()
#     serializer_class = ModuloSerializer
#     permission_classes = [IsAuthenticated]
    
#     def get_queryset(self):
#         queryset = Modulo.objects.all()
#         activo = self.request.query_params.get('activo', None)
#         if activo is not None:
#             queryset = queryset.filter(activo=activo.lower() == 'true')
#         return queryset.order_by('orden', 'nombre')

# class PermisoViewSet(viewsets.ModelViewSet):
#     queryset = Permiso.objects.select_related('modulo')
#     serializer_class = PermisoSerializer
#     permission_classes = [IsAuthenticated]
    
#     def get_queryset(self):
#         queryset = Permiso.objects.select_related('modulo')
#         modulo = self.request.query_params.get('modulo', None)
#         tipo = self.request.query_params.get('tipo', None)
#         activo = self.request.query_params.get('activo', None)
        
#         if modulo:
#             queryset = queryset.filter(modulo__codigo=modulo)
#         if tipo:
#             queryset = queryset.filter(tipo=tipo)
#         if activo is not None:
#             queryset = queryset.filter(activo=activo.lower() == 'true')
            
#         return queryset.order_by('modulo__orden', 'tipo', 'nombre')

# class RolViewSet(viewsets.ModelViewSet):
#     queryset = Rol.objects.prefetch_related('permisos__modulo')
#     serializer_class = RolSerializer
#     permission_classes = [IsAuthenticated]
    
#     def get_queryset(self):
#         queryset = Rol.objects.prefetch_related('permisos__modulo')
#         activo = self.request.query_params.get('activo', None)
#         if activo is not None:
#             queryset = queryset.filter(activo=activo.lower() == 'true')
#         return queryset.annotate(count_permisos=Count('permisos')).order_by('nombre')
    
#     @action(detail=True, methods=['post'])
#     def asignar_permisos(self, request, pk=None):
#         """Asigna múltiples permisos a un rol"""
#         rol = self.get_object()
#         permisos_ids = request.data.get('permisos_ids', [])
        
#         try:
#             permisos = Permiso.objects.filter(id__in=permisos_ids, activo=True)
#             rol.permisos.set(permisos)
            
#             return Response({
#                 'message': f'Se asignaron {len(permisos)} permisos al rol {rol.nombre}',
#                 'permisos_asignados': len(permisos)
#             })
#         except Exception as e:
#             return Response({
#                 'error': str(e)
#             }, status=status.HTTP_400_BAD_REQUEST)
    
#     @action(detail=True, methods=['get'])
#     def usuarios_con_rol(self, request, pk=None):
#         """Obtiene usuarios que tienen este rol"""
#         rol = self.get_object()
#         usuarios_roles = UsuarioRol.objects.filter(rol=rol, activo=True).select_related('usuario')
#         serializer = UsuarioRolSerializer(usuarios_roles, many=True)
#         return Response(serializer.data)

# class UsuarioRolViewSet(viewsets.ModelViewSet):
#     queryset = UsuarioRol.objects.select_related('usuario', 'rol')
#     serializer_class = UsuarioRolSerializer
#     permission_classes = [IsAuthenticated]
    
#     def get_queryset(self):
#         queryset = UsuarioRol.objects.select_related('usuario', 'rol')
#         usuario_id = self.request.query_params.get('usuario', None)
#         rol_id = self.request.query_params.get('rol', None)
#         activo = self.request.query_params.get('activo', None)
        
#         if usuario_id:
#             queryset = queryset.filter(usuario_id=usuario_id)
#         if rol_id:
#             queryset = queryset.filter(rol_id=rol_id)
#         if activo is not None:
#             queryset = queryset.filter(activo=activo.lower() == 'true')
            
#         return queryset.order_by('-fecha_asignacion')

# # API Views específicas
# @api_view(['GET'])
# @permission_classes([IsAuthenticated])
# def mis_permisos(request):
#     """Obtiene los permisos del usuario autenticado"""
#     permisos = RolesService.obtener_permisos_usuario(request.user)
#     serializer = PermisoSerializer(permisos, many=True)
#     return Response({
#         'permisos': serializer.data,
#         'total': permisos.count()
#     })

# @api_view(['GET'])
# @permission_classes([IsAuthenticated])
# def mis_roles(request):
#     """Obtiene los roles del usuario autenticado"""
#     roles_usuario = UsuarioRol.objects.filter(
#         usuario=request.user,
#         activo=True,
#         rol__activo=True
#     ).select_related('rol')
    
#     roles = [ur.rol for ur in roles_usuario]
#     serializer = RolSimpleSerializer(roles, many=True)
#     return Response({
#         'roles': serializer.data,
#         'total': len(roles)
#     })

# @api_view(['POST'])
# @permission_classes([IsAuthenticated])
# def asignar_rol_usuario(request):
#     """Asigna un rol a un usuario"""
#     usuario_id = request.data.get('usuario_id')
#     rol_id = request.data.get('rol_id')
    
#     if not usuario_id or not rol_id:
#         return Response({
#             'error': 'usuario_id y rol_id son requeridos'
#         }, status=status.HTTP_400_BAD_REQUEST)
    
#     try:
#         # Importa aquí para evitar dependencias circulares
#         from usuarios.models import Usuario
        
#         usuario = Usuario.objects.get(id=usuario_id)
#         rol = get_object_or_404(Rol, id=rol_id, activo=True)
        
#         usuario_rol = RolesService.asignar_rol_usuario(
#             usuario=usuario,
#             rol=rol,
#             asignado_por=str(request.user)
#         )
        
#         serializer = UsuarioRolSerializer(usuario_rol)
#         return Response(serializer.data, status=status.HTTP_201_CREATED)
        
#     except Usuario.DoesNotExist:
#         return Response({
#             'error': 'Usuario no encontrado'
#         }, status=status.HTTP_404_NOT_FOUND)
#     except Exception as e:
#         return Response({
#             'error': str(e)
#         }, status=status.HTTP_400_BAD_REQUEST)

# @api_view(['POST'])
# @permission_classes([IsAuthenticated])
# def remover_rol_usuario(request):
#     """Remueve un rol de un usuario"""
#     usuario_id = request.data.get('usuario_id')
#     rol_id = request.data.get('rol_id')
    
#     if not usuario_id or not rol_id:
#         return Response({
#             'error': 'usuario_id y rol_id son requeridos'
#         }, status=status.HTTP_400_BAD_REQUEST)
    
#     try:
#         from usuarios.models import Usuario
        
#         usuario = Usuario.objects.get(id=usuario_id)
#         rol = get_object_or_404(Rol, id=rol_id)
        
#         success = RolesService.remover_rol_usuario(usuario, rol)
        
#         if success:
#             return Response({'message': 'Rol removido exitosamente'})
#         else:
#             return Response({
#                 'error': 'El usuario no tiene asignado este rol'
#             }, status=status.HTTP_404_NOT_FOUND)
            
#     except Usuario.DoesNotExist:
#         return Response({
#             'error': 'Usuario no encontrado'
#         }, status=status.HTTP_404_NOT_FOUND)

# @api_view(['GET'])
# @permission_classes([IsAuthenticated])
# def estadisticas_roles(request):
#     """Estadísticas del sistema de roles"""
#     stats = {
#         'total_roles': Rol.objects.filter(activo=True).count(),
#         'total_permisos': Permiso.objects.filter(activo=True).count(),
#         'total_modulos': Modulo.objects.filter(activo=True).count(),
#         'roles_mas_usados': [],
#         'modulos_con_mas_permisos': []
#     }
    
#     # Roles más usados
#     roles_populares = UsuarioRol.objects.filter(
#         activo=True,
#         rol__activo=True
#     ).values(
#         'rol__nombre', 'rol__id'
#     ).annotate(
#         usuarios_count=Count('usuario')
#     ).order_by('-usuarios_count')[:5]
    
#     stats['roles_mas_usados'] = list(roles_populares)
    
#     # Módulos con más permisos
#     modulos_permisos = Modulo.objects.filter(
#         activo=True
#     ).annotate(
#         permisos_count=Count('permisos', filter=Q(permisos__activo=True))
#     ).order_by('-permisos_count')[:5]
    
#     stats['modulos_con_mas_permisos'] = [
#         {
#             'modulo': m.nombre,
#             'permisos_count': m.permisos_count
#         } for m in modulos_permisos
#     ]
    
#     return Response(stats)

# @api_view(['POST'])
# @permission_classes([IsAuthenticated])
# def clonar_rol(request):
#     """Clona un rol existente con nuevos datos"""
#     rol_origen_id = request.data.get('rol_origen_id')
#     nuevo_nombre = request.data.get('nombre')
#     nuevo_codigo = request.data.get('codigo')
#     descripcion = request.data.get('descripcion', '')
    
#     if not all([rol_origen_id, nuevo_nombre, nuevo_codigo]):
#         return Response({
#             'error': 'rol_origen_id, nombre y codigo son requeridos'
#         }, status=status.HTTP_400_BAD_REQUEST)
    
#     try:
#         rol_origen = get_object_or_404(Rol, id=rol_origen_id)
#         permisos_codigos = list(rol_origen.permisos.values_list('codigo', flat=True))
        
#         nuevo_rol = RolesService.crear_rol_con_permisos(
#             nombre=nuevo_nombre,
#             codigo=nuevo_codigo,
#             permisos_codigos=permisos_codigos,
#             descripcion=descripcion,
#             asignado_por=str(request.user)
#         )
        
#         serializer = RolSerializer(nuevo_rol)
#         return Response(serializer.data, status=status.HTTP_201_CREATED)
        
#     except Exception as e:
#         return Response({
#             'error': str(e)
#         }, status=status.HTTP_400_BAD_REQUEST)

# roles/views.py
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib import messages
from .models import Rol, Permiso, Modulo
from .forms import RolForm, PermisoForm, ModuloForm
from .mixins import PermisoRequeridoMixin
from .services import Permisos

# Vistas para Roles
class RolListView(PermisoRequeridoMixin, ListView):
    model = Rol
    template_name = 'roles/rol_list.html'
    context_object_name = 'roles'
    permiso_requerido = Permisos.ROL_LEER

class RolCreateView(PermisoRequeridoMixin, CreateView):
    model = Rol
    form_class = RolForm
    template_name = 'roles/rol_form.html'
    success_url = reverse_lazy('roles:rol_list')
    permiso_requerido = Permisos.ROL_CREAR
    def form_valid(self, form):
        messages.success(self.request, "Rol creado exitosamente.")
        return super().form_valid(form)

class RolUpdateView(PermisoRequeridoMixin, UpdateView):
    model = Rol
    form_class = RolForm
    template_name = 'roles/rol_form.html'
    success_url = reverse_lazy('roles:rol_list')
    permiso_requerido = Permisos.ROL_EDITAR
    def form_valid(self, form):
        messages.success(self.request, "Rol actualizado exitosamente.")
        return super().form_valid(form)

class RolDeleteView(PermisoRequeridoMixin, DeleteView):
    model = Rol
    template_name = 'roles/rol_confirm_delete.html'
    success_url = reverse_lazy('roles:rol_list')
    permiso_requerido = Permisos.ROL_ELIMINAR
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = f"Eliminar Rol {self.object.nombre}"
        return context

# Vistas para Permisos
class PermisoListView(PermisoRequeridoMixin, ListView):
    model = Permiso
    template_name = 'roles/permiso_list.html'
    context_object_name = 'permisos'
    permiso_requerido = Permisos.PERMISO_LEER

class PermisoCreateView(PermisoRequeridoMixin, CreateView):
    model = Permiso
    form_class = PermisoForm
    template_name = 'roles/permiso_form.html'
    success_url = reverse_lazy('roles:permiso_list')
    permiso_requerido = Permisos.PERMISO_CREAR
    def form_valid(self, form):
        messages.success(self.request, "Permiso creado exitosamente.")
        return super().form_valid(form)

class PermisoUpdateView(PermisoRequeridoMixin, UpdateView):
    model = Permiso
    form_class = PermisoForm
    template_name = 'roles/permiso_form.html'
    success_url = reverse_lazy('roles:permiso_list')
    permiso_requerido = Permisos.PERMISO_EDITAR
    def form_valid(self, form):
        messages.success(self.request, "Permiso actualizado exitosamente.")
        return super().form_valid(form)

class PermisoDeleteView(PermisoRequeridoMixin, DeleteView):
    model = Permiso
    template_name = 'roles/permiso_confirm_delete.html'
    success_url = reverse_lazy('roles:permiso_list')
    permiso_requerido = Permisos.PERMISO_ELIMINAR
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = f"Eliminar Permiso {self.object.nombre}"
        return context

# Vistas para Módulos (CRUD completo por si no lo tienes)
class ModuloListView(PermisoRequeridoMixin, ListView):
    model = Modulo
    template_name = 'roles/modulo_list.html'
    context_object_name = 'modulos'
    permiso_requerido = Permisos.PERMISO_LEER # Se asume que leer permisos incluye leer modulos

class ModuloCreateView(PermisoRequeridoMixin, CreateView):
    model = Modulo
    form_class = ModuloForm
    template_name = 'roles/modulo_form.html'
    success_url = reverse_lazy('roles:modulo_list')
    permiso_requerido = Permisos.PERMISO_CREAR
    def form_valid(self, form):
        messages.success(self.request, "Módulo creado exitosamente.")
        return super().form_valid(form)

class ModuloUpdateView(PermisoRequeridoMixin, UpdateView):
    model = Modulo
    form_class = ModuloForm
    template_name = 'roles/modulo_form.html'
    success_url = reverse_lazy('roles:modulo_list')
    permiso_requerido = Permisos.PERMISO_EDITAR
    def form_valid(self, form):
        messages.success(self.request, "Módulo actualizado exitosamente.")
        return super().form_valid(form)

class ModuloDeleteView(PermisoRequeridoMixin, DeleteView):
    model = Modulo
    template_name = 'roles/modulo_confirm_delete.html'
    success_url = reverse_lazy('roles:modulo_list')
    permiso_requerido = Permisos.PERMISO_ELIMINAR
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = f"Eliminar Módulo {self.object.nombre}"
        return context