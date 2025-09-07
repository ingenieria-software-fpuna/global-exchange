from django.core.management.base import BaseCommand
from django.utils import timezone
from auth.models import CodigoVerificacion

class Command(BaseCommand):
    help = 'Limpia códigos de verificación expirados y usados'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Muestra cuántos códigos se eliminarían sin eliminarlos realmente',
        )

    def handle(self, *args, **options):
        if options['dry_run']:
            # Contar códigos que se eliminarían
            count = CodigoVerificacion.objects.filter(
                fecha_expiracion__lt=timezone.now()
            ).count()
            
            count_usados = CodigoVerificacion.objects.filter(
                usado=True,
                fecha_creacion__lt=timezone.now() - timezone.timedelta(hours=24)
            ).count()
            
            total = count + count_usados
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Se eliminarían {total} códigos de verificación '
                    f'({count} expirados, {count_usados} usados hace más de 24h)'
                )
            )
        else:
            # Ejecutar limpieza real
            deleted_count, _ = CodigoVerificacion.limpiar_codigos_expirados()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Se eliminaron {deleted_count[0]} códigos de verificación expirados'
                )
            )
            
            # Mostrar estadísticas actuales
            total_activos = CodigoVerificacion.objects.filter(
                usado=False,
                fecha_expiracion__gt=timezone.now()
            ).count()
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Códigos activos restantes: {total_activos}'
                )
            )
