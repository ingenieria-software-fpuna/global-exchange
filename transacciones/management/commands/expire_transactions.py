from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction
from transacciones.models import Transaccion, EstadoTransaccion


class Command(BaseCommand):
    help = 'Cancela automáticamente las transacciones pendientes que han expirado'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Muestra qué transacciones serían canceladas sin realizar cambios',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write('Modo DRY RUN - No se realizarán cambios')
        
        # Obtener transacciones pendientes que han expirado
        transacciones_expiradas = Transaccion.objects.filter(
            estado__codigo=EstadoTransaccion.PENDIENTE,
            fecha_expiracion__lt=timezone.now()
        ).select_related('estado', 'moneda_origen', 'moneda_destino')
        
        total_encontradas = transacciones_expiradas.count()
        
        if total_encontradas == 0:
            self.stdout.write(
                self.style.SUCCESS('No se encontraron transacciones expiradas para cancelar.')
            )
            return
        
        self.stdout.write(f'Encontradas {total_encontradas} transacciones expiradas:')
        
        canceladas = 0
        errores = 0
        
        for transaccion in transacciones_expiradas:
            tiempo_expirado = timezone.now() - transaccion.fecha_expiracion
            minutos_expirado = int(tiempo_expirado.total_seconds() / 60)
            
            self.stdout.write(
                f'  - {transaccion.id_transaccion}: '
                f'{transaccion.moneda_origen.simbolo}{transaccion.monto_origen} '
                f'({transaccion.moneda_origen.codigo} → {transaccion.moneda_destino.codigo}) '
                f'- Expiró hace {minutos_expirado} minutos'
            )
            
            if not dry_run:
                try:
                    with transaction.atomic():
                        resultado = transaccion.cancelar_por_expiracion()
                        if resultado:
                            canceladas += 1
                            self.stdout.write(
                                self.style.SUCCESS(f'    ✓ Cancelada exitosamente')
                            )
                        else:
                            self.stdout.write(
                                self.style.WARNING(f'    ⚠ No se pudo cancelar (estado: {transaccion.estado.codigo})')
                            )
                except Exception as e:
                    errores += 1
                    self.stdout.write(
                        self.style.ERROR(f'    ✗ Error al cancelar: {str(e)}')
                    )
        
        if not dry_run:
            self.stdout.write('')
            self.stdout.write(f'Resumen:')
            self.stdout.write(f'  - Transacciones encontradas: {total_encontradas}')
            self.stdout.write(f'  - Canceladas exitosamente: {canceladas}')
            if errores > 0:
                self.stdout.write(f'  - Errores: {errores}')
            
            if canceladas > 0:
                self.stdout.write(
                    self.style.SUCCESS(f'Proceso completado. {canceladas} transacciones fueron canceladas.')
                )
            else:
                self.stdout.write(
                    self.style.WARNING('No se cancelaron transacciones.')
                )
        else:
            self.stdout.write('')
            self.stdout.write(
                self.style.WARNING(f'DRY RUN: {total_encontradas} transacciones serían canceladas.')
            )