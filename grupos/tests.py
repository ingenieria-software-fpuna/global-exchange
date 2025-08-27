from django.test import TestCase
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model

Usuario = get_user_model()

class GruposTestCase(TestCase):
    def setUp(self):
        # Crear usuario de prueba
        self.user = Usuario.objects.create_user(
            email='test@example.com',
            password='testpass123',
            nombre='Usuario',
            apellido='Prueba'
        )
        
        # Crear grupo de prueba
        self.group = Group.objects.create(name='Grupo Prueba')
        
        # Crear permiso de prueba
        content_type = ContentType.objects.get_for_model(Usuario)
        self.permission = Permission.objects.create(
            codename='test_permission',
            name='Test Permission',
            content_type=content_type
        )
    
    def test_group_creation(self):
        """Prueba la creación de grupos"""
        group = Group.objects.create(name='Nuevo Grupo')
        self.assertEqual(group.name, 'Nuevo Grupo')
        self.assertEqual(Group.objects.count(), 2)  # 1 del setUp + 1 nuevo
    
    def test_permission_assignment(self):
        """Prueba la asignación de permisos a grupos"""
        self.group.permissions.add(self.permission)
        self.assertIn(self.permission, self.group.permissions.all())
    
    def test_user_group_assignment(self):
        """Prueba la asignación de usuarios a grupos"""
        self.user.groups.add(self.group)
        self.assertIn(self.group, self.user.groups.all())
    
    def test_user_permissions_through_groups(self):
        """Prueba que los usuarios obtengan permisos a través de grupos"""
        self.group.permissions.add(self.permission)
        self.user.groups.add(self.group)
        
        # El usuario debe tener el permiso del grupo
        self.assertTrue(self.user.has_perm('usuarios.test_permission'))
