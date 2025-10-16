from django.contrib import admin
from .models import Notificacion


@admin.register(Notificacion)
class NotificacionAdmin(admin.ModelAdmin):
    """
    Administración de notificaciones en el panel de Django.
    """
    list_display = [
        'titulo',
        'usuario',
        'tipo',
        'moneda',
        'leida',
        'fecha_creacion'
    ]
    list_filter = [
        'tipo',
        'leida',
        'fecha_creacion',
        'moneda'
    ]
    search_fields = [
        'titulo',
        'mensaje',
        'usuario__email',
        'usuario__nombre'
    ]
    readonly_fields = [
        'fecha_creacion',
        'fecha_lectura'
    ]
    date_hierarchy = 'fecha_creacion'
    ordering = ['-fecha_creacion']
    
    fieldsets = (
        ('Información General', {
            'fields': ('usuario', 'tipo', 'titulo', 'mensaje')
        }),
        ('Detalles de Tasa de Cambio', {
            'fields': ('moneda', 'precio_base_anterior', 'precio_base_nuevo'),
            'classes': ('collapse',)
        }),
        ('Estado', {
            'fields': ('leida', 'fecha_creacion', 'fecha_lectura')
        }),
    )
