from django.contrib.auth.mixins import UserPassesTestMixin
from django.contrib.auth.models import Group
from django.shortcuts import redirect
from django.contrib import messages

class AdminRequiredMixin(UserPassesTestMixin):
    """
    Mixin que verifica si el usuario está en el grupo 'Admin'.
    Reemplaza las validaciones de is_superuser en vistas basadas en clases.
    """
    login_url = '/auth/login/'
    
    def test_func(self):
        user = self.request.user
        if not user.is_authenticated:
            return False
        admin_group = Group.objects.filter(name='Admin').first()
        return admin_group and user in admin_group.user_set.all()
    
    def handle_no_permission(self):
        messages.error(self.request, 'Acceso denegado. Se requieren permisos de administrador.')
        return redirect(self.login_url)

class AdminOrStaffRequiredMixin(UserPassesTestMixin):
    """
    Mixin que verifica si el usuario está en el grupo 'Admin' 
    o es staff.
    """
    login_url = '/auth/login/'
    
    def test_func(self):
        user = self.request.user
        if not user.is_authenticated:
            return False
        if user.is_staff:
            return True
        admin_group = Group.objects.filter(name='Admin').first()
        return admin_group and user in admin_group.user_set.all()
    
    def handle_no_permission(self):
        messages.error(self.request, 'Acceso denegado. Se requieren permisos de administrador o staff.')
        return redirect(self.login_url)
