from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate, get_user_model
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
import random
from .forms import LoginForm, VerificationCodeForm, RegistroForm

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
    return redirect('auth:login')

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
                return redirect('auth:login')
            
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

def registro_view(request):
    """Vista para el registro de nuevos usuarios"""
    if request.method == 'POST':
        form = RegistroForm(request.POST)
        if form.is_valid():
            # Crear el usuario
            user = form.save(commit=False)
            user.activo = False  # El usuario no estará activo hasta verificar el email
            user.save()
            
            # Generar código de verificación
            verification_code = str(random.randint(100000, 999999))
            request.session['verification_code'] = verification_code
            request.session['user_id_to_verify'] = user.id

            
            # Enviar email de verificación
            try:
                
                send_mail(
                    'Tu Código de Verificación',
                    f'Tu código de verificación es {verification_code}.',
                    settings.DEFAULT_FROM_EMAIL,
                    [user.email],
                    fail_silently=False,
                )
                
                messages.success(request, '¡Registro exitoso! Se ha enviado un código de verificación a tu correo electrónico.')
                return redirect('auth:verificar_registro')
                
            except Exception as e:
                # Si falla el envío de email, eliminar el usuario y mostrar error
                user.delete()
                messages.error(request, 'Error al enviar el email de verificación. Por favor, intenta de nuevo.')
                return redirect('auth:registro')
    else:
        form = RegistroForm()
    
    return render(request, 'auth/registro.html', {'form': form})

def verificar_registro_view(request):
    """Vista para verificar el código de registro"""
    user_id = request.session.get('user_id_to_verify')
    verification_code = request.session.get('verification_code')
    
    if not user_id or not verification_code:
        messages.error(request, 'La sesión de verificación ha expirado. Por favor, regístrate de nuevo.')
        return redirect('auth:registro')
    
    if request.method == 'POST':
        code_entered = request.POST.get('code')
        
        if code_entered == verification_code:
            # Activar el usuario
            User = get_user_model()
            try:
                user = User.objects.get(id=user_id)
                user.activo = True
                user.save()
                
                # Limpiar la sesión
                del request.session['verification_code']
                del request.session['user_id_to_verify']
                
                # Iniciar sesión automáticamente
                login(request, user)
                
                messages.success(request, '¡Cuenta verificada exitosamente! Has iniciado sesión.')
                return redirect('auth:dashboard')
                
            except User.DoesNotExist:
                messages.error(request, 'Usuario no encontrado.')
                return redirect('auth:registro')
        else:
            messages.error(request, 'Código de verificación incorrecto.')
    
    return render(request, 'auth/verificar_registro.html')