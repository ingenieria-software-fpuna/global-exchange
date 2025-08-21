# apps/usuarios/forms.py
from django import forms
from django.contrib.auth import authenticate

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