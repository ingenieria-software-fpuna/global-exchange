from django.contrib import admin
from django.utils.html import format_html
from .models import Tauser, Stock


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


class StockInline(admin.TabularInline):
    """Inline para gestionar stock desde el admin de Tauser"""
    model = Stock
    extra = 0
    fields = ['moneda', 'cantidad', 'cantidad_minima', 'es_activo']
    readonly_fields = ['fecha_creacion', 'fecha_actualizacion']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('moneda')


@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    """Administración de Stock"""
    
    list_display = ['tauser', 'moneda', 'cantidad_display', 'cantidad_minima_display', 'es_activo', 'bajo_stock', 'fecha_actualizacion']
    list_filter = ['es_activo', 'tauser', 'moneda', 'fecha_creacion']
    search_fields = ['tauser__nombre', 'moneda__nombre', 'moneda__codigo']
    list_editable = ['es_activo']
    ordering = ['tauser', 'moneda']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('tauser', 'moneda')
        }),
        ('Stock', {
            'fields': ('cantidad', 'cantidad_minima', 'es_activo')
        }),
        ('Fechas', {
            'fields': ('fecha_creacion', 'fecha_actualizacion'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['fecha_creacion', 'fecha_actualizacion']
    
    def cantidad_display(self, obj):
        """Muestra la cantidad formateada con el símbolo de la moneda"""
        return obj.mostrar_cantidad()
    cantidad_display.short_description = 'Cantidad'
    cantidad_display.admin_order_field = 'cantidad'
    
    def cantidad_minima_display(self, obj):
        """Muestra la cantidad mínima formateada"""
        return f"{obj.moneda.simbolo}{obj.cantidad_minima:.{obj.moneda.decimales}f}"
    cantidad_minima_display.short_description = 'Cantidad Mínima'
    cantidad_minima_display.admin_order_field = 'cantidad_minima'
    
    def bajo_stock(self, obj):
        """Indica si el stock está bajo"""
        if obj.esta_bajo_stock():
            return format_html('<span style="color: red; font-weight: bold;">⚠️ BAJO STOCK</span>')
        return format_html('<span style="color: green;">✓ OK</span>')
    bajo_stock.short_description = 'Estado'
    bajo_stock.admin_order_field = 'cantidad'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('tauser', 'moneda')


# Actualizar TauserAdmin para incluir StockInline
TauserAdmin.inlines = [StockInline]
