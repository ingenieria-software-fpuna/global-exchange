from django.contrib import admin
from django.utils.html import format_html
from .models import Tauser, Stock, StockDenominacion, HistorialStockDenominacion


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
    fields = ['moneda', 'cantidad', 'es_activo']
    readonly_fields = ['fecha_creacion', 'fecha_actualizacion']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('moneda')


@admin.register(Stock)
class StockAdmin(admin.ModelAdmin):
    """Administración de Stock"""
    
    list_display = ['tauser', 'moneda', 'cantidad_display', 'es_activo', 'bajo_stock', 'fecha_actualizacion']
    list_filter = ['es_activo', 'tauser', 'moneda', 'fecha_creacion']
    search_fields = ['tauser__nombre', 'moneda__nombre', 'moneda__codigo']
    list_editable = ['es_activo']
    ordering = ['tauser', 'moneda']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('tauser', 'moneda')
        }),
        ('Stock', {
            'fields': ('cantidad', 'es_activo')
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
    
    
    def bajo_stock(self, obj):
        """Indica si el stock está bajo"""
        if obj.esta_bajo_stock():
            return format_html('<span style="color: red; font-weight: bold;">⚠️ BAJO STOCK</span>')
        return format_html('<span style="color: green;">✓ OK</span>')
    bajo_stock.short_description = 'Estado'
    bajo_stock.admin_order_field = 'cantidad'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('tauser', 'moneda')


class StockDenominacionInline(admin.TabularInline):
    """Inline para gestionar stock por denominación desde el admin de Stock"""
    model = StockDenominacion
    extra = 0
    fields = ['denominacion', 'cantidad', 'es_activo']
    readonly_fields = ['fecha_creacion', 'fecha_actualizacion']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('denominacion', 'denominacion__moneda')


@admin.register(StockDenominacion)
class StockDenominacionAdmin(admin.ModelAdmin):
    """Administración de Stock por Denominación"""
    
    list_display = [
        'stock', 'denominacion', 'cantidad', 'valor_total_display', 
        'es_activo', 'bajo_stock', 'fecha_actualizacion'
    ]
    list_filter = ['es_activo', 'stock__tauser', 'denominacion__moneda', 'denominacion__tipo', 'fecha_creacion']
    search_fields = [
        'stock__tauser__nombre', 'denominacion__moneda__nombre', 
        'denominacion__moneda__codigo', 'denominacion__valor'
    ]
    list_editable = ['es_activo']
    ordering = ['stock__tauser', 'denominacion__valor']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('stock', 'denominacion')
        }),
        ('Stock por Denominación', {
            'fields': ('cantidad', 'es_activo')
        }),
        ('Fechas', {
            'fields': ('fecha_creacion', 'fecha_actualizacion'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ['fecha_creacion', 'fecha_actualizacion']
    
    def valor_total_display(self, obj):
        """Muestra el valor total formateado"""
        return obj.mostrar_valor_total()
    valor_total_display.short_description = 'Valor Total'
    valor_total_display.admin_order_field = 'cantidad'
    
    def bajo_stock(self, obj):
        """Indica si el stock de denominación está bajo"""
        if obj.esta_bajo_stock():
            return format_html('<span style="color: red; font-weight: bold;">⚠️ BAJO STOCK</span>')
        return format_html('<span style="color: green;">✓ OK</span>')
    bajo_stock.short_description = 'Estado'
    bajo_stock.admin_order_field = 'cantidad'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'stock__tauser', 'stock__moneda', 'denominacion__moneda'
        )


@admin.register(HistorialStockDenominacion)
class HistorialStockDenominacionAdmin(admin.ModelAdmin):
    """Administración del Historial de Stock por Denominación"""
    
    list_display = [
        'stock_denominacion', 'tipo_movimiento', 'cantidad_movida', 
        'valor_movido_display', 'usuario', 'fecha_movimiento'
    ]
    list_filter = [
        'tipo_movimiento', 'origen_movimiento', 'stock_denominacion__stock__tauser',
        'stock_denominacion__denominacion__moneda', 'fecha_movimiento'
    ]
    search_fields = [
        'stock_denominacion__stock__tauser__nombre',
        'stock_denominacion__denominacion__moneda__nombre',
        'usuario__username', 'observaciones'
    ]
    readonly_fields = ['fecha_movimiento']
    ordering = ['-fecha_movimiento']
    
    fieldsets = (
        ('Información del Movimiento', {
            'fields': ('stock_denominacion', 'tipo_movimiento', 'origen_movimiento')
        }),
        ('Cantidades', {
            'fields': ('cantidad_movida', 'cantidad_anterior', 'cantidad_posterior')
        }),
        ('Detalles', {
            'fields': ('usuario', 'transaccion', 'observaciones', 'fecha_movimiento')
        }),
    )
    
    def valor_movido_display(self, obj):
        """Muestra el valor movido formateado"""
        return obj.formatear_valor_movido()
    valor_movido_display.short_description = 'Valor Movido'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'stock_denominacion__stock__tauser',
            'stock_denominacion__denominacion__moneda',
            'usuario'
        )


# Actualizar StockAdmin para incluir StockDenominacionInline
StockAdmin.inlines = [StockDenominacionInline]

# Actualizar TauserAdmin para incluir StockInline
TauserAdmin.inlines = [StockInline]
