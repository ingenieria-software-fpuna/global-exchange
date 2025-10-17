# Crear una App de Notificaciones en Django

### Usuario: 
hola quiero hacer una app en django para manejar notificaciones cuando cambian las tasas de cambio como empiezo

### IA: 
hola para empezar necesitamos crear el modelo que va a representar las notificaciones te dejo el código para el modelo `Notificacion` que vamos a usar en el archivo `models.py este modelo tiene campos como `usuario`, `tipo`, `titulo`, `mensaje` y otros que nos van a permitir almacenar la información de las notificaciones

```python
from django.db import models
from django.contrib.auth import get_user_model
from monedas.models import Moneda

Usuario = get_user_model()

class Notificacion(models.Model):
    TIPO_CHOICES = [
        ('tasa_cambio', 'Cambio de Tasa'),
    ]
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='notificaciones')
    tipo = models.CharField(max_length=20, choices=TIPO_CHOICES, default='tasa_cambio')
    titulo = models.CharField(max_length=200)
    mensaje = models.TextField()
    moneda = models.ForeignKey(Moneda, on_delete=models.SET_NULL, null=True, blank=True)
    leida = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_lectura = models.DateTimeField(null=True, blank=True)
con este modelo vamos a poder guardar las notificaciones que se le envían a los usuarios

Usuario:
genial y cómo generamos esas notificaciones cuando cambian las tasas de cambio

IA:
para generar las notificaciones cuando cambian las tasas de cambio usamos señales de django (signals) en el archivo signals.py definimos cómo escuchar los cambios en el modelo TasaCambio` y generar las notificaciones automáticamente te dejo el código

python
Copiar código
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Notificacion
from tasa_cambio.models import TasaCambio

@receiver(post_save, sender=TasaCambio)
def notificar_cambio_tasa(sender, instance, created, **kwargs):
    if not instance.es_activa:
        return
    usuarios = Usuario.objects.filter(groups__name__in=['Operador', 'Visitante'], es_activo=True)
    titulo = f"Nuevo cambio de tasa: {instance.moneda.nombre}"
    mensaje = f"La tasa de cambio para {instance.moneda.nombre} ha cambiado."
    
    # Crear las notificaciones
    for usuario in usuarios:
        notificacion = Notificacion(
            usuario=usuario,
            tipo='tasa_cambio',
            titulo=titulo,
            mensaje=mensaje,
            moneda=instance.moneda
        )
        notificacion.save()
usamos la señal post_save para detectar cuando se guarda una nueva TasaCambio si el cambio es válido y la tasa está activa se generan las notificaciones para los usuarios de los grupos Operador y Visitante

Usuario:
perfecto y cómo enviamos correos a los usuarios para notificarles

IA:
para enviar correos electrónicos agregamos una función en la señal aquí te dejo el código para enviar un correo a los usuarios que tienen activada la opción de recibir notificaciones por correo electrónico

python
Copiar código
from django.core.mail import send_mail
from django.template.loader import render_to_string

def enviar_emails_notificacion(usuarios, moneda, precio_nuevo):
    for usuario in usuarios:
        context = {
            'usuario': usuario,
            'moneda': moneda,
            'precio_nuevo': precio_nuevo,
        }
        html_message = render_to_string('notificaciones/email_notificacion.html', context)
        
        send_mail(
            subject=f"🔔 Cambio en cotización: {moneda.nombre}",
            message='',
            from_email='noreply@tusitio.com',
            recipient_list=[usuario.email],
            html_message=html_message
        )
este código renderiza el contenido del correo usando un template HTML (email_notificacion.html después usamos send_mail para enviar el correo a todos los usuarios con la preferencia activada

Usuario:
puedo personalizar el asunto y el contenido del correo

IA:
sí claro puedes personalizar tanto el asunto como el contenido del correo por ejemplo si el cambio es un aumento en la tasa podemos agregar un icono de gráfico ascendente en el asunto

python
Copiar código
if es_aumento:
    asunto = f"📈 Cambio en cotización: {moneda.nombre}"
else:
    asunto = f"📉 Cambio en cotización: {moneda.nombre}"
y para el cuerpo del correo puedes modificar el template `email_notificacion.html para mostrar cualquier detalle que desees como el porcentaje de cambio y las tasas de compra y venta anteriores y nuevas

Usuario:
genial ahora cómo hago para que los usuarios puedan ver las notificaciones en la app

IA:
para mostrar las notificaciones en la app necesitas una vista en django que recupere las notificaciones y las pase a un template HTML te dejo un ejemplo

python
Copiar código
from django.shortcuts import render
from .models import Notificacion

def ver_notificaciones(request):
    notificaciones = Notificacion.objects.filter(usuario=request.user)
    return render(request, 'notificaciones/ver_notificaciones.html', {'notificaciones': notificaciones})
y en el template `ver_notificaciones.html puedes mostrar las notificaciones así

html
Copiar código
<ul>
    {% for notificacion in notificaciones %}
        <li>
            <strong>{{ notificacion.titulo }}</strong><br>
            {{ notificacion.mensaje }}<br>
            <small>{{ notificacion.fecha_creacion }}</small>
        </li>
    {% endfor %}
</ul>