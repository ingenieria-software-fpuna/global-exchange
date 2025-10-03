from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator
from monedas.models import Moneda


class Tauser(models.Model):
    """Modelo para representar un Tauser (punto de atención)"""
    
    nombre = models.CharField(
        max_length=100,
        verbose_name='Nombre',
        help_text='Nombre del punto de atención'
    )
    direccion = models.CharField(
        max_length=255,
        verbose_name='Dirección',
        help_text='Dirección física del punto de atención'
    )
    horario_atencion = models.CharField(
        max_length=100,
        verbose_name='Horario de Atención',
        help_text='Horario de funcionamiento del punto'
    )
    es_activo = models.BooleanField(
        default=True,
        verbose_name='Activo',
        help_text='Indica si el punto está activo'
    )
    fecha_instalacion = models.DateTimeField(
        default=timezone.now,
        verbose_name='Fecha de Instalación',
        help_text='Fecha en que se instaló el punto'
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Tauser'
        verbose_name_plural = 'Tausers'
        ordering = ['nombre']
        permissions = [
            ('deactivate_tauser', 'Can deactivate tauser'),
        ]

    def __str__(self):
        return f"{self.nombre} - {'Activo' if self.es_activo else 'Inactivo'}"

    def toggle_activo(self):
        """Cambiar el estado activo/inactivo"""
        self.es_activo = not self.es_activo
        self.save()
        return self.es_activo


class Stock(models.Model):
    """Modelo para representar el stock de monedas en cada Tauser"""
    
    tauser = models.ForeignKey(
        Tauser,
        on_delete=models.CASCADE,
        related_name='stocks',
        verbose_name='Tauser',
        help_text='Punto de atención al que pertenece este stock'
    )
    moneda = models.ForeignKey(
        Moneda,
        on_delete=models.CASCADE,
        verbose_name='Moneda',
        help_text='Moneda del stock'
    )
    cantidad = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name='Cantidad',
        help_text='Cantidad disponible en stock'
    )
    cantidad_minima = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        default=0,
        verbose_name='Cantidad Mínima',
        help_text='Cantidad mínima antes de alertar'
    )
    es_activo = models.BooleanField(
        default=True,
        verbose_name='Activo',
        help_text='Indica si este stock está activo'
    )
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha de Creación'
    )
    fecha_actualizacion = models.DateTimeField(
        auto_now=True,
        verbose_name='Fecha de Actualización'
    )

    class Meta:
        verbose_name = 'Stock'
        verbose_name_plural = 'Stocks'
        unique_together = ['tauser', 'moneda']
        ordering = ['tauser', 'moneda']
        permissions = [
            ('manage_stock', 'Can manage stock'),
        ]

    def __str__(self):
        return f"{self.tauser.nombre} - {self.moneda.nombre}: {self.cantidad}"

    def esta_bajo_stock(self):
        """Verifica si el stock está por debajo del mínimo"""
        return self.cantidad <= self.cantidad_minima

    def agregar_cantidad(self, cantidad):
        """Agrega cantidad al stock"""
        if cantidad > 0:
            self.cantidad += cantidad
            self.save()
            return True
        return False

    def reducir_cantidad(self, cantidad):
        """Reduce cantidad del stock"""
        if cantidad > 0 and self.cantidad >= cantidad:
            self.cantidad -= cantidad
            self.save()
            return True
        return False

    def formatear_cantidad(self):
        """Formatea la cantidad según los decimales de la moneda"""
        return self.moneda.formatear_monto(self.cantidad)

    def mostrar_cantidad(self):
        """Muestra la cantidad con el símbolo de la moneda"""
        return self.moneda.mostrar_monto(self.cantidad)
