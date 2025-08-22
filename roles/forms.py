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