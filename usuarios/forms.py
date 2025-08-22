# apps/usuarios/forms.py
from django import forms
from django.contrib.auth import authenticate,get_user_model
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
        return user

class UsuarioUpdateForm(forms.ModelForm):
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