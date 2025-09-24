from django.db import models
from django.utils import timezone


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
