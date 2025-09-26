#!/usr/bin/env python3
"""
Script para crear datos históricos de tasas de cambio.
Crea múltiples entradas para poder ver gráficos en la vista histórica.
"""

import os
import sys
import django
from datetime import datetime, timedelta
from decimal import Decimal
import random

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'global_exchange.settings')
django.setup()

from monedas.models import Moneda
from tasa_cambio.models import TasaCambio
from django.utils import timezone


def crear_datos_historicos():
    """Crear múltiples tasas de cambio históricas para poder ver gráficos"""

    print("📈 Creando datos históricos de tasas de cambio...")

    # Obtener algunas monedas para crear historial
    monedas_principales = ['USD', 'EUR', 'BRL', 'ARS', 'GBP', 'JPY', 'CHF', 'CAD', 'AUD', 'CNY']

    datos_creados = 0

    for codigo_moneda in monedas_principales:
        try:
            moneda = Moneda.objects.get(codigo=codigo_moneda, es_activa=True)
            print(f"\n💱 Creando historial para {moneda.nombre} ({codigo_moneda})")

            # Obtener la tasa actual
            tasa_actual = TasaCambio.objects.filter(moneda=moneda, es_activa=True).first()

            if not tasa_actual:
                print(f"  ⚠️  No hay tasa activa para {codigo_moneda}")
                continue

            # Crear 15 entradas históricas en los últimos 30 días
            base_precio = tasa_actual.precio_base
            base_comision_compra = tasa_actual.comision_compra
            base_comision_venta = tasa_actual.comision_venta

            for i in range(15):
                # Fecha hacia atrás
                dias_atras = 30 - (i * 2)
                fecha_historica = timezone.now() - timedelta(days=dias_atras)

                # Generar variaciones realistas en los precios
                variacion = Decimal(str(random.uniform(-0.05, 0.05)))  # ±5%
                nuevo_precio = base_precio * (Decimal('1') + variacion)

                # Crear nueva tasa histórica (inactiva)
                TasaCambio.objects.create(
                    moneda=moneda,
                    precio_base=nuevo_precio.quantize(Decimal('0.01')),
                    comision_compra=base_comision_compra,
                    comision_venta=base_comision_venta,
                    es_activa=False,
                    fecha_creacion=fecha_historica,
                    fecha_actualizacion=fecha_historica
                )
                datos_creados += 1

            # Activar la tasa más reciente (la última creada)
            tasa_mas_reciente = TasaCambio.objects.filter(moneda=moneda).order_by('-fecha_creacion').first()
            if tasa_mas_reciente:
                # Desactivar todas las tasas de esta moneda
                TasaCambio.objects.filter(moneda=moneda).update(es_activa=False)
                # Activar solo la más reciente
                tasa_mas_reciente.es_activa = True
                tasa_mas_reciente.save()

            print(f"  ✅ Creadas 15 entradas históricas para {codigo_moneda} (activada la más reciente)")

        except Moneda.DoesNotExist:
            print(f"  ❌ Moneda {codigo_moneda} no encontrada")

    print(f"\n📊 Resumen:")
    print(f"  • Total de entradas históricas creadas: {datos_creados}")
    print(f"  • Monedas con historial: {len(monedas_principales)}")

    return datos_creados


def verificar_datos_historicos():
    """Verificar que se crearon los datos históricos"""
    print("\n🔍 Verificando datos históricos...")

    monedas_con_historial = []

    for codigo_moneda in ['USD', 'EUR', 'BRL', 'ARS', 'GBP', 'JPY', 'CHF', 'CAD', 'AUD', 'CNY']:
        try:
            moneda = Moneda.objects.get(codigo=codigo_moneda)
            total_tasas = TasaCambio.objects.filter(moneda=moneda).count()
            tasas_activas = TasaCambio.objects.filter(moneda=moneda, es_activa=True).count()
            tasas_historicas = total_tasas - tasas_activas

            print(f"  • {codigo_moneda}: {total_tasas} total ({tasas_activas} activa, {tasas_historicas} históricas)")

            if tasas_historicas > 0:
                monedas_con_historial.append(codigo_moneda)

        except Moneda.DoesNotExist:
            continue

    if len(monedas_con_historial) > 0:
        print(f"\n✅ {len(monedas_con_historial)} monedas tienen datos históricos")
        print("🎯 Ahora puedes ver gráficos en las vistas históricas")
        return True
    else:
        print("\n❌ No se encontraron datos históricos")
        return False


def main():
    """Función principal del script"""
    print("🚀 Iniciando creación de datos históricos...")
    print("=" * 55)

    try:
        # Crear datos históricos
        datos_creados = crear_datos_historicos()

        # Verificar datos
        if verificar_datos_historicos():
            print("\n🎉 ¡Datos históricos creados exitosamente!")
            print("   Ahora puedes ver gráficos evolutivos en las vistas históricas.")
            print("   Ve a Cotizaciones → Click en el ícono de gráfico de cualquier moneda")
        else:
            print("\n❌ Error al crear los datos históricos.")
            sys.exit(1)

    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()