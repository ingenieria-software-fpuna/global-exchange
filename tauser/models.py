from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator
from monedas.models import Moneda
from decimal import Decimal
from django.contrib.auth import get_user_model

User = get_user_model()



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
        return self.cantidad <= 0

    def agregar_cantidad(self, cantidad, usuario=None, transaccion=None, observaciones=''):
        """Agrega cantidad al stock y registra en historial"""
        if cantidad > 0:
            # Convertir a Decimal para mantener precisión
            cantidad_decimal = Decimal(str(cantidad))
            cantidad_anterior = self.cantidad
            self.cantidad = self.cantidad + cantidad_decimal
            self.save()
            
            # Registrar en historial
            HistorialStock.objects.create(
                stock=self,
                tipo_movimiento='ENTRADA',
                origen_movimiento='TRANSACCION' if transaccion else 'MANUAL',
                cantidad_movida=cantidad_decimal,
                cantidad_anterior=cantidad_anterior,
                cantidad_posterior=self.cantidad,
                usuario=usuario,
                transaccion=transaccion,
                observaciones=observaciones
            )
            return True
        return False

    def reducir_cantidad(self, cantidad, usuario=None, transaccion=None, observaciones=''):
        """Reduce cantidad del stock y registra en historial"""
        if cantidad > 0 and self.cantidad >= cantidad:
            # Convertir a Decimal para mantener precisión
            cantidad_decimal = Decimal(str(cantidad))
            cantidad_anterior = self.cantidad
            self.cantidad = self.cantidad - cantidad_decimal
            self.save()
            
            # Registrar en historial
            HistorialStock.objects.create(
                stock=self,
                tipo_movimiento='SALIDA',
                origen_movimiento='TRANSACCION' if transaccion else 'MANUAL',
                cantidad_movida=cantidad_decimal,
                cantidad_anterior=cantidad_anterior,
                cantidad_posterior=self.cantidad,
                usuario=usuario,
                transaccion=transaccion,
                observaciones=observaciones
            )
            return True
        return False

    def formatear_cantidad(self):
        """Formatea la cantidad según los decimales de la moneda"""
        return self.moneda.formatear_monto(self.cantidad)

    def mostrar_cantidad(self):
        """Muestra la cantidad con el símbolo de la moneda"""
        return self.moneda.mostrar_monto(self.cantidad)


class StockDenominacion(models.Model):
    """Modelo para representar el stock por denominación específica en cada Tauser"""
    
    stock = models.ForeignKey(
        Stock,
        on_delete=models.CASCADE,
        related_name='stock_denominaciones',
        verbose_name='Stock',
        help_text='Stock al que pertenece esta denominación'
    )
    denominacion = models.ForeignKey(
        'monedas.DenominacionMoneda',
        on_delete=models.CASCADE,
        verbose_name='Denominación',
        help_text='Denominación específica (billete/moneda)'
    )
    cantidad = models.PositiveIntegerField(
        default=0,
        verbose_name='Cantidad',
        help_text='Cantidad de billetes/monedas de esta denominación'
    )
    es_activo = models.BooleanField(
        default=True,
        verbose_name='Activo',
        help_text='Indica si este stock de denominación está activo'
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
        verbose_name = 'Stock por Denominación'
        verbose_name_plural = 'Stocks por Denominación'
        unique_together = ['stock', 'denominacion']
        ordering = ['stock', 'denominacion__valor']
        permissions = [
            ('manage_stock_denominacion', 'Can manage stock by denomination'),
        ]

    def __str__(self):
        return f"{self.stock.tauser.nombre} - {self.denominacion}: {self.cantidad} unidades"

    def esta_bajo_stock(self):
        """Verifica si el stock de esta denominación está por debajo del mínimo"""
        return self.cantidad <= 0

    def agregar_cantidad(self, cantidad, usuario=None, transaccion=None, observaciones=''):
        """Agrega cantidad al stock de denominación y registra en historial"""
        if cantidad > 0:
            cantidad_anterior = self.cantidad
            self.cantidad = self.cantidad + cantidad
            self.save()
            
            # Actualizar el stock general
            valor_total = cantidad * self.denominacion.valor
            self.stock.agregar_cantidad(valor_total, usuario, transaccion, observaciones)
            
            # Registrar en historial específico de denominación
            HistorialStockDenominacion.objects.create(
                stock_denominacion=self,
                tipo_movimiento='ENTRADA',
                origen_movimiento='TRANSACCION' if transaccion else 'MANUAL',
                cantidad_movida=cantidad,
                cantidad_anterior=cantidad_anterior,
                cantidad_posterior=self.cantidad,
                usuario=usuario,
                transaccion=transaccion,
                observaciones=observaciones
            )
            return True
        return False

    def reducir_cantidad(self, cantidad, usuario=None, transaccion=None, observaciones=''):
        """Reduce cantidad del stock de denominación y registra en historial"""
        if cantidad > 0 and self.cantidad >= cantidad:
            cantidad_anterior = self.cantidad
            self.cantidad = self.cantidad - cantidad
            self.save()
            
            # Actualizar el stock general
            valor_total = cantidad * self.denominacion.valor
            self.stock.reducir_cantidad(valor_total, usuario, transaccion, observaciones)
            
            # Registrar en historial específico de denominación
            HistorialStockDenominacion.objects.create(
                stock_denominacion=self,
                tipo_movimiento='SALIDA',
                origen_movimiento='TRANSACCION' if transaccion else 'MANUAL',
                cantidad_movida=cantidad,
                cantidad_anterior=cantidad_anterior,
                cantidad_posterior=self.cantidad,
                usuario=usuario,
                transaccion=transaccion,
                observaciones=observaciones
            )
            return True
        return False

    def valor_total(self):
        """Calcula el valor total de esta denominación en stock"""
        return self.cantidad * self.denominacion.valor

    def formatear_valor_total(self):
        """Formatea el valor total según los decimales de la moneda"""
        return self.stock.moneda.formatear_monto(self.valor_total())

    def mostrar_valor_total(self):
        """Muestra el valor total con el símbolo de la moneda"""
        return self.stock.moneda.mostrar_monto(self.valor_total())


class HistorialStockDenominacion(models.Model):
    """Modelo para registrar el historial de movimientos de stock por denominación"""
    
    TIPO_MOVIMIENTO_CHOICES = [
        ('ENTRADA', 'Entrada'),
        ('SALIDA', 'Salida'),
    ]
    
    ORIGEN_MOVIMIENTO_CHOICES = [
        ('MANUAL', 'Manual'),
        ('TRANSACCION', 'Transacción'),
    ]
    
    stock_denominacion = models.ForeignKey(
        StockDenominacion,
        on_delete=models.CASCADE,
        related_name='historial',
        verbose_name='Stock Denominación',
        help_text='Stock de denominación al que pertenece este movimiento'
    )
    tipo_movimiento = models.CharField(
        max_length=10,
        choices=TIPO_MOVIMIENTO_CHOICES,
        verbose_name='Tipo de Movimiento',
        help_text='Si es entrada o salida de stock'
    )
    origen_movimiento = models.CharField(
        max_length=15,
        choices=ORIGEN_MOVIMIENTO_CHOICES,
        verbose_name='Origen del Movimiento',
        help_text='Si fue manual o por transacción'
    )
    cantidad_movida = models.PositiveIntegerField(
        verbose_name='Cantidad Movida',
        help_text='Cantidad de billetes/monedas que se movió'
    )
    cantidad_anterior = models.PositiveIntegerField(
        verbose_name='Cantidad Anterior',
        help_text='Cantidad que había antes del movimiento'
    )
    cantidad_posterior = models.PositiveIntegerField(
        verbose_name='Cantidad Posterior',
        help_text='Cantidad que quedó después del movimiento'
    )
    usuario = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Usuario',
        help_text='Usuario que realizó el movimiento'
    )
    transaccion = models.ForeignKey(
        'transacciones.Transaccion',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Transacción',
        help_text='Transacción relacionada (si aplica)'
    )
    observaciones = models.TextField(
        blank=True,
        verbose_name='Observaciones',
        help_text='Observaciones adicionales del movimiento'
    )
    fecha_movimiento = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha del Movimiento',
        help_text='Fecha y hora en que se realizó el movimiento'
    )

    class Meta:
        verbose_name = 'Historial de Stock por Denominación'
        verbose_name_plural = 'Historial de Stocks por Denominación'
        ordering = ['-fecha_movimiento']
        permissions = [
            ('view_historial_stock_denominacion', 'Can view stock denomination history'),
        ]

    def __str__(self):
        return f"{self.stock_denominacion} - {self.tipo_movimiento} {self.cantidad_movida}"

    def valor_movido(self):
        """Calcula el valor total movido en esta operación"""
        return self.cantidad_movida * self.stock_denominacion.denominacion.valor

    def formatear_valor_movido(self):
        """Formatea el valor movido según los decimales de la moneda"""
        return self.stock_denominacion.stock.moneda.formatear_monto(self.valor_movido())


class HistorialStock(models.Model):
    """Modelo para registrar el historial de movimientos de stock"""
    
    TIPO_MOVIMIENTO_CHOICES = [
        ('ENTRADA', 'Entrada'),
        ('SALIDA', 'Salida'),
    ]
    
    ORIGEN_MOVIMIENTO_CHOICES = [
        ('MANUAL', 'Manual'),
        ('TRANSACCION', 'Transacción'),
    ]
    
    stock = models.ForeignKey(
        Stock,
        on_delete=models.CASCADE,
        related_name='historial',
        verbose_name='Stock',
        help_text='Stock al que pertenece este movimiento'
    )
    tipo_movimiento = models.CharField(
        max_length=10,
        choices=TIPO_MOVIMIENTO_CHOICES,
        verbose_name='Tipo de Movimiento',
        help_text='Si es entrada o salida de stock'
    )
    origen_movimiento = models.CharField(
        max_length=15,
        choices=ORIGEN_MOVIMIENTO_CHOICES,
        verbose_name='Origen del Movimiento',
        help_text='Si fue manual o por transacción'
    )
    cantidad_movida = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name='Cantidad Movida',
        help_text='Cantidad que se movió en este registro'
    )
    cantidad_anterior = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name='Cantidad Anterior',
        help_text='Cantidad que había antes del movimiento'
    )
    cantidad_posterior = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        verbose_name='Cantidad Posterior',
        help_text='Cantidad que quedó después del movimiento'
    )
    usuario = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Usuario',
        help_text='Usuario que realizó el movimiento'
    )
    transaccion = models.ForeignKey(
        'transacciones.Transaccion',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Transacción',
        help_text='Transacción relacionada (si aplica)'
    )
    observaciones = models.TextField(
        blank=True,
        verbose_name='Observaciones',
        help_text='Observaciones adicionales del movimiento'
    )
    fecha_movimiento = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Fecha del Movimiento',
        help_text='Fecha y hora en que se realizó el movimiento'
    )

    class Meta:
        verbose_name = 'Historial de Stock'
        verbose_name_plural = 'Historial de Stocks'
        ordering = ['-fecha_movimiento']
        permissions = [
            ('view_historial_stock', 'Can view stock history'),
        ]

    def __str__(self):
        return f"{self.stock.tauser.nombre} - {self.stock.moneda.nombre}: {self.tipo_movimiento} {self.cantidad_movida}"

    def formatear_cantidad_movida(self):
        """Formatea la cantidad movida según los decimales de la moneda"""
        return self.stock.moneda.formatear_monto(self.cantidad_movida)

    def formatear_cantidad_anterior(self):
        """Formatea la cantidad anterior según los decimales de la moneda"""
        return self.stock.moneda.formatear_monto(self.cantidad_anterior)

    def formatear_cantidad_posterior(self):
        """Formatea la cantidad posterior según los decimales de la moneda"""
        return self.stock.moneda.formatear_monto(self.cantidad_posterior)
