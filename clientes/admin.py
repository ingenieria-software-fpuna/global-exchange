from django.contrib import admin
from .models import TipoCliente

@admin.register(TipoCliente)
class TipoClienteAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'descripcion', 'activo', 'fecha_creacion', 'fecha_modificacion']
    list_filter = ['activo', 'fecha_creacion']
    search_fields = ['nombre', 'descripcion']
    readonly_fields = ['fecha_creacion', 'fecha_modificacion']
    ordering = ['nombre']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('nombre', 'descripcion')
        }),
        ('Estado', {
            'fields': ('activo',)
        }),
        ('Fechas', {
            'fields': ('fecha_creacion', 'fecha_modificacion'),
            'classes': ('collapse',)
        }),
    )
