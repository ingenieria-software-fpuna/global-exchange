# apps/usuarios/forms.py
from django import forms
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.models import Group
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
    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all().order_by('name'),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Grupos"
    )

    class Meta:
        model = Usuario
        fields = ('email', 'nombre', 'apellido', 'cedula', 'fecha_nacimiento', 'groups')
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'apellido': forms.TextInput(attrs={'class': 'form-control'}),
            'cedula': forms.TextInput(attrs={'class': 'form-control'}),
            'fecha_nacimiento': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password2 = cleaned_data.get("password2")
        if password and password2 and password != password2:
            raise forms.ValidationError("Las contraseñas no coinciden.")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()

        # Sincronizar grupos seleccionados
        groups_seleccionados = self.cleaned_data.get('groups')
        if groups_seleccionados is not None:
            user.groups.set(groups_seleccionados)

        return user

class UsuarioUpdateForm(forms.ModelForm):
    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all().order_by('name'),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Grupos"
    )
    class Meta:
        model = Usuario
        fields = ('email', 'nombre', 'apellido', 'cedula', 'fecha_nacimiento', 'is_staff', 'activo', 'groups')
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'apellido': forms.TextInput(attrs={'class': 'form-control'}),
            'cedula': forms.TextInput(attrs={'class': 'form-control'}),
            'fecha_nacimiento': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }
    
    def get_user(self):
        return self.user_cache

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Pre-cargar grupos asignados al usuario
        if self.instance and self.instance.pk:
            self.fields['groups'].initial = self.instance.groups.values_list('pk', flat=True)

    def save(self, commit=True):
        user = super().save(commit=commit)

        # Sincronizar grupos seleccionados
        groups_seleccionados = self.cleaned_data.get('groups')
        if groups_seleccionados is not None:
            user.groups.set(groups_seleccionados)

        return user
