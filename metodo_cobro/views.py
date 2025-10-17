from django.shortcuts import render, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth.decorators import login_required, permission_required
from django.contrib import messages
from django.views.generic import ListView, CreateView, UpdateView
from django.urls import reverse_lazy
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods

from .models import MetodoCobro
from .forms import MetodoCobroForm, CampoFormSet
from metodo_pago.models import Campo


class MetodoCobroListView(LoginRequiredMixin, PermissionRequiredMixin, ListView):
    """Lista de métodos de cobro"""
    model = MetodoCobro
    template_name = 'metodo_cobro/metodocobro_list.html'
    context_object_name = 'metodos'
    permission_required = 'metodo_cobro.view_metodocobro'
    paginate_by = 20

    def get_queryset(self):
        queryset = MetodoCobro.objects.prefetch_related('monedas_permitidas').all()

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
        context['titulo'] = 'Métodos de Cobro'
        context['q'] = self.request.GET.get('q', '')
        context['estado'] = self.request.GET.get('estado', '')
        return context


class MetodoCobroCreateView(LoginRequiredMixin, PermissionRequiredMixin, CreateView):
    """Crear método de cobro"""
    model = MetodoCobro
    form_class = MetodoCobroForm
    template_name = 'metodo_cobro/metodocobro_form.html'
    success_url = reverse_lazy('metodo_cobro:metodocobro_list')
    permission_required = 'metodo_cobro.add_metodocobro'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = 'Crear Método de Cobro'
        context['accion'] = 'Crear'
        
        if self.request.POST:
            context['campo_formset'] = CampoFormSet(self.request.POST)
        else:
            context['campo_formset'] = CampoFormSet()
        
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        campo_formset = context['campo_formset']
        
        if campo_formset.is_valid():
            # Guardar el método de cobro
            self.object = form.save()
            
            # Procesar campos
            for campo_form in campo_formset:
                if campo_form.cleaned_data and not campo_form.cleaned_data.get('DELETE', False):
                    campo = campo_form.save()
                    self.object.campos.add(campo)
            
            messages.success(self.request, f"Método de cobro '{form.instance.nombre}' creado correctamente.")
            return super().form_valid(form)
        else:
            return self.form_invalid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Error al crear el método de cobro. Verifique los datos.")
        return super().form_invalid(form)


class MetodoCobroUpdateView(LoginRequiredMixin, PermissionRequiredMixin, UpdateView):
    """Editar método de cobro"""
    model = MetodoCobro
    form_class = MetodoCobroForm
    template_name = 'metodo_cobro/metodocobro_form.html'
    success_url = reverse_lazy('metodo_cobro:metodocobro_list')
    permission_required = 'metodo_cobro.change_metodocobro'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['titulo'] = f'Editar Método: {self.object.nombre}'
        context['accion'] = 'Actualizar'
        
        if self.request.POST:
            context['campo_formset'] = CampoFormSet(self.request.POST)
        else:
            # Cargar campos existentes
            initial_data = []
            for campo in self.object.campos.all():
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
        
        return context

    def form_valid(self, form):
        context = self.get_context_data()
        campo_formset = context['campo_formset']
        
        if campo_formset.is_valid():
            # Guardar el método de cobro
            self.object = form.save()
            
            # Limpiar campos existentes
            self.object.campos.clear()
            
            # Procesar campos
            for campo_form in campo_formset:
                if campo_form.cleaned_data and not campo_form.cleaned_data.get('DELETE', False):
                    campo = campo_form.save()
                    self.object.campos.add(campo)
            
            messages.success(self.request, f"Método de cobro '{form.instance.nombre}' actualizado correctamente.")
            return super().form_valid(form)
        else:
            return self.form_invalid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Error al actualizar el método de cobro. Verifique los datos.")
        return super().form_invalid(form)


@login_required
@permission_required('metodo_cobro.change_metodocobro', raise_exception=True)
@require_http_methods(["POST"])
def toggle_metodocobro_status(request, pk):
    """Cambiar estado activo/inactivo (AJAX)"""
    metodo = get_object_or_404(MetodoCobro, pk=pk)
    metodo.es_activo = not metodo.es_activo
    metodo.save()
    return JsonResponse({
        'success': True,
        'nueva_estado': metodo.es_activo,
        'message': f"Método {'activado' if metodo.es_activo else 'desactivado'} correctamente."
    })


@login_required
@require_http_methods(["GET"])
def api_campos_metodo_cobro(request):
    """API para obtener campos de un método de cobro específico"""
    metodo_cobro_id = request.GET.get('metodo_cobro_id')
    
    if not metodo_cobro_id:
        return JsonResponse({'error': 'ID de método de cobro requerido'}, status=400)
    
    try:
        metodo_cobro = MetodoCobro.objects.get(id=metodo_cobro_id)
        campos = metodo_cobro.get_campos_activos()
        
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
                'opciones': campo.opciones.split('\n') if campo.opciones else [],
            })
        
        return JsonResponse({
            'success': True,
            'campos': campos_data
        })
    except MetodoCobro.DoesNotExist:
        return JsonResponse({'error': 'Método de cobro no encontrado'}, status=404)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)