from django import forms
from django.core.validators import MinValueValidator
from django.utils import timezone
from .models import TasaCambio
from monedas.models import Moneda


class TasaCambioForm(forms.ModelForm):
    """
    Formulario para crear y editar tasas de cambio
    """
    
    class Meta:
        model = TasaCambio
        fields = [
            'moneda', 'tasa_compra', 'tasa_venta', 'fecha_vigencia', 'es_activa'
        ]
        widgets = {
            'moneda': forms.Select(attrs={
                'class': 'form-select',
                'placeholder': 'Seleccione una moneda'
            }),
            'tasa_compra': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: 1.25',
                'step': 'any',
                'min': '0.00000001'
            }),
            'tasa_venta': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: 1.26',
                'step': 'any',
                'min': '0.00000001'
            }),
            'fecha_vigencia': forms.DateTimeInput(attrs={
                'class': 'form-control',
                'type': 'datetime-local',
                'placeholder': 'Fecha y hora de vigencia'
            }),
            'es_activa': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'moneda': 'Moneda',
            'tasa_compra': 'Tasa de Compra',
            'tasa_venta': 'Tasa de Venta',
            'fecha_vigencia': 'Fecha de Vigencia',
            'es_activa': 'Cotización Activa',
        }
        help_texts = {
            'moneda': 'Seleccione la moneda para la cual se establece la cotización',
            'tasa_compra': 'Precio al cual se compra la moneda (mínimo 0.0001)',
            'tasa_venta': 'Precio al cual se vende la moneda (mínimo 0.0001)',
            'fecha_vigencia': 'Fecha y hora desde la cual la cotización estará vigente',
            'es_activa': 'Indica si la cotización está disponible para operaciones',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Filtrar solo monedas activas para el selector
        self.fields['moneda'].queryset = Moneda.objects.filter(es_activa=True).order_by('nombre')
        
        # Establecer fecha y hora actual como valor por defecto
        if not self.instance.pk:
            self.fields['fecha_vigencia'].initial = timezone.now().strftime('%Y-%m-%dT%H:%M')

    def clean(self):
        cleaned_data = super().clean()
        tasa_compra = cleaned_data.get('tasa_compra')
        tasa_venta = cleaned_data.get('tasa_venta')
        moneda = cleaned_data.get('moneda')
        
        # Validar que la tasa de venta sea mayor que la de compra
        if tasa_compra and tasa_venta:
            if tasa_venta <= tasa_compra:
                raise forms.ValidationError(
                    'La tasa de venta debe ser mayor que la tasa de compra.'
                )
        
        # Validar que las tasas respeten los decimales de la moneda
        if moneda and (tasa_compra or tasa_venta):
            decimales_moneda = moneda.decimales
            
            if tasa_compra:
                # Verificar que la tasa de compra no tenga más decimales de los permitidos
                str_compra = str(tasa_compra)
                if '.' in str_compra:
                    decimales_compra = len(str_compra.split('.')[1])
                    if decimales_compra > decimales_moneda:
                        raise forms.ValidationError(
                            f'La tasa de compra no puede tener más de {decimales_moneda} decimales '
                            f'(configurado para {moneda.nombre}).'
                        )
            
            if tasa_venta:
                # Verificar que la tasa de venta no tenga más decimales de los permitidos
                str_venta = str(tasa_venta)
                if '.' in str_venta:
                    decimales_venta = len(str_venta.split('.')[1])
                    if decimales_venta > decimales_moneda:
                        raise forms.ValidationError(
                            f'La tasa de venta no puede tener más de {decimales_moneda} decimales '
                            f'(configurado para {moneda.nombre}).'
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

    def clean_tasa_compra(self):
        tasa_compra = self.cleaned_data.get('tasa_compra')
        if tasa_compra and tasa_compra <= 0:
            raise forms.ValidationError('La tasa de compra debe ser mayor que cero.')
        return tasa_compra

    def clean_tasa_venta(self):
        tasa_venta = self.cleaned_data.get('tasa_venta')
        if tasa_venta and tasa_venta <= 0:
            raise forms.ValidationError('La tasa de venta debe ser mayor que cero.')
        return tasa_venta


class TasaCambioSearchForm(forms.Form):
    """
    Formulario para búsqueda y filtros de tasas de cambio
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
