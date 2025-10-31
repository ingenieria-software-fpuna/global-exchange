from django.contrib import admin
from .models import Moneda, DenominacionMoneda


class DenominacionMonedaInline(admin.TabularInline):
    model = DenominacionMoneda
    extra = 1
    fields = ['valor', 'tipo', 'es_activa']
    ordering = ['-valor', 'tipo']
    can_delete = True


@admin.register(Moneda)
class MonedaAdmin(admin.ModelAdmin):
    list_display = [
        'nombre', 'codigo', 'simbolo', 'decimales', 'monto_limite_transaccion', 'es_activa', 'fecha_creacion'
    ]
    list_filter = ['es_activa', 'fecha_creacion']
    search_fields = ['nombre', 'codigo', 'simbolo']
    readonly_fields = ['fecha_creacion', 'fecha_actualizacion']
    ordering = ['nombre']
    inlines = [DenominacionMonedaInline]

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


@admin.register(DenominacionMoneda)
class DenominacionMonedaAdmin(admin.ModelAdmin):
    list_display = [
        'moneda', 'valor', 'tipo', 'es_activa', 'fecha_creacion'
    ]
    list_filter = ['moneda', 'tipo', 'es_activa', 'fecha_creacion']
    search_fields = ['moneda__nombre', 'moneda__codigo', 'valor']
    readonly_fields = ['fecha_creacion', 'fecha_actualizacion']
    ordering = ['moneda', '-valor', 'tipo']
    list_editable = ['es_activa']

    fieldsets = (
        ('Información Básica', {
            'fields': ('moneda', 'valor', 'tipo')
        }),
        ('Estado', {
            'fields': ('es_activa',)
        }),
        ('Fechas', {
            'fields': ('fecha_creacion', 'fecha_actualizacion'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('moneda')
