from django.contrib import admin
from .models import Moneda


@admin.register(Moneda)
class MonedaAdmin(admin.ModelAdmin):
    list_display = [
        'nombre', 'codigo', 'simbolo', 'decimales', 'monto_limite_transaccion', 'es_activa', 'fecha_creacion'
    ]
    list_filter = ['es_activa', 'fecha_creacion']
    search_fields = ['nombre', 'codigo', 'simbolo']
    readonly_fields = ['fecha_creacion', 'fecha_actualizacion']
    ordering = ['nombre']

    fieldsets = (
        ('Información Básica', {
            'fields': ('nombre', 'codigo', 'simbolo', 'decimales', 'monto_limite_transaccion')
        }),
        ('Estado', {
            'fields': ('es_activa',)
        }),
        ('Fechas', {
            'fields': ('fecha_creacion', 'fecha_actualizacion'),
            'classes': ('collapse',)
        }),
    )
