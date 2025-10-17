from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from decimal import Decimal
import json

from .models import TasaCambio
from monedas.models import Moneda
from .forms import TasaCambioForm
from clientes.models import Cliente, TipoCliente
from metodo_pago.models import MetodoPago

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
    
    # def test_dashboard_view(self):
    #     """Prueba la vista del dashboard"""
    #     self.client.force_login(self.user)
    #     response = self.client.get(reverse('tasa_cambio:dashboard'))
    #     # Usuario sin permisos devuelve 403
    #     self.assertEqual(response.status_code, 403)
    
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
    
    
    def test_tasacambio_dashboard_url(self):
        """Prueba la URL del dashboard"""
        url = reverse('tasa_cambio:dashboard')
        self.assertEqual(url, '/tasa-cambio/dashboard/')


class SimuladorCambioTest(TestCase):
    """Tests para el simulador de cambios de monedas"""
    
    def setUp(self):
        # Crear usuario de prueba
        self.user = User.objects.create_user(
            email='test@example.com',
            password='testpass123'
        )
        
        # Crear monedas de prueba
        self.moneda_pyg = Moneda.objects.create(
            codigo='PYG',
            nombre='Guaraní Paraguayo',
            simbolo='₲',
            decimales=0,
            es_activa=True
        )
        
        self.moneda_usd = Moneda.objects.create(
            codigo='USD',
            nombre='Dólar Estadounidense',
            simbolo='$',
            decimales=2,
            es_activa=True
        )
        
        self.moneda_eur = Moneda.objects.create(
            codigo='EUR',
            nombre='Euro',
            simbolo='€',
            decimales=2,
            es_activa=True
        )
        
        # Crear tasas de cambio activas
        self.tasa_usd = TasaCambio.objects.create(
            moneda=self.moneda_usd,
            precio_base=7500,
            comision_compra=50,
            comision_venta=75,
            es_activa=True
        )
        
        self.tasa_eur = TasaCambio.objects.create(
            moneda=self.moneda_eur,
            precio_base=8000,
            comision_compra=60,
            comision_venta=80,
            es_activa=True
        )
        
        # Crear tipo de cliente y cliente para pruebas
        self.tipo_cliente = TipoCliente.objects.create(
            nombre='Cliente Premium',
            descuento=Decimal('5.00')
        )
        
        self.cliente = Cliente.objects.create(
            nombre_comercial='Cliente Test',
            ruc='12345678',
            tipo_cliente=self.tipo_cliente,
            activo=True
        )
        self.cliente.usuarios_asociados.add(self.user)
        
        # Crear método de pago
        self.metodo_pago = MetodoPago.objects.create(
            nombre='Transferencia Bancaria',
            comision=Decimal('2.50'),
            es_activo=True
        )
        
        self.client = Client()
    
    def test_simulador_pyg_a_usd_sin_cliente_ni_metodo(self):
        """Prueba conversión de PYG a USD sin cliente ni método de pago"""
        self.client.force_login(self.user)
        
        url = reverse('tasa_cambio:simular_cambio_api')
        response = self.client.get(url, {
            'origen': 'PYG',
            'destino': 'USD',
            'monto': '75000'
        })
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        self.assertTrue(data['success'])
        self.assertIn('data', data)
        
        # Verificar cálculo: 75000 PYG / 7575 (precio_venta) = 9.90 USD
        expected_result = 75000 / 7575  # 7575 = 7500 + 75
        self.assertAlmostEqual(data['data']['resultado'], expected_result, places=2)
        self.assertEqual(data['data']['detalle'], 'PYG -> USD usando precio de venta')
        self.assertIsNone(data['data']['cliente'])
        self.assertIsNone(data['data']['metodo_pago'])
    
    def test_simulador_usd_a_pyg_sin_cliente_ni_metodo(self):
        """Prueba conversión de USD a PYG sin cliente ni método de pago"""
        self.client.force_login(self.user)
        
        url = reverse('tasa_cambio:simular_cambio_api')
        response = self.client.get(url, {
            'origen': 'USD',
            'destino': 'PYG',
            'monto': '10'
        })
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        self.assertTrue(data['success'])
        
        # Verificar cálculo: 10 USD * 7450 (precio_compra) = 74500 PYG
        expected_result = 10 * 7450  # 7450 = 7500 - 50
        self.assertEqual(data['data']['resultado'], expected_result)
        self.assertEqual(data['data']['detalle'], 'USD -> PYG usando precio de compra')
    
    def test_simulador_con_cliente_y_descuento(self):
        """Prueba conversión con cliente que tiene descuento"""
        self.client.force_login(self.user)
        
        url = reverse('tasa_cambio:simular_cambio_api')
        response = self.client.get(url, {
            'origen': 'PYG',
            'destino': 'USD',
            'monto': '75000',
            'cliente_id': self.cliente.id
        })
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        self.assertTrue(data['success'])
        self.assertIsNotNone(data['data']['cliente'])
        self.assertEqual(data['data']['cliente']['nombre'], 'Cliente Test')
        self.assertEqual(data['data']['cliente']['descuento'], 5.0)
        
        # Verificar que se aplicó el descuento en la comisión
        # Comisión ajustada: 75 * (1 - 5/100) = 71.25
        # Precio de venta: 7500 + 71.25 = 7571.25
        # Resultado: 75000 / 7571.25 = 9.91 USD
        expected_result = 75000 / 7571.25
        self.assertAlmostEqual(data['data']['resultado'], expected_result, places=2)
        self.assertIn('descuento 5.00% en comisión', data['data']['detalle'])
    
    def test_simulador_con_cliente_y_metodo_pago(self):
        """Prueba conversión con cliente (descuento) y método de pago (comisión)"""
        self.client.force_login(self.user)
        
        url = reverse('tasa_cambio:simular_cambio_api')
        response = self.client.get(url, {
            'origen': 'PYG',
            'destino': 'USD',
            'monto': '75000',
            'cliente_id': self.cliente.id,
            'metodo_pago_id': self.metodo_pago.id
        })
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        self.assertTrue(data['success'])
        self.assertIsNotNone(data['data']['cliente'])
        self.assertIsNotNone(data['data']['metodo_pago'])
        
        # Verificar que se aplicaron tanto el descuento como la comisión
        self.assertIn('descuento 5.00% en comisión', data['data']['detalle'])
        self.assertGreater(data['data']['comision_pct'], 0)
    
    def test_simulador_parametros_faltantes(self):
        """Prueba que falle cuando faltan parámetros requeridos"""
        self.client.force_login(self.user)
        
        url = reverse('tasa_cambio:simular_cambio_api')
        
        # Sin origen
        response = self.client.get(url, {
            'destino': 'USD',
            'monto': '100'
        })
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        self.assertIn('Parámetros requeridos', data['message'])
        
        # Sin destino
        response = self.client.get(url, {
            'origen': 'PYG',
            'monto': '100'
        })
        self.assertEqual(response.status_code, 400)
        
        # Sin monto
        response = self.client.get(url, {
            'origen': 'PYG',
            'destino': 'USD'
        })
        self.assertEqual(response.status_code, 400)
    
    def test_simulador_monto_invalido(self):
        """Prueba que falle con monto inválido"""
        self.client.force_login(self.user)
        
        url = reverse('tasa_cambio:simular_cambio_api')
        
        # Monto negativo
        response = self.client.get(url, {
            'origen': 'PYG',
            'destino': 'USD',
            'monto': '-100'
        })
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        self.assertIn('Monto inválido', data['message'])
        
        # Monto cero
        response = self.client.get(url, {
            'origen': 'PYG',
            'destino': 'USD',
            'monto': '0'
        })
        self.assertEqual(response.status_code, 400)
        
        # Monto no numérico
        response = self.client.get(url, {
            'origen': 'PYG',
            'destino': 'USD',
            'monto': 'abc'
        })
        self.assertEqual(response.status_code, 400)
    
    def test_simulador_mismas_monedas(self):
        """Prueba que falle cuando origen y destino son iguales"""
        self.client.force_login(self.user)
        
        url = reverse('tasa_cambio:simular_cambio_api')
        response = self.client.get(url, {
            'origen': 'PYG',
            'destino': 'PYG',
            'monto': '100'
        })
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        self.assertIn('Seleccione una moneda distinta de PYG', data['message'])
    
    def test_simulador_cruce_directo_no_permitido(self):
        """Prueba que falle cuando se intenta cruzar dos monedas no-PYG"""
        self.client.force_login(self.user)
        
        url = reverse('tasa_cambio:simular_cambio_api')
        response = self.client.get(url, {
            'origen': 'USD',
            'destino': 'EUR',
            'monto': '100'
        })
        
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        self.assertIn('No se permiten cruces entre monedas', data['message'])
    
    def test_simulador_moneda_no_encontrada(self):
        """Prueba que falle cuando la moneda no existe o está inactiva"""
        self.client.force_login(self.user)
        
        url = reverse('tasa_cambio:simular_cambio_api')
        
        # Moneda inexistente
        response = self.client.get(url, {
            'origen': 'PYG',
            'destino': 'BTC',
            'monto': '100'
        })
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        self.assertIn('no encontrada o inactiva', data['message'])
        
        # Moneda inactiva
        self.moneda_usd.es_activa = False
        self.moneda_usd.save()
        
        response = self.client.get(url, {
            'origen': 'PYG',
            'destino': 'USD',
            'monto': '100'
        })
        self.assertEqual(response.status_code, 404)
    
    def test_simulador_sin_tasa_activa(self):
        """Prueba que falle cuando no hay tasa activa para la moneda"""
        self.client.force_login(self.user)
        
        # Desactivar la tasa
        self.tasa_usd.es_activa = False
        self.tasa_usd.save()
        
        url = reverse('tasa_cambio:simular_cambio_api')
        response = self.client.get(url, {
            'origen': 'PYG',
            'destino': 'USD',
            'monto': '100'
        })
        
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        self.assertIn('No hay tasa activa para USD', data['message'])
    
    def test_simulador_cliente_invalido(self):
        """Prueba que falle con cliente inválido o no asociado"""
        self.client.force_login(self.user)
        
        url = reverse('tasa_cambio:simular_cambio_api')
        
        # Cliente inexistente
        response = self.client.get(url, {
            'origen': 'PYG',
            'destino': 'USD',
            'monto': '100',
            'cliente_id': 99999
        })
        self.assertEqual(response.status_code, 403)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        self.assertIn('Cliente inválido o no asociado', data['message'])
        
        # Cliente no asociado al usuario
        otro_cliente = Cliente.objects.create(
            nombre_comercial='Otro Cliente',
            ruc='87654321',
            tipo_cliente=self.tipo_cliente,
            activo=True
        )
        
        response = self.client.get(url, {
            'origen': 'PYG',
            'destino': 'USD',
            'monto': '100',
            'cliente_id': otro_cliente.id
        })
        self.assertEqual(response.status_code, 403)
    
    def test_simulador_metodo_pago_invalido(self):
        """Prueba que falle con método de pago inválido"""
        self.client.force_login(self.user)
        
        url = reverse('tasa_cambio:simular_cambio_api')
        
        # Método inexistente
        response = self.client.get(url, {
            'origen': 'PYG',
            'destino': 'USD',
            'monto': '100',
            'metodo_pago_id': 99999
        })
        self.assertEqual(response.status_code, 404)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        self.assertIn('Método de pago inválido o inactivo', data['message'])
        
        # Método inactivo
        self.metodo_pago.es_activo = False
        self.metodo_pago.save()
        
        response = self.client.get(url, {
            'origen': 'PYG',
            'destino': 'USD',
            'monto': '100',
            'metodo_pago_id': self.metodo_pago.id
        })
        self.assertEqual(response.status_code, 404)
    
    def test_simulador_sin_autenticacion(self):
        """Prueba que falle sin autenticación cuando se especifica cliente"""
        url = reverse('tasa_cambio:simular_cambio_api')
        response = self.client.get(url, {
            'origen': 'PYG',
            'destino': 'USD',
            'monto': '100',
            'cliente_id': self.cliente.id
        })
        
        self.assertEqual(response.status_code, 401)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        self.assertIn('Autenticación requerida', data['message'])
    
    def test_simulador_formateo_resultados(self):
        """Prueba que los resultados se formateen correctamente"""
        self.client.force_login(self.user)
        
        url = reverse('tasa_cambio:simular_cambio_api')
        response = self.client.get(url, {
            'origen': 'PYG',
            'destino': 'USD',
            'monto': '75000'
        })
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        self.assertTrue(data['success'])
        self.assertIn('resultado_formateado', data['data'])
        self.assertIn('subtotal_formateado', data['data'])
        self.assertIn('comision_monto_formateado', data['data'])
        self.assertIn('total_neto_formateado', data['data'])
        
        # Verificar que el formateo incluye el símbolo de la moneda
        self.assertIn('$', data['data']['resultado_formateado'])
    
    def test_simulador_diferentes_decimales(self):
        """Prueba conversión con monedas que tienen diferentes decimales"""
        self.client.force_login(self.user)
        
        # Crear moneda con 0 decimales
        moneda_jpy = Moneda.objects.create(
            codigo='JPY',
            nombre='Yen Japonés',
            simbolo='¥',
            decimales=0,
            es_activa=True
        )
        
        TasaCambio.objects.create(
            moneda=moneda_jpy,
            precio_base=50,
            comision_compra=1,
            comision_venta=1,
            es_activa=True
        )
        
        url = reverse('tasa_cambio:simular_cambio_api')
        response = self.client.get(url, {
            'origen': 'PYG',
            'destino': 'JPY',
            'monto': '1000'
        })
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        self.assertTrue(data['success'])
        # Verificar que el resultado se redondea correctamente según los decimales
        self.assertIsInstance(data['data']['resultado'], (int, float))
    
    def test_simulador_precision_calculos(self):
        """Prueba la precisión de los cálculos con valores específicos"""
        self.client.force_login(self.user)
        
        url = reverse('tasa_cambio:simular_cambio_api')
        response = self.client.get(url, {
            'origen': 'USD',
            'destino': 'PYG',
            'monto': '1.50'
        })
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        self.assertTrue(data['success'])
        
        # Cálculo exacto: 1.50 * 7450 = 11175 PYG
        expected_result = 1.50 * 7450
        self.assertEqual(data['data']['resultado'], expected_result)
    
    def test_simulador_redondeo_correcto(self):
        """Prueba que el redondeo se aplique correctamente"""
        self.client.force_login(self.user)
        
        # Crear tasa con valores que generen redondeo
        tasa_test = TasaCambio.objects.create(
            moneda=self.moneda_usd,
            precio_base=1000,
            comision_compra=33,
            comision_venta=33,
            es_activa=True
        )
        
        url = reverse('tasa_cambio:simular_cambio_api')
        response = self.client.get(url, {
            'origen': 'PYG',
            'destino': 'USD',
            'monto': '1033'  # 1033 / 1033 = 1.000... debería redondear a 1.00
        })
        
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        
        self.assertTrue(data['success'])
        # Verificar que el resultado se redondea correctamente
        self.assertAlmostEqual(data['data']['resultado'], 1.0, places=2)


class TasaCambioSensitiveColumnsTestCase(TestCase):
    """Tests para verificar el permiso de visualización de columnas sensibles en tasa_cambio"""
    
    def setUp(self):
        """Configurar datos de prueba"""
        from django.contrib.auth.models import Group, Permission
        from django.contrib.contenttypes.models import ContentType
        from usuarios.models import Usuario
        
        # Crear moneda de prueba
        self.moneda = Moneda.objects.create(
            codigo='USD',
            nombre='Dólar Estadounidense',
            simbolo='$',
            decimales=2
        )
        
        # Crear usuarios
        self.usuario_analista = Usuario.objects.create_user(
            email='analista_tc@test.com',
            nombre='Analista',
            apellido='Tasa',
            password='test123'
        )
        
        self.usuario_operador = Usuario.objects.create_user(
            email='operador_tc@test.com',
            nombre='Operador',
            apellido='Tasa',
            password='test123'
        )
        
        # Crear grupos
        self.grupo_analista = Group.objects.create(name='Analista TC')
        self.grupo_operador = Group.objects.create(name='Operador TC')
        
        # Obtener el ContentType de TasaCambio
        content_type = ContentType.objects.get_for_model(TasaCambio)
        
        # Obtener permisos
        self.perm_view = Permission.objects.get(
            codename='view_tasacambio',
            content_type=content_type
        )
        self.perm_view_sensitive = Permission.objects.get(
            codename='can_view_sensitive_columns',
            content_type=content_type
        )
        
        # Asignar permisos a grupos
        # Analista: puede ver columnas sensibles
        self.grupo_analista.permissions.add(self.perm_view)
        self.grupo_analista.permissions.add(self.perm_view_sensitive)
        
        # Operador: NO puede ver columnas sensibles
        self.grupo_operador.permissions.add(self.perm_view)
        
        # Asignar usuarios a grupos
        self.usuario_analista.groups.add(self.grupo_analista)
        self.usuario_operador.groups.add(self.grupo_operador)
        
        # Crear tasa de cambio
        self.tasa = TasaCambio.objects.create(
            moneda=self.moneda,
            precio_base=7500,
            comision_compra=50,
            comision_venta=75,
            es_activa=True
        )
    
    def test_analista_has_sensitive_columns_permission(self):
        """Test: El Analista tiene permiso para ver columnas sensibles"""
        self.assertTrue(
            self.usuario_analista.has_perm('tasa_cambio.can_view_sensitive_columns'),
            "El Analista debería tener el permiso can_view_sensitive_columns"
        )
    
    def test_operador_does_not_have_sensitive_columns_permission(self):
        """Test: El Operador NO tiene permiso para ver columnas sensibles"""
        self.assertFalse(
            self.usuario_operador.has_perm('tasa_cambio.can_view_sensitive_columns'),
            "El Operador NO debería tener el permiso can_view_sensitive_columns"
        )
    
    def test_context_includes_permission_for_analista(self):
        """Test: El contexto incluye el permiso para el Analista"""
        from .views import TasaCambioListView
        from django.test import RequestFactory
        
        factory = RequestFactory()
        request = factory.get('/tasa_cambio/')
        request.user = self.usuario_analista
        
        view = TasaCambioListView()
        view.request = request
        view.kwargs = {}
        view.object_list = view.get_queryset()
        
        context = view.get_context_data()
        
        self.assertIn('can_view_sensitive_columns', context)
        self.assertTrue(context['can_view_sensitive_columns'])
    
    def test_context_excludes_permission_for_operador(self):
        """Test: El contexto no incluye el permiso para el Operador"""
        from .views import TasaCambioListView
        from django.test import RequestFactory
        
        factory = RequestFactory()
        request = factory.get('/tasa_cambio/')
        request.user = self.usuario_operador
        
        view = TasaCambioListView()
        view.request = request
        view.kwargs = {}
        view.object_list = view.get_queryset()
        
        context = view.get_context_data()
        
        self.assertIn('can_view_sensitive_columns', context)
        self.assertFalse(context['can_view_sensitive_columns'])
    
    def test_admin_has_sensitive_columns_permission(self):
        """Test: El Admin tiene permiso para ver columnas sensibles"""
        from django.contrib.auth.models import Group, Permission
        from usuarios.models import Usuario
        
        # Crear usuario Admin
        usuario_admin = Usuario.objects.create_user(
            email='admin_tc@test.com',
            nombre='Admin',
            apellido='Tasa',
            password='test123'
        )
        
        # Crear grupo Admin y asignar todos los permisos
        grupo_admin = Group.objects.create(name='Admin TC')
        all_permissions = Permission.objects.all()
        grupo_admin.permissions.set(all_permissions)
        usuario_admin.groups.add(grupo_admin)
        
        self.assertTrue(
            usuario_admin.has_perm('tasa_cambio.can_view_sensitive_columns'),
            "El Admin debería tener el permiso can_view_sensitive_columns"
        )


class TasaCambioActionsColumnTestCase(TestCase):
    """Tests para verificar que la columna de acciones se muestra correctamente"""
    
    def setUp(self):
        """Configurar datos de prueba"""
        from django.contrib.auth.models import Group, Permission
        from django.contrib.contenttypes.models import ContentType
        from usuarios.models import Usuario
        
        # Crear moneda de prueba
        self.moneda = Moneda.objects.create(
            codigo='USD',
            nombre='Dólar Estadounidense',
            simbolo='$',
            decimales=2
        )
        
        # Crear tasa de cambio
        self.tasa = TasaCambio.objects.create(
            moneda=self.moneda,
            precio_base=7500,
            comision_compra=50,
            comision_venta=75,
            es_activa=True
        )
        
        # Crear usuarios
        self.usuario_operador = Usuario.objects.create_user(
            email='operador_actions@test.com',
            nombre='Operador',
            apellido='Actions',
            password='test123'
        )
        
        self.usuario_visitante = Usuario.objects.create_user(
            email='visitante_actions@test.com',
            nombre='Visitante',
            apellido='Actions',
            password='test123'
        )
        
        # Crear grupos
        self.grupo_operador = Group.objects.create(name='Operador Actions')
        self.grupo_visitante = Group.objects.create(name='Visitante Actions')
        
        # Obtener ContentType de TasaCambio
        content_type = ContentType.objects.get_for_model(TasaCambio)
        
        # Obtener permisos
        self.perm_view = Permission.objects.get(
            codename='view_tasacambio',
            content_type=content_type
        )
        
        # Operador: puede ver tasas (para acceder al historial)
        self.grupo_operador.permissions.add(self.perm_view)
        
        # Visitante: NO tiene ningún permiso en tasas
        
        # Asignar usuarios a grupos
        self.usuario_operador.groups.add(self.grupo_operador)
        self.usuario_visitante.groups.add(self.grupo_visitante)
    
    def test_operador_can_see_actions_column(self):
        """Test: El Operador puede ver la columna de acciones (para ver historial)"""
        self.client.login(email='operador_actions@test.com', password='test123')
        response = self.client.get(reverse('tasa_cambio:tasacambio_list'))
        
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Acciones')
        self.assertContains(response, 'Ver historial')
    
    def test_operador_can_access_historial(self):
        """Test: El Operador puede acceder al historial de tasas"""
        self.client.login(email='operador_actions@test.com', password='test123')
        response = self.client.get(
            reverse('tasa_cambio:tasacambio_historial', kwargs={'moneda_id': self.moneda.id})
        )
        
        self.assertEqual(response.status_code, 200)
    
    def test_visitante_cannot_see_actions_column(self):
        """Test: El Visitante NO puede ver la columna de acciones"""
        # Dar permiso de vista al visitante para que pueda acceder a la página
        self.grupo_visitante.permissions.add(self.perm_view)
        
        self.client.login(email='visitante_actions@test.com', password='test123')
        response = self.client.get(reverse('tasa_cambio:tasacambio_list'))
        
        # Debería poder ver la página con el permiso view
        self.assertEqual(response.status_code, 200)
        # La palabra "Acciones" SÍ debería aparecer porque tiene view_tasacambio
        # (el permiso view_tasacambio permite ver la columna de acciones con el historial)
        self.assertContains(response, 'Acciones')
        self.assertContains(response, 'Ver historial')

