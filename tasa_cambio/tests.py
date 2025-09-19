from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from decimal import Decimal

from .models import TasaCambio
from monedas.models import Moneda

User = get_user_model()


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
            precio_base=Decimal('1250'),
            comision_compra=Decimal('50'),
            comision_venta=Decimal('60'),
            fecha_vigencia=timezone.now(),
            es_activa=True
        )
    
    def test_crear_tasa_cambio(self):
        """Prueba la creación de una tasa de cambio"""
        self.assertEqual(self.tasa_cambio.moneda, self.moneda)
        self.assertEqual(self.tasa_cambio.precio_base, Decimal('1250'))
        self.assertEqual(self.tasa_cambio.comision_compra, Decimal('50'))
        self.assertEqual(self.tasa_cambio.comision_venta, Decimal('60'))
        self.assertTrue(self.tasa_cambio.es_activa)
    
    def test_spread_calculation(self):
        """Prueba el cálculo del spread"""
        expected_spread = Decimal('110')  # 1310 - 1200
        self.assertEqual(self.tasa_cambio.spread, expected_spread)
    
    def test_spread_porcentual_calculation(self):
        """Prueba el cálculo del spread porcentual"""
        # spread = (precio_base + comision_venta) - (precio_base - comision_compra) = comision_venta + comision_compra = 60 + 50 = 110
        # precio_compra = precio_base - comision_compra = 1250 - 50 = 1200
        # porcentaje = (110 / 1200) * 100
        expected_percentage = (Decimal('110') / Decimal('1200')) * 100
        self.assertEqual(self.tasa_cambio.spread_porcentual, expected_percentage)
    
    def test_formatear_tasas(self):
        """Prueba el formateo de las tasas"""
        self.assertEqual(self.tasa_cambio.formatear_tasa_compra(), "1200.00")
        self.assertEqual(self.tasa_cambio.formatear_tasa_venta(), "1310.00")
    
    def test_str_representation(self):
        """Prueba la representación en string del modelo"""
        expected_str = "Dólar Estadounidense: Base 1250 - Com. C/V 50/60"
        self.assertEqual(str(self.tasa_cambio), expected_str)
    
    def test_auto_desactivar_anterior(self):
        """Prueba que se desactive automáticamente la cotización anterior"""
        # Crear nueva cotización para la misma moneda
        nueva_tasa = TasaCambio.objects.create(
            moneda=self.moneda,
            precio_base=Decimal('1260'),
            comision_compra=Decimal('60'),
            comision_venta=Decimal('65'),
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
            'precio_base': '1250',
            'comision_compra': '50',
            'comision_venta': '60',
            'fecha_vigencia': timezone.now().strftime('%Y-%m-%dT%H:%M'),
            'es_activa': True
        }
        
        form = TasaCambioForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_form_invalid_precio_compra_negativo(self):
        """Prueba que el precio de compra resultante no puede ser negativo o cero"""
        from .forms import TasaCambioForm
        
        form_data = {
            'moneda': self.moneda.id,
            'precio_base': '100',
            'comision_compra': '200',  # Comisión mayor que base
            'comision_venta': '50',
            'fecha_vigencia': timezone.now().strftime('%Y-%m-%dT%H:%M'),
            'es_activa': True
        }
        
        form = TasaCambioForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('precio de compra', str(form.errors))
    
    def test_form_invalid_precio_base_cero(self):
        """Prueba que el precio base no puede ser cero o negativo"""
        from .forms import TasaCambioForm
        
        form_data = {
            'moneda': self.moneda.id,
            'precio_base': '0',
            'comision_compra': '50',
            'comision_venta': '60',
            'fecha_vigencia': timezone.now().strftime('%Y-%m-%dT%H:%M'),
            'es_activa': True
        }
        
        form = TasaCambioForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('mayor o igual a 1e-08', str(form.errors))


class TasaCambioViewTest(TestCase):
    """Pruebas para las vistas de TasaCambio"""
    
    def setUp(self):
        """Configuración inicial para las pruebas"""
        # Crear usuario de prueba
        self.user = User.objects.create_user(
            email='testuser@example.com',
            password='testpass123',
            nombre='Test',
            apellido='User',
            cedula='12345678'
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
            precio_base=Decimal('1250'),
            comision_compra=Decimal('50'),
            comision_venta=Decimal('60'),
            fecha_vigencia=timezone.now(),
            es_activa=True
        )
        
        # Crear permisos
        content_type = ContentType.objects.get_for_model(TasaCambio)
        self.view_permission = Permission.objects.get(
            codename='view_tasacambio',
            content_type=content_type,
        )
        self.add_permission = Permission.objects.get(
            codename='add_tasacambio',
            content_type=content_type,
        )
        self.change_permission = Permission.objects.get(
            codename='change_tasacambio',
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
        self.client.login(username='testuser@example.com', password='testpass123')
    
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
            'precio_base': '1260',
            'comision_compra': '60',
            'comision_venta': '70',
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
