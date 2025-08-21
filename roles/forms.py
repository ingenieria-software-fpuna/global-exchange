# # apps/roles/forms.py
# from django import forms
# from .models import Rol, Modulo, Permiso

# class RolForm(forms.ModelForm):
#     class Meta:
#         model = Rol
#         fields = ['nombre', 'codigo', 'descripcion', 'es_admin', 'activo']
#         widgets = {
#             'nombre': forms.TextInput(attrs={
#                 'class': 'form-control',
#                 'placeholder': 'Nombre del rol'
#             }),
#             'codigo': forms.TextInput(attrs={
#                 'class': 'form-control',
#                 'placeholder': 'Código único del rol'
#             }),
#             'descripcion': forms.Textarea(attrs={
#                 'class': 'form-control',
#                 'rows': 3,
#                 'placeholder': 'Descripción del rol'
#             }),
#             'es_admin': forms.CheckboxInput(attrs={
#                 'class': 'form-check-input'
#             }),
#             'activo': forms.CheckboxInput(attrs={
#                 'class': 'form-check-input'
#             }),
#         }
    
#     def clean_codigo(self):
#         codigo = self.cleaned_data['codigo'].lower().replace(' ', '_')
#         # Validar que no exista otro rol con el mismo código
#         if Rol.objects.filter(codigo=codigo).exclude(pk=self.instance.pk if self.instance else None).exists():
#             raise forms.ValidationError('Ya existe un rol con este código.')
#         return codigo

# class ModuloForm(forms.ModelForm):
#     class Meta:
#         model = Modulo
#         fields = ['nombre', 'codigo', 'descripcion', 'orden', 'activo']
#         widgets = {
#             'nombre': forms.TextInput(attrs={'class': 'form-control'}),
#             'codigo': forms.TextInput(attrs={'class': 'form-control'}),
#             'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
#             'orden': forms.NumberInput(attrs={'class': 'form-control'}),
#             'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
#         }

# class PermisoForm(forms.ModelForm):
#     class Meta:
#         model = Permiso
#         fields = ['nombre', 'codigo', 'descripcion', 'tipo', 'modulo', 'activo']
#         widgets = {
#             'nombre': forms.TextInput(attrs={'class': 'form-control'}),
#             'codigo': forms.TextInput(attrs={'class': 'form-control'}),
#             'descripcion': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
#             'tipo': forms.Select(attrs={'class': 'form-control'}),
#             'modulo': forms.Select(attrs={'class': 'form-control'}),
#             'activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
#         }

# class AsignarRolUsuarioForm(forms.Form):
#     usuario = forms.ModelChoiceField(
#         queryset=None,  # Se define en __init__
#         widget=forms.Select(attrs={'class': 'form-control'}),
#         label='Usuario'
#     )
#     rol = forms.ModelChoiceField(
#         queryset=Rol.objects.filter(activo=True),
#         widget=forms.Select(attrs={'class': 'form-control'}),
#         label='Rol'
#     )
    
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         # Importa aquí para evitar dependencias circulares
#         from apps.usuarios.models import Usuario
#         self.fields['usuario'].queryset = Usuario.objects.filter(activo=True)

# roles/forms.py
from django import forms
from .models import Rol, Permiso, Modulo

class RolForm(forms.ModelForm):
    permisos = forms.ModelMultipleChoiceField(
        queryset=Permiso.objects.select_related('modulo').all().order_by('modulo__nombre', 'nombre'),
        widget=forms.CheckboxSelectMultiple,
        required=False
    )
    
    class Meta:
        model = Rol
        fields = ['nombre', 'descripcion', 'codigo', 'es_admin', 'activo', 'permisos']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control'}),
            'codigo': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            self.fields['permisos'].initial = self.instance.permisos.values_list('pk', flat=True)

    def save(self, *args, **kwargs):
        rol = super().save(*args, **kwargs)
        if 'permisos' in self.cleaned_data:
            rol.permisos.set(self.cleaned_data['permisos'])
        return rol


class PermisoForm(forms.ModelForm):
    class Meta:
        model = Permiso
        fields = ['nombre', 'codigo', 'descripcion', 'tipo', 'modulo', 'activo']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'codigo': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control'}),
            'tipo': forms.Select(attrs={'class': 'form-control'}),
            'modulo': forms.Select(attrs={'class': 'form-control'}),
        }


class ModuloForm(forms.ModelForm):
    class Meta:
        model = Modulo
        fields = ['nombre', 'descripcion', 'codigo', 'orden', 'activo']
        widgets = {
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'descripcion': forms.Textarea(attrs={'class': 'form-control'}),
            'codigo': forms.TextInput(attrs={'class': 'form-control'}),
            'orden': forms.NumberInput(attrs={'class': 'form-control'}),
        }