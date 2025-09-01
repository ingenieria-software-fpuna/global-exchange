from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone


class Moneda(models.Model):
    """
    Modelo para representar las monedas del sistema.
    """
    nombre = models.CharField(
        max_length=100,
        unique=True,
        help_text="Nombre completo de la moneda (ej: Dólar Estadounidense)"
    )
    codigo = models.CharField(
        max_length=3,
        unique=True,
        help_text="Código ISO 4217 de la moneda (ej: USD, EUR, PYG)"
    )
    simbolo = models.CharField(
        max_length=5,
        help_text="Símbolo de la moneda (ej: $, €, ₲)"
    )
    decimales = models.PositiveSmallIntegerField(
        default=2,
        validators=[MinValueValidator(0)],
        help_text="Número de decimales que usa la moneda (ej: 2 para USD, 0 para JPY)"
    )
    es_activa = models.BooleanField(
        default=True,
        help_text="Indica si la moneda está activa para operaciones"
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
        verbose_name = "Moneda"
        verbose_name_plural = "Monedas"
        ordering = ['nombre']
        db_table = 'monedas_moneda'

    def __str__(self):
        return f"{self.nombre} ({self.codigo})"

    def save(self, *args, **kwargs):
        # Convertir código a mayúsculas
        self.codigo = self.codigo.upper()
        super().save(*args, **kwargs)
    
    def formatear_monto(self, monto):
        """
        Formatea un monto según el número de decimales de la moneda
        """
        formato = f"{{:.{self.decimales}f}}"
        return formato.format(float(monto))
    
    def mostrar_monto(self, monto):
        """
        Muestra un monto con el símbolo y decimales apropiados
        """
        monto_formateado = self.formatear_monto(monto)
        return f"{self.simbolo}{monto_formateado}"
