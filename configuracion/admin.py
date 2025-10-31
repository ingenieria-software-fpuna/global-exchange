from django.contrib import admin
from .models import ConfiguracionSistema, ContadorDocumentoFactura


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


@admin.register(ContadorDocumentoFactura)
class ContadorDocumentoFacturaAdmin(admin.ModelAdmin):
    """
    Administración para el contador de documentos de factura.
    """
    list_display = [
        'numero_actual_formateado',
        'numero_minimo',
        'numero_maximo',
        'documentos_restantes',
        'fecha_actualizacion'
    ]
    readonly_fields = ['fecha_creacion', 'fecha_actualizacion', 'numero_actual_formateado']

    fieldsets = (
        ('Estado Actual', {
            'fields': (
                'numero_actual_formateado',
                'numero_actual',
            )
        }),
        ('Configuración del Rango', {
            'fields': (
                'numero_minimo',
                'numero_maximo',
                'formato_longitud',
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

    def numero_actual_formateado(self, obj):
        """Muestra el número actual formateado"""
        return obj.get_numero_formateado()
    numero_actual_formateado.short_description = "Número Actual (Formateado)"

    def documentos_restantes(self, obj):
        """Calcula cuántos documentos quedan disponibles"""
        restantes = obj.numero_maximo - obj.numero_actual + 1
        if restantes <= 10:
            return f"⚠️ {restantes}"
        return restantes
    documentos_restantes.short_description = "Documentos Disponibles"

    def has_add_permission(self, request):
        # Solo permitir una instancia del contador
        return not ContadorDocumentoFactura.objects.exists()

    def has_delete_permission(self, request, obj=None):
        # No permitir eliminar el contador
        return False
