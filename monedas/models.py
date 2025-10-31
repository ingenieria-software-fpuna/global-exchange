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
    monto_limite_transaccion = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(0)],
        help_text="Monto máximo permitido para una sola transacción en esta moneda. Vacío = sin límite."
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


class DenominacionMoneda(models.Model):
    """
    Modelo para representar las denominaciones (billetes/monedas) de cada moneda.
    """
    TIPO_DENOMINACION_CHOICES = [
        ('BILLETE', 'Billete'),
        ('MONEDA', 'Moneda'),
    ]
    
    moneda = models.ForeignKey(
        Moneda,
        on_delete=models.CASCADE,
        related_name='denominaciones',
        verbose_name='Moneda',
        help_text='Moneda a la que pertenece esta denominación'
    )
    valor = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name='Valor',
        help_text='Valor de la denominación (ej: 1000, 500, 50, 1)'
    )
    tipo = models.CharField(
        max_length=10,
        choices=TIPO_DENOMINACION_CHOICES,
        verbose_name='Tipo',
        help_text='Si es billete o moneda'
    )
    es_activa = models.BooleanField(
        default=True,
        verbose_name='Activa',
        help_text='Indica si esta denominación está activa'
    )
    orden = models.PositiveIntegerField(
        default=0,
        verbose_name='Orden',
        help_text='Orden de visualización (mayor a menor)'
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
        verbose_name = 'Denominación de Moneda'
        verbose_name_plural = 'Denominaciones de Monedas'
        unique_together = ['moneda', 'valor', 'tipo']
        ordering = ['moneda', '-valor', 'tipo']
        db_table = 'monedas_denominacionmoneda'

    def __str__(self):
        return f"{self.moneda.codigo} - {self.tipo} {self.valor}"

    def save(self, *args, **kwargs):
        # Si no se especifica orden, calcular automáticamente
        if self.orden == 0:
            max_orden = DenominacionMoneda.objects.filter(
                moneda=self.moneda
            ).aggregate(
                max_orden=models.Max('orden')
            )['max_orden'] or 0
            self.orden = max_orden + 1
        super().save(*args, **kwargs)

    def formatear_valor(self):
        """Formatea el valor según los decimales de la moneda"""
        return self.moneda.formatear_monto(self.valor)

    def mostrar_denominacion(self):
        """Muestra la denominación con el símbolo de la moneda"""
        valor_formateado = self.formatear_valor()
        return f"{self.moneda.simbolo}{valor_formateado} ({self.tipo})"
