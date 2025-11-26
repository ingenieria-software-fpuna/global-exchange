"""
Generador de facturas electrónicas.
Basado en sql-proxy01/client/app.py pero integrado con GLX.
"""
import psycopg
from datetime import datetime
import logging
import os
import django
from django.core.exceptions import ValidationError

# Configurar Django si aún no está configurado
if not django.apps.apps.ready:
    django.setup()

from configuracion.models import ContadorDocumentoFactura

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


def get_active_esi(connection):
    """
    Obtiene el ESI activo desde la base de datos.
    """
    try:
        cursor = connection.cursor()
        cursor.execute("SELECT ruc, ruc_dv, nombre, esi_email FROM public.esi WHERE estado = 'ACTIVO' LIMIT 1;")
        esi = cursor.fetchone()
        cursor.close()

        if not esi:
            raise Exception("No hay ESI activo configurado")

        return {
            'ruc': esi[0],
            'ruc_dv': esi[1],
            'nombre': esi[2],
            'email': esi[3]
        }
    except (Exception, psycopg.Error) as error:
        logger.error(f"Error al obtener ESI: {error}")
        raise


def generar_factura_desde_transaccion(transaccion):
    """
    Genera una factura electrónica a partir de una transacción de GLX.

    Args:
        transaccion: Objeto Transaccion de Django

    Returns:
        ID del DE generado
    """
    connection = None
    try:
        # Conectar a SQL-Proxy DB
        connection = get_sql_proxy_connection()
        cursor = connection.cursor()

        # Obtener ESI activo
        esi = get_active_esi(connection)

        # Generar fecha de emisión
        dFeEmiDE = datetime.now().strftime("%Y-%m-%d")

        # Obtener el siguiente número de documento auto-incremental
        try:
            dNumDoc = ContadorDocumentoFactura.obtener_siguiente_numero()
        except ValidationError as e:
            logger.error(f"Error al obtener número de documento: {e}")
            raise Exception(f"No se pudo generar el número de documento: {e}")

        # Datos del receptor (cliente)
        if transaccion.cliente:
            dNomRec = transaccion.cliente.nombre_comercial
            dEmailRec = transaccion.cliente.correo_electronico
            dRucRec = transaccion.cliente.ruc
            dDVRec = transaccion.cliente.dv
        else:
            dNomRec = "CLIENTE CASUAL"
            dEmailRec = ""

        # Insertar DE (Documento Electrónico) - usando la misma estructura que app.py
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
        VALUES( '1', '{dFeEmiDE}', '001', '003', '{dNumDoc}', '0', '', 'Borrador',
        '1', '2', '3', '4', '5', '6', '7', '8', '9', '10', '11', '12',
        '1', '02595733', '2025-03-27', '2', '5', 'PYG', '1', '', '{esi["ruc"]}', '{esi["ruc_dv"]}',
        '2', '{esi["nombre"]}', 'FACULTAD POLITECNICA UNA', '0',
        '1', 'CAPITAL', '1', 'ASUNCION (DISTRITO)', '(0981)111111', '{esi["email"]}',
        '1', '1', 'PRY', '1', '{dRucRec}', '{dDVRec}', '0', '', '0',
        '{dNomRec}', '{dEmailRec}',
        '', '', '', '', '', '',
        '', '', '', '', '', '', '', '', '', '',
        '', '', '', '', '',
        '',
        '1', '1', '',
        '', '', '', '', '',
        '1', 'Transacción GLX ID: {transaccion.id_transaccion}',
        '', '',
        '', '', '', '', '',
        '', '', '', '', '', '',
        '', '', '', '', '', '',
        '', '', '', '', '',
        '', '', '', '', '', '',
        '', '',
        CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        RETURNING id;
        """
        cursor.execute(insert_query)
        connection.commit()
        de_id = cursor.fetchone()[0]
        logger.info(f"DE insertado exitosamente, ID: {de_id}")

        # Insertar actividades económicas
        insert_query = f"""
        INSERT INTO public.gActEco
        (cActEco, dDesActEco, fch_ins, fch_upd, de_id) VALUES
        ('62010','Actividades de programación informática', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, {de_id}),
        ('74909','Otras actividades profesionales, científicas y técnicas n.c.p.', CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, {de_id});
        """
        cursor.execute(insert_query)
        connection.commit()
        logger.info("Actividades económicas insertadas")

        # Insertar item de la factura (servicio de cambio de divisas)
        descripcion_servicio = f"Cambio de divisas - {transaccion.tipo_operacion.nombre}"
        
        # Usar monto en guaranies segun el tipo de operacion
        if transaccion.tipo_operacion.codigo == "VENTA":
            # Para VENTA usar el monto destino (Esto era el error)
            monto = float(transaccion.monto_destino)
        else:
            # Para COMPRA usar el monto origen
            monto = float(transaccion.monto_origen)

        insert_query = f"""
        INSERT INTO public.gCamItem
        (dCodInt, dDesProSer, dCantProSer, dPUniProSer, dDescItem,
        iAfecIVA, dPropIVA, dTasaIVA,
        dParAranc, dNCM, dDncpG, dDncpE, dGtin, dGtinPq,
        fch_ins, fch_upd,
        de_id) VALUES
        ('1', '{descripcion_servicio}', '1', '{monto}', '0',
        '3', '0', '0',
        '', '', '', '', '', '',
        CURRENT_TIMESTAMP, CURRENT_TIMESTAMP,
        {de_id});
        """
        cursor.execute(insert_query)
        connection.commit()
        logger.info("Item de factura insertado")

        # Insertar condición de pago
        insert_query = f"""
        INSERT INTO public.gPaConEIni
        (iTiPago, dMonTiPag, cMoneTiPag, dTiCamTiPag,
        dNumCheq, dBcoEmi,
        iDenTarj, iForProPa,
        fch_ins, fch_upd, de_id)
        VALUES('1', '0', '{transaccion.moneda_origen.codigo}', '1',
        '', '',
        '', '',
        CURRENT_TIMESTAMP, CURRENT_TIMESTAMP, {de_id});
        """
        cursor.execute(insert_query)
        connection.commit()
        logger.info("Condición de pago insertada")

        # Actualizar DE a estado "Confirmado"
        update_query = f"""
        UPDATE public.de
        SET estado = 'Confirmado'
        WHERE estado = 'Borrador'
        AND id = {de_id};
        """
        cursor.execute(update_query)
        connection.commit()
        logger.info(f"DE {de_id} actualizado a 'Confirmado'")

        cursor.close()

        logger.info(f"✅ Factura generada exitosamente para transacción {transaccion.id_transaccion}, DE ID: {de_id}")
        return de_id

    except (Exception, psycopg.Error) as error:
        logger.error(f"Error al generar factura: {error}")
        if connection:
            connection.rollback()
        raise
    finally:
        if connection:
            connection.close()
