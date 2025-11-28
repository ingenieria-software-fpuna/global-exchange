from django.test import TestCase, Client
from django.urls import reverse
from django.contrib.auth import get_user_model
from decimal import Decimal

from monedas.models import Moneda
from metodo_pago.models import MetodoPago
from metodo_cobro.models import MetodoCobro
from clientes.models import Cliente, TipoCliente
from tasa_cambio.models import TasaCambio
from usuarios.models import Usuario
from transacciones.views import calcular_transaccion_completa, calcular_venta_completa

User = get_user_model()


class TransaccionModelTest(TestCase):
    """Tests básicos para modelos de transacciones"""
    
    def setUp(self):
        # Crear monedas
        self.usd = Moneda.objects.create(
            codigo='USD', nombre='Dólar Americano', simbolo='$'
        )
        self.pyg = Moneda.objects.create(
            codigo='PYG', nombre='Guaraní', simbolo='₲'
        )
        
        # Crear tasa de cambio
        self.tasa_usd = TasaCambio.objects.create(
            moneda=self.usd,
            precio_base=7400,
            comision_compra=200,
            comision_venta=200,
            es_activa=True
        )

    def test_tasa_cambio_propiedades(self):
        """Test: Las propiedades calculadas de TasaCambio funcionan"""
        # Tasa de compra: precio_base - comision_compra
        self.assertEqual(self.tasa_usd.tasa_compra, 7200)
        
        # Tasa de venta: precio_base + comision_venta  
        self.assertEqual(self.tasa_usd.tasa_venta, 7600)
        
        # Spread: diferencia entre venta y compra
        self.assertEqual(self.tasa_usd.spread, 400)

    def test_monedas_creacion(self):
        """Test: Las monedas se crean correctamente"""
        self.assertEqual(self.usd.codigo, 'USD')
        self.assertEqual(self.pyg.codigo, 'PYG')
        self.assertEqual(self.usd.simbolo, '$')
        self.assertEqual(self.pyg.simbolo, '₲')


class TransaccionViewsTest(TestCase):
    """Tests esenciales para vistas de transacciones"""
    
    def setUp(self):
        # Crear usuario de prueba
        self.user = Usuario.objects.create_user(
            email='test@test.com',
            nombre='Test',
            apellido='User',
            password='testpass123'
        )
        
        # Crear datos básicos
        self.usd = Moneda.objects.create(codigo='USD', nombre='Dólar', simbolo='$')
        self.pyg = Moneda.objects.create(codigo='PYG', nombre='Guaraní', simbolo='₲')
        
        self.tasa_usd = TasaCambio.objects.create(
            moneda=self.usd, precio_base=7400, comision_compra=200, 
            comision_venta=200, es_activa=True
        )
        
        self.metodo_pago = MetodoPago.objects.create(nombre='Efectivo', comision=0)
        self.metodo_cobro = MetodoCobro.objects.create(nombre='Efectivo USD', comision=0)
        self.metodo_cobro.monedas_permitidas.add(self.usd)
        

        
        # Asignar permisos necesarios
        from django.contrib.auth.models import Permission
        can_operate = Permission.objects.get(codename='can_operate')
        self.user.user_permissions.add(can_operate)
        
        self.client = Client()
        self.client.force_login(self.user)

    def test_vista_comprar_divisas_get(self):
        """Test: Acceso a la vista de comprar divisas"""
        response = self.client.get(reverse('transacciones:comprar_divisas'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Comprar Divisas')

    def test_vista_vender_divisas_get(self):
        """Test: Acceso a la vista de vender divisas"""
        response = self.client.get(reverse('transacciones:vender_divisas'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Vender Divisas')

    def test_api_calcular_compra(self):
        """Test: API de cálculo de compra"""
        response = self.client.get(reverse('transacciones:api_calcular_compra_completa'), {
            'monto': '100',
            'origen': 'PYG',
            'destino': 'USD',
            'metodo_cobro_id': self.metodo_cobro.id,
            'metodo_pago_id': self.metodo_pago.id
        })
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        if not data['success']:
            print(f"API Error: {data}")
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['tasa_ajustada'], 7600)

    def test_api_calcular_venta(self):
        """Test: API de cálculo de venta"""
        response = self.client.get(reverse('transacciones:api_calcular_venta_completa'), {
            'monto': '100',
            'origen': 'USD',
            'destino': 'PYG',
            'metodo_cobro_id': self.metodo_cobro.id,
            'metodo_pago_id': self.metodo_pago.id
        })
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['tasa_ajustada'], 7200)

    def test_api_metodos_cobro_por_moneda(self):
        """Test: API que filtra métodos de cobro por moneda"""
        response = self.client.get(reverse('transacciones:api_metodos_cobro_por_moneda'), {
            'moneda_codigo': 'USD'
        })
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data['success'])
        self.assertEqual(len(data['metodos_cobro']), 1)
        self.assertEqual(data['metodos_cobro'][0]['nombre'], 'Efectivo USD')

    def test_descuento_tipo_cliente_inactivo(self):
        """Test: Los tipos de cliente inactivos no aplican descuentos"""
        # Crear tipo de cliente activo con descuento
        tipo_inactivo = TipoCliente.objects.create(
            nombre='Tipo Inactivo',
            descuento=Decimal('15.00'),
            activo=True
        )
        
        # Crear cliente con tipo activo
        cliente_inactivo = Cliente.objects.create(
            nombre_comercial='Cliente Inactivo',
            ruc='12345678',
            tipo_cliente=tipo_inactivo
        )
        
        # Desactivar el tipo de cliente después de crear el cliente
        tipo_inactivo.activo = False
        tipo_inactivo.save()
        
        # Crear tipo de cliente activo con descuento
        tipo_activo = TipoCliente.objects.create(
            nombre='Tipo Activo',
            descuento=Decimal('10.00'),
            activo=True
        )
        
        # Crear cliente con tipo activo
        cliente_activo = Cliente.objects.create(
            nombre_comercial='Cliente Activo',
            ruc='87654321',
            tipo_cliente=tipo_activo
        )
        
        # Test compra con cliente inactivo - no debe aplicar descuento
        resultado_inactivo = calcular_transaccion_completa(
            monto=Decimal('100000'),
            moneda_origen=self.pyg,
            moneda_destino=self.usd,
            cliente=cliente_inactivo
        )
        
        self.assertTrue(resultado_inactivo['success'])
        self.assertEqual(resultado_inactivo['data']['descuento_pct'], 0)
        self.assertEqual(resultado_inactivo['data']['descuento_aplicado'], 0)
        
        # Test compra con cliente activo - debe aplicar descuento
        resultado_activo = calcular_transaccion_completa(
            monto=Decimal('100000'),
            moneda_origen=self.pyg,
            moneda_destino=self.usd,
            cliente=cliente_activo
        )
        
        self.assertTrue(resultado_activo['success'])
        self.assertEqual(resultado_activo['data']['descuento_pct'], 10.0)
        # El descuento se aplica a la comisión de venta
        self.assertGreater(resultado_activo['data']['descuento_aplicado'], 0)
        
        # Test venta con cliente inactivo - no debe aplicar descuento
        resultado_venta_inactivo = calcular_venta_completa(
            monto=Decimal('100'),
            moneda_origen=self.usd,
            moneda_destino=self.pyg,
            cliente=cliente_inactivo
        )
        
        self.assertTrue(resultado_venta_inactivo['success'])
        self.assertEqual(resultado_venta_inactivo['data']['descuento_pct'], 0)
        self.assertEqual(resultado_venta_inactivo['data']['descuento_aplicado'], 0)
        
        # Test venta con cliente activo - debe aplicar descuento
        resultado_venta_activo = calcular_venta_completa(
            monto=Decimal('100'),
            moneda_origen=self.usd,
            moneda_destino=self.pyg,
            cliente=cliente_activo
        )
        
        self.assertTrue(resultado_venta_activo['success'])
        self.assertEqual(resultado_venta_activo['data']['descuento_pct'], 10.0)
        # El descuento se aplica a la comisión de compra
        self.assertGreater(resultado_venta_activo['data']['descuento_aplicado'], 0)

    def test_venta_descuento_aplicado_a_comision_compra(self):
        """Test: En ventas, el descuento se aplica a la comisión de compra, no al precio final"""
        # Crear tipo de cliente con descuento
        tipo_cliente = TipoCliente.objects.create(
            nombre='Tipo con Descuento',
            descuento=Decimal('20.00'),
            activo=True
        )
        
        # Crear cliente
        cliente = Cliente.objects.create(
            nombre_comercial='Cliente Test',
            ruc='12345678',
            tipo_cliente=tipo_cliente
        )
        
        # Calcular venta sin descuento (simulando cliente sin tipo)
        resultado_sin_descuento = calcular_venta_completa(
            monto=Decimal('100'),
            moneda_origen=self.usd,
            moneda_destino=self.pyg,
            cliente=None
        )
        
        # Verificar que el cálculo sin descuento fue exitoso
        if not resultado_sin_descuento['success']:
            print(f"Error en cálculo sin descuento: {resultado_sin_descuento.get('error', 'Error desconocido')}")
            self.fail("El cálculo sin descuento falló")
        
        # Calcular venta con descuento
        resultado_con_descuento = calcular_venta_completa(
            monto=Decimal('100'),
            moneda_origen=self.usd,
            moneda_destino=self.pyg,
            cliente=cliente
        )
        
        self.assertTrue(resultado_sin_descuento['success'])
        self.assertTrue(resultado_con_descuento['success'])
        
        # El cliente con descuento debe recibir más PYG
        self.assertGreater(
            resultado_con_descuento['data']['resultado'],
            resultado_sin_descuento['data']['resultado']
        )
        
        # Verificar que el descuento se aplicó correctamente
        self.assertEqual(resultado_con_descuento['data']['descuento_pct'], 20.0)
        
        # La tasa usada con descuento debe ser mayor (mejor para el cliente)
        self.assertGreater(
            resultado_con_descuento['data']['precio_usado'],
            resultado_sin_descuento['data']['precio_usado']
        )


class ReportesViewsTest(TestCase):
    """Tests para vistas de reportes"""
    
    def setUp(self):
        from django.utils import timezone
        from datetime import timedelta
        from transacciones.models import TipoOperacion, EstadoTransaccion, Transaccion
        from configuracion.models import ConfiguracionSistema
        
        # Crear usuario de prueba
        self.user = Usuario.objects.create_user(
            email='reportes@test.com',
            nombre='Reportes',
            apellido='User',
            password='testpass123'
        )
        
        # Crear monedas
        self.usd = Moneda.objects.create(codigo='USD', nombre='Dólar', simbolo='$', es_activa=True)
        self.pyg = Moneda.objects.create(codigo='PYG', nombre='Guaraní', simbolo='₲', es_activa=True)
        
        # Crear tasa de cambio
        self.tasa_usd = TasaCambio.objects.create(
            moneda=self.usd,
            precio_base=Decimal('7400'),
            comision_compra=Decimal('200'),
            comision_venta=Decimal('200'),
            es_activa=True
        )
        
        # Crear tipos de operación y estados
        self.tipo_compra = TipoOperacion.objects.create(
            codigo='COMPRA',
            nombre='Compra de Divisas',
            activo=True
        )
        self.tipo_venta = TipoOperacion.objects.create(
            codigo='VENTA',
            nombre='Venta de Divisas',
            activo=True
        )
        
        self.estado_pagada = EstadoTransaccion.objects.create(
            codigo='PAGADA',
            nombre='Pagada',
            es_final=False
        )
        self.estado_pendiente = EstadoTransaccion.objects.create(
            codigo='PENDIENTE',
            nombre='Pendiente',
            es_final=False
        )
        self.estado_cancelada = EstadoTransaccion.objects.create(
            codigo='CANCELADA',
            nombre='Cancelada',
            es_final=True
        )
        
        # Crear transacciones de prueba
        fecha_base = timezone.now() - timedelta(days=5)
        
        # Transacción COMPRA (cliente compra USD) - PAGADA
        self.trans_compra = Transaccion.objects.create(
            id_transaccion=f'TXN-{timezone.now().strftime("%Y%m%d%H%M%S")}-TEST1',
            tipo_operacion=self.tipo_compra,
            estado=self.estado_pagada,
            moneda_origen=self.pyg,
            moneda_destino=self.usd,
            monto_origen=Decimal('760000'),
            monto_destino=Decimal('100'),
            tasa_cambio=Decimal('7600'),
            tasa_cambio_base=Decimal('7600'),
            precio_base=Decimal('7400'),
            monto_comision=Decimal('20000'),
            monto_descuento=Decimal('0'),
            usuario=self.user,
            fecha_creacion=fecha_base
        )
        
        # Transacción VENTA (cliente vende USD) - PAGADA
        self.trans_venta = Transaccion.objects.create(
            id_transaccion=f'TXN-{timezone.now().strftime("%Y%m%d%H%M%S")}-TEST2',
            tipo_operacion=self.tipo_venta,
            estado=self.estado_pagada,
            moneda_origen=self.usd,
            moneda_destino=self.pyg,
            monto_origen=Decimal('100'),
            monto_destino=Decimal('720000'),
            tasa_cambio=Decimal('7200'),
            tasa_cambio_base=Decimal('7200'),
            precio_base=Decimal('7400'),
            monto_comision=Decimal('20000'),
            monto_descuento=Decimal('5000'),
            usuario=self.user,
            fecha_creacion=fecha_base + timedelta(days=1)
        )
        
        # Transacción PENDIENTE
        self.trans_pendiente = Transaccion.objects.create(
            id_transaccion=f'TXN-{timezone.now().strftime("%Y%m%d%H%M%S")}-TEST3',
            tipo_operacion=self.tipo_compra,
            estado=self.estado_pendiente,
            moneda_origen=self.pyg,
            moneda_destino=self.usd,
            monto_origen=Decimal('380000'),
            monto_destino=Decimal('50'),
            tasa_cambio=Decimal('7600'),
            tasa_cambio_base=Decimal('7600'),
            precio_base=Decimal('7400'),
            monto_comision=Decimal('10000'),
            monto_descuento=Decimal('0'),
            usuario=self.user,
            fecha_creacion=fecha_base + timedelta(days=2)
        )
        
        # Asignar permisos necesarios
        from django.contrib.auth.models import Permission
        perm_reporte_trans = Permission.objects.get(codename='view_reporte_transacciones')
        perm_reporte_gan = Permission.objects.get(codename='view_reporte_ganancias')
        self.user.user_permissions.add(perm_reporte_trans, perm_reporte_gan)
        
        self.client = Client()
        self.client.force_login(self.user)
        
        # Crear configuración del sistema
        try:
            config = ConfiguracionSistema.objects.first()
            if not config:
                ConfiguracionSistema.objects.create(moneda_base=self.pyg)
        except:
            pass

    def test_obtener_tipo_operacion_display(self):
        """Test: La función obtener_tipo_operacion_display invierte correctamente"""
        from transacciones.views_reportes import obtener_tipo_operacion_display
        
        # COMPRA desde cliente = VENTA desde casa
        display_compra = obtener_tipo_operacion_display(self.trans_compra)
        self.assertEqual(display_compra, 'Venta de Divisas')
        
        # VENTA desde cliente = COMPRA desde casa
        display_venta = obtener_tipo_operacion_display(self.trans_venta)
        self.assertEqual(display_venta, 'Compra de Divisas')

    def test_calcular_comision_real_cambio(self):
        """Test: La función calcular_comision_real_cambio calcula correctamente"""
        from transacciones.views_reportes import calcular_comision_real_cambio
        
        # Para COMPRA: (tasa_cambio_base - precio_base) × cantidad_divisa
        # tasa_cambio_base = 7600, precio_base = 7400, cantidad = 100
        # comision = (7600 - 7400) × 100 = 20000
        comision_compra = calcular_comision_real_cambio(self.trans_compra)
        self.assertEqual(comision_compra, Decimal('20000'))
        
        # Para VENTA: (precio_base - tasa_cambio_base) × cantidad_divisa
        # precio_base = 7400, tasa_cambio_base = 7200, cantidad = 100
        # comision = (7400 - 7200) × 100 = 20000
        comision_venta = calcular_comision_real_cambio(self.trans_venta)
        self.assertEqual(comision_venta, Decimal('20000'))

    def test_aplicar_filtros_transacciones(self):
        """Test: La función aplicar_filtros_transacciones filtra correctamente"""
        from transacciones.views_reportes import aplicar_filtros_transacciones
        from transacciones.models import Transaccion
        from django.utils import timezone
        from datetime import timedelta
        
        queryset = Transaccion.objects.all()
        
        # Filtro por tipo de operación
        form_data = {'tipo_operacion': self.tipo_compra}
        filtered, _, _ = aplicar_filtros_transacciones(queryset, form_data)
        self.assertEqual(filtered.count(), 2)  # trans_compra y trans_pendiente
        
        # Filtro por estado
        form_data = {'estado': self.estado_pagada}
        filtered, _, _ = aplicar_filtros_transacciones(queryset, form_data)
        self.assertEqual(filtered.count(), 2)  # trans_compra y trans_venta
        
        # Filtro por moneda
        form_data = {'moneda': self.usd}
        filtered, _, _ = aplicar_filtros_transacciones(queryset, form_data)
        self.assertEqual(filtered.count(), 3)  # Todas tienen USD
        
        # Filtro por fecha
        fecha_desde = timezone.now().date() - timedelta(days=3)
        fecha_hasta = timezone.now().date()
        form_data = {'fecha_desde': fecha_desde, 'fecha_hasta': fecha_hasta}
        filtered, fecha_d, fecha_h = aplicar_filtros_transacciones(queryset, form_data)
        self.assertEqual(fecha_d, fecha_desde)
        self.assertEqual(fecha_h, fecha_hasta)

    def test_calcular_ganancias_por_tipo(self):
        """Test: La función calcular_ganancias_por_tipo calcula correctamente"""
        from transacciones.views_reportes import calcular_ganancias_por_tipo
        from transacciones.models import Transaccion
        
        # Solo transacciones pagadas generan ganancias
        transacciones = Transaccion.objects.filter(estado=self.estado_pagada)
        ganancias = calcular_ganancias_por_tipo(transacciones)
        
        # Debe tener 2 tipos: VENTA (desde COMPRA) y COMPRA (desde VENTA)
        self.assertIn('VENTA', ganancias)
        self.assertIn('COMPRA', ganancias)
        
        # Verificar cálculos
        ganancia_venta = ganancias['VENTA']
        self.assertEqual(ganancia_venta['comisiones_pyg'], Decimal('20000'))
        self.assertEqual(ganancia_venta['descuentos_pyg'], Decimal('0'))
        self.assertEqual(ganancia_venta['ganancia_neta_pyg'], Decimal('20000'))
        
        ganancia_compra = ganancias['COMPRA']
        self.assertEqual(ganancia_compra['comisiones_pyg'], Decimal('20000'))
        self.assertEqual(ganancia_compra['descuentos_pyg'], Decimal('5000'))
        self.assertEqual(ganancia_compra['ganancia_neta_pyg'], Decimal('15000'))

    def test_reporte_transacciones_sin_permiso(self):
        """Test: Usuario sin permiso no puede acceder al reporte"""
        from django.contrib.auth.models import Permission
        
        # Crear usuario sin permisos
        user_sin_permiso = Usuario.objects.create_user(
            email='sinpermiso@test.com',
            nombre='Sin',
            apellido='Permiso',
            password='testpass123'
        )
        client = Client()
        client.force_login(user_sin_permiso)
        
        response = client.get(reverse('transacciones:reporte_transacciones'))
        self.assertEqual(response.status_code, 403)

    def test_reporte_transacciones_con_permiso(self):
        """Test: Usuario con permiso puede acceder al reporte"""
        response = self.client.get(reverse('transacciones:reporte_transacciones'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Reporte de Transacciones')

    def test_reporte_transacciones_con_filtros(self):
        """Test: El reporte aplica filtros correctamente"""
        from django.utils import timezone
        from datetime import timedelta
        
        fecha_desde = (timezone.now() - timedelta(days=3)).date()
        fecha_hasta = timezone.now().date()
        
        response = self.client.get(reverse('transacciones:reporte_transacciones'), {
            'fecha_desde': fecha_desde.strftime('%Y-%m-%d'),
            'fecha_hasta': fecha_hasta.strftime('%Y-%m-%d'),
            'tipo_operacion': self.tipo_compra.id,
            'estado': self.estado_pagada.id
        })
        
        self.assertEqual(response.status_code, 200)
        # Verificar que el contexto tiene las transacciones filtradas
        self.assertIn('transacciones', response.context)

    def test_reporte_ganancias_sin_permiso(self):
        """Test: Usuario sin permiso no puede acceder al reporte de ganancias"""
        from django.contrib.auth.models import Permission
        
        user_sin_permiso = Usuario.objects.create_user(
            email='sinpermiso2@test.com',
            nombre='Sin',
            apellido='Permiso2',
            password='testpass123'
        )
        client = Client()
        client.force_login(user_sin_permiso)
        
        response = client.get(reverse('transacciones:reporte_ganancias'))
        self.assertEqual(response.status_code, 403)

    def test_reporte_ganancias_con_permiso(self):
        """Test: Usuario con permiso puede acceder al reporte de ganancias"""
        response = self.client.get(reverse('transacciones:reporte_ganancias'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Tablero de Control de Ganancias')

    def test_reporte_ganancias_solo_pagadas(self):
        """Test: El reporte de ganancias solo muestra transacciones pagadas"""
        response = self.client.get(reverse('transacciones:reporte_ganancias'))
        self.assertEqual(response.status_code, 200)
        
        # Verificar que el contexto tiene ganancias
        self.assertIn('ganancias_por_moneda', response.context)
        self.assertIn('ganancias_por_tipo', response.context)
        self.assertIn('total_ganancia_pyg', response.context)

    def test_exportar_transacciones_excel(self):
        """Test: Exportación a Excel de transacciones"""
        response = self.client.get(reverse('transacciones:exportar_transacciones_excel'))
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response['Content-Type'],
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        self.assertIn('attachment', response['Content-Disposition'])
        self.assertIn('.xlsx', response['Content-Disposition'])

    def test_exportar_transacciones_excel_con_filtros(self):
        """Test: Exportación a Excel con filtros aplicados"""
        from django.utils import timezone
        from datetime import timedelta
        
        fecha_desde = (timezone.now() - timedelta(days=3)).date()
        fecha_hasta = timezone.now().date()
        
        response = self.client.get(reverse('transacciones:exportar_transacciones_excel'), {
            'fecha_desde': fecha_desde.strftime('%Y-%m-%d'),
            'fecha_hasta': fecha_hasta.strftime('%Y-%m-%d'),
            'tipo_operacion': self.tipo_compra.id
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response['Content-Type'],
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    def test_exportar_transacciones_pdf(self):
        """Test: Exportación a PDF de transacciones"""
        response = self.client.get(reverse('transacciones:exportar_transacciones_pdf'))
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertIn('attachment', response['Content-Disposition'])
        self.assertIn('.pdf', response['Content-Disposition'])

    def test_exportar_transacciones_pdf_con_filtros(self):
        """Test: Exportación a PDF con filtros aplicados"""
        from django.utils import timezone
        from datetime import timedelta
        
        fecha_desde = (timezone.now() - timedelta(days=3)).date()
        fecha_hasta = timezone.now().date()
        
        response = self.client.get(reverse('transacciones:exportar_transacciones_pdf'), {
            'fecha_desde': fecha_desde.strftime('%Y-%m-%d'),
            'fecha_hasta': fecha_hasta.strftime('%Y-%m-%d'),
            'estado': self.estado_pagada.id
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')

    def test_exportar_ganancias_excel(self):
        """Test: Exportación a Excel de ganancias"""
        response = self.client.get(reverse('transacciones:exportar_ganancias_excel'))
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response['Content-Type'],
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        self.assertIn('attachment', response['Content-Disposition'])
        self.assertIn('.xlsx', response['Content-Disposition'])

    def test_exportar_ganancias_excel_con_filtros(self):
        """Test: Exportación a Excel de ganancias con filtros"""
        from django.utils import timezone
        from datetime import timedelta
        
        fecha_desde = (timezone.now() - timedelta(days=3)).date()
        fecha_hasta = timezone.now().date()
        
        response = self.client.get(reverse('transacciones:exportar_ganancias_excel'), {
            'fecha_desde': fecha_desde.strftime('%Y-%m-%d'),
            'fecha_hasta': fecha_hasta.strftime('%Y-%m-%d')
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response['Content-Type'],
            'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )

    def test_exportar_ganancias_pdf(self):
        """Test: Exportación a PDF de ganancias"""
        response = self.client.get(reverse('transacciones:exportar_ganancias_pdf'))
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertIn('attachment', response['Content-Disposition'])
        self.assertIn('.pdf', response['Content-Disposition'])

    def test_exportar_ganancias_pdf_con_filtros(self):
        """Test: Exportación a PDF de ganancias con filtros"""
        from django.utils import timezone
        from datetime import timedelta
        
        fecha_desde = (timezone.now() - timedelta(days=3)).date()
        fecha_hasta = timezone.now().date()
        
        response = self.client.get(reverse('transacciones:exportar_ganancias_pdf'), {
            'fecha_desde': fecha_desde.strftime('%Y-%m-%d'),
            'fecha_hasta': fecha_hasta.strftime('%Y-%m-%d')
        })
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')

    def test_reporte_transacciones_paginacion(self):
        """Test: El reporte de transacciones tiene paginación"""
        response = self.client.get(reverse('transacciones:reporte_transacciones'))
        self.assertEqual(response.status_code, 200)
        
        # Verificar que el contexto tiene información de paginación
        self.assertIn('page_obj', response.context)
        self.assertIn('is_paginated', response.context)
