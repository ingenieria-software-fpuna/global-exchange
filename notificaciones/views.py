"""
Vistas para el módulo de notificaciones de cambios en tasas de cambio.
Solo accesible para usuarios con roles Operador o Visitante.
"""
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponseForbidden
from django.core.paginator import Paginator
from django.contrib import messages
from .models import Notificacion
from .forms import PreferenciasNotificacionesForm


def tiene_permiso_notificaciones(user):
    """
    Verifica si el usuario tiene permiso para ver notificaciones.
    Solo usuarios con roles Operador o Visitante pueden ver notificaciones.
    """
    return user.groups.filter(name__in=['Operador', 'Visitante']).exists()


@login_required
def lista_notificaciones(request):
    """
    Lista todas las notificaciones del usuario actual.
    Permite filtrar por leídas/no leídas.
    Solo accesible para Operadores y Visitantes.
    """
    # Verificar que el usuario tenga permiso
    if not tiene_permiso_notificaciones(request.user):
        return HttpResponseForbidden("No tienes permiso para ver notificaciones.")
    
    filtro = request.GET.get('filtro', 'todas')
    
    notificaciones = Notificacion.objects.filter(usuario=request.user)
    
    if filtro == 'no_leidas':
        notificaciones = notificaciones.filter(leida=False)
    elif filtro == 'leidas':
        notificaciones = notificaciones.filter(leida=True)
    
    # Paginación
    paginator = Paginator(notificaciones, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Contar no leídas
    no_leidas = Notificacion.objects.filter(usuario=request.user, leida=False).count()
    
    context = {
        'page_obj': page_obj,
        'filtro': filtro,
        'no_leidas': no_leidas,
    }
    
    return render(request, 'notificaciones/lista.html', context)


@login_required
def marcar_leida(request, pk):
    """
    Marca una notificación como leída.
    Solo accesible para Operadores y Visitantes.
    """
    # Verificar que el usuario tenga permiso
    if not tiene_permiso_notificaciones(request.user):
        return HttpResponseForbidden("No tienes permiso para realizar esta acción.")
    
    notificacion = get_object_or_404(Notificacion, pk=pk, usuario=request.user)
    notificacion.marcar_como_leida()
    
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        return JsonResponse({'success': True})
    
    return redirect('notificaciones:lista')


@login_required
def marcar_todas_leidas(request):
    """
    Marca todas las notificaciones del usuario como leídas.
    Solo accesible para Operadores y Visitantes.
    """
    # Verificar que el usuario tenga permiso
    if not tiene_permiso_notificaciones(request.user):
        return HttpResponseForbidden("No tienes permiso para realizar esta acción.")
    
    if request.method == 'POST':
        Notificacion.objects.filter(
            usuario=request.user,
            leida=False
        ).update(leida=True)
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
    
    return redirect('notificaciones:lista')


@login_required
def contar_no_leidas(request):
    """
    Retorna el conteo de notificaciones no leídas (para uso AJAX).
    Solo accesible para Operadores y Visitantes.
    """
    # Verificar que el usuario tenga permiso
    if not tiene_permiso_notificaciones(request.user):
        return JsonResponse({'count': 0})
    
    count = Notificacion.objects.filter(usuario=request.user, leida=False).count()
    return JsonResponse({'count': count})


@login_required
def eliminar_notificacion(request, pk):
    """
    Elimina una notificación específica.
    Solo accesible para Operadores y Visitantes.
    """
    # Verificar que el usuario tenga permiso
    if not tiene_permiso_notificaciones(request.user):
        return HttpResponseForbidden("No tienes permiso para realizar esta acción.")
    
    if request.method == 'POST':
        notificacion = get_object_or_404(Notificacion, pk=pk, usuario=request.user)
        notificacion.delete()
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': True})
    
    return redirect('notificaciones:lista')


@login_required
def notificaciones_recientes(request):
    """
    Retorna las últimas 5 notificaciones para mostrar en el popup.
    Solo accesible para Operadores y Visitantes.
    """
    # Verificar que el usuario tenga permiso
    if not tiene_permiso_notificaciones(request.user):
        return JsonResponse({'notificaciones': [], 'total_no_leidas': 0})
    
    notificaciones = Notificacion.objects.filter(
        usuario=request.user
    ).order_by('-fecha_creacion')[:5]
    
    total_no_leidas = Notificacion.objects.filter(
        usuario=request.user,
        leida=False
    ).count()
    
    data = {
        'notificaciones': [
            {
                'id': n.id,
                'titulo': n.titulo,
                'mensaje': n.mensaje[:100] + '...' if len(n.mensaje) > 100 else n.mensaje,
                'leida': n.leida,
                'fecha_creacion': n.fecha_creacion.strftime('%d/%m/%Y %H:%M'),
                'moneda': n.moneda.codigo if n.moneda else None,
                'es_aumento': n.es_aumento,
                'cambio_porcentual': str(n.cambio_porcentual) if n.cambio_porcentual else None,
            }
            for n in notificaciones
        ],
        'total_no_leidas': total_no_leidas
    }
    
    return JsonResponse(data)


@login_required
def preferencias_notificaciones(request):
    """
    Vista para configurar las preferencias de notificaciones del usuario.
    Solo accesible para Operadores y Visitantes.
    """
    # Verificar que el usuario tenga permiso
    if not tiene_permiso_notificaciones(request.user):
        return HttpResponseForbidden("No tienes permiso para acceder a esta página.")
    
    if request.method == 'POST':
        form = PreferenciasNotificacionesForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(
                request, 
                '¡Preferencias de notificaciones actualizadas correctamente!'
            )
            return redirect('notificaciones:preferencias')
    else:
        form = PreferenciasNotificacionesForm(instance=request.user)
    
    context = {
        'form': form,
    }
    
    return render(request, 'notificaciones/preferencias.html', context)
