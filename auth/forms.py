from django import forms
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.forms import PasswordResetForm
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
                self.user_cache = authenticate(username=user.email, password=password)
            except user_model.DoesNotExist:
                raise forms.ValidationError("El correo electrónico no existe.")
            
            if self.user_cache is None:
                raise forms.ValidationError("Contraseña inválida.")

        return cleaned_data
        
    def get_user(self):
        return self.user_cache
class VerificationCodeForm(forms.Form):
    code = forms.CharField(
        max_length=6,
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Código de 6 dígitos'}),
        label="Código de Verificación"
    )


