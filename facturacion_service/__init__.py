"""
Servicio de facturación electrónica.
Conecta directamente con la base de datos de SQL-Proxy usando psycopg.
"""
from .invoice_generator import generar_factura_desde_transaccion

__all__ = ['generar_factura_desde_transaccion']
