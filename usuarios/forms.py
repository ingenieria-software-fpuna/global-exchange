# apps/usuarios/forms.py
from django import forms
from django.contrib.auth import authenticate, get_user_model
from roles.models import Rol, UsuarioRol
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
            self.user_cache = authenticate(username=email, password=password)
            if self.user_cache is None:
                raise forms.ValidationError("Correo electrónico o contraseña inválidos.")
        
        return cleaned_data
    

Usuario = get_user_model()
class UsuarioCreationForm(forms.ModelForm):
    password = forms.CharField(label="Contraseña", widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    password2 = forms.CharField(label="Repetir Contraseña", widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    roles = forms.ModelMultipleChoiceField(
        queryset=Rol.objects.filter(activo=True).order_by('nombre'),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Roles"
    )

    class Meta:
        model = Usuario
        fields = ('email', 'nombre', 'apellido')
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'apellido': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()

        # Sincronizar roles seleccionados
        roles_seleccionados = self.cleaned_data.get('roles')
        if roles_seleccionados is not None:
            # Eliminar relaciones no seleccionadas (no habrá ninguna en creación, pero es seguro)
            UsuarioRol.objects.filter(usuario=user).exclude(rol__in=roles_seleccionados).delete()
            # Crear las relaciones faltantes
            for rol in roles_seleccionados:
                UsuarioRol.objects.get_or_create(usuario=user, rol=rol)

        return user

class UsuarioUpdateForm(forms.ModelForm):
    roles = forms.ModelMultipleChoiceField(
        queryset=Rol.objects.filter(activo=True).order_by('nombre'),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Roles"
    )
    class Meta:
        model = Usuario
        fields = ('email', 'nombre', 'apellido', 'is_staff', 'is_superuser', 'activo')
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'apellido': forms.TextInput(attrs={'class': 'form-control'}),
        }
    
    def get_user(self):
        return self.user_cache

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Pre-cargar roles asignados al usuario
        if self.instance and self.instance.pk:
            self.fields['roles'].initial = Rol.objects.filter(usuario_roles__usuario=self.instance).values_list('pk', flat=True)

    def save(self, commit=True):
        user = super().save(commit=commit)

        # Sincronizar roles seleccionados
        roles_seleccionados = self.cleaned_data.get('roles')
        if roles_seleccionados is not None:
            UsuarioRol.objects.filter(usuario=user).exclude(rol__in=roles_seleccionados).delete()
            for rol in roles_seleccionados:
                UsuarioRol.objects.get_or_create(usuario=user, rol=rol)

        return user
