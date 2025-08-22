from django.db import models

# Create your models here.

class TipoCliente(models.Model):
    nombre = models.CharField(max_length=100, unique=True, verbose_name="Nombre del tipo")
    descripcion = models.TextField(blank=True, null=True, verbose_name="Descripción")
    activo = models.BooleanField(default=True, verbose_name="Activo")
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")
    fecha_modificacion = models.DateTimeField(auto_now=True, verbose_name="Fecha de modificación")

    class Meta:
        verbose_name = "Tipo de Cliente"
        verbose_name_plural = "Tipos de Cliente"
        ordering = ['nombre']

    def __str__(self):
        return self.nombre

# Modelo Cliente (para el futuro)
class Cliente(models.Model):
    # Este modelo lo implementaremos más adelante
    pass
