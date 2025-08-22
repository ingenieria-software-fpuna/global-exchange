from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.contrib import messages
from .models import TipoCliente

# Create your views here.

class TipoClienteListView(ListView):
    model = TipoCliente
    template_name = 'clientes/tipocliente_list.html'
    context_object_name = 'tipos_cliente'
    paginate_by = 10

class TipoClienteCreateView(CreateView):
    model = TipoCliente
    template_name = 'clientes/tipocliente_form.html'
    fields = ['nombre', 'descripcion', 'activo']
    success_url = reverse_lazy('clientes:tipocliente_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Tipo de cliente creado exitosamente.')
        return super().form_valid(form)

class TipoClienteUpdateView(UpdateView):
    model = TipoCliente
    template_name = 'clientes/tipocliente_form.html'
    fields = ['nombre', 'descripcion', 'activo']
    success_url = reverse_lazy('clientes:tipocliente_list')
    
    def form_valid(self, form):
        messages.success(self.request, 'Tipo de cliente actualizado exitosamente.')
        return super().form_valid(form)

class TipoClienteDeleteView(DeleteView):
    model = TipoCliente
    template_name = 'clientes/tipocliente_confirm_delete.html'
    success_url = reverse_lazy('clientes:tipocliente_list')
    
    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Tipo de cliente eliminado exitosamente.')
        return super().delete(request, *args, **kwargs)
