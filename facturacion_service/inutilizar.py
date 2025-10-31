#!/usr/bin/env python3
"""
Script de línea de comandos para inutilizar documentos electrónicos.

Uso:
    python inutilizar.py                    # Inutiliza el rango configurado
    python inutilizar.py 1 2 3             # Inutiliza los números específicos
    python inutilizar.py --start 1 --end 100  # Inutiliza un rango específico
"""
import psycopg
import os
import sys
import argparse
from datetime import datetime
import logging

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def get_sql_proxy_connection():
    """
    Crea una conexión a la base de datos de SQL-Proxy.
    Lee las credenciales desde variables de entorno.
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


def get_default_range():
    """
    Obtiene el rango por defecto desde las variables de entorno.
    """
    start = int(os.getenv("INUTILIZAR_START", "1"))
    end = int(os.getenv("INUTILIZAR_END", "100"))
    return start, end


def insert_de_inutilizar(connection, dNumDoc):
    """
    Inserta un documento electrónico con estado 'Inutilizar'.

    Args:
        connection: Conexión a la base de datos
        dNumDoc: Número de documento (será formateado a 7 dígitos)

    Returns:
        True si fue exitoso, False en caso contrario
    """
    try:
        cursor = connection.cursor()

        # Formatear dNumDoc a 7 dígitos con ceros a la izquierda
        dNumDoc_formatted = str(dNumDoc).zfill(7)

        insert_query = f"""
        INSERT INTO public.de
        (iTiDE, dFeEmiDE, dEst, dPunExp, dNumDoc, CDC, dSerieNum, estado,
        estado_sifen, desc_sifen, error_sifen, fch_sifen, estado_can, desc_can, error_can, fch_can, estado_inu, desc_inu, error_inu, fch_inu,
        iTipEmi, dNumTim, dFeIniT, iTipTra, iTImp, cMoneOpe, dTiCam, dInfoFisc, dRucEm, dDVEmi,
        iTipCont, dNomEmi, dDirEmi, dNumCas,
        cDepEmi, dDesDepEmi, cCiuEmi, dDesCiuEmi, dTelEmi, dEmailE,
        iNatRec, iTiOpe, cPaisRec, iTiContRec, dRucRec, dDVRec, iTipIDRec, dDTipIDRec, dNumIDRec,
        dNomRec, dEmailRec,
        dDirRec, dNumCasRec, cDepRec, dDesDepRec, cCiuRec, dDesCiuRec,
        iNatVen, iTipIDVen, dNumIDVen, dNomVen, dDirVen, dNumCasVen, cDepVen, dDesDepVen, cCiuVen, dDesCiuVen,
        dDirProv, cDepProv, dDesDepProv, cCiuProv, dDesCiuProv,
        iMotEmi,
        iIndPres, iCondOpe, dPlazoCre,
        dModCont, dEntCont, dAnoCont, dSecCont, dFeCodCont,
        dSisFact, dInfAdic,
        iMotEmiNR, iRespEmiNR,
        iTipTrans, iModTrans, iRespFlete, dIniTras, dFinTras,
        dDirLocSal, dNumCasSal, cDepSal, dDesDepSal, cCiuSal, dDesCiuSal,
        dDirLocEnt, dNumCasEnt, cDepEnt, dDesDepEnt, cCiuEnt, dDesCiuEnt,
        dTiVehTras, dMarVeh, dTipIdenVeh, dNroIDVeh, dNroMatVeh,
        iNatTrans, dNomTrans, dRucTrans, dDVTrans, iTipIDTrans, dNumIDTrans,
        dNumIDChof, dNomChof,
        fch_ins, fch_upd)
        VALUES( '1', '', '001', '001', '{dNumDoc_formatted}', '0', '', 'Inutilizar',
        '', '', '', '', '', '', '', '', '', '', '', '',
        '', '80143335', '', '', '', '', '', '', '80143335', '',
        '', '', '', '',
        '', '', '', '', '', '',
        '', '', '', '', '', '', '', '', '',
        '', '',
        '', '', '', '', '', '',
        '', '', '', '', '', '', '', '', '', '',
        '', '', '', '', '',
        '',
        '', '', '',
        '', '', '', '', '',
        '', '',
        '', '',
        '', '', '', '', '',
        '', '', '', '', '', '',
        '', '', '', '', '', '',
        '', '', '', '', '',
        '', '', '', '', '', '',
        '', '',
        CURRENT_TIMESTAMP, CURRENT_TIMESTAMP);
        """
        cursor.execute(insert_query)
        connection.commit()
        cursor.close()
        logger.info(f"✅ Documento {dNumDoc_formatted} marcado para inutilizar")
        return True

    except (Exception, psycopg.Error) as error:
        logger.error(f"❌ Error al insertar documento {dNumDoc}: {error}")
        connection.rollback()
        return False


def inutilizar_documentos(num_docs):
    """
    Inutiliza una lista de documentos.

    Args:
        num_docs: Lista de números de documentos a inutilizar
    """
    connection = None
    try:
        connection = get_sql_proxy_connection()
        logger.info(f"Conectado a la base de datos SQL-Proxy")

        exitosos = 0
        fallidos = 0

        for num_doc in num_docs:
            if insert_de_inutilizar(connection, num_doc):
                exitosos += 1
            else:
                fallidos += 1

        logger.info(f"\n📊 Resumen:")
        logger.info(f"   Total procesados: {len(num_docs)}")
        logger.info(f"   Exitosos: {exitosos}")
        logger.info(f"   Fallidos: {fallidos}")

    except Exception as error:
        logger.error(f"Error en el proceso: {error}")
        sys.exit(1)
    finally:
        if connection:
            connection.close()
            logger.info("Conexión cerrada")


def main():
    parser = argparse.ArgumentParser(
        description='Inutilizar documentos electrónicos',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Ejemplos de uso:
  %(prog)s                        # Inutiliza el rango configurado en variables de entorno
  %(prog)s 1 2 3                  # Inutiliza los documentos 1, 2 y 3
  %(prog)s --start 1 --end 100    # Inutiliza del documento 1 al 100
  %(prog)s --start 50 --end 60    # Inutiliza del documento 50 al 60
        """
    )

    parser.add_argument(
        'num_docs',
        nargs='*',
        type=int,
        help='Números de documentos a inutilizar (separados por espacio)'
    )

    parser.add_argument(
        '--start',
        type=int,
        help='Número inicial del rango a inutilizar'
    )

    parser.add_argument(
        '--end',
        type=int,
        help='Número final del rango a inutilizar'
    )

    args = parser.parse_args()

    # Determinar qué números de documentos procesar
    if args.start is not None and args.end is not None:
        # Usar el rango especificado por argumentos
        if args.start > args.end:
            logger.error("❌ El número inicial debe ser menor o igual al final")
            sys.exit(1)
        num_docs = list(range(args.start, args.end + 1))
        logger.info(f"Inutilizando rango especificado: {args.start} - {args.end}")

    elif args.num_docs:
        # Usar los números específicos proporcionados
        num_docs = args.num_docs
        logger.info(f"Inutilizando documentos específicos: {', '.join(map(str, num_docs))}")

    else:
        # Usar el rango por defecto de las variables de entorno
        start, end = get_default_range()
        num_docs = list(range(start, end + 1))
        logger.info(f"Inutilizando rango configurado: {start} - {end}")
        logger.info(f"(Total: {len(num_docs)} documentos)")

    # Confirmar acción
    if len(num_docs) > 10:
        respuesta = input(f"⚠️  Se van a inutilizar {len(num_docs)} documentos. ¿Continuar? (s/n): ")
        if respuesta.lower() != 's':
            logger.info("Operación cancelada por el usuario")
            sys.exit(0)

    # Ejecutar inutilización
    inutilizar_documentos(num_docs)


if __name__ == "__main__":
    main()
