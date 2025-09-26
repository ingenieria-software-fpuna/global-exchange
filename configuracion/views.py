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
