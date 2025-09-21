from django.contrib import admin
from .models import TasaCambio


@admin.register(TasaCambio)
class TasaCambioAdmin(admin.ModelAdmin):
    list_display = [
        'moneda', 'precio_base', 'comision_compra', 'comision_venta', 
        'spread_display', 'es_activa', 'fecha_creacion'
    ]
    list_filter = [
        'es_activa', 'moneda', 'fecha_creacion'
    ]
    search_fields = [
        'moneda__nombre', 'moneda__codigo', 'moneda__simbolo'
    ]
    readonly_fields = ['fecha_creacion', 'fecha_actualizacion']
    ordering = ['-fecha_creacion', 'moneda__nombre']
    
    fieldsets = (
        ('Información de la Moneda', {
            'fields': ('moneda',)
        }),
        ('Precios y Comisiones', {
            'fields': ('precio_base', 'comision_compra', 'comision_venta')
        }),
        ('Estado', {
            'fields': ('es_activa',)
        }),
        ('Información del Sistema', {
            'fields': ('fecha_creacion', 'fecha_actualizacion'),
            'classes': ('collapse',)
        }),
    )
    
    def spread_display(self, obj):
        """Muestra el spread formateado"""
        return f"{obj.spread:.4f}"
    spread_display.short_description = 'Spread'
    
    def save_model(self, request, obj, form, change):
        """Lógica personalizada al guardar"""
        super().save_model(request, obj, form, change)
