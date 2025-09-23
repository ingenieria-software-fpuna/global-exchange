from django.contrib import admin
from .models import ConfiguracionSistema


@admin.register(ConfiguracionSistema)
class ConfiguracionSistemaAdmin(admin.ModelAdmin):
    """
    Administración para la configuración del sistema.
    """
    list_display = [
        'limite_diario_transacciones',
        'limite_mensual_transacciones',
        'fecha_actualizacion'
    ]
    list_filter = ['fecha_creacion', 'fecha_actualizacion']
    readonly_fields = ['fecha_creacion', 'fecha_actualizacion']
    
    fieldsets = (
        ('Límites de Transacciones', {
            'fields': (
                'limite_diario_transacciones',
                'limite_mensual_transacciones',
            )
        }),
        ('Información del Sistema', {
            'fields': (
                'fecha_creacion',
                'fecha_actualizacion',
            ),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        # Solo permitir una instancia de configuración
        return not ConfiguracionSistema.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        # No permitir eliminar la configuración
        return False
