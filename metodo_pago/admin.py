from django.contrib import admin
from .models import MetodoPago


@admin.register(MetodoPago)
class MetodoPagoAdmin(admin.ModelAdmin):
    list_display = ("nombre", "comision", "es_activo", "fecha_creacion", "fecha_actualizacion")
    list_filter = ("es_activo",)
    search_fields = ("nombre", "descripcion")
    ordering = ("nombre",)

