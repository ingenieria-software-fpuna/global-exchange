from django.test import TestCase
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.urls import reverse
from django.conf import settings
from .models import Moneda

User = get_user_model()  # Esto obtiene el modelo de usuario personalizado


class MonedaModelTests(TestCase):
    """Tests para el modelo Moneda"""
    
    def test_moneda_creation(self):
        """Test de creación de moneda"""
        moneda = Moneda.objects.create(
            nombre="Dólar Test",
            codigo="tst",  # Minúsculas para probar conversión
            simbolo="T$",
            decimales=2
        )
        
        # Verificar que se creó correctamente
        self.assertEqual(moneda.nombre, "Dólar Test")
        self.assertEqual(moneda.codigo, "TST")  # Debe convertirse a mayúsculas
        self.assertEqual(moneda.simbolo, "T$")
        self.assertEqual(moneda.decimales, 2)
        self.assertTrue(moneda.es_activa)  # Debe ser activa por defecto
    
    def test_moneda_str_method(self):
        """Test del método __str__"""
        moneda = Moneda.objects.create(
            nombre="Euro",
            codigo="EUR",
            simbolo="€"
        )
        self.assertEqual(str(moneda), "Euro (EUR)")
    
    def test_codigo_uppercase_conversion(self):
        """Test de conversión automática a mayúsculas del código"""
        moneda = Moneda.objects.create(
            nombre="Peso Argentino",
            codigo="ars",  # Minúsculas
            simbolo="$"
        )
        self.assertEqual(moneda.codigo, "ARS")
    
    def test_decimales_default_value(self):
        """Test del valor por defecto del campo decimales"""
        moneda = Moneda.objects.create(
            nombre="Euro",
            codigo="EUR",
            simbolo="€"
            # No especificamos decimales
        )
        self.assertEqual(moneda.decimales, 2)  # Debe ser 2 por defecto
    
    def test_decimales_custom_values(self):
        """Test de valores personalizados para decimales"""
        # Test con 0 decimales (como JPY)
        moneda_jpy = Moneda.objects.create(
            nombre="Yen Japonés",
            codigo="JPY",
            simbolo="¥",
            decimales=0
        )
        self.assertEqual(moneda_jpy.decimales, 0)
        
        # Test con muchos decimales (como criptomonedas)
        moneda_crypto = Moneda.objects.create(
            nombre="Bitcoin",
            codigo="BTC",
            simbolo="₿",
            decimales=8
        )
        self.assertEqual(moneda_crypto.decimales, 8)
        
        # Test con valor alto (sin límite máximo)
        moneda_high = Moneda.objects.create(
            nombre="Test High Decimals",
            codigo="THD",
            simbolo="T",
            decimales=18
        )
        self.assertEqual(moneda_high.decimales, 18)
    
    def test_decimales_validation(self):
        """Test de validación del campo decimales"""
        # Test valor mínimo válido
        moneda_valid = Moneda.objects.create(
            nombre="Test Moneda",
            codigo="TST",
            simbolo="T",
            decimales=0
        )
        self.assertEqual(moneda_valid.decimales, 0)
        
        # Test que no acepta valores negativos se haría con ValidationError
        # pero como usamos PositiveSmallIntegerField, Django ya lo maneja


class MonedaPermissionsTests(TestCase):
    """Tests para el sistema de permisos de monedas"""
    
    def setUp(self):
        """Configuración inicial para los tests"""
        # Crear grupos
        self.admin_group = Group.objects.create(name='Admin')
        self.analista_group = Group.objects.create(name='Analista')
        
        # Crear usuarios (usando email en lugar de username)
        self.admin_user = User.objects.create_user(
            email='admin@test.com',
            password='testpass123',
            nombre='Admin Test'
        )
        self.analista_user = User.objects.create_user(
            email='analista@test.com',
            password='testpass123',
            nombre='Analista Test'
        )
        
        # Asignar usuarios a grupos
        self.admin_user.groups.add(self.admin_group)
        self.analista_user.groups.add(self.analista_group)
        
        # Obtener permisos de monedas
        content_type = ContentType.objects.get_for_model(Moneda)
        self.view_permission = Permission.objects.get(
            content_type=content_type, codename='view_moneda'
        )
        self.add_permission = Permission.objects.get(
            content_type=content_type, codename='add_moneda'
        )
        self.change_permission = Permission.objects.get(
            content_type=content_type, codename='change_moneda'
        )
        self.delete_permission = Permission.objects.get(
            content_type=content_type, codename='delete_moneda'
        )
        
        # Asignar permisos a grupos
        # Admin: todos los permisos
        self.admin_group.permissions.add(
            self.view_permission, self.add_permission,
            self.change_permission, self.delete_permission
        )
        
        # Analista: solo view, add y change (NO delete)
        self.analista_group.permissions.add(
            self.view_permission, self.add_permission, self.change_permission
        )
    
    def test_admin_permissions(self):
        """Test de permisos del grupo Admin"""
        self.assertTrue(self.admin_user.has_perm('monedas.view_moneda'))
        self.assertTrue(self.admin_user.has_perm('monedas.add_moneda'))
        self.assertTrue(self.admin_user.has_perm('monedas.change_moneda'))
        self.assertTrue(self.admin_user.has_perm('monedas.delete_moneda'))
    
    def test_analista_permissions(self):
        """Test de permisos del grupo Analista"""
        self.assertTrue(self.analista_user.has_perm('monedas.view_moneda'))
        self.assertTrue(self.analista_user.has_perm('monedas.add_moneda'))
        self.assertTrue(self.analista_user.has_perm('monedas.change_moneda'))
        self.assertFalse(self.analista_user.has_perm('monedas.delete_moneda'))  # NO debe tener
    
    def test_no_superuser_dependency(self):
        """Test para verificar que NO dependemos de superuser"""
        # Verificar que los usuarios de prueba NO son superuser
        self.assertFalse(self.admin_user.is_superuser)
        self.assertFalse(self.analista_user.is_superuser)
        
        # Verificar que aún así tienen permisos via grupos
        self.assertTrue(self.admin_user.has_perm('monedas.view_moneda'))
        self.assertTrue(self.analista_user.has_perm('monedas.view_moneda'))


class MonedaViewsTests(TestCase):
    """Tests para las vistas de monedas"""
    
    def setUp(self):
        """Configuración inicial"""
        # Crear grupo y usuario con permisos
        self.group = Group.objects.create(name='Admin')
        self.user = User.objects.create_user(
            email='test@test.com',
            password='testpass123',
            nombre='Test User'
        )
        self.user.groups.add(self.group)
        
        # Asignar permisos
        content_type = ContentType.objects.get_for_model(Moneda)
        permissions = Permission.objects.filter(content_type=content_type)
        self.group.permissions.set(permissions)
        
        # Crear moneda de prueba
        self.moneda = Moneda.objects.create(
            nombre="Dólar Test",
            codigo="USD",
            simbolo="$"
        )
    
    def test_moneda_list_view(self):
        """Test de la vista lista"""
        self.client.login(email='test@test.com', password='testpass123')
        response = self.client.get(reverse('monedas:moneda_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Dólar Test')
    
    def test_moneda_create_view(self):
        """Test de la vista crear"""
        self.client.login(email='test@test.com', password='testpass123')
        response = self.client.get(reverse('monedas:moneda_create'))
        self.assertEqual(response.status_code, 200)
        # Verificar que el campo decimales está en el formulario
        self.assertContains(response, 'name="decimales"')
    
    def test_moneda_create_post(self):
        """Test de creación de moneda via POST"""
        self.client.login(email='test@test.com', password='testpass123')
        response = self.client.post(reverse('monedas:moneda_create'), {
            'nombre': 'Bitcoin',
            'codigo': 'BTC',
            'simbolo': '₿',
            'decimales': 8,
            'es_activa': True
        })
        # Debe redirigir después de crear exitosamente
        self.assertEqual(response.status_code, 302)
        
        # Verificar que se creó la moneda con decimales correctos
        bitcoin = Moneda.objects.get(codigo='BTC')
        self.assertEqual(bitcoin.decimales, 8)
    
    def test_moneda_update_view(self):
        """Test de la vista editar"""
        self.client.login(email='test@test.com', password='testpass123')
        response = self.client.get(reverse('monedas:moneda_update', args=[self.moneda.pk]))
        self.assertEqual(response.status_code, 200)
    
    def test_unauthorized_access(self):
        """Test de acceso sin permisos"""
        # Usuario sin login
        response = self.client.get(reverse('monedas:moneda_list'))
        self.assertEqual(response.status_code, 302)  # Redirect al login
        
        # Usuario sin permisos
        user_no_perms = User.objects.create_user(
            email='noperms@test.com',
            password='testpass123',
            nombre='No Perms User'
        )
        self.client.login(email='noperms@test.com', password='testpass123')
        response = self.client.get(reverse('monedas:moneda_list'))
        self.assertEqual(response.status_code, 403)  # Forbidden


class MonedaConfigurationTests(TestCase):
    """Tests de configuración del sistema"""
    
    def test_app_in_installed_apps(self):
        """Test que la app esté en INSTALLED_APPS"""
        self.assertIn('monedas', settings.INSTALLED_APPS)
    
    def test_urls_configuration(self):
        """Test de configuración de URLs"""
        # Verificar que las URLs existan
        try:
            reverse('monedas:moneda_list')
            reverse('monedas:moneda_create')
            self.assertTrue(True)  # Si llegamos aquí, las URLs están bien
        except Exception as e:
            self.fail(f"Error en configuración de URLs: {e}")
    
    def test_permissions_exist(self):
        """Test que los permisos existan"""
        content_type = ContentType.objects.get_for_model(Moneda)
        expected_permissions = ['view_moneda', 'add_moneda', 'change_moneda', 'delete_moneda']
        
        for perm_code in expected_permissions:
            try:
                Permission.objects.get(content_type=content_type, codename=perm_code)
            except Permission.DoesNotExist:
                self.fail(f"Permiso {perm_code} no existe")
