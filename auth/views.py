from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate, get_user_model
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
import random
from .forms import LoginForm, VerificationCodeForm

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            user = form.get_user()
            if user is not None:
                verification_code = str(random.randint(100000, 999999))
                request.session['verification_code'] = verification_code
                request.session['user_id_to_verify'] = user.id

                send_mail(
                    'Tu Código de Verificación',
                    f'Tu código de verificación es {verification_code}.',
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    fail_silently=False,
                )

                messages.success(request, 'Se ha enviado un código de verificación a tu correo.')
                return redirect('auth:verify_code')
            else:
                messages.error(request, "Correo electrónico o contraseña inválidos.")
    else:
        form = LoginForm()

    return render(request, 'auth/login.html', {'form': form})
def logout_view(request):
    logout(request)
    messages.info(request, "Has cerrado sesión exitosamente.")
    return redirect('usuarios:login')

def verify_code_view(request):
    User = get_user_model()
    
    if request.method == 'POST':
        form = VerificationCodeForm(request.POST)
        if form.is_valid():
            user_id = request.session.get('user_id_to_verify')
            code_sent = request.session.get('verification_code')
            code_entered = form.cleaned_data.get('code')
            
            if not user_id or not code_sent:
                messages.error(request, 'La sesión de verificación ha expirado. Por favor, intenta iniciar sesión de nuevo.')
                return redirect('usuarios:login')
            
            if code_entered == code_sent:
                user = get_object_or_404(User, id=user_id)
                login(request, user)
                
                # Limpiar los datos de la sesión
                del request.session['verification_code']
                del request.session['user_id_to_verify']
                
                messages.success(request, "¡Has iniciado sesión exitosamente!")
                return redirect('auth:dashboard')
            else:
                messages.error(request, "El código de verificación es incorrecto.")
    else:
        form = VerificationCodeForm()

        return render(request, 'auth/verify_code.html', {'form': form}) 
    
def dashboard_view(request):
    """Renderiza la página del dashboard."""
    return render(request, 'auth/dashboard.html')