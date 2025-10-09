from django.db import models


class PagoPasarela(models.Model):
    """
    Modelo para registrar los pagos procesados a través de la pasarela de pagos.
    """
    
    ESTADO_CHOICES = [
        ('exito', 'Éxito'),
        ('fallo', 'Fallo'),
        ('pendiente', 'Pendiente'),
    ]
    
    # Relación con la transacción
    transaccion = models.ForeignKey(
        'transacciones.Transaccion',
        on_delete=models.CASCADE,
        related_name='pagos_pasarela',
        verbose_name="Transacción"
    )
    
    # Información del pago en la pasarela
    id_pago_externo = models.CharField(
        max_length=100,
        unique=True,
        verbose_name="ID Pago Externo",
        help_text="ID del pago en la pasarela externa"
    )
    
    monto = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        verbose_name="Monto"
    )
    
    metodo_pasarela = models.CharField(
        max_length=50,
        verbose_name="Método en Pasarela",
        help_text="Método de pago según la pasarela (tarjeta, billetera, transferencia)"
    )
    
    moneda = models.CharField(
        max_length=10,
        verbose_name="Moneda"
    )
    
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_CHOICES,
        verbose_name="Estado del Pago"
    )
    
    # Datos adicionales del pago
    datos_pago = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Datos del Pago",
        help_text="Información adicional del pago (datos de tarjeta enmascarados, etc.)"
    )
    
    # Información de respuesta de la pasarela
    respuesta_pasarela = models.JSONField(
        default=dict,
        blank=True,
        verbose_name="Respuesta de Pasarela",
        help_text="Respuesta completa de la pasarela de pagos"
    )
    
    # Fechas de control
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de Creación"
    )
    
    fecha_actualizacion = models.DateTimeField(
        auto_now=True,
        verbose_name="Fecha de Actualización"
    )
    
    fecha_procesamiento = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Fecha de Procesamiento",
        help_text="Fecha en que se procesó el pago en la pasarela"
    )
    
    # Información de error (si aplica)
    mensaje_error = models.TextField(
        blank=True,
        verbose_name="Mensaje de Error",
        help_text="Mensaje de error si el pago falló"
    )
    
    class Meta:
        verbose_name = "Pago de Pasarela"
        verbose_name_plural = "Pagos de Pasarela"
        ordering = ['-fecha_creacion']
        indexes = [
            models.Index(fields=['id_pago_externo']),
            models.Index(fields=['transaccion', '-fecha_creacion']),
            models.Index(fields=['estado', '-fecha_creacion']),
        ]
    
    def __str__(self):
        return f"Pago {self.id_pago_externo} - {self.transaccion.id_transaccion}"
    
    def es_exitoso(self):
        """Verifica si el pago fue exitoso"""
        return self.estado == 'exito'
    
    def es_fallido(self):
        """Verifica si el pago falló"""
        return self.estado == 'fallo'
    
    def es_pendiente(self):
        """Verifica si el pago está pendiente"""
        return self.estado == 'pendiente'
