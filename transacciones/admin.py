from django.contrib import admin
from django.utils.html import format_html
from .models import TipoOperacion, EstadoTransaccion, Transaccion


@admin.register(TipoOperacion)
class TipoOperacionAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'nombre', 'activo', 'fecha_creacion']
    list_filter = ['activo', 'fecha_creacion']
    search_fields = ['codigo', 'nombre']
    readonly_fields = ['fecha_creacion']
    ordering = ['nombre']


@admin.register(EstadoTransaccion)
class EstadoTransaccionAdmin(admin.ModelAdmin):
    list_display = ['codigo', 'nombre', 'es_final', 'activo']
    list_filter = ['es_final', 'activo']
    search_fields = ['codigo', 'nombre']
    ordering = ['nombre']


@admin.register(Transaccion)
class TransaccionAdmin(admin.ModelAdmin):
    list_display = [
        'id_transaccion', 'tipo_operacion', 'cliente', 'estado_badge',
        'monto_origen_formatted', 'monto_destino_formatted', 'fecha_creacion'
    ]
    list_filter = [
        'tipo_operacion', 'estado', 'moneda_origen', 'moneda_destino',
        'fecha_creacion', 'fecha_expiracion'
    ]
    search_fields = [
        'id_transaccion', 'codigo_verificacion', 'cliente__nombre_comercial',
        'cliente__ruc', 'usuario__email'
    ]
    readonly_fields = [
        'id_transaccion', 'codigo_verificacion', 'fecha_creacion',
        'fecha_actualizacion', 'ip_cliente'
    ]
    
    fieldsets = (
        ('Información General', {
            'fields': ('id_transaccion', 'tipo_operacion', 'estado', 'codigo_verificacion')
        }),
        ('Participantes', {
            'fields': ('cliente', 'usuario')
        }),
        ('Detalles de la Operación', {
            'fields': (
                ('moneda_origen', 'monto_origen'),
                ('moneda_destino', 'monto_destino'),
                'tasa_cambio'
            )
        }),
        ('Métodos y Comisiones', {
            'fields': (
                ('metodo_cobro', 'metodo_pago'),
                ('porcentaje_comision', 'monto_comision'),
                ('porcentaje_descuento', 'monto_descuento')
            )
        }),
        ('Fechas', {
            'fields': (
                'fecha_creacion', 'fecha_actualizacion',
                'fecha_expiracion', 'fecha_pago'
            )
        }),
        ('Información Adicional', {
            'fields': ('observaciones', 'ip_cliente'),
            'classes': ('collapse',)
        })
    )
    
    ordering = ['-fecha_creacion']
    date_hierarchy = 'fecha_creacion'
    
    def estado_badge(self, obj):
        """Muestra el estado con colores"""
        colors = {
            'PENDIENTE': 'orange',
            'PAGADA': 'green',
            'CANCELADA': 'red',
            'ANULADA': 'gray'
        }
        color = colors.get(obj.estado.codigo, 'black')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color, obj.estado.nombre
        )
    estado_badge.short_description = 'Estado'
    
    def monto_origen_formatted(self, obj):
        """Formatea el monto origen con símbolo de moneda"""
        return f"{obj.moneda_origen.simbolo}{obj.monto_origen:,.2f}"
    monto_origen_formatted.short_description = 'Monto Origen'
    
    def monto_destino_formatted(self, obj):
        """Formatea el monto destino con símbolo de moneda"""
        return f"{obj.moneda_destino.simbolo}{obj.monto_destino:,.2f}"
    monto_destino_formatted.short_description = 'Monto Destino'
    
    def get_queryset(self, request):
        """Optimiza las consultas con select_related"""
        return super().get_queryset(request).select_related(
            'cliente', 'usuario', 'tipo_operacion', 'estado',
            'moneda_origen', 'moneda_destino', 'metodo_cobro', 'metodo_pago'
        )
