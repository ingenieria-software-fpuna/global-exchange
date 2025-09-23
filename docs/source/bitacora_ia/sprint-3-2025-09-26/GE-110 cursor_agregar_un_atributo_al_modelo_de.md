# Agregar un atributo al modelo de Clientes "monto_limite_transaccion" en donde
_Exported on 9/23/2025 at 14:48:47 GMT-3 from Cursor (1.5.5)_

---

**User**

Agregar un atributo al modelo de Clientes "monto_limite_transaccion" en donde se especifique cual es el monto máximo que puede realizar un cliente en una sola transacción. Modificar tambien las vistas y formularios necesarios. No hace falta crear migraciones para los datos ya existentes. Hacer de cuenta que voy a correr make app-setup cuando ya hayas implementado todo esto.

---

**Cursor**

I'll scan the codebase to locate the Clientes model, related forms, and views to implement the new field across the stack. Then I'll add the field, update forms, adjust views, and ensure admin/serializers if present.

I'll open the `clientes` app files for the model, form, admin, views, and template to implement the new field and ensure it's exposed in the UI.

I'll add the new `monto_limite_transaccion` field to the `Cliente` model, update the `ClienteForm` to include and style it, extend the admin to display and edit it, and update the `cliente_form.html` template to render the field with validation messages. Then I'll check for linter errors in the modified files.

```python
from django.db import models
from django.core.validators import RegexValidator, MinValueValidator
from django.core.exceptions import ValidationError

# Create your models here.

class TipoCliente(models.Model):
    nombre = models.CharField(max_length=100, unique=True, verbose_name="Nombre del tipo")
    descripcion = models.TextField(blank=True, null=True, verbose_name="Descripción")
    descuento = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, verbose_name="Descuento (%)")
    activo = models.BooleanField(default=True, verbose_name="Activo")
    fecha_creacion = models.DateTimeField(auto_now_add=True, verbose_name="Fecha de creación")
    fecha_modificacion = models.DateTimeField(auto_now=True, verbose_name="Fecha de modificación")

    class Meta:
        verbose_name = "Tipo de Cliente"
        verbose_name_plural = "Tipos de Cliente"
        ordering = ['nombre']

    def __str__(self):
        return self.nombre

class Cliente(models.Model):
    nombre_comercial = models.CharField(
        max_length=200, 
        verbose_name="Nombre Comercial",
        help_text="Nombre comercial o razón social del cliente"
    )
    ruc = models.CharField(
        max_length=20, 
        unique=True, 
        verbose_name="RUC",
        help_text="Número de RUC del cliente",
        validators=[
            RegexValidator(
                regex=r'^\d{5,20}$',
                message='El RUC debe contener solo números y tener entre 5 y 20 dígitos.'
            )
        ]
    )
    direccion = models.TextField(
        verbose_name="Dirección",
        help_text="Dirección completa del cliente",
        blank=True,
        null=True
    )
    correo_electronico = models.EmailField(
        verbose_name="Correo Electrónico",
        help_text="Correo electrónico de contacto del cliente",
        null=True,
        blank=True
    )
    numero_telefono = models.CharField(
        max_length=20, 
        verbose_name="Número de Teléfono",
        help_text="Número de teléfono de contacto",
        blank=True,
        null=True,
        validators=[
            RegexValidator(
                regex=r'^[\d\s\-\+\(\)]+$',
                message='El número de teléfono debe contener solo números, espacios, guiones, paréntesis y el símbolo +.'
            )
        ]
    )
    tipo_cliente = models.ForeignKey(
        TipoCliente,
        on_delete=models.PROTECT,
        verbose_name="Tipo de Cliente",
        help_text="Tipo de cliente que determina el descuento aplicable"
    )
    usuarios_asociados = models.ManyToManyField(
        'usuarios.Usuario',
        blank=True,
        verbose_name="Usuarios Asociados",
        help_text="Usuarios que pueden operar en nombre de este cliente"
    )
    monto_limite_transaccion = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(0)],
        verbose_name="Monto límite por transacción",
        help_text="Monto máximo permitido para una sola transacción. Dejar vacío para sin límite."
    )
    activo = models.BooleanField(
        default=True, 
        verbose_name="Activo",
        help_text="Indica si el cliente está activo en el sistema"
    )
    fecha_creacion = models.DateTimeField(
        auto_now_add=True, 
        verbose_name="Fecha de creación"
    )
    fecha_modificacion = models.DateTimeField(
        auto_now=True, 
        verbose_name="Fecha de modificación"
    )

    class Meta:
        verbose_name = "Cliente"
        verbose_name_plural = "Clientes"
        ordering = ['nombre_comercial']
        indexes = [
            models.Index(fields=['ruc']),
            models.Index(fields=['nombre_comercial']),
            models.Index(fields=['tipo_cliente']),
            models.Index(fields=['activo']),
        ]

    def __str__(self):
        return f"{self.nombre_comercial} ({self.ruc})"

    def clean(self):
        """Validación personalizada del modelo"""
        super().clean()
        
        # Validar que el tipo de cliente esté activo
        if self.tipo_cliente and not self.tipo_cliente.activo:
            raise ValidationError({
                'tipo_cliente': 'No se puede asignar un tipo de cliente inactivo.'
            })

    def save(self, *args, **kwargs):
        self.clean()
        super().save(*args, **kwargs)

```

```python
from django import forms
from django.contrib.auth import get_user_model
from .models import Cliente, TipoCliente
from .widgets import UsuarioSelectorWidget

User = get_user_model()

class ClienteForm(forms.ModelForm):
    """
    Formulario para crear y editar clientes con widget personalizado
    para selección de usuarios asociados.
    """
    
    usuarios_asociados = forms.ModelMultipleChoiceField(
        queryset=User.objects.none(),  # Se configurará en __init__
        widget=UsuarioSelectorWidget(),
        required=False,
        label="Usuarios Asociados",
        help_text="Usuarios que pueden operar en nombre de este cliente."
    )
    
    class Meta:
        model = Cliente
        fields = [
            'nombre_comercial', 'ruc', 'direccion', 'correo_electronico',
            'numero_telefono', 'tipo_cliente', 'monto_limite_transaccion', 'usuarios_asociados', 'activo'
        ]
        widgets = {
            'nombre_comercial': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Empresa ABC S.A.'
            }),
            'ruc': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: 801234567'
            }),
            'direccion': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Av. Principal 123, Asunción'
            }),
            'correo_electronico': forms.EmailInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: contacto@empresa.com'
            }),
            'numero_telefono': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: +595 21 123456'
            }),
            'tipo_cliente': forms.Select(attrs={
                'class': 'form-select'
            }),
            'monto_limite_transaccion': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: 1000000.00',
                'min': '0',
                'step': '0.01'
            }),
            'activo': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Configurar queryset para usuarios activos
        self.fields['usuarios_asociados'].queryset = User.objects.filter(
            activo=True, es_activo=True
        ).order_by('nombre', 'apellido')
        
        # Configurar queryset para tipos de cliente activos
        self.fields['tipo_cliente'].queryset = TipoCliente.objects.filter(
            activo=True
        ).order_by('nombre')
        
        # Configurar labels y help texts
        self.fields['nombre_comercial'].label = "Nombre Comercial"
        self.fields['ruc'].label = "RUC"
        self.fields['direccion'].label = "Dirección"
        self.fields['correo_electronico'].label = "Correo Electrónico"
        self.fields['numero_telefono'].label = "Número de Teléfono"
        self.fields['tipo_cliente'].label = "Tipo de Cliente"
        self.fields['monto_limite_transaccion'].label = "Monto límite por transacción"
        self.fields['monto_limite_transaccion'].help_text = "Monto máximo permitido en una sola transacción. Vacío = sin límite."
        self.fields['activo'].label = "Activo"
        
        # Marcar campos requeridos
        self.fields['nombre_comercial'].required = True
        self.fields['ruc'].required = True
        self.fields['correo_electronico'].required = True
        self.fields['tipo_cliente'].required = True

```

```python
from django.contrib import admin
from .models import TipoCliente, Cliente

@admin.register(TipoCliente)
class TipoClienteAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'descripcion', 'descuento', 'activo', 'fecha_creacion', 'fecha_modificacion']
    list_filter = ['activo', 'fecha_creacion']
    search_fields = ['nombre', 'descripcion']
    readonly_fields = ['fecha_creacion', 'fecha_modificacion']
    ordering = ['nombre']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('nombre', 'descripcion', 'descuento')
        }),
        ('Estado', {
            'fields': ('activo',)
        }),
        ('Fechas', {
            'fields': ('fecha_creacion', 'fecha_modificacion'),
            'classes': ('collapse',)
        }),
    )

@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = [
        'nombre_comercial', 'ruc', 'tipo_cliente', 'correo_electronico', 
        'numero_telefono', 'monto_limite_transaccion', 'activo', 'fecha_creacion'
    ]
    list_filter = [
        'activo', 'tipo_cliente', 'fecha_creacion', 'usuarios_asociados'
    ]
    search_fields = [
        'nombre_comercial', 'ruc', 'correo_electronico', 'numero_telefono'
    ]
    readonly_fields = ['fecha_creacion', 'fecha_modificacion']
    ordering = ['nombre_comercial']
    filter_horizontal = ['usuarios_asociados']
    
    fieldsets = (
        ('Información Básica', {
            'fields': ('nombre_comercial', 'ruc', 'tipo_cliente', 'monto_limite_transaccion')
        }),
        ('Información de Contacto', {
            'fields': ('direccion', 'correo_electronico', 'numero_telefono')
        }),
        ('Relaciones', {
            'fields': ('usuarios_asociados',)
        }),
        ('Estado', {
            'fields': ('activo',)
        }),
        ('Fechas', {
            'fields': ('fecha_creacion', 'fecha_modificacion'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('tipo_cliente').prefetch_related('usuarios_asociados')

```

```django-html
{% extends "base.html" %}

{% block title %}{% if form.instance.pk %}Editar{% else %}Crear{% endif %} Cliente - Global Exchange{% endblock %}

{% block content %}
<div class="container mt-4">
    <!-- Breadcrumbs -->
    <nav aria-label="breadcrumb" class="mb-4">
        <ol class="breadcrumb">
            <li class="breadcrumb-item">
                <a href="{% url 'auth:dashboard' %}">
                    <i class="fas fa-home me-1"></i>Dashboard
                </a>
            </li>
            <li class="breadcrumb-item">
                <a href="{% url 'clientes:cliente_list' %}">
                    <i class="fas fa-user-tie me-1"></i>Clientes
                </a>
            </li>
            <li class="breadcrumb-item active" aria-current="page">
                {% if form.instance.pk %}Editar{% else %}Crear{% endif %}
            </li>
        </ol>
    </nav>

    {% include 'includes/back_button.html' with text="Volver a Clientes" %}
    
    <div class="row justify-content-center">
        <div class="col-lg-10">
            <div class="card shadow-sm">
                <div class="card-header bg-success text-white">
                    <h4 class="mb-0">
                        <i class="fas fa-user-tie me-2"></i>
                        {% if form.instance.pk %}Editar{% else %}Crear{% endif %} Cliente
                    </h4>
                </div>
                <div class="card-body">
                    <form method="post">
                        {% csrf_token %}
                        
                        <div class="row">
                            <!-- Información Básica -->
                            <div class="col-md-6">
                                <h5 class="text-success mb-3">
                                    <i class="fas fa-info-circle me-2"></i>Información Básica
                                </h5>
                                
                                <div class="mb-3">
                                    <label for="{{ form.nombre_comercial.id_for_label }}" class="form-label">
                                        <strong>Nombre Comercial:</strong> <span class="text-danger">*</span>
                                    </label>
                                    {{ form.nombre_comercial }}
                                    {% if form.nombre_comercial.errors %}
                                        <div class="invalid-feedback d-block">
                                            {{ form.nombre_comercial.errors.0 }}
                                        </div>
                                    {% endif %}
                                    <div class="form-text">Nombre comercial o razón social del cliente.</div>
                                </div>

                                <div class="mb-3">
                                    <label for="{{ form.ruc.id_for_label }}" class="form-label">
                                        <strong>RUC:</strong> <span class="text-danger">*</span>
                                    </label>
                                    {{ form.ruc }}
                                    {% if form.ruc.errors %}
                                        <div class="invalid-feedback d-block">
                                            {{ form.ruc.errors.0 }}
                                        </div>
                                    {% endif %}
                                    <div class="form-text">Número de RUC del cliente (solo números).</div>
                                </div>

                                <div class="mb-3">
                                    <label for="{{ form.tipo_cliente.id_for_label }}" class="form-label">
                                        <strong>Tipo de Cliente:</strong> <span class="text-danger">*</span>
                                    </label>
                                    {{ form.tipo_cliente }}
                                    {% if form.tipo_cliente.errors %}
                                        <div class="invalid-feedback d-block">
                                            {{ form.tipo_cliente.errors.0 }}
                                        </div>
                                    {% endif %}
                                    <div class="form-text">Tipo de cliente que determina el descuento aplicable.</div>
                                </div>

                                <div class="mb-3">
                                    <label for="{{ form.monto_limite_transaccion.id_for_label }}" class="form-label">
                                        <strong>Monto límite por transacción:</strong>
                                    </label>
                                    {{ form.monto_limite_transaccion }}
                                    {% if form.monto_limite_transaccion.errors %}
                                        <div class="invalid-feedback d-block">
                                            {{ form.monto_limite_transaccion.errors.0 }}
                                        </div>
                                    {% endif %}
                                    <div class="form-text">Monto máximo permitido en una sola transacción. Vacío = sin límite.</div>
                                </div>
                            </div>

                            <!-- Información de Contacto -->
                            <div class="col-md-6">
                                <h5 class="text-success mb-3">
                                    <i class="fas fa-address-book me-2"></i>Información de Contacto
                                </h5>
                                
                                <div class="mb-3">
                                    <label for="{{ form.correo_electronico.id_for_label }}" class="form-label">
                                        <strong>Correo Electrónico:</strong> <span class="text-danger">*</span>
                                    </label>
                                    {{ form.correo_electronico }}
                                    {% if form.correo_electronico.errors %}
                                        <div class="invalid-feedback d-block">
                                            {{ form.correo_electronico.errors.0 }}
                                        </div>
                                    {% endif %}
                                    <div class="form-text">Correo electrónico de contacto del cliente.</div>
                                </div>

                                <div class="mb-3">
                                    <label for="{{ form.numero_telefono.id_for_label }}" class="form-label">
                                        <strong>Número de Teléfono:</strong>
                                    </label>
                                    {{ form.numero_telefono }}
                                    {% if form.numero_telefono.errors %}
                                        <div class="invalid-feedback d-block">
                                            {{ form.numero_telefono.errors.0 }}
                                        </div>
                                    {% endif %}
                                    <div class="form-text">Número de teléfono de contacto.</div>
                                </div>

                                <div class="mb-3">
                                    <label for="{{ form.direccion.id_for_label }}" class="form-label">
                                        <strong>Dirección:</strong>
                                    </label>
                                    {{ form.direccion }}
                                    {% if form.direccion.errors %}
                                        <div class="invalid-feedback d-block">
                                            {{ form.direccion.errors.0 }}
                                        </div>
                                    {% endif %}
                                    <div class="form-text">Dirección completa del cliente.</div>
                                </div>
                            </div>
                        </div>

                        <!-- Usuarios Asociados -->
                        <div class="row mt-4">
                            <div class="col-12">
                                <h5 class="text-success mb-3">
                                    <i class="fas fa-users me-2"></i>Usuarios Asociados
                                </h5>
                                
                                <div class="mb-3">
                                    <div class="border rounded p-3 bg-light">
                                        {{ form.usuarios_asociados }}
                                        {% if form.usuarios_asociados.errors %}
                                            <div class="invalid-feedback d-block mt-2">
                                                {{ form.usuarios_asociados.errors.0 }}
                                            </div>
                                        {% endif %}
                                        <div class="form-text mt-2">
                                            {{ form.usuarios_asociados.help_text }}
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <!-- Estado -->
                        <div class="row mt-4">
                            <div class="col-12">
                                <h5 class="text-success mb-3">
                                    <i class="fa-solid fa-shield-halved"></i> Estado
                                </h5>
                                
                                <div class="mb-4">
                                    <div class="form-check">
                                        {{ form.activo }}
                                        <label class="form-check-label" for="{{ form.activo.id_for_label }}">
                                            <strong>Activo</strong>
                                        </label>
                                        {% if form.activo.errors %}
                                            <div class="invalid-feedback d-block">
                                                {{ form.activo.errors.0 }}
                                            </div>
                                        {% endif %}
                                        <div class="form-text">Indica si el cliente está activo en el sistema.</div>
                                    </div>
                                </div>
                            </div>
                        </div>

                        <!-- Botones de acción -->
                        <div class="d-flex justify-content-end gap-2 mt-4">
                            <a href="{% url 'clientes:cliente_list' %}" class="btn btn-secondary">
                                <i class="fas fa-times"></i> Cancelar
                            </a>
                            <button type="submit" class="btn btn-success">
                                <i class="fas fa-save"></i> 
                                {% if form.instance.pk %}Actualizar{% else %}Crear{% endif %}
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}

```

I added the model field, updated the form, admin, and template. Now I'll run a quick linter check on the modified files and fix any issues if present.

I'll check the `clientes/migrations` directory to add a proper schema migration for the new field so it applies during make app-setup.

I added the model field. I'll mark that done and proceed to update the form, template, and admin (already edited), then create a migration so make app-setup applies it. Now I'll update the todo states and generate the migration file.

I'll generate the Django migration for the `clientes` app now.

- Agregué el campo nuevo y ajusté las capas necesarias. Ahora podrás correr make app-setup y la migración se aplicará automáticamente.

Cambios clave:
- Modelo `clientes/models.py`: nuevo `monto_limite_transaccion` (`DecimalField`, null/blank, `MinValueValidator(0)`).
- Formulario `clientes/forms.py`: incluido `monto_limite_transaccion` con `NumberInput`, labels y help text.
- Admin `clientes/admin.py`: visible en `list_display` y en `fieldsets`.
- Template `clientes/templates/clientes/cliente_form.html`: render del campo con errores y ayuda.
- Migración creada: `clientes/migrations/0005_cliente_monto_limite_transaccion.py`.

Con esto, al ejecutar `make app-setup` se crearán las tablas actualizadas sin necesidad de migraciones de datos.

---

**User**

Hacer lo mismo para el modelo de monedas. Un campo nuevo que se llame "monto_limite_transaccion".

---

**Cursor**

I'll locate the Moneda model, its forms, views, templates, and admin to add the new field consistently across the stack. Then I'll implement the field, update UI/admin, and generate a migration.

I'll add the new field to the `Moneda` model, include it in `MonedaForm` with appropriate widget/labels, update the admin to display/edit it, update the `moneda_form.html` template to render it, and then generate the migration.

```python
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone


class Moneda(models.Model):
    """
    Modelo para representar las monedas del sistema.
    """
    nombre = models.CharField(
        max_length=100,
        unique=True,
        help_text="Nombre completo de la moneda (ej: Dólar Estadounidense)"
    )
    codigo = models.CharField(
        max_length=3,
        unique=True,
        help_text="Código ISO 4217 de la moneda (ej: USD, EUR, PYG)"
    )
    simbolo = models.CharField(
        max_length=5,
        help_text="Símbolo de la moneda (ej: $, €, ₲)"
    )
    decimales = models.PositiveSmallIntegerField(
        default=2,
        validators=[MinValueValidator(0)],
        help_text="Número de decimales que usa la moneda (ej: 2 para USD, 0 para JPY)"
    )
    monto_limite_transaccion = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        blank=True,
        null=True,
        validators=[MinValueValidator(0)],
        help_text="Monto máximo permitido para una sola transacción en esta moneda. Vacío = sin límite."
    )
    es_activa = models.BooleanField(
        default=True,
        help_text="Indica si la moneda está activa para operaciones"
    )
    fecha_creacion = models.DateTimeField(
        default=timezone.now,
        help_text="Fecha y hora de creación del registro"
    )
    fecha_actualizacion = models.DateTimeField(
        auto_now=True,
        help_text="Fecha y hora de la última actualización"
    )

    class Meta:
        verbose_name = "Moneda"
        verbose_name_plural = "Monedas"
        ordering = ['nombre']
        db_table = 'monedas_moneda'

    def __str__(self):
        return f"{self.nombre} ({self.codigo})"

    def save(self, *args, **kwargs):
        # Convertir código a mayúsculas
        self.codigo = self.codigo.upper()
        super().save(*args, **kwargs)
    
    def formatear_monto(self, monto):
        """
        Formatea un monto según el número de decimales de la moneda
        """
        formato = f"{{:.{self.decimales}f}}"
        return formato.format(float(monto))
    
    def mostrar_monto(self, monto):
        """
        Muestra un monto con el símbolo y decimales apropiados
        """
        monto_formateado = self.formatear_monto(monto)
        return f"{self.simbolo}{monto_formateado}"

```

```python
from django import forms
from django.core.validators import RegexValidator
from .models import Moneda


class MonedaForm(forms.ModelForm):
    """
    Formulario para crear y editar monedas
    """
    
    class Meta:
        model = Moneda
        fields = [
            'nombre', 'codigo', 'simbolo', 'decimales', 'monto_limite_transaccion', 'es_activa'
        ]
        widgets = {
            'nombre': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: Dólar Estadounidense'
            }),
            'codigo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: USD',
                'maxlength': 3,
                'style': 'text-transform: uppercase;'
            }),
            'simbolo': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: $'
            }),
            'decimales': forms.NumberInput(attrs={
                'class': 'form-control',
                'min': 0,
                'placeholder': 'Ej: 2'
            }),
            'monto_limite_transaccion': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'Ej: 1000000.00',
                'min': '0',
                'step': '0.01'
            }),
            'es_activa': forms.CheckboxInput(attrs={
                'class': 'form-check-input'
            }),
        }
        labels = {
            'nombre': 'Nombre de la Moneda',
            'codigo': 'Código ISO 4217',
            'simbolo': 'Símbolo',
            'monto_limite_transaccion': 'Monto límite por transacción',
            'es_activa': 'Moneda Activa',
        }
        help_texts = {
            'nombre': 'Nombre completo de la moneda',
            'codigo': 'Código de 3 letras según ISO 4217',
            'simbolo': 'Símbolo usado para representar la moneda',
            'monto_limite_transaccion': 'Monto máximo permitido en una sola transacción. Vacío = sin límite.',
            'es_activa': 'Indica si la moneda está disponible para operaciones',
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Validaciones adicionales
        self.fields['codigo'].validators.append(
            RegexValidator(
                regex=r'^[A-Z]{3}$',
                message='El código debe tener exactamente 3 letras mayúsculas.'
            )
        )

    def clean_codigo(self):
        codigo = self.cleaned_data.get('codigo')
        if codigo:
            codigo = codigo.upper()
            
            # Verificar que no exista otra moneda con el mismo código
            if self.instance.pk:
                # Es edición
                if Moneda.objects.filter(codigo=codigo).exclude(pk=self.instance.pk).exists():
                    raise forms.ValidationError('Ya existe una moneda con este código.')
            else:
                # Es creación
                if Moneda.objects.filter(codigo=codigo).exists():
                    raise forms.ValidationError('Ya existe una moneda con este código.')
                    
        return codigo

    def clean_nombre(self):
        nombre = self.cleaned_data.get('nombre')
        if nombre:
            # Verificar que no exista otra moneda con el mismo nombre
            if self.instance.pk:
                # Es edición
                if Moneda.objects.filter(nombre__iexact=nombre).exclude(pk=self.instance.pk).exists():
                    raise forms.ValidationError('Ya existe una moneda con este nombre.')
            else:
                # Es creación
                if Moneda.objects.filter(nombre__iexact=nombre).exists():
                    raise forms.ValidationError('Ya existe una moneda con este nombre.')
                    
        return nombre


class MonedaSearchForm(forms.Form):
    """
    Formulario para búsqueda y filtros de monedas
    """
    q = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Buscar por nombre, código o símbolo...'
        }),
        label='Buscar'
    )
    
    estado = forms.ChoiceField(
        required=False,
        choices=[
            ('', 'Todas'),
            ('activo', 'Activas'),
            ('inactivo', 'Inactivas')
        ],
        widget=forms.Select(attrs={'class': 'form-select'}),
        label='Estado'
    )

```

I'll implement the field across Moneda: update admin, update the template to render the new field, then generate the migration.

```python
from django.contrib import admin
from .models import Moneda


@admin.register(Moneda)
class MonedaAdmin(admin.ModelAdmin):
    list_display = [
        'nombre', 'codigo', 'simbolo', 'decimales', 'monto_limite_transaccion', 'es_activa', 'fecha_creacion'
    ]
    list_filter = ['es_activa', 'fecha_creacion']
    search_fields = ['nombre', 'codigo', 'simbolo']
    readonly_fields = ['fecha_creacion', 'fecha_actualizacion']
    ordering = ['nombre']

    fieldsets = (
        ('Información Básica', {
            'fields': ('nombre', 'codigo', 'simbolo', 'decimales', 'monto_limite_transaccion')
        }),
        ('Estado', {
            'fields': ('es_activa',)
        }),
        ('Fechas', {
            'fields': ('fecha_creacion', 'fecha_actualizacion'),
            'classes': ('collapse',)
        }),
    )

```

```django-html
{% extends 'base.html' %}
{% load static %}

{% block title %}{{ titulo }}{% endblock %}

{% block content %}
<div class="container mt-4">
    <!-- Breadcrumbs -->
    <nav aria-label="breadcrumb" class="mb-4">
        <ol class="breadcrumb">
            <li class="breadcrumb-item">
                <a href="{% url 'auth:dashboard' %}">
                    <i class="fas fa-home me-1"></i>Dashboard
                </a>
            </li>
            <li class="breadcrumb-item">
                <a href="{% url 'monedas:moneda_list' %}">
                    <i class="fas fa-coins me-1"></i>Monedas
                </a>
            </li>
            <li class="breadcrumb-item active" aria-current="page">
                {{ accion|default:"Editar" }}
            </li>
        </ol>
    </nav>

    <div class="row">
        <div class="col-md-8 mx-auto">
            {% include 'includes/back_button.html' with text="Volver a Monedas" %}
            
            <div class="d-flex justify-content-between align-items-center mb-4">
                <h1 class="h2">
                    <i class="fas fa-coins text-success me-2"></i>
                    {{ titulo }}
                </h1>
            </div>

            <div class="card shadow-sm">
                <div class="card-body">
                    <form method="post" class="needs-validation" novalidate>
                        {% csrf_token %}
                        
                        <div class="row g-3">
                            <!-- Nombre -->
                            <div class="col-md-12">
                                <label for="{{ form.nombre.id_for_label }}" class="form-label">
                                    {{ form.nombre.label }} <span class="text-danger">*</span>
                                </label>
                                {{ form.nombre }}
                                {% if form.nombre.errors %}
                                    <div class="invalid-feedback d-block">
                                        {{ form.nombre.errors.0 }}
                                    </div>
                                {% endif %}
                                {% if form.nombre.help_text %}
                                    <div class="form-text">{{ form.nombre.help_text }}</div>
                                {% endif %}
                            </div>

                            <!-- Código -->
                            <div class="col-md-6">
                                <label for="{{ form.codigo.id_for_label }}" class="form-label">
                                    {{ form.codigo.label }} <span class="text-danger">*</span>
                                </label>
                                {{ form.codigo }}
                                {% if form.codigo.errors %}
                                    <div class="invalid-feedback d-block">
                                        {{ form.codigo.errors.0 }}
                                    </div>
                                {% endif %}
                                {% if form.codigo.help_text %}
                                    <div class="form-text">{{ form.codigo.help_text }}</div>
                                {% endif %}
                            </div>

                            <!-- Símbolo -->
                            <div class="col-md-6">
                                <label for="{{ form.simbolo.id_for_label }}" class="form-label">
                                    {{ form.simbolo.label }} <span class="text-danger">*</span>
                                </label>
                                {{ form.simbolo }}
                                {% if form.simbolo.errors %}
                                    <div class="invalid-feedback d-block">
                                        {{ form.simbolo.errors.0 }}
                                    </div>
                                {% endif %}
                                {% if form.simbolo.help_text %}
                                    <div class="form-text">{{ form.simbolo.help_text }}</div>
                                {% endif %}
                            </div>

                            <!-- Decimales -->
                            <div class="col-md-6">
                                <label for="{{ form.decimales.id_for_label }}" class="form-label">
                                    {{ form.decimales.label }} <span class="text-danger">*</span>
                                </label>
                                {{ form.decimales }}
                                {% if form.decimales.errors %}
                                    <div class="invalid-feedback d-block">
                                        {{ form.decimales.errors.0 }}
                                    </div>
                                {% endif %}
                                {% if form.decimales.help_text %}
                                    <div class="form-text">{{ form.decimales.help_text }}</div>
                                {% endif %}
                            </div>

                            <!-- Monto límite por transacción -->
                            <div class="col-md-6">
                                <label for="{{ form.monto_limite_transaccion.id_for_label }}" class="form-label">
                                    {{ form.monto_limite_transaccion.label }}
                                </label>
                                {{ form.monto_limite_transaccion }}
                                {% if form.monto_limite_transaccion.errors %}
                                    <div class="invalid-feedback d-block">
                                        {{ form.monto_limite_transaccion.errors.0 }}
                                    </div>
                                {% endif %}
                                {% if form.monto_limite_transaccion.help_text %}
                                    <div class="form-text">{{ form.monto_limite_transaccion.help_text }}</div>
                                {% endif %}
                            </div>

                            <!-- Estado activo -->
                            <div class="col-md-12">
                                <div class="form-check">
                                    {{ form.es_activa }}
                                    <label class="form-check-label" for="{{ form.es_activa.id_for_label }}">
                                        {{ form.es_activa.label }}
                                    </label>
                                </div>
                                {% if form.es_activa.errors %}
                                    <div class="invalid-feedback d-block">
                                        {{ form.es_activa.errors.0 }}
                                    </div>
                                {% endif %}
                                {% if form.es_activa.help_text %}
                                    <div class="form-text">{{ form.es_activa.help_text }}</div>
                                {% endif %}
                            </div>
                        </div>

                        <!-- Errores generales del formulario -->
                        {% if form.non_field_errors %}
                            <div class="alert alert-danger mt-3">
                                {{ form.non_field_errors }}
                            </div>
                        {% endif %}

                        <!-- Botones de acción -->
                        <div class="d-flex justify-content-end gap-2 mt-4">
                            <a href="{% url 'monedas:moneda_list' %}" class="btn btn-secondary">
                                <i class="fas fa-times"></i> Cancelar
                            </a>
                            <button type="submit" class="btn btn-success">
                                <i class="fas fa-save"></i> {{ accion|default:"Guardar" }}
                            </button>
                        </div>
                    </form>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}

{% block extra_js %}
<script>
// Convertir código a mayúsculas automáticamente
document.getElementById('{{ form.codigo.id_for_label }}').addEventListener('input', function(e) {
    e.target.value = e.target.value.toUpperCase();
});

// Validación de formulario de Bootstrap
(function() {
    'use strict';
    window.addEventListener('load', function() {
        var forms = document.getElementsByClassName('needs-validation');
        var validation = Array.prototype.filter.call(forms, function(form) {
            form.addEventListener('submit', function(event) {
                if (form.checkValidity() === false) {
                    event.preventDefault();
                    event.stopPropagation();
                }
                form.classList.add('was-validated');
            }, false);
        });
    }, false);
})();
</script>
{% endblock %}

```

- Añadí el campo en Monedas y actualicé formularios, admin, template y migración. Listo para make app-setup.

Cambios:
- `monedas/models.py`: `monto_limite_transaccion` (`DecimalField`, null/blank, `MinValueValidator(0)`).
- `monedas/forms.py`: incluido el campo con `NumberInput`, labels y help text.
- `monedas/admin.py`: agregado en `list_display` y `fieldsets`.
- `monedas/templates/monedas/moneda_form.html`: nuevo bloque para renderizar el campo.
- Migración creada: `monedas/migrations/0004_moneda_monto_limite_transaccion.py`.

---

**User**

Ese monto límite debe estar en guaranies (PYG). Puedes agregar algo en los formularios que indique que el monto debe estar expresado en guaranies.

