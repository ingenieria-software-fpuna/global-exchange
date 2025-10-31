#!/usr/bin/env python3
"""
Script para inicializar el contador de documentos de factura.
Crea el contador con el rango 0000501 a 0000550.
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'global_exchange.settings')
django.setup()

from configuracion.models import ContadorDocumentoFactura


def main():
    """Función principal del script"""
    print("🔢 Inicializando contador de documentos de factura...")
    print("=" * 60)

    try:
        # Verificar si ya existe un contador
        contador_existente = ContadorDocumentoFactura.objects.first()

        if contador_existente:
            print(f"ℹ️  Ya existe un contador configurado:")
            print(f"   • Número actual: {contador_existente.get_numero_formateado()}")
            print(f"   • Rango: {contador_existente.numero_minimo} - {contador_existente.numero_maximo}")
            print(f"   • Documentos disponibles: {contador_existente.numero_maximo - contador_existente.numero_actual + 1}")

            respuesta = input("\n¿Deseas reiniciar el contador? (s/N): ")
            if respuesta.lower() != 's':
                print("\n✅ Manteniendo contador existente")
                return

            # Reiniciar contador
            contador_existente.numero_actual = 501
            contador_existente.numero_minimo = 501
            contador_existente.numero_maximo = 550
            contador_existente.formato_longitud = 7
            contador_existente.save()

            print("\n✅ Contador reiniciado exitosamente")
            print(f"   • Número inicial: {contador_existente.get_numero_formateado()}")
            print(f"   • Rango: {contador_existente.numero_minimo} - {contador_existente.numero_maximo}")
            print(f"   • Total de documentos disponibles: {contador_existente.numero_maximo - contador_existente.numero_minimo + 1}")
        else:
            # Crear nuevo contador
            contador = ContadorDocumentoFactura.objects.create(
                numero_actual=501,
                numero_minimo=501,
                numero_maximo=550,
                formato_longitud=7
            )

            print("\n✅ Contador creado exitosamente")
            print(f"   • Número inicial: {contador.get_numero_formateado()}")
            print(f"   • Rango: {contador.numero_minimo} - {contador.numero_maximo}")
            print(f"   • Total de documentos disponibles: {contador.numero_maximo - contador.numero_minimo + 1}")

        print("\n📋 Información importante:")
        print("   • El contador se auto-incrementa con cada factura generada")
        print("   • El rango actual permite generar 50 facturas (0000501 a 0000550)")
        print("   • Cuando se alcance el límite, deberás configurar un nuevo rango")
        print("   • Los números son thread-safe (seguros para concurrencia)")

    except Exception as e:
        print(f"\n❌ Error al inicializar contador: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
