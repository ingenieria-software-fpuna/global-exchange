from django import forms
from django.core.validators import MinValueValidator
from .models import ConfiguracionSistema


class ConfiguracionSistemaForm(forms.ModelForm):
    """
    Formulario para configurar los límites de transacciones del sistema.
    """
    limite_diario_transacciones = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'min': '0',
            'placeholder': '0.00'
        }),
        label="Límite Diario de Transacciones",
        help_text="Monto máximo permitido para transacciones por día. 0 = sin límite."
    )
    
    limite_mensual_transacciones = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'min': '0',
            'placeholder': '0.00'
        }),
        label="Límite Mensual de Transacciones",
        help_text="Monto máximo permitido para transacciones por mes. 0 = sin límite."
    )

    class Meta:
        model = ConfiguracionSistema
        fields = ['limite_diario_transacciones', 'limite_mensual_transacciones']

    def clean(self):
        cleaned_data = super().clean()
        limite_diario = cleaned_data.get('limite_diario_transacciones')
        limite_mensual = cleaned_data.get('limite_mensual_transacciones')

        # Validar que el límite mensual sea mayor o igual al límite diario
        if limite_diario and limite_mensual and limite_mensual < limite_diario:
            raise forms.ValidationError(
                "El límite mensual debe ser mayor o igual al límite diario."
            )

        return cleaned_data
