from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone


class ConfiguracionSistema(models.Model):
    """
    Modelo para configuraciones globales del sistema.
    """
    limite_diario_transacciones = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name="Límite Diario de Transacciones",
        help_text="Monto máximo permitido para transacciones por día. 0 = sin límite."
    )
    limite_mensual_transacciones = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name="Límite Mensual de Transacciones",
        help_text="Monto máximo permitido para transacciones por mes. 0 = sin límite."
    )
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de creación"
    )
    fecha_actualizacion = models.DateTimeField(
        auto_now=True,
        verbose_name="Fecha de actualización"
    )

    class Meta:
        verbose_name = "Configuración del Sistema"
        verbose_name_plural = "Configuraciones del Sistema"
        db_table = 'configuracion_sistema'

    def __str__(self):
        return f"Configuración del Sistema - {self.fecha_actualizacion.strftime('%d/%m/%Y %H:%M')}"

    def save(self, *args, **kwargs):
        # Asegurar que solo exista una instancia de configuración
        if not self.pk and ConfiguracionSistema.objects.exists():
            # Si ya existe una configuración, actualizar la existente
            existing = ConfiguracionSistema.objects.first()
            existing.limite_diario_transacciones = self.limite_diario_transacciones
            existing.limite_mensual_transacciones = self.limite_mensual_transacciones
            existing.save()
            return existing
        super().save(*args, **kwargs)

    @classmethod
    def get_configuracion(cls):
        """
        Obtiene la configuración del sistema, creando una instancia por defecto si no existe.
        """
        config, created = cls.objects.get_or_create(
            defaults={
                'limite_diario_transacciones': 0,
                'limite_mensual_transacciones': 0,
            }
        )
        return config
