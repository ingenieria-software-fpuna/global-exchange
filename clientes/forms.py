from django import forms
from django.contrib.auth import get_user_model
from .models import Cliente, TipoCliente
from .widgets import UsuarioSelectorWidget

User = get_user_model()

class ClienteForm(forms.ModelForm):
    """
    Formulario para crear clientes (sin campo activo).
    """
    
    usuarios_asociados = forms.ModelMultipleChoiceField(
        queryset=User.objects.none(),
        widget=UsuarioSelectorWidget(),
        required=False,
        label="Usuarios Asociados",
        help_text="Usuarios que pueden operar en nombre de este cliente."
    )
    
    class Meta:
        model = Cliente
        fields = [
            'nombre_comercial', 'ruc', 'direccion', 'correo_electronico',
            'numero_telefono', 'tipo_cliente', 'usuarios_asociados'
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
        
        # Marcar campos requeridos
        self.fields['nombre_comercial'].required = True
        self.fields['ruc'].required = True
        self.fields['correo_electronico'].required = True
        self.fields['tipo_cliente'].required = True

    def save(self, commit=True):
        cliente = super().save(commit=False)
        cliente.activo = True
        if commit:
            cliente.save()
            self.save_m2m()
        return cliente


class ClienteUpdateForm(forms.ModelForm):
    """
    Formulario para editar clientes (incluye campo activo).
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
        help_texts = {
            'monto_limite_transaccion': 'El monto límite debe estar expresado en guaraníes (PYG). Vacío = sin límite.',
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


class TipoClienteForm(forms.ModelForm):
    """
    Formulario para crear y editar tipos de cliente con estilo Bootstrap.
    """

    class Meta:
        model = TipoCliente
        fields = ['nombre', 'descripcion', 'descuento']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Cliente VIP, Cliente Regular, Cliente Corporativo'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descripción detallada del tipo de cliente...'
            }),
            'descuento': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'max': '100',
                'step': '0.01',
                'placeholder': '0.00'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Configurar labels
        self.fields['nombre'].label = "Nombre del Tipo"
        self.fields['descripcion'].label = "Descripción"
        self.fields['descuento'].label = "Descuento (%)"

        # Configurar help texts
        self.fields['nombre'].help_text = "Nombre único e identificativo del tipo de cliente"
        self.fields['descripcion'].help_text = "Descripción detallada del tipo de cliente (opcional)"
        self.fields['descuento'].help_text = "Porcentaje de descuento en comisiones (0-100)"

        # Marcar campos requeridos
        self.fields['nombre'].required = True
        self.fields['descuento'].required = True

    def save(self, commit=True):
        tipo_cliente = super().save(commit=False)
        # Ensure new tipos are active by default
        if not tipo_cliente.pk:  # Only for new instances
            tipo_cliente.activo = True
        if commit:
            tipo_cliente.save()
        return tipo_cliente


class TipoClienteUpdateForm(forms.ModelForm):
    """
    Formulario para editar tipos de cliente que incluye el campo activo.
    """

    class Meta:
        model = TipoCliente
        fields = ['nombre', 'descripcion', 'descuento', 'activo']
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Cliente VIP, Cliente Regular, Cliente Corporativo'
            }),
            'descripcion': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Descripción detallada del tipo de cliente...'
            }),
            'descuento': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': '0',
                'max': '100',
                'step': '0.01',
                'placeholder': '0.00'
            }),
            'activo': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Configurar labels
        self.fields['nombre'].label = "Nombre del Tipo"
        self.fields['descripcion'].label = "Descripción"
        self.fields['descuento'].label = "Descuento (%)"
        self.fields['activo'].label = "Activo"

        # Configurar help texts
        self.fields['nombre'].help_text = "Nombre único e identificativo del tipo de cliente"
        self.fields['descripcion'].help_text = "Descripción detallada del tipo de cliente (opcional)"
        self.fields['descuento'].help_text = "Porcentaje de descuento en comisiones (0-100)"
        self.fields['activo'].help_text = "Indica si este tipo de cliente está activo en el sistema"

        # Marcar campos requeridos
        self.fields['nombre'].required = True
        self.fields['descuento'].required = True
