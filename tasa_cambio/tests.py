from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth.models import User, Permission
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from decimal import Decimal

from .models import TasaCambio
from monedas.models import Moneda


class TasaCambioModelTest(TestCase):
    """Pruebas para el modelo TasaCambio"""
    
    def setUp(self):
        """Configuración inicial para las pruebas"""
        # Crear moneda de prueba
        self.moneda = Moneda.objects.create(
            nombre="Dólar Estadounidense",
            codigo="USD",
            simbolo="$",
            decimales=2,
            es_activa=True
        )
        
        # Crear tasa de cambio de prueba
        self.tasa_cambio = TasaCambio.objects.create(
            moneda=self.moneda,
            tasa_compra=Decimal('1.2500'),
            tasa_venta=Decimal('1.2550'),
            fecha_vigencia=timezone.now(),
            es_activa=True
        )
    
    def test_crear_tasa_cambio(self):
        """Prueba la creación de una tasa de cambio"""
        self.assertEqual(self.tasa_cambio.moneda, self.moneda)
        self.assertEqual(self.tasa_cambio.tasa_compra, Decimal('1.2500'))
        self.assertEqual(self.tasa_cambio.tasa_venta, Decimal('1.2550'))
        self.assertTrue(self.tasa_cambio.es_activa)
    
    def test_spread_calculation(self):
        """Prueba el cálculo del spread"""
        expected_spread = Decimal('0.0050')
        self.assertEqual(self.tasa_cambio.spread, expected_spread)
    
    def test_spread_porcentual_calculation(self):
        """Prueba el cálculo del spread porcentual"""
        expected_percentage = (Decimal('0.0050') / Decimal('1.2500')) * 100
        self.assertEqual(self.tasa_cambio.spread_porcentual, expected_percentage)
    
    def test_formatear_tasas(self):
        """Prueba el formateo de las tasas"""
        self.assertEqual(self.tasa_cambio.formatear_tasa_compra(), "1.25")
        self.assertEqual(self.tasa_cambio.formatear_tasa_venta(), "1.26")
    
    def test_str_representation(self):
        """Prueba la representación en string del modelo"""
        expected_str = "Dólar Estadounidense: Compra 1.2500 - Venta 1.2550"
        self.assertEqual(str(self.tasa_cambio), expected_str)
    
    def test_auto_desactivar_anterior(self):
        """Prueba que se desactive automáticamente la cotización anterior"""
        # Crear nueva cotización para la misma moneda
        nueva_tasa = TasaCambio.objects.create(
            moneda=self.moneda,
            tasa_compra=Decimal('1.2600'),
            tasa_venta=Decimal('1.2650'),
            fecha_vigencia=timezone.now(),
            es_activa=True
        )
        
        # Verificar que la anterior se desactivó
        self.tasa_cambio.refresh_from_db()
        self.assertFalse(self.tasa_cambio.es_activa)
        self.assertTrue(nueva_tasa.es_activa)


class TasaCambioFormTest(TestCase):
    """Pruebas para el formulario TasaCambioForm"""
    
    def setUp(self):
        """Configuración inicial para las pruebas"""
        self.moneda = Moneda.objects.create(
            nombre="Dólar Estadounidense",
            codigo="USD",
            simbolo="$",
            decimales=2,
            es_activa=True
        )
    
    def test_form_valid_data(self):
        """Prueba el formulario con datos válidos"""
        from .forms import TasaCambioForm
        
        form_data = {
            'moneda': self.moneda.id,
            'tasa_compra': '1.2500',
            'tasa_venta': '1.2550',
            'fecha_vigencia': timezone.now().strftime('%Y-%m-%dT%H:%M'),
            'es_activa': True
        }
        
        form = TasaCambioForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_form_invalid_tasa_venta_menor(self):
        """Prueba que la tasa de venta debe ser mayor que la de compra"""
        from .forms import TasaCambioForm
        
        form_data = {
            'moneda': self.moneda.id,
            'tasa_compra': '1.2550',
            'tasa_venta': '1.2500',  # Menor que compra
            'fecha_vigencia': timezone.now().strftime('%Y-%m-%dT%H:%M'),
            'es_activa': True
        }
        
        form = TasaCambioForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('tasa de venta debe ser mayor', str(form.errors))
    
    def test_form_invalid_tasas_cero(self):
        """Prueba que las tasas no pueden ser cero o negativas"""
        from .forms import TasaCambioForm
        
        form_data = {
            'moneda': self.moneda.id,
            'tasa_compra': '0',
            'tasa_venta': '1.2550',
            'fecha_vigencia': timezone.now().strftime('%Y-%m-%dT%H:%M'),
            'es_activa': True
        }
        
        form = TasaCambioForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('mayor que cero', str(form.errors))


class TasaCambioViewTest(TestCase):
    """Pruebas para las vistas de TasaCambio"""
    
    def setUp(self):
        """Configuración inicial para las pruebas"""
        # Crear usuario de prueba
        self.user = User.objects.create_user(
            username='testuser',
            password='testpass123'
        )
        
        # Crear moneda de prueba
        self.moneda = Moneda.objects.create(
            nombre="Dólar Estadounidense",
            codigo="USD",
            simbolo="$",
            decimales=2,
            es_activa=True
        )
        
        # Crear tasa de cambio de prueba
        self.tasa_cambio = TasaCambio.objects.create(
            moneda=self.moneda,
            tasa_compra=Decimal('1.2500'),
            tasa_venta=Decimal('1.2550'),
            fecha_vigencia=timezone.now(),
            es_activa=True
        )
        
        # Crear permisos
        content_type = ContentType.objects.get_for_model(TasaCambio)
        self.view_permission = Permission.objects.create(
            codename='view_tasacambio',
            name='Can view tasa cambio',
            content_type=content_type,
        )
        self.add_permission = Permission.objects.create(
            codename='add_tasacambio',
            name='Can add tasa cambio',
            content_type=content_type,
        )
        self.change_permission = Permission.objects.create(
            codename='change_tasacambio',
            name='Can change tasa cambio',
            content_type=content_type,
        )
        
        # Asignar permisos al usuario
        self.user.user_permissions.add(
            self.view_permission,
            self.add_permission,
            self.change_permission
        )
        
        # Crear cliente de prueba
        self.client = Client()
        self.client.login(username='testuser', password='testpass123')
    
    def test_list_view_with_permission(self):
        """Prueba la vista de lista con permisos"""
        response = self.client.get(reverse('tasa_cambio:tasacambio_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Dólar Estadounidense')
    
    def test_list_view_without_permission(self):
        """Prueba la vista de lista sin permisos"""
        self.user.user_permissions.clear()
        response = self.client.get(reverse('tasa_cambio:tasacambio_list'))
        self.assertEqual(response.status_code, 403)
    
    def test_create_view_with_permission(self):
        """Prueba la vista de creación con permisos"""
        response = self.client.get(reverse('tasa_cambio:tasacambio_create'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Crear Nueva Cotización')
    
    def test_create_view_without_permission(self):
        """Prueba la vista de creación sin permisos"""
        self.user.user_permissions.remove(self.add_permission)
        response = self.client.get(reverse('tasa_cambio:tasacambio_create'))
        self.assertEqual(response.status_code, 403)
    
    def test_create_tasa_cambio(self):
        """Prueba la creación de una tasa de cambio"""
        form_data = {
            'moneda': self.moneda.id,
            'tasa_compra': '1.2600',
            'tasa_venta': '1.2650',
            'fecha_vigencia': timezone.now().strftime('%Y-%m-%dT%H:%M'),
            'es_activa': True
        }
        
        response = self.client.post(
            reverse('tasa_cambio:tasacambio_create'),
            data=form_data
        )
        
        self.assertEqual(response.status_code, 302)  # Redirect después de crear
        self.assertEqual(TasaCambio.objects.count(), 2)
    
    def test_toggle_status_with_permission(self):
        """Prueba el toggle de estado con permisos"""
        response = self.client.post(
            reverse('tasa_cambio:toggle_status', args=[self.tasa_cambio.id]),
            data={'es_activa': False},
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 200)
        self.tasa_cambio.refresh_from_db()
        self.assertFalse(self.tasa_cambio.es_activa)
    
    def test_toggle_status_without_permission(self):
        """Prueba el toggle de estado sin permisos"""
        self.user.user_permissions.remove(self.change_permission)
        response = self.client.post(
            reverse('tasa_cambio:toggle_status', args=[self.tasa_cambio.id]),
            data={'es_activa': False},
            content_type='application/json'
        )
        
        self.assertEqual(response.status_code, 403)
    
    def test_dashboard_view(self):
        """Prueba la vista del dashboard"""
        response = self.client.get(reverse('tasa_cambio:dashboard'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Dashboard de Cotizaciones')
        self.assertContains(response, '1')  # Total de cotizaciones


class TasaCambioURLTest(TestCase):
    """Pruebas para las URLs de TasaCambio"""
    
    def test_tasacambio_list_url(self):
        """Prueba la URL de lista de tasas de cambio"""
        url = reverse('tasa_cambio:tasacambio_list')
        self.assertEqual(url, '/tasa-cambio/')
    
    def test_tasacambio_create_url(self):
        """Prueba la URL de creación de tasas de cambio"""
        url = reverse('tasa_cambio:tasacambio_create')
        self.assertEqual(url, '/tasa-cambio/crear/')
    
    def test_tasacambio_dashboard_url(self):
        """Prueba la URL del dashboard"""
        url = reverse('tasa_cambio:dashboard')
        self.assertEqual(url, '/tasa-cambio/dashboard/')
    
    def test_toggle_status_url(self):
        """Prueba la URL de toggle de estado"""
        url = reverse('tasa_cambio:toggle_status', args=[1])
        self.assertEqual(url, '/tasa-cambio/toggle-status/1/')
