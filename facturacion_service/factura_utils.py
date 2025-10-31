"""
Utilidades para consultar el estado de facturas electrónicas y obtener archivos generados.
"""
import psycopg
import os
import glob
import logging
from pathlib import Path

logger = logging.getLogger(__name__)


def get_sql_proxy_connection():
    """
    Crea una conexión a la base de datos de SQL-Proxy.
    """
    try:
        connection = psycopg.connect(
            user=os.getenv("INVOICE_DB_USER", "fs_proxy_user"),
            password=os.getenv("INVOICE_DB_PASSWORD", "p123456"),
            host=os.getenv("INVOICE_DB_HOST", "localhost"),
            port=os.getenv("INVOICE_DB_PORT", "45432"),
            dbname=os.getenv("INVOICE_DB_NAME", "fs_proxy_bd")
        )
        return connection
    except (Exception, psycopg.Error) as error:
        logger.error(f"Error al conectar a PostgreSQL: {error}")
        raise


def get_de_status(de_id):
    """
    Obtiene el estado de un Documento Electrónico desde SQL-Proxy.

    Args:
        de_id: ID del DE en la base de datos de SQL-Proxy

    Returns:
        dict con información del DE o None si no se encuentra:
        {
            'id': int,
            'dnumdoc': str,
            'dest': str,
            'dpunexp': str,
            'estado': str,
            'cdc': str,
            'dfeemide': str,
            'estado_sifen': str
        }
    """
    connection = None
    try:
        connection = get_sql_proxy_connection()
        cursor = connection.cursor()

        query = """
        SELECT id, dnumdoc, dest, dpunexp, estado, cdc, dfeemide, estado_sifen,
               error_sifen, error_inu
        FROM public.de
        WHERE id = %s;
        """
        cursor.execute(query, (de_id,))
        result = cursor.fetchone()
        cursor.close()

        if result:
            return {
                'id': result[0],
                'dnumdoc': result[1],
                'dest': result[2],
                'dpunexp': result[3],
                'estado': result[4],
                'cdc': result[5],
                'dfeemide': result[6],
                'estado_sifen': result[7],
                'error_sifen': result[8],
                'error_inu': result[9]
            }
        return None

    except (Exception, psycopg.Error) as error:
        logger.error(f"Error al obtener estado del DE {de_id}: {error}")
        return None
    finally:
        if connection:
            connection.close()


def find_de_files(de_info):
    """
    Busca los archivos PDF y XML generados para un DE.

    Args:
        de_info: dict con información del DE (retornado por get_de_status)

    Returns:
        dict con rutas a los archivos:
        {
            'pdf': str o None,
            'xml': str o None
        }
    """
    if not de_info or de_info['estado'] != 'Aprobado':
        return {'pdf': None, 'xml': None}

    # Construir el patrón de búsqueda
    # Formato: {dest}-{dpunexp}-{dnumdoc}_*.{ext}
    dest = de_info['dest']
    dpunexp = de_info['dpunexp']
    dnumdoc = de_info['dnumdoc']
    dfeemide = de_info['dfeemide']

    # Determinar el directorio basado en la fecha
    # Formato de directorio: YYYYMM
    if dfeemide:
        try:
            # dfeemide está en formato YYYY-MM-DD
            year_month = dfeemide.replace('-', '')[:6]  # YYYYMM
        except:
            year_month = None
    else:
        year_month = None

    # Base path del kude
    base_path = os.getenv("KUDE_PATH", "/home/sebas/Desktop/fpuna/is2/glx/sql-proxy/volumes/web/kude")

    files = {'pdf': None, 'xml': None}

    if year_month:
        search_dir = os.path.join(base_path, year_month)
    else:
        # Si no hay fecha, buscar en todos los subdirectorios
        search_dir = base_path

    # Patrón de búsqueda
    pattern = f"{dest}-{dpunexp}-{dnumdoc}_*"

    try:
        if os.path.exists(search_dir):
            # Buscar archivos PDF
            pdf_pattern = os.path.join(search_dir, f"{pattern}.pdf")
            pdf_files = glob.glob(pdf_pattern)
            if pdf_files:
                files['pdf'] = pdf_files[0]  # Tomar el primero

            # Buscar archivos XML
            xml_pattern = os.path.join(search_dir, f"{pattern}.xml")
            xml_files = glob.glob(xml_pattern)
            if xml_files:
                files['xml'] = xml_files[0]  # Tomar el primero
        else:
            logger.warning(f"Directorio no existe: {search_dir}")

    except Exception as e:
        logger.error(f"Error al buscar archivos para DE {de_info['id']}: {e}")

    return files


def get_factura_files_for_transaction(de_id):
    """
    Obtiene los archivos de factura para una transacción dado su de_id.

    Esta es la función principal que debe ser usada desde las vistas.

    Args:
        de_id: ID del DE

    Returns:
        dict:
        {
            'disponible': bool,
            'estado': str,
            'pdf': str o None,
            'xml': str o None,
            'de_info': dict o None
        }
    """
    if not de_id:
        return {
            'disponible': False,
            'estado': None,
            'pdf': None,
            'xml': None,
            'de_info': None
        }

    # Obtener información del DE
    de_info = get_de_status(de_id)

    if not de_info:
        return {
            'disponible': False,
            'estado': None,
            'pdf': None,
            'xml': None,
            'de_info': None
        }

    # Buscar archivos solo si está aprobado
    files = {'pdf': None, 'xml': None}
    if de_info['estado'] == 'Aprobado':
        files = find_de_files(de_info)

    return {
        'disponible': de_info['estado'] == 'Aprobado' and (files['pdf'] or files['xml']),
        'estado': de_info['estado'],
        'pdf': files['pdf'],
        'xml': files['xml'],
        'de_info': de_info
    }
