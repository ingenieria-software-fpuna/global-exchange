from django.db import models, transaction
from django.core.validators import MinValueValidator
from django.core.exceptions import ValidationError
from django.utils import timezone


class ConfiguracionSistema(models.Model):
    """
    Modelo para configuraciones globales del sistema.
    """
    limite_diario_transacciones = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name="Límite Diario de Transacciones",
        help_text="Monto máximo permitido para transacciones por día. 0 = sin límite."
    )
    limite_mensual_transacciones = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name="Límite Mensual de Transacciones",
        help_text="Monto máximo permitido para transacciones por mes. 0 = sin límite."
    )
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de creación"
    )
    fecha_actualizacion = models.DateTimeField(
        auto_now=True,
        verbose_name="Fecha de actualización"
    )

    class Meta:
        verbose_name = "Configuración del Sistema"
        verbose_name_plural = "Configuraciones del Sistema"
        db_table = 'configuracion_sistema'

    def __str__(self):
        return f"Configuración del Sistema - {self.fecha_actualizacion.strftime('%d/%m/%Y %H:%M')}"

    def save(self, *args, **kwargs):
        # Asegurar que solo exista una instancia de configuración
        if not self.pk and ConfiguracionSistema.objects.exists():
            # Si ya existe una configuración, actualizar la existente
            existing = ConfiguracionSistema.objects.first()
            existing.limite_diario_transacciones = self.limite_diario_transacciones
            existing.limite_mensual_transacciones = self.limite_mensual_transacciones
            existing.save()
            return existing
        super().save(*args, **kwargs)

    @classmethod
    def get_configuracion(cls):
        """
        Obtiene la configuración del sistema, creando una instancia por defecto si no existe.
        """
        config, created = cls.objects.get_or_create(
            defaults={
                'limite_diario_transacciones': 0,
                'limite_mensual_transacciones': 0,
            }
        )
        return config


class ContadorDocumentoFactura(models.Model):
    """
    Contador auto-incremental para números de documentos de facturas electrónicas.
    Usa locking a nivel de base de datos para garantizar thread-safety.
    """
    numero_actual = models.IntegerField(
        default=501,
        verbose_name="Número Actual",
        help_text="Número actual del documento (ejemplo: 501 para 0000501)"
    )
    numero_minimo = models.IntegerField(
        default=501,
        verbose_name="Número Mínimo",
        help_text="Número mínimo permitido del rango"
    )
    numero_maximo = models.IntegerField(
        default=550,
        verbose_name="Número Máximo",
        help_text="Número máximo permitido del rango"
    )
    formato_longitud = models.IntegerField(
        default=7,
        verbose_name="Longitud del Formato",
        help_text="Cantidad de dígitos para formatear (ejemplo: 7 para 0000501)"
    )
    fecha_actualizacion = models.DateTimeField(
        auto_now=True,
        verbose_name="Fecha de última actualización"
    )
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de creación"
    )

    class Meta:
        verbose_name = "Contador de Documentos de Factura"
        verbose_name_plural = "Contadores de Documentos de Factura"
        db_table = 'contador_documento_factura'

    def __str__(self):
        return f"Contador: {self.get_numero_formateado()} (rango: {self.numero_minimo}-{self.numero_maximo})"

    def clean(self):
        """Validación del modelo"""
        if self.numero_actual < self.numero_minimo:
            raise ValidationError(
                f"El número actual ({self.numero_actual}) no puede ser menor que el mínimo ({self.numero_minimo})"
            )
        if self.numero_actual > self.numero_maximo:
            raise ValidationError(
                f"El número actual ({self.numero_actual}) no puede ser mayor que el máximo ({self.numero_maximo})"
            )
        if self.numero_minimo > self.numero_maximo:
            raise ValidationError(
                f"El número mínimo ({self.numero_minimo}) no puede ser mayor que el máximo ({self.numero_maximo})"
            )

    def save(self, *args, **kwargs):
        self.clean()
        # Asegurar que solo exista una instancia
        if not self.pk and ContadorDocumentoFactura.objects.exists():
            raise ValidationError("Ya existe un contador de documentos. Modifica el existente.")
        super().save(*args, **kwargs)

    def get_numero_formateado(self):
        """Retorna el número actual formateado con ceros a la izquierda"""
        return str(self.numero_actual).zfill(self.formato_longitud)

    @classmethod
    @transaction.atomic
    def obtener_siguiente_numero(cls):
        """
        Obtiene el siguiente número de documento de manera thread-safe.

        Returns:
            str: Número de documento formateado (ejemplo: "0000501")

        Raises:
            ValidationError: Si se alcanzó el límite máximo del rango
        """
        # Usar select_for_update para bloquear la fila durante la transacción
        contador = cls.objects.select_for_update().first()

        if not contador:
            # Crear contador si no existe
            contador = cls.objects.create(
                numero_actual=501,
                numero_minimo=501,
                numero_maximo=550,
                formato_longitud=7
            )

        # Verificar que no se exceda el máximo
        if contador.numero_actual > contador.numero_maximo:
            raise ValidationError(
                f"Se alcanzó el límite máximo de documentos ({contador.numero_maximo}). "
                f"Por favor, contacte al administrador para obtener un nuevo rango."
            )

        # Obtener el número actual formateado
        numero_formateado = contador.get_numero_formateado()

        # Incrementar para la próxima vez
        contador.numero_actual += 1
        contador.save()

        return numero_formateado

    @classmethod
    def get_contador(cls):
        """
        Obtiene el contador actual, creando uno por defecto si no existe.
        """
        contador, created = cls.objects.get_or_create(
            defaults={
                'numero_actual': 501,
                'numero_minimo': 501,
                'numero_maximo': 550,
                'formato_longitud': 7,
            }
        )
        return contador
