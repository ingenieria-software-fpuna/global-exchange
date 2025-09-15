from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone


class MetodoPago(models.Model):
    """Modelo para representar métodos de pago."""
    nombre = models.CharField(
        max_length=100,
        unique=True,
        help_text="Nombre del método de pago (ej: Efectivo, Tarjeta de Crédito)"
    )
    descripcion = models.TextField(
        blank=True,
        help_text="Descripción breve del método de pago"
    )
    comision = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Porcentaje de comisión aplicado (0 a 100)"
    )
    es_activo = models.BooleanField(
        default=True,
        help_text="Indica si el método está activo"
    )
    fecha_creacion = models.DateTimeField(
        default=timezone.now,
        help_text="Fecha y hora de creación del registro"
    )
    fecha_actualizacion = models.DateTimeField(
        auto_now=True,
        help_text="Fecha y hora de la última actualización"
    )

    class Meta:
        verbose_name = "Método de Pago"
        verbose_name_plural = "Métodos de Pago"
        ordering = ['nombre']
        db_table = 'metodo_pago_metodopago'

    def __str__(self):
        return self.nombre

