from django.contrib import admin
from django.utils import timezone
from django.utils.html import format_html
from .models import CodigoVerificacion

@admin.register(CodigoVerificacion)
class CodigoVerificacionAdmin(admin.ModelAdmin):
    list_display = [
        'codigo_masked', 
        'usuario_email', 
        'tipo', 
        'estado_display',
        'fecha_creacion', 
        'tiempo_restante',
        'ip_address'
    ]
    list_filter = [
        'tipo', 
        'usado', 
        'fecha_creacion',
        ('fecha_expiracion', admin.DateFieldListFilter),
    ]
    search_fields = [
        'usuario__email', 
        'usuario__nombre', 
        'usuario__apellido',
        'codigo',
        'ip_address'
    ]
    readonly_fields = [
        'codigo', 
        'fecha_creacion', 
        'fecha_expiracion',
        'ip_address',
        'user_agent'
    ]
    ordering = ['-fecha_creacion']
    
    def codigo_masked(self, obj):
        """Muestra el código parcialmente oculto por seguridad"""
        if obj.codigo:
            return f"{'*' * 3}{obj.codigo[-3:]}"
        return "-"
    codigo_masked.short_description = "Código"
    
    def usuario_email(self, obj):
        """Muestra el email del usuario"""
        return obj.usuario.email
    usuario_email.short_description = "Usuario"
    
    def estado_display(self, obj):
        """Muestra el estado del código con colores"""
        if obj.usado:
            return format_html(
                '<span style="color: green; font-weight: bold;">✅ Usado</span>'
            )
        elif obj.fecha_expiracion < timezone.now():
            return format_html(
                '<span style="color: red; font-weight: bold;">❌ Expirado</span>'
            )
        else:
            return format_html(
                '<span style="color: blue; font-weight: bold;">⏳ Válido</span>'
            )
    estado_display.short_description = "Estado"
    
    def tiempo_restante(self, obj):
        """Muestra el tiempo restante para expiración"""
        if obj.usado:
            return "-"
        
        ahora = timezone.now()
        if obj.fecha_expiracion < ahora:
            tiempo_expirado = ahora - obj.fecha_expiracion
            return format_html(
                '<span style="color: red;">Expiró hace {}</span>',
                self._format_timedelta(tiempo_expirado)
            )
        else:
            tiempo_restante = obj.fecha_expiracion - ahora
            return format_html(
                '<span style="color: green;">Expira en {}</span>',
                self._format_timedelta(tiempo_restante)
            )
    tiempo_restante.short_description = "Tiempo restante"
    
    def _format_timedelta(self, td):
        """Formatea un timedelta de manera legible"""
        total_seconds = int(td.total_seconds())
        
        if total_seconds < 60:
            return f"{total_seconds}s"
        elif total_seconds < 3600:
            minutes = total_seconds // 60
            return f"{minutes}m"
        else:
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            return f"{hours}h {minutes}m"
    
    def has_add_permission(self, request):
        """No permitir crear códigos desde el admin"""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Solo permitir ver, no editar"""
        return False
    
    actions = ['marcar_como_usado', 'limpiar_expirados']
    
    def marcar_como_usado(self, request, queryset):
        """Acción para marcar códigos como usados"""
        count = 0
        for codigo in queryset:
            if not codigo.usado:
                codigo.marcar_como_usado()
                count += 1
        
        self.message_user(
            request,
            f"Se marcaron {count} códigos como usados."
        )
    marcar_como_usado.short_description = "Marcar como usados"
    
    def limpiar_expirados(self, request, queryset):
        """Acción para limpiar códigos expirados"""
        deleted_count, _ = CodigoVerificacion.limpiar_codigos_expirados()
        
        self.message_user(
            request,
            f"Se eliminaron {deleted_count[0]} códigos expirados."
        )
    limpiar_expirados.short_description = "Limpiar códigos expirados"
