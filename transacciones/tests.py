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
from transacciones.views import calcular_transaccion_completa, calcular_venta_completa

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
            'metodo_cobro_id': self.metodo_cobro.id,
            'metodo_pago_id': self.metodo_pago.id
        })
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        if not data['success']:
            print(f"API Error: {data}")
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

    def test_descuento_tipo_cliente_inactivo(self):
        """Test: Los tipos de cliente inactivos no aplican descuentos"""
        # Crear tipo de cliente activo con descuento
        tipo_inactivo = TipoCliente.objects.create(
            nombre='Tipo Inactivo',
            descuento=Decimal('15.00'),
            activo=True
        )
        
        # Crear cliente con tipo activo
        cliente_inactivo = Cliente.objects.create(
            nombre_comercial='Cliente Inactivo',
            ruc='12345678',
            tipo_cliente=tipo_inactivo
        )
        
        # Desactivar el tipo de cliente después de crear el cliente
        tipo_inactivo.activo = False
        tipo_inactivo.save()
        
        # Crear tipo de cliente activo con descuento
        tipo_activo = TipoCliente.objects.create(
            nombre='Tipo Activo',
            descuento=Decimal('10.00'),
            activo=True
        )
        
        # Crear cliente con tipo activo
        cliente_activo = Cliente.objects.create(
            nombre_comercial='Cliente Activo',
            ruc='87654321',
            tipo_cliente=tipo_activo
        )
        
        # Test compra con cliente inactivo - no debe aplicar descuento
        resultado_inactivo = calcular_transaccion_completa(
            monto=Decimal('100000'),
            moneda_origen=self.pyg,
            moneda_destino=self.usd,
            cliente=cliente_inactivo
        )
        
        self.assertTrue(resultado_inactivo['success'])
        self.assertEqual(resultado_inactivo['data']['descuento_pct'], 0)
        self.assertEqual(resultado_inactivo['data']['descuento_aplicado'], 0)
        
        # Test compra con cliente activo - debe aplicar descuento
        resultado_activo = calcular_transaccion_completa(
            monto=Decimal('100000'),
            moneda_origen=self.pyg,
            moneda_destino=self.usd,
            cliente=cliente_activo
        )
        
        self.assertTrue(resultado_activo['success'])
        self.assertEqual(resultado_activo['data']['descuento_pct'], 10.0)
        # El descuento se aplica a la tasa, no a las comisiones
        self.assertEqual(resultado_activo['data']['descuento_aplicado'], 0)
        
        # Test venta con cliente inactivo - no debe aplicar descuento
        resultado_venta_inactivo = calcular_venta_completa(
            monto=Decimal('100'),
            moneda_origen=self.usd,
            moneda_destino=self.pyg,
            cliente=cliente_inactivo
        )
        
        self.assertTrue(resultado_venta_inactivo['success'])
        self.assertEqual(resultado_venta_inactivo['data']['descuento_pct'], 0)
        self.assertEqual(resultado_venta_inactivo['data']['descuento_aplicado'], 0)
        
        # Test venta con cliente activo - debe aplicar descuento
        resultado_venta_activo = calcular_venta_completa(
            monto=Decimal('100'),
            moneda_origen=self.usd,
            moneda_destino=self.pyg,
            cliente=cliente_activo
        )
        
        self.assertTrue(resultado_venta_activo['success'])
        self.assertEqual(resultado_venta_activo['data']['descuento_pct'], 10.0)
        # El descuento se aplica a la tasa, no a las comisiones
        self.assertEqual(resultado_venta_activo['data']['descuento_aplicado'], 0)

    def test_venta_descuento_aplicado_a_comision_compra(self):
        """Test: En ventas, el descuento se aplica a la comisión de compra, no al precio final"""
        # Crear tipo de cliente con descuento
        tipo_cliente = TipoCliente.objects.create(
            nombre='Tipo con Descuento',
            descuento=Decimal('20.00'),
            activo=True
        )
        
        # Crear cliente
        cliente = Cliente.objects.create(
            nombre_comercial='Cliente Test',
            ruc='12345678',
            tipo_cliente=tipo_cliente
        )
        
        # Calcular venta sin descuento (simulando cliente sin tipo)
        resultado_sin_descuento = calcular_venta_completa(
            monto=Decimal('100'),
            moneda_origen=self.usd,
            moneda_destino=self.pyg,
            cliente=None
        )
        
        # Verificar que el cálculo sin descuento fue exitoso
        if not resultado_sin_descuento['success']:
            print(f"Error en cálculo sin descuento: {resultado_sin_descuento.get('error', 'Error desconocido')}")
            self.fail("El cálculo sin descuento falló")
        
        # Calcular venta con descuento
        resultado_con_descuento = calcular_venta_completa(
            monto=Decimal('100'),
            moneda_origen=self.usd,
            moneda_destino=self.pyg,
            cliente=cliente
        )
        
        self.assertTrue(resultado_sin_descuento['success'])
        self.assertTrue(resultado_con_descuento['success'])
        
        # El cliente con descuento debe recibir más PYG
        self.assertGreater(
            resultado_con_descuento['data']['resultado'],
            resultado_sin_descuento['data']['resultado']
        )
        
        # Verificar que el descuento se aplicó correctamente
        self.assertEqual(resultado_con_descuento['data']['descuento_pct'], 20.0)
        
        # La tasa usada con descuento debe ser mayor (mejor para el cliente)
        self.assertGreater(
            resultado_con_descuento['data']['precio_usado'],
            resultado_sin_descuento['data']['precio_usado']
        )
