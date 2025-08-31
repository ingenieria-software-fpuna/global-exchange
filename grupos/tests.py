from django.test import TestCase
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model
from grupos.models import Grupo
from grupos.backends import GrupoActivoBackend

Usuario = get_user_model()


class GrupoActivoBackendTest(TestCase):
    """Tests para el backend de autenticación personalizado"""
    
    def setUp(self):
        """Configurar datos de prueba"""
        # Crear usuario de prueba
        self.usuario = Usuario.objects.create_user(
            email='test@example.com',
            password='testpass123',
            nombre='Usuario',
            apellido='Prueba',
            cedula='12345678',
            fecha_nacimiento='1990-01-01'
        )
        
        # Crear grupos
        self.grupo_activo = Group.objects.create(name='Grupo Activo')
        self.grupo_inactivo = Group.objects.create(name='Grupo Inactivo')
        
        # Crear extensiones de grupos
        self.extension_activa = Grupo.objects.create(
            group=self.grupo_activo,
            es_activo=True
        )
        self.extension_inactiva = Grupo.objects.create(
            group=self.grupo_inactivo,
            es_activo=False
        )
        
        # Crear permisos
        content_type = ContentType.objects.get_for_model(Usuario)
        self.perm_view = Permission.objects.create(
            codename='test_view',
            name='Can view test',
            content_type=content_type
        )
        self.perm_add = Permission.objects.create(
            codename='test_add',
            name='Can add test',
            content_type=content_type
        )
        
        # Asignar permisos a grupos
        self.grupo_activo.permissions.add(self.perm_view)
        self.grupo_inactivo.permissions.add(self.perm_add)
        
        # Asignar usuario a ambos grupos
        self.usuario.groups.add(self.grupo_activo, self.grupo_inactivo)
        
        # Crear instancia del backend
        self.backend = GrupoActivoBackend()
    
    def test_grupos_activos_permisos(self):
        """Test que solo grupos activos otorgan permisos"""
        # El usuario debería tener solo el permiso del grupo activo
        user_permissions = self.backend.get_group_permissions(self.usuario)
        
        self.assertIn(self.perm_view, user_permissions)
        self.assertNotIn(self.perm_add, user_permissions)
    
    def test_has_perm_grupo_activo(self):
        """Test que has_perm funciona correctamente con grupos activos"""
        # Debería tener permiso del grupo activo
        self.assertTrue(
            self.backend.has_perm(self.usuario, 'usuarios.test_view')
        )
        
        # No debería tener permiso del grupo inactivo
        self.assertFalse(
            self.backend.has_perm(self.usuario, 'usuarios.test_add')
        )
    
    def test_get_all_permissions(self):
        """Test que get_all_permissions solo incluye permisos de grupos activos"""
        all_permissions = self.backend.get_all_permissions(self.usuario)
        
        # Convertir a strings para comparación
        perm_strings = {f"{p.content_type.app_label}.{p.codename}" for p in all_permissions}
        
        self.assertIn('usuarios.test_view', perm_strings)
        self.assertNotIn('usuarios.test_add', perm_strings)
    
    def test_grupo_sin_extension_es_activo(self):
        """Test que grupos sin extensión se consideran activos por compatibilidad"""
        # Crear grupo sin extensión
        grupo_sin_extension = Group.objects.create(name='Grupo Sin Extensión')
        grupo_sin_extension.permissions.add(self.perm_add)
        self.usuario.groups.add(grupo_sin_extension)
        
        # El usuario debería tener el permiso del grupo sin extensión
        self.assertTrue(
            self.backend.has_perm(self.usuario, 'usuarios.test_add')
        )
    
    def test_usuario_inactivo_sin_permisos(self):
        """Test que usuarios inactivos no tienen permisos"""
        self.usuario.is_active = False
        self.usuario.save()
        
        # Usuario inactivo no debería tener permisos
        self.assertFalse(
            self.backend.has_perm(self.usuario, 'usuarios.test_view')
        )
        
        user_permissions = self.backend.get_all_permissions(self.usuario)
        self.assertEqual(len(user_permissions), 0)
    
    def test_multiple_grupos_activos(self):
        """Test que permisos de múltiples grupos activos se combinan"""
        # Crear otro grupo activo con permiso diferente
        grupo_activo_2 = Group.objects.create(name='Grupo Activo 2')
        Grupo.objects.create(group=grupo_activo_2, es_activo=True)
        
        perm_edit = Permission.objects.create(
            codename='test_edit',
            name='Can edit test',
            content_type=ContentType.objects.get_for_model(Usuario)
        )
        grupo_activo_2.permissions.add(perm_edit)
        
        self.usuario.groups.add(grupo_activo_2)
        
        # El usuario debería tener permisos de ambos grupos activos
        self.assertTrue(
            self.backend.has_perm(self.usuario, 'usuarios.test_view')
        )
        self.assertTrue(
            self.backend.has_perm(self.usuario, 'usuarios.test_edit')
        )
        self.assertFalse(
            self.backend.has_perm(self.usuario, 'usuarios.test_add')
        )


class GrupoModelTest(TestCase):
    """Tests para el modelo Grupo"""
    
    def test_crear_grupo_con_extension(self):
        """Test crear grupo con extensión personalizada"""
        grupo_django = Group.objects.create(name='Test Group')
        grupo_extension = Grupo.objects.create(
            group=grupo_django,
            es_activo=True
        )
        
        self.assertEqual(grupo_extension.name, 'Test Group')
        self.assertTrue(grupo_extension.es_activo)
        self.assertEqual(grupo_extension.group, grupo_django)
    
    def test_propiedades_compatibilidad(self):
        """Test que las propiedades de compatibilidad funcionan"""
        grupo_django = Group.objects.create(name='Test Group')
        grupo_extension = Grupo.objects.create(
            group=grupo_django,
            es_activo=True
        )
        
        # Test propiedades de compatibilidad
        self.assertEqual(grupo_extension.name, grupo_django.name)
        self.assertEqual(grupo_extension.permissions, grupo_django.permissions)
        self.assertEqual(grupo_extension.user_set, grupo_django.user_set)