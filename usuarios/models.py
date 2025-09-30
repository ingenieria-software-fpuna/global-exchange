from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin, Group
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver

class UsuarioManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("El usuario debe tener un correo electrónico")
        email = self.normalize_email(email)
        usuario = self.model(email=email, **extra_fields)
        usuario.set_password(password)
        usuario.save(using=self._db)
        return usuario

    def create_admin_user(self, email, password=None, **extra_fields):
        """
        Crea un usuario administrador del sistema.
        Lo asigna al grupo 'Admin' en lugar de usar is_superuser.
        """
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', False)
        
        # Crear el usuario
        usuario = self.create_user(email, password, **extra_fields)
        
        # Asignar al grupo de administradores
        admin_group, created = Group.objects.get_or_create(name='Admin')
        usuario.groups.add(admin_group)
        
        return usuario

class Usuario(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    cedula = models.CharField(max_length=20, unique=True, verbose_name="Cédula de Identidad", null=True, blank=True)
    nombre = models.CharField(max_length=100)
    apellido = models.CharField(max_length=100, blank=True)
    fecha_nacimiento = models.DateField(verbose_name="Fecha de Nacimiento", null=True, blank=True)
    
    # Para verificar correo
    activo = models.BooleanField(default=True)

    # Para indicar si el usuario esta activo o inactivo
    es_activo = models.BooleanField(default=True)

    is_staff = models.BooleanField(default=False)
    
    # Campos de auditoría
    fecha_creacion = models.DateTimeField(default=timezone.now, verbose_name="Fecha de creación")
    fecha_actualizacion = models.DateTimeField(auto_now=True, verbose_name="Fecha de actualización")

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['nombre', 'cedula', 'fecha_nacimiento']

    objects = UsuarioManager()

    def __str__(self):
        return self.email


@receiver(post_save, sender=Usuario)
def asignar_grupo_visitante(sender, instance, created, **kwargs):
    """
    Asigna automáticamente el grupo 'Visitante' a nuevos usuarios
    que no tienen ningún grupo asignado.
    """
    if created:
        try:
            # Buscar el grupo Visitante
            grupo_visitante, created_group = Group.objects.get_or_create(name='Visitante')
            
            # Solo asignar si el usuario no tiene grupos
            if not instance.groups.exists():
                instance.groups.add(grupo_visitante)
                print(f"Usuario {instance.email} asignado automáticamente al grupo 'Visitante'")
        except Exception as e:
            print(f"⚠️ Error asignando grupo Visitante a {instance.email}: {e}")
