from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin, Group

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

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['nombre', 'cedula', 'fecha_nacimiento']

    objects = UsuarioManager()

    def __str__(self):
        return self.email
