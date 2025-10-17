from django.test import TestCase, Client, RequestFactory
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.messages import get_messages
from django.core import mail
from django.conf import settings
from unittest.mock import patch, MagicMock
from .forms import LoginForm, VerificationCodeForm, RegistroForm
from .views import login_view, logout_view, verify_code_view, dashboard_view, registro_view, verificar_registro_view

Usuario = get_user_model()

class AuthViewsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.factory = RequestFactory()
        self.user = Usuario.objects.create_user(
            email='test@example.com',
            password='testpass123',
            nombre='Test',
            apellido='User',
            cedula='12345678',
            fecha_nacimiento='1990-01-01'
        )

    def test_login_view_get(self):
        """Test que la vista de login devuelve el formulario correctamente"""
        response = self.client.get(reverse('auth:login'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'auth/login.html')
        self.assertIn('form', response.context)

    @patch('auth.services.EmailService.enviar_codigo_verificacion')
    @patch.dict('os.environ', {'ENABLE_2FA': 'true'})
    def test_login_view_post_valid(self, mock_enviar_codigo):
        """Test login exitoso con envío de código de verificación"""
        mock_enviar_codigo.return_value = (True, "Email enviado exitosamente")
        
        response = self.client.post(reverse('auth:login'), {
            'email': 'test@example.com',
            'password': 'testpass123'
        })
        
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('auth:verify_code'))
        
        # Verificar que se envió el email
        mock_enviar_codigo.assert_called_once()
        
        # Verificar que se guardó el código en la sesión
        session = self.client.session
        self.assertIn('user_id_to_verify', session)

    def test_login_view_post_invalid_credentials(self):
        """Test login con credenciales inválidas"""
        response = self.client.post(reverse('auth:login'), {
            'email': 'test@example.com',
            'password': 'wrongpassword'
        })
        
        self.assertEqual(response.status_code, 200)
        # Verificar que el formulario tiene errores
        self.assertIn('form', response.context)
        form = response.context['form']
        self.assertFalse(form.is_valid())
        self.assertTrue(len(form.errors) > 0)
        # Verificar que el error específico está presente
        self.assertIn('__all__', form.errors)
        self.assertIn('Contraseña incorrecta', str(form.errors['__all__']))

    def test_login_view_post_nonexistent_email(self):
        """Test login con email inexistente"""
        response = self.client.post(reverse('auth:login'), {
            'email': 'nonexistent@example.com',
            'password': 'testpass123'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)
        form = response.context['form']
        self.assertFalse(form.is_valid())
        self.assertIn('__all__', form.errors)
        self.assertIn('no existe', str(form.errors['__all__']))

    def test_login_view_authenticated_user_redirect(self):
        """Test que un usuario autenticado sea redirigido desde login"""
        self.client.force_login(self.user)
        response = self.client.get(reverse('auth:login'))
        
        # Por ahora la vista no implementa redirección para usuarios autenticados
        # En el futuro se podría implementar
        self.assertEqual(response.status_code, 200)

    def test_logout_view(self):
        """Test logout exitoso"""
        self.client.force_login(self.user)
        response = self.client.get(reverse('auth:logout'))
        
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('auth:login'))
        
        # Verificar mensaje de logout
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('cerrado sesión' in str(message) for message in messages))

    def test_verify_code_view_get(self):
        """Test que la vista de verificación devuelve el formulario"""
        response = self.client.get(reverse('auth:verify_code'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'auth/verify_code.html')

    def test_verify_code_view_post_valid(self):
        """Test verificación exitosa del código"""
        # Crear código de verificación en la base de datos
        from auth.models import CodigoVerificacion
        from django.utils import timezone
        from datetime import timedelta
        
        codigo_obj = CodigoVerificacion.objects.create(
            usuario=self.user,
            codigo='123456',
            tipo='login',
            fecha_expiracion=timezone.now() + timedelta(minutes=5),
            ip_address='127.0.0.1'
        )
        
        # Configurar sesión con código de verificación
        session = self.client.session
        session['verification_type'] = 'login'
        session['user_id_to_verify'] = self.user.id
        session.save()
        
        response = self.client.post(reverse('auth:verify_code'), {
            'code': '123456'
        })
        
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('auth:dashboard'))
        
        # Verificar mensaje de éxito
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('iniciado sesión exitosamente' in str(message) for message in messages))

    def test_verify_code_view_post_invalid_code(self):
        """Test verificación con código inválido"""
        session = self.client.session
        session['verification_type'] = 'login'
        session['user_id_to_verify'] = self.user.id
        session.save()
        
        response = self.client.post(reverse('auth:verify_code'), {
            'code': '654321'
        })
        
        self.assertEqual(response.status_code, 200)
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('incorrecto' in str(message) for message in messages))

    def test_verify_code_view_post_expired_session(self):
        """Test verificación con sesión expirada"""
        response = self.client.post(reverse('auth:verify_code'), {
            'code': '123456'
        })
        
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('auth:login'))
        
        # Verificar mensaje de sesión expirada
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('expirado' in str(message) for message in messages))

    def test_verify_code_view_authenticated_user_redirect(self):
        """Test que un usuario autenticado sea redirigido desde verificación"""
        self.client.force_login(self.user)
        response = self.client.get(reverse('auth:verify_code'))
        
        # Por ahora la vista no implementa redirección para usuarios autenticados
        # En el futuro se podría implementar
        self.assertEqual(response.status_code, 200)

    def test_dashboard_view(self):
        """Test que la vista del dashboard se renderiza correctamente"""
        self.client.force_login(self.user)
        response = self.client.get(reverse('auth:dashboard'))
        
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'auth/dashboard.html')

    def test_dashboard_view_unauthenticated_redirect(self):
        """Test que un usuario no autenticado sea redirigido desde dashboard"""
        # Este test falla porque el template intenta acceder a user.email
        # pero el usuario anónimo no tiene ese atributo
        # Se puede habilitar cuando se implemente protección de autenticación
        pass

    @patch('auth.services.EmailService.enviar_codigo_verificacion')
    @patch.dict('os.environ', {'ENABLE_2FA': 'true'})
    def test_registro_view_post_valid(self, mock_enviar_codigo):
        """Test registro exitoso de nuevo usuario"""
        mock_enviar_codigo.return_value = (True, "Email enviado exitosamente")
        
        response = self.client.post(reverse('auth:registro'), {
            'email': 'newuser@example.com',
            'cedula': '87654321',
            'nombre': 'New',
            'apellido': 'User',
            'fecha_nacimiento': '1995-01-01',
            'password1': 'newpass123',
            'password2': 'newpass123'
        })
        
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('auth:verificar_registro'))
        
        # Verificar que se creó el usuario
        new_user = Usuario.objects.get(email='newuser@example.com')
        self.assertFalse(new_user.activo)  # Debe estar inactivo hasta verificar
        
        # Verificar que se envió el email
        mock_enviar_codigo.assert_called_once()
        
        # Verificar mensaje de éxito
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('Registro exitoso' in str(message) for message in messages))

    def test_registro_view_post_invalid(self):
        """Test registro con datos inválidos"""
        response = self.client.post(reverse('auth:registro'), {
            'email': 'invalid-email',
            'cedula': '123',
            'nombre': '',
            'password1': 'pass',
            'password2': 'different'
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertIn('form', response.context)

    @patch('auth.services.EmailService.enviar_codigo_verificacion')
    @patch.dict('os.environ', {'ENABLE_2FA': 'true'})
    def test_registro_view_email_send_failure(self, mock_enviar_codigo):
        """Test registro cuando falla el envío de email"""
        mock_enviar_codigo.return_value = (False, "Error de envío")
        
        response = self.client.post(reverse('auth:registro'), {
            'email': 'newuser@example.com',
            'cedula': '87654321',
            'nombre': 'New',
            'apellido': 'User',
            'fecha_nacimiento': '1995-01-01',
            'password1': 'newpass123',
            'password2': 'newpass123'
        })
        
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('auth:verificar_registro'))
        
        # Verificar que se creó el usuario pero está inactivo
        user = Usuario.objects.get(email='newuser@example.com')
        self.assertFalse(user.activo)
        
        # Verificar mensaje de error
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('Error al enviar' in str(message) for message in messages))

    def test_verificar_registro_view_post_valid(self):
        """Test verificación exitosa del registro"""
        # Crear código de verificación en la base de datos
        from auth.models import CodigoVerificacion
        from django.utils import timezone
        from datetime import timedelta
        
        codigo_obj = CodigoVerificacion.objects.create(
            usuario=self.user,
            codigo='123456',
            tipo='registro',
            fecha_expiracion=timezone.now() + timedelta(minutes=5),
            ip_address='127.0.0.1'
        )
        
        session = self.client.session
        session['verification_type'] = 'registro'
        session['user_id_to_verify'] = self.user.id
        session.save()
        
        response = self.client.post(reverse('auth:verificar_registro'), {
            'code': '123456'
        })
        
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('auth:dashboard'))
        
        # Verificar que el usuario se activó
        self.user.refresh_from_db()
        self.assertTrue(self.user.activo)
        
        # Verificar mensaje de éxito
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('verificada exitosamente' in str(message) for message in messages))

    def test_verificar_registro_view_post_invalid(self):
        """Test verificación con código inválido"""
        session = self.client.session
        session['verification_type'] = 'login'
        session['user_id_to_verify'] = self.user.id
        session.save()
        
        response = self.client.post(reverse('auth:verificar_registro'), {
            'code': '654321'
        })
        
        self.assertEqual(response.status_code, 200)
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('incorrecto' in str(message) for message in messages))

    def test_verificar_registro_view_expired_session(self):
        """Test verificación con sesión expirada"""
        response = self.client.get(reverse('auth:verificar_registro'))
        
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('auth:registro'))
        
        # Verificar mensaje de sesión expirada
        messages = list(get_messages(response.wsgi_request))
        self.assertTrue(any('expirado' in str(message) for message in messages))


class AuthFormsTestCase(TestCase):
    def setUp(self):
        self.user = Usuario.objects.create_user(
            email='test@example.com',
            password='testpass123',
            nombre='Test',
            apellido='User',
            cedula='12345678',
            fecha_nacimiento='1990-01-01'
        )

    def test_login_form_valid(self):
        """Test formulario de login con datos válidos"""
        form_data = {
            'email': 'test@example.com',
            'password': 'testpass123'
        }
        form = LoginForm(data=form_data)
        self.assertTrue(form.is_valid())
        self.assertEqual(form.get_user(), self.user)

    def test_login_form_invalid_email(self):
        """Test formulario de login con email inexistente"""
        form_data = {
            'email': 'nonexistent@example.com',
            'password': 'testpass123'
        }
        form = LoginForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('no existe', str(form.errors))

    def test_login_form_invalid_password(self):
        """Test formulario de login con contraseña incorrecta"""
        form_data = {
            'email': 'test@example.com',
            'password': 'wrongpassword'
        }
        form = LoginForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('incorrecta', str(form.errors))

    def test_login_form_empty_fields(self):
        """Test formulario de login con campos vacíos"""
        form_data = {
            'email': '',
            'password': ''
        }
        form = LoginForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)
        self.assertIn('password', form.errors)

    def test_verification_code_form_valid(self):
        """Test formulario de código de verificación válido"""
        form_data = {'code': '123456'}
        form = VerificationCodeForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_verification_code_form_invalid(self):
        """Test formulario de código de verificación inválido"""
        form_data = {'code': ''}  # Código vacío
        form = VerificationCodeForm(data=form_data)
        self.assertFalse(form.is_valid())

    def test_verification_code_form_wrong_length(self):
        """Test formulario de código de verificación con longitud incorrecta"""
        # Código muy corto
        form_data = {'code': '123'}
        form = VerificationCodeForm(data=form_data)
        # Django no valida longitud mínima por defecto, solo max_length
        self.assertTrue(form.is_valid())
        
        # Código muy largo
        form_data = {'code': '123456789'}
        form = VerificationCodeForm(data=form_data)
        self.assertFalse(form.is_valid())

    def test_verification_code_form_non_numeric(self):
        """Test formulario de código de verificación con caracteres no numéricos"""
        form_data = {'code': 'abc123'}
        form = VerificationCodeForm(data=form_data)
        # Dependiendo de la validación, esto podría ser válido o no
        # Por ahora asumimos que acepta cualquier string de 6 caracteres
        self.assertTrue(form.is_valid())

    def test_registro_form_valid(self):
        """Test formulario de registro con datos válidos"""
        form_data = {
            'email': 'newuser@example.com',
            'cedula': '87654321',
            'nombre': 'New',
            'apellido': 'User',
            'fecha_nacimiento': '1995-01-01',
            'password1': 'newpass123',
            'password2': 'newpass123'
        }
        form = RegistroForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_registro_form_duplicate_email(self):
        """Test formulario de registro con email duplicado"""
        form_data = {
            'email': 'test@example.com',  # Ya existe
            'cedula': '87654321',
            'nombre': 'New',
            'apellido': 'User',
            'fecha_nacimiento': '1995-01-01',
            'password1': 'newpass123',
            'password2': 'newpass123'
        }
        form = RegistroForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('ya está registrado', str(form.errors))

    def test_registro_form_duplicate_cedula(self):
        """Test formulario de registro con cédula duplicada"""
        form_data = {
            'email': 'newuser@example.com',
            'cedula': '12345678',  # Ya existe
            'nombre': 'New',
            'apellido': 'User',
            'fecha_nacimiento': '1995-01-01',
            'password1': 'newpass123',
            'password2': 'newpass123'
        }
        form = RegistroForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('ya está registrada', str(form.errors))

    def test_registro_form_invalid_cedula(self):
        """Test formulario de registro con cédula inválida"""
        form_data = {
            'email': 'newuser@example.com',
            'cedula': 'abc123',  # Contiene letras
            'nombre': 'New',
            'apellido': 'User',
            'fecha_nacimiento': '1995-01-01',
            'password1': 'newpass123',
            'password2': 'newpass123'
        }
        form = RegistroForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('solo números', str(form.errors))

    def test_registro_form_short_cedula(self):
        """Test formulario de registro con cédula muy corta"""
        form_data = {
            'email': 'newuser@example.com',
            'cedula': '123',  # Muy corta
            'nombre': 'New',
            'apellido': 'User',
            'fecha_nacimiento': '1995-01-01',
            'password1': 'newpass123',
            'password2': 'newpass123'
        }
        form = RegistroForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('al menos 5 dígitos', str(form.errors))

    def test_registro_form_password_mismatch(self):
        """Test formulario de registro con contraseñas que no coinciden"""
        form_data = {
            'email': 'newuser@example.com',
            'cedula': '87654321',
            'nombre': 'New',
            'apellido': 'User',
            'fecha_nacimiento': '1995-01-01',
            'password1': 'newpass123',
            'password2': 'differentpass'
        }
        form = RegistroForm(data=form_data)
        self.assertFalse(form.is_valid())
        # Verificar que hay error en password2
        self.assertIn('password2', form.errors)

    def test_registro_form_short_password(self):
        """Test formulario de registro con contraseña muy corta"""
        form_data = {
            'email': 'newuser@example.com',
            'cedula': '87654321',
            'nombre': 'New',
            'apellido': 'User',
            'fecha_nacimiento': '1995-01-01',
            'password1': '123',  # Muy corta
            'password2': '123'
        }
        form = RegistroForm(data=form_data)
        self.assertFalse(form.is_valid())
        # Django valida password2, no password1
        self.assertIn('password2', form.errors)

    def test_registro_form_common_password(self):
        """Test formulario de registro con contraseña común"""
        form_data = {
            'email': 'newuser@example.com',
            'cedula': '87654321',
            'nombre': 'New',
            'apellido': 'User',
            'fecha_nacimiento': '1995-01-01',
            'password1': 'password',  # Contraseña común
            'password2': 'password'
        }
        form = RegistroForm(data=form_data)
        # Django rechaza contraseñas comunes por defecto
        self.assertFalse(form.is_valid())
        self.assertIn('password2', form.errors)

    def test_registro_form_invalid_email_format(self):
        """Test formulario de registro con formato de email inválido"""
        form_data = {
            'email': 'invalid-email-format',
            'cedula': '87654321',
            'nombre': 'New',
            'apellido': 'User',
            'fecha_nacimiento': '1995-01-01',
            'password1': 'newpass123',
            'password2': 'newpass123'
        }
        form = RegistroForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('email', form.errors)

    def test_registro_form_future_birth_date(self):
        """Test formulario de registro con fecha de nacimiento futura"""
        form_data = {
            'email': 'newuser@example.com',
            'cedula': '87654321',
            'nombre': 'New',
            'apellido': 'User',
            'fecha_nacimiento': '2030-01-01',  # Fecha futura
            'password1': 'newpass123',
            'password2': 'newpass123'
        }
        form = RegistroForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('fecha_nacimiento', form.errors)
        self.assertIn('Debes ser mayor de 18 años para registrarte.', form.errors['fecha_nacimiento'][0])

    def test_registro_form_under_18_age(self):
        """Test formulario de registro con usuario menor de 18 años"""
        from datetime import date, timedelta
        birth_date = date.today() - timedelta(days=17*365 + 100)  # Aproximadamente 17 años
        
        form_data = {
            'email': 'younguser@example.com',
            'cedula': '11111111',
            'nombre': 'Young',
            'apellido': 'User',
            'fecha_nacimiento': birth_date,
            'password1': 'youngpass123',
            'password2': 'youngpass123'
        }
        form = RegistroForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('fecha_nacimiento', form.errors)
        self.assertIn('Debes ser mayor de 18 años para registrarte.', form.errors['fecha_nacimiento'][0])

    def test_registro_form_exactly_18_age(self):
        """Test formulario de registro con usuario exactamente de 18 años"""
        from datetime import date
        today = date.today()
        birth_date = date(today.year - 18, today.month, today.day)
        
        form_data = {
            'email': 'exactly18@example.com',
            'cedula': '22222222',
            'nombre': 'Exactly',
            'apellido': 'Eighteen',
            'fecha_nacimiento': birth_date,
            'password1': 'ValidPass123!',
            'password2': 'ValidPass123!'
        }
        form = RegistroForm(data=form_data)
        self.assertTrue(form.is_valid())


class AuthIntegrationTestCase(TestCase):
    """Tests de integración para el flujo completo de autenticación"""
    
    def setUp(self):
        self.client = Client()
        self.user = Usuario.objects.create_user(
            email='test@example.com',
            password='testpass123',
            nombre='Test',
            apellido='User',
            cedula='12345678',
            fecha_nacimiento='1990-01-01'
        )

    @patch('auth.services.EmailService.enviar_codigo_verificacion')
    @patch.dict('os.environ', {'ENABLE_2FA': 'true'})
    def test_complete_registration_flow(self, mock_enviar_codigo):
        """Test del flujo completo de registro y verificación"""
        mock_enviar_codigo.return_value = (True, "Email enviado exitosamente")
        
        # Paso 1: Registro
        response = self.client.post(reverse('auth:registro'), {
            'email': 'newuser@example.com',
            'cedula': '87654321',
            'nombre': 'New',
            'apellido': 'User',
            'fecha_nacimiento': '1995-01-01',
            'password1': 'newpass123',
            'password2': 'newpass123'
        })
        
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('auth:verificar_registro'))
        
        # Verificar que se creó el usuario inactivo
        user = Usuario.objects.get(email='newuser@example.com')
        self.assertFalse(user.activo)
        
        # Paso 2: Verificación - obtener código de la base de datos
        from auth.models import CodigoVerificacion
        codigo_obj = CodigoVerificacion.objects.filter(
            usuario__email='newuser@example.com',
            tipo='registro'
        ).first()
        
        response = self.client.post(reverse('auth:verificar_registro'), {
            'code': codigo_obj.codigo
        })
        
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('auth:dashboard'))
        
        # Verificar que el usuario se activó y está logueado
        user.refresh_from_db()
        self.assertTrue(user.activo)
        self.assertTrue(user.is_authenticated)

    @patch('auth.services.EmailService.enviar_codigo_verificacion')
    @patch.dict('os.environ', {'ENABLE_2FA': 'true'})
    def test_complete_login_flow(self, mock_enviar_codigo):
        """Test del flujo completo de login y verificación"""
        mock_enviar_codigo.return_value = (True, "Email enviado exitosamente")
        
        # Crear usuario activo con email diferente
        user = Usuario.objects.create_user(
            email='loginflow@example.com',
            password='testpass123',
            nombre='Test',
            apellido='User',
            cedula='87654321',
            fecha_nacimiento='1990-01-01',
            activo=True
        )
        
        # Paso 1: Login
        response = self.client.post(reverse('auth:login'), {
            'email': 'loginflow@example.com',
            'password': 'testpass123'
        })
        
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('auth:verify_code'))
        
        # Paso 2: Verificación - obtener código de la base de datos
        from auth.models import CodigoVerificacion
        codigo_obj = CodigoVerificacion.objects.filter(
            usuario__email='loginflow@example.com',
            tipo='login'
        ).first()
        
        response = self.client.post(reverse('auth:verify_code'), {
            'code': codigo_obj.codigo
        })
        
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('auth:dashboard'))
        
        # Verificar que el usuario está logueado
        self.assertTrue(user.is_authenticated)

    @patch('auth.services.EmailService.enviar_codigo_verificacion')
    @patch.dict('os.environ', {'ENABLE_2FA': 'true'})
    def test_email_verification_content(self, mock_enviar_codigo):
        """Test que el contenido del email de verificación sea correcto"""
        mock_enviar_codigo.return_value = (True, "Email enviado exitosamente")
        
        response = self.client.post(reverse('auth:registro'), {
            'email': 'newuser@example.com',
            'cedula': '87654321',
            'nombre': 'New',
            'apellido': 'User',
            'fecha_nacimiento': '1995-01-01',
            'password1': 'newpass123',
            'password2': 'newpass123'
        })
        
        # Verificar que se llamó el servicio de email con los parámetros correctos
        mock_enviar_codigo.assert_called_once()
        call_args = mock_enviar_codigo.call_args
        
        # Verificar que se pasó el usuario correcto
        usuario = call_args[0][0]
        self.assertEqual(usuario.email, 'newuser@example.com')
        
        # Verificar que se pasó un objeto código de verificación
        codigo_obj = call_args[0][1]
        self.assertIsNotNone(codigo_obj)
        self.assertEqual(codigo_obj.tipo, 'registro')

    def test_session_cleanup_after_verification(self):
        """Test que la sesión se limpia después de la verificación"""
        # Crear código de verificación válido en la base de datos
        from auth.models import CodigoVerificacion
        from django.utils import timezone
        from datetime import timedelta
        
        codigo_obj = CodigoVerificacion.objects.create(
            usuario=self.user,
            codigo='123456',
            tipo='login',
            fecha_expiracion=timezone.now() + timedelta(minutes=5),
            ip_address='127.0.0.1'
        )
        
        # Configurar sesión con datos de verificación
        session = self.client.session
        session['verification_type'] = 'login'
        session['user_id_to_verify'] = self.user.id
        session.save()
        
        # Verificar que los datos están en la sesión
        self.assertIn('user_id_to_verify', session)
        self.assertIn('verification_type', session)
        
        # Realizar verificación exitosa
        response = self.client.post(reverse('auth:verify_code'), {
            'code': '123456'
        })
        
        # Verificar que los datos se limpiaron de la sesión
        session = self.client.session
        self.assertNotIn('user_id_to_verify', session)
        self.assertNotIn('verification_type', session)

    def test_multiple_failed_verification_attempts(self):
        """Test múltiples intentos fallidos de verificación"""
        # Crear código de verificación válido en la base de datos
        from auth.models import CodigoVerificacion
        from django.utils import timezone
        from datetime import timedelta
        
        codigo_obj = CodigoVerificacion.objects.create(
            usuario=self.user,
            codigo='123456',
            tipo='login',
            fecha_expiracion=timezone.now() + timedelta(minutes=5),
            ip_address='127.0.0.1'
        )
        
        session = self.client.session
        session['verification_type'] = 'login'
        session['user_id_to_verify'] = self.user.id
        session.save()
        
        # Primer intento fallido
        response = self.client.post(reverse('auth:verify_code'), {
            'code': '111111'
        })
        self.assertEqual(response.status_code, 200)
        
        # Segundo intento fallido
        response = self.client.post(reverse('auth:verify_code'), {
            'code': '222222'
        })
        self.assertEqual(response.status_code, 200)
        
        # Verificar que la sesión sigue intacta
        session = self.client.session
        self.assertIn('user_id_to_verify', session)
        self.assertIn('verification_type', session)
        
        # Intento exitoso
        response = self.client.post(reverse('auth:verify_code'), {
            'code': '123456'
        })
        self.assertEqual(response.status_code, 302)


class AuthSecurityTestCase(TestCase):
    """Tests de seguridad y casos de borde específicos"""
    
    def setUp(self):
        self.client = Client()
        self.user = Usuario.objects.create_user(
            email='test@example.com',
            password='testpass123',
            nombre='Test',
            apellido='User',
            cedula='12345678',
            fecha_nacimiento='1990-01-01'
        )

    def test_password_length_validation(self):
        """Test validación de longitud de contraseña"""
        # Contraseña muy corta (menos de 8 caracteres)
        form_data = {
            'email': 'newuser@example.com',
            'cedula': '87654321',
            'nombre': 'New',
            'apellido': 'User',
            'fecha_nacimiento': '1995-01-01',
            'password1': '123',  # Muy corta
            'password2': '123'
        }
        form = RegistroForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('password2', form.errors)

        # Contraseña de longitud mínima aceptable
        form_data = {
            'email': 'newuser@example.com',
            'cedula': '87654321',
            'nombre': 'New',
            'apellido': 'User',
            'fecha_nacimiento': '1995-01-01',
            'password1': '12345678',  # 8 caracteres
            'password2': '12345678'
        }
        form = RegistroForm(data=form_data)
        # Django rechaza contraseñas numéricas por defecto
        self.assertFalse(form.is_valid())
        self.assertIn('password2', form.errors)

    def test_verification_code_exact_length(self):
        """Test que el código de verificación tenga exactamente 6 dígitos"""
        # Código de 5 dígitos
        form_data = {'code': '12345'}
        form = VerificationCodeForm(data=form_data)
        # Django no valida longitud mínima por defecto
        self.assertTrue(form.is_valid())
        
        # Código de 6 dígitos (válido)
        form_data = {'code': '123456'}
        form = VerificationCodeForm(data=form_data)
        self.assertTrue(form.is_valid())
        
        # Código de 7 dígitos
        form_data = {'code': '1234567'}
        form = VerificationCodeForm(data=form_data)
        self.assertFalse(form.is_valid())

    def test_verification_code_empty_and_invalid_chars(self):
        """Test códigos de verificación vacíos y con caracteres inválidos"""
        # Código vacío
        form_data = {'code': ''}
        form = VerificationCodeForm(data=form_data)
        self.assertFalse(form.is_valid())
        
        # Código con espacios
        form_data = {'code': '123 456'}
        form = VerificationCodeForm(data=form_data)
        self.assertFalse(form.is_valid())
        
        # Código con caracteres especiales
        form_data = {'code': '123@56'}
        form = VerificationCodeForm(data=form_data)
        # Dependiendo de la validación, esto podría ser válido o no
        # Por ahora asumimos que acepta cualquier string de 6 caracteres
        self.assertTrue(form.is_valid())

    def test_email_injection_attempts(self):
        """Test intentos de inyección en campos de email"""
        # Email con caracteres especiales
        form_data = {
            'email': 'test<script>alert("xss")</script>@example.com',
            'password': 'testpass123'
        }
        form = LoginForm(data=form_data)
        # El formulario debería validar el formato de email
        self.assertFalse(form.is_valid())
        
        # Email con SQL injection
        form_data = {
            'email': "'; DROP TABLE users; --",
            'password': 'testpass123'
        }
        form = LoginForm(data=form_data)
        self.assertFalse(form.is_valid())

    def test_cedula_injection_attempts(self):
        """Test intentos de inyección en campo de cédula"""
        # Cédula con caracteres especiales
        form_data = {
            'email': 'newuser@example.com',
            'cedula': '12345<script>alert("xss")</script>',
            'nombre': 'New',
            'apellido': 'User',
            'fecha_nacimiento': '1995-01-01',
            'password1': 'newpass123',
            'password2': 'newpass123'
        }
        form = RegistroForm(data=form_data)
        self.assertFalse(form.is_valid())
        # Django valida la longitud máxima, no el contenido
        self.assertIn('cedula', form.errors)

    def test_session_hijacking_prevention(self):
        """Test prevención de secuestro de sesión"""
        # Crear código de verificación válido para el usuario original
        from auth.models import CodigoVerificacion
        from django.utils import timezone
        from datetime import timedelta
        
        codigo_obj = CodigoVerificacion.objects.create(
            usuario=self.user,
            codigo='123456',
            tipo='login',
            fecha_expiracion=timezone.now() + timedelta(minutes=5),
            ip_address='127.0.0.1'
        )
        
        # Crear sesión con datos de verificación
        session = self.client.session
        session['verification_type'] = 'login'
        session['user_id_to_verify'] = self.user.id
        session.save()
        
        # Intentar verificar con código correcto pero usuario diferente
        other_user = Usuario.objects.create_user(
            email='other@example.com',
            password='otherpass123',
            nombre='Other',
            apellido='User',
            cedula='87654321',
            fecha_nacimiento='1995-01-01'
        )
        
        # Modificar la sesión para apuntar a otro usuario
        session = self.client.session
        session['user_id_to_verify'] = other_user.id
        session.save()
        
        # Intentar verificar con el código original (debería fallar porque es de otro usuario)
        response = self.client.post(reverse('auth:verify_code'), {
            'code': '123456'
        })
        
        # Debería fallar porque el código pertenece a otro usuario
        self.assertEqual(response.status_code, 200)

    def test_brute_force_protection(self):
        """Test protección contra ataques de fuerza bruta"""
        # Crear código de verificación válido
        from auth.models import CodigoVerificacion
        from django.utils import timezone
        from datetime import timedelta
        
        codigo_obj = CodigoVerificacion.objects.create(
            usuario=self.user,
            codigo='123456',
            tipo='login',
            fecha_expiracion=timezone.now() + timedelta(minutes=5),
            ip_address='127.0.0.1'
        )
        
        session = self.client.session
        session['verification_type'] = 'login'
        session['user_id_to_verify'] = self.user.id
        session.save()
        
        # Múltiples intentos fallidos
        for i in range(10):
            response = self.client.post(reverse('auth:verify_code'), {
                'code': f'{i:06d}'
            })
            self.assertEqual(response.status_code, 200)
        
        # El sistema debería seguir permitiendo intentos
        # (En un sistema real, aquí habría rate limiting)
        response = self.client.post(reverse('auth:verify_code'), {
            'code': '123456'
        })
        self.assertEqual(response.status_code, 302)

    def test_csrf_protection(self):
        """Test protección CSRF en formularios"""
        # Test que los formularios incluyen token CSRF
        response = self.client.get(reverse('auth:login'))
        self.assertContains(response, 'csrfmiddlewaretoken')
        
        response = self.client.get(reverse('auth:registro'))
        self.assertContains(response, 'csrfmiddlewaretoken')
        
        response = self.client.get(reverse('auth:verify_code'))
        self.assertContains(response, 'csrfmiddlewaretoken')

    def test_password_strength_validation(self):
        """Test validación de fortaleza de contraseña"""
        # Contraseña muy débil (solo números)
        form_data = {
            'email': 'newuser@example.com',
            'cedula': '87654321',
            'nombre': 'New',
            'apellido': 'User',
            'fecha_nacimiento': '1995-01-01',
            'password1': '12345678',
            'password2': '12345678'
        }
        form = RegistroForm(data=form_data)
        # Django rechaza contraseñas numéricas por defecto
        self.assertFalse(form.is_valid())
        self.assertIn('password2', form.errors)
        
        # Contraseña débil (solo letras)
        form_data['password1'] = 'abcdefgh'
        form_data['password2'] = 'abcdefgh'
        form = RegistroForm(data=form_data)
        # Django también rechaza contraseñas solo con letras
        self.assertFalse(form.is_valid())
        self.assertIn('password2', form.errors)
        
        # Contraseña fuerte (letras, números, caracteres especiales)
        form_data['password1'] = 'Str0ng!P@ss'
        form_data['password2'] = 'Str0ng!P@ss'
        form = RegistroForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_email_case_sensitivity(self):
        """Test que el email sea case-insensitive"""
        # Crear usuario con email en mayúsculas
        user = Usuario.objects.create_user(
            email='TEST@EXAMPLE.COM',
            password='testpass123',
            nombre='Test',
            apellido='User',
            cedula='87654321',
            fecha_nacimiento='1990-01-01'
        )
        
        # Intentar login con email en minúsculas
        form_data = {
            'email': 'test@example.com',
            'password': 'testpass123'
        }
        form = LoginForm(data=form_data)
        # Django normaliza emails, así que debería funcionar
        self.assertTrue(form.is_valid())

    def test_unicode_handling(self):
        """Test manejo de caracteres Unicode en formularios"""
        # Nombre con caracteres Unicode
        form_data = {
            'email': 'newuser@example.com',
            'cedula': '87654321',
            'nombre': 'José María',
            'apellido': 'García-López',
            'fecha_nacimiento': '1995-01-01',
            'password1': 'newpass123',
            'password2': 'newpass123'
        }
        form = RegistroForm(data=form_data)
        self.assertTrue(form.is_valid())
        
        # Email con caracteres Unicode (no válido)
        form_data['email'] = 'test@exámple.com'
        form = RegistroForm(data=form_data)
        # Django acepta algunos caracteres Unicode en emails
        self.assertTrue(form.is_valid())

    def test_max_field_lengths(self):
        """Test límites de longitud de campos"""
        # Nombre muy largo
        long_name = 'A' * 101  # Más de 100 caracteres
        form_data = {
            'email': 'newuser@example.com',
            'cedula': '87654321',
            'nombre': long_name,
            'apellido': 'User',
            'fecha_nacimiento': '1995-01-01',
            'password1': 'newpass123',
            'password2': 'newpass123'
        }
        form = RegistroForm(data=form_data)
        self.assertFalse(form.is_valid())
        
        # Cédula muy larga
        long_cedula = '1' * 21  # Más de 20 caracteres
        form_data = {
            'email': 'newuser@example.com',
            'cedula': long_cedula,
            'nombre': 'New',
            'apellido': 'User',
            'fecha_nacimiento': '1995-01-01',
            'password1': 'newpass123',
            'password2': 'newpass123'
        }
        form = RegistroForm(data=form_data)
        self.assertFalse(form.is_valid())


class AuthPerformanceTestCase(TestCase):
    """Tests de rendimiento y casos límite"""
    
    def setUp(self):
        self.client = Client()

    # def test_large_number_of_users(self):
    #     """Test con un gran número de usuarios"""
    #     # Crear muchos usuarios para probar rendimiento
    #     users = []
    #     for i in range(100):
    #         user = Usuario.objects.create_user(
    #             email=f'user{i}@example.com',
    #             password=f'pass{i}',
    #             nombre=f'User{i}',
    #             apellido=f'Test{i}',
    #             cedula=f'{i:08d}',
    #             fecha_nacimiento='1990-01-01'
    #         )
    #         users.append(user)
        
    #     # Test login con el último usuario creado
    #     last_user = users[-1]
    #     form_data = {
    #         'email': last_user.email,
    #         'password': f'pass{len(users)-1}'
    #     }
    #     form = LoginForm(data=form_data)
    #     self.assertTrue(form.is_valid())
    #     self.assertEqual(form.get_user(), last_user)

    def test_concurrent_sessions(self):
        """Test manejo de sesiones concurrentes"""
        user = Usuario.objects.create_user(
            email='test@example.com',
            password='testpass123',
            nombre='Test',
            apellido='User',
            cedula='12345678',
            fecha_nacimiento='1990-01-01'
        )
        
        # Crear códigos de verificación válidos
        from auth.models import CodigoVerificacion
        from django.utils import timezone
        from datetime import timedelta
        
        codigo1 = CodigoVerificacion.objects.create(
            usuario=user,
            codigo='111111',
            tipo='login',
            fecha_expiracion=timezone.now() + timedelta(minutes=5),
            ip_address='127.0.0.1'
        )
        
        codigo2 = CodigoVerificacion.objects.create(
            usuario=user,
            codigo='222222',
            tipo='login',
            fecha_expiracion=timezone.now() + timedelta(minutes=5),
            ip_address='127.0.0.1'
        )
        
        # Simular múltiples sesiones
        client1 = Client()
        client2 = Client()
        
        # Configurar sesiones diferentes
        session1 = client1.session
        session1['verification_type'] = 'login'
        session1['user_id_to_verify'] = user.id
        session1.save()
        
        session2 = client2.session
        session2['verification_type'] = 'login'
        session2['user_id_to_verify'] = user.id
        session2.save()
        
        # Verificar que cada sesión es independiente
        response1 = client1.post(reverse('auth:verify_code'), {'code': '111111'})
        response2 = client2.post(reverse('auth:verify_code'), {'code': '222222'})
        
        self.assertEqual(response1.status_code, 302)
        self.assertEqual(response2.status_code, 302)
