from django.contrib import admin
from .models import MetodoPago, Campo


@admin.register(Campo)
class CampoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "etiqueta", "tipo", "es_obligatorio", "es_activo", "fecha_creacion")
    list_filter = ("tipo", "es_obligatorio", "es_activo")
    search_fields = ("nombre", "etiqueta")
    ordering = ("nombre",)
    list_editable = ("es_activo",)


@admin.register(MetodoPago)
class MetodoPagoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "comision", "get_monedas_permitidas_str", "get_campos_count", "es_activo", "fecha_creacion", "fecha_actualizacion")
    list_filter = ("es_activo", "monedas_permitidas", "campos")
    search_fields = ("nombre", "descripcion")
    ordering = ("nombre",)
    filter_horizontal = ("monedas_permitidas", "campos")  # Para facilitar la selección múltiple
    
    def get_monedas_permitidas_str(self, obj):
        return obj.get_monedas_permitidas_str()
    get_monedas_permitidas_str.short_description = "Monedas Permitidas"
    
    def get_campos_count(self, obj):
        return obj.campos.count()
    get_campos_count.short_description = "Campos"

