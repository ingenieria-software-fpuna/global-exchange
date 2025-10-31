from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.utils import timezone
from decimal import Decimal
from unittest.mock import patch
import json

from .models import Tauser, Stock, StockDenominacion, HistorialStock, HistorialStockDenominacion
from monedas.models import Moneda, DenominacionMoneda
from metodo_cobro.models import MetodoCobro
from metodo_pago.models import MetodoPago
from transacciones.models import Transaccion, TipoOperacion, EstadoTransaccion
from clientes.models import Cliente, TipoCliente

Usuario = get_user_model()


class TauserModelTest(TestCase):
    """Tests importantes para el modelo Tauser"""
    
    def setUp(self):
        self.tauser = Tauser.objects.create(
            nombre='Tauser Test',
            direccion='Av. Test 123',
            horario_atencion='Lun-Vie 9:00-18:00',
            es_activo=True
        )
    
    def test_creacion_tauser(self):
        """Test: Crear un Tauser"""
        self.assertEqual(self.tauser.nombre, 'Tauser Test')
        self.assertEqual(self.tauser.direccion, 'Av. Test 123')
        self.assertTrue(self.tauser.es_activo)
        self.assertIsNotNone(self.tauser.fecha_creacion)
    
    def test_toggle_activo(self):
        """Test: Cambiar estado activo/inactivo"""
        estado_inicial = self.tauser.es_activo
        
        nuevo_estado = self.tauser.toggle_activo()
        self.assertNotEqual(nuevo_estado, estado_inicial)
        self.assertEqual(self.tauser.es_activo, nuevo_estado)
    
    def test_str_representation(self):
        """Test: Representación string del Tauser"""
        self.assertEqual(str(self.tauser), 'Tauser Test - Activo')
        
        self.tauser.es_activo = False
        self.tauser.save()
        self.assertEqual(str(self.tauser), 'Tauser Test - Inactivo')


class TauserViewsTest(TestCase):
    """Tests importantes para las vistas de Tauser"""
    
    def setUp(self):
        self.client = Client()
        self.usuario = Usuario.objects.create_user(
            email='test@example.com',
            password='testpass123',
            nombre='Test',
            apellido='User',
            cedula='12345678',
            fecha_nacimiento='1990-01-01'
        )
        
        # Asignar permisos necesarios
        view_perm = Permission.objects.get(codename='view_tauser')
        add_perm = Permission.objects.get(codename='add_tauser')
        change_perm = Permission.objects.get(codename='change_tauser')
        self.usuario.user_permissions.add(view_perm, add_perm, change_perm)
        
        self.tauser = Tauser.objects.create(
            nombre='Tauser Test',
            direccion='Av. Test 123',
            horario_atencion='Lun-Vie 9:00-18:00'
        )
        
        self.client.force_login(self.usuario)
    
    def test_tauser_list_view(self):
        """Test: Lista de Tausers"""
        response = self.client.get(reverse('tauser:tauser_list'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Tauser Test')
    
    def test_tauser_detail_view(self):
        """Test: Detalle de Tauser"""
        response = self.client.get(reverse('tauser:tauser_detail', args=[self.tauser.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Tauser Test')
        self.assertEqual(response.context['tauser'], self.tauser)
    
    def test_tauser_create_post(self):
        """Test: Crear Tauser mediante POST"""
        fecha_instalacion = timezone.now().strftime('%Y-%m-%dT%H:%M')
        
        data = {
            'nombre': 'Nuevo Tauser',
            'direccion': 'Nueva Dirección 456',  # Al menos 10 caracteres
            'horario_atencion': 'Lun-Vie 8:00-17:00',  # Al menos 5 caracteres
            'es_activo': True,
            'fecha_instalacion': fecha_instalacion
        }
        response = self.client.post(reverse('tauser:tauser_create'), data)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(Tauser.objects.filter(nombre='Nuevo Tauser').exists())
    
    def test_tauser_update_post(self):
        """Test: Actualizar Tauser mediante POST"""
        fecha_instalacion = self.tauser.fecha_instalacion.strftime('%Y-%m-%dT%H:%M')
        
        data = {
            'nombre': 'Tauser Actualizado',
            'direccion': self.tauser.direccion,  # Ya tiene más de 10 caracteres
            'horario_atencion': self.tauser.horario_atencion,  # Ya tiene más de 5 caracteres
            'es_activo': self.tauser.es_activo,
            'fecha_instalacion': fecha_instalacion
        }
        response = self.client.post(reverse('tauser:tauser_update', args=[self.tauser.pk]), data)
        self.assertEqual(response.status_code, 302)
        self.tauser.refresh_from_db()
        self.assertEqual(self.tauser.nombre, 'Tauser Actualizado')
    
    def test_tauser_sin_permisos(self):
        """Test: Usuario sin permisos no puede acceder"""
        usuario_sin_permisos = Usuario.objects.create_user(
            email='nospermisos@example.com',
            password='testpass123',
            nombre='Sin',
            apellido='Permisos',
            cedula='87654321',
            fecha_nacimiento='1990-01-01'
        )
        self.client.force_login(usuario_sin_permisos)
        
        response = self.client.get(reverse('tauser:tauser_list'))
        self.assertEqual(response.status_code, 403)


class StockModelTest(TestCase):
    """Tests importantes para el modelo Stock"""
    
    def setUp(self):
        self.tauser = Tauser.objects.create(
            nombre='Tauser Test',
            direccion='Av. Test 123',
            horario_atencion='Lun-Vie 9:00-18:00'
        )
        
        self.moneda = Moneda.objects.create(
            codigo='USD',
            nombre='Dólar Estadounidense',
            simbolo='$',
            es_activa=True,
            decimales=2
        )
        
        self.stock = Stock.objects.create(
            tauser=self.tauser,
            moneda=self.moneda,
            cantidad=Decimal('1000.00'),
            es_activo=True
        )
        
        self.usuario = Usuario.objects.create_user(
            email='test@example.com',
            password='testpass123',
            nombre='Test',
            apellido='User',
            cedula='12345678',
            fecha_nacimiento='1990-01-01'
        )
    
    def test_crear_stock(self):
        """Test: Crear un Stock"""
        self.assertEqual(self.stock.tauser, self.tauser)
        self.assertEqual(self.stock.moneda, self.moneda)
        self.assertEqual(self.stock.cantidad, Decimal('1000.00'))
        self.assertTrue(self.stock.es_activo)
    
    def test_agregar_cantidad(self):
        """Test: Agregar cantidad al stock"""
        cantidad_inicial = self.stock.cantidad
        cantidad_agregar = Decimal('500.00')
        
        resultado = self.stock.agregar_cantidad(
            cantidad_agregar,
            usuario=self.usuario,
            observaciones='Test agregar cantidad'
        )
        
        self.assertTrue(resultado)
        self.stock.refresh_from_db()
        self.assertEqual(self.stock.cantidad, cantidad_inicial + cantidad_agregar)
        
        # Verificar historial
        historial = HistorialStock.objects.filter(stock=self.stock).last()
        self.assertIsNotNone(historial)
        self.assertEqual(historial.tipo_movimiento, 'ENTRADA')
        self.assertEqual(historial.cantidad_movida, cantidad_agregar)
    
    def test_reducir_cantidad(self):
        """Test: Reducir cantidad del stock"""
        cantidad_inicial = self.stock.cantidad
        cantidad_reducir = Decimal('300.00')
        
        resultado = self.stock.reducir_cantidad(
            cantidad_reducir,
            usuario=self.usuario,
            observaciones='Test reducir cantidad'
        )
        
        self.assertTrue(resultado)
        self.stock.refresh_from_db()
        self.assertEqual(self.stock.cantidad, cantidad_inicial - cantidad_reducir)
        
        # Verificar historial
        historial = HistorialStock.objects.filter(stock=self.stock).last()
        self.assertIsNotNone(historial)
        self.assertEqual(historial.tipo_movimiento, 'SALIDA')
        self.assertEqual(historial.cantidad_movida, cantidad_reducir)
    
    def test_reducir_cantidad_insuficiente(self):
        """Test: No reducir si no hay stock suficiente"""
        cantidad_inicial = self.stock.cantidad
        cantidad_reducir = cantidad_inicial + Decimal('100.00')
        
        resultado = self.stock.reducir_cantidad(cantidad_reducir)
        
        self.assertFalse(resultado)
        self.stock.refresh_from_db()
        self.assertEqual(self.stock.cantidad, cantidad_inicial)


class StockDenominacionTest(TestCase):
    """Tests importantes para Stock por Denominaciones"""
    
    def setUp(self):
        self.tauser = Tauser.objects.create(
            nombre='Tauser Test',
            direccion='Av. Test 123',
            horario_atencion='Lun-Vie 9:00-18:00'
        )
        
        self.moneda = Moneda.objects.create(
            codigo='USD',
            nombre='Dólar Estadounidense',
            simbolo='$',
            es_activa=True,
            decimales=2
        )
        
        self.stock = Stock.objects.create(
            tauser=self.tauser,
            moneda=self.moneda,
            cantidad=Decimal('5000.00'),
            es_activo=True
        )
        
        self.denominacion = DenominacionMoneda.objects.create(
            moneda=self.moneda,
            valor=Decimal('100.00'),
            tipo='BILLETE',
            es_activa=True
        )
        
        self.stock_denominacion = StockDenominacion.objects.create(
            stock=self.stock,
            denominacion=self.denominacion,
            cantidad=50,
            es_activo=True
        )
        
        self.usuario = Usuario.objects.create_user(
            email='test@example.com',
            password='testpass123',
            nombre='Test',
            apellido='User',
            cedula='12345678',
            fecha_nacimiento='1990-01-01'
        )
    
    def test_agregar_cantidad_denominacion(self):
        """Test: Agregar cantidad por denominación (actualiza stock general)"""
        cantidad_inicial = self.stock_denominacion.cantidad
        stock_cantidad_inicial = self.stock.cantidad
        cantidad_agregar = 10
        
        resultado = self.stock_denominacion.agregar_cantidad(
            cantidad_agregar,
            usuario=self.usuario,
            observaciones='Test agregar billetes'
        )
        
        self.assertTrue(resultado)
        self.stock_denominacion.refresh_from_db()
        self.stock.refresh_from_db()
        
        # Verificar stock de denominación
        self.assertEqual(self.stock_denominacion.cantidad, cantidad_inicial + cantidad_agregar)
        
        # Verificar que se actualizó el stock general
        valor_agregado = cantidad_agregar * self.denominacion.valor
        self.assertEqual(self.stock.cantidad, stock_cantidad_inicial + valor_agregado)
    
    def test_reducir_cantidad_denominacion(self):
        """Test: Reducir cantidad por denominación (actualiza stock general)"""
        cantidad_inicial = self.stock_denominacion.cantidad
        stock_cantidad_inicial = self.stock.cantidad
        cantidad_reducir = 20
        
        resultado = self.stock_denominacion.reducir_cantidad(
            cantidad_reducir,
            usuario=self.usuario,
            observaciones='Test reducir billetes'
        )
        
        self.assertTrue(resultado)
        self.stock_denominacion.refresh_from_db()
        self.stock.refresh_from_db()
        
        # Verificar stock de denominación
        self.assertEqual(self.stock_denominacion.cantidad, cantidad_inicial - cantidad_reducir)
        
        # Verificar que se actualizó el stock general
        valor_reducido = cantidad_reducir * self.denominacion.valor
        self.assertEqual(self.stock.cantidad, stock_cantidad_inicial - valor_reducido)


class StockViewsTest(TestCase):
    """Tests importantes para vistas de Stock"""
    
    def setUp(self):
        self.client = Client()
        self.usuario = Usuario.objects.create_user(
            email='test@example.com',
            password='testpass123',
            nombre='Test',
            apellido='User',
            cedula='12345678',
            fecha_nacimiento='1990-01-01'
        )
        
        # Asignar permisos necesarios
        add_stock_perm = Permission.objects.get(codename='add_stock')
        self.usuario.user_permissions.add(add_stock_perm)
        
        self.tauser = Tauser.objects.create(
            nombre='Tauser Test',
            direccion='Av. Test 123',
            horario_atencion='Lun-Vie 9:00-18:00'
        )
        
        self.moneda = Moneda.objects.create(
            codigo='USD',
            nombre='Dólar Estadounidense',
            simbolo='$',
            es_activa=True,
            decimales=2
        )
        
        self.client.force_login(self.usuario)
    
    def test_cargar_stock_denominaciones(self):
        """Test: Cargar stock por denominaciones desde vista"""
        # Crear denominación
        denominacion = DenominacionMoneda.objects.create(
            moneda=self.moneda,
            valor=Decimal('100.00'),
            tipo='BILLETE',
            es_activa=True
        )
        
        data = {
            'moneda': self.moneda.pk,
            f'cantidad_{denominacion.pk}': 10
        }
        
        response = self.client.post(
            reverse('tauser:cargar_stock', args=[self.tauser.pk]),
            data
        )
        
        self.assertEqual(response.status_code, 302)  # Redirect después de cargar
        
        # Verificar que se creó el stock
        stock = Stock.objects.filter(tauser=self.tauser, moneda=self.moneda).first()
        self.assertIsNotNone(stock)
        self.assertEqual(stock.cantidad, Decimal('1000.00'))  # 10 billetes * $100
        
        # Verificar stock por denominación
        stock_denominacion = StockDenominacion.objects.filter(
            stock=stock,
            denominacion=denominacion
        ).first()
        self.assertIsNotNone(stock_denominacion)
        self.assertEqual(stock_denominacion.cantidad, 10)
        
        # Verificar historial
        historial = HistorialStockDenominacion.objects.filter(
            stock_denominacion=stock_denominacion
        ).first()
        self.assertIsNotNone(historial)
        self.assertEqual(historial.tipo_movimiento, 'ENTRADA')
        self.assertEqual(historial.cantidad_movida, 10)


class ConfirmarRecepcionDivisasDepositoTest(TestCase):
    """Valida que la confirmación de recepción registre el depósito en el simulador."""
    
    def setUp(self):
        self.client = Client()
        self.usuario = Usuario.objects.create_user(
            email='operador@example.com',
            password='operador123',
            nombre='Operador',
            apellido='Tauser',
            cedula='1231231',
            fecha_nacimiento='1990-01-01'
        )
        self.client.force_login(self.usuario)
        
        # Monedas
        self.moneda_extranjera = Moneda.objects.create(
            codigo='USD',
            nombre='Dólar Estadounidense',
            simbolo='$',
            es_activa=True,
            decimales=2
        )
        self.moneda_pyg = Moneda.objects.create(
            codigo='PYG',
            nombre='Guaraní',
            simbolo='₲',
            es_activa=True,
            decimales=0
        )
        
        # Denominación recibida
        self.denominacion = DenominacionMoneda.objects.create(
            moneda=self.moneda_extranjera,
            valor=Decimal('100.00'),
            tipo='BILLETE',
            es_activa=True
        )
        
        # Tauser
        self.tauser = Tauser.objects.create(
            nombre='Tauser Central',
            direccion='Av. Principal 123',
            horario_atencion='Lun-Vie 9:00-18:00',
            es_activo=True
        )
        
        # Métodos
        self.metodo_cobro = MetodoCobro.objects.create(
            nombre='Efectivo en Tauser',
            descripcion='Entrega de divisas en el tauser',
            comision=Decimal('0'),
            es_activo=True,
            requiere_retiro_fisico=True
        )
        self.metodo_cobro.monedas_permitidas.add(self.moneda_extranjera)
        
        self.metodo_pago = MetodoPago.objects.create(
            nombre='Billetera electrónica',
            descripcion='Depósito en billetera digital',
            comision=Decimal('1.00'),
            es_activo=True,
            requiere_retiro_fisico=False
        )
        self.metodo_pago.monedas_permitidas.add(self.moneda_pyg)
        
        # Tipos y estados
        self.tipo_venta = TipoOperacion.objects.create(
            codigo=TipoOperacion.VENTA,
            nombre='Venta de Divisas',
            descripcion='El cliente vende divisas y recibe PYG',
            activo=True
        )
        self.estado_pendiente = EstadoTransaccion.objects.create(
            codigo=EstadoTransaccion.PENDIENTE,
            nombre='Pendiente',
            descripcion='Pendiente de procesamiento',
            activo=True
        )
        self.estado_pagada = EstadoTransaccion.objects.create(
            codigo=EstadoTransaccion.PAGADA,
            nombre='Pagada',
            descripcion='Pagada',
            activo=True
        )
        
        # Cliente
        tipo_cliente = TipoCliente.objects.create(
            nombre='Corporativo',
            descripcion='Cliente corporativo',
            descuento=Decimal('0'),
            activo=True
        )
        self.cliente = Cliente.objects.create(
            nombre_comercial='Cliente Demo',
            ruc='1234567',
            direccion='Calle Falsa 123',
            correo_electronico='cliente@example.com',
            tipo_cliente=tipo_cliente
        )
        self.cliente.usuarios_asociados.add(self.usuario)
        
        # Transacción de venta pendiente
        self.transaccion = Transaccion.objects.create(
            cliente=self.cliente,
            usuario=self.usuario,
            tipo_operacion=self.tipo_venta,
            moneda_origen=self.moneda_extranjera,
            moneda_destino=self.moneda_pyg,
            monto_origen=Decimal('100.00'),
            monto_destino=Decimal('700000'),
            metodo_cobro=self.metodo_cobro,
            metodo_pago=self.metodo_pago,
            tasa_cambio=Decimal('7000'),
            estado=self.estado_pendiente,
            datos_metodo_pago={
                'metodo_pago_id': self.metodo_pago.id,
                'metodo_pago_nombre': self.metodo_pago.nombre,
                'campos': [
                    {
                        'id': 1,
                        'nombre': 'numero_telefono',
                        'etiqueta': 'Número de Teléfono',
                        'valor': '+595981234567',
                        'tipo': 'phone',
                    }
                ]
            }
        )
        # Garantizar que tengamos código de verificación
        self.transaccion.refresh_from_db()
    
    @patch('tauser.views.PasarelaService')
    def test_confirmar_recepcion_registra_deposito(self, mock_pasarela_cls):
        """El depósito se registra en el simulador cuando todo es correcto."""
        mock_service = mock_pasarela_cls.return_value
        mock_service.procesar_pago.return_value = {
            'success': True,
            'data': {
                'id_pago': 'deposit-123',
                'estado': 'exito',
                'fecha': '2025-01-01T00:00:00Z'
            }
        }
        
        payload = {
            'codigo_verificacion': self.transaccion.codigo_verificacion,
            'tauser_id': str(self.tauser.id),
            'total_recibido': '100.00',
            'denominaciones': json.dumps([{
                'denominacion_id': self.denominacion.id,
                'cantidad': 1,
                'valor': 100.0
            }])
        }
        
        response = self.client.post(reverse('tauser:confirmar_recepcion_divisas'), data=payload)
        self.assertEqual(response.status_code, 200)
        resultado = response.json()
        self.assertTrue(resultado['success'])
        self.assertIn('deposito', resultado)
        self.assertEqual(resultado['deposito']['estado'], 'exito')
        
        self.transaccion.refresh_from_db()
        self.assertEqual(self.transaccion.estado.codigo, EstadoTransaccion.PAGADA)
        self.assertEqual(self.transaccion.registro_deposito.get('estado'), 'exito')
        self.assertEqual(self.transaccion.registro_deposito.get('id_pago_externo'), 'deposit-123')
        mock_service.procesar_pago.assert_called_once()
