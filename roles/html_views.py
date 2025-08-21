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