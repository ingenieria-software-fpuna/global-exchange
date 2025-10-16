from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from monedas.models import Moneda

Usuario = get_user_model()


class Notificacion(models.Model):
    """
    Modelo para representar notificaciones de cambios en tasas de cambio a los usuarios.
    """
    TIPO_CHOICES = [
        ('tasa_cambio', 'Cambio de Tasa'),
    ]

    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='notificaciones',
        help_text="Usuario que recibe la notificación"
    )
    tipo = models.CharField(
        max_length=20,
        choices=TIPO_CHOICES,
        default='tasa_cambio',
        help_text="Tipo de notificación"
    )
    titulo = models.CharField(
        max_length=200,
        help_text="Título de la notificación"
    )
    mensaje = models.TextField(
        help_text="Mensaje detallado de la notificación"
    )
    moneda = models.ForeignKey(
        Moneda,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notificaciones',
        help_text="Moneda relacionada (si aplica)"
    )
    leida = models.BooleanField(
        default=False,
        help_text="Indica si la notificación fue leída"
    )
    fecha_creacion = models.DateTimeField(
        default=timezone.now,
        help_text="Fecha y hora de creación"
    )
    fecha_lectura = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Fecha y hora en que se leyó la notificación"
    )

    # Campos adicionales para contexto de tasa de cambio
    precio_base_anterior = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Precio base anterior (si aplica)"
    )
    precio_base_nuevo = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Precio base nuevo (si aplica)"
    )
    comision_compra_anterior = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Comisión de compra anterior (si aplica)"
    )
    comision_compra_nueva = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Comisión de compra nueva (si aplica)"
    )
    comision_venta_anterior = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Comisión de venta anterior (si aplica)"
    )
    comision_venta_nueva = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Comisión de venta nueva (si aplica)"
    )

    class Meta:
        verbose_name = "Notificación"
        verbose_name_plural = "Notificaciones"
        ordering = ['-fecha_creacion']
        db_table = 'notificaciones_notificacion'
        indexes = [
            models.Index(fields=['usuario', '-fecha_creacion']),
            models.Index(fields=['usuario', 'leida']),
        ]

    def __str__(self):
        return f"{self.usuario.email} - {self.titulo}"

    def marcar_como_leida(self):
        """Marca la notificación como leída"""
        if not self.leida:
            self.leida = True
            self.fecha_lectura = timezone.now()
            self.save(update_fields=['leida', 'fecha_lectura'])

    @property
    def cambio_porcentual(self):
        """Calcula el cambio porcentual si hay precios disponibles"""
        if self.precio_base_anterior and self.precio_base_nuevo:
            if self.precio_base_anterior > 0:
                cambio = ((self.precio_base_nuevo - self.precio_base_anterior) / 
                         self.precio_base_anterior) * 100
                return round(cambio, 2)
        return None

    @property
    def es_aumento(self):
        """Determina si el cambio es un aumento"""
        if self.precio_base_anterior and self.precio_base_nuevo:
            return self.precio_base_nuevo > self.precio_base_anterior
        return None

    @property
    def tasa_compra_anterior(self):
        """Calcula la tasa de compra anterior"""
        if self.precio_base_anterior is not None and self.comision_compra_anterior is not None:
            return self.precio_base_anterior - self.comision_compra_anterior
        return None

    @property
    def tasa_compra_nueva(self):
        """Calcula la tasa de compra nueva"""
        if self.precio_base_nuevo is not None and self.comision_compra_nueva is not None:
            return self.precio_base_nuevo - self.comision_compra_nueva
        return None

    @property
    def tasa_venta_anterior(self):
        """Calcula la tasa de venta anterior"""
        if self.precio_base_anterior is not None and self.comision_venta_anterior is not None:
            return self.precio_base_anterior + self.comision_venta_anterior
        return None

    @property
    def tasa_venta_nueva(self):
        """Calcula la tasa de venta nueva"""
        if self.precio_base_nuevo is not None and self.comision_venta_nueva is not None:
            return self.precio_base_nuevo + self.comision_venta_nueva
        return None
