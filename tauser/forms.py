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
        fields = ['tauser', 'moneda', 'cantidad', 'cantidad_minima', 'es_activo']
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
            'cantidad_minima': forms.NumberInput(attrs={
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
            'cantidad_minima': 'Cantidad Mínima',
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

    def clean_cantidad_minima(self):
        cantidad_minima = self.cleaned_data.get('cantidad_minima')
        if cantidad_minima is not None and cantidad_minima < 0:
            raise forms.ValidationError('La cantidad mínima no puede ser negativa.')
        return cantidad_minima

    def clean(self):
        cleaned_data = super().clean()
        cantidad = cleaned_data.get('cantidad')
        cantidad_minima = cleaned_data.get('cantidad_minima')
        
        if cantidad is not None and cantidad_minima is not None:
            if cantidad < cantidad_minima:
                raise forms.ValidationError('La cantidad no puede ser menor que la cantidad mínima.')
        
        # Verificar que no exista ya un stock para este tauser y moneda
        tauser = cleaned_data.get('tauser')
        moneda = cleaned_data.get('moneda')
        
        if tauser and moneda:
            existing_stock = Stock.objects.filter(tauser=tauser, moneda=moneda)
            if self.instance.pk:
                existing_stock = existing_stock.exclude(pk=self.instance.pk)
            
            if existing_stock.exists():
                raise forms.ValidationError('Ya existe un stock para este Tauser y Moneda.')
        
        return cleaned_data
