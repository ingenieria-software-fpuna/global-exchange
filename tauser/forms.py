from django import forms
from .models import Tauser


class TauserForm(forms.ModelForm):
    """Formulario para crear y editar Tausers"""

    class Meta:
        model = Tauser
        fields = ['nombre', 'direccion', 'horario_atencion', 'es_activo', 'fecha_instalacion']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Centro Comercial Villa Morra'
            }),
            'direccion': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Av. Mariscal López 3799, Asunción'
            }),
            'horario_atencion': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Lunes a Viernes 8:00 - 18:00'
            }),
            'es_activo': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'fecha_instalacion': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local'
            }),
        }
        labels = {
            'nombre': 'Nombre',
            'direccion': 'Dirección',
            'horario_atencion': 'Horario de Atención',
            'es_activo': 'Activo',
            'fecha_instalacion': 'Fecha de Instalación',
        }

    def clean_nombre(self):
        nombre = self.cleaned_data.get('nombre')
        if nombre:
            if self.instance.pk:
                if Tauser.objects.filter(nombre__iexact=nombre).exclude(pk=self.instance.pk).exists():
                    raise forms.ValidationError('Ya existe un Tauser con este nombre.')
            else:
                if Tauser.objects.filter(nombre__iexact=nombre).exists():
                    raise forms.ValidationError('Ya existe un Tauser con este nombre.')
        return nombre

    def clean_direccion(self):
        direccion = self.cleaned_data.get('direccion')
        if direccion and len(direccion.strip()) < 10:
            raise forms.ValidationError('La dirección debe tener al menos 10 caracteres.')
        return direccion

    def clean_horario_atencion(self):
        horario = self.cleaned_data.get('horario_atencion')
        if horario and len(horario.strip()) < 5:
            raise forms.ValidationError('El horario debe tener al menos 5 caracteres.')
        return horario
