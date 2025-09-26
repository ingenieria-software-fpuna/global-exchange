from django.test import TestCase, RequestFactory
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from decimal import Decimal
from .models import TipoCliente


class TipoClienteModelTestCase(TestCase):
    """Tests unitarios para el modelo TipoCliente"""
    
    def setUp(self):
        self.tipo_cliente_data = {
            'nombre': 'Cliente Premium',
            'descripcion': 'Cliente con beneficios especiales',
            'descuento': Decimal('10.50'),
            'activo': True
        }

    def test_create_tipo_cliente(self):
        """Test creación de tipo de cliente"""
        tipo_cliente = TipoCliente.objects.create(**self.tipo_cliente_data)
        
        self.assertEqual(tipo_cliente.nombre, 'Cliente Premium')
        self.assertEqual(tipo_cliente.descripcion, 'Cliente con beneficios especiales')
        self.assertEqual(tipo_cliente.descuento, Decimal('10.50'))
        self.assertTrue(tipo_cliente.activo)
        self.assertIsNotNone(tipo_cliente.fecha_creacion)
        self.assertIsNotNone(tipo_cliente.fecha_modificacion)

    def test_tipo_cliente_str_representation(self):
        """Test la representación string del tipo de cliente"""
        tipo_cliente = TipoCliente.objects.create(**self.tipo_cliente_data)
        self.assertEqual(str(tipo_cliente), 'Cliente Premium')

    def test_tipo_cliente_unique_nombre(self):
        """Test que el nombre debe ser único"""
        TipoCliente.objects.create(**self.tipo_cliente_data)
        
        with self.assertRaises(IntegrityError):
            TipoCliente.objects.create(
                nombre='Cliente Premium',
                descripcion='Otra descripción',
                descuento=Decimal('5.00'),
                activo=True
            )

    def test_tipo_cliente_default_values(self):
        """Test valores por defecto del modelo"""
        tipo_cliente = TipoCliente.objects.create(
            nombre='Cliente Básico'
        )
        
        self.assertEqual(tipo_cliente.descuento, Decimal('0.00'))
        self.assertTrue(tipo_cliente.activo)
        self.assertIsNone(tipo_cliente.descripcion)

    def test_tipo_cliente_meta_options(self):
        """Test opciones de Meta del modelo"""
        meta = TipoCliente._meta
        
        self.assertEqual(meta.verbose_name, 'Tipo de Cliente')
        self.assertEqual(meta.verbose_name_plural, 'Tipos de Cliente')
        self.assertEqual(meta.ordering, ['nombre'])

    def test_tipo_cliente_descuento_validation(self):
        """Test validación del campo descuento"""
        tipo_cliente = TipoCliente(
            nombre='Cliente Test',
            descuento=Decimal('99.99')
        )
        tipo_cliente.full_clean()
        
        tipo_cliente = TipoCliente(
            nombre='Cliente Test2',
            descuento=Decimal('10.123')
        )
        tipo_cliente.save()
        tipo_cliente.refresh_from_db()
        self.assertEqual(tipo_cliente.descuento, Decimal('10.12'))

    def test_tipo_cliente_timestamps(self):
        """Test que los timestamps se actualizan correctamente"""
        tipo_cliente = TipoCliente.objects.create(**self.tipo_cliente_data)
        
        fecha_creacion_original = tipo_cliente.fecha_creacion
        fecha_modificacion_original = tipo_cliente.fecha_modificacion
        
        tipo_cliente.nombre = 'Cliente Premium Actualizado'
        tipo_cliente.save()
        tipo_cliente.refresh_from_db()
        
        self.assertEqual(tipo_cliente.fecha_creacion, fecha_creacion_original)
        self.assertGreater(tipo_cliente.fecha_modificacion, fecha_modificacion_original)

    def test_tipo_cliente_field_max_lengths(self):
        """Test longitudes máximas de los campos"""
        nombre_largo = 'A' * 100
        tipo_cliente = TipoCliente(
            nombre=nombre_largo,
            descuento=Decimal('0.00')
        )
        tipo_cliente.full_clean()
        
        nombre_muy_largo = 'A' * 101
        tipo_cliente = TipoCliente(
            nombre=nombre_muy_largo,
            descuento=Decimal('0.00')
        )
        with self.assertRaises(ValidationError):
            tipo_cliente.full_clean()

    def test_tipo_cliente_ordering(self):
        """Test que el ordenamiento por defecto funciona"""
        TipoCliente.objects.create(nombre='Zebra', descuento=Decimal('0.00'))
        TipoCliente.objects.create(nombre='Alpha', descuento=Decimal('0.00'))
        TipoCliente.objects.create(nombre='Beta', descuento=Decimal('0.00'))
        
        tipos_cliente = list(TipoCliente.objects.all())
        nombres = [tc.nombre for tc in tipos_cliente]
        
        self.assertEqual(nombres, ['Alpha', 'Beta', 'Zebra'])


class TipoClienteViewsTestCase(TestCase):
    """Tests unitarios para las vistas de TipoCliente"""
    
    def setUp(self):
        self.factory = RequestFactory()
        self.tipo_cliente = TipoCliente.objects.create(
            nombre='Cliente Test',
            descripcion='Descripción test',
            descuento=Decimal('5.00'),
            activo=True
        )

    def test_tipo_cliente_list_view_attributes(self):
        """Test unitario de atributos de la vista de lista"""
        from .views import TipoClienteListView
        
        self.assertEqual(TipoClienteListView.model, TipoCliente)
        self.assertEqual(TipoClienteListView.template_name, 'clientes/tipocliente_list.html')
        self.assertEqual(TipoClienteListView.context_object_name, 'tipos')
        self.assertEqual(TipoClienteListView.paginate_by, 10)

    def test_tipo_cliente_create_view_attributes(self):
        """Test unitario de atributos de la vista de creación"""
        from .views import TipoClienteCreateView
        from .forms import TipoClienteForm
        
        self.assertEqual(TipoClienteCreateView.model, TipoCliente)
        self.assertEqual(TipoClienteCreateView.template_name, 'clientes/tipocliente_form.html')
        self.assertEqual(TipoClienteCreateView.form_class, TipoClienteForm)
        self.assertEqual(str(TipoClienteCreateView.success_url), '/clientes/tipos/')

    def test_tipo_cliente_update_view_attributes(self):
        """Test unitario de atributos de la vista de actualización"""
        from .views import TipoClienteUpdateView
        from .forms import TipoClienteUpdateForm
        
        self.assertEqual(TipoClienteUpdateView.model, TipoCliente)
        self.assertEqual(TipoClienteUpdateView.template_name, 'clientes/tipocliente_form.html')
        self.assertEqual(TipoClienteUpdateView.form_class, TipoClienteUpdateForm)
        self.assertEqual(str(TipoClienteUpdateView.success_url), '/clientes/tipos/')

    def test_tipo_cliente_delete_view_attributes(self):
        """Test unitario de atributos de la vista de eliminación"""
        from .views import TipoClienteDeleteView
        
        self.assertEqual(TipoClienteDeleteView.model, TipoCliente)
        self.assertEqual(TipoClienteDeleteView.template_name, 'clientes/tipocliente_confirm_delete.html')
        self.assertEqual(str(TipoClienteDeleteView.success_url), '/clientes/tipos/')

    def test_view_methods_exist(self):
        """Test unitario que verifica que los métodos personalizados existen"""
        from .views import TipoClienteCreateView, TipoClienteUpdateView, TipoClienteDeleteView
        
        self.assertTrue(hasattr(TipoClienteCreateView, 'form_valid'))
        self.assertTrue(callable(TipoClienteCreateView.form_valid))
        
        self.assertTrue(hasattr(TipoClienteUpdateView, 'form_valid'))
        self.assertTrue(callable(TipoClienteUpdateView.form_valid))
        
        self.assertTrue(hasattr(TipoClienteDeleteView, 'delete'))
        self.assertTrue(callable(TipoClienteDeleteView.delete))

    def test_view_dispatch_methods_exist(self):
        """Test unitario que verifica que los métodos dispatch existen"""
        from .views import (TipoClienteListView, TipoClienteCreateView, 
                           TipoClienteUpdateView, TipoClienteDeleteView)
        
        views = [TipoClienteListView, TipoClienteCreateView, 
                TipoClienteUpdateView, TipoClienteDeleteView]
        
        for view_class in views:
            self.assertTrue(hasattr(view_class, 'dispatch'))
            self.assertTrue(callable(getattr(view_class, 'dispatch')))

    def test_view_inheritance(self):
        """Test unitario que verifica la herencia correcta de las vistas"""
        from django.views.generic import ListView, CreateView, UpdateView, DeleteView
        from django.contrib.auth.mixins import LoginRequiredMixin
        from .views import (TipoClienteListView, TipoClienteCreateView, 
                           TipoClienteUpdateView, TipoClienteDeleteView)
        
        self.assertTrue(issubclass(TipoClienteListView, LoginRequiredMixin))
        self.assertTrue(issubclass(TipoClienteListView, ListView))
        
        self.assertTrue(issubclass(TipoClienteCreateView, LoginRequiredMixin))
        self.assertTrue(issubclass(TipoClienteCreateView, CreateView))
        
        self.assertTrue(issubclass(TipoClienteUpdateView, LoginRequiredMixin))
        self.assertTrue(issubclass(TipoClienteUpdateView, UpdateView))
        
        self.assertTrue(issubclass(TipoClienteDeleteView, LoginRequiredMixin))
        self.assertTrue(issubclass(TipoClienteDeleteView, DeleteView))
