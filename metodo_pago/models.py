from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from monedas.models import Moneda


class Campo(models.Model):
    """Modelo genérico para campos de métodos de pago."""
    TIPOS_CAMPO = [
        ('text', 'Texto'),
        ('number', 'Número'),
        ('email', 'Email'),
        ('phone', 'Teléfono'),
        ('select', 'Selección'),
        ('textarea', 'Área de texto'),
    ]
    
    nombre = models.CharField(
        max_length=100,
        unique=True,
        help_text="Nombre del campo (ej: numero_telefono, documento)"
    )
    etiqueta = models.CharField(
        max_length=100,
        help_text="Etiqueta a mostrar en el formulario"
    )
    tipo = models.CharField(
        max_length=20,
        choices=TIPOS_CAMPO,
        default='text',
        help_text="Tipo de campo HTML"
    )
    es_obligatorio = models.BooleanField(
        default=True,
        help_text="Indica si el campo es obligatorio"
    )
    max_length = models.PositiveIntegerField(
        null=True,
        blank=True,
        help_text="Longitud máxima del campo"
    )
    regex_validacion = models.CharField(
        max_length=500,
        blank=True,
        help_text="Expresión regular para validación"
    )
    placeholder = models.CharField(
        max_length=200,
        blank=True,
        help_text="Texto de ayuda para el campo"
    )
    opciones = models.TextField(
        blank=True,
        help_text="Opciones para campos de selección (una por línea)"
    )
    es_activo = models.BooleanField(
        default=True,
        help_text="Indica si el campo está activo"
    )
    fecha_creacion = models.DateTimeField(
        default=timezone.now,
        help_text="Fecha y hora de creación del registro"
    )

    class Meta:
        verbose_name = "Campo"
        verbose_name_plural = "Campos"
        ordering = ['nombre']
        db_table = 'metodo_pago_campo'

    def __str__(self):
        return f"{self.nombre} ({self.etiqueta})"

    def get_opciones_list(self):
        """Retorna las opciones como lista"""
        if self.opciones:
            return [opcion.strip() for opcion in self.opciones.split('\n') if opcion.strip()]
        return []


class MetodoPago(models.Model):
    """Modelo para representar métodos de pago."""
    nombre = models.CharField(
        max_length=100,
        unique=True,
        help_text="Nombre del método de pago (ej: Efectivo, Tarjeta de Crédito)"
    )
    descripcion = models.TextField(
        blank=True,
        help_text="Descripción breve del método de pago"
    )
    comision = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text="Porcentaje de comisión aplicado (0 a 100)"
    )
    es_activo = models.BooleanField(
        default=True,
        help_text="Indica si el método está activo"
    )
    monedas_permitidas = models.ManyToManyField(
        Moneda,
        help_text="Monedas en las que se puede usar este método de pago"
    )
    campos = models.ManyToManyField(
        Campo,
        blank=True,
        help_text="Campos específicos requeridos para este método de pago"
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
        verbose_name = "Método de Pago"
        verbose_name_plural = "Métodos de Pago"
        ordering = ['nombre']
        db_table = 'metodo_pago_metodopago'

    def __str__(self):
        return self.nombre

    def get_monedas_permitidas_str(self):
        """Retorna las monedas permitidas como string separado por comas"""
        return ", ".join([moneda.codigo for moneda in self.monedas_permitidas.all()])

    def permite_moneda(self, moneda):
        """Verifica si el método permite una moneda específica"""
        return self.monedas_permitidas.filter(id=moneda.id).exists()

    def get_campos_activos(self):
        """Retorna los campos activos del método de pago"""
        return self.campos.filter(es_activo=True).order_by('nombre')

