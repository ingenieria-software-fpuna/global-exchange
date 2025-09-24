from django.contrib import admin
from .models import TipoCliente, Cliente

@admin.register(TipoCliente)
class TipoClienteAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'descripcion', 'descuento', 'activo', 'fecha_creacion', 'fecha_modificacion']
    list_filter = ['activo', 'fecha_creacion']
    search_fields = ['nombre', 'descripcion']
    readonly_fields = ['fecha_creacion', 'fecha_modificacion']
    ordering = ['nombre']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('nombre', 'descripcion', 'descuento')
        }),
        ('Estado', {
            'fields': ('activo',)
        }),
        ('Fechas', {
            'fields': ('fecha_creacion', 'fecha_modificacion'),
            'classes': ('collapse',)
        }),
    )

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = [
        'nombre_comercial', 'ruc', 'tipo_cliente', 'correo_electronico', 
        'numero_telefono', 'monto_limite_transaccion', 'activo', 'fecha_creacion'
    ]
    list_filter = [
        'activo', 'tipo_cliente', 'fecha_creacion', 'usuarios_asociados'
    ]
    search_fields = [
        'nombre_comercial', 'ruc', 'correo_electronico', 'numero_telefono'
    ]
    readonly_fields = ['fecha_creacion', 'fecha_modificacion']
    ordering = ['nombre_comercial']
    filter_horizontal = ['usuarios_asociados']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('nombre_comercial', 'ruc', 'tipo_cliente', 'monto_limite_transaccion')
        }),
        ('Información de Contacto', {
            'fields': ('direccion', 'correo_electronico', 'numero_telefono')
        }),
        ('Relaciones', {
            'fields': ('usuarios_asociados',)
        }),
        ('Estado', {
            'fields': ('activo',)
        }),
        ('Fechas', {
            'fields': ('fecha_creacion', 'fecha_modificacion'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('tipo_cliente').prefetch_related('usuarios_asociados')
