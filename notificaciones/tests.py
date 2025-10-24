"""
Pruebas para el módulo de notificaciones de cambios en tasas de cambio.
"""
from django.test import TestCase, Client
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.urls import reverse
from monedas.models import Moneda
from tasa_cambio.models import TasaCambio
from .models import Notificacion

Usuario = get_user_model()


class NotificacionModelTest(TestCase):
    """Pruebas para el modelo Notificacion"""

    def setUp(self):
        self.usuario = Usuario.objects.create_user(
            email='test@example.com',
            password='testpass123',
            nombre='Test',
            cedula='1234567',
            fecha_nacimiento='1990-01-01'
        )
        self.moneda = Moneda.objects.create(
            nombre='Dólar',
            codigo='USD',
            simbolo='$',
            decimales=2
        )

    def test_crear_notificacion(self):
        """Prueba crear una notificación"""
        notificacion = Notificacion.objects.create(
            usuario=self.usuario,
            tipo='tasa_cambio',
            titulo='Test',
            mensaje='Mensaje de prueba',
            moneda=self.moneda
        )
        self.assertEqual(notificacion.usuario, self.usuario)
        self.assertEqual(notificacion.tipo, 'tasa_cambio')
        self.assertFalse(notificacion.leida)
        self.assertIsNone(notificacion.fecha_lectura)

    def test_marcar_como_leida(self):
        """Prueba marcar notificación como leída"""
        notificacion = Notificacion.objects.create(
            usuario=self.usuario,
            tipo='tasa_cambio',
            titulo='Test',
            mensaje='Mensaje'
        )
        self.assertFalse(notificacion.leida)
        
        notificacion.marcar_como_leida()
        
        self.assertTrue(notificacion.leida)
        self.assertIsNotNone(notificacion.fecha_lectura)

    def test_cambio_porcentual(self):
        """Prueba el cálculo del cambio porcentual"""
        notificacion = Notificacion.objects.create(
            usuario=self.usuario,
            tipo='tasa_cambio',
            titulo='Cambio',
            mensaje='Cambio de tasa',
            precio_base_anterior=1000,
            precio_base_nuevo=1100
        )
        
        self.assertEqual(notificacion.cambio_porcentual, 10.0)
        self.assertTrue(notificacion.es_aumento)

    def test_cambio_porcentual_disminucion(self):
        """Prueba el cambio porcentual con disminución"""
        notificacion = Notificacion.objects.create(
            usuario=self.usuario,
            tipo='tasa_cambio',
            titulo='Cambio',
            mensaje='Cambio de tasa',
            precio_base_anterior=1000,
            precio_base_nuevo=900
        )
        
        self.assertEqual(notificacion.cambio_porcentual, -10.0)
        self.assertFalse(notificacion.es_aumento)


class NotificacionSignalTest(TestCase):
    """Pruebas para las señales de notificación"""

    def setUp(self):
        # Crear grupos necesarios
        self.grupo_operador = Group.objects.create(name='Operador')
        self.grupo_visitante = Group.objects.create(name='Visitante')
        self.grupo_admin = Group.objects.create(name='Admin')
        
        # Crear usuarios con diferentes roles
        self.usuario_operador = Usuario.objects.create_user(
            email='operador@example.com',
            password='pass123',
            nombre='Operador',
            cedula='1111111',
            fecha_nacimiento='1990-01-01'
        )
        # Limpiar grupos auto-asignados y asignar el correcto
        self.usuario_operador.groups.clear()
        self.usuario_operador.groups.add(self.grupo_operador)
        
        self.usuario_visitante = Usuario.objects.create_user(
            email='visitante@example.com',
            password='pass123',
            nombre='Visitante',
            cedula='2222222',
            fecha_nacimiento='1990-01-01'
        )
        # Este ya debería tener Visitante, pero lo aseguramos
        self.usuario_visitante.groups.clear()
        self.usuario_visitante.groups.add(self.grupo_visitante)
        
        # Usuario admin que NO debe recibir notificaciones
        self.usuario_admin = Usuario.objects.create_user(
            email='admin@example.com',
            password='pass123',
            nombre='Admin',
            cedula='3333333',
            fecha_nacimiento='1990-01-01'
        )
        # Limpiar grupos auto-asignados y asignar solo Admin
        self.usuario_admin.groups.clear()
        self.usuario_admin.groups.add(self.grupo_admin)
        
        self.moneda = Moneda.objects.create(
            nombre='Euro',
            codigo='EUR',
            simbolo='€',
            decimales=2
        )

    def test_crear_tasa_genera_notificaciones(self):
        """Prueba que crear una tasa genera notificaciones solo para Operador y Visitante"""
        # Contar notificaciones antes
        count_antes = Notificacion.objects.count()
        
        # Crear nueva tasa
        TasaCambio.objects.create(
            moneda=self.moneda,
            precio_base=7500,
            comision_compra=50,
            comision_venta=50,
            es_activa=True
        )
        
        # Verificar que se crearon notificaciones
        count_despues = Notificacion.objects.count()
        self.assertEqual(count_despues, count_antes + 2)  # Solo Operador y Visitante
        
        # Verificar que Operador y Visitante tienen notificaciones
        self.assertTrue(
            Notificacion.objects.filter(usuario=self.usuario_operador).exists()
        )
        self.assertTrue(
            Notificacion.objects.filter(usuario=self.usuario_visitante).exists()
        )
        
        # Verificar que Admin NO tiene notificaciones
        self.assertFalse(
            Notificacion.objects.filter(usuario=self.usuario_admin).exists()
        )

    def test_actualizar_tasa_genera_notificaciones(self):
        """Prueba que actualizar una tasa genera notificaciones solo para roles permitidos"""
        # Crear tasa inicial
        tasa = TasaCambio.objects.create(
            moneda=self.moneda,
            precio_base=7500,
            comision_compra=50,
            comision_venta=50,
            es_activa=True
        )
        
        # Limpiar notificaciones iniciales
        Notificacion.objects.all().delete()
        
        # Actualizar tasa
        tasa.precio_base = 7600
        tasa.save()
        
        # Verificar nuevas notificaciones
        notificaciones = Notificacion.objects.all()
        self.assertEqual(notificaciones.count(), 2)  # Solo Operador y Visitante
        
        # Verificar que Admin NO recibió notificación
        self.assertFalse(
            Notificacion.objects.filter(usuario=self.usuario_admin).exists()
        )


class NotificacionViewTest(TestCase):
    """Pruebas para las vistas de notificaciones"""

    def setUp(self):
        self.client = Client()
        
        # Crear grupos
        self.grupo_visitante = Group.objects.create(name='Visitante')
        self.grupo_admin = Group.objects.create(name='Admin')
        
        # Usuario con rol Visitante (puede ver notificaciones)
        self.usuario = Usuario.objects.create_user(
            email='testview@example.com',
            password='pass123',
            nombre='Test',
            cedula='3333333',
            fecha_nacimiento='1990-01-01'
        )
        self.usuario.groups.clear()
        self.usuario.groups.add(self.grupo_visitante)
        
        # Usuario Admin (NO puede ver notificaciones)
        self.usuario_admin = Usuario.objects.create_user(
            email='admin@example.com',
            password='pass123',
            nombre='Admin',
            cedula='4444444',
            fecha_nacimiento='1990-01-01'
        )
        self.usuario_admin.groups.clear()
        self.usuario_admin.groups.add(self.grupo_admin)
        
        # Crear algunas notificaciones para el usuario visitante
        for i in range(5):
            Notificacion.objects.create(
                usuario=self.usuario,
                tipo='tasa_cambio',
                titulo=f'Notificación {i}',
                mensaje=f'Mensaje {i}'
            )

    def test_lista_notificaciones_accesible(self):
        """Prueba que la lista de notificaciones es accesible para Visitante"""
        self.client.login(email='testview@example.com', password='pass123')
        response = self.client.get(reverse('notificaciones:lista'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Mis Notificaciones')
    
    def test_lista_bloqueada_para_admin(self):
        """Prueba que la lista de notificaciones está bloqueada para Admin"""
        self.client.login(email='admin@example.com', password='pass123')
        response = self.client.get(reverse('notificaciones:lista'))
        self.assertEqual(response.status_code, 403)  # Forbidden

    def test_lista_requiere_autenticacion(self):
        """Prueba que la lista requiere autenticación"""
        self.client.logout()
        response = self.client.get(reverse('notificaciones:lista'))
        self.assertEqual(response.status_code, 302)  # Redirect a login

    def test_marcar_leida(self):
        """Prueba marcar una notificación como leída"""
        self.client.login(email='testview@example.com', password='pass123')
        notificacion = Notificacion.objects.filter(usuario=self.usuario).first()
        self.assertFalse(notificacion.leida)
        
        response = self.client.post(
            reverse('notificaciones:marcar_leida', args=[notificacion.pk])
        )
        
        notificacion.refresh_from_db()
        self.assertTrue(notificacion.leida)

    def test_marcar_todas_leidas(self):
        """Prueba marcar todas las notificaciones como leídas"""
        self.client.login(email='testview@example.com', password='pass123')
        # Verificar que hay no leídas
        no_leidas = Notificacion.objects.filter(
            usuario=self.usuario,
            leida=False
        ).count()
        self.assertGreater(no_leidas, 0)
        
        # Marcar todas
        response = self.client.post(
            reverse('notificaciones:marcar_todas_leidas')
        )
        
        # Verificar que no quedan no leídas
        no_leidas_despues = Notificacion.objects.filter(
            usuario=self.usuario,
            leida=False
        ).count()
        self.assertEqual(no_leidas_despues, 0)

    def test_contar_no_leidas(self):
        """Prueba el endpoint de conteo de no leídas"""
        self.client.login(email='testview@example.com', password='pass123')
        response = self.client.get(reverse('notificaciones:contar_no_leidas'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('count', data)
        self.assertEqual(data['count'], 5)  # Las 5 creadas en setUp
    
    def test_contar_no_leidas_admin_retorna_cero(self):
        """Prueba que el conteo retorna 0 para Admin"""
        self.client.login(email='admin@example.com', password='pass123')
        response = self.client.get(reverse('notificaciones:contar_no_leidas'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data['count'], 0)

    def test_eliminar_notificacion(self):
        """Prueba eliminar una notificación"""
        self.client.login(email='testview@example.com', password='pass123')
        notificacion = Notificacion.objects.filter(usuario=self.usuario).first()
        pk = notificacion.pk
        
        response = self.client.post(
            reverse('notificaciones:eliminar', args=[pk])
        )
        
        # Verificar que ya no existe
        self.assertFalse(
            Notificacion.objects.filter(pk=pk).exists()
        )

    def test_filtro_no_leidas(self):
        """Prueba el filtro de no leídas"""
        self.client.login(email='testview@example.com', password='pass123')
        # Marcar algunas como leídas
        notis = Notificacion.objects.filter(usuario=self.usuario)[:2]
        for noti in notis:
            noti.marcar_como_leida()
        
        response = self.client.get(
            reverse('notificaciones:lista') + '?filtro=no_leidas'
        )
        
        self.assertEqual(response.status_code, 200)
        # Debería mostrar solo 3 (5 - 2 leídas)
        self.assertContains(response, 'Notificación')
    
    def test_notificaciones_recientes(self):
        """Prueba el endpoint de notificaciones recientes para el popup"""
        self.client.login(email='testview@example.com', password='pass123')
        response = self.client.get(reverse('notificaciones:recientes'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn('notificaciones', data)
        self.assertIn('total_no_leidas', data)
        # Debe retornar máximo 5 notificaciones
        self.assertLessEqual(len(data['notificaciones']), 5)
        # Verificar estructura de cada notificación
        if len(data['notificaciones']) > 0:
            notif = data['notificaciones'][0]
            self.assertIn('id', notif)
            self.assertIn('titulo', notif)
            self.assertIn('mensaje', notif)
            self.assertIn('leida', notif)
            self.assertIn('fecha_creacion', notif)
    
    def test_notificaciones_recientes_admin_sin_acceso(self):
        """Prueba que Admin no puede acceder al endpoint de recientes"""
        self.client.login(email='admin@example.com', password='pass123')
        response = self.client.get(reverse('notificaciones:recientes'))
        self.assertEqual(response.status_code, 200)
        data = response.json()
        # Admin recibe lista vacía
        self.assertEqual(len(data['notificaciones']), 0)
        self.assertEqual(data['total_no_leidas'], 0)


class PreferenciasNotificacionesTest(TestCase):
    """Tests para las preferencias de notificaciones"""
    
    def setUp(self):
        """Configuración inicial para los tests de preferencias"""
        # Crear grupos
        self.grupo_visitante = Group.objects.create(name='Visitante')
        
        # Crear usuario
        self.usuario = Usuario.objects.create_user(
            email='testpref@example.com',
            password='pass123',
            nombre='Test',
            apellido='Preferencias'
        )
        self.usuario.groups.add(self.grupo_visitante)
        self.usuario.save()
    
    def test_preferencias_accesible_para_visitante(self):
        """Prueba que Visitante puede acceder a preferencias"""
        self.client.login(email='testpref@example.com', password='pass123')
        response = self.client.get(reverse('notificaciones:preferencias'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Preferencias de Notificaciones')
    
    def test_cambiar_preferencia_email(self):
        """Prueba que el usuario puede activar/desactivar emails"""
        self.client.login(email='testpref@example.com', password='pass123')
        
        # Inicialmente desactivado
        self.assertFalse(self.usuario.recibir_notificaciones_email)
        
        # Activar
        response = self.client.post(
            reverse('notificaciones:preferencias'),
            {'recibir_notificaciones_email': True}
        )
        self.assertEqual(response.status_code, 302)  # Redirect
        
        # Verificar que se activó
        self.usuario.refresh_from_db()
        self.assertTrue(self.usuario.recibir_notificaciones_email)
        
        # Desactivar
        response = self.client.post(
            reverse('notificaciones:preferencias'),
            {}  # Checkbox no marcado = False
        )
        self.assertEqual(response.status_code, 302)
        
        # Verificar que se desactivó
        self.usuario.refresh_from_db()
        self.assertFalse(self.usuario.recibir_notificaciones_email)
