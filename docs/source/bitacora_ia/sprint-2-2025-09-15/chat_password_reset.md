# Chat: Implementación de "Olvidé mi contraseña"

## Usuario
agregar al iniciar sesion un boton de "olvide mi contraseña" que permita al usuario con cuenta cambiar su contraseña mediante un enlace de restablecimiento enviado al correo electrónico registrado.

## Claude
Perfecto, voy a implementar la funcionalidad de "Olvidé mi contraseña" para el sistema.

### URLs

```python
urls = [
    # URLs para reset de contraseña
    path('olvide-mi-contrasena/', views.password_reset_request_view, name='password_reset_request'),
    path('reset-contrasena/<str:token>/', views.password_reset_confirm_view, name='password_reset_confirm'),
    path('contrasena-cambiada/', views.password_reset_complete_view, name='password_reset_complete'),
]
```

### Los formularios

```python
class PasswordResetRequestForm(forms.Form):
    """Formulario para solicitar reset de contraseña"""
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'class': 'form-control', 
            'placeholder': 'Correo electrónico'
        }),
        label="Correo electrónico",
        help_text="Ingresa tu correo electrónico para recibir las instrucciones de restablecimiento."
    )
    
    def clean_email(self):
        email = self.cleaned_data.get('email')
        user_model = get_user_model()
        try:
            user = user_model.objects.get(email=email)
            if not user.es_activo:
                raise forms.ValidationError("Tu cuenta está desactivada. Contacta al administrador.")
            if not user.activo:
                raise forms.ValidationError("Tu cuenta no está verificada. Verifica tu correo primero.")
            self.user_cache = user
        except user_model.DoesNotExist:
            raise forms.ValidationError("No existe una cuenta con este correo electrónico.")
        return email
    
    def get_user(self):
        return getattr(self, 'user_cache', None)


class PasswordResetForm(forms.Form):
    """Formulario para establecer nueva contraseña"""
    password1 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control', 
            'placeholder': 'Nueva contraseña'
        }),
        label="Nueva contraseña",
        min_length=8,
        help_text="La contraseña debe tener al menos 8 caracteres."
    )
    password2 = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control', 
            'placeholder': 'Confirmar nueva contraseña'
        }),
        label="Confirmar nueva contraseña"
    )
    
    def clean_password2(self):
        password1 = self.cleaned_data.get('password1')
        password2 = self.cleaned_data.get('password2')
        
        if password1 and password2 and password1 != password2:
            raise forms.ValidationError("Las contraseñas no coinciden.")
        
        return password2
```

Ahora voy a agregar el modelo para tokens de reset de contraseña:

```python
class PasswordResetToken(models.Model):
    """Modelo para tokens de reset de contraseña"""
    
    usuario = models.ForeignKey(
        get_user_model(),
        on_delete=models.CASCADE,
        verbose_name="Usuario"
    )
    token = models.CharField(
        max_length=64,
        unique=True,
        verbose_name="Token"
    )
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de Creación"
    )
    fecha_expiracion = models.DateTimeField(
        verbose_name="Fecha de Expiración"
    )
    usado = models.BooleanField(
        default=False,
        verbose_name="Usado"
    )
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name="Dirección IP"
    )
    
    class Meta:
        verbose_name = "Token de Reset de Contraseña"
        verbose_name_plural = "Tokens de Reset de Contraseña"
    
    def __str__(self):
        return f"Token para {self.usuario.email} - {self.fecha_creacion}"
    
    def save(self, *args, **kwargs):
        if not self.token:
            self.token = self.generar_token()
        if not self.fecha_expiracion:
            # Token válido por 1 hora
            self.fecha_expiracion = timezone.now() + timedelta(hours=1)
        super().save(*args, **kwargs)
    
    def generar_token(self):
        """Genera un token único"""
        while True:
            token = ''.join(random.choices(string.ascii_letters + string.digits, k=64))
            if not PasswordResetToken.objects.filter(token=token).exists():
                return token
    
    def marcar_como_usado(self):
        """Marca el token como usado"""
        self.usado = True
        self.save()
    
    def es_valido(self):
        """Verifica si el token es válido"""
        return not self.usado and self.fecha_expiracion > timezone.now()
    
    @classmethod
    def limpiar_tokens_expirados(cls):
        """Limpia tokens expirados y usados antiguos"""
        fecha_limite = timezone.now() - timedelta(hours=24)
        cls.objects.filter(
            models.Q(fecha_expiracion__lt=timezone.now()) |
            models.Q(usado=True, fecha_creacion__lt=fecha_limite)
        ).delete()
    
    @classmethod
    def crear_token(cls, usuario, request=None):
        """Crea un nuevo token para el usuario"""
        # Limpiar tokens anteriores del usuario
        cls.objects.filter(usuario=usuario).delete()
        
        # Crear nuevo token
        token = cls.objects.create(
            usuario=usuario,
            ip_address=request.META.get('REMOTE_ADDR') if request else None
        )
        return token
```

Ahora voy a actualizar el EmailService para manejar el envío de emails de reset de contraseña:

```python
@staticmethod
def enviar_reset_password(usuario, token_obj, request=None):
    """
    Envía email con enlace de reset de contraseña
    """
    try:
        # Calcular tiempo de expiración en minutos
        tiempo_restante = token_obj.fecha_expiracion - timezone.now()
        minutos_expiracion = int(tiempo_restante.total_seconds() / 60)
        
        # Generar URL de reset
        if request:
            reset_url = request.build_absolute_uri(
                f"/auth/reset-contrasena/{token_obj.token}/"
            )
        else:
            # Fallback URL (configurable en settings)
            base_url = getattr(settings, 'SITE_URL', 'http://localhost:8000')
            reset_url = f"{base_url}/auth/reset-contrasena/{token_obj.token}/"
        
        # Contexto para el template
        context = {
            'usuario': usuario,
            'token': token_obj.token,
            'reset_url': reset_url,
            'minutos_expiracion': minutos_expiracion,
            'fecha_expiracion': token_obj.fecha_expiracion,
            'ip_address': token_obj.ip_address,
            'sitio_web': getattr(settings, 'SITE_NAME', 'Global Exchange'),
        }
        
        subject = '🔑 Restablecimiento de Contraseña - Global Exchange'
        template_name = 'auth/emails/reset_password.html'
        
        # Renderizar el contenido HTML
        html_content = render_to_string(template_name, context)
        
        # Contenido en texto plano como fallback
        text_content = f"""
{context['sitio_web']} - Restablecimiento de Contraseña

Hola {usuario.nombre},

Has solicitado restablecer tu contraseña. Haz clic en el siguiente enlace para crear una nueva contraseña:

{reset_url}

Este enlace expirará en {minutos_expiracion} minutos.

Si no solicitaste este restablecimiento, ignora este mensaje y tu contraseña permanecerá sin cambios.

Saludos,
Equipo de {context['sitio_web']}
        """.strip()
        
        # Crear el mensaje
        msg = EmailMultiAlternatives(
            subject=subject,
            body=text_content,
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[usuario.email],
        )
        
        # Adjuntar versión HTML
        msg.attach_alternative(html_content, "text/html")
        
        # Enviar email
        msg.send()
        
        logger.info(f"Email de reset de contraseña enviado exitosamente a {usuario.email}")
        return True, "Email enviado exitosamente"
        
    except Exception as e:
        logger.error(f"Error al enviar email de reset a {usuario.email}: {str(e)}")
        return False, f"Error al enviar email: {str(e)}"
```

Ahora voy a agregar las nuevas vistas para el reset de contraseña:

```python
def password_reset_request_view(request):
    """Vista para solicitar reset de contraseña"""
    from .forms import PasswordResetRequestForm
    from .models import PasswordResetToken
    
    if request.method == 'POST':
        form = PasswordResetRequestForm(request.POST)
        if form.is_valid():
            user = form.get_user()
            
            # Limpiar tokens expirados
            PasswordResetToken.limpiar_tokens_expirados()
            
            # Crear nuevo token
            token_obj = PasswordResetToken.crear_token(user, request)
            
            # Enviar email
            exito, mensaje = EmailService.enviar_reset_password(user, token_obj, request)
            
            if exito:
                messages.success(
                    request, 
                    'Se han enviado las instrucciones de restablecimiento a tu correo electrónico. '
                    'Revisa tu bandeja de entrada y sigue las instrucciones.'
                )
                return redirect('auth:login')
            else:
                messages.error(request, f'Error al enviar el email: {mensaje}')
    else:
        form = PasswordResetRequestForm()
    
    return render(request, 'auth/password_reset_request.html', {'form': form})


def password_reset_confirm_view(request, token):
    """Vista para confirmar reset de contraseña con token"""
    from .forms import PasswordResetForm
    from .models import PasswordResetToken
    
    try:
        token_obj = PasswordResetToken.objects.get(token=token)
        
        if not token_obj.es_valido():
            messages.error(
                request, 
                'El enlace de restablecimiento ha expirado o ya ha sido usado. '
                'Solicita uno nuevo.'
            )
            return redirect('auth:password_reset_request')
        
        if request.method == 'POST':
            form = PasswordResetForm(request.POST)
            if form.is_valid():
                # Cambiar la contraseña
                user = token_obj.usuario
                new_password = form.cleaned_data['password1']
                user.set_password(new_password)
                user.save()
                
                # Marcar token como usado
                token_obj.marcar_como_usado()
                
                messages.success(
                    request, 
                    '¡Tu contraseña ha sido restablecida exitosamente! '
                    'Ya puedes iniciar sesión con tu nueva contraseña.'
                )
                return redirect('auth:password_reset_complete')
        else:
            form = PasswordResetForm()
        
        context = {
            'form': form,
            'token': token,
            'user': token_obj.usuario
        }
        return render(request, 'auth/password_reset_confirm.html', context)
        
    except PasswordResetToken.DoesNotExist:
        messages.error(
            request, 
            'El enlace de restablecimiento no es válido. '
            'Verifica el enlace o solicita uno nuevo.'
        )
        return redirect('auth:password_reset_request')


def password_reset_complete_view(request):
    """Vista de confirmación de reset completado"""
    return render(request, 'auth/password_reset_complete.html')
```

Ahora voy a crear el template para confirmar el reset de contraseña:

```html
{% extends "base.html" %}

{% block title %}Nueva Contraseña - Global Exchange{% endblock %}

{% block content %}
<div class="container mt-5">
    <div class="row justify-content-center">
        <div class="col-md-6 col-lg-5">
            <div class="card shadow-soft">
                <div class="card-header bg-primary text-white">
                    <h4 class="mb-0 text-center">
                        <i class="fas fa-lock me-2"></i>Nueva Contraseña
                    </h4>
                </div>
                <div class="card-body p-4">
                    {% if form.errors %}
                        <div class="alert alert-danger" role="alert">
                            <i class="fas fa-exclamation-triangle me-2"></i>
                            {% for field in form %}
                                {% for error in field.errors %}
                                    {{ error }}
                                {% endfor %}
                            {% endfor %}
                            {% for error in form.non_field_errors %}
                                {{ error }}
                            {% endfor %}
                        </div>
                    {% endif %}
                    
                    {% if messages %}
                        {% for message in messages %}
                            <div class="alert alert-{% if message.tags == 'error' %}danger{% elif message.tags == 'success' %}success{% else %}{{ message.tags }}{% endif %}" role="alert">
                                <i class="fas fa-{% if message.tags == 'error' %}exclamation-triangle{% elif message.tags == 'success' %}check-circle{% else %}info-circle{% endif %} me-2"></i>
                                {{ message }}
                            </div>
                        {% endfor %}
                    {% endif %}
                    
                    <div class="alert alert-info border-0" role="alert" style="background: rgba(13,110,253,0.1);">
                        <i class="fas fa-shield-alt me-2 text-primary"></i>
                        <strong>Crear nueva contraseña</strong><br>
                        <span class="text-muted-sm">Por tu seguridad, elige una contraseña fuerte y única.</span>
                    </div>
                    
                    <form action="{% url 'auth:password_reset_confirm' token=token %}" method="post">
                        {% csrf_token %}
                        <div class="mb-3">
                            {{ form.password1.label_tag }}
                            {{ form.password1 }}
                            {% if form.password1.help_text %}
                                <div class="form-text text-muted-sm">{{ form.password1.help_text }}</div>
                            {% endif %}
                        </div>
                        
                        <div class="mb-4">
                            {{ form.password2.label_tag }}
                            {{ form.password2 }}
                            {% if form.password2.help_text %}
                                <div class="form-text text-muted-sm">{{ form.password2.help_text }}</div>
                            {% endif %}
                        </div>
                        
                        <button type="submit" class="btn btn-primary w-100 btn-lg btn-rounded">
                            <i class="fas fa-save me-2"></i>Cambiar Contraseña
                        </button>
                    </form>
                    
                    <hr class="my-4">
                    <div class="text-center">
                        <p class="mb-0">
                            <a href="{% url 'auth:login' %}" class="text-muted small text-decoration-none">
                                <i class="fas fa-arrow-left me-1"></i>Volver al login
                            </a>
                        </p>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}
```

Ahora voy a crear el template de confirmación de reset completado:

```html
{% extends "base.html" %}

{% block title %}Contraseña Actualizada - Global Exchange{% endblock %}

{% block content %}
<div class="container mt-5">
    <div class="row justify-content-center">
        <div class="col-md-6 col-lg-5">
            <div class="card shadow-soft">
                <div class="card-header bg-primary text-white">
                    <h4 class="mb-0 text-center">
                        <i class="fas fa-check-circle me-2"></i>Contraseña Actualizada
                    </h4>
                </div>
                <div class="card-body p-4 text-center">
                    <div class="mb-4">
                        <div class="d-inline-flex align-items-center justify-content-center bg-success text-white rounded-circle" style="width: 80px; height: 80px; font-size: 2rem;">
                            <i class="fas fa-check"></i>
                        </div>
                    </div>
                    
                    <h5 class="mb-3 text-primary fw-bold">¡Contraseña actualizada exitosamente!</h5>
                    
                    <div class="alert alert-success border-0" role="alert" style="background: rgba(25,135,84,0.1);">
                        <i class="fas fa-shield-check me-2 text-success"></i>
                        <span class="text-muted-sm">Tu contraseña ha sido cambiada de forma segura. Ya puedes iniciar sesión con tu nueva contraseña.</span>
                    </div>
                    
                    <div class="d-grid gap-2">
                        <a href="{% url 'auth:login' %}" class="btn btn-primary btn-lg btn-rounded">
                            <i class="fas fa-sign-in-alt me-2"></i>Iniciar Sesión
                        </a>
                        
                        <a href="{% url 'welcome' %}" class="btn btn-outline-secondary btn-rounded">
                            <i class="fas fa-home me-2"></i>Ir al Inicio
                        </a>
                    </div>
                    
                    <hr class="my-4">
                    <div class="text-center">
                        <small class="text-muted">
                            <i class="fas fa-info-circle me-1"></i>
                            Si no solicitaste este cambio, contacta inmediatamente al soporte técnico.
                        </small>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}
```

Ahora voy a crear el template de email para el reset de contraseña:

```html
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Restablecimiento de Contraseña - {{ sitio_web }}</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 600px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f4f4f4;
        }
        .container {
            background-color: #ffffff;
            border-radius: 10px;
            padding: 30px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        }
        .header {
            text-align: center;
            background: linear-gradient(135deg, #ffc107, #ff9800);
            color: white;
            padding: 20px;
            border-radius: 10px 10px 0 0;
            margin: -30px -30px 30px -30px;
        }
        .header h1 {
            margin: 0;
            font-size: 24px;
        }
        .reset-button {
            display: inline-block;
            background: linear-gradient(135deg, #28a745, #20c997);
            color: white;
            text-decoration: none;
            padding: 15px 30px;
            border-radius: 50px;
            font-weight: bold;
            font-size: 16px;
            margin: 20px 0;
            text-align: center;
            transition: all 0.3s ease;
        }
        .reset-button:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2);
        }
        .info-box {
            background-color: #e3f2fd;
            border-left: 4px solid #2196f3;
            padding: 15px;
            margin: 20px 0;
            border-radius: 5px;
        }
        .warning-box {
            background-color: #fff3e0;
            border-left: 4px solid #ff9800;
            padding: 15px;
            margin: 20px 0;
            border-radius: 5px;
        }
        .footer {
            text-align: center;
            margin-top: 30px;
            padding-top: 20px;
            border-top: 1px solid #eee;
            color: #666;
            font-size: 14px;
        }
        .button-container {
            text-align: center;
            margin: 30px 0;
        }
        .details {
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 5px;
            margin: 20px 0;
            font-size: 14px;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1> Restablecimiento de Contraseña</h1>
            <p style="margin: 10px 0 0 0;">{{ sitio_web }}</p>
        </div>

        <h2>Hola {{ usuario.nombre }},</h2>
        
        <p>Has solicitado restablecer la contraseña de tu cuenta en <strong>{{ sitio_web }}</strong>.</p>
        
        <div class="info-box">
            <strong>📧 Cuenta:</strong> {{ usuario.email }}<br>
            <strong>⏰ Solicitud:</strong> {{ token.fecha_creacion|date:"d/m/Y H:i" }}<br>
            <strong>🕒 Expira:</strong> {{ fecha_expiracion|date:"d/m/Y H:i" }} ({{ minutos_expiracion }} minutos)
        </div>

        <p>Para crear una nueva contraseña, haz clic en el siguiente botón:</p>
        
        <div class="button-container">
            <a href="{{ reset_url }}" class="reset-button">
                🔐 Restablecer mi Contraseña
            </a>
        </div>

        <p><strong>O copia y pega este enlace en tu navegador:</strong></p>
        <div class="details">
            <a href="{{ reset_url }}" style="word-break: break-all;">{{ reset_url }}</a>
        </div>

        <div class="warning-box">
            <strong>⚠️ Importante:</strong>
            <ul style="margin: 10px 0;">
                <li>Este enlace es válido por <strong>{{ minutos_expiracion }} minutos</strong></li>
                <li>Solo puede ser usado una vez</li>
                <li>Si no solicitaste este restablecimiento, ignora este mensaje</li>
                <li>Tu contraseña actual permanecerá sin cambios hasta que uses este enlace</li>
            </ul>
        </div>

        {% if ip_address %}
        <div class="details">
            <strong>🌐 Información de seguridad:</strong><br>
            Solicitud realizada desde la IP: {{ ip_address }}
        </div>
        {% endif %}

        <div class="footer">
            <p>
                <strong>{{ sitio_web }}</strong><br>
                Este es un mensaje automático, no respondas a este correo.
            </p>
            <p>
                Si tienes problemas con el enlace, contacta al soporte técnico.
            </p>
        </div>
    </div>
</body>
</html>
```