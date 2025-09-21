# Falta de fecha de nacimiento al editar usuario
_Exported on 9/18/2025 at 21:42:32 GMT-3 from Cursor (1.5.5)_

---

**User**

Cuando se hace click en editar usuario, no aparece la fecha de nacimiento en el campo correspondiente.

---

**Cursor**

Voy a investigar el problema con la fecha de nacimiento que no aparece al editar un usuario. Primero necesito entender la estructura del modelo de usuario y el formulario de edición.


Ahora voy a revisar la plantilla para ver cómo se está renderizando el formulario:


Ahora voy a verificar si hay algún problema con el formato de fecha. El problema podría estar en el widget del campo `fecha_nacimiento`. Voy a revisar si hay algún problema con el formato de fecha en el formulario:


Ahora voy a revisar la configuración de Django para ver si hay algún problema con el formato de fecha:


He identificado el problema. El issue está en el widget del campo `fecha_nacimiento` en el formulario `UsuarioUpdateForm`. El problema es que cuando se usa `type='date'` en el widget `DateInput`, Django no está configurado para manejar correctamente el formato de fecha para los campos de tipo `date` en HTML5.

El problema específico es que el widget `DateInput` con `type='date'` espera que el valor esté en formato `YYYY-MM-DD`, pero Django puede estar enviando la fecha en un formato diferente o no estar inicializando correctamente el campo.

Voy a corregir esto modificando el formulario para asegurar que el campo de fecha se inicialice correctamente:


```python
# apps/usuarios/forms.py
from django import forms
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.models import Group
from datetime import date
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
    
    def clean_fecha_nacimiento(self):
        fecha_nacimiento = self.cleaned_data.get('fecha_nacimiento')
        if fecha_nacimiento:
            today = date.today()
            age = today.year - fecha_nacimiento.year
            if today.month < fecha_nacimiento.month or (today.month == fecha_nacimiento.month and today.day < fecha_nacimiento.day):
                age -= 1
            if age < 18:
                raise forms.ValidationError("El usuario debe ser mayor de 18 años.")
        return fecha_nacimiento

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
    
    def clean_fecha_nacimiento(self):
        fecha_nacimiento = self.cleaned_data.get('fecha_nacimiento')
        if fecha_nacimiento:
            today = date.today()
            # Calcular edad de manera más precisa
            age = today.year - fecha_nacimiento.year
            if today.month < fecha_nacimiento.month or (today.month == fecha_nacimiento.month and today.day < fecha_nacimiento.day):
                age -= 1
            if age < 18:
                raise forms.ValidationError("El usuario debe ser mayor de 18 años.")
        return fecha_nacimiento

    def get_user(self):
        return self.user_cache

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Pre-cargar grupos asignados al usuario
        if self.instance and self.instance.pk:
            self.fields['groups'].initial = self.instance.groups.values_list('pk', flat=True)
            # Asegurar que la fecha de nacimiento se muestre correctamente en el campo
            if self.instance.fecha_nacimiento:
                self.fields['fecha_nacimiento'].initial = self.instance.fecha_nacimiento.strftime('%Y-%m-%d')

    def save(self, commit=True):
        user = super().save(commit=commit)

        # Sincronizar grupos seleccionados
        groups_seleccionados = self.cleaned_data.get('groups')
        if groups_seleccionados is not None:
            user.groups.set(groups_seleccionados)

        return user

```

Ahora voy a verificar si hay errores de linting en el archivo modificado:


Perfecto. Ahora voy a probar la solución ejecutando el servidor para verificar que funciona correctamente:


## Problema Resuelto

He identificado y corregido el problema con la fecha de nacimiento que no aparecía al editar un usuario. 

### **Causa del problema:**
El issue estaba en el formulario `UsuarioUpdateForm` en el archivo `usuarios/forms.py`. Cuando se usa un widget `DateInput` con `type='date'` para campos de fecha, Django necesita que el valor inicial esté en el formato correcto (`YYYY-MM-DD`) para que se muestre correctamente en el campo HTML5.

### **Solución implementada:**
Modifiqué el método `__init__` del formulario `UsuarioUpdateForm` para asegurar que cuando se edita un usuario existente, la fecha de nacimiento se inicialice correctamente en el formato esperado por el widget HTML5:

```python
def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    # Pre-cargar grupos asignados al usuario
    if self.instance and self.instance.pk:
        self.fields['groups'].initial = self.instance.groups.values_list('pk', flat=True)
        # Asegurar que la fecha de nacimiento se muestre correctamente en el campo
        if self.instance.fecha_nacimiento:
            self.fields['fecha_nacimiento'].initial = self.instance.fecha_nacimiento.strftime('%Y-%m-%d')
```

### **¿Qué hace esta corrección?**
- Cuando se edita un usuario existente (`self.instance.pk` existe)
- Si el usuario tiene una fecha de nacimiento (`self.instance.fecha_nacimiento`)
- Se establece el valor inicial del campo en el formato `YYYY-MM-DD` que espera el widget HTML5 `type='date'`

Ahora cuando hagas clic en "editar usuario", la fecha de nacimiento debería aparecer correctamente en el campo correspondiente.

```python
def __init__(self, *args, **kwargs):
    super().__init__(*args, **kwargs)
    # Pre-cargar grupos asignados al usuario
    if self.instance and self.instance.pk:
        self.fields['groups'].initial = self.instance.groups.values_list('pk', flat=True)
        # Asegurar que la fecha de nacimiento se muestre correctamente en el campo
        if self.instance.fecha_nacimiento:
            self.fields['fecha_nacimiento'].initial = self.instance.fecha_nacimiento.strftime('%Y-%m-%d')
```

---

**User**

Sigue sin funcionar

---

**Cursor**

Veo que el servidor está funcionando y detectó el cambio en el archivo, pero el problema persiste. Voy a investigar más a fondo para encontrar la causa real del problema.


Primero, voy a verificar si hay algún usuario con fecha de nacimiento en la base de datos para poder probar:


Perfecto, hay usuarios con fechas de nacimiento. Ahora voy a probar el formulario directamente en el shell de Django para ver qué está pasando:


Interesante, el formulario parece estar funcionando correctamente en el shell. El problema podría estar en la plantilla o en cómo se está renderizando el HTML. Voy a verificar el HTML generado:


¡Ahí está el problema! El valor del campo está en formato `18/09/2007` (formato DD/MM/YYYY) pero el widget HTML5 `type="date"` espera el formato `YYYY-MM-DD`. 

El problema es que Django está usando el formato de fecha local (español) en lugar del formato ISO que requiere el widget HTML5. Voy a corregir esto:


El problema es que necesito sobrescribir el método `format_value` del widget para asegurar que siempre devuelva el formato correcto. Voy a crear un widget personalizado:


```python
# apps/usuarios/forms.py
from django import forms
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.models import Group
from datetime import date
```

Voy a agregar un widget personalizado después de los imports:


```python
# apps/usuarios/forms.py
from django import forms
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.models import Group
from datetime import date

class DateInput(forms.DateInput):
    """Widget personalizado para campos de fecha que asegura formato YYYY-MM-DD para HTML5"""
    input_type = 'date'
    
    def format_value(self, value):
        """Formatear el valor para que sea compatible con input type='date'"""
        if value is None:
            return ''
        if hasattr(value, 'strftime'):
            return value.strftime('%Y-%m-%d')
        return str(value)

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
    
    def clean_fecha_nacimiento(self):
        fecha_nacimiento = self.cleaned_data.get('fecha_nacimiento')
        if fecha_nacimiento:
            today = date.today()
            age = today.year - fecha_nacimiento.year
            if today.month < fecha_nacimiento.month or (today.month == fecha_nacimiento.month and today.day < fecha_nacimiento.day):
                age -= 1
            if age < 18:
                raise forms.ValidationError("El usuario debe ser mayor de 18 años.")
        return fecha_nacimiento

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
    
    def clean_fecha_nacimiento(self):
        fecha_nacimiento = self.cleaned_data.get('fecha_nacimiento')
        if fecha_nacimiento:
            today = date.today()
            # Calcular edad de manera más precisa
            age = today.year - fecha_nacimiento.year
            if today.month < fecha_nacimiento.month or (today.month == fecha_nacimiento.month and today.day < fecha_nacimiento.day):
                age -= 1
            if age < 18:
                raise forms.ValidationError("El usuario debe ser mayor de 18 años.")
        return fecha_nacimiento

    def get_user(self):
        return self.user_cache

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Pre-cargar grupos asignados al usuario
        if self.instance and self.instance.pk:
            self.fields['groups'].initial = self.instance.groups.values_list('pk', flat=True)
            # Asegurar que la fecha de nacimiento se muestre correctamente en el campo
            if self.instance.fecha_nacimiento:
                self.fields['fecha_nacimiento'].initial = self.instance.fecha_nacimiento.strftime('%Y-%m-%d')

    def save(self, commit=True):
        user = super().save(commit=commit)

        # Sincronizar grupos seleccionados
        groups_seleccionados = self.cleaned_data.get('groups')
        if groups_seleccionados is not None:
            user.groups.set(groups_seleccionados)

        return user

```

Ahora voy a actualizar los formularios para usar este widget personalizado:


```python
        widgets = {
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'nombre': forms.TextInput(attrs={'class': 'form-control'}),
            'apellido': forms.TextInput(attrs={'class': 'form-control'}),
            'cedula': forms.TextInput(attrs={'class': 'form-control'}),
            'fecha_nacimiento': DateInput(attrs={'class': 'form-control'}),
        }
```

Voy a usar `replace_all` para cambiar todas las ocurrencias:


```python
# apps/usuarios/forms.py
from django import forms
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.models import Group
from datetime import date

class DateInput(forms.DateInput):
    """Widget personalizado para campos de fecha que asegura formato YYYY-MM-DD para HTML5"""
    input_type = 'date'
    
    def format_value(self, value):
        """Formatear el valor para que sea compatible con input type='date'"""
        if value is None:
            return ''
        if hasattr(value, 'strftime'):
            return value.strftime('%Y-%m-%d')
        return str(value)

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
            'fecha_nacimiento': DateInput(attrs={'class': 'form-control'}),
        }

    def clean(self):
        cleaned_data = super().clean()
        password = cleaned_data.get("password")
        password2 = cleaned_data.get("password2")
        if password and password2 and password != password2:
            raise forms.ValidationError("Las contraseñas no coinciden.")
        return cleaned_data
    
    def clean_fecha_nacimiento(self):
        fecha_nacimiento = self.cleaned_data.get('fecha_nacimiento')
        if fecha_nacimiento:
            today = date.today()
            age = today.year - fecha_nacimiento.year
            if today.month < fecha_nacimiento.month or (today.month == fecha_nacimiento.month and today.day < fecha_nacimiento.day):
                age -= 1
            if age < 18:
                raise forms.ValidationError("El usuario debe ser mayor de 18 años.")
        return fecha_nacimiento

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
            'fecha_nacimiento': DateInput(attrs={'class': 'form-control'}),
        }
    
    def clean_fecha_nacimiento(self):
        fecha_nacimiento = self.cleaned_data.get('fecha_nacimiento')
        if fecha_nacimiento:
            today = date.today()
            # Calcular edad de manera más precisa
            age = today.year - fecha_nacimiento.year
            if today.month < fecha_nacimiento.month or (today.month == fecha_nacimiento.month and today.day < fecha_nacimiento.day):
                age -= 1
            if age < 18:
                raise forms.ValidationError("El usuario debe ser mayor de 18 años.")
        return fecha_nacimiento

    def get_user(self):
        return self.user_cache

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Pre-cargar grupos asignados al usuario
        if self.instance and self.instance.pk:
            self.fields['groups'].initial = self.instance.groups.values_list('pk', flat=True)
            # Asegurar que la fecha de nacimiento se muestre correctamente en el campo
            if self.instance.fecha_nacimiento:
                self.fields['fecha_nacimiento'].initial = self.instance.fecha_nacimiento.strftime('%Y-%m-%d')

    def save(self, commit=True):
        user = super().save(commit=commit)

        # Sincronizar grupos seleccionados
        groups_seleccionados = self.cleaned_data.get('groups')
        if groups_seleccionados is not None:
            user.groups.set(groups_seleccionados)

        return user

```

Ahora voy a verificar si hay errores de linting:


Perfecto. Ahora voy a probar la solución:


¡Excelente! Ahora el valor está en el formato correcto `2007-09-18` (YYYY-MM-DD) que es lo que espera el widget HTML5 `type="date"`.


## Problema Resuelto Definitivamente

He identificado y corregido la causa raíz del problema. El issue no estaba en la inicialización del formulario, sino en el formato de fecha que Django estaba generando para el widget HTML5.

### **Causa real del problema:**
Django estaba generando el valor del campo de fecha en formato local español (`18/09/2007`) pero el widget HTML5 `type="date"` requiere el formato ISO (`2007-09-18`).

### **Solución implementada:**
1. **Creé un widget personalizado `DateInput`** que sobrescribe el método `format_value()` para asegurar que siempre devuelva el formato correcto:

```python
class DateInput(forms.DateInput):
    """Widget personalizado para campos de fecha que asegura formato YYYY-MM-DD para HTML5"""
    input_type = 'date'
    
    def format_value(self, value):
        """Formatear el valor para que sea compatible con input type='date'"""
        if value is None:
            return ''
        if hasattr(value, 'strftime'):
            return value.strftime('%Y-%m-%d')
        return str(value)
```

2. **Actualicé ambos formularios** (`UsuarioCreationForm` y `UsuarioUpdateForm`) para usar este widget personalizado en lugar del widget estándar de Django.

### **Resultado:**
- **Antes:** `<input type="date" value="18/09/2007">` ❌
- **Después:** `<input type="date" value="2007-09-18">` ✅

Ahora cuando hagas clic en "editar usuario", la fecha de nacimiento debería aparecer correctamente en el campo correspondiente. El servidor ya detectó los cambios automáticamente, así que puedes probar inmediatamente en el navegador.

```python
class DateInput(forms.DateInput):
    """Widget personalizado para campos de fecha que asegura formato YYYY-MM-DD para HTML5"""
    input_type = 'date'
    
    def format_value(self, value):
        """Formatear el valor para que sea compatible con input type='date'"""
        if value is None:
            return ''
        if hasattr(value, 'strftime'):
            return value.strftime('%Y-%m-%d')
        return str(value)
```

