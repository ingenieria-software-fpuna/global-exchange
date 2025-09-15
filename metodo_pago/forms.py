from django import forms
from .models import MetodoPago


class MetodoPagoForm(forms.ModelForm):
    """Formulario para crear y editar métodos de pago"""

    class Meta:
        model = MetodoPago
        fields = ['nombre', 'descripcion', 'comision', 'es_activo']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Tarjeta de Crédito'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Detalles del método de pago'
            }),
            'comision': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'max': 100,
                'step': '0.01',
                'placeholder': 'Ej: 2.50'
            }),
            'es_activo': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'nombre': 'Nombre',
            'descripcion': 'Descripción',
            'comision': 'Comisión (%)',
            'es_activo': 'Activo',
        }

    def clean_nombre(self):
        nombre = self.cleaned_data.get('nombre')
        if nombre:
            if self.instance.pk:
                if MetodoPago.objects.filter(nombre__iexact=nombre).exclude(pk=self.instance.pk).exists():
                    raise forms.ValidationError('Ya existe un método de pago con este nombre.')
            else:
                if MetodoPago.objects.filter(nombre__iexact=nombre).exists():
                    raise forms.ValidationError('Ya existe un método de pago con este nombre.')
        return nombre

