from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from decimal import Decimal

from monedas.models import Moneda
from metodo_pago.models import MetodoPago
from metodo_cobro.models import MetodoCobro
from clientes.models import Cliente, TipoCliente
from tasa_cambio.models import TasaCambio
from usuarios.models import Usuario

User = get_user_model()


class TransaccionModelTest(TestCase):
    """Tests básicos para modelos de transacciones"""
    
    def setUp(self):
        # Crear monedas
        self.usd = Moneda.objects.create(
            codigo='USD', nombre='Dólar Americano', simbolo='$'
        )
        self.pyg = Moneda.objects.create(
            codigo='PYG', nombre='Guaraní', simbolo='₲'
        )
        
        # Crear tasa de cambio
        self.tasa_usd = TasaCambio.objects.create(
            moneda=self.usd,
            precio_base=7400,
            comision_compra=200,
            comision_venta=200,
            es_activa=True
        )

    def test_tasa_cambio_propiedades(self):
        """Test: Las propiedades calculadas de TasaCambio funcionan"""
        # Tasa de compra: precio_base - comision_compra
        self.assertEqual(self.tasa_usd.tasa_compra, 7200)
        
        # Tasa de venta: precio_base + comision_venta  
        self.assertEqual(self.tasa_usd.tasa_venta, 7600)
        
        # Spread: diferencia entre venta y compra
        self.assertEqual(self.tasa_usd.spread, 400)

    def test_monedas_creacion(self):
        """Test: Las monedas se crean correctamente"""
        self.assertEqual(self.usd.codigo, 'USD')
        self.assertEqual(self.pyg.codigo, 'PYG')
        self.assertEqual(self.usd.simbolo, '$')
        self.assertEqual(self.pyg.simbolo, '₲')


class TransaccionViewsTest(TestCase):
    """Tests esenciales para vistas de transacciones"""
    
    def setUp(self):
        # Crear usuario de prueba
        self.user = Usuario.objects.create_user(
            email='test@test.com',
            nombre='Test',
            apellido='User',
            password='testpass123'
        )
        
        # Crear datos básicos
        self.usd = Moneda.objects.create(codigo='USD', nombre='Dólar', simbolo='$')
        self.pyg = Moneda.objects.create(codigo='PYG', nombre='Guaraní', simbolo='₲')
        
        self.tasa_usd = TasaCambio.objects.create(
            moneda=self.usd, precio_base=7400, comision_compra=200, 
            comision_venta=200, es_activa=True
        )
        
        self.metodo_pago = MetodoPago.objects.create(nombre='Efectivo', comision=0)
        self.metodo_cobro = MetodoCobro.objects.create(nombre='Efectivo USD', comision=0)
        self.metodo_cobro.monedas_permitidas.add(self.usd)
        

        
        self.client = Client()
        self.client.force_login(self.user)

    def test_vista_comprar_divisas_get(self):
        """Test: Acceso a la vista de comprar divisas"""
        response = self.client.get(reverse('transacciones:comprar_divisas'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Comprar Divisas')

    def test_vista_vender_divisas_get(self):
        """Test: Acceso a la vista de vender divisas"""
        response = self.client.get(reverse('transacciones:vender_divisas'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Vender Divisas')

    def test_api_calcular_compra(self):
        """Test: API de cálculo de compra"""
        response = self.client.get(reverse('transacciones:api_calcular_compra_completa'), {
            'monto': '100',
            'origen': 'PYG',
            'destino': 'USD',
            'metodo_cobro_id': self.metodo_pago.id,
            'metodo_pago_id': self.metodo_pago.id
        })
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['tasa_ajustada'], 7600)

    def test_api_calcular_venta(self):
        """Test: API de cálculo de venta"""
        response = self.client.get(reverse('transacciones:api_calcular_venta_completa'), {
            'monto': '100',
            'origen': 'USD',
            'destino': 'PYG',
            'metodo_cobro_id': self.metodo_cobro.id,
            'metodo_pago_id': self.metodo_pago.id
        })
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['tasa_ajustada'], 7200)

    def test_api_metodos_cobro_por_moneda(self):
        """Test: API que filtra métodos de cobro por moneda"""
        response = self.client.get(reverse('transacciones:api_metodos_cobro_por_moneda'), {
            'moneda_codigo': 'USD'
        })
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(len(data['metodos_cobro']), 1)
        self.assertEqual(data['metodos_cobro'][0]['nombre'], 'Efectivo USD')
