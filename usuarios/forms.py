# apps/usuarios/forms.py
from django import forms
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.models import Group
from datetime import date
from grupos.models import Grupo

class DateInput(forms.DateInput):
    """Widget personalizado para campos de fecha que asegura formato YYYY-MM-DD para HTML5"""
    input_type = 'date'
    
    def format_value(self, value):
        """Formatear el valor para que sea compatible con input type='date'"""
        if value is None:
            return ''
        if hasattr(value, 'strftime'):
            return value.strftime('%Y-%m-%d')
        return str(value)

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
    password1 = forms.CharField(label="Contraseña", widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    password2 = forms.CharField(label="Repetir Contraseña", widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.none(),  # Se configurará en __init__
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
            'fecha_nacimiento': DateInput(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        password1 = cleaned_data.get("password1")
        password2 = cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Las contraseñas no coinciden.")
        return cleaned_data
    
    def clean_fecha_nacimiento(self):
        fecha_nacimiento = self.cleaned_data.get('fecha_nacimiento')
        if fecha_nacimiento:
            today = date.today()
            age = today.year - fecha_nacimiento.year
            if today.month < fecha_nacimiento.month or (today.month == fecha_nacimiento.month and today.day < fecha_nacimiento.day):
                age -= 1
            if age < 18:
                raise forms.ValidationError("El usuario debe ser mayor de 18 años.")
        return fecha_nacimiento

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Configurar queryset para grupos activos
        grupos_activos = Grupo.objects.filter(es_activo=True).select_related('group')
        self.fields['groups'].queryset = Group.objects.filter(
            grupo_extension__in=grupos_activos
        ).order_by('name')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password1"])
        user.es_activo = True
        if commit:
            user.save()

        # Sincronizar grupos seleccionados
        groups_seleccionados = self.cleaned_data.get('groups')
        if groups_seleccionados is not None:
            user.groups.set(groups_seleccionados)

        return user

class UsuarioUpdateForm(forms.ModelForm):
    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.none(),  # Se configurará en __init__
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Grupos"
    )
    class Meta:
        model = Usuario
        fields = ('email', 'nombre', 'apellido', 'cedula', 'fecha_nacimiento', 'is_staff', 'es_activo', 'groups')
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'apellido': forms.TextInput(attrs={'class': 'form-control'}),
            'cedula': forms.TextInput(attrs={'class': 'form-control'}),
            'fecha_nacimiento': DateInput(attrs={'class': 'form-control'}),
        }
    
    def clean_fecha_nacimiento(self):
        fecha_nacimiento = self.cleaned_data.get('fecha_nacimiento')
        if fecha_nacimiento:
            today = date.today()
            # Calcular edad de manera más precisa
            age = today.year - fecha_nacimiento.year
            if today.month < fecha_nacimiento.month or (today.month == fecha_nacimiento.month and today.day < fecha_nacimiento.day):
                age -= 1
            if age < 18:
                raise forms.ValidationError("El usuario debe ser mayor de 18 años.")
        return fecha_nacimiento

    def get_user(self):
        return self.user_cache

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Configurar queryset para grupos activos
        grupos_activos = Grupo.objects.filter(es_activo=True).select_related('group')
        self.fields['groups'].queryset = Group.objects.filter(
            grupo_extension__in=grupos_activos
        ).order_by('name')
        
        # Pre-cargar grupos asignados al usuario
        if self.instance and self.instance.pk:
            self.fields['groups'].initial = self.instance.groups.values_list('pk', flat=True)
            # Asegurar que la fecha de nacimiento se muestre correctamente en el campo
            if self.instance.fecha_nacimiento:
                self.fields['fecha_nacimiento'].initial = self.instance.fecha_nacimiento.strftime('%Y-%m-%d')

    def save(self, commit=True):
        user = super().save(commit=commit)

        # Sincronizar grupos seleccionados
        groups_seleccionados = self.cleaned_data.get('groups')
        if groups_seleccionados is not None:
            user.groups.set(groups_seleccionados)

        return user
