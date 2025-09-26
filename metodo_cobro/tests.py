from django.test import TestCase
from django.contrib.auth import get_user_model
from decimal import Decimal

from .models import MetodoCobro
from monedas.models import Moneda

User = get_user_model()


class MetodoCobroTestCase(TestCase):
    def setUp(self):
        """Configuración inicial para las pruebas"""
        # Crear monedas de prueba
        self.pyg = Moneda.objects.create(codigo="PYG", nombre="Guaraní", simbolo="₲")
        self.usd = Moneda.objects.create(codigo="USD", nombre="Dólar Americano", simbolo="$")
        self.eur = Moneda.objects.create(codigo="EUR", nombre="Euro", simbolo="€")

    def test_metodo_cobro_creation(self):
        """Prueba la creación de un método de cobro"""
        metodo = MetodoCobro.objects.create(
            nombre="Transferencia bancaria",
            descripcion="Transferencia bancaria local",
            comision=1.50
        )
        metodo.monedas_permitidas.add(self.pyg)
        
        self.assertEqual(metodo.nombre, "Transferencia bancaria")
        self.assertEqual(metodo.comision, Decimal('1.50'))
        self.assertTrue(metodo.es_activo)
        self.assertEqual(metodo.monedas_permitidas.count(), 1)

    def test_str_representation(self):
        """Prueba la representación en string del modelo"""
        metodo = MetodoCobro.objects.create(
            nombre="Efectivo",
            descripcion="Pago en efectivo",
            comision=0.0
        )
        self.assertEqual(str(metodo), "Efectivo")

    def test_monedas_permitidas_relationship(self):
        """Prueba la relación many-to-many con monedas"""
        metodo = MetodoCobro.objects.create(
            nombre="Cheque",
            descripcion="Pago con cheque",
            comision=2.0
        )
        metodo.monedas_permitidas.add(self.pyg, self.usd, self.eur)
        
        self.assertEqual(metodo.monedas_permitidas.count(), 3)
        self.assertIn(self.pyg, metodo.monedas_permitidas.all())
        self.assertIn(self.usd, metodo.monedas_permitidas.all())
        self.assertIn(self.eur, metodo.monedas_permitidas.all())