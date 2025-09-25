from django.core.management.base import BaseCommand
from django.db import transaction
from transacciones.models import TipoOperacion, EstadoTransaccion


class Command(BaseCommand):
    help = 'Crea los datos iniciales para tipos de operación y estados de transacción'

    def handle(self, *args, **options):
        self.stdout.write('Creando datos iniciales para transacciones...')
        
        with transaction.atomic():
            # Crear tipos de operación
            self.crear_tipos_operacion()
            
            # Crear estados de transacción
            self.crear_estados_transaccion()
        
        self.stdout.write(
            self.style.SUCCESS('Datos iniciales creados exitosamente')
        )

    def crear_tipos_operacion(self):
        """Crea los tipos de operación iniciales"""
        tipos = [
            {
                'codigo': TipoOperacion.COMPRA,
                'nombre': 'Compra de Divisas',
                'descripcion': 'Operación de compra de moneda extranjera',
                'activo': True
            },
            {
                'codigo': TipoOperacion.VENTA,
                'nombre': 'Venta de Divisas',
                'descripcion': 'Operación de venta de moneda extranjera',
                'activo': True
            }
        ]
        
        for tipo_data in tipos:
            tipo, created = TipoOperacion.objects.get_or_create(
                codigo=tipo_data['codigo'],
                defaults=tipo_data
            )
            if created:
                self.stdout.write(f'  ✓ Creado tipo de operación: {tipo.nombre}')
            else:
                self.stdout.write(f'  - Ya existe tipo de operación: {tipo.nombre}')

    def crear_estados_transaccion(self):
        """Crea los estados de transacción iniciales"""
        estados = [
            {
                'codigo': EstadoTransaccion.PENDIENTE,
                'nombre': 'Pendiente de Pago',
                'descripcion': 'La transacción está esperando el pago del cliente',
                'es_final': False,
                'activo': True
            },
            {
                'codigo': EstadoTransaccion.PAGADA,
                'nombre': 'Pagada',
                'descripcion': 'La transacción ha sido pagada y completada exitosamente',
                'es_final': True,
                'activo': True
            },
            {
                'codigo': EstadoTransaccion.CANCELADA,
                'nombre': 'Cancelada',
                'descripcion': 'La transacción fue cancelada antes de completarse',
                'es_final': True,
                'activo': True
            },
            {
                'codigo': EstadoTransaccion.ANULADA,
                'nombre': 'Anulada',
                'descripcion': 'La transacción fue anulada después de haberse completado',
                'es_final': True,
                'activo': True
            }
        ]
        
        for estado_data in estados:
            estado, created = EstadoTransaccion.objects.get_or_create(
                codigo=estado_data['codigo'],
                defaults=estado_data
            )
            if created:
                self.stdout.write(f'  ✓ Creado estado: {estado.nombre}')
            else:
                self.stdout.write(f'  - Ya existe estado: {estado.nombre}')