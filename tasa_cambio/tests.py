from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from decimal import Decimal

from .models import TasaCambio
from monedas.models import Moneda
from .forms import TasaCambioForm

User = get_user_model()


class TasaCambioModelTest(TestCase):
    """Tests para el modelo TasaCambio"""
    
    def setUp(self):
        # Crear moneda de prueba
        self.moneda = Moneda.objects.create(
            codigo='USD',
            nombre='Dólar Estadounidense',
            simbolo='$',
            decimales=2
        )
    
    def test_crear_tasa_cambio(self):
        """Prueba la creación de una cotización"""
        tasa = TasaCambio.objects.create(
            moneda=self.moneda,
            precio_base=7500,
            comision_compra=50,
            comision_venta=75,
            es_activa=True
        )
        
        self.assertEqual(tasa.moneda, self.moneda)
        self.assertEqual(tasa.precio_base, 7500)
        self.assertEqual(tasa.comision_compra, 50)
        self.assertEqual(tasa.comision_venta, 75)
        self.assertTrue(tasa.es_activa)
    
    def test_tasa_compra_calculation(self):
        """Prueba el cálculo de la tasa de compra"""
        tasa = TasaCambio(
            moneda=self.moneda,
            precio_base=7500,
            comision_compra=50,
            comision_venta=75
        )
        
        expected = 7500 - 50  # precio_base - comision_compra
        self.assertEqual(tasa.tasa_compra, expected)
    
    def test_tasa_venta_calculation(self):
        """Prueba el cálculo de la tasa de venta"""
        tasa = TasaCambio(
            moneda=self.moneda,
            precio_base=7500,
            comision_compra=50,
            comision_venta=75
        )
        
        expected = 7500 + 75  # precio_base + comision_venta
        self.assertEqual(tasa.tasa_venta, expected)
    
    def test_spread_calculation(self):
        """Prueba el cálculo del spread"""
        tasa = TasaCambio(
            moneda=self.moneda,
            precio_base=7500,
            comision_compra=50,
            comision_venta=75
        )
        
        expected = (50 + 75)  # comision_compra + comision_venta
        self.assertEqual(tasa.spread, expected)
    
    def test_spread_porcentual_calculation(self):
        """Prueba el cálculo del spread porcentual"""
        tasa = TasaCambio(
            moneda=self.moneda,
            precio_base=7500,
            comision_compra=50,
            comision_venta=75
        )
        
        # spread = 50 + 75 = 125
        # precio_compra = 7500 - 50 = 7450
        # precio_venta = 7500 + 75 = 7575
        # spread_porcentual = ((7575 - 7450) / 7450) * 100
        expected = ((7575 - 7450) / 7450) * 100
        self.assertAlmostEqual(tasa.spread_porcentual, expected, places=4)
    
    def test_str_representation(self):
        """Prueba la representación en string del modelo"""
        tasa = TasaCambio(
            moneda=self.moneda,
            precio_base=7500,
            comision_compra=50,
            comision_venta=75
        )
        
        expected = f"Dólar Estadounidense: Base 7500 - Com. C/V 50/75"
        self.assertEqual(str(tasa), expected)
    
    def test_formatear_tasas(self):
        """Prueba el formateo de las tasas"""
        tasa = TasaCambio(
            moneda=self.moneda,
            precio_base=7500,
            comision_compra=50,
            comision_venta=75
        )
        
        self.assertEqual(tasa.formatear_precio_base(), "7500.00")
        self.assertEqual(tasa.formatear_tasa_compra(), "7450.00")
        self.assertEqual(tasa.formatear_tasa_venta(), "7575.00")
    
    def test_auto_desactivar_anterior(self):
        """Prueba que se desactive automáticamente la cotización anterior"""
        # Crear primera cotización activa
        tasa1 = TasaCambio.objects.create(
            moneda=self.moneda,
            precio_base=7500,
            comision_compra=50,
            comision_venta=75,
            es_activa=True
        )
        
        # Verificar que está activa
        self.assertTrue(tasa1.es_activa)
        
        # Crear segunda cotización activa para la misma moneda
        tasa2 = TasaCambio.objects.create(
            moneda=self.moneda,
            precio_base=7600,
            comision_compra=60,
            comision_venta=80,
            es_activa=True
        )
        
        # Refrescar desde la base de datos
        tasa1.refresh_from_db()
        
        # Verificar que la primera se desactivó y la segunda está activa
        self.assertFalse(tasa1.es_activa)
        self.assertTrue(tasa2.es_activa)


class TasaCambioFormTest(TestCase):
    """Tests para el formulario TasaCambio"""
    
    def setUp(self):
        self.moneda = Moneda.objects.create(
            codigo='USD',
            nombre='Dólar Estadounidense',
            simbolo='$',
            decimales=2
        )
    
    def test_form_valid_data(self):
        """Prueba el formulario con datos válidos"""
        form_data = {
            'moneda': self.moneda.id,
            'precio_base': '7500',
            'comision_compra': '50',
            'comision_venta': '75',
            'es_activa': True
        }
        
        form = TasaCambioForm(data=form_data)
        self.assertTrue(form.is_valid())
    
    def test_form_invalid_precio_compra_negativo(self):
        """Prueba que el precio de compra resultante no puede ser negativo o cero"""
        form_data = {
            'moneda': self.moneda.id,
            'precio_base': '100',
            'comision_compra': '200',  # Comisión mayor que base
            'comision_venta': '50',
            'es_activa': True
        }
        
        form = TasaCambioForm(data=form_data)
        self.assertFalse(form.is_valid())
        self.assertIn('El precio de compra resultante debe ser positivo', str(form.errors))
    
    def test_form_invalid_precio_base_cero(self):
        """Prueba que el precio base no puede ser cero o negativo"""
        form_data = {
            'moneda': self.moneda.id,
            'precio_base': '0',
            'comision_compra': '50',
            'comision_venta': '75',
            'es_activa': True
        }
        
        form = TasaCambioForm(data=form_data)
        self.assertFalse(form.is_valid())


class TasaCambioViewTest(TestCase):
    """Tests para las vistas de TasaCambio"""
    
    def setUp(self):
        # Crear usuario de prueba
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        
        # Crear moneda de prueba
        self.moneda = Moneda.objects.create(
            codigo='USD',
            nombre='Dólar Estadounidense',
            simbolo='$',
            decimales=2
        )
        
        # Crear cotización de prueba
        self.tasa_cambio = TasaCambio.objects.create(
            moneda=self.moneda,
            precio_base=7500,
            comision_compra=50,
            comision_venta=75,
            es_activa=True
        )
        
        self.client = Client()
    
    def test_dashboard_view(self):
        """Prueba la vista del dashboard"""
        self.client.force_login(self.user)
        response = self.client.get(reverse('tasa_cambio:dashboard'))
        # Usuario sin permisos devuelve 403
        self.assertEqual(response.status_code, 403)
    
    def test_list_view_with_permission(self):
        """Prueba la vista de lista con permisos"""
        # Agregar permiso al usuario
        content_type = ContentType.objects.get_for_model(TasaCambio)
        permission = Permission.objects.get(
            codename='view_tasacambio',
            content_type=content_type,
        )
        self.user.user_permissions.add(permission)
        
        self.client.force_login(self.user)
        response = self.client.get(reverse('tasa_cambio:tasacambio_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, self.tasa_cambio.moneda.codigo)
    
    def test_list_view_without_permission(self):
        """Prueba la vista de lista sin permisos"""
        self.client.force_login(self.user)
        response = self.client.get(reverse('tasa_cambio:tasacambio_list'))
        # Debería devolver 403 por falta de permisos
        self.assertEqual(response.status_code, 403)
    
    def test_create_view_with_permission(self):
        """Prueba la vista de creación con permisos"""
        # Agregar permiso al usuario
        content_type = ContentType.objects.get_for_model(TasaCambio)
        permission = Permission.objects.get(
            codename='add_tasacambio',
            content_type=content_type,
        )
        self.user.user_permissions.add(permission)
        
        self.client.force_login(self.user)
        response = self.client.get(reverse('tasa_cambio:tasacambio_create'))
        self.assertEqual(response.status_code, 200)
    
    def test_create_view_without_permission(self):
        """Prueba la vista de creación sin permisos"""
        self.client.force_login(self.user)
        response = self.client.get(reverse('tasa_cambio:tasacambio_create'))
        # Debería devolver 403 por falta de permisos
        self.assertEqual(response.status_code, 403)
    
    def test_create_tasa_cambio(self):
        """Prueba la creación de una cotización"""
        # Agregar permiso al usuario
        content_type = ContentType.objects.get_for_model(TasaCambio)
        permission = Permission.objects.get(
            codename='add_tasacambio',
            content_type=content_type,
        )
        self.user.user_permissions.add(permission)
        
        self.client.force_login(self.user)
        
        form_data = {
            'moneda': self.moneda.id,
            'precio_base': '7600',
            'comision_compra': '60',
            'comision_venta': '80',
            'es_activa': True
        }
        
        response = self.client.post(reverse('tasa_cambio:tasacambio_create'), data=form_data)
        self.assertEqual(response.status_code, 302)  # Redirección después del éxito
        
        # Verificar que la cotización se creó
        self.assertTrue(TasaCambio.objects.filter(precio_base=7600).exists())
    
    def test_toggle_status_with_permission(self):
        """Prueba el toggle de estado con permisos"""
        # Agregar permiso al usuario
        content_type = ContentType.objects.get_for_model(TasaCambio)
        permission = Permission.objects.get(
            codename='change_tasacambio',
            content_type=content_type,
        )
        self.user.user_permissions.add(permission)
        
        self.client.force_login(self.user)
        
        response = self.client.post(
            reverse('tasa_cambio:toggle_status', kwargs={'pk': self.tasa_cambio.pk}),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 200)
    
    def test_toggle_status_without_permission(self):
        """Prueba el toggle de estado sin permisos"""
        self.client.force_login(self.user)
        
        response = self.client.post(
            reverse('tasa_cambio:toggle_status', kwargs={'pk': self.tasa_cambio.pk}),
            HTTP_X_REQUESTED_WITH='XMLHttpRequest'
        )
        self.assertEqual(response.status_code, 403)  # Prohibido


class TasaCambioURLTest(TestCase):
    """Tests para las URLs de TasaCambio"""
    
    def test_tasacambio_list_url(self):
        """Prueba la URL de lista de cotizaciones"""
        url = reverse('tasa_cambio:tasacambio_list')
        self.assertEqual(url, '/tasa-cambio/')
    
    def test_tasacambio_create_url(self):
        """Prueba la URL de creación de cotizaciones"""
        url = reverse('tasa_cambio:tasacambio_create')
        self.assertEqual(url, '/tasa-cambio/crear/')
    
    def test_toggle_status_url(self):
        """Prueba la URL de toggle de estado"""
        url = reverse('tasa_cambio:toggle_status', kwargs={'pk': 1})
        self.assertEqual(url, '/tasa-cambio/toggle-status/1/')
    
    def test_tasacambio_dashboard_url(self):
        """Prueba la URL del dashboard"""
        url = reverse('tasa_cambio:dashboard')
        self.assertEqual(url, '/tasa-cambio/dashboard/')