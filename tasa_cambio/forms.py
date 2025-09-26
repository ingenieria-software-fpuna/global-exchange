from django import forms
from django.core.validators import MinValueValidator
from django.utils import timezone
from .models import TasaCambio
from monedas.models import Moneda


class TasaCambioForm(forms.ModelForm):
    """
    Formulario para crear y editar cotizaciones
    """
    
    class Meta:
        model = TasaCambio
        fields = [
            'moneda', 'precio_base', 'comision_compra', 'comision_venta'
        ]
        widgets = {
            'moneda': forms.Select(attrs={
                'class': 'form-select',
                'placeholder': 'Seleccione una moneda'
            }),
            'precio_base': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: 7500',
                'step': '1',
                'min': '1'
            }),
            'comision_compra': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: 300',
                'step': '1',
                'min': '0'
            }),
            'comision_venta': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: 200',
                'step': '1',
                'min': '0'
            }),
        }
        labels = {
            'moneda': 'Moneda',
            'precio_base': 'Precio Base',
            'comision_compra': 'Comisión de Compra',
            'comision_venta': 'Comisión de Venta',
        }
        help_texts = {
            'moneda': 'Seleccione la moneda para la cual se establece la cotización',
            'precio_base': 'Precio base de referencia en guaraníes (valor entero)',
            'comision_compra': 'Comisión en guaraníes que se resta al precio base para calcular el precio de compra',
            'comision_venta': 'Comisión en guaraníes que se suma al precio base para calcular el precio de venta',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filtrar solo monedas activas para el selector
        self.fields['moneda'].queryset = Moneda.objects.filter(es_activa=True).order_by('nombre')

    def save(self, commit=True):
        """
        Sobrescribir save para establecer es_activa=True por defecto
        """
        instance = super().save(commit=False)
        if not instance.pk:  # Solo para nuevas cotizaciones
            instance.es_activa = True
        if commit:
            instance.save()
        return instance

    def clean(self):
        cleaned_data = super().clean()
        precio_base = cleaned_data.get('precio_base')
        comision_compra = cleaned_data.get('comision_compra')
        comision_venta = cleaned_data.get('comision_venta')
        moneda = cleaned_data.get('moneda')
        
        # Validar que el precio de compra resultante sea positivo
        if precio_base and comision_compra:
            precio_compra = precio_base - comision_compra
            if precio_compra <= 0:
                raise forms.ValidationError(
                    f'El precio de compra resultante debe ser positivo. '
                    f'Precio base: {precio_base:,} Gs., Comisión de compra: {comision_compra:,} Gs. '
                    f'= Precio de compra: {precio_compra:,} Gs.'
                )
        
        # Verificar si ya existe una cotización activa para informar al usuario
        if moneda and not self.instance.pk:
            cotizacion_existente = TasaCambio.objects.filter(
                moneda=moneda,
                es_activa=True
            ).first()
            
            if cotizacion_existente:
                # Agregar información al cleaned_data para usar en la vista
                cleaned_data['cotizacion_existente'] = cotizacion_existente
        
        return cleaned_data

    def clean_precio_base(self):
        precio_base = self.cleaned_data.get('precio_base')
        if precio_base and precio_base <= 0:
            raise forms.ValidationError('El precio base debe ser mayor que cero.')
        return precio_base

    def clean_comision_compra(self):
        comision_compra = self.cleaned_data.get('comision_compra')
        if comision_compra and comision_compra < 0:
            raise forms.ValidationError('La comisión de compra no puede ser negativa.')
        return comision_compra

    def clean_comision_venta(self):
        comision_venta = self.cleaned_data.get('comision_venta')
        if comision_venta and comision_venta < 0:
            raise forms.ValidationError('La comisión de venta no puede ser negativa.')
        return comision_venta


class TasaCambioSearchForm(forms.Form):
    """
    Formulario para búsqueda y filtros de cotizaciones
    """
    q = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por moneda, código o símbolo...'
        }),
        label='Buscar'
    )
    
    moneda = forms.ModelChoiceField(
        required=False,
        queryset=Moneda.objects.filter(es_activa=True).order_by('nombre'),
        empty_label="Todas las monedas",
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Moneda'
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
    
    fecha_desde = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label='Fecha desde'
    )
    
    fecha_hasta = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        }),
        label='Fecha hasta'
    )