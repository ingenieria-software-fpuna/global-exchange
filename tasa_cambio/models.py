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
    precio_base = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        help_text="Precio base de la moneda en guaraníes (valor entero)",
        default=1
    )
    comision_compra = models.PositiveIntegerField(
        validators=[MinValueValidator(0)],
        help_text="Comisión en guaraníes que se resta al precio base para obtener el precio de compra",
        default=0
    )
    comision_venta = models.PositiveIntegerField(
        validators=[MinValueValidator(0)],
        help_text="Comisión en guaraníes que se suma al precio base para obtener el precio de venta",
        default=0
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
        verbose_name = "Cotización"
        verbose_name_plural = "Cotizaciones"
        ordering = ['-fecha_creacion', 'moneda__nombre']
        db_table = 'tasa_cambio_tasacambio'

    def __str__(self):
        return f"{self.moneda.nombre}: Base {self.precio_base} - Com. C/V {self.comision_compra}/{self.comision_venta}"

    @property
    def tasa_compra(self):
        """
        Propiedad de compatibilidad que devuelve el precio de compra calculado
        """
        return self.precio_base - self.comision_compra

    @property
    def tasa_venta(self):
        """
        Propiedad de compatibilidad que devuelve el precio de venta calculado
        """
        return self.precio_base + self.comision_venta

    def save(self, *args, **kwargs):
        # Usar transacción para asegurar que la desactivación se ejecute antes de guardar
        with transaction.atomic():
            # Si es una nueva cotización o se está activando, desactivar las anteriores de la misma moneda
            if not self.pk or (self.pk and self.es_activa):
                TasaCambio.objects.filter(
                    moneda=self.moneda,
                    es_activa=True
                ).exclude(pk=self.pk).update(es_activa=False)

                # Cancelar transacciones pendientes que usen esta moneda
                # Importar aquí para evitar importación circular
                from transacciones.models import Transaccion
                canceladas = Transaccion.cancelar_pendientes_por_moneda(self.moneda)

                # Log opcional para debugging (se puede quitar en producción)
                if canceladas > 0:
                    print(f"Canceladas {canceladas} transacciones pendientes por cambio de tasa para {self.moneda.codigo}")

            super().save(*args, **kwargs)

    @property
    def spread(self): 
        """
        Calcula el spread (diferencia entre venta y compra)
        """
        return (self.precio_base + self.comision_venta) - (self.precio_base - self.comision_compra)

    @property
    def spread_porcentual(self):
        """
        Calcula el spread como porcentaje
        """
        precio_compra = self.precio_base - self.comision_compra
        if precio_compra > 0:
            precio_venta = self.precio_base + self.comision_venta
            return ((precio_venta - precio_compra) / precio_compra) * 100
        return 0

    @property
    def margen_total(self):
        """
        Calcula el margen total (suma de comisiones)
        """
        return self.comision_compra + self.comision_venta

    @property
    def margen_porcentual(self):
        """
        Calcula el margen total como porcentaje del precio base
        """
        if self.precio_base > 0:
            return (self.margen_total / self.precio_base) * 100
        return 0

    def formatear_precio_base(self):
        """
        Formatea el precio base según los decimales de la moneda
        """
        return self.moneda.formatear_monto(self.precio_base)

    def formatear_tasa_compra(self):
        """
        Formatea la tasa de compra según los decimales de la moneda
        """
        return self.moneda.formatear_monto(self.precio_base - self.comision_compra)

    def formatear_tasa_venta(self):
        """
        Formatea la tasa de venta según los decimales de la moneda
        """
        return self.moneda.formatear_monto(self.precio_base + self.comision_venta)
    