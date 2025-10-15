from django import forms
from django.core.validators import RegexValidator


class BilleteraElectronicaForm(forms.Form):
    """Formulario para datos de billetera electrónica"""
    numero_telefono = forms.CharField(
        max_length=20,
        label="Número de teléfono",
        help_text="Ingrese el número de teléfono asociado a su billetera electrónica",
        validators=[
            RegexValidator(
                regex=r'^\+?[\d\s\-\(\)]+$',
                message="Ingrese un número de teléfono válido"
            )
        ],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': '+595 XXX XXX XXX'
        })
    )
    
    pin_autorizacion = forms.CharField(
        max_length=6,
        label="PIN de autorización",
        help_text="Ingrese su PIN de autorización de 4 a 6 dígitos",
        validators=[
            RegexValidator(
                regex=r'^\d{4,6}$',
                message="El PIN debe tener entre 4 y 6 dígitos"
            )
        ],
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'XXXX'
        })
    )


class TarjetaDebitoForm(forms.Form):
    """Formulario para datos de tarjeta de débito"""
    numero_tarjeta = forms.CharField(
        max_length=19,
        label="Número de tarjeta",
        help_text="Ingrese los 16 dígitos de su tarjeta de débito",
        validators=[
            RegexValidator(
                regex=r'^[\d\s]{13,19}$',
                message="Ingrese un número de tarjeta válido"
            )
        ],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'XXXX XXXX XXXX XXXX',
            'maxlength': '19'
        })
    )
    
    fecha_vencimiento = forms.CharField(
        max_length=5,
        label="Fecha de vencimiento",
        help_text="Formato MM/AA",
        validators=[
            RegexValidator(
                regex=r'^(0[1-9]|1[0-2])\/\d{2}$',
                message="Formato inválido. Use MM/AA"
            )
        ],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'MM/AA',
            'maxlength': '5'
        })
    )
    
    cvv = forms.CharField(
        max_length=4,
        label="CVV",
        help_text="Código de seguridad de 3 o 4 dígitos",
        validators=[
            RegexValidator(
                regex=r'^\d{3,4}$',
                message="El CVV debe tener 3 o 4 dígitos"
            )
        ],
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'XXX',
            'maxlength': '4'
        })
    )
    
    nombre_titular = forms.CharField(
        max_length=100,
        label="Nombre del titular",
        help_text="Nombre como aparece en la tarjeta",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'JUAN PEREZ'
        })
    )


class TransferenciaBancariaForm(forms.Form):
    """Formulario para datos de transferencia bancaria"""
    numero_comprobante = forms.CharField(
        max_length=50,
        label="Número de comprobante",
        help_text="Ingrese el número de comprobante de su transferencia bancaria",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: TRF123456789'
        })
    )
    
    banco_origen = forms.CharField(
        max_length=100,
        label="Banco origen",
        help_text="Nombre del banco desde donde realizó la transferencia",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Ej: Banco Nacional'
        })
    )
    
    fecha_transferencia = forms.DateField(
        label="Fecha de transferencia",
        help_text="Fecha en que realizó la transferencia",
        widget=forms.DateInput(attrs={
            'class': 'form-control',
            'type': 'date'
        })
    )
    
    observaciones = forms.CharField(
        max_length=500,
        required=False,
        label="Observaciones",
        help_text="Información adicional (opcional)",
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'rows': 3,
            'placeholder': 'Observaciones adicionales...'
        })
    )