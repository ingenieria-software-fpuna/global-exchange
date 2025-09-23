# Agregar tarjeta para límites de transacciones
_Exported on 9/23/2025 at 14:49:09 GMT-3 from Cursor (1.5.5)_

---

**User**

En el dashboard principal agregar una nueva tarjeta para poder configurar límites para transacciones tanto por dia como por mes. NO quiero un CRUD, quiero que solo hayan dos campos. En uno de ellos debe ir el límite diario y en otro el límite por mes.

---

**Cursor**

Revisando la estructura del dashboard y los modelos para ubicar dónde agregar la tarjeta de límites de transacciones.


Buscando modelos de configuración o límites de transacciones.


La app `configuracion` existe pero no tiene archivos Python. Creando la estructura necesaria para la tarjeta de límites de transacciones.


Creando los archivos necesarios para la app `configuracion`.


```python
from django.apps import AppConfig


class ConfiguracionConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'configuracion'
    verbose_name = 'Configuración del Sistema'
```

```python
from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone


class ConfiguracionSistema(models.Model):
    """
    Modelo para configuraciones globales del sistema.
    """
    limite_diario_transacciones = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name="Límite Diario de Transacciones",
        help_text="Monto máximo permitido para transacciones por día. 0 = sin límite."
    )
    limite_mensual_transacciones = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        validators=[MinValueValidator(0)],
        verbose_name="Límite Mensual de Transacciones",
        help_text="Monto máximo permitido para transacciones por mes. 0 = sin límite."
    )
    fecha_creacion = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Fecha de creación"
    )
    fecha_actualizacion = models.DateTimeField(
        auto_now=True,
        verbose_name="Fecha de actualización"
    )

    class Meta:
        verbose_name = "Configuración del Sistema"
        verbose_name_plural = "Configuraciones del Sistema"
        db_table = 'configuracion_sistema'

    def __str__(self):
        return f"Configuración del Sistema - {self.fecha_actualizacion.strftime('%d/%m/%Y %H:%M')}"

    def save(self, *args, **kwargs):
        # Asegurar que solo exista una instancia de configuración
        if not self.pk and ConfiguracionSistema.objects.exists():
            # Si ya existe una configuración, actualizar la existente
            existing = ConfiguracionSistema.objects.first()
            existing.limite_diario_transacciones = self.limite_diario_transacciones
            existing.limite_mensual_transacciones = self.limite_mensual_transacciones
            existing.save()
            return existing
        super().save(*args, **kwargs)

    @classmethod
    def get_configuracion(cls):
        """
        Obtiene la configuración del sistema, creando una instancia por defecto si no existe.
        """
        config, created = cls.objects.get_or_create(
            defaults={
                'limite_diario_transacciones': 0,
                'limite_mensual_transacciones': 0,
            }
        )
        return config
```

```python
from django import forms
from django.core.validators import MinValueValidator
from .models import ConfiguracionSistema


class ConfiguracionSistemaForm(forms.ModelForm):
    """
    Formulario para configurar los límites de transacciones del sistema.
    """
    limite_diario_transacciones = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'min': '0',
            'placeholder': '0.00'
        }),
        label="Límite Diario de Transacciones",
        help_text="Monto máximo permitido para transacciones por día. 0 = sin límite."
    )
    
    limite_mensual_transacciones = forms.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=0,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'step': '0.01',
            'min': '0',
            'placeholder': '0.00'
        }),
        label="Límite Mensual de Transacciones",
        help_text="Monto máximo permitido para transacciones por mes. 0 = sin límite."
    )

    class Meta:
        model = ConfiguracionSistema
        fields = ['limite_diario_transacciones', 'limite_mensual_transacciones']

    def clean(self):
        cleaned_data = super().clean()
        limite_diario = cleaned_data.get('limite_diario_transacciones')
        limite_mensual = cleaned_data.get('limite_mensual_transacciones')

        # Validar que el límite mensual sea mayor o igual al límite diario
        if limite_diario and limite_mensual and limite_mensual < limite_diario:
            raise forms.ValidationError(
                "El límite mensual debe ser mayor o igual al límite diario."
            )

        return cleaned_data
```

```python
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth.decorators import permission_required
from .models import ConfiguracionSistema
from .forms import ConfiguracionSistemaForm


@login_required
@permission_required('configuracion.change_configuracionsistema', raise_exception=True)
def configuracion_view(request):
    """
    Vista para mostrar y actualizar la configuración del sistema.
    """
    configuracion = ConfiguracionSistema.get_configuracion()
    
    if request.method == 'POST':
        form = ConfiguracionSistemaForm(request.POST, instance=configuracion)
        if form.is_valid():
            form.save()
            messages.success(
                request, 
                'Configuración actualizada correctamente.'
            )
            return redirect('configuracion:configuracion')
    else:
        form = ConfiguracionSistemaForm(instance=configuracion)
    
    context = {
        'form': form,
        'configuracion': configuracion,
        'titulo': 'Configuración del Sistema',
    }
    
    return render(request, 'configuracion/configuracion.html', context)
```

```python
from django.urls import path
from . import views

app_name = 'configuracion'

urlpatterns = [
    path('', views.configuracion_view, name='configuracion'),
]
```

```python
from django.contrib import admin
from .models import ConfiguracionSistema


@admin.register(ConfiguracionSistema)
class ConfiguracionSistemaAdmin(admin.ModelAdmin):
    """
    Administración para la configuración del sistema.
    """
    list_display = [
        'limite_diario_transacciones',
        'limite_mensual_transacciones',
        'fecha_actualizacion'
    ]
    list_filter = ['fecha_creacion', 'fecha_actualizacion']
    readonly_fields = ['fecha_creacion', 'fecha_actualizacion']
    
    fieldsets = (
        ('Límites de Transacciones', {
            'fields': (
                'limite_diario_transacciones',
                'limite_mensual_transacciones',
            )
        }),
        ('Información del Sistema', {
            'fields': (
                'fecha_creacion',
                'fecha_actualizacion',
            ),
            'classes': ('collapse',)
        }),
    )
    
    def has_add_permission(self, request):
        # Solo permitir una instancia de configuración
        return not ConfiguracionSistema.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        # No permitir eliminar la configuración
        return False
```

```python
from django.test import TestCase
from django.core.exceptions import ValidationError
from .models import ConfiguracionSistema


class ConfiguracionSistemaModelTest(TestCase):
    """
    Pruebas para el modelo ConfiguracionSistema.
    """
    
    def test_crear_configuracion_por_defecto(self):
        """Test que se puede crear una configuración con valores por defecto."""
        config = ConfiguracionSistema.objects.create()
        self.assertEqual(config.limite_diario_transacciones, 0)
        self.assertEqual(config.limite_mensual_transacciones, 0)
    
    def test_get_configuracion_crea_instancia_si_no_existe(self):
        """Test que get_configuracion crea una instancia si no existe."""
        self.assertEqual(ConfiguracionSistema.objects.count(), 0)
        config = ConfiguracionSistema.get_configuracion()
        self.assertEqual(ConfiguracionSistema.objects.count(), 1)
        self.assertIsInstance(config, ConfiguracionSistema)
    
    def test_get_configuracion_retorna_existente(self):
        """Test que get_configuracion retorna la instancia existente."""
        config_original = ConfiguracionSistema.objects.create(
            limite_diario_transacciones=1000,
            limite_mensual_transacciones=30000
        )
        config_obtenida = ConfiguracionSistema.get_configuracion()
        self.assertEqual(config_obtenida.id, config_original.id)
        self.assertEqual(ConfiguracionSistema.objects.count(), 1)
    
    def test_save_actualiza_existente_si_no_tiene_pk(self):
        """Test que save actualiza la instancia existente si no tiene pk."""
        config_existente = ConfiguracionSistema.objects.create(
            limite_diario_transacciones=1000,
            limite_mensual_transacciones=30000
        )
        
        nueva_config = ConfiguracionSistema(
            limite_diario_transacciones=2000,
            limite_mensual_transacciones=60000
        )
        resultado = nueva_config.save()
        
        # Verificar que se actualizó la configuración existente
        config_existente.refresh_from_db()
        self.assertEqual(config_existente.limite_diario_transacciones, 2000)
        self.assertEqual(config_existente.limite_mensual_transacciones, 60000)
        self.assertEqual(ConfiguracionSistema.objects.count(), 1)
```

```django-html
{% extends "base.html" %}

{% block title %}Configuración del Sistema - Global Exchange{% endblock %}

{% block content %}
<div class="container mt-4">
    <div class="row">
        <div class="col-12">
            <div class="d-flex justify-content-between align-items-center mb-4">
                <h1 class="h3 mb-0">
                    <i class="fas fa-cog me-2 text-primary"></i>
                    Configuración del Sistema
                </h1>
                <a href="{% url 'auth:dashboard' %}" class="btn btn-outline-secondary">
                    <i class="fas fa-arrow-left me-1"></i>
                    Volver al Dashboard
                </a>
            </div>
        </div>
    </div>

    <div class="row justify-content-center">
        <div class="col-lg-8">
            <div class="card shadow-sm">
                <div class="card-header bg-primary text-white">
                    <h5 class="card-title mb-0">
                        <i class="fas fa-shield-alt me-2"></i>
                        Límites de Transacciones
                    </h5>
                </div>
                <div class="card-body">
                    <form method="post">
                        {% csrf_token %}
                        
                        {% if form.non_field_errors %}
                            <div class="alert alert-danger">
                                {{ form.non_field_errors }}
                            </div>
                        {% endif %}

                        <div class="row">
                            <div class="col-md-6 mb-3">
                                <label for="{{ form.limite_diario_transacciones.id_for_label }}" class="form-label">
                                    {{ form.limite_diario_transacciones.label }}
                                </label>
                                {{ form.limite_diario_transacciones }}
                                {% if form.limite_diario_transacciones.help_text %}
                                    <div class="form-text">{{ form.limite_diario_transacciones.help_text }}</div>
                                {% endif %}
                                {% if form.limite_diario_transacciones.errors %}
                                    <div class="text-danger small mt-1">
                                        {{ form.limite_diario_transacciones.errors }}
                                    </div>
                                {% endif %}
                            </div>

                            <div class="col-md-6 mb-3">
                                <label for="{{ form.limite_mensual_transacciones.id_for_label }}" class="form-label">
                                    {{ form.limite_mensual_transacciones.label }}
                                </label>
                                {{ form.limite_mensual_transacciones }}
                                {% if form.limite_mensual_transacciones.help_text %}
                                    <div class="form-text">{{ form.limite_mensual_transacciones.help_text }}</div>
                                {% endif %}
                                {% if form.limite_mensual_transacciones.errors %}
                                    <div class="text-danger small mt-1">
                                        {{ form.limite_mensual_transacciones.errors }}
                                    </div>
                                {% endif %}
                            </div>
                        </div>

                        <div class="alert alert-info">
                            <i class="fas fa-info-circle me-2"></i>
                            <strong>Nota:</strong> Establecer el valor en 0 significa que no hay límite para ese período.
                        </div>

                        <div class="d-flex justify-content-end gap-2">
                            <a href="{% url 'auth:dashboard' %}" class="btn btn-secondary">
                                <i class="fas fa-times me-1"></i>
                                Cancelar
                            </a>
                            <button type="submit" class="btn btn-primary">
                                <i class="fas fa-save me-1"></i>
                                Guardar Configuración
                            </button>
                        </div>
                    </form>
                </div>
            </div>

            {% if configuracion %}
            <div class="card mt-4">
                <div class="card-header bg-light">
                    <h6 class="card-title mb-0">
                        <i class="fas fa-history me-2"></i>
                        Información de la Configuración
                    </h6>
                </div>
                <div class="card-body">
                    <div class="row">
                        <div class="col-md-6">
                            <small class="text-muted">Última actualización:</small>
                            <p class="mb-0">{{ configuracion.fecha_actualizacion|date:"d/m/Y H:i" }}</p>
                        </div>
                        <div class="col-md-6">
                            <small class="text-muted">Fecha de creación:</small>
                            <p class="mb-0">{{ configuracion.fecha_creacion|date:"d/m/Y H:i" }}</p>
                        </div>
                    </div>
                </div>
            </div>
            {% endif %}
        </div>
    </div>
</div>
{% endblock %}
```

Registrando la app en `settings.py` y agregando las URLs.


```python
"""
Django settings for global_exchange project.

Generated by 'django-admin startproject' using Django 5.2.5.

For more information on this file, see
https://docs.djangoproject.com/en/5.2/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/5.2/ref/settings/
"""

from pathlib import Path
import os

# Cargar variables desde un archivo .env si está disponible (opcional)
try:
    from dotenv import load_dotenv  # type: ignore
    load_dotenv(Path(__file__).resolve().parent.parent / ".env")
except Exception:
    pass

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.2/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-i9)_lkfc()cl)0gwqn82ps*sfgiiga*n&m^sh42x@*l@7bd#p@'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get("DEBUG", "true").lower() in {"1", "true", "yes", "on"}

# Allow configuring hosts from environment. In debug, default to allow all.
_allowed_hosts_env = os.environ.get("ALLOWED_HOSTS", "*" if DEBUG else "")
ALLOWED_HOSTS = [h.strip() for h in _allowed_hosts_env.split(",") if h.strip()]

# Optional: CSRF trusted origins from env (scheme://host[:port])
_csrf_env = os.environ.get("CSRF_TRUSTED_ORIGINS", "")
if _csrf_env:
    CSRF_TRUSTED_ORIGINS = [o.strip() for o in _csrf_env.split(",") if o.strip()]


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Apps del proyecto
    'grupos', 'usuarios', 'auth.apps.AuthConfig', 'clientes', 'monedas', 'tasa_cambio', 'metodo_pago', 'metodo_cobro', 'configuracion',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'auth.middleware.UsuarioActivoMiddleware',  # Verificar usuario activo
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'global_exchange.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'grupos.context_processors.permissions_context',
            ],
        },
    },
]

WSGI_APPLICATION = 'global_exchange.wsgi.application'


# Database
# https://docs.djangoproject.com/en/5.2/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.environ.get("DB_NAME", "glx_db"),
        "USER": os.environ.get("DB_USER", "admin"),
        "PASSWORD": os.environ.get("DB_PASSWORD", "1234"),
        "HOST": os.environ.get("DB_HOST", "localhost"),
        "PORT": os.environ.get("DB_PORT", "5432"),
    }
}


# Password validation
# https://docs.djangoproject.com/en/5.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.2/topics/i18n/

LANGUAGE_CODE = 'es'

TIME_ZONE = 'America/Asuncion'  # Zona horaria de Paraguay

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.2/howto/static-files/

STATIC_URL = 'static/'

# Additional static files directories
STATICFILES_DIRS = [
    BASE_DIR / "docs" / "_build" / "html",  # Sphinx documentation
]

# Default primary key field type
# https://docs.djangoproject.com/en/5.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
AUTH_USER_MODEL = 'usuarios.Usuario'

# Backends de autenticación personalizados
AUTHENTICATION_BACKENDS = [
    'grupos.backends.GrupoActivoBackend',  # Backend personalizado para grupos activos
    # Por alguna razón si no comento esta linea django toma su backend como el default y no funcionan permisos de grupos activos
    #'django.contrib.auth.backends.ModelBackend',  # Backend por defecto como fallback
]

# Configuración de Correo Electrónico
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '587'))
EMAIL_USE_TLS = os.environ.get('EMAIL_USE_TLS', 'true').lower() == 'true'
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', 'ejemplo@fpuna.edu.py')
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', '')
DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL', EMAIL_HOST_USER)

# Configuración del sitio
SITE_NAME = os.environ.get('SITE_NAME', 'Global Exchange')

# Configuración de logging
# Asegurar que el directorio de logs existe
LOG_DIR = BASE_DIR / 'logs'
LOG_DIR.mkdir(exist_ok=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': LOG_DIR / 'auth.log',
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'loggers': {
        'auth.services': {
            'handlers': ['file', 'console'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

```

Agregando las URLs de la app `configuracion` en `global_exchange/urls.py`.


```python
"""
URL configuration for global_exchange project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.views.generic.base import RedirectView
from django.shortcuts import render
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve
from django.http import Http404
import os

def welcome_view(request):
    """Vista para la pantalla de bienvenida con cotizaciones"""
    from monedas.models import Moneda
    from tasa_cambio.models import TasaCambio
    
    # Obtener monedas activas con sus cotizaciones activas
    monedas_con_tasas = []
    monedas_activas = Moneda.objects.filter(es_activa=True).order_by('nombre')
    
    for moneda in monedas_activas:
        tasa_activa = TasaCambio.objects.filter(
            moneda=moneda,
            es_activa=True
        ).first()
        
        if tasa_activa:
            monedas_con_tasas.append({
                'moneda': moneda,
                'tasa': tasa_activa
            })
    
    context = {
        'monedas_con_tasas': monedas_con_tasas,
        'monedas': monedas_activas,
    }
    
    return render(request, 'welcome.html', context)

def docs_view(request, path=''):
    """Vista para servir la documentación Sphinx"""
    docs_root = os.path.join(settings.BASE_DIR, 'docs', '_build', 'html')
    
    # Si no se especifica path o es vacío, servir index.html
    if not path or path == '':
        path = 'index.html'
    # Si es un directorio, agregar index.html
    elif path.endswith('/'):
        path = path + 'index.html'
    
    file_path = os.path.join(docs_root, path)
    
    # Verificar que el archivo existe y está dentro del directorio de docs
    if not os.path.exists(file_path) or os.path.commonpath([docs_root, file_path]) != docs_root:
        raise Http404("Página de documentación no encontrada")
    
    return serve(request, path, document_root=docs_root)

urlpatterns = [
    path('', welcome_view, name='welcome'),
    path('admin/', admin.site.urls),
    path('auth/', include('auth.urls', namespace='auth')),
    path('usuarios/', include('usuarios.urls', namespace='usuarios')),
    path('grupos/', include('grupos.urls', namespace='grupos')),
    path('clientes/', include('clientes.urls', namespace='clientes')),
    path('monedas/', include('monedas.urls', namespace='monedas')),
    path('tasa-cambio/', include('tasa_cambio.urls', namespace='tasa_cambio')),
    path('metodos-pago/', include('metodo_pago.urls', namespace='metodo_pago')),
    path('metodos-cobro/', include('metodo_cobro.urls', namespace='metodo_cobro')),
    path('configuracion/', include('configuracion.urls', namespace='configuracion')),
    path('docs/', docs_view, name='docs_index'),
    path('docs/<path:path>', docs_view, name='docs'),
]

```

Agregando la tarjeta de configuración al dashboard principal.


```django-html
{% extends "base.html" %}

{% block title %}Dashboard - Global Exchange{% endblock %}

{% block content %}
<div class="container mt-5">
    <div class="row">
        <div class="col text-center">
            <h1 class="display-4">¡Bienvenido, {{ user.nombre|default:user.email }}!</h1>
            <p class="lead">Dashboard de administración para Global Exchange.</p>
        </div>
    </div>
    <hr>
    <div class="row row-cols-1 row-cols-md-2 row-cols-lg-4 g-4 text-center">
        <!-- Simulador de cambio (acceso público) -->
        <div class="col">
            <div class="card h-100 shadow-sm">
                <div class="card-body">
                    <i class="fas fa-calculator fa-3x text-secondary mb-3"></i>
                    <h5 class="card-title">Simulador de Cambio</h5>
                    <p class="card-text">Calcula cuánto recibes al cambiar entre monedas.</p>
                </div>
                <div class="card-footer bg-light">
                    <a href="{% url 'tasa_cambio:dashboard' %}" class="btn btn-outline-secondary w-100">
                        Abrir Simulador
                    </a>
                </div>
            </div>
        </div>
        {% if can_view_usuarios %}
        <div class="col">
            <div class="card h-100 shadow-sm">
                <div class="card-body">
                    <i class="fas fa-users fa-3x text-primary mb-3"></i>
                    <h5 class="card-title">Usuarios</h5>
                    <p class="card-text">Administra los usuarios del sistema. Crea, edita y elimina perfiles.</p>
                </div>
                <div class="card-footer bg-light">
                    <a href="{% url 'usuarios:user_list' %}"  class="btn btn-primary w-100">
                        Ir a Usuarios
                    </a>
                </div>
            </div>
        </div>
        {% endif %}
        {% if can_view_groups %}
        <div class="col">
            <div class="card h-100 shadow-sm">
                <div class="card-body">
                    <i class="fas fa-layer-group fa-3x text-info mb-3"></i>
                    <h5 class="card-title">Grupos</h5>
                    <p class="card-text">Gestiona los grupos y permisos para controlar el acceso a la aplicación.</p>
                </div>
                <div class="card-footer bg-light">
                    <a href="{% url 'grupos:group_list' %}" class="btn btn-info w-100 text-white">
                        Ir a Grupos
                    </a>
                </div>
            </div>
        </div>
        {% endif %}
        {% if can_view_tipocliente %}
        <div class="col">
            <div class="card h-100 shadow-sm">
                <div class="card-body">
                    <i class="fas fa-tags fa-3x text-warning mb-3"></i>
                    <h5 class="card-title">Tipos de Cliente</h5>
                    <p class="card-text">Gestiona los tipos de clientes del sistema.</p>
                </div>
                <div class="card-footer bg-light">
                    <a href="{% url 'clientes:tipocliente_list' %}" class="btn btn-warning w-100 text-dark">
                        Ir a Tipos de Cliente
                    </a>
                </div>
            </div>
        </div>
        {% endif %}
        {% if can_view_cliente %}
        <div class="col">
            <div class="card h-100 shadow-sm">
                <div class="card-body">
                    <i class="fas fa-user-tie fa-3x text-success mb-3"></i>
                    <h5 class="card-title">Clientes</h5>
                    <p class="card-text">Administra la información de tus clientes y su segmentación.</p>
                </div>
                <div class="card-footer bg-light">
                    <a href="{% url 'clientes:cliente_list' %}" class="btn btn-success w-100">
                        Ir a Clientes
                    </a>
                </div>
            </div>
        </div>
        {% endif %}
        {% if can_view_monedas %}
        <div class="col">
            <div class="card h-100 shadow-sm">
                <div class="card-body">
                    <i class="fas fa-coins fa-3x text-success mb-3"></i>
                    <h5 class="card-title">Monedas</h5>
                    <p class="card-text">Gestiona las monedas del sistema para las operaciones de cambio.</p>
                </div>
                <div class="card-footer bg-light">
                    <a href="{% url 'monedas:moneda_list' %}" class="btn btn-success w-100 text-white">
                        Ir a Monedas
                    </a>
                </div>
            </div>
        </div>
        {% endif %}
        {% if can_view_tasacambio %}
        <div class="col">
            <div class="card h-100 shadow-sm">
                <div class="card-body">
                    <i class="fas fa-chart-line fa-3x text-primary mb-3"></i>
                    <h5 class="card-title">Cotizaciones</h5>
                    <p class="card-text">Administra las cotizaciones para todas las monedas.</p>
                </div>
                <div class="card-footer bg-light">
                    <a href="{% url 'tasa_cambio:tasacambio_list' %}" class="btn btn-primary w-100">
                        Ir a Cotizaciones
                    </a>
                </div>
            </div>
        </div>
        {% endif %}
        {% if can_view_metodopago %}
        <div class="col">
            <div class="card h-100 shadow-sm">
                <div class="card-body">
                    <i class="fas fa-credit-card fa-3x text-secondary mb-3"></i>
                    <h5 class="card-title">Métodos de Pago</h5>
                    <p class="card-text">Configura métodos de pago y sus comisiones.</p>
                </div>
                <div class="card-footer bg-light">
                    <a href="{% url 'metodo_pago:metodopago_list' %}" class="btn btn-secondary w-100">
                        Ir a Métodos de Pago
                    </a>
                </div>
            </div>
        </div>
        {% endif %}
        {% if can_view_metodocobro %}
        <div class="col">
            <div class="card h-100 shadow-sm">
                <div class="card-body">
                    <i class="fas fa-money-bill-wave fa-3x text-danger mb-3"></i>
                    <h5 class="card-title">Métodos de Cobro</h5>
                    <p class="card-text">Configura métodos de cobro y sus restricciones de moneda.</p>
                </div>
                <div class="card-footer bg-light">
                    <a href="{% url 'metodo_cobro:metodocobro_list' %}" class="btn btn-danger w-100">
                        Ir a Métodos de Cobro
                    </a>
                </div>
            </div>
        </div>
        {% endif %}
        {% if can_view_configuracion %}
        <div class="col">
            <div class="card h-100 shadow-sm">
                <div class="card-body">
                    <i class="fas fa-cog fa-3x text-dark mb-3"></i>
                    <h5 class="card-title">Configuración</h5>
                    <p class="card-text">Configura los límites de transacciones diarias y mensuales del sistema.</p>
                </div>
                <div class="card-footer bg-light">
                    <a href="{% url 'configuracion:configuracion' %}" class="btn btn-dark w-100">
                        Ir a Configuración
                    </a>
                </div>
            </div>
        </div>
        {% endif %}
    </div>
</div>
{% endblock %}

```

Revisando el context processor de permisos para agregar `can_view_configuracion`.


```python
from django.contrib.auth.models import Permission, Group

def permissions_context(request):
    """
    Context processor que proporciona información de permisos usando Django estándar.
    Reemplaza el sistema personalizado de roles.
    """
    context = {}
    
    if request.user.is_authenticated:
        # Información del usuario
        context['current_user'] = request.user
        
        # Verificar si es administrador del sistema
        admin_group = Group.objects.filter(name='Admin').first()
        context['is_admin'] = admin_group and request.user in admin_group.user_set.all()
        
        # Grupos del usuario (Django estándar)
        context['user_groups'] = request.user.groups.all()
        context['user_group_names'] = [g.name for g in request.user.groups.all()]
        
        # Permisos del usuario (Django estándar)
        if context['is_admin']:
            # Usuario del grupo Admin tiene todos los permisos
            context['user_permissions'] = Permission.objects.all()
            context['user_permission_codes'] = [p.codename for p in Permission.objects.all()]
        else:
            # Obtener permisos del usuario y sus grupos
            user_permissions = request.user.user_permissions.all()
            group_permissions = Permission.objects.filter(group__user=request.user)
            all_permissions = (user_permissions | group_permissions).distinct()
            
            context['user_permissions'] = all_permissions
            context['user_permission_codes'] = [p.codename for p in all_permissions]
        
        # Verificaciones comunes usando permisos de Django
        context['can_manage_users'] = (
            context['is_admin'] or 
            request.user.is_staff or
            request.user.has_perm('usuarios.add_usuario') or
            request.user.has_perm('usuarios.change_usuario') or
            request.user.has_perm('usuarios.delete_usuario')
        )
        
        context['can_manage_groups'] = (
            context['is_admin'] or 
            request.user.is_staff or
            request.user.has_perm('auth.add_group') or
            request.user.has_perm('auth.change_group') or
            request.user.has_perm('auth.delete_group')
        )
        
        context['can_manage_permissions'] = (
            context['is_admin'] or 
            request.user.is_staff or
            request.user.has_perm('auth.change_permission')
        )
        
        context['can_view_admin_dashboard'] = (
            context['is_admin'] or 
            request.user.is_staff or
            context['can_manage_users'] or
            context['can_manage_groups'] or
            context['can_manage_permissions']
        )
        
        # Permisos específicos para clientes
        context['can_view_cliente'] = request.user.has_perm('clientes.view_cliente')
        context['can_create_cliente'] = request.user.has_perm('clientes.add_cliente')
        context['can_edit_cliente'] = request.user.has_perm('clientes.change_cliente')
        context['can_delete_cliente'] = request.user.has_perm('clientes.delete_cliente')
        
        context['can_view_tipocliente'] = request.user.has_perm('clientes.view_tipocliente')
        context['can_create_tipocliente'] = request.user.has_perm('clientes.add_tipocliente')
        context['can_edit_tipocliente'] = request.user.has_perm('clientes.change_tipocliente')
        context['can_delete_tipocliente'] = request.user.has_perm('clientes.delete_tipocliente')
        
        # Permisos para usuarios
        context['can_view_usuarios'] = request.user.has_perm('usuarios.view_usuario')
        context['can_create_usuarios'] = request.user.has_perm('usuarios.add_usuario')
        context['can_edit_usuarios'] = request.user.has_perm('usuarios.change_usuario')
        context['can_delete_usuarios'] = request.user.has_perm('usuarios.delete_usuario')
        
        # Permisos para grupos
        context['can_view_groups'] = request.user.has_perm('auth.view_group')
        context['can_create_groups'] = request.user.has_perm('auth.add_group')
        context['can_edit_groups'] = request.user.has_perm('auth.change_group')
        context['can_delete_groups'] = request.user.has_perm('auth.delete_group')
        
        # Permisos específicos para monedas
        context['can_view_monedas'] = request.user.has_perm('monedas.view_moneda')
        context['can_create_monedas'] = request.user.has_perm('monedas.add_moneda')
        context['can_edit_monedas'] = request.user.has_perm('monedas.change_moneda')
        
        # Permisos específicos para tasas de cambio
        context['can_view_tasacambio'] = request.user.has_perm('tasa_cambio.view_tasacambio')
        context['can_create_tasacambio'] = request.user.has_perm('tasa_cambio.add_tasacambio')
        context['can_edit_tasacambio'] = request.user.has_perm('tasa_cambio.change_tasacambio')
        
        # Permisos específicos para métodos de pago
        context['can_view_metodopago'] = request.user.has_perm('metodo_pago.view_metodopago')
        context['can_create_metodopago'] = request.user.has_perm('metodo_pago.add_metodopago')
        context['can_edit_metodopago'] = request.user.has_perm('metodo_pago.change_metodopago')
        
        # Permisos específicos para métodos de cobro
        context['can_view_metodocobro'] = request.user.has_perm('metodo_cobro.view_metodocobro')
        context['can_create_metodocobro'] = request.user.has_perm('metodo_cobro.add_metodocobro')
        context['can_edit_metodocobro'] = request.user.has_perm('metodo_cobro.change_metodocobro')
        
        # Permisos específicos para configuración
        context['can_view_configuracion'] = request.user.has_perm('configuracion.change_configuracionsistema')
        
        # Dashboard
        context['can_view_dashboard'] = (
            context['is_admin'] or 
            request.user.is_staff or
            context['can_view_usuarios'] or
            context['can_view_groups'] or
            context['can_view_cliente'] or
            context['can_view_monedas'] or
            context['can_view_tasacambio'] or
            context['can_view_metodopago'] or
            context['can_view_metodocobro']
        )
        
    else:
        # Usuario no autenticado
        context['current_user'] = None
        context['is_admin'] = False
        context['user_groups'] = []
        context['user_group_names'] = []
        context['user_permissions'] = []
        context['user_permission_codes'] = []
        context['can_manage_users'] = False
        context['can_manage_groups'] = False
        context['can_manage_permissions'] = False
        context['can_view_admin_dashboard'] = False
        context['can_view_cliente'] = False
        context['can_create_cliente'] = False
        context['can_edit_cliente'] = False
        context['can_delete_cliente'] = False
        context['can_view_tipocliente'] = False
        context['can_create_tipocliente'] = False
        context['can_edit_tipocliente'] = False
        context['can_delete_tipocliente'] = False
        context['can_view_usuarios'] = False
        context['can_create_usuarios'] = False
        context['can_edit_usuarios'] = False
        context['can_delete_usuarios'] = False
        context['can_view_groups'] = False
        context['can_create_groups'] = False
        context['can_edit_groups'] = False
        context['can_delete_groups'] = False
        context['can_view_monedas'] = False
        context['can_create_monedas'] = False
        context['can_edit_monedas'] = False
        context['can_view_tasacambio'] = False
        context['can_create_tasacambio'] = False
        context['can_edit_tasacambio'] = False
        context['can_view_dashboard'] = False
        context['can_view_metodopago'] = False
        context['can_create_metodopago'] = False
        context['can_edit_metodopago'] = False
        context['can_view_metodocobro'] = False
        context['can_create_metodocobro'] = False
        context['can_edit_metodocobro'] = False
    
    return context

```

```python
from django.contrib.auth.models import Permission, Group

def permissions_context(request):
    """
    Context processor que proporciona información de permisos usando Django estándar.
    Reemplaza el sistema personalizado de roles.
    """
    context = {}
    
    if request.user.is_authenticated:
        # Información del usuario
        context['current_user'] = request.user
        
        # Verificar si es administrador del sistema
        admin_group = Group.objects.filter(name='Admin').first()
        context['is_admin'] = admin_group and request.user in admin_group.user_set.all()
        
        # Grupos del usuario (Django estándar)
        context['user_groups'] = request.user.groups.all()
        context['user_group_names'] = [g.name for g in request.user.groups.all()]
        
        # Permisos del usuario (Django estándar)
        if context['is_admin']:
            # Usuario del grupo Admin tiene todos los permisos
            context['user_permissions'] = Permission.objects.all()
            context['user_permission_codes'] = [p.codename for p in Permission.objects.all()]
        else:
            # Obtener permisos del usuario y sus grupos
            user_permissions = request.user.user_permissions.all()
            group_permissions = Permission.objects.filter(group__user=request.user)
            all_permissions = (user_permissions | group_permissions).distinct()
            
            context['user_permissions'] = all_permissions
            context['user_permission_codes'] = [p.codename for p in all_permissions]
        
        # Verificaciones comunes usando permisos de Django
        context['can_manage_users'] = (
            context['is_admin'] or 
            request.user.is_staff or
            request.user.has_perm('usuarios.add_usuario') or
            request.user.has_perm('usuarios.change_usuario') or
            request.user.has_perm('usuarios.delete_usuario')
        )
        
        context['can_manage_groups'] = (
            context['is_admin'] or 
            request.user.is_staff or
            request.user.has_perm('auth.add_group') or
            request.user.has_perm('auth.change_group') or
            request.user.has_perm('auth.delete_group')
        )
        
        context['can_manage_permissions'] = (
            context['is_admin'] or 
            request.user.is_staff or
            request.user.has_perm('auth.change_permission')
        )
        
        context['can_view_admin_dashboard'] = (
            context['is_admin'] or 
            request.user.is_staff or
            context['can_manage_users'] or
            context['can_manage_groups'] or
            context['can_manage_permissions']
        )
        
        # Permisos específicos para clientes
        context['can_view_cliente'] = request.user.has_perm('clientes.view_cliente')
        context['can_create_cliente'] = request.user.has_perm('clientes.add_cliente')
        context['can_edit_cliente'] = request.user.has_perm('clientes.change_cliente')
        context['can_delete_cliente'] = request.user.has_perm('clientes.delete_cliente')
        
        context['can_view_tipocliente'] = request.user.has_perm('clientes.view_tipocliente')
        context['can_create_tipocliente'] = request.user.has_perm('clientes.add_tipocliente')
        context['can_edit_tipocliente'] = request.user.has_perm('clientes.change_tipocliente')
        context['can_delete_tipocliente'] = request.user.has_perm('clientes.delete_tipocliente')
        
        # Permisos para usuarios
        context['can_view_usuarios'] = request.user.has_perm('usuarios.view_usuario')
        context['can_create_usuarios'] = request.user.has_perm('usuarios.add_usuario')
        context['can_edit_usuarios'] = request.user.has_perm('usuarios.change_usuario')
        context['can_delete_usuarios'] = request.user.has_perm('usuarios.delete_usuario')
        
        # Permisos para grupos
        context['can_view_groups'] = request.user.has_perm('auth.view_group')
        context['can_create_groups'] = request.user.has_perm('auth.add_group')
        context['can_edit_groups'] = request.user.has_perm('auth.change_group')
        context['can_delete_groups'] = request.user.has_perm('auth.delete_group')
        
        # Permisos específicos para monedas
        context['can_view_monedas'] = request.user.has_perm('monedas.view_moneda')
        context['can_create_monedas'] = request.user.has_perm('monedas.add_moneda')
        context['can_edit_monedas'] = request.user.has_perm('monedas.change_moneda')
        
        # Permisos específicos para tasas de cambio
        context['can_view_tasacambio'] = request.user.has_perm('tasa_cambio.view_tasacambio')
        context['can_create_tasacambio'] = request.user.has_perm('tasa_cambio.add_tasacambio')
        context['can_edit_tasacambio'] = request.user.has_perm('tasa_cambio.change_tasacambio')
        
        # Permisos específicos para métodos de pago
        context['can_view_metodopago'] = request.user.has_perm('metodo_pago.view_metodopago')
        context['can_create_metodopago'] = request.user.has_perm('metodo_pago.add_metodopago')
        context['can_edit_metodopago'] = request.user.has_perm('metodo_pago.change_metodopago')
        
        # Permisos específicos para métodos de cobro
        context['can_view_metodocobro'] = request.user.has_perm('metodo_cobro.view_metodocobro')
        context['can_create_metodocobro'] = request.user.has_perm('metodo_cobro.add_metodocobro')
        context['can_edit_metodocobro'] = request.user.has_perm('metodo_cobro.change_metodocobro')
        
        # Permisos específicos para configuración
        context['can_view_configuracion'] = request.user.has_perm('configuracion.change_configuracionsistema')
        
        # Dashboard
        context['can_view_dashboard'] = (
            context['is_admin'] or 
            request.user.is_staff or
            context['can_view_usuarios'] or
            context['can_view_groups'] or
            context['can_view_cliente'] or
            context['can_view_monedas'] or
            context['can_view_tasacambio'] or
            context['can_view_metodopago'] or
            context['can_view_metodocobro'] or
            context['can_view_configuracion']
        )
        
    else:
        # Usuario no autenticado
        context['current_user'] = None
        context['is_admin'] = False
        context['user_groups'] = []
        context['user_group_names'] = []
        context['user_permissions'] = []
        context['user_permission_codes'] = []
        context['can_manage_users'] = False
        context['can_manage_groups'] = False
        context['can_manage_permissions'] = False
        context['can_view_admin_dashboard'] = False
        context['can_view_cliente'] = False
        context['can_create_cliente'] = False
        context['can_edit_cliente'] = False
        context['can_delete_cliente'] = False
        context['can_view_tipocliente'] = False
        context['can_create_tipocliente'] = False
        context['can_edit_tipocliente'] = False
        context['can_delete_tipocliente'] = False
        context['can_view_usuarios'] = False
        context['can_create_usuarios'] = False
        context['can_edit_usuarios'] = False
        context['can_delete_usuarios'] = False
        context['can_view_groups'] = False
        context['can_create_groups'] = False
        context['can_edit_groups'] = False
        context['can_delete_groups'] = False
        context['can_view_monedas'] = False
        context['can_create_monedas'] = False
        context['can_edit_monedas'] = False
        context['can_view_tasacambio'] = False
        context['can_create_tasacambio'] = False
        context['can_edit_tasacambio'] = False
        context['can_view_dashboard'] = False
        context['can_view_metodopago'] = False
        context['can_create_metodopago'] = False
        context['can_edit_metodopago'] = False
        context['can_view_metodocobro'] = False
        context['can_create_metodocobro'] = False
        context['can_edit_metodocobro'] = False
    
    return context

```

```python
from django.contrib.auth.models import Permission, Group

def permissions_context(request):
    """
    Context processor que proporciona información de permisos usando Django estándar.
    Reemplaza el sistema personalizado de roles.
    """
    context = {}
    
    if request.user.is_authenticated:
        # Información del usuario
        context['current_user'] = request.user
        
        # Verificar si es administrador del sistema
        admin_group = Group.objects.filter(name='Admin').first()
        context['is_admin'] = admin_group and request.user in admin_group.user_set.all()
        
        # Grupos del usuario (Django estándar)
        context['user_groups'] = request.user.groups.all()
        context['user_group_names'] = [g.name for g in request.user.groups.all()]
        
        # Permisos del usuario (Django estándar)
        if context['is_admin']:
            # Usuario del grupo Admin tiene todos los permisos
            context['user_permissions'] = Permission.objects.all()
            context['user_permission_codes'] = [p.codename for p in Permission.objects.all()]
        else:
            # Obtener permisos del usuario y sus grupos
            user_permissions = request.user.user_permissions.all()
            group_permissions = Permission.objects.filter(group__user=request.user)
            all_permissions = (user_permissions | group_permissions).distinct()
            
            context['user_permissions'] = all_permissions
            context['user_permission_codes'] = [p.codename for p in all_permissions]
        
        # Verificaciones comunes usando permisos de Django
        context['can_manage_users'] = (
            context['is_admin'] or 
            request.user.is_staff or
            request.user.has_perm('usuarios.add_usuario') or
            request.user.has_perm('usuarios.change_usuario') or
            request.user.has_perm('usuarios.delete_usuario')
        )
        
        context['can_manage_groups'] = (
            context['is_admin'] or 
            request.user.is_staff or
            request.user.has_perm('auth.add_group') or
            request.user.has_perm('auth.change_group') or
            request.user.has_perm('auth.delete_group')
        )
        
        context['can_manage_permissions'] = (
            context['is_admin'] or 
            request.user.is_staff or
            request.user.has_perm('auth.change_permission')
        )
        
        context['can_view_admin_dashboard'] = (
            context['is_admin'] or 
            request.user.is_staff or
            context['can_manage_users'] or
            context['can_manage_groups'] or
            context['can_manage_permissions']
        )
        
        # Permisos específicos para clientes
        context['can_view_cliente'] = request.user.has_perm('clientes.view_cliente')
        context['can_create_cliente'] = request.user.has_perm('clientes.add_cliente')
        context['can_edit_cliente'] = request.user.has_perm('clientes.change_cliente')
        context['can_delete_cliente'] = request.user.has_perm('clientes.delete_cliente')
        
        context['can_view_tipocliente'] = request.user.has_perm('clientes.view_tipocliente')
        context['can_create_tipocliente'] = request.user.has_perm('clientes.add_tipocliente')
        context['can_edit_tipocliente'] = request.user.has_perm('clientes.change_tipocliente')
        context['can_delete_tipocliente'] = request.user.has_perm('clientes.delete_tipocliente')
        
        # Permisos para usuarios
        context['can_view_usuarios'] = request.user.has_perm('usuarios.view_usuario')
        context['can_create_usuarios'] = request.user.has_perm('usuarios.add_usuario')
        context['can_edit_usuarios'] = request.user.has_perm('usuarios.change_usuario')
        context['can_delete_usuarios'] = request.user.has_perm('usuarios.delete_usuario')
        
        # Permisos para grupos
        context['can_view_groups'] = request.user.has_perm('auth.view_group')
        context['can_create_groups'] = request.user.has_perm('auth.add_group')
        context['can_edit_groups'] = request.user.has_perm('auth.change_group')
        context['can_delete_groups'] = request.user.has_perm('auth.delete_group')
        
        # Permisos específicos para monedas
        context['can_view_monedas'] = request.user.has_perm('monedas.view_moneda')
        context['can_create_monedas'] = request.user.has_perm('monedas.add_moneda')
        context['can_edit_monedas'] = request.user.has_perm('monedas.change_moneda')
        
        # Permisos específicos para tasas de cambio
        context['can_view_tasacambio'] = request.user.has_perm('tasa_cambio.view_tasacambio')
        context['can_create_tasacambio'] = request.user.has_perm('tasa_cambio.add_tasacambio')
        context['can_edit_tasacambio'] = request.user.has_perm('tasa_cambio.change_tasacambio')
        
        # Permisos específicos para métodos de pago
        context['can_view_metodopago'] = request.user.has_perm('metodo_pago.view_metodopago')
        context['can_create_metodopago'] = request.user.has_perm('metodo_pago.add_metodopago')
        context['can_edit_metodopago'] = request.user.has_perm('metodo_pago.change_metodopago')
        
        # Permisos específicos para métodos de cobro
        context['can_view_metodocobro'] = request.user.has_perm('metodo_cobro.view_metodocobro')
        context['can_create_metodocobro'] = request.user.has_perm('metodo_cobro.add_metodocobro')
        context['can_edit_metodocobro'] = request.user.has_perm('metodo_cobro.change_metodocobro')
        
        # Permisos específicos para configuración
        context['can_view_configuracion'] = request.user.has_perm('configuracion.change_configuracionsistema')
        
        # Dashboard
        context['can_view_dashboard'] = (
            context['is_admin'] or 
            request.user.is_staff or
            context['can_view_usuarios'] or
            context['can_view_groups'] or
            context['can_view_cliente'] or
            context['can_view_monedas'] or
            context['can_view_tasacambio'] or
            context['can_view_metodopago'] or
            context['can_view_metodocobro'] or
            context['can_view_configuracion']
        )
        
    else:
        # Usuario no autenticado
        context['current_user'] = None
        context['is_admin'] = False
        context['user_groups'] = []
        context['user_group_names'] = []
        context['user_permissions'] = []
        context['user_permission_codes'] = []
        context['can_manage_users'] = False
        context['can_manage_groups'] = False
        context['can_manage_permissions'] = False
        context['can_view_admin_dashboard'] = False
        context['can_view_cliente'] = False
        context['can_create_cliente'] = False
        context['can_edit_cliente'] = False
        context['can_delete_cliente'] = False
        context['can_view_tipocliente'] = False
        context['can_create_tipocliente'] = False
        context['can_edit_tipocliente'] = False
        context['can_delete_tipocliente'] = False
        context['can_view_usuarios'] = False
        context['can_create_usuarios'] = False
        context['can_edit_usuarios'] = False
        context['can_delete_usuarios'] = False
        context['can_view_groups'] = False
        context['can_create_groups'] = False
        context['can_edit_groups'] = False
        context['can_delete_groups'] = False
        context['can_view_monedas'] = False
        context['can_create_monedas'] = False
        context['can_edit_monedas'] = False
        context['can_view_tasacambio'] = False
        context['can_create_tasacambio'] = False
        context['can_edit_tasacambio'] = False
        context['can_view_dashboard'] = False
        context['can_view_metodopago'] = False
        context['can_create_metodopago'] = False
        context['can_edit_metodopago'] = False
        context['can_view_metodocobro'] = False
        context['can_create_metodocobro'] = False
        context['can_edit_metodocobro'] = False
        context['can_view_configuracion'] = False
    
    return context

```

Creando y ejecutando las migraciones.


El warning de importación es esperado en este entorno. Ejecutando las pruebas de la app `configuracion`.


Las pruebas pasaron. Verificando que el servidor inicie correctamente:


## Funcionalidad implementada

### 1. **Modelo de configuración** (`configuracion/models.py`)
- `ConfiguracionSistema` con:
  - `limite_diario_transacciones`
  - `limite_mensual_transacciones`
- Singleton: una sola instancia
- Método `get_configuracion()` para obtener o crear la configuración

### 2. **Formulario** (`configuracion/forms.py`)
- Validación: límite mensual >= límite diario
- Campos con decimales
- Mensajes de ayuda

### 3. **Vista y URLs** (`configuracion/views.py`, `configuracion/urls.py`)
- Vista protegida con permisos
- Formulario para mostrar y actualizar
- Mensajes de éxito

### 4. **Template** (`configuracion/templates/configuracion/configuracion.html`)
- Formulario con Bootstrap
- Información de última actualización
- Navegación al dashboard

### 5. **Tarjeta en el dashboard** (`auth/templates/auth/dashboard.html`)
- Tarjeta "Configuración" con ícono
- Visible solo con permisos
- Enlace a la página de configuración

### 6. **Permisos y contexto** (`grupos/context_processors.py`)
- `can_view_configuracion` basado en `configuracion.change_configuracionsistema`
- Integrado en el contexto del dashboard

### 7. **Configuración del proyecto**
- App registrada en `settings.py`
- URLs agregadas en `global_exchange/urls.py`
- Migraciones creadas y aplicadas

### 8. **Pruebas** (`configuracion/tests.py`)
- Pruebas del modelo
- Verificación del patrón singleton
- Todas las pruebas pasan

## Características
- Solo dos campos: límite diario y mensual
- Sin CRUD: formulario simple de configuración
- Validación: mensual >= diario
- Permisos: solo usuarios autorizados
- Singleton: una sola configuración
- UI consistente con el resto del sistema

## Cómo usar
1. Acceder al dashboard
2. Abrir la tarjeta "Configuración"
3. Establecer límites diario y mensual
4. Guardar

La funcionalidad está lista y operativa.

