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


class TarjetaCreditoLocalForm(forms.Form):
    """Formulario para datos de tarjeta de crédito local (Panal, Cabal)"""
    
    TIPO_TARJETA_CHOICES = [
        ('panal', 'Panal'),
        ('cabal', 'Cabal')
    ]
    
    tipo_tarjeta = forms.ChoiceField(
        choices=TIPO_TARJETA_CHOICES,
        label="Tipo de tarjeta",
        help_text="Seleccione el tipo de tarjeta de crédito local",
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )
    
    numero_tarjeta = forms.CharField(
        max_length=19,
        label="Número de tarjeta",
        help_text="Ingrese los dígitos de su tarjeta de crédito local",
        validators=[
            RegexValidator(
                regex=r'^[\d\s]{13,19}$',
                message="Ingrese un número de tarjeta válido"
            )
        ],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'XXXX XXXX XXXX XXXX'
        })
    )
    
    nombre_titular = forms.CharField(
        max_length=100,
        label="Nombre del titular",
        help_text="Nombre completo como aparece en la tarjeta",
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'JUAN PEREZ',
            'style': 'text-transform: uppercase;'
        })
    )
    
    fecha_vencimiento = forms.CharField(
        max_length=5,
        label="Fecha de vencimiento",
        help_text="MM/AA",
        validators=[
            RegexValidator(
                regex=r'^(0[1-9]|1[0-2])\/\d{2}$',
                message="Ingrese una fecha válida en formato MM/AA"
            )
        ],
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'MM/AA'
        })
    )
    
    codigo_seguridad = forms.CharField(
        max_length=4,
        label="Código de seguridad",
        help_text="CVV (3 o 4 dígitos al reverso de la tarjeta)",
        validators=[
            RegexValidator(
                regex=r'^\d{3,4}$',
                message="El código de seguridad debe tener 3 o 4 dígitos"
            )
        ],
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'XXX'
        })
    )
    
    cuotas = forms.ChoiceField(
        choices=[
            ('1', '1 cuota (único pago)'),
            ('2', '2 cuotas'),
            ('3', '3 cuotas'),
            ('6', '6 cuotas'),
            ('12', '12 cuotas'),
        ],
        label="Cantidad de cuotas",
        help_text="Seleccione el número de cuotas para el pago",
        initial='1',
        widget=forms.Select(attrs={
            'class': 'form-select'
        })
    )