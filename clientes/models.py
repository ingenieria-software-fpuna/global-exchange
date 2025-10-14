from django.db import models
from django.core.validators import RegexValidator, MinValueValidator
from django.core.exceptions import ValidationError

# Create your models here.

class TipoCliente(models.Model):
    nombre = models.CharField(max_length=100, unique=True, verbose_name="Nombre del tipo")
    descripcion = models.TextField(blank=True, null=True, verbose_name="Descripción")
    descuento = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, verbose_name="Descuento (%)")
    activo = models.BooleanField(default=True, verbose_name="Activo")
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")
    fecha_modificacion = models.DateTimeField(auto_now=True, verbose_name="Fecha de modificación")

    class Meta:
        verbose_name = "Tipo de Cliente"
        verbose_name_plural = "Tipos de Cliente"
        ordering = ['nombre']

    def __str__(self):
        return self.nombre

class Cliente(models.Model):
    nombre_comercial = models.CharField(
        max_length=200, 
        verbose_name="Nombre Comercial",
        help_text="Nombre comercial o razón social del cliente"
    )
    ruc = models.CharField(
        max_length=20, 
        unique=True, 
        verbose_name="RUC",
        help_text="Número de RUC del cliente",
        validators=[
            RegexValidator(
                regex=r'^\d{5,20}$',
                message='El RUC debe contener solo números y tener entre 5 y 20 dígitos.'
            )
        ]
    )
    direccion = models.TextField(
        verbose_name="Dirección",
        help_text="Dirección completa del cliente",
        blank=True,
        null=True
    )
    correo_electronico = models.EmailField(
        verbose_name="Correo Electrónico",
        help_text="Correo electrónico de contacto del cliente",
        null=True,
        blank=True
    )
    numero_telefono = models.CharField(
        max_length=20, 
        verbose_name="Número de Teléfono",
        help_text="Número de teléfono de contacto",
        blank=True,
        null=True,
        validators=[
            RegexValidator(
                regex=r'^[\d\s\-\+\(\)]+$',
                message='El número de teléfono debe contener solo números, espacios, guiones, paréntesis y el símbolo +.'
            )
        ]
    )
    tipo_cliente = models.ForeignKey(
        TipoCliente,
        on_delete=models.PROTECT,
        verbose_name="Tipo de Cliente",
        help_text="Tipo de cliente que determina el descuento aplicable"
    )
    usuarios_asociados = models.ManyToManyField(
        'usuarios.Usuario',
        blank=True,
        verbose_name="Usuarios Asociados",
        help_text="Usuarios que pueden operar en nombre de este cliente"
    )
    monto_limite_transaccion = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(0)],
        verbose_name="Monto límite por transacción",
        help_text="Monto máximo permitido para una sola transacción. Dejar vacío para sin límite."
    )
    activo = models.BooleanField(
        default=True, 
        verbose_name="Activo",
        help_text="Indica si el cliente está activo en el sistema"
    )
    fecha_creacion = models.DateTimeField(
        auto_now_add=True, 
        verbose_name="Fecha de creación"
    )
    fecha_modificacion = models.DateTimeField(
        auto_now=True, 
        verbose_name="Fecha de modificación"
    )

    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        ordering = ['nombre_comercial']
        indexes = [
            models.Index(fields=['ruc']),
            models.Index(fields=['nombre_comercial']),
            models.Index(fields=['tipo_cliente']),
            models.Index(fields=['activo']),
        ]
        permissions = [
            ("can_view_all_clients", "Puede ver todos los clientes"),
            ("can_view_sensitive_columns", "Puede ver columnas sensibles (usuarios asociados, estado, fecha creación)"),
        ]

    def __str__(self):
        return f"{self.nombre_comercial} ({self.ruc})"

    def clean(self):
        """Validación personalizada del modelo"""
        super().clean()
        
        # Validaciones personalizadas del modelo Cliente
        # (Se removió la validación de tipo de cliente activo)

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)
