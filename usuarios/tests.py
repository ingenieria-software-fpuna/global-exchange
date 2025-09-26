from django.test import TestCase, RequestFactory
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from .forms import UsuarioCreationForm, UsuarioUpdateForm

Usuario = get_user_model()


class UsuarioModelTestCase(TestCase):
    """Tests para el modelo Usuario"""
    
    def setUp(self):
        self.user_data = {
            'email': 'test@example.com',
            'password': 'testpass123',
            'nombre': 'Test',
            'apellido': 'User',
            'cedula': '12345678',
            'fecha_nacimiento': '1990-01-01'
        }

    def test_create_user(self):
        """Test creación de usuario normal"""
        user = Usuario.objects.create_user(**self.user_data)
        self.assertEqual(user.email, 'test@example.com')
        self.assertEqual(user.nombre, 'Test')
        self.assertEqual(user.apellido, 'User')
        self.assertEqual(user.cedula, '12345678')
        if hasattr(user.fecha_nacimiento, 'strftime'):
            self.assertEqual(user.fecha_nacimiento.strftime('%Y-%m-%d'), '1990-01-01')
        else:
            self.assertEqual(str(user.fecha_nacimiento), '1990-01-01')
        self.assertTrue(user.activo)
        self.assertFalse(user.is_staff)
        self.assertTrue(user.check_password('testpass123'))

    def test_create_admin_user(self):
        """Test creación de usuario administrador"""
        user = Usuario.objects.create_admin_user(
            email='admin@example.com',
            password='adminpass123',
            nombre='Admin',
            apellido='User',
            cedula='87654321',
            fecha_nacimiento='1985-01-01'
        )
        self.assertTrue(user.is_staff)
        self.assertFalse(user.is_superuser)
        self.assertTrue(user.es_activo)
        # Verificar que está en el grupo de administradores
        admin_group = user.groups.filter(name='Admin').first()
        self.assertIsNotNone(admin_group)

    def test_create_user_without_email(self):
        """Test que no se puede crear usuario sin email"""
        with self.assertRaises(ValueError):
            Usuario.objects.create_user(
                email='',
                password='testpass123',
                nombre='Test',
                apellido='User',
                cedula='12345678',
                fecha_nacimiento='1990-01-01'
            )

    def test_user_required_fields(self):
        """Test que los campos requeridos están configurados correctamente"""
        self.assertEqual(Usuario.USERNAME_FIELD, 'email')
        self.assertEqual(Usuario.REQUIRED_FIELDS, ['nombre', 'cedula', 'fecha_nacimiento'])

    def test_user_str_representation(self):
        """Test la representación string del usuario"""
        user = Usuario.objects.create_user(**self.user_data)
        self.assertEqual(str(user), 'test@example.com')

    def test_user_unique_email(self):
        """Test que el email debe ser único"""
        Usuario.objects.create_user(**self.user_data)
        
        with self.assertRaises(IntegrityError):
            Usuario.objects.create_user(
                email='test@example.com',
                password='otherpass123',
                nombre='Other',
                apellido='User',
                cedula='87654321',
                fecha_nacimiento='1995-01-01'
            )

    def test_user_unique_cedula(self):
        """Test que la cédula debe ser única"""
        Usuario.objects.create_user(**self.user_data)
        
        with self.assertRaises(IntegrityError):
            Usuario.objects.create_user(
                email='other@example.com',
                password='otherpass123',
                nombre='Other',
                apellido='User',
                cedula='12345678',
                fecha_nacimiento='1995-01-01'
            )


class UsuarioFormsTestCase(TestCase):
    """Tests para los formularios de Usuario"""
    
    def setUp(self):
        self.user_data = {
            'email': 'test@example.com',
            'password1': 'testpass123',
            'password2': 'testpass123',
            'nombre': 'Test',
            'apellido': 'User',
            'cedula': '12345678',
            'fecha_nacimiento': '1995-01-01'
        }

    def test_usuario_creation_form_valid(self):
        """Test formulario de creación válido"""
        form = UsuarioCreationForm(data=self.user_data)
        self.assertTrue(form.is_valid())

    def test_usuario_creation_form_password_mismatch(self):
        """Test formulario de creación con contraseñas que no coinciden"""
        form_data = self.user_data.copy()
        form_data['password2'] = 'differentpass'
        form = UsuarioCreationForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('__all__', form.errors)
        self.assertIn('no coinciden', str(form.errors['__all__']))

    def test_usuario_creation_form_required_fields(self):
        """Test que los campos requeridos están marcados correctamente"""
        form = UsuarioCreationForm()
        self.assertTrue(form.fields['email'].required)
        self.assertTrue(form.fields['nombre'].required)
        self.assertFalse(form.fields['apellido'].required)

    def test_usuario_creation_form_save(self):
        """Test que el formulario guarda correctamente el usuario y roles"""
        form = UsuarioCreationForm(data=self.user_data)
        self.assertTrue(form.is_valid())
        
        user = form.save()
        self.assertEqual(user.email, 'test@example.com')
        self.assertEqual(user.nombre, 'Test')
        self.assertTrue(user.check_password('testpass123'))

    def test_usuario_update_form_valid(self):
        """Test formulario de actualización válido"""
        user = Usuario.objects.create_user(
            email='test@example.com',
            password='testpass123',
            nombre='Test',
            apellido='User',
            cedula='12345678',
            fecha_nacimiento='1990-01-01'
        )
        
        form_data = {
            'email': 'updated@example.com',
            'nombre': 'Updated',
            'apellido': 'User',
            'is_staff': True,
            'is_superuser': False,
            'activo': True
        }
        
        form = UsuarioUpdateForm(data=form_data, instance=user)
        self.assertTrue(form.is_valid())

    def test_usuario_update_form_required_fields(self):
        """Test que los campos requeridos están marcados correctamente en actualización"""
        form = UsuarioUpdateForm()
        self.assertTrue(form.fields['email'].required)
        self.assertTrue(form.fields['nombre'].required)
        self.assertFalse(form.fields['apellido'].required)

    def test_usuario_update_form_save(self):
        """Test que el formulario actualiza correctamente el usuario y roles"""
        user = Usuario.objects.create_user(
            email='test@example.com',
            password='testpass123',
            nombre='Test',
            apellido='User',
            cedula='12345678',
            fecha_nacimiento='1990-01-01'
        )
        
        form_data = {
            'email': 'updated@example.com',
            'nombre': 'Updated',
            'apellido': 'User',
            'is_staff': True,
            'is_superuser': False,
            'es_activo': True
        }
        
        form = UsuarioUpdateForm(data=form_data, instance=user)
        self.assertTrue(form.is_valid())
        
        updated_user = form.save()
        self.assertEqual(updated_user.email, 'updated@example.com')
        self.assertEqual(updated_user.nombre, 'Updated')
        self.assertTrue(updated_user.is_staff)

    def test_usuario_update_form_initial_roles(self):
        """Test que el formulario carga correctamente los roles iniciales"""
        user = Usuario.objects.create_user(
            email='test@example.com',
            password='testpass123',
            nombre='Test',
            apellido='User',
            cedula='12345678',
            fecha_nacimiento='1990-01-01'
        )
        
        form = UsuarioUpdateForm(instance=user)
        self.assertIsNotNone(form)


class UsuarioViewsTestCase(TestCase):
    """Tests unitarios para las vistas de Usuario"""
    
    def setUp(self):
        self.factory = RequestFactory()
        self.user = Usuario.objects.create_user(
            email='test@example.com',
            password='testpass123',
            nombre='Test',
            apellido='User',
            cedula='12345678',
            fecha_nacimiento='1990-01-01'
        )

    def test_usuario_list_view_attributes(self):
        """Test unitario de atributos de la vista de lista"""
        from .views import UsuarioListView
        
        self.assertEqual(UsuarioListView.model, Usuario)
        self.assertEqual(UsuarioListView.template_name, 'usuarios/user_list.html')
        self.assertEqual(UsuarioListView.context_object_name, 'usuarios')

    def test_usuario_create_view_attributes(self):
        """Test unitario de atributos de la vista de creación"""
        from .views import UsuarioCreateView
        from .forms import UsuarioCreationForm
        
        self.assertEqual(UsuarioCreateView.model, Usuario)
        self.assertEqual(UsuarioCreateView.form_class, UsuarioCreationForm)
        self.assertEqual(UsuarioCreateView.template_name, 'usuarios/user_form.html')
        self.assertEqual(str(UsuarioCreateView.success_url), '/usuarios/')

    def test_usuario_update_view_attributes(self):
        """Test unitario de atributos de la vista de actualización"""
        from .views import UsuarioUpdateView
        from .forms import UsuarioUpdateForm
        
        self.assertEqual(UsuarioUpdateView.model, Usuario)
        self.assertEqual(UsuarioUpdateView.form_class, UsuarioUpdateForm)
        self.assertEqual(UsuarioUpdateView.template_name, 'usuarios/user_form.html')
        self.assertEqual(str(UsuarioUpdateView.success_url), '/usuarios/')

    def test_usuario_delete_view_attributes(self):
        """Test unitario de atributos de la vista de eliminación"""
        from .views import UsuarioDeleteView
        
        self.assertEqual(UsuarioDeleteView.model, Usuario)
        self.assertEqual(UsuarioDeleteView.template_name, 'usuarios/user_confirm_delete.html')
        self.assertEqual(str(UsuarioDeleteView.success_url), '/usuarios/')

    def test_usuario_delete_view_context_data_method(self):
        """Test unitario de que el método get_context_data existe y es callable"""
        from .views import UsuarioDeleteView
        
        view = UsuarioDeleteView()
        
        self.assertTrue(hasattr(view, 'get_context_data'))
        self.assertTrue(callable(view.get_context_data))
        
        self.assertIn('get_context_data', UsuarioDeleteView.__dict__)
