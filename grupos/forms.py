from django import forms
from django.contrib.auth.models import Group, Permission

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
