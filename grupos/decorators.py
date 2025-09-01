from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.models import Group
from django.shortcuts import redirect
from django.contrib import messages

def admin_required(view_func):
    """
    Decorador que verifica si el usuario está en el grupo 'Admin'.
    """
    def check_admin(user):
        if not user.is_authenticated:
            return False
        admin_group = Group.objects.filter(name='Admin').first()
        return admin_group and user in admin_group.user_set.all()
    
    decorated_view = user_passes_test(check_admin, login_url='/auth/login/')
    return decorated_view(view_func)

def admin_or_staff_required(view_func):
    """
    Decorador que verifica si el usuario está en el grupo 'Admin' 
    o es staff.
    """
    def check_admin_or_staff(user):
        if not user.is_authenticated:
            return False
        if user.is_staff:
            return True
        admin_group = Group.objects.filter(name='Admin').first()
        return admin_group and user in admin_group.user_set.all()
    
    decorated_view = user_passes_test(check_admin_or_staff, login_url='/auth/login/')
    return decorated_view(view_func)
