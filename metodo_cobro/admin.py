from django.contrib import admin
from .models import MetodoCobro


@admin.register(MetodoCobro)
class MetodoCobroAdmin(admin.ModelAdmin):
    list_display = ("nombre", "comision", "get_monedas_permitidas_str", "es_activo", "fecha_creacion", "fecha_actualizacion")
    list_filter = ("es_activo", "monedas_permitidas")
    search_fields = ("nombre", "descripcion")
    ordering = ("nombre",)
    filter_horizontal = ("monedas_permitidas",)
    
    def get_monedas_permitidas_str(self, obj):
        return obj.get_monedas_permitidas_str()
    get_monedas_permitidas_str.short_description = "Monedas Permitidas"