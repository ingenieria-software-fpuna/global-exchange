from django.shortcuts import render, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.views.generic import ListView, CreateView, UpdateView
from django.urls import reverse_lazy
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from .models import MetodoPago, Campo
from .forms import MetodoPagoForm, CampoFormSet


class MetodoPagoListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """Lista de métodos de pago"""
    model = MetodoPago
    template_name = 'metodo_pago/metodopago_list.html'
    context_object_name = 'metodos'
    permission_required = 'metodo_pago.view_metodopago'
    paginate_by = 20

    def get_queryset(self):
        queryset = MetodoPago.objects.all()

        q = self.request.GET.get('q')
        if q:
            queryset = queryset.filter(
                Q(nombre__icontains=q) | Q(descripcion__icontains=q)
            )

        estado = self.request.GET.get('estado')
        if estado == 'activo':
            queryset = queryset.filter(es_activo=True)
        elif estado == 'inactivo':
            queryset = queryset.filter(es_activo=False)

        return queryset.order_by('nombre')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Métodos de Pago'
        context['q'] = self.request.GET.get('q', '')
        context['estado'] = self.request.GET.get('estado', '')
        return context


class MetodoPagoCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """Crear método de pago"""
    model = MetodoPago
    form_class = MetodoPagoForm
    template_name = 'metodo_pago/metodopago_form.html'
    success_url = reverse_lazy('metodo_pago:metodopago_list')
    permission_required = 'metodo_pago.add_metodopago'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['campo_formset'] = CampoFormSet(self.request.POST)
        else:
            context['campo_formset'] = CampoFormSet()
        context['titulo'] = 'Crear Método de Pago'
        context['accion'] = 'Crear'
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        campo_formset = context['campo_formset']
        
        if campo_formset.is_valid():
            self.object = form.save()
            
            # Crear y asociar campos
            for campo_form in campo_formset:
                if campo_form.cleaned_data and not campo_form.cleaned_data.get('DELETE', False):
                    campo = campo_form.save(commit=False)
                    campo.save()
                    self.object.campos.add(campo)
            
            messages.success(self.request, f"Método de pago '{form.instance.nombre}' creado correctamente.")
            return super().form_valid(form)
        else:
            messages.error(self.request, "Error en los campos. Verifique los datos.")
            return self.render_to_response(self.get_context_data(form=form))

    def form_invalid(self, form):
        messages.error(self.request, "Error al crear el método de pago. Verifique los datos.")
        return super().form_invalid(form)


class MetodoPagoUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """Editar método de pago"""
    model = MetodoPago
    form_class = MetodoPagoForm
    template_name = 'metodo_pago/metodopago_form.html'
    success_url = reverse_lazy('metodo_pago:metodopago_list')
    permission_required = 'metodo_pago.change_metodopago'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context['campo_formset'] = CampoFormSet(self.request.POST)
        else:
            # Cargar campos existentes del método de pago
            campos_existentes = self.object.campos.all()
            initial_data = []
            for campo in campos_existentes:
                initial_data.append({
                    'nombre': campo.nombre,
                    'etiqueta': campo.etiqueta,
                    'tipo': campo.tipo,
                    'es_obligatorio': campo.es_obligatorio,
                    'max_length': campo.max_length,
                    'regex_validacion': campo.regex_validacion,
                    'placeholder': campo.placeholder,
                    'opciones': campo.opciones,
                    'es_activo': campo.es_activo,
                })
            context['campo_formset'] = CampoFormSet(initial=initial_data)
        context['titulo'] = f'Editar Método: {self.object.nombre}'
        context['accion'] = 'Actualizar'
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        campo_formset = context['campo_formset']
        
        if campo_formset.is_valid():
            self.object = form.save()
            
            # Obtener campos existentes
            campos_existentes = list(self.object.campos.all())
            
            # Procesar cada formulario del formset
            for i, campo_form in enumerate(campo_formset):
                if campo_form.cleaned_data and not campo_form.cleaned_data.get('DELETE', False):
                    # Si hay un campo existente en esta posición, actualizarlo
                    if i < len(campos_existentes):
                        campo = campos_existentes[i]
                        campo.nombre = campo_form.cleaned_data['nombre']
                        campo.etiqueta = campo_form.cleaned_data['etiqueta']
                        campo.tipo = campo_form.cleaned_data['tipo']
                        campo.es_obligatorio = campo_form.cleaned_data['es_obligatorio']
                        campo.max_length = campo_form.cleaned_data['max_length']
                        campo.regex_validacion = campo_form.cleaned_data['regex_validacion']
                        campo.placeholder = campo_form.cleaned_data['placeholder']
                        campo.opciones = campo_form.cleaned_data['opciones']
                        campo.es_activo = campo_form.cleaned_data['es_activo']
                        campo.save()
                    else:
                        # Crear nuevo campo
                        campo = campo_form.save(commit=False)
                        campo.save()
                        self.object.campos.add(campo)
                elif i < len(campos_existentes):
                    # Eliminar campo existente
                    campo = campos_existentes[i]
                    self.object.campos.remove(campo)
                    campo.delete()
            
            messages.success(self.request, f"Método de pago '{form.instance.nombre}' actualizado correctamente.")
            return super().form_valid(form)
        else:
            messages.error(self.request, "Error en los campos. Verifique los datos.")
            return self.render_to_response(self.get_context_data(form=form))

    def form_invalid(self, form):
        messages.error(self.request, "Error al actualizar el método de pago. Verifique los datos.")
        return super().form_invalid(form)


@login_required
@permission_required('metodo_pago.change_metodopago', raise_exception=True)
@require_http_methods(["POST"])
def toggle_metodopago_status(request, pk):
    """Cambiar estado activo/inactivo (AJAX)"""
    metodo = get_object_or_404(MetodoPago, pk=pk)
    metodo.es_activo = not metodo.es_activo
    metodo.save()
    return JsonResponse({
        'success': True,
        'nueva_estado': metodo.es_activo,
        'message': f"Método {'activado' if metodo.es_activo else 'desactivado'} correctamente."
    })


@login_required
@require_http_methods(["GET"])
def api_campos_metodo_pago(request):
    """API para obtener campos de un método de pago (AJAX)"""
    metodo_pago_id = request.GET.get('metodo_pago_id')
    
    if not metodo_pago_id:
        return JsonResponse({
            'success': False,
            'error': 'ID de método de pago requerido'
        })
    
    try:
        metodo_pago = get_object_or_404(MetodoPago, pk=metodo_pago_id, es_activo=True)
        campos = metodo_pago.get_campos_activos()
        
        campos_data = []
        for campo in campos:
            campos_data.append({
                'id': campo.id,
                'nombre': campo.nombre,
                'etiqueta': campo.etiqueta,
                'tipo': campo.tipo,
                'es_obligatorio': campo.es_obligatorio,
                'max_length': campo.max_length,
                'regex_validacion': campo.regex_validacion,
                'placeholder': campo.placeholder,
                'opciones': campo.opciones,
                'es_activo': campo.es_activo,
            })
        
        return JsonResponse({
            'success': True,
            'campos': campos_data
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

