import json

from django.test import TestCase, Client, override_settings
from django.urls import reverse
from decimal import Decimal
from unittest.mock import patch

from .services import PasarelaService
from .models import PagoPasarela
from transacciones.models import Transaccion, TipoOperacion, EstadoTransaccion
from monedas.models import Moneda
from metodo_cobro.models import MetodoCobro
from metodo_pago.models import MetodoPago
from clientes.models import Cliente, TipoCliente
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
            ("Pago en cuenta bancaria", "transferencia"),
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


class PagoWebDepositoTestCase(TestCase):
    """Validaciones para el depósito automático después de pagos web."""

    def setUp(self):
        self.client = Client()
        self.usuario = Usuario.objects.create_user(
            email='operador-web@example.com',
            password='testpass123',
            nombre='Operador',
            apellido='Web',
            cedula='4455667',
            fecha_nacimiento='1990-01-01'
        )
        self.client.force_login(self.usuario)

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

        self.metodo_cobro = MetodoCobro.objects.create(
            nombre='Tarjeta de Crédito',
            descripcion='Cobro mediante tarjeta de crédito',
            comision=Decimal('2.50'),
            es_activo=True,
            requiere_retiro_fisico=False
        )
        self.metodo_cobro.monedas_permitidas.add(self.moneda_extranjera)

        self.metodo_pago = MetodoPago.objects.create(
            nombre='Pago en cuenta bancaria',
            descripcion='Depósito automático en cuenta bancaria',
            comision=Decimal('0.50'),
            es_activo=True,
            requiere_retiro_fisico=False
        )
        self.metodo_pago.monedas_permitidas.add(self.moneda_pyg)

        tipo_cliente = TipoCliente.objects.create(
            nombre='Corporativo Web',
            descripcion='Cliente corporativo para pruebas web',
            descuento=Decimal('0'),
            activo=True
        )
        self.cliente = Cliente.objects.create(
            nombre_comercial='Cliente Web Test',
            ruc='1555666',
            direccion='Calle Web 123',
            correo_electronico='cliente.web@example.com',
            tipo_cliente=tipo_cliente
        )
        self.cliente.usuarios_asociados.add(self.usuario)

        self.tipo_venta, _ = TipoOperacion.objects.get_or_create(
            codigo=TipoOperacion.VENTA,
            defaults={
                'nombre': 'Venta de Divisas',
                'descripcion': 'El cliente vende divisa extranjera y recibe PYG',
                'activo': True
            }
        )
        self.estado_pendiente, _ = EstadoTransaccion.objects.get_or_create(
            codigo=EstadoTransaccion.PENDIENTE,
            defaults={
                'nombre': 'Pendiente',
                'descripcion': 'Pendiente de pago',
                'activo': True
            }
        )
        self.estado_pagada, _ = EstadoTransaccion.objects.get_or_create(
            codigo=EstadoTransaccion.PAGADA,
            defaults={
                'nombre': 'Pagada',
                'descripcion': 'Pago confirmado',
                'activo': True
            }
        )

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
                    {'id': 1, 'nombre': 'numero_cuenta', 'valor': '123456789012'},
                    {'id': 2, 'nombre': 'banco', 'valor': 'Banco Web'},
                    {'id': 3, 'nombre': 'titular', 'valor': 'Cliente Web Test'},
                    {'id': 4, 'nombre': 'documento', 'valor': '1555666'},
                ]
            }
        )

    @patch('pagos.views.PasarelaService')
    @patch('pagos.views.registrar_deposito_en_simulador')
    def test_pago_tarjeta_credito_registra_deposito(self, mock_registrar_deposito, mock_pasarela_cls):
        mock_pasarela = mock_pasarela_cls.return_value
        mock_pasarela.procesar_pago.return_value = {
            'success': True,
            'data': {
                'id_pago': 'pay-test-123',
                'estado': 'exito'
            }
        }
        mock_pasarela._mapear_metodo.return_value = 'tarjeta_credito_local'

        mock_registrar_deposito.return_value = {
            'estado': 'exito',
            'id_pago_externo': 'dep-test-987',
            'metadata': {}
        }

        url = reverse('pagos:pago_tarjeta_credito_local', args=[self.transaccion.id_transaccion])
        data = {
            'tipo_tarjeta': 'panal',
            'numero_tarjeta': '4111 1111 1111 1111',
            'nombre_titular': 'CLIENTE WEB TEST',
            'fecha_vencimiento': '12/30',
            'codigo_seguridad': '123',
            'cuotas': '1'
        }

        response = self.client.post(url, data)
        info_error = (
            response.context['form'].errors if response.context
            else f"status={response.status_code}, tipo={type(response)}, templates={getattr(response, 'templates', None)}"
        )
        self.assertEqual(response.status_code, 302, info_error)

        self.transaccion.refresh_from_db()
        self.assertEqual(self.transaccion.estado.codigo, EstadoTransaccion.PAGADA)
        self.assertEqual(self.transaccion.registro_deposito.get('estado'), 'exito')

        mock_registrar_deposito.assert_called_once()
        args, kwargs = mock_registrar_deposito.call_args
        self.assertEqual(args[0], self.transaccion)
        self.assertEqual(kwargs.get('usuario_email'), self.usuario.email)
        self.assertEqual(kwargs.get('extra_payload'), {'origen': 'pago_web'})

    @patch('pagos.views._registrar_deposito_automatico')
    @patch('pagos.views.StripeService')
    def test_stripe_success_registra_deposito(self, mock_stripe_cls, mock_registrar_deposito):
        session_id = 'sess_test_123'
        PagoPasarela.objects.create(
            transaccion=self.transaccion,
            id_pago_externo=session_id,
            monto=Decimal('700000'),
            metodo_pasarela='stripe',
            moneda=self.moneda_pyg.codigo,
            estado='pendiente',
            datos_pago={'session_id': session_id},
            respuesta_pasarela={}
        )

        stripe_instance = mock_stripe_cls.return_value
        stripe_instance.recuperar_sesion.return_value = {
            'success': True,
            'session': {'id': session_id},
            'payment_status': 'paid',
            'payment_intent': 'pi_test_123'
        }

        response = self.client.get(reverse('pagos:stripe_success'), {'session_id': session_id})
        self.assertEqual(response.status_code, 302)

        mock_registrar_deposito.assert_called_once()
        call_args = mock_registrar_deposito.call_args
        self.assertEqual(call_args.args[0].id_transaccion, self.transaccion.id_transaccion)
        self.assertEqual(call_args.kwargs.get('origen'), 'stripe_success')
        self.assertEqual(call_args.kwargs.get('usuario_email'), self.usuario.email)
        self.assertIsNotNone(call_args.kwargs.get('request'))

        self.transaccion.refresh_from_db()
        self.assertEqual(self.transaccion.estado.codigo, EstadoTransaccion.PAGADA)

    @override_settings(DEBUG=True, STRIPE_WEBHOOK_SECRET='')
    @patch('pagos.views._registrar_deposito_automatico')
    def test_stripe_webhook_registra_deposito(self, mock_registrar_deposito):
        session_id = 'sess_webhook_123'
        PagoPasarela.objects.create(
            transaccion=self.transaccion,
            id_pago_externo=session_id,
            monto=Decimal('700000'),
            metodo_pasarela='stripe',
            moneda=self.moneda_pyg.codigo,
            estado='pendiente',
            datos_pago={'session_id': session_id},
            respuesta_pasarela={}
        )

        evento = {
            'type': 'checkout.session.completed',
            'data': {
                'object': {
                    'id': session_id,
                    'payment_status': 'paid'
                }
            }
        }

        response = self.client.post(
            reverse('pagos:stripe_webhook'),
            data=json.dumps(evento),
            content_type='application/json'
        )

        self.assertEqual(response.status_code, 200)
        mock_registrar_deposito.assert_called_once()
        call_kwargs = mock_registrar_deposito.call_args.kwargs
        self.assertEqual(call_kwargs.get('origen'), 'stripe_webhook')
        self.assertEqual(call_kwargs.get('usuario_email'), self.transaccion.usuario.email)
        self.assertIsNone(call_kwargs.get('request'))

        self.transaccion.refresh_from_db()
        self.assertEqual(self.transaccion.estado.codigo, EstadoTransaccion.PAGADA)
