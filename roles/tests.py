from django.test import TestCase, RequestFactory
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.contrib.auth import get_user_model
from unittest.mock import Mock, patch
from decimal import Decimal

from .models import Modulo, Permiso, Rol, RolPermiso, UsuarioRol
from .services import RolesService, Permisos
from .forms import RolForm, PermisoForm, ModuloForm
from .decorators import requiere_permiso, requiere_rol
from .mixins import PermisoRequeridoMixin

Usuario = get_user_model()


class ModuloModelTestCase(TestCase):
    """Tests unitarios para el modelo Modulo"""
    
    def setUp(self):
        self.modulo_data = {
            'nombre': 'Gestión de Usuarios',
            'descripcion': 'Módulo para administrar usuarios',
            'codigo': 'usuarios',
            'activo': True,
            'orden': 1
        }

    def test_create_modulo(self):
        """Test creación de módulo"""
        modulo = Modulo.objects.create(**self.modulo_data)
        
        self.assertEqual(modulo.nombre, 'Gestión de Usuarios')
        self.assertEqual(modulo.codigo, 'usuarios')
        self.assertTrue(modulo.activo)
        self.assertEqual(modulo.orden, 1)
        self.assertIsNotNone(modulo.created_at)
        self.assertIsNotNone(modulo.updated_at)

    def test_modulo_str_representation(self):
        """Test representación string del módulo"""
        modulo = Modulo.objects.create(**self.modulo_data)
        self.assertEqual(str(modulo), 'Gestión de Usuarios')

    def test_modulo_unique_nombre(self):
        """Test que el nombre debe ser único"""
        Modulo.objects.create(**self.modulo_data)
        
        with self.assertRaises(IntegrityError):
            Modulo.objects.create(
                nombre='Gestión de Usuarios',
                codigo='usuarios2',
                activo=True
            )

    def test_modulo_unique_codigo(self):
        """Test que el código debe ser único"""
        Modulo.objects.create(**self.modulo_data)
        
        with self.assertRaises(IntegrityError):
            Modulo.objects.create(
                nombre='Otro Módulo',
                codigo='usuarios',
                activo=True
            )

    def test_modulo_meta_options(self):
        """Test opciones de Meta del modelo"""
        meta = Modulo._meta
        
        self.assertEqual(meta.db_table, 'roles_modulos')
        self.assertEqual(meta.ordering, ['orden', 'nombre'])
        self.assertEqual(meta.verbose_name, 'Módulo')
        self.assertEqual(meta.verbose_name_plural, 'Módulos')

    def test_modulo_default_values(self):
        """Test valores por defecto del modelo"""
        modulo = Modulo.objects.create(
            nombre='Módulo Test',
            codigo='test'
        )
        
        self.assertTrue(modulo.activo)
        self.assertEqual(modulo.orden, 0)
        self.assertEqual(modulo.descripcion, '')


class PermisoModelTestCase(TestCase):
    """Tests unitarios para el modelo Permiso"""
    
    def setUp(self):
        self.modulo = Modulo.objects.create(
            nombre='Test Module',
            codigo='test',
            activo=True
        )
        self.permiso_data = {
            'nombre': 'Leer Usuarios',
            'codigo': 'usuario_leer',
            'descripcion': 'Permite leer información de usuarios',
            'tipo': 'read',
            'modulo': self.modulo,
            'activo': True
        }

    def test_create_permiso(self):
        """Test creación de permiso"""
        permiso = Permiso.objects.create(**self.permiso_data)
        
        self.assertEqual(permiso.nombre, 'Leer Usuarios')
        self.assertEqual(permiso.codigo, 'usuario_leer')
        self.assertEqual(permiso.tipo, 'read')
        self.assertEqual(permiso.modulo, self.modulo)
        self.assertTrue(permiso.activo)

    def test_permiso_str_representation(self):
        """Test representación string del permiso"""
        permiso = Permiso.objects.create(**self.permiso_data)
        expected = f"{self.modulo.nombre} - {permiso.nombre}"
        self.assertEqual(str(permiso), expected)

    def test_permiso_tipos_choices(self):
        """Test que los tipos de permiso están definidos correctamente"""
        tipos_esperados = [
            ('create', 'Crear'),
            ('read', 'Leer'),
            ('update', 'Actualizar'),
            ('delete', 'Eliminar'),
            ('custom', 'Personalizado'),
        ]
        self.assertEqual(Permiso.TIPOS_PERMISO, tipos_esperados)

    def test_permiso_unique_together(self):
        """Test que código y módulo deben ser únicos juntos"""
        Permiso.objects.create(**self.permiso_data)
        
        with self.assertRaises(IntegrityError):
            Permiso.objects.create(
                nombre='Otro Permiso',
                codigo='usuario_leer',
                tipo='create',
                modulo=self.modulo,
                activo=True
            )

    def test_permiso_meta_options(self):
        """Test opciones de Meta del modelo"""
        meta = Permiso._meta
        
        self.assertEqual(meta.db_table, 'roles_permisos')
        self.assertEqual(meta.ordering, ['modulo', 'tipo', 'nombre'])
        self.assertEqual(meta.unique_together, (('codigo', 'modulo'),))


class RolModelTestCase(TestCase):
    """Tests unitarios para el modelo Rol"""
    
    def setUp(self):
        self.modulo = Modulo.objects.create(nombre='Test', codigo='test')
        self.permiso = Permiso.objects.create(
            nombre='Test Permission',
            codigo='test_perm',
            tipo='read',
            modulo=self.modulo
        )
        self.rol_data = {
            'nombre': 'Administrador',
            'descripcion': 'Rol con todos los permisos',
            'codigo': 'admin',
            'es_admin': True,
            'activo': True
        }

    def test_create_rol(self):
        """Test creación de rol"""
        rol = Rol.objects.create(**self.rol_data)
        
        self.assertEqual(rol.nombre, 'Administrador')
        self.assertEqual(rol.codigo, 'admin')
        self.assertTrue(rol.es_admin)
        self.assertTrue(rol.activo)

    def test_rol_str_representation(self):
        """Test representación string del rol"""
        rol = Rol.objects.create(**self.rol_data)
        self.assertEqual(str(rol), 'Administrador')

    def test_rol_clean_admin_activo(self):
        """Test que un rol admin no puede estar inactivo"""
        rol = Rol(
            nombre='Admin Inactivo',
            codigo='admin_inactivo',
            es_admin=True,
            activo=False
        )
        
        with self.assertRaises(ValidationError):
            rol.clean()

    def test_rol_tiene_permiso_admin(self):
        """Test que un rol admin tiene todos los permisos"""
        rol = Rol.objects.create(**self.rol_data)
        
        self.assertTrue(rol.tiene_permiso('cualquier_codigo'))
        self.assertTrue(rol.tiene_permiso('usuario_leer'))

    def test_rol_tiene_permiso_normal(self):
        """Test verificación de permiso para rol normal"""
        rol_data = self.rol_data.copy()
        rol_data['es_admin'] = False
        rol = Rol.objects.create(**rol_data)
        
        self.assertFalse(rol.tiene_permiso('test_perm'))
        
        rol.permisos.add(self.permiso)
        self.assertTrue(rol.tiene_permiso('test_perm'))

    def test_rol_get_permisos_por_modulo(self):
        """Test que el método get_permisos_por_modulo existe"""
        rol = Rol.objects.create(**self.rol_data)
        
        self.assertTrue(hasattr(rol, 'get_permisos_por_modulo'))
        self.assertTrue(callable(rol.get_permisos_por_modulo))

    def test_rol_meta_options(self):
        """Test opciones de Meta del modelo"""
        meta = Rol._meta
        
        self.assertEqual(meta.db_table, 'roles_roles')
        self.assertEqual(meta.ordering, ['nombre'])


class RolesServiceTestCase(TestCase):
    """Tests unitarios para RolesService"""
    
    def setUp(self):
        self.usuario = Usuario.objects.create_user(
            email='test@example.com',
            password='testpass123',
            nombre='Test',
            apellido='User',
            cedula='12345678',
            fecha_nacimiento='1990-01-01'
        )
        self.rol = Rol.objects.create(
            nombre='Test Role',
            codigo='test_role'
        )
        self.modulo = Modulo.objects.create(nombre='Test', codigo='test')
        self.permiso = Permiso.objects.create(
            nombre='Test Permission',
            codigo='test_perm',
            tipo='read',
            modulo=self.modulo
        )

    def test_asignar_rol_usuario_new(self):
        """Test asignación de rol nuevo a usuario"""
        usuario_rol = RolesService.asignar_rol_usuario(
            self.usuario, self.rol, 'admin'
        )
        
        self.assertEqual(usuario_rol.usuario, self.usuario)
        self.assertEqual(usuario_rol.rol, self.rol)
        self.assertEqual(usuario_rol.asignado_por, 'admin')
        self.assertTrue(usuario_rol.activo)

    def test_remover_rol_usuario_success(self):
        """Test remoción exitosa de rol"""
        UsuarioRol.objects.create(
            usuario=self.usuario,
            rol=self.rol,
            activo=True
        )
        
        resultado = RolesService.remover_rol_usuario(self.usuario, self.rol)
        self.assertTrue(resultado)
        
        usuario_rol = UsuarioRol.objects.get(usuario=self.usuario, rol=self.rol)
        self.assertFalse(usuario_rol.activo)

    def test_remover_rol_usuario_not_exists(self):
        """Test remoción de rol inexistente"""
        resultado = RolesService.remover_rol_usuario(self.usuario, self.rol)
        self.assertFalse(resultado)

    def test_usuario_es_admin(self):
        """Test verificación si usuario es admin"""
        resultado = RolesService.usuario_es_admin(self.usuario)
        self.assertFalse(resultado)
        
        rol_admin = Rol.objects.create(
            nombre='Admin',
            codigo='admin',
            es_admin=True
        )
        UsuarioRol.objects.create(
            usuario=self.usuario,
            rol=rol_admin,
            activo=True
        )
        
        resultado = RolesService.usuario_es_admin(self.usuario)
        self.assertTrue(resultado)

    def test_crear_rol_con_permisos(self):
        """Test creación de rol con permisos"""
        rol = RolesService.crear_rol_con_permisos(
            nombre='Nuevo Rol',
            codigo='nuevo_rol',
            permisos_codigos=['test_perm'],
            descripcion='Descripción test',
            asignado_por='admin'
        )
        
        self.assertEqual(rol.nombre, 'Nuevo Rol')
        self.assertEqual(rol.codigo, 'nuevo_rol')
        self.assertTrue(rol.permisos.filter(codigo='test_perm').exists())


class PermisosConstantsTestCase(TestCase):
    """Tests unitarios para las constantes de Permisos"""
    
    def test_permisos_constants_exist(self):
        """Test que todas las constantes de permisos existen"""
        expected_permissions = [
            'USUARIO_LEER', 'USUARIO_CREAR', 'USUARIO_EDITAR', 'USUARIO_ELIMINAR',
            'ROL_LEER', 'ROL_CREAR', 'ROL_EDITAR', 'ROL_ELIMINAR',
            'PERMISO_LEER', 'PERMISO_CREAR', 'PERMISO_EDITAR', 'PERMISO_ELIMINAR',
            'TIPOCLIENTE_LEER', 'TIPOCLIENTE_CREAR', 'TIPOCLIENTE_EDITAR', 'TIPOCLIENTE_ELIMINAR',
            'DASHBOARD_VER'
        ]
        
        for permission in expected_permissions:
            self.assertTrue(hasattr(Permisos, permission))
            self.assertIsInstance(getattr(Permisos, permission), str)

    def test_permisos_values(self):
        """Test que los valores de permisos son strings válidos"""
        self.assertEqual(Permisos.USUARIO_LEER, 'usuario_leer')
        self.assertEqual(Permisos.ROL_CREAR, 'rol_crear')
        self.assertEqual(Permisos.DASHBOARD_VER, 'dashboard_ver')


class RolFormsTestCase(TestCase):
    """Tests unitarios para los formularios de Rol"""
    
    def setUp(self):
        self.modulo = Modulo.objects.create(nombre='Test', codigo='test')
        self.permiso = Permiso.objects.create(
            nombre='Test Permission',
            codigo='test_perm',
            tipo='read',
            modulo=self.modulo
        )

    def test_rol_form_valid(self):
        """Test formulario de rol válido"""
        form_data = {
            'nombre': 'Test Role',
            'codigo': 'test_role',
            'descripcion': 'Test description',
            'es_admin': False,
            'activo': True,
            'permisos': [self.permiso.pk]
        }
        
        form = RolForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_rol_form_fields(self):
        """Test que el formulario tiene los campos correctos"""
        form = RolForm()
        expected_fields = ['nombre', 'descripcion', 'codigo', 'es_admin', 'activo', 'permisos']
        
        for field in expected_fields:
            self.assertIn(field, form.fields)

    def test_permiso_form_valid(self):
        """Test formulario de permiso válido"""
        modulo_test = Modulo.objects.create(nombre='Test Form Module', codigo='test_form')
        
        form_data = {
            'nombre': 'Test Permission Form',
            'codigo': 'test_perm_form',
            'descripcion': 'Test description',
            'tipo': 'read',
            'modulo': modulo_test.pk,
            'activo': True
        }
        
        form = PermisoForm(data=form_data)
        if not form.is_valid():
            print(f"Form errors: {form.errors}")
        self.assertTrue(form.is_valid())

    def test_modulo_form_valid(self):
        """Test formulario de módulo válido"""
        form_data = {
            'nombre': 'Test Module',
            'codigo': 'test_module',
            'descripcion': 'Test description',
            'orden': 1,
            'activo': True
        }
        
        form = ModuloForm(data=form_data)
        self.assertTrue(form.is_valid())


class RolesViewsTestCase(TestCase):
    """Tests unitarios para las vistas de Roles"""
    
    def setUp(self):
        self.factory = RequestFactory()

    def test_rol_list_view_attributes(self):
        """Test atributos de la vista de lista de roles"""
        from .views import RolListView
        
        self.assertEqual(RolListView.model, Rol)
        self.assertEqual(RolListView.template_name, 'roles/rol_list.html')
        self.assertEqual(RolListView.context_object_name, 'roles')
        self.assertEqual(RolListView.permiso_requerido, Permisos.ROL_LEER)

    def test_rol_create_view_attributes(self):
        """Test atributos de la vista de creación de roles"""
        from .views import RolCreateView
        
        self.assertEqual(RolCreateView.model, Rol)
        self.assertEqual(RolCreateView.form_class, RolForm)
        self.assertEqual(RolCreateView.template_name, 'roles/rol_form.html')
        self.assertEqual(RolCreateView.permiso_requerido, Permisos.ROL_CREAR)

    def test_permiso_list_view_attributes(self):
        """Test atributos de la vista de lista de permisos"""
        from .views import PermisoListView
        
        self.assertEqual(PermisoListView.model, Permiso)
        self.assertEqual(PermisoListView.template_name, 'roles/permiso_list.html')
        self.assertEqual(PermisoListView.context_object_name, 'permisos')

    def test_views_inheritance(self):
        """Test herencia correcta de las vistas"""
        from django.views.generic import ListView, CreateView, UpdateView, DeleteView
        from .views import (RolListView, RolCreateView, RolUpdateView, RolDeleteView,
                           PermisoListView, PermisoCreateView, PermisoUpdateView, PermisoDeleteView)
        
        self.assertTrue(issubclass(RolListView, PermisoRequeridoMixin))
        self.assertTrue(issubclass(RolListView, ListView))
        self.assertTrue(issubclass(RolCreateView, PermisoRequeridoMixin))
        self.assertTrue(issubclass(RolCreateView, CreateView))
        
        self.assertTrue(issubclass(PermisoListView, PermisoRequeridoMixin))
        self.assertTrue(issubclass(PermisoListView, ListView))


class RolesMixinsTestCase(TestCase):
    """Tests unitarios para los mixins de Roles"""
    
    def setUp(self):
        self.factory = RequestFactory()

    def test_permiso_requerido_mixin_attributes(self):
        """Test atributos del mixin PermisoRequeridoMixin"""
        mixin = PermisoRequeridoMixin()
        
        self.assertIsNone(mixin.permiso_requerido)
        self.assertTrue(hasattr(mixin, 'dispatch'))
        self.assertTrue(hasattr(mixin, 'handle_no_permission'))

    def test_permiso_requerido_mixin_methods_exist(self):
        """Test que los métodos del mixin existen y son callable"""
        mixin = PermisoRequeridoMixin()
        
        self.assertTrue(callable(mixin.dispatch))
        self.assertTrue(callable(mixin.handle_no_permission))


class RolesDecoratorsTestCase(TestCase):
    """Tests unitarios para los decoradores de Roles"""
    
    def test_requiere_permiso_decorator_exists(self):
        """Test que el decorador requiere_permiso existe"""
        self.assertTrue(callable(requiere_permiso))

    def test_requiere_rol_decorator_exists(self):
        """Test que el decorador requiere_rol existe"""
        self.assertTrue(callable(requiere_rol))

    def test_decorators_return_functions(self):
        """Test que los decoradores retornan funciones"""
        @requiere_permiso('test_permission')
        def test_view(request):
            return "OK"
        
        self.assertTrue(callable(test_view))
        
        @requiere_rol('test_role')
        def test_view2(request):
            return "OK"
        
        self.assertTrue(callable(test_view2))
