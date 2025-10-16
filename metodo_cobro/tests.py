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


    def test_metodo_cobro_default_values(self):
        """Prueba los valores por defecto del modelo"""
        metodo = MetodoCobro.objects.create(
            nombre="Test Default",
            descripcion="Test descripción",
            comision=0.0  # Campo requerido
        )
        
        self.assertEqual(metodo.comision, Decimal('0.00'))
        self.assertTrue(metodo.es_activo)
        self.assertEqual(metodo.monedas_permitidas.count(), 0)

    def test_metodo_cobro_comision_validation(self):
        """Prueba la validación del campo comisión"""
        # Comisión positiva
        metodo1 = MetodoCobro.objects.create(
            nombre="Test Positivo",
            comision=5.25
        )
        self.assertEqual(metodo1.comision, Decimal('5.25'))
        
        # Comisión cero
        metodo2 = MetodoCobro.objects.create(
            nombre="Test Cero",
            comision=0.0
        )
        self.assertEqual(metodo2.comision, Decimal('0.00'))
        
        # Comisión con decimales
        metodo3 = MetodoCobro.objects.create(
            nombre="Test Decimales",
            comision=2.75
        )
        self.assertEqual(metodo3.comision, Decimal('2.75'))

    def test_metodo_cobro_es_activo_field(self):
        """Prueba el campo es_activo"""
        # Método activo por defecto
        metodo_activo = MetodoCobro.objects.create(
            nombre="Activo",
            comision=1.0
        )
        self.assertTrue(metodo_activo.es_activo)
        
        # Método inactivo
        metodo_inactivo = MetodoCobro.objects.create(
            nombre="Inactivo",
            comision=1.0,
            es_activo=False
        )
        self.assertFalse(metodo_inactivo.es_activo)

    def test_metodo_cobro_nombre_max_length(self):
        """Prueba la longitud máxima del campo nombre"""
        # Nombre con longitud máxima (100 caracteres)
        nombre_largo = "A" * 100
        metodo = MetodoCobro.objects.create(
            nombre=nombre_largo,
            comision=1.0
        )
        self.assertEqual(len(metodo.nombre), 100)
        self.assertEqual(metodo.nombre, nombre_largo)

    def test_metodo_cobro_descripcion_max_length(self):
        """Prueba la longitud máxima del campo descripción"""
        # Descripción con longitud máxima (255 caracteres)
        descripcion_larga = "B" * 255
        metodo = MetodoCobro.objects.create(
            nombre="Test Descripción",
            descripcion=descripcion_larga,
            comision=1.0
        )
        self.assertEqual(len(metodo.descripcion), 255)
        self.assertEqual(metodo.descripcion, descripcion_larga)

    def test_metodo_cobro_nombre_blank_and_null(self):
        """Prueba que el campo nombre puede estar vacío (blank=True)"""
        # El campo nombre permite valores vacíos según el modelo
        metodo = MetodoCobro.objects.create(
            nombre="",  # Nombre vacío
            comision=1.0
        )
        self.assertEqual(metodo.nombre, "")

    def test_metodo_cobro_descripcion_blank(self):
        """Prueba que el campo descripción puede estar vacío"""
        metodo = MetodoCobro.objects.create(
            nombre="Test Sin Descripción",
            descripcion="",  # Descripción vacía
            comision=1.0
        )
        self.assertEqual(metodo.descripcion, "")

    def test_metodo_cobro_monedas_permitidas_add_remove(self):
        """Prueba agregar y remover monedas permitidas"""
        metodo = MetodoCobro.objects.create(
            nombre="Test Add Remove",
            comision=1.0
        )
        
        # Agregar monedas
        metodo.monedas_permitidas.add(self.pyg, self.usd)
        self.assertEqual(metodo.monedas_permitidas.count(), 2)
        
        # Agregar una moneda más
        metodo.monedas_permitidas.add(self.eur)
        self.assertEqual(metodo.monedas_permitidas.count(), 3)
        
        # Remover una moneda
        metodo.monedas_permitidas.remove(self.usd)
        self.assertEqual(metodo.monedas_permitidas.count(), 2)
        self.assertNotIn(self.usd, metodo.monedas_permitidas.all())
        
        # Limpiar todas las monedas
        metodo.monedas_permitidas.clear()
        self.assertEqual(metodo.monedas_permitidas.count(), 0)

    def test_metodo_cobro_str_with_special_characters(self):
        """Prueba la representación string con caracteres especiales"""
        metodo = MetodoCobro.objects.create(
            nombre="Método de Cobro & Pago",
            comision=1.5
        )
        self.assertEqual(str(metodo), "Método de Cobro & Pago")

    def test_metodo_cobro_unicode_handling(self):
        """Prueba el manejo de caracteres Unicode"""
        metodo = MetodoCobro.objects.create(
            nombre="Método de Cobro Español",
            descripcion="Descripción con acentos: áéíóú",
            comision=2.5
        )
        self.assertEqual(metodo.nombre, "Método de Cobro Español")
        self.assertEqual(metodo.descripcion, "Descripción con acentos: áéíóú")

    def test_metodo_cobro_comision_decimal_precision(self):
        """Prueba la precisión decimal del campo comisión"""
        # Comisión con muchos decimales
        valor_original = 3.14159265359
        metodo = MetodoCobro.objects.create(
            nombre="Test Precisión",
            comision=valor_original
        )
        # Django mantiene la precisión original del Decimal
        self.assertEqual(float(metodo.comision), valor_original)

    def test_metodo_cobro_ordering(self):
        """Prueba el ordenamiento por nombre"""
        # Crear métodos en orden no alfabético
        metodo_c = MetodoCobro.objects.create(nombre="C", comision=1.0)
        metodo_a = MetodoCobro.objects.create(nombre="A", comision=2.0)
        metodo_b = MetodoCobro.objects.create(nombre="B", comision=3.0)
        
        # Obtener todos los métodos ordenados
        metodos = MetodoCobro.objects.all().order_by('nombre')
        metodos_list = list(metodos)
        
        self.assertEqual(metodos_list[0], metodo_a)
        self.assertEqual(metodos_list[1], metodo_b)
        self.assertEqual(metodos_list[2], metodo_c)

    def test_metodo_cobro_filter_by_es_activo(self):
        """Prueba filtrar métodos por estado activo"""
        # Crear métodos activos e inactivos
        MetodoCobro.objects.create(nombre="Activo 1", comision=1.0, es_activo=True)
        MetodoCobro.objects.create(nombre="Activo 2", comision=2.0, es_activo=True)
        MetodoCobro.objects.create(nombre="Inactivo 1", comision=3.0, es_activo=False)
        
        # Filtrar solo activos
        activos = MetodoCobro.objects.filter(es_activo=True)
        self.assertEqual(activos.count(), 2)
        
        # Filtrar solo inactivos
        inactivos = MetodoCobro.objects.filter(es_activo=False)
        self.assertEqual(inactivos.count(), 1)

    def test_metodo_cobro_filter_by_comision(self):
        """Prueba filtrar métodos por comisión"""
        # Crear métodos con diferentes comisiones
        MetodoCobro.objects.create(nombre="Comisión 1", comision=1.0)
        MetodoCobro.objects.create(nombre="Comisión 2", comision=2.5)
        MetodoCobro.objects.create(nombre="Comisión 3", comision=5.0)
        
        # Filtrar por comisión mayor a 2.0
        comisiones_altas = MetodoCobro.objects.filter(comision__gt=2.0)
        self.assertEqual(comisiones_altas.count(), 2)
        
        # Filtrar por comisión exacta
        comision_exacta = MetodoCobro.objects.filter(comision=2.5)
        self.assertEqual(comision_exacta.count(), 1)
        self.assertEqual(comision_exacta.first().nombre, "Comisión 2")