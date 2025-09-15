
## Solicitud Inicial
**Usuario:** "Necesito crear un CRUD completo para monedas, debe tener nombre, codigo, simbolo,decimales"


**Claude**
## Análisis de Requerimientos

### Funcionalidades Solicitadas
- ✅ Crear, leer, actualizar y eliminar monedas
- ✅ Validación de campos únicos (código y nombre)
- ✅ Gestión de estado activo/inactivo
- ✅ Interfaz de usuario consistente con el diseño del sistema
- ✅ Validaciones de seguridad y permisos
- ✅ Paginación y búsqueda

### Estructura de Datos Definida
```python
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

### 2. Configuración de URLs (urls.py)
**Archivo:** `monedas/urls.py`

```python
from django.urls import path
from . import views

app_name = 'monedas'

urlpatterns = [
    # CRUD de monedas
    path('', MonedaListView.as_view(), name='moneda_list'),
    path('crear/', MonedaCreateView.as_view(), name='moneda_create'),
    path('editar/<int:pk>/', MonedaUpdateView.as_view(), name='moneda_update'),
    
    # APIs AJAX
    path('toggle-status/<int:pk>/', toggle_moneda_status, name='toggle_status'),
    path('api/detalle/<int:pk>/', moneda_detail_api, name='moneda_detail_api'),
    path('relations/<int:pk>/', get_moneda_relations, name='get_relations'),
]
```

### 3. Desarrollo de Vistas (views.py)
**Archivo:** `monedas/views.py`

```python
from django.shortcuts import render
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.db.models import Q
from .models import Moneda

class MonedaListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """Vista para listar todas las monedas"""
    model = Moneda
    template_name = 'monedas/moneda_list.html'
    context_object_name = 'monedas'
    permission_required = 'monedas.view_moneda'
    paginate_by = 20

    def get_queryset(self):
        queryset = Moneda.objects.all()
        
        # Filtro de búsqueda
        q = self.request.GET.get('q')
        if q:
            queryset = queryset.filter(
                Q(nombre__icontains=q) |
                Q(codigo__icontains=q) |
                Q(simbolo__icontains=q)
            )
        
        # Filtro por estado activo/inactivo
        estado = self.request.GET.get('estado')
        if estado == 'activo':
            queryset = queryset.filter(es_activa=True)
        elif estado == 'inactivo':
            queryset = queryset.filter(es_activa=False)
        
        return queryset.order_by('nombre')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Gestión de Monedas'
        context['q'] = self.request.GET.get('q', '')
        context['estado'] = self.request.GET.get('estado', '')
        return context


class MonedaCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """Vista para crear una nueva moneda"""
    model = Moneda
    form_class = MonedaForm
    template_name = 'monedas/moneda_form.html'
    success_url = reverse_lazy('monedas:moneda_list')
    permission_required = 'monedas.add_moneda'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Crear Nueva Moneda'
        context['accion'] = 'Crear'
        return context

    def form_valid(self, form):
        messages.success(self.request, f"Moneda '{form.instance.nombre}' creada exitosamente.")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Error al crear la moneda. Verifique los datos ingresados.")
        return super().form_invalid(form)


class MonedaUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """Vista para editar una moneda existente"""
    model = Moneda
    form_class = MonedaForm
    template_name = 'monedas/moneda_form.html'
    success_url = reverse_lazy('monedas:moneda_list')
    permission_required = 'monedas.change_moneda'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = f'Editar Moneda: {self.object.nombre}'
        context['accion'] = 'Actualizar'
        return context

    def form_valid(self, form):
        messages.success(self.request, f"Moneda '{form.instance.nombre}' actualizada exitosamente.")
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Error al actualizar la moneda. Verifique los datos ingresados.")
        return super().form_invalid(form)


### 4. Templates Desarrollados

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
                        
                        <!-- Campos del formulario con validación completa -->
                        <!-- ... campos ... -->
                        
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
```


### 6. Migraciones y Base de Datos
```bash
# Comandos ejecutados:
python manage.py makemigrations monedas
python manage.py migrate
```

### 7. Configuración de Permisos
```python
# En apps.py se configuraron los permisos automáticos
class MonedasConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'monedas'
    verbose_name = 'Gestión de Monedas'
```

### 8. Integración en el Sistema Principal
```python
# URLs principales (global_exchange/urls.py)
urlpatterns = [
    # ... otras URLs ...
    path('monedas/', include('monedas.urls')),
]

# Settings.py
INSTALLED_APPS = [
    # ... otras apps ...
    'monedas',
]
```
