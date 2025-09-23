from django import forms
from django.contrib.auth import get_user_model
from .models import Cliente, TipoCliente
from .widgets import UsuarioSelectorWidget

User = get_user_model()

class ClienteForm(forms.ModelForm):
    """
    Formulario para crear y editar clientes con widget personalizado
    para selección de usuarios asociados.
    """
    
    usuarios_asociados = forms.ModelMultipleChoiceField(
        queryset=User.objects.none(),  # Se configurará en __init__
        widget=UsuarioSelectorWidget(),
        required=False,
        label="Usuarios Asociados",
        help_text="Usuarios que pueden operar en nombre de este cliente."
    )
    
    class Meta:
        model = Cliente
        fields = [
            'nombre_comercial', 'ruc', 'direccion', 'correo_electronico',
            'numero_telefono', 'tipo_cliente', 'monto_limite_transaccion', 'usuarios_asociados', 'activo'
        ]
        widgets = {
            'nombre_comercial': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Empresa ABC S.A.'
            }),
            'ruc': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: 801234567'
            }),
            'direccion': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Av. Principal 123, Asunción'
            }),
            'correo_electronico': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: contacto@empresa.com'
            }),
            'numero_telefono': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: +595 21 123456'
            }),
            'tipo_cliente': forms.Select(attrs={
                'class': 'form-select'
            }),
            'monto_limite_transaccion': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: 1000000.00',
                'min': '0',
                'step': '0.01'
            }),
            'activo': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Configurar queryset para usuarios activos
        self.fields['usuarios_asociados'].queryset = User.objects.filter(
            activo=True, es_activo=True
        ).order_by('nombre', 'apellido')
        
        # Configurar queryset para tipos de cliente activos
        self.fields['tipo_cliente'].queryset = TipoCliente.objects.filter(
            activo=True
        ).order_by('nombre')
        
        # Configurar labels y help texts
        self.fields['nombre_comercial'].label = "Nombre Comercial"
        self.fields['ruc'].label = "RUC"
        self.fields['direccion'].label = "Dirección"
        self.fields['correo_electronico'].label = "Correo Electrónico"
        self.fields['numero_telefono'].label = "Número de Teléfono"
        self.fields['tipo_cliente'].label = "Tipo de Cliente"
        self.fields['monto_limite_transaccion'].label = "Monto límite por transacción"
        self.fields['monto_limite_transaccion'].help_text = "Monto máximo permitido en una sola transacción. Vacío = sin límite."
        self.fields['activo'].label = "Activo"
        
        # Marcar campos requeridos
        self.fields['nombre_comercial'].required = True
        self.fields['ruc'].required = True
        self.fields['correo_electronico'].required = True
        self.fields['tipo_cliente'].required = True
