from django import forms
from django.forms import inlineformset_factory
from .models import MetodoPago, Campo
from .widgets import MonedaSelectorWidget


class CampoForm(forms.ModelForm):
    """Formulario para campos de métodos de pago"""
    
    class Meta:
        model = Campo
        fields = ['nombre', 'etiqueta', 'tipo', 'es_obligatorio', 'max_length', 
                 'regex_validacion', 'placeholder', 'opciones', 'es_activo']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'ej: numero_telefono'
            }),
            'etiqueta': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Número de Teléfono'
            }),
            'tipo': forms.Select(attrs={
                'class': 'form-control'
            }),
            'es_obligatorio': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'max_length': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 1,
                'max': 1000
            }),
            'regex_validacion': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': '^[0-9]{10,15}$'
            }),
            'placeholder': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: +595981234567'
            }),
            'opciones': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Una opción por línea'
            }),
            'es_activo': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'nombre': 'Nombre del Campo',
            'etiqueta': 'Etiqueta',
            'tipo': 'Tipo',
            'es_obligatorio': 'Obligatorio',
            'max_length': 'Longitud Máxima',
            'regex_validacion': 'Regex de Validación',
            'placeholder': 'Placeholder',
            'opciones': 'Opciones (una por línea)',
            'es_activo': 'Activo',
        }

    def clean_nombre(self):
        nombre = self.cleaned_data.get('nombre')
        if nombre:
            # Convertir a lowercase y reemplazar espacios con guiones bajos
            nombre = nombre.lower().replace(' ', '_')
        return nombre


# Formset para manejar múltiples campos
from django.forms import formset_factory

CampoFormSet = formset_factory(
    CampoForm,
    extra=1,
    can_delete=True
)


class MetodoPagoForm(forms.ModelForm):
    """Formulario para crear y editar métodos de pago"""

    class Meta:
        model = MetodoPago
        fields = ['nombre', 'descripcion', 'comision', 'monedas_permitidas', 'es_activo', 'requiere_retiro_fisico']
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
            'requiere_retiro_fisico': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
            'monedas_permitidas': MonedaSelectorWidget(),
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
                if MetodoPago.objects.filter(nombre__iexact=nombre).exclude(pk=self.instance.pk).exists():
                    raise forms.ValidationError('Ya existe un método de pago con este nombre.')
            else:
                if MetodoPago.objects.filter(nombre__iexact=nombre).exists():
                    raise forms.ValidationError('Ya existe un método de pago con este nombre.')
        return nombre

