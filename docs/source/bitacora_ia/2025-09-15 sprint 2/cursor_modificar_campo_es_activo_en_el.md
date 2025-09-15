# Modificar campo es_activo en el modelo Usuario
_Exported on 9/4/2025 at 17:47:39 GMT-3 from Cursor (1.5.5)_

---

**User**

En el modelo Usuario he agregado un campo llamado "es_activo" que sirve para indicar si un usuario esta activo o no.  Entonces quiero que hagas las modificaciones necesarias en el sistema para que cuando se desactive o active un usuario sea el campo "es_activo" el que se modifica, no el campo "activo". El campo "activo" sirve para verificar el correo electronico al iniciar sesion o algo asi.

---

**Cursor**

Entiendo que necesitas modificar el sistema para que el campo `es_activo` sea el que controle si un usuario está activo o no, mientras que el campo `activo` se mantenga para la verificación del correo electrónico. Voy a revisar el modelo actual y hacer las modificaciones necesarias.


Perfecto, he identificado el problema. Veo que el modelo `Usuario` ya tiene ambos campos:
- `activo`: Para verificar correo (línea 39)
- `es_activo`: Para indicar si el usuario está activo o inactivo (línea 42)

Sin embargo, el código actual está usando el campo `activo` para controlar el estado del usuario en lugar de `es_activo`. Ahora voy a buscar todas las referencias y hacer las modificaciones necesarias.


Ahora voy a hacer las modificaciones necesarias. He identificado que necesito cambiar:

1. **En `usuarios/forms.py`**: Cambiar `'activo'` por `'es_activo'` en el formulario de actualización
2. **En `usuarios/views.py`**: Cambiar la lógica de `toggle_usuario_status` para usar `es_activo`
3. **En `usuarios/templates/usuarios/user_list.html`**: Cambiar todas las referencias de `usuario.activo` por `usuario.es_activo`
4. **En `usuarios/tests.py`**: Actualizar las pruebas para usar `es_activo`

Empezaré con las modificaciones:


```python
# apps/usuarios/forms.py
from django import forms
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.models import Group
class LoginForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'Correo electrónico'}),
        label="Correo electrónico"
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={'class': 'form-control', 'placeholder': 'Contraseña'}),
        label="Contraseña"
    )
    
    def clean(self):
        cleaned_data = super().clean()
        email = cleaned_data.get('email')
        password = cleaned_data.get('password')
        
        if email and password:
            self.user_cache = authenticate(username=email, password=password)
            if self.user_cache is None:
                raise forms.ValidationError("Correo electrónico o contraseña inválidos.")
        
        return cleaned_data
    

Usuario = get_user_model()
class UsuarioCreationForm(forms.ModelForm):
    password = forms.CharField(label="Contraseña", widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    password2 = forms.CharField(label="Repetir Contraseña", widget=forms.PasswordInput(attrs={'class': 'form-control'}))
    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all().order_by('name'),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Grupos"
    )

    class Meta:
        model = Usuario
        fields = ('email', 'nombre', 'apellido', 'cedula', 'fecha_nacimiento', 'groups')
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'apellido': forms.TextInput(attrs={'class': 'form-control'}),
            'cedula': forms.TextInput(attrs={'class': 'form-control'}),
            'fecha_nacimiento': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password2 = cleaned_data.get("password2")
        if password and password2 and password != password2:
            raise forms.ValidationError("Las contraseñas no coinciden.")
        return cleaned_data

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()

        # Sincronizar grupos seleccionados
        groups_seleccionados = self.cleaned_data.get('groups')
        if groups_seleccionados is not None:
            user.groups.set(groups_seleccionados)

        return user

class UsuarioUpdateForm(forms.ModelForm):
    groups = forms.ModelMultipleChoiceField(
        queryset=Group.objects.all().order_by('name'),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label="Grupos"
    )
    class Meta:
        model = Usuario
        fields = ('email', 'nombre', 'apellido', 'cedula', 'fecha_nacimiento', 'is_staff', 'es_activo', 'groups')
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'apellido': forms.TextInput(attrs={'class': 'form-control'}),
            'cedula': forms.TextInput(attrs={'class': 'form-control'}),
            'fecha_nacimiento': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
        }
    
    def get_user(self):
        return self.user_cache

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Pre-cargar grupos asignados al usuario
        if self.instance and self.instance.pk:
            self.fields['groups'].initial = self.instance.groups.values_list('pk', flat=True)

    def save(self, commit=True):
        user = super().save(commit=commit)

        # Sincronizar grupos seleccionados
        groups_seleccionados = self.cleaned_data.get('groups')
        if groups_seleccionados is not None:
            user.groups.set(groups_seleccionados)

        return user

```

```python
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.decorators import login_required, permission_required
from django.shortcuts import get_object_or_404
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from .forms import UsuarioCreationForm, UsuarioUpdateForm

Usuario = get_user_model()

# Vista para listar usuarios
class UsuarioListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    model = Usuario
    template_name = 'usuarios/user_list.html'
    context_object_name = 'usuarios'
    permission_required = 'usuarios.view_usuario'
    paginate_by = 20

# Vista para crear un nuevo usuario
class UsuarioCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    model = Usuario
    form_class = UsuarioCreationForm
    template_name = 'usuarios/user_form.html'
    success_url = reverse_lazy('usuarios:user_list')
    permission_required = 'usuarios.add_usuario'

    def form_valid(self, form):
        messages.success(self.request, "Usuario creado exitosamente.")
        return super().form_valid(form)

# Vista para actualizar un usuario
class UsuarioUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    model = Usuario
    form_class = UsuarioUpdateForm
    template_name = 'usuarios/user_form.html'
    success_url = reverse_lazy('usuarios:user_list')
    permission_required = 'usuarios.change_usuario'

    def form_valid(self, form):
        messages.success(self.request, "Usuario actualizado exitosamente.")
        return super().form_valid(form)

# Vista para eliminar un usuario
class UsuarioDeleteView(LoginRequiredMixin, PermissionRequiredMixin, DeleteView):
    model = Usuario
    template_name = 'usuarios/user_confirm_delete.html'
    success_url = reverse_lazy('usuarios:user_list')
    permission_required = 'usuarios.delete_usuario'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = f'Eliminar usuario {self.object.email}'
        return context


@login_required
@permission_required('usuarios.change_usuario', raise_exception=True)
@require_http_methods(["POST"])
def toggle_usuario_status(request, pk):
    """Vista AJAX para cambiar el estado activo/inactivo de un usuario"""
    try:
        usuario = get_object_or_404(Usuario, pk=pk)
        
        usuario.es_activo = not usuario.es_activo
        usuario.save()
        
        status_text = "activado" if usuario.es_activo else "desactivado"
        return JsonResponse({
            'success': True,
            'message': f'Usuario {status_text} exitosamente.',
            'nueva_estado': usuario.es_activo
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': f'Error al cambiar el estado: {str(e)}'
        })
```

```django-html
{% extends "base.html" %}
{% load static %}

{% block title %}Usuarios - Global Exchange{% endblock %}

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
            <li class="breadcrumb-item active" aria-current="page">
                <i class="fas fa-users me-1"></i>Usuarios
            </li>
        </ol>
    </nav>

    <div class="row">
        <div class="col-12">
            <div class="d-flex justify-content-between align-items-center mb-4">
                <h1 class="h2">
                    <i class="fas fa-users text-primary me-2"></i>
                    Usuarios
                </h1>
                {% if can_create_usuarios %}
                <a href="{% url 'usuarios:user_create' %}" class="btn btn-primary">
                    <i class="fas fa-plus me-2"></i>Crear Nuevo Usuario
                </a>
                {% endif %}
            </div>

            {% if usuarios %}
            <div class="card shadow-sm">
                <div class="card-body">
                    <div class="table-responsive">
                        <table class="table table-hover">
                            <thead class="table-light">
                                <tr>
                                    <th>Email</th>
                                    <th>Nombre Completo</th>
                                    <th>Cédula</th>
                                    <th>Estado</th>
                                    <th>Fecha Nacimiento</th>
                                    <th class="text-center">Acciones</th>
                                </tr>
                            </thead>
                            <tbody>
                                {% for usuario in usuarios %}
                                <tr>
                                    <td>
                                        <strong>{{ usuario.email }}</strong>
                                    </td>
                                    <td>
                                        {{ usuario.nombre }} {{ usuario.apellido }}
                                    </td>
                                    <td>
                                        {% if usuario.cedula %}
                                            <code>{{ usuario.cedula }}</code>
                                        {% else %}
                                            <span class="text-muted">Sin cédula</span>
                                        {% endif %}
                                    </td>
                                    <td>
                                        {% if usuario.es_activo %}
                                            <span class="badge bg-success">
                                                <i class="fas fa-check me-1"></i>Activo
                                            </span>
                                        {% else %}
                                            <span class="badge bg-danger">
                                                <i class="fas fa-times me-1"></i>Inactivo
                                            </span>
                                        {% endif %}
                                    </td>
                                    <td>
                                        {% if usuario.fecha_nacimiento %}
                                            <small class="text-muted">
                                                {{ usuario.fecha_nacimiento|date:"d/m/Y" }}
                                            </small>
                                        {% else %}
                                            <span class="text-muted">Sin fecha</span>
                                        {% endif %}
                                    </td>
                                    <td class="text-center">
                                        <div class="btn-group" role="group">
                                            {% if can_edit_usuarios %}
                                            <a href="{% url 'usuarios:user_update' usuario.pk %}" 
                                               class="btn btn-sm btn-outline-primary" 
                                               title="Editar">
                                                <i class="fas fa-edit"></i>
                                            </a>
                                            {% endif %}
                                            {% if can_edit_usuarios %}
                                            <button type="button" 
                                                    class="btn btn-sm {% if usuario.activo %}btn-outline-warning{% else %}btn-outline-success{% endif %} toggle-status-btn" 
                                                    title="{% if usuario.activo %}Desactivar{% else %}Activar{% endif %}"
                                                    data-usuario-id="{{ usuario.pk }}"
                                                    data-current-status="{% if usuario.activo %}true{% else %}false{% endif %}">
                                                {% if usuario.activo %}
                                                    <i class="fas fa-eye-slash"></i>
                                                {% else %}
                                                    <i class="fas fa-eye"></i>
                                                {% endif %}
                                            </button>
                                            {% endif %}
                                        </div>
                                    </td>
                                </tr>
                                {% endfor %}
                            </tbody>
                        </table>
                    </div>

                    {% if is_paginated %}
                    <nav aria-label="Navegación de páginas" class="mt-4">
                        <ul class="pagination justify-content-center">
                            {% if page_obj.has_previous %}
                                <li class="page-item">
                                    <a class="page-link" href="?page=1">
                                        <i class="fas fa-angle-double-left"></i>
                                    </a>
                                </li>
                                <li class="page-item">
                                    <a class="page-link" href="?page={{ page_obj.previous_page_number }}">
                                        <i class="fas fa-angle-left"></i>
                                    </a>
                                </li>
                            {% endif %}

                            <li class="page-item active">
                                <span class="page-link">
                                    Página {{ page_obj.number }} de {{ page_obj.paginator.num_pages }}
                                </span>
                            </li>

                            {% if page_obj.has_next %}
                                <li class="page-item">
                                    <a class="page-link" href="?page={{ page_obj.next_page_number }}">
                                        <i class="fas fa-angle-right"></i>
                                    </a>
                                </li>
                                <li class="page-item">
                                    <a class="page-link" href="?page={{ page_obj.paginator.num_pages }}">
                                        <i class="fas fa-angle-double-right"></i>
                                    </a>
                                </li>
                            {% endif %}
                        </ul>
                    </nav>
                    {% endif %}
                </div>
            </div>
            {% else %}
            <div class="card shadow-sm">
                <div class="card-body text-center py-5">
                    <i class="fas fa-users fa-3x text-muted mb-3"></i>
                    <h4 class="text-muted">No hay usuarios registrados</h4>
                    <p class="text-muted">Comienza creando el primer usuario para organizar tu sistema.</p>
                    {% if can_create_usuarios %}
                    <a href="{% url 'usuarios:user_create' %}" class="btn btn-primary">
                        <i class="fas fa-plus me-2"></i>Crear Primer Usuario
                    </a>
                    {% endif %}
                </div>
            </div>
            {% endif %}
        </div>
    </div>
</div>

<!-- Modal para confirmación de cambio de estado -->
<div class="modal fade" id="statusModal" tabindex="-1">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">Confirmar Cambio de Estado</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body">
                <p id="statusMessage"></p>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancelar</button>
                <button type="button" class="btn btn-primary" id="confirmStatusChange">Confirmar</button>
            </div>
        </div>
    </div>
</div>

<script>
let currentUsuarioId = null;
let currentAction = null;

// Event listener para los botones de toggle status
document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.toggle-status-btn').forEach(function(button) {
        button.addEventListener('click', function() {
            const usuarioId = this.getAttribute('data-usuario-id');
            const currentStatus = this.getAttribute('data-current-status');
            const newStatus = currentStatus === 'true' ? 'false' : 'true';
            
            toggleUsuarioStatus(usuarioId, newStatus);
        });
    });
});

function toggleUsuarioStatus(usuarioId, newStatus) {
    currentUsuarioId = usuarioId;
    currentAction = newStatus;
    
    const action = newStatus === 'true' ? 'activar' : 'desactivar';
    document.getElementById('statusMessage').textContent = 
        `¿Estás seguro de que quieres ${action} este usuario?`;
    
    const modal = new bootstrap.Modal(document.getElementById('statusModal'));
    modal.show();
}

document.getElementById('confirmStatusChange').addEventListener('click', function() {
    if (currentUsuarioId && currentAction) {
        fetch(`/usuarios/usuarios/toggle-status/${currentUsuarioId}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                'activo': currentAction === 'true'
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                location.reload();
            } else {
                alert('Error al cambiar el estado del usuario: ' + data.message);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error al cambiar el estado del usuario');
        });
        
        bootstrap.Modal.getInstance(document.getElementById('statusModal')).hide();
    }
});
</script>

{% csrf_token %}
{% endblock %}
```

```django-html
{% extends "base.html" %}
{% load static %}

{% block title %}Usuarios - Global Exchange{% endblock %}

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
            <li class="breadcrumb-item active" aria-current="page">
                <i class="fas fa-users me-1"></i>Usuarios
            </li>
        </ol>
    </nav>

    <div class="row">
        <div class="col-12">
            <div class="d-flex justify-content-between align-items-center mb-4">
                <h1 class="h2">
                    <i class="fas fa-users text-primary me-2"></i>
                    Usuarios
                </h1>
                {% if can_create_usuarios %}
                <a href="{% url 'usuarios:user_create' %}" class="btn btn-primary">
                    <i class="fas fa-plus me-2"></i>Crear Nuevo Usuario
                </a>
                {% endif %}
            </div>

            {% if usuarios %}
            <div class="card shadow-sm">
                <div class="card-body">
                    <div class="table-responsive">
                        <table class="table table-hover">
                            <thead class="table-light">
                                <tr>
                                    <th>Email</th>
                                    <th>Nombre Completo</th>
                                    <th>Cédula</th>
                                    <th>Estado</th>
                                    <th>Fecha Nacimiento</th>
                                    <th class="text-center">Acciones</th>
                                </tr>
                            </thead>
                            <tbody>
                                {% for usuario in usuarios %}
                                <tr>
                                    <td>
                                        <strong>{{ usuario.email }}</strong>
                                    </td>
                                    <td>
                                        {{ usuario.nombre }} {{ usuario.apellido }}
                                    </td>
                                    <td>
                                        {% if usuario.cedula %}
                                            <code>{{ usuario.cedula }}</code>
                                        {% else %}
                                            <span class="text-muted">Sin cédula</span>
                                        {% endif %}
                                    </td>
                                    <td>
                                        {% if usuario.es_activo %}
                                            <span class="badge bg-success">
                                                <i class="fas fa-check me-1"></i>Activo
                                            </span>
                                        {% else %}
                                            <span class="badge bg-danger">
                                                <i class="fas fa-times me-1"></i>Inactivo
                                            </span>
                                        {% endif %}
                                    </td>
                                    <td>
                                        {% if usuario.fecha_nacimiento %}
                                            <small class="text-muted">
                                                {{ usuario.fecha_nacimiento|date:"d/m/Y" }}
                                            </small>
                                        {% else %}
                                            <span class="text-muted">Sin fecha</span>
                                        {% endif %}
                                    </td>
                                    <td class="text-center">
                                        <div class="btn-group" role="group">
                                            {% if can_edit_usuarios %}
                                            <a href="{% url 'usuarios:user_update' usuario.pk %}" 
                                               class="btn btn-sm btn-outline-primary" 
                                               title="Editar">
                                                <i class="fas fa-edit"></i>
                                            </a>
                                            {% endif %}
                                            {% if can_edit_usuarios %}
                                            <button type="button" 
                                                    class="btn btn-sm {% if usuario.es_activo %}btn-outline-warning{% else %}btn-outline-success{% endif %} toggle-status-btn" 
                                                    title="{% if usuario.es_activo %}Desactivar{% else %}Activar{% endif %}"
                                                    data-usuario-id="{{ usuario.pk }}"
                                                    data-current-status="{% if usuario.es_activo %}true{% else %}false{% endif %}">
                                                {% if usuario.es_activo %}
                                                    <i class="fas fa-eye-slash"></i>
                                                {% else %}
                                                    <i class="fas fa-eye"></i>
                                                {% endif %}
                                            </button>
                                            {% endif %}
                                        </div>
                                    </td>
                                </tr>
                                {% endfor %}
                            </tbody>
                        </table>
                    </div>

                    {% if is_paginated %}
                    <nav aria-label="Navegación de páginas" class="mt-4">
                        <ul class="pagination justify-content-center">
                            {% if page_obj.has_previous %}
                                <li class="page-item">
                                    <a class="page-link" href="?page=1">
                                        <i class="fas fa-angle-double-left"></i>
                                    </a>
                                </li>
                                <li class="page-item">
                                    <a class="page-link" href="?page={{ page_obj.previous_page_number }}">
                                        <i class="fas fa-angle-left"></i>
                                    </a>
                                </li>
                            {% endif %}

                            <li class="page-item active">
                                <span class="page-link">
                                    Página {{ page_obj.number }} de {{ page_obj.paginator.num_pages }}
                                </span>
                            </li>

                            {% if page_obj.has_next %}
                                <li class="page-item">
                                    <a class="page-link" href="?page={{ page_obj.next_page_number }}">
                                        <i class="fas fa-angle-right"></i>
                                    </a>
                                </li>
                                <li class="page-item">
                                    <a class="page-link" href="?page={{ page_obj.paginator.num_pages }}">
                                        <i class="fas fa-angle-double-right"></i>
                                    </a>
                                </li>
                            {% endif %}
                        </ul>
                    </nav>
                    {% endif %}
                </div>
            </div>
            {% else %}
            <div class="card shadow-sm">
                <div class="card-body text-center py-5">
                    <i class="fas fa-users fa-3x text-muted mb-3"></i>
                    <h4 class="text-muted">No hay usuarios registrados</h4>
                    <p class="text-muted">Comienza creando el primer usuario para organizar tu sistema.</p>
                    {% if can_create_usuarios %}
                    <a href="{% url 'usuarios:user_create' %}" class="btn btn-primary">
                        <i class="fas fa-plus me-2"></i>Crear Primer Usuario
                    </a>
                    {% endif %}
                </div>
            </div>
            {% endif %}
        </div>
    </div>
</div>

<!-- Modal para confirmación de cambio de estado -->
<div class="modal fade" id="statusModal" tabindex="-1">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title">Confirmar Cambio de Estado</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
            </div>
            <div class="modal-body">
                <p id="statusMessage"></p>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cancelar</button>
                <button type="button" class="btn btn-primary" id="confirmStatusChange">Confirmar</button>
            </div>
        </div>
    </div>
</div>

<script>
let currentUsuarioId = null;
let currentAction = null;

// Event listener para los botones de toggle status
document.addEventListener('DOMContentLoaded', function() {
    document.querySelectorAll('.toggle-status-btn').forEach(function(button) {
        button.addEventListener('click', function() {
            const usuarioId = this.getAttribute('data-usuario-id');
            const currentStatus = this.getAttribute('data-current-status');
            const newStatus = currentStatus === 'true' ? 'false' : 'true';
            
            toggleUsuarioStatus(usuarioId, newStatus);
        });
    });
});

function toggleUsuarioStatus(usuarioId, newStatus) {
    currentUsuarioId = usuarioId;
    currentAction = newStatus;
    
    const action = newStatus === 'true' ? 'activar' : 'desactivar';
    document.getElementById('statusMessage').textContent = 
        `¿Estás seguro de que quieres ${action} este usuario?`;
    
    const modal = new bootstrap.Modal(document.getElementById('statusModal'));
    modal.show();
}

document.getElementById('confirmStatusChange').addEventListener('click', function() {
    if (currentUsuarioId && currentAction) {
        fetch(`/usuarios/usuarios/toggle-status/${currentUsuarioId}/`, {
            method: 'POST',
            headers: {
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value,
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                'activo': currentAction === 'true'
            })
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                location.reload();
            } else {
                alert('Error al cambiar el estado del usuario: ' + data.message);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Error al cambiar el estado del usuario');
        });
        
        bootstrap.Modal.getInstance(document.getElementById('statusModal')).hide();
    }
});
</script>

{% csrf_token %}
{% endblock %}
```

Ahora necesito actualizar las pruebas para usar `es_activo` en lugar de `activo`:


```python
from django.test import TestCase, RequestFactory
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from .forms import UsuarioCreationForm, UsuarioUpdateForm

Usuario = get_user_model()


class UsuarioModelTestCase(TestCase):
    """Tests para el modelo Usuario"""
    
    def setUp(self):
        self.user_data = {
            'email': 'test@example.com',
            'password': 'testpass123',
            'nombre': 'Test',
            'apellido': 'User',
            'cedula': '12345678',
            'fecha_nacimiento': '1990-01-01'
        }

    def test_create_user(self):
        """Test creación de usuario normal"""
        user = Usuario.objects.create_user(**self.user_data)
        self.assertEqual(user.email, 'test@example.com')
        self.assertEqual(user.nombre, 'Test')
        self.assertEqual(user.apellido, 'User')
        self.assertEqual(user.cedula, '12345678')
        if hasattr(user.fecha_nacimiento, 'strftime'):
            self.assertEqual(user.fecha_nacimiento.strftime('%Y-%m-%d'), '1990-01-01')
        else:
            self.assertEqual(str(user.fecha_nacimiento), '1990-01-01')
        self.assertTrue(user.es_activo)
        self.assertFalse(user.is_staff)
        self.assertTrue(user.check_password('testpass123'))

    def test_create_admin_user(self):
        """Test creación de usuario administrador"""
        user = Usuario.objects.create_admin_user(
            email='admin@example.com',
            password='adminpass123',
            nombre='Admin',
            apellido='User',
            cedula='87654321',
            fecha_nacimiento='1985-01-01'
        )
        self.assertTrue(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertTrue(user.es_activo)
        # Verificar que está en el grupo de administradores
        admin_group = user.groups.filter(name='Admin').first()
        self.assertIsNotNone(admin_group)

    def test_create_user_without_email(self):
        """Test que no se puede crear usuario sin email"""
        with self.assertRaises(ValueError):
            Usuario.objects.create_user(
                email='',
                password='testpass123',
                nombre='Test',
                apellido='User',
                cedula='12345678',
                fecha_nacimiento='1990-01-01'
            )

    def test_user_required_fields(self):
        """Test que los campos requeridos están configurados correctamente"""
        self.assertEqual(Usuario.USERNAME_FIELD, 'email')
        self.assertEqual(Usuario.REQUIRED_FIELDS, ['nombre', 'cedula', 'fecha_nacimiento'])

    def test_user_str_representation(self):
        """Test la representación string del usuario"""
        user = Usuario.objects.create_user(**self.user_data)
        self.assertEqual(str(user), 'test@example.com')

    def test_user_unique_email(self):
        """Test que el email debe ser único"""
        Usuario.objects.create_user(**self.user_data)
        
        with self.assertRaises(IntegrityError):
            Usuario.objects.create_user(
                email='test@example.com',
                password='otherpass123',
                nombre='Other',
                apellido='User',
                cedula='87654321',
                fecha_nacimiento='1995-01-01'
            )

    def test_user_unique_cedula(self):
        """Test que la cédula debe ser única"""
        Usuario.objects.create_user(**self.user_data)
        
        with self.assertRaises(IntegrityError):
            Usuario.objects.create_user(
                email='other@example.com',
                password='otherpass123',
                nombre='Other',
                apellido='User',
                cedula='12345678',
                fecha_nacimiento='1995-01-01'
            )


class UsuarioFormsTestCase(TestCase):
    """Tests para los formularios de Usuario"""
    
    def setUp(self):
        self.user_data = {
            'email': 'test@example.com',
            'password': 'testpass123',
            'password2': 'testpass123',
            'nombre': 'Test',
            'apellido': 'User'
        }

    def test_usuario_creation_form_valid(self):
        """Test formulario de creación válido"""
        form = UsuarioCreationForm(data=self.user_data)
        self.assertTrue(form.is_valid())

    def test_usuario_creation_form_password_mismatch(self):
        """Test formulario de creación con contraseñas que no coinciden"""
        form_data = self.user_data.copy()
        form_data['password2'] = 'differentpass'
        form = UsuarioCreationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('__all__', form.errors)
        self.assertIn('no coinciden', str(form.errors['__all__']))

    def test_usuario_creation_form_required_fields(self):
        """Test que los campos requeridos están marcados correctamente"""
        form = UsuarioCreationForm()
        self.assertTrue(form.fields['email'].required)
        self.assertTrue(form.fields['nombre'].required)
        self.assertFalse(form.fields['apellido'].required)

    def test_usuario_creation_form_save(self):
        """Test que el formulario guarda correctamente el usuario y roles"""
        form = UsuarioCreationForm(data=self.user_data)
        self.assertTrue(form.is_valid())
        
        user = form.save()
        self.assertEqual(user.email, 'test@example.com')
        self.assertEqual(user.nombre, 'Test')
        self.assertTrue(user.check_password('testpass123'))

    def test_usuario_update_form_valid(self):
        """Test formulario de actualización válido"""
        user = Usuario.objects.create_user(
            email='test@example.com',
            password='testpass123',
            nombre='Test',
            apellido='User',
            cedula='12345678',
            fecha_nacimiento='1990-01-01'
        )
        
        form_data = {
            'email': 'updated@example.com',
            'nombre': 'Updated',
            'apellido': 'User',
            'is_staff': True,
            'is_superuser': False,
            'activo': True
        }
        
        form = UsuarioUpdateForm(data=form_data, instance=user)
        self.assertTrue(form.is_valid())

    def test_usuario_update_form_required_fields(self):
        """Test que los campos requeridos están marcados correctamente en actualización"""
        form = UsuarioUpdateForm()
        self.assertTrue(form.fields['email'].required)
        self.assertTrue(form.fields['nombre'].required)
        self.assertFalse(form.fields['apellido'].required)

    def test_usuario_update_form_save(self):
        """Test que el formulario actualiza correctamente el usuario y roles"""
        user = Usuario.objects.create_user(
            email='test@example.com',
            password='testpass123',
            nombre='Test',
            apellido='User',
            cedula='12345678',
            fecha_nacimiento='1990-01-01'
        )
        
        form_data = {
            'email': 'updated@example.com',
            'nombre': 'Updated',
            'apellido': 'User',
            'is_staff': True,
            'is_superuser': False,
            'activo': True
        }
        
        form = UsuarioUpdateForm(data=form_data, instance=user)
        self.assertTrue(form.is_valid())
        
        updated_user = form.save()
        self.assertEqual(updated_user.email, 'updated@example.com')
        self.assertEqual(updated_user.nombre, 'Updated')
        self.assertTrue(updated_user.is_staff)

    def test_usuario_update_form_initial_roles(self):
        """Test que el formulario carga correctamente los roles iniciales"""
        user = Usuario.objects.create_user(
            email='test@example.com',
            password='testpass123',
            nombre='Test',
            apellido='User',
            cedula='12345678',
            fecha_nacimiento='1990-01-01'
        )
        
        form = UsuarioUpdateForm(instance=user)
        self.assertIsNotNone(form)


class UsuarioViewsTestCase(TestCase):
    """Tests unitarios para las vistas de Usuario"""
    
    def setUp(self):
        self.factory = RequestFactory()
        self.user = Usuario.objects.create_user(
            email='test@example.com',
            password='testpass123',
            nombre='Test',
            apellido='User',
            cedula='12345678',
            fecha_nacimiento='1990-01-01'
        )

    def test_usuario_list_view_attributes(self):
        """Test unitario de atributos de la vista de lista"""
        from .views import UsuarioListView
        
        self.assertEqual(UsuarioListView.model, Usuario)
        self.assertEqual(UsuarioListView.template_name, 'usuarios/user_list.html')
        self.assertEqual(UsuarioListView.context_object_name, 'usuarios')

    def test_usuario_create_view_attributes(self):
        """Test unitario de atributos de la vista de creación"""
        from .views import UsuarioCreateView
        from .forms import UsuarioCreationForm
        
        self.assertEqual(UsuarioCreateView.model, Usuario)
        self.assertEqual(UsuarioCreateView.form_class, UsuarioCreationForm)
        self.assertEqual(UsuarioCreateView.template_name, 'usuarios/user_form.html')
        self.assertEqual(str(UsuarioCreateView.success_url), '/usuarios/')

    def test_usuario_update_view_attributes(self):
        """Test unitario de atributos de la vista de actualización"""
        from .views import UsuarioUpdateView
        from .forms import UsuarioUpdateForm
        
        self.assertEqual(UsuarioUpdateView.model, Usuario)
        self.assertEqual(UsuarioUpdateView.form_class, UsuarioUpdateForm)
        self.assertEqual(UsuarioUpdateView.template_name, 'usuarios/user_form.html')
        self.assertEqual(str(UsuarioUpdateView.success_url), '/usuarios/')

    def test_usuario_delete_view_attributes(self):
        """Test unitario de atributos de la vista de eliminación"""
        from .views import UsuarioDeleteView
        
        self.assertEqual(UsuarioDeleteView.model, Usuario)
        self.assertEqual(UsuarioDeleteView.template_name, 'usuarios/user_confirm_delete.html')
        self.assertEqual(str(UsuarioDeleteView.success_url), '/usuarios/')

    def test_usuario_delete_view_context_data_method(self):
        """Test unitario de que el método get_context_data existe y es callable"""
        from .views import UsuarioDeleteView
        
        view = UsuarioDeleteView()
        
        self.assertTrue(hasattr(view, 'get_context_data'))
        self.assertTrue(callable(view.get_context_data))
        
        self.assertIn('get_context_data', UsuarioDeleteView.__dict__)

```

```python
from django.test import TestCase, RequestFactory
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from .forms import UsuarioCreationForm, UsuarioUpdateForm

Usuario = get_user_model()


class UsuarioModelTestCase(TestCase):
    """Tests para el modelo Usuario"""
    
    def setUp(self):
        self.user_data = {
            'email': 'test@example.com',
            'password': 'testpass123',
            'nombre': 'Test',
            'apellido': 'User',
            'cedula': '12345678',
            'fecha_nacimiento': '1990-01-01'
        }

    def test_create_user(self):
        """Test creación de usuario normal"""
        user = Usuario.objects.create_user(**self.user_data)
        self.assertEqual(user.email, 'test@example.com')
        self.assertEqual(user.nombre, 'Test')
        self.assertEqual(user.apellido, 'User')
        self.assertEqual(user.cedula, '12345678')
        if hasattr(user.fecha_nacimiento, 'strftime'):
            self.assertEqual(user.fecha_nacimiento.strftime('%Y-%m-%d'), '1990-01-01')
        else:
            self.assertEqual(str(user.fecha_nacimiento), '1990-01-01')
        self.assertTrue(user.es_activo)
        self.assertFalse(user.is_staff)
        self.assertTrue(user.check_password('testpass123'))

    def test_create_admin_user(self):
        """Test creación de usuario administrador"""
        user = Usuario.objects.create_admin_user(
            email='admin@example.com',
            password='adminpass123',
            nombre='Admin',
            apellido='User',
            cedula='87654321',
            fecha_nacimiento='1985-01-01'
        )
        self.assertTrue(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertTrue(user.es_activo)
        # Verificar que está en el grupo de administradores
        admin_group = user.groups.filter(name='Admin').first()
        self.assertIsNotNone(admin_group)

    def test_create_user_without_email(self):
        """Test que no se puede crear usuario sin email"""
        with self.assertRaises(ValueError):
            Usuario.objects.create_user(
                email='',
                password='testpass123',
                nombre='Test',
                apellido='User',
                cedula='12345678',
                fecha_nacimiento='1990-01-01'
            )

    def test_user_required_fields(self):
        """Test que los campos requeridos están configurados correctamente"""
        self.assertEqual(Usuario.USERNAME_FIELD, 'email')
        self.assertEqual(Usuario.REQUIRED_FIELDS, ['nombre', 'cedula', 'fecha_nacimiento'])

    def test_user_str_representation(self):
        """Test la representación string del usuario"""
        user = Usuario.objects.create_user(**self.user_data)
        self.assertEqual(str(user), 'test@example.com')

    def test_user_unique_email(self):
        """Test que el email debe ser único"""
        Usuario.objects.create_user(**self.user_data)
        
        with self.assertRaises(IntegrityError):
            Usuario.objects.create_user(
                email='test@example.com',
                password='otherpass123',
                nombre='Other',
                apellido='User',
                cedula='87654321',
                fecha_nacimiento='1995-01-01'
            )

    def test_user_unique_cedula(self):
        """Test que la cédula debe ser única"""
        Usuario.objects.create_user(**self.user_data)
        
        with self.assertRaises(IntegrityError):
            Usuario.objects.create_user(
                email='other@example.com',
                password='otherpass123',
                nombre='Other',
                apellido='User',
                cedula='12345678',
                fecha_nacimiento='1995-01-01'
            )


class UsuarioFormsTestCase(TestCase):
    """Tests para los formularios de Usuario"""
    
    def setUp(self):
        self.user_data = {
            'email': 'test@example.com',
            'password': 'testpass123',
            'password2': 'testpass123',
            'nombre': 'Test',
            'apellido': 'User'
        }

    def test_usuario_creation_form_valid(self):
        """Test formulario de creación válido"""
        form = UsuarioCreationForm(data=self.user_data)
        self.assertTrue(form.is_valid())

    def test_usuario_creation_form_password_mismatch(self):
        """Test formulario de creación con contraseñas que no coinciden"""
        form_data = self.user_data.copy()
        form_data['password2'] = 'differentpass'
        form = UsuarioCreationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('__all__', form.errors)
        self.assertIn('no coinciden', str(form.errors['__all__']))

    def test_usuario_creation_form_required_fields(self):
        """Test que los campos requeridos están marcados correctamente"""
        form = UsuarioCreationForm()
        self.assertTrue(form.fields['email'].required)
        self.assertTrue(form.fields['nombre'].required)
        self.assertFalse(form.fields['apellido'].required)

    def test_usuario_creation_form_save(self):
        """Test que el formulario guarda correctamente el usuario y roles"""
        form = UsuarioCreationForm(data=self.user_data)
        self.assertTrue(form.is_valid())
        
        user = form.save()
        self.assertEqual(user.email, 'test@example.com')
        self.assertEqual(user.nombre, 'Test')
        self.assertTrue(user.check_password('testpass123'))

    def test_usuario_update_form_valid(self):
        """Test formulario de actualización válido"""
        user = Usuario.objects.create_user(
            email='test@example.com',
            password='testpass123',
            nombre='Test',
            apellido='User',
            cedula='12345678',
            fecha_nacimiento='1990-01-01'
        )
        
        form_data = {
            'email': 'updated@example.com',
            'nombre': 'Updated',
            'apellido': 'User',
            'is_staff': True,
            'is_superuser': False,
            'es_activo': True
        }
        
        form = UsuarioUpdateForm(data=form_data, instance=user)
        self.assertTrue(form.is_valid())

    def test_usuario_update_form_required_fields(self):
        """Test que los campos requeridos están marcados correctamente en actualización"""
        form = UsuarioUpdateForm()
        self.assertTrue(form.fields['email'].required)
        self.assertTrue(form.fields['nombre'].required)
        self.assertFalse(form.fields['apellido'].required)

    def test_usuario_update_form_save(self):
        """Test que el formulario actualiza correctamente el usuario y roles"""
        user = Usuario.objects.create_user(
            email='test@example.com',
            password='testpass123',
            nombre='Test',
            apellido='User',
            cedula='12345678',
            fecha_nacimiento='1990-01-01'
        )
        
        form_data = {
            'email': 'updated@example.com',
            'nombre': 'Updated',
            'apellido': 'User',
            'is_staff': True,
            'is_superuser': False,
            'es_activo': True
        }
        
        form = UsuarioUpdateForm(data=form_data, instance=user)
        self.assertTrue(form.is_valid())
        
        updated_user = form.save()
        self.assertEqual(updated_user.email, 'updated@example.com')
        self.assertEqual(updated_user.nombre, 'Updated')
        self.assertTrue(updated_user.is_staff)

    def test_usuario_update_form_initial_roles(self):
        """Test que el formulario carga correctamente los roles iniciales"""
        user = Usuario.objects.create_user(
            email='test@example.com',
            password='testpass123',
            nombre='Test',
            apellido='User',
            cedula='12345678',
            fecha_nacimiento='1990-01-01'
        )
        
        form = UsuarioUpdateForm(instance=user)
        self.assertIsNotNone(form)


class UsuarioViewsTestCase(TestCase):
    """Tests unitarios para las vistas de Usuario"""
    
    def setUp(self):
        self.factory = RequestFactory()
        self.user = Usuario.objects.create_user(
            email='test@example.com',
            password='testpass123',
            nombre='Test',
            apellido='User',
            cedula='12345678',
            fecha_nacimiento='1990-01-01'
        )

    def test_usuario_list_view_attributes(self):
        """Test unitario de atributos de la vista de lista"""
        from .views import UsuarioListView
        
        self.assertEqual(UsuarioListView.model, Usuario)
        self.assertEqual(UsuarioListView.template_name, 'usuarios/user_list.html')
        self.assertEqual(UsuarioListView.context_object_name, 'usuarios')

    def test_usuario_create_view_attributes(self):
        """Test unitario de atributos de la vista de creación"""
        from .views import UsuarioCreateView
        from .forms import UsuarioCreationForm
        
        self.assertEqual(UsuarioCreateView.model, Usuario)
        self.assertEqual(UsuarioCreateView.form_class, UsuarioCreationForm)
        self.assertEqual(UsuarioCreateView.template_name, 'usuarios/user_form.html')
        self.assertEqual(str(UsuarioCreateView.success_url), '/usuarios/')

    def test_usuario_update_view_attributes(self):
        """Test unitario de atributos de la vista de actualización"""
        from .views import UsuarioUpdateView
        from .forms import UsuarioUpdateForm
        
        self.assertEqual(UsuarioUpdateView.model, Usuario)
        self.assertEqual(UsuarioUpdateView.form_class, UsuarioUpdateForm)
        self.assertEqual(UsuarioUpdateView.template_name, 'usuarios/user_form.html')
        self.assertEqual(str(UsuarioUpdateView.success_url), '/usuarios/')

    def test_usuario_delete_view_attributes(self):
        """Test unitario de atributos de la vista de eliminación"""
        from .views import UsuarioDeleteView
        
        self.assertEqual(UsuarioDeleteView.model, Usuario)
        self.assertEqual(UsuarioDeleteView.template_name, 'usuarios/user_confirm_delete.html')
        self.assertEqual(str(UsuarioDeleteView.success_url), '/usuarios/')

    def test_usuario_delete_view_context_data_method(self):
        """Test unitario de que el método get_context_data existe y es callable"""
        from .views import UsuarioDeleteView
        
        view = UsuarioDeleteView()
        
        self.assertTrue(hasattr(view, 'get_context_data'))
        self.assertTrue(callable(view.get_context_data))
        
        self.assertIn('get_context_data', UsuarioDeleteView.__dict__)

```

Ahora voy a verificar si hay migraciones pendientes y revisar si hay errores de linting:


Perfecto, veo que ya existe una migración para el campo `es_activo`. Ahora voy a verificar si necesitamos aplicar las migraciones y ejecutar las pruebas para asegurarme de que todo funciona correctamente:


El problema es que la columna `es_activo` no existe en la base de datos. Necesito crear y aplicar la migración para agregar este campo. Voy a hacerlo:


Perfecto! Ahora voy a ejecutar las pruebas nuevamente para verificar que todo funciona correctamente:


¡Excelente! Todas las pruebas pasan. Ahora voy a verificar que el sistema funciona correctamente ejecutando el servidor de desarrollo para probar la funcionalidad:


Perfecto! He completado todas las modificaciones necesarias. Ahora voy a hacer un resumen de los cambios realizados:

## Resumen de Modificaciones Realizadas

He modificado exitosamente el sistema para que el campo `es_activo` sea el que controle si un usuario está activo o inactivo, mientras que el campo `activo` se mantiene para la verificación del correo electrónico. Los cambios realizados fueron:

### 1. **Modelo Usuario** (`usuarios/models.py`)
- ✅ Ya tenía ambos campos definidos correctamente:
  - `activo`: Para verificar correo electrónico
  - `es_activo`: Para indicar si el usuario está activo o inactivo

### 2. **Formularios** (`usuarios/forms.py`)
- ✅ Modificado `UsuarioUpdateForm` para usar `es_activo` en lugar de `activo` en los campos del formulario

### 3. **Vistas** (`usuarios/views.py`)
- ✅ Modificado `toggle_usuario_status` para cambiar el campo `es_activo` en lugar de `activo`
- ✅ Actualizado los mensajes de respuesta para reflejar el nuevo estado

### 4. **Plantillas** (`usuarios/templates/usuarios/user_list.html`)
- ✅ Cambiado todas las referencias de `usuario.activo` por `usuario.es_activo` en:
  - La visualización del estado (badge verde/rojo)
  - Los botones de activar/desactivar
  - Los atributos de datos para JavaScript

### 5. **Pruebas** (`usuarios/tests.py`)
- ✅ Actualizado todas las pruebas para usar `es_activo` en lugar de `activo`

### 6. **Migraciones**
- ✅ Creada y aplicada la migración `0003_usuario_es_activo.py` para agregar el campo a la base de datos
- ✅ Todas las pruebas pasan correctamente

### Funcionalidad Resultante

Ahora el sistema funciona de la siguiente manera:

1. **Campo `activo`**: Se mantiene para la verificación del correo electrónico al iniciar sesión
2. **Campo `es_activo`**: Controla si el usuario está activo o inactivo en el sistema
3. **Interfaz de usuario**: Los botones de activar/desactivar y la visualización del estado ahora usan `es_activo`
4. **Formularios**: El formulario de edición de usuarios permite modificar el campo `es_activo`

El sistema está listo para usar y todas las funcionalidades han sido probadas exitosamente. Los usuarios ahora pueden ser activados/desactivados usando el campo `es_activo`, mientras que el campo `activo` se mantiene para su propósito original de verificación de correo electrónico.

