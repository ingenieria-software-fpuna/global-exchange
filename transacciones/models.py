from django.db import models
from django.db.models import Q
from django.core.validators import MinValueValidator
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
import uuid
import secrets
import string

# Imports de otros modelos
from monedas.models import Moneda
from metodo_pago.models import MetodoPago
from metodo_cobro.models import MetodoCobro
from clientes.models import Cliente
from tauser.models import Tauser

User = get_user_model()


class TipoOperacion(models.Model):
    """
    Modelo para los tipos de operación disponibles en el sistema.
    """
    COMPRA = 'COMPRA'
    VENTA = 'VENTA'
    
    TIPOS_CHOICES = [
        (COMPRA, 'Compra de Divisas'),
        (VENTA, 'Venta de Divisas'),
    ]
    
    codigo = models.CharField(
        max_length=10,
        choices=TIPOS_CHOICES,
        unique=True,
        verbose_name="Código del tipo"
    )
    nombre = models.CharField(
        max_length=100,
        verbose_name="Nombre descriptivo"
    )
    descripcion = models.TextField(
        blank=True,
        verbose_name="Descripción del tipo de operación"
    )
    activo = models.BooleanField(
        default=True,
        verbose_name="Activo"
    )
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de creación"
    )

    class Meta:
        verbose_name = "Tipo de Operación"
        verbose_name_plural = "Tipos de Operación"
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class EstadoTransaccion(models.Model):
    """
    Modelo para los estados de las transacciones.
    """
    PENDIENTE = 'PENDIENTE'
    PAGADA = 'PAGADA'
    CANCELADA = 'CANCELADA'
    ANULADA = 'ANULADA'
    
    ESTADOS_CHOICES = [
        (PENDIENTE, 'Pendiente de Pago'),
        (PAGADA, 'Pagada'),
        (CANCELADA, 'Cancelada'),
        (ANULADA, 'Anulada'),
    ]
    
    codigo = models.CharField(
        max_length=15,
        choices=ESTADOS_CHOICES,
        unique=True,
        verbose_name="Código del estado"
    )
    nombre = models.CharField(
        max_length=100,
        verbose_name="Nombre descriptivo"
    )
    descripcion = models.TextField(
        blank=True,
        verbose_name="Descripción del estado"
    )
    es_final = models.BooleanField(
        default=False,
        verbose_name="Es estado final",
        help_text="Indica si este estado es final (no puede cambiar a otro)"
    )
    activo = models.BooleanField(
        default=True,
        verbose_name="Activo"
    )

    class Meta:
        verbose_name = "Estado de Transacción"
        verbose_name_plural = "Estados de Transacción"
        ordering = ['nombre']

    def __str__(self):
        return self.nombre


class Transaccion(models.Model):
    """
    Modelo principal para las transacciones de compra y venta de divisas.
    """
    
    # Identificadores únicos
    id = models.BigAutoField(primary_key=True)
    id_transaccion = models.CharField(
        max_length=50,
        unique=True,
        verbose_name="ID de Transacción",
        help_text="Identificador único para la transacción"
    )
    
    # Relaciones con otros modelos
    cliente = models.ForeignKey(
        Cliente,
        on_delete=models.PROTECT,
        related_name='transacciones',
        verbose_name="Cliente",
        null=True,
        blank=True,
        help_text="Cliente que realiza la transacción (opcional para clientes casuales)"
    )
    tauser = models.ForeignKey(
        Tauser,
        on_delete=models.PROTECT,
        related_name='transacciones',
        verbose_name="Tauser",
        null=True,
        blank=True,
        help_text="Punto de atención donde se realiza la transacción (opcional)"
    )
    usuario = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='transacciones_realizadas',
        verbose_name="Usuario que procesa",
        help_text="Usuario del sistema que procesa la transacción"
    )
    tipo_operacion = models.ForeignKey(
        TipoOperacion,
        on_delete=models.PROTECT,
        related_name='transacciones',
        verbose_name="Tipo de Operación"
    )
    
    # Monedas y cantidades
    moneda_origen = models.ForeignKey(
        Moneda,
        on_delete=models.PROTECT,
        related_name='transacciones_origen',
        verbose_name="Moneda de Origen"
    )
    moneda_destino = models.ForeignKey(
        Moneda,
        on_delete=models.PROTECT,
        related_name='transacciones_destino',
        verbose_name="Moneda de Destino"
    )
    
    # Cantidades - usando DecimalField para mayor precisión
    monto_origen = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        verbose_name="Monto en moneda origen",
        help_text="Cantidad en la moneda de origen"
    )
    monto_destino = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        validators=[MinValueValidator(0.01)],
        verbose_name="Monto en moneda destino",
        help_text="Cantidad que se entrega en la moneda destino"
    )
    
    # Métodos de pago y cobro
    metodo_cobro = models.ForeignKey(
        MetodoCobro,
        on_delete=models.PROTECT,
        related_name='transacciones_cobro',
        verbose_name="Método de Cobro",
        null=True,
        blank=True,
        help_text="Método por el cual se recibe el dinero"
    )
    metodo_pago = models.ForeignKey(
        MetodoPago,
        on_delete=models.PROTECT,
        related_name='transacciones_pago',
        verbose_name="Método de Pago",
        null=True,
        blank=True,
        help_text="Método por el cual se entrega el dinero"
    )
    
    # Tasa de cambio utilizada
    tasa_cambio = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        verbose_name="Tasa de Cambio",
        help_text="Tasa de cambio aplicada en la transacción"
    )
    
    # Comisiones y descuentos
    porcentaje_comision = models.DecimalField(
        max_digits=8,
        decimal_places=4,
        default=0.00,
        validators=[MinValueValidator(0)],
        verbose_name="Porcentaje de Comisión (%)",
        help_text="Porcentaje de comisión aplicado"
    )
    monto_comision = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0)],
        verbose_name="Monto de Comisión",
        help_text="Monto total de comisión en la moneda origen"
    )
    porcentaje_descuento = models.DecimalField(
        max_digits=8,
        decimal_places=4,
        default=0.00,
        validators=[MinValueValidator(0)],
        verbose_name="Porcentaje de Descuento (%)",
        help_text="Porcentaje de descuento aplicado por tipo de cliente"
    )
    monto_descuento = models.DecimalField(
        max_digits=15,
        decimal_places=2,
        default=0.00,
        validators=[MinValueValidator(0)],
        verbose_name="Monto de Descuento",
        help_text="Monto total de descuento aplicado"
    )
    
    # Estado de la transacción
    estado = models.ForeignKey(
        EstadoTransaccion,
        on_delete=models.PROTECT,
        related_name='transacciones',
        verbose_name="Estado"
    )
    
    # Código de verificación
    codigo_verificacion = models.CharField(
        max_length=10,
        verbose_name="Código de Verificación",
        help_text="Código alfanumérico para verificar la transacción"
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
    fecha_expiracion = models.DateTimeField(
        verbose_name="Fecha de Expiración",
        help_text="Fecha límite para completar el pago"
    )
    fecha_pago = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name="Fecha de Pago",
        help_text="Fecha en que se completó el pago"
    )
    
    # Campos adicionales para auditoría
    observaciones = models.TextField(
        blank=True,
        verbose_name="Observaciones",
        help_text="Observaciones adicionales sobre la transacción"
    )
    ip_cliente = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name="IP del Cliente",
        help_text="Dirección IP desde donde se originó la transacción"
    )

    class Meta:
        verbose_name = "Transacción"
        verbose_name_plural = "Transacciones"
        ordering = ['-fecha_creacion']
        indexes = [
            models.Index(fields=['id_transaccion']),
            models.Index(fields=['cliente', '-fecha_creacion']),
            models.Index(fields=['tauser', '-fecha_creacion']),
            models.Index(fields=['usuario', '-fecha_creacion']),
            models.Index(fields=['estado', '-fecha_creacion']),
            models.Index(fields=['fecha_expiracion']),
            models.Index(fields=['tipo_operacion', '-fecha_creacion']),
        ]

    def __str__(self):
        return f"Transacción {self.id_transaccion} - {self.tipo_operacion.nombre}"

    def save(self, *args, **kwargs):
        # Generar ID de transacción si no existe
        if not self.id_transaccion:
            self.id_transaccion = self.generar_id_transaccion()
        
        # Generar código de verificación si no existe
        if not self.codigo_verificacion:
            self.codigo_verificacion = self.generar_codigo_verificacion()
        
        # Establecer fecha de expiración si no existe (5 minutos por defecto)
        if not self.fecha_expiracion:
            self.fecha_expiracion = timezone.now() + timezone.timedelta(minutes=5)
        
        super().save(*args, **kwargs)

    def clean(self):
        """Validaciones personalizadas del modelo"""
        super().clean()
        
        # Validar que las monedas sean diferentes
        if self.moneda_origen == self.moneda_destino:
            raise ValidationError({
                'moneda_destino': 'La moneda de destino debe ser diferente a la de origen.'
            })
        
        # Validar que el cliente esté activo si se especifica
        if self.cliente and not self.cliente.activo:
            raise ValidationError({
                'cliente': 'No se puede crear una transacción para un cliente inactivo.'
            })
        
        # Validar que el tauser esté activo si se especifica
        if self.tauser and not self.tauser.es_activo:
            raise ValidationError({
                'tauser': 'No se puede crear una transacción para un tauser inactivo.'
            })
        
        # Validar que el tipo de operación esté activo
        if self.tipo_operacion and not self.tipo_operacion.activo:
            raise ValidationError({
                'tipo_operacion': 'No se puede usar un tipo de operación inactivo.'
            })

    @staticmethod
    def generar_id_transaccion():
        """Genera un ID único para la transacción"""
        timestamp = timezone.now().strftime('%Y%m%d%H%M%S')
        random_part = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(6))
        return f"TXN-{timestamp}-{random_part}"

    @staticmethod
    def generar_codigo_verificacion():
        """Genera un código de verificación alfanumérico"""
        return ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(8))

    def esta_expirada(self):
        """Verifica si la transacción está expirada"""
        return timezone.now() > self.fecha_expiracion

    def puede_cancelar_por_expiracion(self):
        """Verifica si la transacción puede ser cancelada por expiración"""
        return (self.estado.codigo == EstadoTransaccion.PENDIENTE 
                and self.esta_expirada())

    def cancelar_por_expiracion(self):
        """Cancela la transacción por expiración"""
        if self.puede_cancelar_por_expiracion():
            estado_cancelada = EstadoTransaccion.objects.get(codigo=EstadoTransaccion.CANCELADA)
            self.estado = estado_cancelada
            self.observaciones += f"\nCancelada automáticamente por expiración el {timezone.now()}"
            self.save(update_fields=['estado', 'observaciones', 'fecha_actualizacion'])
            return True
        return False

    def calcular_total_final(self):
        """Calcula el monto total final considerando comisiones y descuentos"""
        total = self.monto_destino + self.monto_comision - self.monto_descuento
        return max(total, 0)  # Asegurar que no sea negativo

    def get_resumen_financiero(self):
        """Retorna un diccionario con el resumen financiero de la transacción"""
        return {
            'monto_base': self.monto_destino,
            'comision': self.monto_comision,
            'descuento': self.monto_descuento,
            'total_final': self.calcular_total_final(),
            'tasa': self.tasa_cambio,
            'porcentaje_comision': self.porcentaje_comision,
            'porcentaje_descuento': self.porcentaje_descuento,
        }

    def get_resumen_detallado(self):
        """Retorna un diccionario con el resumen financiero detallado con la NUEVA lógica"""
        from decimal import Decimal
        
        # Calcular comisiones según el tipo de operación
        comision_cobro = Decimal('0')
        comision_pago = Decimal('0')
        
        if self.tipo_operacion.codigo == 'VENTA':
            # Para VENTAS: las comisiones se calculan sobre el PYG bruto (subtotal)
            # Necesitamos recalcular el PYG bruto desde la divisa vendida
            monto_pyg_bruto = self.monto_origen * self.tasa_cambio
            
            if self.metodo_cobro and self.metodo_cobro.comision > 0:
                comision_cobro = monto_pyg_bruto * (Decimal(str(self.metodo_cobro.comision)) / Decimal('100'))
            
            if self.metodo_pago and self.metodo_pago.comision > 0:
                comision_pago = monto_pyg_bruto * (Decimal(str(self.metodo_pago.comision)) / Decimal('100'))
        else:
            # Para COMPRAS: las comisiones se calculan sobre el monto que paga el cliente (PYG)
            monto_total_pagado = self.monto_origen
            
            if self.metodo_cobro and self.metodo_cobro.comision > 0:
                comision_cobro = monto_total_pagado * (Decimal(str(self.metodo_cobro.comision)) / Decimal('100'))
            
            if self.metodo_pago and self.metodo_pago.comision > 0:
                comision_pago = monto_total_pagado * (Decimal(str(self.metodo_pago.comision)) / Decimal('100'))
        
        comision_total = comision_cobro + comision_pago
        
        # Descuento aplicado (sobre las comisiones)
        descuento_aplicado = Decimal('0')
        descuento_pct = Decimal('0')
        if self.cliente and self.cliente.tipo_cliente and self.cliente.tipo_cliente.activo and self.cliente.tipo_cliente.descuento > 0:
            descuento_pct = Decimal(str(self.cliente.tipo_cliente.descuento))
            descuento_aplicado = comision_total * (descuento_pct / Decimal('100'))
        
        # Definir variables según el tipo de operación
        if self.tipo_operacion.codigo == 'VENTA':
            # Para ventas: el cliente entrega divisa extranjera
            monto_base = self.monto_origen  # Divisa extranjera que entrega
            total_cliente = self.monto_origen  # Lo que entrega el cliente
        else:
            # Para compras: el cliente paga PYG
            monto_base = self.monto_origen  # PYG que paga
            total_cliente = self.monto_origen  # Lo que paga el cliente
        
        # Formatear montos
        def formatear_monto(valor, moneda):
            if moneda.codigo == 'PYG':
                return f"₲ {valor:,.0f}"
            else:
                return f"{moneda.simbolo} {valor:,.2f}"
        
        return {
            # Básicos
            'subtotal': float(self.monto_origen),
            'subtotal_formateado': formatear_monto(self.monto_origen, self.moneda_origen),
            
            # Comisiones - formatear según el tipo de operación
            'comision_cobro': float(comision_cobro),
            'comision_cobro_formateado': formatear_monto(comision_cobro, 
                self.moneda_destino if self.tipo_operacion.codigo == 'VENTA' else self.moneda_origen),
            'comision_pago': float(comision_pago),
            'comision_pago_formateado': formatear_monto(comision_pago, 
                self.moneda_destino if self.tipo_operacion.codigo == 'VENTA' else self.moneda_origen),
            'comision_total': float(comision_total),
            'comision_total_formateado': formatear_monto(comision_total, 
                self.moneda_destino if self.tipo_operacion.codigo == 'VENTA' else self.moneda_origen),
            
            # Descuento - formatear según el tipo de operación
            'descuento_aplicado': float(descuento_aplicado),
            'descuento_aplicado_formateado': formatear_monto(descuento_aplicado, 
                self.moneda_destino if self.tipo_operacion.codigo == 'VENTA' else self.moneda_origen),
            'descuento_pct': float(descuento_pct),
            
            # Total final
            'total_cliente': float(total_cliente),
            'total_cliente_formateado': formatear_monto(total_cliente, self.moneda_origen),
            
            # Lo que recibe
            'monto_recibe': float(self.monto_destino),
            'monto_recibe_formateado': formatear_monto(self.monto_destino, self.moneda_destino),
            
            # Tasas de cambio (SIMPLE - usar lo que está guardado en BD)
            'tasa_cambio': float(self.tasa_cambio),  # La tasa que se usó (YA está ajustada si había descuento)
            'tasa_cambio_tipo': self.get_tipo_tasa_utilizada(),
            'tasa_base': self.get_tasa_base(),  # Tasa original sin descuentos
            'tasa_ajustada': float(self.tasa_cambio),  # La tasa guardada (YA ajustada)
            
            # Información de métodos
            'metodo_cobro': {
                'nombre': self.metodo_cobro.nombre if self.metodo_cobro else None,
                'comision': float(self.metodo_cobro.comision) if self.metodo_cobro else 0
            },
            'metodo_pago': {
                'nombre': self.metodo_pago.nombre if self.metodo_pago else None,
                'comision': float(self.metodo_pago.comision) if self.metodo_pago else 0
            },
            
            # Cliente
            'cliente': {
                'nombre': self.cliente.nombre_comercial if self.cliente else None,
                'tipo': self.cliente.tipo_cliente.nombre if self.cliente and self.cliente.tipo_cliente else None,
                'descuento': float(self.cliente.tipo_cliente.descuento) if self.cliente and self.cliente.tipo_cliente else 0
            } if self.cliente else None
        }

    def get_tipo_tasa_utilizada(self):
        """Determina qué tipo de tasa se utilizó en la transacción"""
        if self.moneda_origen.codigo == 'PYG':
            return 'venta'  # Cliente compra divisa extranjera con PYG
        else:
            return 'compra'  # Cliente vende divisa extranjera por PYG
    
    def get_tasa_base(self):
        """Obtiene la tasa base (sin ajustes por cliente) consultando la TasaCambio actual"""
        from tasa_cambio.models import TasaCambio

        try:
            if self.moneda_origen.codigo == 'PYG':
                # Para compras (PYG -> otra moneda)
                tasa_actual = TasaCambio.objects.filter(
                    moneda=self.moneda_destino,
                    es_activa=True
                ).first()
                if tasa_actual:
                    # Tasa base = precio_base + comision_venta (SIN descuento)
                    return float(tasa_actual.precio_base + tasa_actual.comision_venta)
            else:
                # Para ventas (otra moneda -> PYG)
                tasa_actual = TasaCambio.objects.filter(
                    moneda=self.moneda_origen,
                    es_activa=True
                ).first()
                if tasa_actual:
                    return float(tasa_actual.precio_base - tasa_actual.comision_compra)
        except:
            pass

        # Si no se puede obtener la tasa actual, devolver la que está guardada
        return float(self.tasa_cambio)

    def tiene_tasa_actualizada(self):
        """Verifica si la transacción tiene la tasa de cambio actualizada"""
        from tasa_cambio.models import TasaCambio
        from decimal import Decimal

        try:
            # Determinar qué moneda buscar en TasaCambio
            if self.moneda_origen.codigo == 'PYG':
                # COMPRAS: PYG -> otra moneda
                tasa_actual = TasaCambio.objects.filter(
                    moneda=self.moneda_destino,
                    es_activa=True
                ).first()
                if not tasa_actual:
                    return False

                # Calcular precio de venta con descuento (como se hace en calcular_compra)
                comision_venta_ajustada = Decimal(str(tasa_actual.comision_venta))
                if self.cliente and self.cliente.tipo_cliente and self.cliente.tipo_cliente.activo and self.cliente.tipo_cliente.descuento > 0:
                    descuento_pct = Decimal(str(self.cliente.tipo_cliente.descuento))
                    comision_venta_ajustada = comision_venta_ajustada * (Decimal('1') - (descuento_pct / Decimal('100')))

                tasa_esperada = Decimal(str(tasa_actual.precio_base)) + comision_venta_ajustada

            else:
                # VENTAS: otra moneda -> PYG
                tasa_actual = TasaCambio.objects.filter(
                    moneda=self.moneda_origen,
                    es_activa=True
                ).first()
                if not tasa_actual:
                    return False

                # Calcular precio de compra con descuento aplicado a la comisión (como se hace en calcular_venta)
                comision_compra_ajustada = Decimal(str(tasa_actual.comision_compra))
                if self.cliente and self.cliente.tipo_cliente and self.cliente.tipo_cliente.activo and self.cliente.tipo_cliente.descuento > 0:
                    descuento_pct = Decimal(str(self.cliente.tipo_cliente.descuento))
                    # El descuento reduce la comisión de compra (cliente recibe más PYG)
                    comision_compra_ajustada = comision_compra_ajustada * (Decimal('1') - (descuento_pct / Decimal('100')))
                
                # Precio de compra ajustado: precio_base - comision_compra_ajustada
                tasa_esperada = Decimal(str(tasa_actual.precio_base)) - comision_compra_ajustada

            # Comparar con la tasa guardada en la transacción (con tolerancia)
            diferencia = abs(tasa_esperada - self.tasa_cambio)
            tolerancia = Decimal('10.00')  # Tolerancia más amplia para manejar redondeos

            return diferencia <= tolerancia

        except Exception as e:
            # Para debug - se puede quitar en producción
            print(f"Error en tiene_tasa_actualizada: {e}")
            return False

    def cancelar_por_cambio_tasa(self):
        """Cancela la transacción por cambio en la tasa de cambio"""
        if self.estado.codigo == EstadoTransaccion.PENDIENTE:
            estado_cancelada = EstadoTransaccion.objects.get(codigo=EstadoTransaccion.CANCELADA)
            self.estado = estado_cancelada
            self.observaciones += f"\nCancelada automáticamente por cambio en tasa de cambio el {timezone.now()}"
            self.save(update_fields=['estado', 'observaciones', 'fecha_actualizacion'])
            return True
        return False

    @classmethod
    def cancelar_pendientes_por_moneda(cls, moneda):
        """Cancela todas las transacciones pendientes que involucren una moneda específica"""
        from django.db import transaction as db_transaction

        # Buscar transacciones pendientes que usen la moneda como origen o destino
        transacciones_pendientes = cls.objects.filter(
            estado__codigo=EstadoTransaccion.PENDIENTE
        ).filter(
            Q(moneda_origen=moneda) | Q(moneda_destino=moneda)
        )

        canceladas = 0
        with db_transaction.atomic():
            for transaccion in transacciones_pendientes:
                if transaccion.cancelar_por_cambio_tasa():
                    canceladas += 1

        return canceladas

    def requiere_retiro_fisico(self):
        """
        Determina si la transacción requiere retiro físico en un Tauser.
        
        Para COMPRA: Siempre requiere retiro físico (cliente retira divisas)
        Para VENTA: Solo si el método de cobro requiere retiro físico
        """
        if self.tipo_operacion.codigo == 'COMPRA':
            # Para compras, siempre requiere retiro físico (cliente retira divisas)
            return True
        elif self.tipo_operacion.codigo == 'VENTA':
            # Para ventas, verificar si el método de cobro requiere retiro físico
            if self.metodo_cobro and self.metodo_cobro.requiere_retiro_fisico:
                return True
        return False
