from django import forms
from .models import Tauser, Stock


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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Formatear la fecha para el input datetime-local
        if self.instance and self.instance.pk and self.instance.fecha_instalacion:
            # Convertir a formato YYYY-MM-DDTHH:MM para datetime-local
            fecha_formateada = self.instance.fecha_instalacion.strftime('%Y-%m-%dT%H:%M')
            self.initial['fecha_instalacion'] = fecha_formateada

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


class StockForm(forms.ModelForm):
    """Formulario para crear y editar Stock"""

    class Meta:
        model = Stock
        fields = ['tauser', 'moneda', 'cantidad', 'es_activo']
        widgets = {
            'tauser': forms.Select(attrs={
                'class': 'form-select',
            }),
            'moneda': forms.Select(attrs={
                'class': 'form-select',
            }),
            'cantidad': forms.NumberInput(attrs={
                'class': 'form-control',
                'step': '0.01',
                'min': '0',
                'placeholder': '0.00'
            }),
            'es_activo': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'tauser': 'Tauser',
            'moneda': 'Moneda',
            'cantidad': 'Cantidad',
            'es_activo': 'Activo',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Filtrar solo tausers activos
        self.fields['tauser'].queryset = Tauser.objects.filter(es_activo=True).order_by('nombre')
        # Filtrar solo monedas activas
        from monedas.models import Moneda
        self.fields['moneda'].queryset = Moneda.objects.filter(es_activa=True).order_by('nombre')

    def clean_cantidad(self):
        cantidad = self.cleaned_data.get('cantidad')
        if cantidad is not None and cantidad < 0:
            raise forms.ValidationError('La cantidad no puede ser negativa.')
        return cantidad



class CargarStockDenominacionForm(forms.Form):
    """Formulario para cargar stock por denominaciones"""
    
    moneda = forms.ModelChoiceField(
        queryset=None,
        widget=forms.Select(attrs={
            'class': 'form-select',
            'id': 'moneda_select'
        }),
        label='Moneda',
        help_text='Selecciona la moneda para cargar stock'
    )
    
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        from monedas.models import Moneda
        self.fields['moneda'].queryset = Moneda.objects.filter(es_activa=True).order_by('nombre')
    


class DenominacionStockForm(forms.Form):
    """Formulario dinámico para cada denominación"""
    
    def __init__(self, denominacion, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.denominacion = denominacion
        
        # Campo para cantidad de billetes/monedas
        self.fields[f'cantidad_{denominacion.pk}'] = forms.IntegerField(
            min_value=0,
            initial=0,
            required=False,
            widget=forms.NumberInput(attrs={
                'class': 'form-control denominacion-cantidad',
                'data-denominacion-id': denominacion.pk,
                'data-valor': str(denominacion.valor),
                'placeholder': '0'
            }),
            label=f'Cantidad de {denominacion.tipo}s de {denominacion.mostrar_denominacion()}',
            help_text=f'Cantidad de {denominacion.tipo.lower()}s de {denominacion.mostrar_denominacion()}'
        )
        
    
    def clean(self):
        cleaned_data = super().clean()
        cantidad_key = f'cantidad_{self.denominacion.pk}'
        cantidad = cleaned_data.get(cantidad_key, 0)
        
        if cantidad and cantidad < 0:
            raise forms.ValidationError(f'La cantidad de {self.denominacion.tipo.lower()}s no puede ser negativa.')
        
        return cleaned_data
