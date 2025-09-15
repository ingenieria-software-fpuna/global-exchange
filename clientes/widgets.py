from django import forms
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils.safestring import mark_safe

User = get_user_model()

class UsuarioSelectorWidget(forms.SelectMultiple):
    """
    Widget personalizado para selección de usuarios con tabla interactiva,
    búsqueda y mejor UX.
    """
    
    def __init__(self, attrs=None):
        default_attrs = {
            'class': 'usuario-selector',
            'style': 'display: none;'  # Ocultar el select original
        }
        if attrs:
            default_attrs.update(attrs)
        super().__init__(default_attrs)
    
    def render(self, name, value, attrs=None, renderer=None):
        # Obtener el select original (oculto)
        original_select = super().render(name, value, attrs, renderer)
        
        # Generar un ID único para este widget
        widget_id = f"usuario-selector-{name.replace('[', '-').replace(']', '')}"
        
        # Obtener usuarios seleccionados
        selected_ids = []
        if value:
            if isinstance(value, list):
                selected_ids = [str(v) for v in value]
            else:
                selected_ids = [str(value)]
        
        # Obtener usuarios activos para la tabla
        usuarios = User.objects.filter(
            activo=True, es_activo=True
        ).values('id', 'nombre', 'apellido', 'email', 'cedula').order_by('nombre', 'apellido')
        
        # Generar HTML del widget personalizado
        widget_html = f"""
        {original_select}
        <div class="usuario-selector-widget" id="{widget_id}">
            <!-- Buscador -->
            <div class="mb-3">
                <div class="input-group">
                    <span class="input-group-text">
                        <i class="fas fa-search"></i>
                    </span>
                    <input type="text" 
                           id="{widget_id}-search" 
                           class="form-control" 
                           placeholder="Buscar usuarios por nombre, email o cédula...">
                </div>
            </div>
            
            <!-- Contador de seleccionados -->
            <div class="mb-3">
                <div class="alert alert-info d-flex justify-content-between align-items-center">
                    <span>
                        <i class="fas fa-users me-2"></i>
                        Usuarios seleccionados: <strong id="{widget_id}-count">{len(selected_ids)}</strong>
                    </span>
                    <button type="button" 
                            class="btn btn-outline-secondary btn-sm" 
                            id="{widget_id}-clear">
                        <i class="fas fa-times me-1"></i>Limpiar selección
                    </button>
                </div>
            </div>
            
            <!-- Alerta de advertencia cuando no hay usuarios seleccionados -->
            <div id="{widget_id}-warning" class="alert alert-warning" style="{'display: none;' if selected_ids else ''}">
                <i class="fas fa-exclamation-triangle me-2"></i>
                <strong>Advertencia:</strong> Sin usuarios asociados, nadie podrá operar en nombre de este cliente.
            </div>
            
            <!-- Tabla de usuarios -->
            <div class="table-responsive" style="max-height: 400px; overflow-y: auto;">
                <table class="table table-hover table-sm">
                    <thead class="table-light sticky-top">
                        <tr>
                            <th width="50">
                                <input type="checkbox" id="{widget_id}-select-all" class="form-check-input">
                            </th>
                            <th>Nombre</th>
                            <th>Email</th>
                            <th>Cédula</th>
                        </tr>
                    </thead>
                    <tbody id="{widget_id}-table">
        """
        
        # Agregar filas de usuarios
        for usuario in usuarios:
            is_selected = str(usuario['id']) in selected_ids
            selected_class = 'table-primary' if is_selected else ''
            checked = 'checked' if is_selected else ''
            
            nombre_completo = f"{usuario['nombre']} {usuario['apellido'] or ''}".strip()
            
            widget_html += f"""
                        <tr class="usuario-row {selected_class}" data-user-id="{usuario['id']}" data-widget="{widget_id}">
                            <td>
                                <input type="checkbox" 
                                       class="form-check-input user-checkbox" 
                                       value="{usuario['id']}" 
                                       data-widget="{widget_id}"
                                       {checked}>
                            </td>
                            <td class="user-name">{nombre_completo}</td>
                            <td class="user-email">{usuario['email']}</td>
                            <td class="user-cedula">{usuario['cedula'] or '-'}</td>
                        </tr>
            """
        
        widget_html += f"""
                    </tbody>
                </table>
            </div>
            
            <!-- Mensaje cuando no hay resultados -->
            <div id="{widget_id}-no-results" class="text-center py-4" style="display: none;">
                <i class="fas fa-search text-muted fa-2x mb-2"></i>
                <p class="text-muted">No se encontraron usuarios con ese criterio de búsqueda.</p>
            </div>
        </div>
        
        <script>
        document.addEventListener('DOMContentLoaded', function() {{
            var widgetId = '{widget_id}';
            var fieldName = '{name}';
            var searchInput = document.getElementById(widgetId + '-search');
            var selectAllCheckbox = document.getElementById(widgetId + '-select-all');
            var clearSelectionBtn = document.getElementById(widgetId + '-clear');
            var selectedCountSpan = document.getElementById(widgetId + '-count');
            var noResultsDiv = document.getElementById(widgetId + '-no-results');
            var usersTable = document.getElementById(widgetId + '-table');
            var warningDiv = document.getElementById(widgetId + '-warning');
            var originalSelect = document.querySelector('select[name="' + fieldName + '"]');
            
            // Intentar diferentes selectores si el primero no funciona
            if (!originalSelect) {{
                originalSelect = document.querySelector('#id_' + fieldName) ||
                               document.querySelector('select[id*="' + fieldName + '"]') ||
                               document.querySelector('select.usuario-selector');
            }}
            
            if (!originalSelect || !selectedCountSpan) {{
                return;
            }}
            
            function updateOriginalSelect() {{
                if (!originalSelect || !originalSelect.options) {{
                    return;
                }}
                
                var checkedBoxes = document.querySelectorAll('input[data-widget="' + widgetId + '"].user-checkbox:checked');
                var selectedValues = [];
                for (var i = 0; i < checkedBoxes.length; i++) {{
                    selectedValues.push(checkedBoxes[i].value);
                }}
                
                for (var i = 0; i < originalSelect.options.length; i++) {{
                    originalSelect.options[i].selected = false;
                }}
                
                for (var i = 0; i < selectedValues.length; i++) {{
                    for (var j = 0; j < originalSelect.options.length; j++) {{
                        if (originalSelect.options[j].value === selectedValues[i]) {{
                            originalSelect.options[j].selected = true;
                        }}
                    }}
                }}
                
                // Actualizar contador inmediatamente
                if (selectedCountSpan) {{
                    selectedCountSpan.textContent = selectedValues.length;
                }}
                
                // Mostrar/ocultar alerta de advertencia inmediatamente
                if (warningDiv) {{
                    warningDiv.style.display = selectedValues.length === 0 ? 'block' : 'none';
                }}
                
                // Actualizar estilos de filas
                var rows = document.querySelectorAll('tr[data-widget="' + widgetId + '"].usuario-row');
                for (var i = 0; i < rows.length; i++) {{
                    var checkbox = rows[i].querySelector('.user-checkbox');
                    if (checkbox && checkbox.checked) {{
                        rows[i].classList.add('table-primary');
                    }} else {{
                        rows[i].classList.remove('table-primary');
                    }}
                }}
            }}
            
            // Función para actualizar UI inmediatamente sin esperar otros procesos
            function updateUIFast() {{
                var checkedCount = document.querySelectorAll('input[data-widget="' + widgetId + '"].user-checkbox:checked').length;
                
                if (selectedCountSpan) {{
                    selectedCountSpan.textContent = checkedCount;
                }}
                
                if (warningDiv) {{
                    warningDiv.style.display = checkedCount === 0 ? 'block' : 'none';
                }}
            }}
            
            function filterUsers() {{
                if (!searchInput) return;
                var searchTerm = searchInput.value.toLowerCase();
                var rows = document.querySelectorAll('tr[data-widget="' + widgetId + '"].usuario-row');
                var visibleCount = 0;
                
                for (var i = 0; i < rows.length; i++) {{
                    var name = rows[i].querySelector('.user-name').textContent.toLowerCase();
                    var email = rows[i].querySelector('.user-email').textContent.toLowerCase();
                    var cedula = rows[i].querySelector('.user-cedula').textContent.toLowerCase();
                    
                    var matches = name.indexOf(searchTerm) >= 0 || 
                                  email.indexOf(searchTerm) >= 0 || 
                                  cedula.indexOf(searchTerm) >= 0;
                    
                    if (matches) {{
                        rows[i].style.display = '';
                        visibleCount++;
                    }} else {{
                        rows[i].style.display = 'none';
                    }}
                }}
                
                if (noResultsDiv && usersTable) {{
                    if (visibleCount === 0 && searchTerm) {{
                        noResultsDiv.style.display = 'block';
                        usersTable.style.display = 'none';
                    }} else {{
                        noResultsDiv.style.display = 'none';
                        usersTable.style.display = '';
                    }}
                }}
            }}
            
            if (searchInput) {{
                searchInput.addEventListener('input', filterUsers);
            }}
            
            if (selectAllCheckbox) {{
                selectAllCheckbox.addEventListener('change', function() {{
                    var visibleCheckboxes = document.querySelectorAll('tr[data-widget="' + widgetId + '"].usuario-row:not([style*="display: none"]) .user-checkbox');
                    for (var i = 0; i < visibleCheckboxes.length; i++) {{
                        visibleCheckboxes[i].checked = this.checked;
                    }}
                    updateUIFast(); // Actualización inmediata
                    updateOriginalSelect(); // Actualización completa
                }});
            }}
            
            if (clearSelectionBtn) {{
                clearSelectionBtn.addEventListener('click', function() {{
                    var checkboxes = document.querySelectorAll('input[data-widget="' + widgetId + '"].user-checkbox');
                    for (var i = 0; i < checkboxes.length; i++) {{
                        checkboxes[i].checked = false;
                    }}
                    if (selectAllCheckbox) {{
                        selectAllCheckbox.checked = false;
                    }}
                    updateUIFast(); // Actualización inmediata
                    updateOriginalSelect(); // Actualización completa
                }});
            }}
            
            document.addEventListener('change', function(e) {{
                if (e.target && e.target.classList && e.target.classList.contains('user-checkbox') && e.target.dataset.widget === widgetId) {{
                    updateUIFast(); // Actualización inmediata del contador y alerta
                    
                    // Actualización del "seleccionar todo" checkbox
                    var allVisible = document.querySelectorAll('tr[data-widget="' + widgetId + '"].usuario-row:not([style*="display: none"]) .user-checkbox');
                    var allChecked = true;
                    for (var i = 0; i < allVisible.length; i++) {{
                        if (!allVisible[i].checked) {{
                            allChecked = false;
                            break;
                        }}
                    }}
                    if (selectAllCheckbox) {{
                        selectAllCheckbox.checked = allVisible.length > 0 && allChecked;
                    }}
                    
                    updateOriginalSelect(); // Actualización completa
                }}
            }});
            
            document.addEventListener('click', function(e) {{
                if (!e.target) return;
                
                var row = e.target.closest('tr[data-widget="' + widgetId + '"].usuario-row');
                if (row && e.target.classList && !e.target.classList.contains('user-checkbox') && !e.target.closest('input')) {{
                    var checkbox = row.querySelector('.user-checkbox');
                    if (checkbox) {{
                        checkbox.checked = !checkbox.checked;
                        updateUIFast(); // Actualización inmediata
                        
                        // Trigger change event para mantener consistencia
                        var event = new Event('change');
                        event.bubbles = true;
                        checkbox.dispatchEvent(event);
                    }}
                }}
            }});
            
            setTimeout(function() {{
                // Re-intentar encontrar el select si no se encontró inicialmente
                if (!originalSelect) {{
                    originalSelect = document.querySelector('select[name="{name}"]') ||
                                   document.querySelector('#id_{name}') ||
                                   document.querySelector('select[id*="{name}"]') ||
                                   document.querySelector('select.usuario-selector');
                }}
                
                if (originalSelect && selectedCountSpan) {{
                    updateOriginalSelect();
                }}
            }}, 500);
        }});
        </script>
        """
        
        return mark_safe(widget_html)
