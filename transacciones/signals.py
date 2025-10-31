"""
Señales para el app de transacciones.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Transaccion, EstadoTransaccion
import logging
import os

logger = logging.getLogger(__name__)


def is_sqlproxy_available():
    """
    Verifica si SQL-Proxy está disponible intentando conectar.
    """
    try:
        import psycopg
        connection = psycopg.connect(
            user=os.getenv("INVOICE_DB_USER", "fs_proxy_user"),
            password=os.getenv("INVOICE_DB_PASSWORD", "p123456"),
            host=os.getenv("INVOICE_DB_HOST", "localhost"),
            port=os.getenv("INVOICE_DB_PORT", "45432"),
            dbname=os.getenv("INVOICE_DB_NAME", "fs_proxy_bd"),
            connect_timeout=2  # Timeout rápido
        )
        connection.close()
        return True
    except:
        return False


@receiver(post_save, sender=Transaccion)
def generar_factura_al_pagar(sender, instance, created, **kwargs):
    """
    Genera automáticamente una factura electrónica cuando una transacción es pagada.

    NOTA: Solo genera facturas si SQL-Proxy está corriendo. Durante make app-setup
    o cuando SQL-Proxy no está disponible, simplemente se salta la generación.
    """
    # Solo procesar si la transacción está en estado PAGADA y no tiene ya un DE asignado
    if instance.estado.codigo == EstadoTransaccion.PAGADA and not instance.de_id:
        # Verificar si SQL-Proxy está disponible
        if not is_sqlproxy_available():
            logger.info(
                f"⏭️  SQL-Proxy no disponible. Saltando generación de factura para "
                f"transacción {instance.id_transaccion}"
            )
            return

        try:
            # Importar aquí para evitar problemas de import circular
            from facturacion_service import generar_factura_desde_transaccion

            logger.info(f"Generando factura para transacción {instance.id_transaccion}")
            de_id = generar_factura_desde_transaccion(instance)
            logger.info(
                f"✅ Factura generada exitosamente para transacción {instance.id_transaccion}. "
                f"DE ID: {de_id}"
            )

            # Guardar el de_id en la transacción sin trigger el signal de nuevo
            Transaccion.objects.filter(id=instance.id).update(de_id=de_id)

        except Exception as e:
            # Log el error pero no romper el flujo
            logger.warning(
                f"⚠️  No se pudo generar factura para transacción {instance.id_transaccion}: {e}"
            )
            # NO hacer raise para no romper el guardado de la transacción
