from django import forms
from .models import MetodoCobro
from monedas.models import Moneda
from .widgets import MonedaSelectorWidget
from metodo_pago.models import Campo
from django.forms import formset_factory


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
        fields = ['nombre', 'descripcion', 'comision', 'monedas_permitidas', 'campos', 'es_activo']
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
        }
        labels = {
            'nombre': 'Nombre',
            'descripcion': 'Descripción',
            'comision': 'Comisión (%)',
            'monedas_permitidas': 'Monedas Permitidas',
            'es_activo': 'Activo',
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


class CampoMetodoCobroForm(forms.ModelForm):
    """Formulario para campos de método de cobro"""
    
    class Meta:
        model = Campo
        fields = ['nombre', 'etiqueta', 'tipo', 'es_obligatorio', 'max_length', 'regex_validacion', 'placeholder', 'opciones', 'es_activo']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'nombre_campo'}),
            'etiqueta': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Etiqueta del Campo'}),
            'tipo': forms.Select(attrs={'class': 'form-select'}),
            'es_obligatorio': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'max_length': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 255}),
            'regex_validacion': forms.TextInput(attrs={'class': 'form-control', 'placeholder': '^[0-9]+$'}),
            'placeholder': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Texto de ayuda'}),
            'opciones': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Opción 1\nOpción 2\nOpción 3'}),
            'es_activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }
        labels = {
            'nombre': 'Nombre del Campo',
            'etiqueta': 'Etiqueta',
            'tipo': 'Tipo de Campo',
            'es_obligatorio': 'Obligatorio',
            'max_length': 'Longitud Máxima',
            'regex_validacion': 'Expresión Regular',
            'placeholder': 'Texto de Ayuda',
            'opciones': 'Opciones (para select)',
            'es_activo': 'Activo',
        }
    
    def clean_nombre(self):
        nombre = self.cleaned_data.get('nombre')
        if nombre:
            # Convertir a lowercase y reemplazar espacios con guiones bajos
            nombre = nombre.lower().replace(' ', '_')
        return nombre


# Formset para campos de método de cobro
CampoFormSet = formset_factory(
    CampoMetodoCobroForm,
    extra=1,
    can_delete=True
)