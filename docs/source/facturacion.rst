Servicio de Facturación Electrónica
====================================

El módulo facturacion_service proporciona integración con sistemas de facturación electrónica compatibles con SIFEN (Paraguay).

Componentes Principales
-----------------------

invoice_generator
~~~~~~~~~~~~~~~~~

Módulo principal para generación de facturas electrónicas.

**Funcionalidades:**

- Conexión a base de datos SQL-Proxy (sistema de facturación)
- Obtención de ESI (Emisor de Facturas Electrónicas) activo
- Generación de facturas según estándar SIFEN
- Manejo de códigos de control y numeración

**Funciones principales:**

.. code-block:: python

    from facturacion_service.invoice_generator import (
        get_sql_proxy_connection,
        get_active_esi,
        generate_invoice
    )
    
    # Conectar a sistema de facturación
    conn = get_sql_proxy_connection()
    
    # Obtener ESI activo
    esi = get_active_esi(conn)
    
    # Generar factura
    factura = generate_invoice(
        transaccion=transaccion,
        cliente=cliente,
        items=items_factura
    )

factura_utils
~~~~~~~~~~~~~

Módulo de utilidades para consultar el estado de facturas electrónicas y obtener archivos generados.

**Funciones principales:**

get_sql_proxy_connection()
^^^^^^^^^^^^^^^^^^^^^^^^^^^

Crea una conexión a la base de datos de SQL-Proxy.

- Lee credenciales desde variables de entorno
- Retorna conexión psycopg
- Lanza excepción si la conexión falla

get_de_status(de_id)
^^^^^^^^^^^^^^^^^^^^

Obtiene el estado de un Documento Electrónico desde SQL-Proxy.

**Parámetros:**

- ``de_id``: ID del DE en la base de datos de SQL-Proxy

**Retorna:**

Dict con información del DE o None si no se encuentra:

.. code-block:: python

    {
        'id': int,
        'dnumdoc': str,          # Número de documento
        'dest': str,             # Establecimiento
        'dpunexp': str,          # Punto de expedición
        'estado': str,           # Estado interno
        'cdc': str,              # Código de Control
        'dfeemide': str,         # Fecha de emisión
        'estado_sifen': str,     # Estado en SIFEN
        'error_sifen': str,      # Error si falló
        'error_inu': str         # Error de inutilización
    }

**Uso:**

.. code-block:: python

    from facturacion_service.factura_utils import get_de_status
    
    de_info = get_de_status(123)
    if de_info:
        print(f"CDC: {de_info['cdc']}")
        print(f"Estado SIFEN: {de_info['estado_sifen']}")

find_de_files(de_info)
^^^^^^^^^^^^^^^^^^^^^^

Busca los archivos PDF y XML generados para un DE.

**Parámetros:**

- ``de_info``: Dict con información del DE (retornado por get_de_status)

**Retorna:**

Dict con rutas a los archivos:

.. code-block:: python

    {
        'pdf': '/path/to/factura.pdf' o None,
        'xml': '/path/to/factura.xml' o None
    }

**Directorio de búsqueda:**

- Lee ``INVOICE_FILES_DIR`` de variables de entorno
- Default: ``/app/invoices``
- Busca archivos por patrón del CDC

**Ejemplo:**

.. code-block:: python

    from facturacion_service.factura_utils import get_de_status, find_de_files
    
    de_info = get_de_status(123)
    if de_info:
        archivos = find_de_files(de_info)
        if archivos['pdf']:
            print(f"PDF disponible en: {archivos['pdf']}")
        if archivos['xml']:
            print(f"XML disponible en: {archivos['xml']}")

inutilizar
~~~~~~~~~~

Script y módulo para inutilización de rangos de numeración de documentos electrónicos.

**Descripción:**

Cuando se pierden, dañan o no se utilizan documentos de un rango pre-asignado, la normativa SIFEN requiere inutilizarlos formalmente. Este módulo permite:

- Registrar documentos con estado 'Inutilizar' en la base de datos
- Notificar a SIFEN según normativa paraguaya
- Mantener trazabilidad de numeración
- Evitar huecos en la secuencia de facturas

**Funciones principales:**

get_default_range()
^^^^^^^^^^^^^^^^^^^

Obtiene el rango por defecto desde variables de entorno.

**Variables de entorno:**

- ``INUTILIZAR_START``: Número inicial del rango (default: 1)
- ``INUTILIZAR_END``: Número final del rango (default: 100)

**Retorna:**

- Tupla ``(start, end)`` con los números del rango

insert_de_inutilizar(connection, dNumDoc)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Inserta un documento electrónico con estado 'Inutilizar'.

**Parámetros:**

- ``connection``: Conexión a la base de datos SQL-Proxy
- ``dNumDoc``: Número de documento (será formateado a 7 dígitos)

**Retorna:**

- ``True`` si fue exitoso
- ``False`` si falló

**Proceso:**

1. Formatea el número a 7 dígitos con ceros a la izquierda
2. Inserta registro en tabla ``de`` con estado 'Inutilizar'
3. El sistema SQL-Proxy procesa la inutilización en SIFEN
4. Registra timestamp de inserción

inutilizar_range(start, end)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Inutiliza un rango completo de documentos.

**Parámetros:**

- ``start``: Número inicial del rango
- ``end``: Número final del rango

**Proceso:**

.. code-block:: python

    def inutilizar_range(start, end):
        connection = get_sql_proxy_connection()
        exitosos = 0
        fallidos = 0
        
        for num in range(start, end + 1):
            if insert_de_inutilizar(connection, num):
                exitosos += 1
            else:
                fallidos += 1
        
        connection.close()
        return exitosos, fallidos

**Uso desde línea de comandos:**

.. code-block:: bash

    # Inutilizar rango por defecto (desde variables de entorno)
    python facturacion_service/inutilizar.py
    
    # Inutilizar números específicos
    python facturacion_service/inutilizar.py 1 2 3 5 10
    
    # Inutilizar rango específico
    python facturacion_service/inutilizar.py --start 100 --end 200

**Uso programático:**

.. code-block:: python

    from facturacion_service.inutilizar import inutilizar_range
    
    # Inutilizar documentos 501-520
    exitosos, fallidos = inutilizar_range(501, 520)
    print(f"Inutilizados: {exitosos}, Fallidos: {fallidos}")

**Casos de uso comunes:**

1. **Cambio de numeración:** Al cambiar de rango pre-asignado
2. **Documentos dañados:** Hojas de talonarios físicos dañadas
3. **Error en configuración:** Números asignados incorrectamente
4. **Migración de sistema:** Rangos no utilizados del sistema anterior

**Consideraciones importantes:**

- Solo se pueden inutilizar documentos que no han sido emitidos
- La inutilización es irreversible
- SIFEN registra la inutilización permanentemente
- Mantener log de todas las inutilizaciones
- Documentar el motivo de cada inutilización

Configuración
-------------

**Variables de entorno requeridas:**

.. code-block:: bash

    # Conexión a base de datos de facturación
    INVOICE_DB_HOST=localhost
    INVOICE_DB_PORT=45432
    INVOICE_DB_NAME=fs_proxy_bd
    INVOICE_DB_USER=fs_proxy_user
    INVOICE_DB_PASSWORD=password_secreto
    
    # Configuración ESI
    ESI_RUC=80012345
    ESI_DV=6
    ESI_NOMBRE="Mi Empresa SA"
    ESI_EMAIL=facturacion@empresa.com

**En settings.py:**

.. code-block:: python

    # Habilitar facturación electrónica
    FACTURACION_ENABLED = os.getenv('FACTURACION_ENABLED', 'False') == 'True'
    
    # Timeout para conexiones
    FACTURACION_TIMEOUT = int(os.getenv('FACTURACION_TIMEOUT', '30'))

Integración con Transacciones
------------------------------

Al completar una transacción pagada:

.. code-block:: python

    from facturacion_service.invoice_generator import generar_factura_transaccion
    
    # Después de confirmar pago
    if transaccion.estado.codigo == 'PAGADA':
        try:
            factura = generar_factura_transaccion(transaccion)
            transaccion.factura_numero = factura['numero']
            transaccion.factura_cdc = factura['cdc']  # Código de Control
            transaccion.save()
        except Exception as e:
            logger.error(f"Error generando factura: {e}")
            # Transacción se completa igualmente

Modelo ContadorDocumentoFactura
--------------------------------

En ``configuracion.models``:

.. code-block:: python

    class ContadorDocumentoFactura(models.Model):
        """
        Contador de numeración de facturas.
        Asegura secuencia única e ininterrumpida.
        """
        establecimiento = models.CharField(max_length=3)  # Ej: 001
        punto_expedicion = models.CharField(max_length=3)  # Ej: 001
        ultimo_numero = models.IntegerField(default=0)
        
        def siguiente_numero(self):
            """Obtiene y incrementa el contador de forma atómica"""
            with transaction.atomic():
                self.ultimo_numero = F('ultimo_numero') + 1
                self.save()
                self.refresh_from_db()
                return self.ultimo_numero

Estructura de Factura
---------------------

**Campos principales:**

- **Encabezado:**
  - RUC emisor
  - Número de factura (establecimiento-punto-número)
  - Fecha y hora de emisión
  - Código de Control (CDC)
  
- **Cliente (Receptor):**
  - Nombre/Razón social
  - RUC (si aplica)
  - Documento de identidad
  
- **Detalle:**
  - Descripción del servicio (Cambio de moneda)
  - Cantidad
  - Precio unitario
  - Subtotal
  
- **Totales:**
  - Subtotal gravado
  - IVA (si aplica)
  - Total general

Formato de Numeración
----------------------

Las facturas siguen el formato SIFEN:

``001-001-0000001``

Donde:

- ``001``: Establecimiento (Tauser/sucursal)
- ``001``: Punto de expedición (caja/terminal)
- ``0000001``: Número secuencial (7 dígitos)

Casos de Uso
------------

**Factura para transacción de cambio:**

.. code-block:: python

    {
        "tipo_documento": "01",  # Factura electrónica
        "numero": "001-001-0000123",
        "fecha": "2025-10-31T14:30:00",
        "emisor": {
            "ruc": "80012345",
            "dv": "6",
            "nombre": "Global Exchange SA"
        },
        "receptor": {
            "nombre": "Juan Pérez",
            "documento": "1234567"
        },
        "items": [
            {
                "descripcion": "Cambio USD 100.00 a PYG",
                "cantidad": 1,
                "precio_unitario": 760000,
                "subtotal": 760000
            }
        ],
        "total": 760000
    }

Manejo de Errores
-----------------

**Errores comunes:**

1. **Conexión a SQL-Proxy falla:**
   - Log del error
   - Continuar transacción sin factura
   - Generar factura posteriormente

2. **ESI no configurado:**
   - Validar durante setup inicial
   - Mostrar advertencia a admin
   - Deshabilitar facturación automática

3. **Numeración duplicada:**
   - Usar transacciones atómicas
   - Reintentar con nuevo número
   - Log de conflictos

Consideraciones SIFEN
----------------------

**Normativa paraguaya:**

- Facturas deben generarse en tiempo real
- CDC (Código de Control) único por documento
- Formato XML según esquema SIFEN
- Envío a SET (autoridad fiscal) obligatorio
- Conservación por 5 años mínimo

**Requisitos técnicos:**

- Certificado digital válido
- Conexión estable a internet
- Respaldo de facturas emitidas
- Sincronización de reloj del sistema

Seguridad
---------

**Protección de datos:**

- Credenciales en variables de entorno
- Conexión encriptada a base de datos
- Logs de acceso a facturación
- Validación de permisos por usuario

**Auditoría:**

- Registro de todas las facturas generadas
- Tracking de intentos fallidos
- Alertas de anomalías en numeración
- Respaldo automático de facturas

Pruebas
-------

**Testing del servicio:**

.. code-block:: python

    # tests/test_facturacion.py
    from facturacion_service import invoice_generator
    
    def test_conexion_sql_proxy():
        conn = invoice_generator.get_sql_proxy_connection()
        assert conn is not None
        conn.close()
    
    def test_obtener_esi_activo():
        conn = invoice_generator.get_sql_proxy_connection()
        esi = invoice_generator.get_active_esi(conn)
        assert esi is not None
        assert 'ruc' in esi

**Ejecutar pruebas:**

.. code-block:: bash

    poetry run python manage.py test facturacion_service

Deployment
----------

**Requisitos previos:**

1. Sistema SQL-Proxy instalado y configurado
2. Base de datos PostgreSQL para facturas
3. Certificado digital SIFEN configurado
4. Variables de entorno configuradas

**Verificación:**

.. code-block:: bash

    # Verificar conexión
    python manage.py shell
    >>> from facturacion_service import invoice_generator
    >>> conn = invoice_generator.get_sql_proxy_connection()
    >>> print("Conexión exitosa")

Soporte y Troubleshooting
--------------------------

**Logs:**

.. code-block:: bash

    # Ver logs de facturación
    tail -f logs/facturacion.log

**Comandos útiles:**

.. code-block:: bash

    # Verificar ESI activo
    python manage.py check_esi
    
    # Sincronizar contador de facturas
    python manage.py sync_contador_facturas
    
    # Regenerar facturas fallidas
    python manage.py retry_facturas_fallidas

Referencias
-----------

- Documentación SIFEN: https://www.set.gov.py/web/factura-electronica
- SQL-Proxy: Sistema intermedio de facturación
- Esquemas XML SIFEN para validación de estructura

Mejoras Futuras
---------------

- Generación de notas de crédito
- Facturación en moneda extranjera
- Reportes fiscales automatizados
- API REST para consulta de facturas
- Integración con sistemas contables
