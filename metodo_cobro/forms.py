from django import forms
from .models import MetodoCobro
from monedas.models import Moneda
from .widgets import MonedaSelectorWidget


class MetodoCobroForm(forms.ModelForm):
    """Formulario para crear y editar métodos de cobro"""

    monedas_permitidas = forms.ModelMultipleChoiceField(
        queryset=Moneda.objects.filter(es_activa=True),
        widget=MonedaSelectorWidget(),
        help_text="Seleccione las monedas permitidas para este método de cobro",
        required=True
    )

    class Meta:
        model = MetodoCobro
        fields = ['nombre', 'descripcion', 'comision', 'monedas_permitidas', 'es_activo', 'requiere_retiro_fisico']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Transferencia bancaria'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Detalles del método de cobro'
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
            'requiere_retiro_fisico': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'nombre': 'Nombre',
            'descripcion': 'Descripción',
            'comision': 'Comisión (%)',
            'monedas_permitidas': 'Monedas Permitidas',
            'es_activo': 'Activo',
            'requiere_retiro_fisico': 'Requiere Retiro Físico',
        }

    def clean_nombre(self):
        nombre = self.cleaned_data.get('nombre')
        if nombre:
            if self.instance.pk:
                if MetodoCobro.objects.filter(nombre__iexact=nombre).exclude(pk=self.instance.pk).exists():
                    raise forms.ValidationError('Ya existe un método de cobro con este nombre.')
            else:
                if MetodoCobro.objects.filter(nombre__iexact=nombre).exists():
                    raise forms.ValidationError('Ya existe un método de cobro con este nombre.')
        return nombre

    def clean_monedas_permitidas(self):
        monedas = self.cleaned_data.get('monedas_permitidas')
        if not monedas:
            raise forms.ValidationError('Debe seleccionar al menos una moneda permitida.')
        return monedas