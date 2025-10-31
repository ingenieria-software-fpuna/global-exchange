#!/usr/bin/env python
"""
Script para configurar el ESI desde variables de entorno.
Lee las credenciales desde .env y las inserta en la base de datos de SQL-Proxy.
"""
import psycopg
import os
import sys
from pathlib import Path

# Cargar variables de entorno desde .env
try:
    from dotenv import load_dotenv
    # Buscar el archivo .env en el directorio del proyecto
    env_path = Path(__file__).resolve().parent.parent / '.env'
    load_dotenv(env_path)
except ImportError:
    print("⚠️  python-dotenv no está instalado, usando variables de entorno del sistema")
except Exception as e:
    print(f"⚠️  Error al cargar .env: {e}")


def get_connection():
    """Conecta a la base de datos de SQL-Proxy"""
    try:
        connection = psycopg.connect(
            user=os.getenv("INVOICE_DB_USER", "fs_proxy_user"),
            password=os.getenv("INVOICE_DB_PASSWORD", "p123456"),
            host=os.getenv("INVOICE_DB_HOST", "localhost"),
            port=os.getenv("INVOICE_DB_PORT", "45432"),
            dbname=os.getenv("INVOICE_DB_NAME", "fs_proxy_bd"),
            connect_timeout=5
        )
        return connection
    except Exception as e:
        print(f"❌ Error al conectar a SQL-Proxy: {e}")
        print("\nAsegúrate de que SQL-Proxy esté corriendo:")
        print("  make sqlproxy-up")
        return None


def check_existing_esi(connection):
    """Verifica si ya existe un ESI"""
    cursor = connection.cursor()
    cursor.execute("SELECT COUNT(*) FROM public.esi;")
    count = cursor.fetchone()[0]
    cursor.close()
    return count > 0


def delete_all_esi(connection):
    """Elimina todos los ESI existentes"""
    cursor = connection.cursor()
    cursor.execute("DELETE FROM public.esi;")
    connection.commit()
    cursor.close()


def insert_esi_from_env(connection):
    """Inserta ESI usando datos de variables de entorno"""
    # Leer variables de entorno
    ruc = os.getenv("ESI_RUC")
    ruc_dv = os.getenv("ESI_RUC_DV")
    nombre = os.getenv("ESI_NOMBRE")
    descripcion = os.getenv("ESI_DESCRIPCION", "")
    esi_email = os.getenv("ESI_EMAIL")
    esi_password = os.getenv("ESI_PASSWORD", "")
    esi_token = os.getenv("ESI_TOKEN", "")
    esi_url = os.getenv("ESI_URL")

    # Validar que todas las variables requeridas estén presentes
    # Nota: ESI_PASSWORD y ESI_TOKEN son opcionales (uno u otro debe estar presente)
    required = {
        "ESI_RUC": ruc,
        "ESI_RUC_DV": ruc_dv,
        "ESI_NOMBRE": nombre,
        "ESI_EMAIL": esi_email,
        "ESI_URL": esi_url
    }

    missing = [key for key, value in required.items() if not value]
    if missing:
        print(f"❌ Faltan variables de entorno: {', '.join(missing)}")
        print("\nAgrega estas variables a tu archivo .env:")
        for key in missing:
            print(f"  {key}=valor")
        return False

    try:
        cursor = connection.cursor()
        insert_query = """
        INSERT INTO public.esi (ruc, ruc_dv, nombre, descripcion, estado, esi_email, esi_passwd, esi_token, esi_url)
        VALUES (%s, %s, %s, %s, 'ACTIVO', %s, %s, %s, %s);
        """
        cursor.execute(insert_query, (ruc, ruc_dv, nombre, descripcion, esi_email, esi_password, esi_token, esi_url))
        connection.commit()
        cursor.close()
        print("✅ ESI configurado exitosamente")
        print(f"   RUC: {ruc}-{ruc_dv}")
        print(f"   Nombre: {nombre}")
        print(f"   Email: {esi_email}")
        print(f"   URL: {esi_url}")
        if esi_token:
            print(f"   Token: {'*' * 20}... (configurado)")
        if esi_password:
            print(f"   Password: {'*' * 10} (configurado)")
        return True
    except Exception as e:
        print(f"❌ Error al insertar ESI: {e}")
        return False


def main():
    # Conectar a la base de datos
    connection = get_connection()
    if not connection:
        sys.exit(1)

    # Si ya existe ESI, eliminarlo
    if check_existing_esi(connection):
        print("ℹ️  ESI existente encontrado, reemplazando...")
        delete_all_esi(connection)

    # Insertar ESI desde .env
    success = insert_esi_from_env(connection)
    connection.close()

    if not success:
        sys.exit(1)


if __name__ == "__main__":
    main()
