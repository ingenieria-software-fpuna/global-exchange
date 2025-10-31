#!/usr/bin/env python
"""
Script para configurar el ESI (Emisor de Servicios de Integración) en SQL-Proxy.
Este script se conecta directamente a la base de datos de SQL-Proxy e inserta
la configuración del ESI necesaria para generar facturas electrónicas.
"""
import psycopg
import os
from getpass import getpass


def get_connection():
    """Conecta a la base de datos de SQL-Proxy"""
    try:
        connection = psycopg.connect(
            user=os.getenv("INVOICE_DB_USER", "fs_proxy_user"),
            password=os.getenv("INVOICE_DB_PASSWORD", "p123456"),
            host=os.getenv("INVOICE_DB_HOST", "localhost"),
            port=os.getenv("INVOICE_DB_PORT", "45432"),
            dbname=os.getenv("INVOICE_DB_NAME", "fs_proxy_bd")
        )
        return connection
    except Exception as e:
        print(f"❌ Error al conectar a la base de datos: {e}")
        print("\nAsegúrate de que SQL-Proxy esté corriendo:")
        print("  make sqlproxy-up")
        return None


def check_existing_esi(connection):
    """Verifica si ya existe un ESI activo"""
    cursor = connection.cursor()
    cursor.execute("SELECT COUNT(*) FROM public.esi WHERE estado = 'ACTIVO';")
    count = cursor.fetchone()[0]
    cursor.close()
    return count > 0


def delete_all_esi(connection):
    """Elimina todos los ESI existentes"""
    cursor = connection.cursor()
    cursor.execute("DELETE FROM public.esi;")
    connection.commit()
    cursor.close()
    print("✅ Todos los ESI anteriores han sido eliminados")


def insert_esi(connection, ruc, ruc_dv, nombre, descripcion, esi_email, esi_passwd, esi_url):
    """Inserta un nuevo ESI en la base de datos"""
    try:
        cursor = connection.cursor()
        insert_query = """
        INSERT INTO public.esi (ruc, ruc_dv, nombre, descripcion, estado, esi_email, esi_passwd, esi_token, esi_url)
        VALUES (%s, %s, %s, %s, 'ACTIVO', %s, %s, '', %s);
        """
        cursor.execute(insert_query, (ruc, ruc_dv, nombre, descripcion, esi_email, esi_passwd, esi_url))
        connection.commit()
        cursor.close()
        print("✅ ESI configurado exitosamente")
        return True
    except Exception as e:
        print(f"❌ Error al insertar ESI: {e}")
        return False


def main():
    print("╔════════════════════════════════════════════════════════════╗")
    print("║        CONFIGURACIÓN DE ESI - Facturación Electrónica     ║")
    print("╚════════════════════════════════════════════════════════════╝")
    print()

    # Conectar a la base de datos
    connection = get_connection()
    if not connection:
        return

    # Verificar si ya existe un ESI
    if check_existing_esi(connection):
        print("⚠️  Ya existe un ESI activo en la base de datos")
        respuesta = input("¿Deseas eliminar el ESI existente y crear uno nuevo? (s/N): ").strip().lower()
        if respuesta != 's':
            print("Operación cancelada")
            connection.close()
            return
        delete_all_esi(connection)
        print()

    # Solicitar datos del ESI
    print("Ingresa los datos del ESI:")
    print()

    ruc = input("RUC de tu empresa: ").strip()
    ruc_dv = input("RUC DV (dígito verificador): ").strip()
    nombre = input("Nombre de tu empresa: ").strip()
    descripcion = input("Descripción (opcional): ").strip()
    esi_email = input("Email del ESI (FacturaSegura): ").strip()
    esi_passwd = getpass("Contraseña del ESI (FacturaSegura): ")

    print()
    print("Selecciona el ambiente:")
    print("  1. TEST (https://apitest.facturasegura.com.py)")
    print("  2. PROD (https://api.facturasegura.com.py)")
    ambiente = input("Ambiente (1 o 2): ").strip()

    if ambiente == "1":
        esi_url = "https://apitest.facturasegura.com.py"
    elif ambiente == "2":
        esi_url = "https://api.facturasegura.com.py"
    else:
        print("❌ Opción inválida. Debe ser 1 o 2")
        connection.close()
        return

    # Confirmar datos
    print()
    print("═" * 60)
    print("Datos a guardar:")
    print(f"  RUC: {ruc}-{ruc_dv}")
    print(f"  Nombre: {nombre}")
    print(f"  Descripción: {descripcion or '(sin descripción)'}")
    print(f"  Email: {esi_email}")
    print(f"  URL: {esi_url}")
    print("═" * 60)
    print()

    confirmar = input("¿Confirmas estos datos? (s/N): ").strip().lower()
    if confirmar != 's':
        print("Operación cancelada")
        connection.close()
        return

    # Insertar ESI
    print()
    if insert_esi(connection, ruc, ruc_dv, nombre, descripcion, esi_email, esi_passwd, esi_url):
        print()
        print("╔════════════════════════════════════════════════════════════╗")
        print("║                  ✅ ESI CONFIGURADO                        ║")
        print("╚════════════════════════════════════════════════════════════╝")
        print()
        print("El sistema ya puede generar facturas electrónicas automáticamente")
        print("cuando una transacción sea marcada como PAGADA.")
    else:
        print()
        print("❌ Error al configurar el ESI")

    connection.close()


if __name__ == "__main__":
    main()
