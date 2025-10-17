from django.test import TestCase
from decimal import Decimal

from .services import PasarelaService
from .models import PagoPasarela
from transacciones.models import Transaccion, TipoOperacion, EstadoTransaccion
from monedas.models import Moneda
from metodo_cobro.models import MetodoCobro
from usuarios.models import Usuario


class PasarelaServiceTestCase(TestCase):
    """Tests para el servicio de integración con la pasarela de pagos"""
    
    def setUp(self):
        """Configuración inicial para los tests"""
        self.service = PasarelaService()
        
    def test_mapeo_metodos_cobro(self):
        """Prueba el mapeo de métodos de cobro"""
        # Casos de prueba para el mapeo
        casos_mapeo = [
            ("Billetera electrónica", "billetera"),
            ("Tarjeta de débito", "tarjeta"),
            ("Transferencia bancaria", "transferencia"),
            ("Método desconocido", "tarjeta"),  # El servicio devuelve 'tarjeta' por defecto
        ]
        
        for metodo_original, metodo_esperado in casos_mapeo:
            with self.subTest(metodo=metodo_original):
                resultado = self.service._mapear_metodo(metodo_original)
                self.assertEqual(resultado, metodo_esperado)
    
    def test_servicio_inicializacion(self):
        """Prueba que el servicio se inicializa correctamente"""
        self.assertEqual(self.service.BASE_URL, "http://localhost:3001")
        self.assertEqual(self.service.timeout, 30)
        self.assertIn('webhook-pago', self.service.webhook_url)
    
    def test_metodo_mapping_case_insensitive(self):
        """Prueba que el mapeo funciona sin importar mayúsculas/minúsculas"""
        casos = [
            ("BILLETERA ELECTRÓNICA", "billetera"),
            ("billetera electrónica", "billetera"),
            ("Billetera Electrónica", "billetera"),
        ]
        
        for metodo, esperado in casos:
            resultado = self.service._mapear_metodo(metodo)
            self.assertEqual(resultado, esperado)


class PagoPasarelaModelTestCase(TestCase):
    """Tests básicos para el modelo PagoPasarela"""
    
    def test_modelo_definicion(self):
        """Prueba que el modelo tiene los campos esperados"""
        # Verificar que el modelo existe y tiene los campos básicos
        self.assertTrue(hasattr(PagoPasarela, 'id_pago_externo'))
        self.assertTrue(hasattr(PagoPasarela, 'monto'))
        self.assertTrue(hasattr(PagoPasarela, 'metodo_pasarela'))
        self.assertTrue(hasattr(PagoPasarela, 'moneda'))
        self.assertTrue(hasattr(PagoPasarela, 'estado'))
        self.assertTrue(hasattr(PagoPasarela, 'fecha_creacion'))
    
    def test_modelo_meta(self):
        """Prueba las opciones meta del modelo"""
        meta = PagoPasarela._meta
        self.assertEqual(meta.verbose_name, 'Pago de Pasarela')
        self.assertEqual(meta.verbose_name_plural, 'Pagos de Pasarela')
