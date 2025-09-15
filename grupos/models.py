from django.db import models
from django.contrib.auth.models import Group as DjangoGroup, Permission
from django.contrib.auth import get_user_model

Usuario = get_user_model()

class Grupo(models.Model):
    """
    Modelo personalizado que extiende la funcionalidad de Group de Django
    para agregar funcionalidad de activación/desactivación
    """
    group = models.OneToOneField(
        DjangoGroup,
        on_delete=models.CASCADE,
        related_name='grupo_extension',
        verbose_name="Grupo de Django"
    )
    es_activo = models.BooleanField(
        default=True,
        verbose_name="Activo",
        help_text="Indica si el grupo está activo en el sistema"
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
        verbose_name = "Grupo"
        verbose_name_plural = "Grupos"
        ordering = ['group__name']

    def __str__(self):
        return self.group.name

    @property
    def name(self):
        """Propiedad para compatibilidad con el modelo Group original"""
        return self.group.name

    @property
    def permissions(self):
        """Propiedad para acceder a los permisos del grupo"""
        return self.group.permissions

    @property
    def user_set(self):
        """Propiedad para acceder a los usuarios del grupo"""
        return self.group.user_set

    def save(self, *args, **kwargs):
        # Si no existe el grupo de Django, lo creamos
        if not self.group_id:
            django_group = DjangoGroup.objects.create(name=f"Grupo_{self.pk or 'temp'}")
            self.group = django_group
        super().save(*args, **kwargs)
