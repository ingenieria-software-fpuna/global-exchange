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
    """Vista para la pantalla de bienvenida con tasas de cambio"""
    return render(request, 'welcome.html')

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
    path('docs/', docs_view, name='docs_index'),
    path('docs/<path:path>', docs_view, name='docs'),
]
