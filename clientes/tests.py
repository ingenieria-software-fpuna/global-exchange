from django.test import TestCase, RequestFactory
from django.urls import reverse
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from decimal import Decimal
from .models import TipoCliente, Cliente
from .forms import ClienteForm, ClienteUpdateForm


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


class ClienteFormTestCase(TestCase):
    """Tests para los formularios de cliente"""
    
    def setUp(self):
        # Crear tipos de cliente activos e inactivos
        self.tipo_activo = TipoCliente.objects.create(
            nombre='Tipo Activo',
            descuento=Decimal('10.00'),
            activo=True
        )
        self.tipo_inactivo = TipoCliente.objects.create(
            nombre='Tipo Inactivo',
            descuento=Decimal('15.00'),
            activo=False
        )
    
    def test_cliente_form_shows_all_tipos(self):
        """Test: El formulario de cliente muestra todos los tipos, activos e inactivos"""
        form = ClienteForm()
        
        # Verificar que el queryset incluye ambos tipos
        tipo_choices = [choice[0] for choice in form.fields['tipo_cliente'].queryset.values_list('id')]
        
        self.assertIn(self.tipo_activo.id, tipo_choices)
        self.assertIn(self.tipo_inactivo.id, tipo_choices)
        self.assertEqual(len(tipo_choices), 2)
    
    def test_cliente_update_form_shows_all_tipos(self):
        """Test: El formulario de actualización de cliente muestra todos los tipos"""
        form = ClienteUpdateForm()
        
        # Verificar que el queryset incluye ambos tipos
        tipo_choices = [choice[0] for choice in form.fields['tipo_cliente'].queryset.values_list('id')]
        
        self.assertIn(self.tipo_activo.id, tipo_choices)
        self.assertIn(self.tipo_inactivo.id, tipo_choices)
        self.assertEqual(len(tipo_choices), 2)
    
    def test_can_create_cliente_with_inactive_tipo(self):
        """Test: Se puede crear un cliente con tipo inactivo"""
        form_data = {
            'nombre_comercial': 'Cliente Test',
            'ruc': '12345678',
            'correo_electronico': 'test@example.com',
            'tipo_cliente': self.tipo_inactivo.id,
        }
        
        form = ClienteForm(data=form_data)
        
        # Verificar que el formulario es válido
        if not form.is_valid():
            print(f"Form errors: {form.errors}")
            self.fail(f"Form is not valid: {form.errors}")
        
        self.assertTrue(form.is_valid())
        
        # Crear el cliente
        cliente = form.save()
        self.assertEqual(cliente.tipo_cliente, self.tipo_inactivo)
        self.assertFalse(cliente.tipo_cliente.activo)


class ClientePermissionsTestCase(TestCase):
    """Tests para verificar los permisos de visualización de clientes"""
    
    def setUp(self):
        """Configurar datos de prueba"""
        from django.contrib.auth.models import Group, Permission
        from django.contrib.contenttypes.models import ContentType
        from usuarios.models import Usuario
        
        # Crear tipo de cliente
        self.tipo_cliente = TipoCliente.objects.create(
            nombre='Tipo Test',
            descuento=Decimal('5.00'),
            activo=True
        )
        
        # Crear usuarios
        self.usuario_analista = Usuario.objects.create_user(
            email='analista@test.com',
            nombre='Analista',
            apellido='Test',
            password='test123'
        )
        
        self.usuario_operador = Usuario.objects.create_user(
            email='operador@test.com',
            nombre='Operador',
            apellido='Test',
            password='test123'
        )
        
        # Crear grupos
        self.grupo_analista = Group.objects.create(name='Analista Test')
        self.grupo_operador = Group.objects.create(name='Operador Test')
        
        # Obtener el ContentType de Cliente
        content_type = ContentType.objects.get_for_model(Cliente)
        
        # Obtener permisos
        self.perm_view_cliente = Permission.objects.get(
            codename='view_cliente',
            content_type=content_type
        )
        self.perm_view_all_clients = Permission.objects.get(
            codename='can_view_all_clients',
            content_type=content_type
        )
        
        # Asignar permisos a grupos
        # Analista: puede ver todos los clientes
        self.grupo_analista.permissions.add(self.perm_view_cliente)
        self.grupo_analista.permissions.add(self.perm_view_all_clients)
        
        # Operador: solo puede ver clientes asociados
        self.grupo_operador.permissions.add(self.perm_view_cliente)
        
        # Asignar usuarios a grupos
        self.usuario_analista.groups.add(self.grupo_analista)
        self.usuario_operador.groups.add(self.grupo_operador)
        
        # Crear clientes
        self.cliente1 = Cliente.objects.create(
            nombre_comercial='Cliente 1',
            ruc='11111111',
            tipo_cliente=self.tipo_cliente,
            activo=True
        )
        
        self.cliente2 = Cliente.objects.create(
            nombre_comercial='Cliente 2',
            ruc='22222222',
            tipo_cliente=self.tipo_cliente,
            activo=True
        )
        
        self.cliente3 = Cliente.objects.create(
            nombre_comercial='Cliente 3',
            ruc='33333333',
            tipo_cliente=self.tipo_cliente,
            activo=True
        )
        
        # Asociar cliente1 y cliente2 al operador
        self.cliente1.usuarios_asociados.add(self.usuario_operador)
        self.cliente2.usuarios_asociados.add(self.usuario_operador)
        
    def test_analista_can_view_all_clients(self):
        """Test: El usuario Analista puede ver todos los clientes"""
        self.assertTrue(
            self.usuario_analista.has_perm('clientes.can_view_all_clients'),
            "El Analista debería tener el permiso can_view_all_clients"
        )
        
    def test_operador_cannot_view_all_clients(self):
        """Test: El usuario Operador NO puede ver todos los clientes"""
        self.assertFalse(
            self.usuario_operador.has_perm('clientes.can_view_all_clients'),
            "El Operador NO debería tener el permiso can_view_all_clients"
        )
    
    def test_analista_sees_all_clients_in_list_view(self):
        """Test: El Analista ve todos los clientes en la vista de lista"""
        from .views import ClienteListView
        from django.test import RequestFactory
        
        factory = RequestFactory()
        request = factory.get('/clientes/')
        request.user = self.usuario_analista
        
        view = ClienteListView()
        view.request = request
        
        queryset = view.get_queryset()
        
        self.assertEqual(queryset.count(), 3, "El Analista debería ver los 3 clientes")
        self.assertIn(self.cliente1, queryset)
        self.assertIn(self.cliente2, queryset)
        self.assertIn(self.cliente3, queryset)
    
    def test_operador_sees_only_associated_clients(self):
        """Test: El Operador ve solo los clientes asociados"""
        from .views import ClienteListView
        from django.test import RequestFactory
        
        factory = RequestFactory()
        request = factory.get('/clientes/')
        request.user = self.usuario_operador
        
        view = ClienteListView()
        view.request = request
        
        queryset = view.get_queryset()
        
        self.assertEqual(queryset.count(), 2, "El Operador debería ver solo 2 clientes asociados")
        self.assertIn(self.cliente1, queryset)
        self.assertIn(self.cliente2, queryset)
        self.assertNotIn(self.cliente3, queryset, "El Operador NO debería ver el cliente3")
    
    def test_operador_without_associations_sees_no_clients(self):
        """Test: Un Operador sin clientes asociados no ve ningún cliente"""
        from .views import ClienteListView
        from django.test import RequestFactory
        from usuarios.models import Usuario
        
        # Crear un operador sin clientes asociados
        usuario_sin_clientes = Usuario.objects.create_user(
            email='operador_sin_clientes@test.com',
            nombre='Operador',
            apellido='Sin Clientes',
            password='test123'
        )
        usuario_sin_clientes.groups.add(self.grupo_operador)
        
        factory = RequestFactory()
        request = factory.get('/clientes/')
        request.user = usuario_sin_clientes
        
        view = ClienteListView()
        view.request = request
        
        queryset = view.get_queryset()
        
        self.assertEqual(queryset.count(), 0, "Un Operador sin clientes asociados no debería ver ningún cliente")
    
    def test_permission_works_with_filters(self):
        """Test: El permiso funciona correctamente con filtros de búsqueda"""
        from .views import ClienteListView
        from django.test import RequestFactory
        
        factory = RequestFactory()
        
        # Test con Analista (ve todos)
        request = factory.get('/clientes/?q=Cliente')
        request.user = self.usuario_analista
        
        view = ClienteListView()
        view.request = request
        
        queryset = view.get_queryset()
        self.assertEqual(queryset.count(), 3, "El Analista debería ver los 3 clientes con el filtro")
        
        # Test con Operador (ve solo asociados)
        request = factory.get('/clientes/?q=Cliente')
        request.user = self.usuario_operador
        
        view = ClienteListView()
        view.request = request
        
        queryset = view.get_queryset()
        self.assertEqual(queryset.count(), 2, "El Operador debería ver solo 2 clientes con el filtro")
    
    def test_admin_can_view_all_clients(self):
        """Test: El usuario Admin tiene el permiso can_view_all_clients"""
        from django.contrib.auth.models import Group, Permission
        from django.contrib.contenttypes.models import ContentType
        from usuarios.models import Usuario
        
        # Crear usuario Admin
        usuario_admin = Usuario.objects.create_user(
            email='admin@test.com',
            nombre='Admin',
            apellido='Test',
            password='test123'
        )
        
        # Crear grupo Admin y asignar todos los permisos
        grupo_admin = Group.objects.create(name='Admin Test Group')
        all_permissions = Permission.objects.all()
        grupo_admin.permissions.set(all_permissions)
        usuario_admin.groups.add(grupo_admin)
        
        self.assertTrue(
            usuario_admin.has_perm('clientes.can_view_all_clients'),
            "El Admin debería tener el permiso can_view_all_clients"
        )
    
    def test_admin_sees_all_clients_in_list_view(self):
        """Test: El Admin ve todos los clientes en la vista de lista"""
        from .views import ClienteListView
        from django.test import RequestFactory
        from django.contrib.auth.models import Group, Permission
        from usuarios.models import Usuario
        
        # Crear usuario Admin
        usuario_admin = Usuario.objects.create_user(
            email='admin2@test.com',
            nombre='Admin',
            apellido='Test2',
            password='test123'
        )
        
        # Crear grupo Admin y asignar todos los permisos
        grupo_admin = Group.objects.create(name='Admin Test Group 2')
        all_permissions = Permission.objects.all()
        grupo_admin.permissions.set(all_permissions)
        usuario_admin.groups.add(grupo_admin)
        
        factory = RequestFactory()
        request = factory.get('/clientes/')
        request.user = usuario_admin
        
        view = ClienteListView()
        view.request = request
        
        queryset = view.get_queryset()
        
        self.assertEqual(queryset.count(), 3, "El Admin debería ver los 3 clientes")
        self.assertIn(self.cliente1, queryset)
        self.assertIn(self.cliente2, queryset)
        self.assertIn(self.cliente3, queryset)


