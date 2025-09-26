from django import forms
from django.contrib.auth.models import Group, Permission
from .models import Grupo

class GrupoCreationForm(forms.ModelForm):
    name = forms.CharField(
        label="Nombre",
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nombre del grupo'
        })
    )
    descripcion = forms.CharField(
        label="Descripción",
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Descripción opcional del grupo',
            'rows': 3
        })
    )

    class Meta:
        model = Grupo
        fields = []

    def save(self, commit=True):
        django_group = Group.objects.create(name=self.cleaned_data['name'])
        
        grupo = Grupo(group=django_group, es_activo=True)
        
        if commit:
            grupo.save()
        
        return grupo

class GrupoUpdateForm(forms.ModelForm):
    name = forms.CharField(
        label="Nombre",
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Nombre del grupo'
        })
    )
    descripcion = forms.CharField(
        label="Descripción",
        required=False,
        widget=forms.Textarea(attrs={
            'class': 'form-control',
            'placeholder': 'Descripción opcional del grupo',
            'rows': 3
        })
    )

    class Meta:
        model = Grupo
        fields = ['es_activo']
        widgets = {
            'es_activo': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance and self.instance.group:
            self.fields['name'].initial = self.instance.group.name

    def save(self, commit=True):
        grupo = super().save(commit=False)
        
        grupo.group.name = self.cleaned_data['name']
        if commit:
            grupo.group.save()
            grupo.save()
        
        return grupo

class GroupForm(forms.ModelForm):
    class Meta:
        model = Group
        fields = ['name']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Nombre del grupo'
            })
        }

class GroupPermissionsForm(forms.ModelForm):
    permissions = forms.ModelMultipleChoiceField(
        queryset=Permission.objects.all().select_related('content_type'),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        help_text="Selecciona los permisos para este grupo"
    )
    
    class Meta:
        model = Group
        fields = ['permissions']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Agrupar permisos por aplicación
        permissions = Permission.objects.all().select_related('content_type').order_by('content_type__app_label', 'content_type__model', 'codename')
        
        choices = []
        current_app = None
        
        for perm in permissions:
            app_label = perm.content_type.app_label
            model_name = perm.content_type.model
            
            if app_label != current_app:
                current_app = app_label
                choices.append((f'--- {app_label.upper()} ---', []))
            
            choices.append((perm.id, f"{model_name}: {perm.name}"))
        
        self.fields['permissions'].choices = choices
