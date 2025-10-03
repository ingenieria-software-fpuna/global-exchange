from django.contrib import admin
from .models import Tauser


@admin.register(Tauser)
class TauserAdmin(admin.ModelAdmin):
    """Administración de Tausers"""
    
    list_display = ['nombre', 'direccion', 'horario_atencion', 'es_activo', 'fecha_instalacion', 'fecha_creacion']
    list_filter = ['es_activo', 'fecha_instalacion', 'fecha_creacion']
    search_fields = ['nombre', 'direccion', 'horario_atencion']
    list_editable = ['es_activo']
    ordering = ['nombre']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('nombre', 'direccion', 'horario_atencion')
        }),
        ('Estado y Fechas', {
            'fields': ('es_activo', 'fecha_instalacion')
        }),
    )
    
    readonly_fields = ['fecha_creacion', 'fecha_actualizacion']
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  # Editing an existing object
            return self.readonly_fields + ['fecha_creacion']
        return self.readonly_fields
