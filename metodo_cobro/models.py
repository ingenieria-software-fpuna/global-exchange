from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from monedas.models import Moneda


class MetodoCobro(models.Model):
    """Modelo para representar métodos de cobro."""
    nombre = models.CharField(
        max_length=100,
        unique=True,
        help_text="Nombre del método de cobro (ej: Efectivo, Transferencia bancaria)"
    )
    descripcion = models.TextField(
        blank=True,
        help_text="Descripción breve del método de cobro"
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
    monedas_permitidas = models.ManyToManyField(
        Moneda,
        help_text="Monedas en las que se puede usar este método de cobro"
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
        verbose_name = "Método de Cobro"
        verbose_name_plural = "Métodos de Cobro"
        ordering = ['nombre']
        db_table = 'metodo_cobro_metodocobro'

    def __str__(self):
        return self.nombre

    def get_monedas_permitidas_str(self):
        """Retorna las monedas permitidas como string separado por comas"""
        return ", ".join([moneda.codigo for moneda in self.monedas_permitidas.all()])

    def permite_moneda(self, moneda):
        """Verifica si el método permite una moneda específica"""
        return self.monedas_permitidas.filter(id=moneda.id).exists()