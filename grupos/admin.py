from django.contrib import admin
from django.contrib.auth.models import Group, Permission
from .models import Grupo

@admin.register(Grupo)
class GrupoAdmin(admin.ModelAdmin):
    list_display = ['name', 'es_activo', 'fecha_creacion', 'fecha_modificacion']
    list_filter = ['es_activo', 'fecha_creacion']
    search_fields = ['group__name']
    readonly_fields = ['fecha_creacion', 'fecha_modificacion']
    
    def name(self, obj):
        return obj.group.name
    name.short_description = 'Nombre del Grupo'
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('group')

# Registrar modelos de Django estándar si es necesario
# admin.site.register(Group)
# admin.site.register(Permission)
