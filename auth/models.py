from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
import string
import random

class CodigoVerificacion(models.Model):
    """Modelo para almacenar códigos de verificación con expiración"""
    
    TIPO_CHOICES = [
        ('login', 'Inicio de Sesión'),
        ('registro', 'Registro de Usuario'),
        ('reset_password', 'Reseteo de Contraseña'),
    ]
    
    usuario = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        verbose_name="Usuario"
    )
    codigo = models.CharField(
        max_length=6,
        verbose_name="Código de Verificación"
    )
    tipo = models.CharField(
        max_length=20,
        choices=TIPO_CHOICES,
        verbose_name="Tipo de Verificación"
    )
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de Creación"
    )
    fecha_expiracion = models.DateTimeField(
        verbose_name="Fecha de Expiración"
    )
    usado = models.BooleanField(
        default=False,
        verbose_name="Usado"
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name="Dirección IP"
    )
    user_agent = models.TextField(
        null=True,
        blank=True,
        verbose_name="User Agent"
    )
    
    class Meta:
        verbose_name = "Código de Verificación"
        verbose_name_plural = "Códigos de Verificación"
        ordering = ['-fecha_creacion']
        indexes = [
            models.Index(fields=['codigo', 'tipo']),
            models.Index(fields=['usuario', 'tipo']),
            models.Index(fields=['fecha_expiracion']),
        ]
    
    def __str__(self):
        return f"Código {self.codigo} para {self.usuario.email} ({self.tipo})"
    
    @classmethod
    def generar_codigo(cls):
        """Genera un código de verificación de 6 dígitos"""
        return ''.join(random.choices(string.digits, k=6))
    
    @classmethod
    def crear_codigo(cls, usuario, tipo, request=None, minutos_expiracion=5):
        """Crea un nuevo código de verificación"""
        # Invalidar códigos anteriores del mismo tipo
        cls.objects.filter(
            usuario=usuario,
            tipo=tipo,
            usado=False,
            fecha_expiracion__gt=timezone.now()
        ).update(usado=True)
        
        # Crear nuevo código
        codigo = cls.generar_codigo()
        fecha_expiracion = timezone.now() + timedelta(minutes=minutos_expiracion)
        
        # Obtener información de la request si está disponible
        ip_address = None
        user_agent = None
        if request:
            x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
            if x_forwarded_for:
                ip_address = x_forwarded_for.split(',')[0]
            else:
                ip_address = request.META.get('REMOTE_ADDR')
            user_agent = request.META.get('HTTP_USER_AGENT')
        
        return cls.objects.create(
            usuario=usuario,
            codigo=codigo,
            tipo=tipo,
            fecha_expiracion=fecha_expiracion,
            ip_address=ip_address,
            user_agent=user_agent
        )
    
    def es_valido(self):
        """Verifica si el código es válido (no usado y no expirado)"""
        return not self.usado and self.fecha_expiracion > timezone.now()
    
    def marcar_como_usado(self):
        """Marca el código como usado"""
        self.usado = True
        self.save(update_fields=['usado'])
    
    @classmethod
    def limpiar_codigos_expirados(cls):
        """Elimina códigos expirados (después de 5 minutos) y códigos usados más antiguos que 1 hora"""
        fecha_limite_usados = timezone.now() - timedelta(hours=1)
        return cls.objects.filter(
            models.Q(fecha_expiracion__lt=timezone.now()) |  # Códigos que ya expiraron (después de 5 min)
            models.Q(usado=True, fecha_creacion__lt=fecha_limite_usados)  # Códigos usados más antiguos que 1h
        ).delete()
    
    @classmethod
    def verificar_codigo(cls, usuario, codigo, tipo):
        """Verifica un código de verificación"""
        try:
            codigo_obj = cls.objects.get(
                usuario=usuario,
                codigo=codigo,
                tipo=tipo,
                usado=False,
                fecha_expiracion__gt=timezone.now()
            )
            codigo_obj.marcar_como_usado()
            return True, codigo_obj
        except cls.DoesNotExist:
            return False, None
