from django.db import models, transaction
from django.core.validators import MinValueValidator
from django.utils import timezone
from monedas.models import Moneda


class TasaCambio(models.Model):
    """
    Modelo para representar las cotizaciones de divisas del sistema.
    """
    moneda = models.ForeignKey(
        Moneda,
        on_delete=models.CASCADE,
        related_name='tasas_cambio',
        help_text="Moneda para la cual se establece la cotización"
    )
    tasa_compra = models.DecimalField(
        max_digits=15,
        decimal_places=8,
        validators=[MinValueValidator(0.00000001)],
        help_text="Tasa de compra de la moneda (precio al que se compra)"
    )
    tasa_venta = models.DecimalField(
        max_digits=15,
        decimal_places=8,
        validators=[MinValueValidator(0.00000001)],
        help_text="Tasa de venta de la moneda (precio al que se vende)"
    )
    fecha_vigencia = models.DateTimeField(
        default=timezone.now,
        help_text="Fecha y hora desde la cual la cotización está vigente"
    )
    es_activa = models.BooleanField(
        default=True,
        help_text="Indica si la cotización está activa para operaciones"
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
        verbose_name = "Tasa de Cambio"
        verbose_name_plural = "Tasas de Cambio"
        ordering = ['-fecha_vigencia', 'moneda__nombre']
        db_table = 'tasa_cambio_tasacambio'

    def __str__(self):
        return f"{self.moneda.nombre}: Compra {self.tasa_compra} - Venta {self.tasa_venta}"

    def save(self, *args, **kwargs):
        # Usar transacción para asegurar que la desactivación se ejecute antes de guardar
        with transaction.atomic():
            # Si es una nueva cotización o se está activando, desactivar las anteriores de la misma moneda
            if not self.pk or (self.pk and self.es_activa):
                TasaCambio.objects.filter(
                    moneda=self.moneda,
                    es_activa=True
                ).exclude(pk=self.pk).update(es_activa=False)
            super().save(*args, **kwargs)

    @property
    def spread(self): 
        """
        Calcula el spread (diferencia entre venta y compra)
        """
        return self.tasa_venta - self.tasa_compra

    @property
    def spread_porcentual(self):
        """
        Calcula el spread como porcentaje
        """
        if self.tasa_compra > 0:
            return ((self.tasa_venta - self.tasa_compra) / self.tasa_compra) * 100
        return 0

    def formatear_tasa_compra(self):
        """
        Formatea la tasa de compra según los decimales de la moneda
        """
        return self.moneda.formatear_monto(self.tasa_compra)

    def formatear_tasa_venta(self):
        """
        Formatea la tasa de venta según los decimales de la moneda
        """
        return self.moneda.formatear_monto(self.tasa_venta)
    