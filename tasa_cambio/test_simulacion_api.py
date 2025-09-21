from django.test import TestCase, Client
from django.urls import reverse
from django.utils import timezone
from decimal import Decimal
from django.contrib.auth import get_user_model

from monedas.models import Moneda
from tasa_cambio.models import TasaCambio
from metodo_pago.models import MetodoPago

User = get_user_model()


class SimularCambioAPITest(TestCase):
    """Pruebas del endpoint de simulación con comisión por método de pago"""

    def setUp(self):
        # Usuario (login no requerido por el endpoint, pero es consistente con otras pruebas)
        self.user = User.objects.create_user(
            email='apiuser@example.com',
            password='pass1234',
            nombre='API',
            apellido='User',
            cedula='12345678'
        )
        self.client = Client()
        self.client.login(username='apiuser@example.com', password='pass1234')

        # Moneda USD y tasa activa
        self.usd = Moneda.objects.create(
            nombre="Dólar Estadounidense",
            codigo="USD",
            simbolo="$",
            decimales=2,
            es_activa=True,
        )
        self.tasa = TasaCambio.objects.create(
            moneda=self.usd,
            precio_base=9500,  # Precio base en guaraníes
            comision_compra=500,  # Comisión de compra: 9500 - 500 = 9000
            comision_venta=500,   # Comisión de venta: 9500 + 500 = 10000
            es_activa=True,
        )

        # Método de pago (2%)
        self.mp = MetodoPago.objects.create(
            nombre='Tarjeta de Crédito',
            descripcion='Test',
            comision=Decimal('2.00'),
            es_activo=True,
        )

    def test_pyg_a_usd_con_comision(self):
        """PYG -> USD: subtotal 100, comisión 2, total 98"""
        url = reverse('tasa_cambio:simular_cambio_api')
        resp = self.client.get(url, {
            'origen': 'PYG',
            'destino': 'USD',
            'monto': '1000000',  # 1.000.000 PYG
            'metodo_pago_id': str(self.mp.id),
        })
        self.assertEqual(resp.status_code, 200)
        payload = resp.json()
        self.assertTrue(payload.get('success'))
        d = payload['data']
        self.assertAlmostEqual(d['subtotal'], 100.0, places=6)
        self.assertAlmostEqual(d['comision_monto'], 2.0, places=6)
        self.assertAlmostEqual(d['total_neto'], 98.0, places=6)
        # resultado debe ser igual al total cuando hay comisión
        self.assertAlmostEqual(d['resultado'], 98.0, places=6)

    def test_usd_a_pyg_con_comision(self):
        """USD -> PYG: subtotal 900000, comisión 18000, total 882000"""
        url = reverse('tasa_cambio:simular_cambio_api')
        resp = self.client.get(url, {
            'origen': 'USD',
            'destino': 'PYG',
            'monto': '100',
            'metodo_pago_id': str(self.mp.id),
        })
        self.assertEqual(resp.status_code, 200)
        payload = resp.json()
        self.assertTrue(payload.get('success'))
        d = payload['data']
        self.assertAlmostEqual(d['subtotal'], 900000.0, places=6)
        self.assertAlmostEqual(d['comision_monto'], 18000.0, places=6)
        self.assertAlmostEqual(d['total_neto'], 882000.0, places=6)
        self.assertAlmostEqual(d['resultado'], 882000.0, places=6)

