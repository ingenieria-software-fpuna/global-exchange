from django import forms
from django.core.validators import RegexValidator
from .models import Moneda


class MonedaForm(forms.ModelForm):
    """
    Formulario para crear y editar monedas
    """
    
    class Meta:
        model = Moneda
        fields = [
            'nombre', 'codigo', 'simbolo', 'decimales', 'monto_limite_transaccion', 'es_activa'
        ]
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Dólar Estadounidense'
            }),
            'codigo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: USD',
                'maxlength': 3,
                'style': 'text-transform: uppercase;'
            }),
            'simbolo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: $'
            }),
            'decimales': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'placeholder': 'Ej: 2'
            }),
            'monto_limite_transaccion': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: 1000000.00',
                'min': '0',
                'step': '0.01'
            }),
            'es_activa': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'nombre': 'Nombre de la Moneda',
            'codigo': 'Código ISO 4217',
            'simbolo': 'Símbolo',
            'monto_limite_transaccion': 'Monto límite por transacción',
            'es_activa': 'Moneda Activa',
        }
        help_texts = {
            'nombre': 'Nombre completo de la moneda',
            'codigo': 'Código de 3 letras según ISO 4217',
            'simbolo': 'Símbolo usado para representar la moneda',
            'monto_limite_transaccion': 'El monto límite debe estar expresado en guaraníes (PYG). Vacío = sin límite.',
            'es_activa': 'Indica si la moneda está disponible para operaciones',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Validaciones adicionales
        self.fields['codigo'].validators.append(
            RegexValidator(
                regex=r'^[A-Z]{3}$',
                message='El código debe tener exactamente 3 letras mayúsculas.'
            )
        )

    def clean_codigo(self):
        codigo = self.cleaned_data.get('codigo')
        if codigo:
            codigo = codigo.upper()
            
            # Verificar que no exista otra moneda con el mismo código
            if self.instance.pk:
                # Es edición
                if Moneda.objects.filter(codigo=codigo).exclude(pk=self.instance.pk).exists():
                    raise forms.ValidationError('Ya existe una moneda con este código.')
            else:
                # Es creación
                if Moneda.objects.filter(codigo=codigo).exists():
                    raise forms.ValidationError('Ya existe una moneda con este código.')
                    
        return codigo

    def clean_nombre(self):
        nombre = self.cleaned_data.get('nombre')
        if nombre:
            # Verificar que no exista otra moneda con el mismo nombre
            if self.instance.pk:
                # Es edición
                if Moneda.objects.filter(nombre__iexact=nombre).exclude(pk=self.instance.pk).exists():
                    raise forms.ValidationError('Ya existe una moneda con este nombre.')
            else:
                # Es creación
                if Moneda.objects.filter(nombre__iexact=nombre).exists():
                    raise forms.ValidationError('Ya existe una moneda con este nombre.')
                    
        return nombre


class MonedaSearchForm(forms.Form):
    """
    Formulario para búsqueda y filtros de monedas
    """
    q = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por nombre, código o símbolo...'
        }),
        label='Buscar'
    )
    
    estado = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'Todas'),
            ('activo', 'Activas'),
            ('inactivo', 'Inactivas')
        ],
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Estado'
    )
