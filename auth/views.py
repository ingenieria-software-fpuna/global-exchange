from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, get_user_model
from django.contrib import messages
from django.core.mail import send_mail
from django.conf import settings
from django.utils import timezone
import random
import os
from .forms import LoginForm, VerificationCodeForm, RegistroForm
from .models import CodigoVerificacion
from .services import EmailService

def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            user = form.get_user()
            if user is not None:
                # Verificar si 2FA está habilitada
                enable_2fa = os.environ.get('ENABLE_2FA', 'true').lower() in ['true', '1', 'yes', 'on']

                if not enable_2fa:
                    # 2FA deshabilitada: login directo
                    login(request, user, backend='grupos.backends.GrupoActivoBackend')
                    messages.success(request, "¡Has iniciado sesión exitosamente!")
                    return redirect('auth:dashboard')

                # 2FA habilitada: proceso normal
                # Limpiar códigos expirados
                CodigoVerificacion.limpiar_codigos_expirados()

                # Crear nuevo código de verificación con expiración de 5 minutos
                codigo_obj = CodigoVerificacion.crear_codigo(
                    usuario=user,
                    tipo='login',
                    request=request,
                    minutos_expiracion=5
                )

                # Guardar ID del usuario en sesión para verificación posterior
                request.session['user_id_to_verify'] = user.id
                request.session['verification_type'] = 'login'

                # Enviar email con el nuevo servicio
                exito, mensaje = EmailService.enviar_codigo_verificacion(user, codigo_obj, request)

                if exito:
                    messages.success(request, 'Se ha enviado un código de verificación a tu correo electrónico.')
                    return redirect('auth:verify_code')
                else:
                    messages.error(request, f'Error al enviar el código: {mensaje}')
            else:
                messages.error(request, "Correo electrónico o contraseña inválidos.")
        else:
            # Verificar si hay un usuario no verificado
            unverified_user = form.get_unverified_user()
            if unverified_user:
                # Guardar información en sesión para reenvío de verificación
                request.session['user_id_to_verify'] = unverified_user.id
                request.session['verification_type'] = 'registro'
                
                
                return render(request, 'auth/login.html', {
                    'form': form,
                    'show_resend_verification': True,
                    'user_email': unverified_user.email
                })
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
            verification_type = request.session.get('verification_type', 'login')
            code_entered = form.cleaned_data.get('code')
            
            if not user_id:
                messages.error(request, 'La sesión de verificación ha expirado. Por favor, intenta iniciar sesión de nuevo.')
                return redirect('auth:login')
            
            try:
                user = User.objects.get(id=user_id)
                es_valido, codigo_obj = CodigoVerificacion.verificar_codigo(
                    usuario=user,
                    codigo=code_entered,
                    tipo=verification_type
                )
                
                if es_valido:
                    login(request, user, backend='grupos.backends.GrupoActivoBackend')
                    
                    # Limpiar los datos de la sesión
                    if 'user_id_to_verify' in request.session:
                        del request.session['user_id_to_verify']
                    if 'verification_type' in request.session:
                        del request.session['verification_type']
                    
                    messages.success(request, "¡Has iniciado sesión exitosamente!")
                    return redirect('auth:dashboard')
                else:
                    # Verificar si el código expiró o es incorrecto
                    codigos_usuario = CodigoVerificacion.objects.filter(
                        usuario=user,
                        tipo=verification_type,
                        codigo=code_entered
                    ).first()
                    
                    if codigos_usuario and not codigos_usuario.es_valido():
                        if codigos_usuario.usado:
                            messages.error(request, "Este código ya ha sido utilizado.")
                        else:
                            messages.error(request, "El código de verificación ha expirado. Por favor, solicita uno nuevo.")
                    else:
                        messages.error(request, "El código de verificación es incorrecto.")
                        
            except User.DoesNotExist:
                messages.error(request, 'Usuario no encontrado.')
                return redirect('auth:login')
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
            # Verificar si 2FA está habilitada
            enable_2fa = os.environ.get('ENABLE_2FA', 'true').lower() in ['true', '1', 'yes', 'on']

            # Crear el usuario
            user = form.save(commit=False)

            if not enable_2fa:
                # 2FA deshabilitada: activar usuario directamente
                user.activo = True  # Email verificado automáticamente
                user.es_activo = True  # Usuario habilitado para el sistema
                user.save()

                # Iniciar sesión automáticamente
                login(request, user, backend='grupos.backends.GrupoActivoBackend')
                messages.success(request, '¡Registro exitoso! Has iniciado sesión automáticamente.')
                return redirect('auth:dashboard')

            # 2FA habilitada: proceso normal de verificación
            user.activo = False  # Email no verificado hasta confirmar
            user.es_activo = True  # Usuario habilitado para el sistema
            user.save()

            # Limpiar códigos expirados
            CodigoVerificacion.limpiar_codigos_expirados()

            # Crear código de verificación con expiración de 5 minutos para registro
            codigo_obj = CodigoVerificacion.crear_codigo(
                usuario=user,
                tipo='registro',
                request=request,
                minutos_expiracion=5
            )

            # Guardar información en sesión
            request.session['user_id_to_verify'] = user.id
            request.session['verification_type'] = 'registro'

            # Enviar email de verificación
            try:
                exito, mensaje = EmailService.enviar_codigo_verificacion(user, codigo_obj, request)

                if exito:
                    messages.success(request, '¡Registro exitoso! Se ha enviado un código de verificación a tu correo electrónico.')
                    return redirect('auth:verificar_registro')
                else:
                    # Si falla el envío de email, mantener usuario inactivo y permitir reenvío
                    user.activo = False  # Email no verificado
                    user.es_activo = True  # Usuario habilitado para reenvío
                    user.save()
                    messages.error(request, f'Error al enviar el email de verificación: {mensaje}. Puedes intentar reenviar el código.')
                    return redirect('auth:verificar_registro')  # Ir a página de verificación

            except Exception as e:
                # Si falla el envío de email, mantener usuario inactivo y permitir reenvío
                user.activo = False  # Email no verificado
                user.es_activo = True  # Usuario habilitado para reenvío
                user.save()
                messages.error(request, 'Error inesperado al enviar el email de verificación. Puedes intentar reenviar el código.')
                return redirect('auth:verificar_registro')  # Ir a página de verificación
    else:
        form = RegistroForm()

    return render(request, 'auth/registro.html', {'form': form})

def verificar_registro_view(request):
    """Vista para verificar el código de registro"""
    user_id = request.session.get('user_id_to_verify')
    verification_type = request.session.get('verification_type', 'registro')
    
    if not user_id:
        messages.error(request, 'La sesión de verificación ha expirado. Por favor, regístrate de nuevo.')
        return redirect('auth:registro')
    
    if request.method == 'POST':
        code_entered = request.POST.get('code')
        
        if code_entered:
            try:
                User = get_user_model()
                user = User.objects.get(id=user_id)
                
                es_valido, codigo_obj = CodigoVerificacion.verificar_codigo(
                    usuario=user,
                    codigo=code_entered,
                    tipo=verification_type
                )
                
                if es_valido:
                    # Activar verificación de email
                    user.activo = True  # Email verificado
                    user.save()
                    
                    # Limpiar la sesión
                    if 'user_id_to_verify' in request.session:
                        del request.session['user_id_to_verify']
                    if 'verification_type' in request.session:
                        del request.session['verification_type']
                    
                    # Iniciar sesión automáticamente
                    login(request, user, backend='grupos.backends.GrupoActivoBackend')
                    
                    messages.success(request, '¡Cuenta verificada exitosamente! Has iniciado sesión.')
                    return redirect('auth:dashboard')
                else:
                    # Verificar si el código expiró o es incorrecto
                    codigos_usuario = CodigoVerificacion.objects.filter(
                        usuario=user,
                        tipo=verification_type,
                        codigo=code_entered
                    ).first()
                    
                    if codigos_usuario and not codigos_usuario.es_valido():
                        if codigos_usuario.usado:
                            messages.error(request, 'Este código ya ha sido utilizado.')
                        else:
                            messages.error(request, 'El código de verificación ha expirado. Puedes solicitar un nuevo código.')
                            return redirect('auth:verificar_registro')
                    else:
                        messages.error(request, 'Código de verificación incorrecto.')
                        
            except User.DoesNotExist:
                messages.error(request, 'Usuario no encontrado.')
                return redirect('auth:registro')
        else:
            messages.error(request, 'Por favor, ingresa un código de verificación.')
    
    return render(request, 'auth/verificar_registro.html')

def reenviar_codigo_view(request):
    """Vista para reenviar código de verificación"""
    user_id = request.session.get('user_id_to_verify')
    verification_type = request.session.get('verification_type', 'login')
    
    if not user_id:
        messages.error(request, 'No hay una sesión de verificación activa.')
        if verification_type == 'registro':
            return redirect('auth:registro')
        else:
            return redirect('auth:login')
    
    try:
        User = get_user_model()
        user = User.objects.get(id=user_id)
        
        # Limpiar códigos expirados
        CodigoVerificacion.limpiar_codigos_expirados()
        
        # Crear nuevo código
        if verification_type == 'registro':
            minutos_expiracion = 5
        else:
            minutos_expiracion = 5
            
        codigo_obj = CodigoVerificacion.crear_codigo(
            usuario=user,
            tipo=verification_type,
            request=request,
            minutos_expiracion=minutos_expiracion
        )
        
        # Enviar email
        exito, mensaje = EmailService.enviar_codigo_verificacion(user, codigo_obj, request)
        
        if exito:
            messages.success(request, f'Se ha enviado un nuevo código de verificación a tu correo.')
        else:
            messages.error(request, f'Error al reenviar el código: {mensaje}')
            
    except User.DoesNotExist:
        messages.error(request, 'Usuario no encontrado.')
        return redirect('auth:login')
    
    # Redirigir según el tipo de verificación
    if verification_type == 'registro':
        return redirect('auth:verificar_registro')
    else:
        return redirect('auth:verify_code')

def reenviar_verificacion_login_view(request):
    """Vista para reenviar código de verificación desde login"""
    user_id = request.session.get('user_id_to_verify')
    
    if not user_id:
        messages.error(request, 'No hay una sesión de verificación activa.')
        return redirect('auth:login')
    
    try:
        User = get_user_model()
        user = User.objects.get(id=user_id)
        
        # Verificar que el usuario realmente necesita verificación
        if user.activo:
            messages.info(request, 'Tu cuenta ya está verificada. Puedes iniciar sesión normalmente.')
            return redirect('auth:login')
        
        # Limpiar códigos expirados
        CodigoVerificacion.limpiar_codigos_expirados()
        
        # Crear nuevo código de verificación para registro
        codigo_obj = CodigoVerificacion.crear_codigo(
            usuario=user,
            tipo='registro',
            request=request,
            minutos_expiracion=5
        )
        
        # Actualizar sesión
        request.session['verification_type'] = 'registro'
        
        # Enviar email
        exito, mensaje = EmailService.enviar_codigo_verificacion(user, codigo_obj, request)
        
        if exito:
            messages.success(request, 'Se ha enviado un nuevo código de verificación a tu correo.')
            return redirect('auth:verificar_registro')
        else:
            messages.error(request, f'Error al reenviar el código: {mensaje}')
            return redirect('auth:login')
            
    except User.DoesNotExist:
        messages.error(request, 'Usuario no encontrado.')
        return redirect('auth:login')


def password_reset_request_view(request):
    """Vista para solicitar reset de contraseña"""
    from .forms import PasswordResetRequestForm
    from .models import PasswordResetToken
    
    if request.method == 'POST':
        form = PasswordResetRequestForm(request.POST)
        if form.is_valid():
            user = form.get_user()
            
            # Limpiar tokens expirados
            PasswordResetToken.limpiar_tokens_expirados()
            
            # Crear nuevo token
            token_obj = PasswordResetToken.crear_token(user, request)
            
            # Enviar email
            exito, mensaje = EmailService.enviar_reset_password(user, token_obj, request)
            
            if exito:
                messages.success(
                    request, 
                    'Se han enviado las instrucciones de restablecimiento a tu correo electrónico. '
                    'Revisa tu bandeja de entrada y sigue las instrucciones.'
                )
                return redirect('auth:login')
            else:
                messages.error(request, f'Error al enviar el email: {mensaje}')
    else:
        form = PasswordResetRequestForm()
    
    return render(request, 'auth/password_reset_request.html', {'form': form})


def password_reset_confirm_view(request, token):
    """Vista para confirmar reset de contraseña con token"""
    from .forms import PasswordResetForm
    from .models import PasswordResetToken
    
    try:
        token_obj = PasswordResetToken.objects.get(token=token)
        
        if not token_obj.es_valido():
            messages.error(
                request, 
                'El enlace de restablecimiento ha expirado o ya ha sido usado. '
                'Solicita uno nuevo.'
            )
            return redirect('auth:password_reset_request')
        
        if request.method == 'POST':
            form = PasswordResetForm(request.POST)
            if form.is_valid():
                # Cambiar la contraseña
                user = token_obj.usuario
                new_password = form.cleaned_data['password1']
                user.set_password(new_password)
                user.save()
                
                # Marcar token como usado
                token_obj.marcar_como_usado()
                
                messages.success(
                    request, 
                    '¡Tu contraseña ha sido restablecida exitosamente! '
                    'Ya puedes iniciar sesión con tu nueva contraseña.'
                )
                return redirect('auth:password_reset_complete')
        else:
            form = PasswordResetForm()
        
        context = {
            'form': form,
            'token': token,
            'user': token_obj.usuario
        }
        return render(request, 'auth/password_reset_confirm.html', context)
        
    except PasswordResetToken.DoesNotExist:
        messages.error(
            request, 
            'El enlace de restablecimiento no es válido. '
            'Verifica el enlace o solicita uno nuevo.'
        )
        return redirect('auth:password_reset_request')


def password_reset_complete_view(request):
    """Vista de confirmación de reset completado"""
    return render(request, 'auth/password_reset_complete.html')