from django import forms
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.forms import UserCreationForm
from usuarios.models import Usuario
class LoginForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Correo electrónico'}),
        label="Correo electrónico"
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Contraseña'}),
        label="Contraseña"
    )
    
    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        password = cleaned_data.get('password')
        
        if email and password:
            user_model = get_user_model()
            try:
                user = user_model.objects.get(email=email)
                
                # PRIMERO: Verificar la contraseña antes que nada
                authenticated_user = authenticate(username=user.email, password=password)
                
                if authenticated_user is None:
                    raise forms.ValidationError("Contraseña incorrecta")
                
                # SEGUNDO: Verificar si el usuario está activo
                if not user.es_activo:
                    raise forms.ValidationError("Tu cuenta está desactivada. Contacta al administrador.")
                
                # TERCERO: Verificar que el email está verificado
                if not user.activo:
                    # Guardar el usuario para poder reenviar verificación
                    self.unverified_user = user
                    raise forms.ValidationError("Debes verificar tu correo electrónico antes de iniciar sesión.")
                
                # Todo OK, guardar el usuario autenticado
                self.user_cache = authenticated_user
                    
            except user_model.DoesNotExist:
                raise forms.ValidationError("El correo electrónico no existe")

        return cleaned_data
        
    def get_user(self):
        return getattr(self, 'user_cache', None)
    
    def get_unverified_user(self):
        return getattr(self, 'unverified_user', None)
class VerificationCodeForm(forms.Form):
    code = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Código de verificación'}),
        label="Código de verificación",
        max_length=6
    )

class RegistroForm(UserCreationForm):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Correo electrónico'}),
        label="Correo electrónico",
        required=True
    )
    cedula = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': '12345678'}),
        label="Cédula de Identidad",
        max_length=20,
        required=True
    )
    nombre = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nombre'}),
        label="Nombre",
        max_length=100,
        required=True
    )
    apellido = forms.CharField(
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Apellido'}),
        label="Apellido",
        max_length=100,
        required=False
    )
    fecha_nacimiento = forms.DateField(
        widget=forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        label="Fecha de Nacimiento",
        required=True
    )
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Contraseña'}),
        label="Contraseña",
        required=True
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Confirmar contraseña'}),
        label="Confirmar contraseña",
        required=True
    )
    
    class Meta:
        model = Usuario
        fields = ('email', 'cedula', 'nombre', 'apellido', 'fecha_nacimiento', 'password1', 'password2')
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        if Usuario.objects.filter(email=email).exists():
            raise forms.ValidationError("Este correo electrónico ya está registrado.")
        return email
    
    def clean_cedula(self):
        cedula = self.cleaned_data.get('cedula')
        if Usuario.objects.filter(cedula=cedula).exists():
            raise forms.ValidationError("Esta cédula ya está registrada.")
        if not cedula.isdigit():
            raise forms.ValidationError("La cédula debe contener solo números.")
        if len(cedula) < 5:
            raise forms.ValidationError("La cédula debe tener al menos 5 dígitos.")
        return cedula