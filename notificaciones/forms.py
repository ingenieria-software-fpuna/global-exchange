"""
Formularios para configuración de notificaciones
"""
from django import forms
from usuarios.models import Usuario


class PreferenciasNotificacionesForm(forms.ModelForm):
    """Formulario para configurar preferencias de notificaciones del usuario"""
    
    class Meta:
        model = Usuario
        fields = ['recibir_notificaciones_email', 'recibir_notificaciones_pago']
        widgets = {
            'recibir_notificaciones_email': forms.CheckboxInput(
                attrs={
                    'class': 'form-check-input',
                    'role': 'switch'
                }
            ),
            'recibir_notificaciones_pago': forms.CheckboxInput(
                attrs={
                    'class': 'form-check-input',
                    'role': 'switch'
                }
            ),
        }
        labels = {
            'recibir_notificaciones_email': 'Recibir notificaciones de tasas de cambio por correo electrónico',
            'recibir_notificaciones_pago': 'Recibir notificaciones de pagos exitosos por correo electrónico',
        }
        help_texts = {
            'recibir_notificaciones_email': 
                'Activa esta opción para recibir un correo cada vez que cambie una tasa de cambio.',
            'recibir_notificaciones_pago':
                'Activa esta opción para recibir un correo electrónico cada vez que realices un pago exitoso.',
        }
