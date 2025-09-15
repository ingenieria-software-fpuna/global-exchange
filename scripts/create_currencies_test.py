#!/usr/bin/env python3
"""
Script para poblar la base de datos con monedas y tasas de cambio de ejemplo.
Útil para desarrollo y testing.
"""

import os
import sys
import django
from decimal import Decimal

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'global_exchange.settings')
django.setup()

from monedas.models import Moneda
from tasa_cambio.models import TasaCambio
from django.utils import timezone

def crear_monedas_ejemplo():
    """Crear monedas de ejemplo con sus tasas de cambio"""
    
    monedas_datos = [
        {
            'nombre': 'Dólar Estadounidense',
            'codigo': 'USD',
            'simbolo': '$',
            'decimales': 2,
            'tasa_compra': Decimal('7200.00'),
            'tasa_venta': Decimal('7300.00')
        },
        {
            'nombre': 'Euro',
            'codigo': 'EUR',
            'simbolo': '€',
            'decimales': 2,
            'tasa_compra': Decimal('7800.00'),
            'tasa_venta': Decimal('7900.00')
        },
        {
            'nombre': 'Real Brasileño',
            'codigo': 'BRL',
            'simbolo': 'R$',
            'decimales': 2,
            'tasa_compra': Decimal('1430.00'),
            'tasa_venta': Decimal('1470.00')
        },
        {
            'nombre': 'Peso Argentino',
            'codigo': 'ARS',
            'simbolo': '$',
            'decimales': 2,
            'tasa_compra': Decimal('8.40'),
            'tasa_venta': Decimal('8.60')
        },
        {
            'nombre': 'Libra Esterlina',
            'codigo': 'GBP',
            'simbolo': '£',
            'decimales': 2,
            'tasa_compra': Decimal('9200.00'),
            'tasa_venta': Decimal('9400.00')
        },
        {
            'nombre': 'Yen Japonés',
            'codigo': 'JPY',
            'simbolo': '¥',
            'decimales': 0,
            'tasa_compra': Decimal('48.00'),
            'tasa_venta': Decimal('52.00')
        },
        {
            'nombre': 'Dólar Canadiense',
            'codigo': 'CAD',
            'simbolo': 'C$',
            'decimales': 2,
            'tasa_compra': Decimal('5300.00'),
            'tasa_venta': Decimal('5400.00')
        },
        {
            'nombre': 'Franco Suizo',
            'codigo': 'CHF',
            'simbolo': 'CHF',
            'decimales': 2,
            'tasa_compra': Decimal('8200.00'),
            'tasa_venta': Decimal('8300.00')
        },
        {
            'nombre': 'Dólar Australiano',
            'codigo': 'AUD',
            'simbolo': 'A$',
            'decimales': 2,
            'tasa_compra': Decimal('4800.00'),
            'tasa_venta': Decimal('4900.00')
        },
        {
            'nombre': 'Yuan Chino',
            'codigo': 'CNY',
            'simbolo': '¥',
            'decimales': 2,
            'tasa_compra': Decimal('1000.00'),
            'tasa_venta': Decimal('1020.00')
        }
    ]
    
    print("💰 Creando monedas y tasas de cambio de ejemplo...")
    
    monedas_creadas = 0
    tasas_creadas = 0
    
    for datos in monedas_datos:
        # Crear o obtener la moneda
        moneda, moneda_created = Moneda.objects.get_or_create(
            codigo=datos['codigo'],
            defaults={
                'nombre': datos['nombre'],
                'simbolo': datos['simbolo'],
                'decimales': datos['decimales'],
                'es_activa': True
            }
        )
        
        if moneda_created:
            print(f"  ✅ Moneda creada: {moneda.nombre} ({moneda.codigo})")
            monedas_creadas += 1
        else:
            print(f"  ℹ️  Moneda ya existe: {moneda.nombre} ({moneda.codigo})")
        
        # Crear tasa de cambio si no existe una activa
        tasa_existente = TasaCambio.objects.filter(
            moneda=moneda,
            es_activa=True
        ).first()
        
        if not tasa_existente:
            TasaCambio.objects.create(
                moneda=moneda,
                tasa_compra=datos['tasa_compra'],
                tasa_venta=datos['tasa_venta'],
                fecha_vigencia=timezone.now(),
                es_activa=True
            )
            print(f"    ✅ Tasa de cambio creada: Compra {datos['tasa_compra']} - Venta {datos['tasa_venta']}")
            tasas_creadas += 1
        else:
            print(f"    ℹ️  Tasa de cambio ya existe para {moneda.codigo}")
    
    print(f"\n📊 Resumen:")
    print(f"  • Monedas procesadas: {len(monedas_datos)}")
    print(f"  • Monedas creadas: {monedas_creadas}")
    print(f"  • Tasas de cambio creadas: {tasas_creadas}")
    
    return monedas_creadas, tasas_creadas

def verificar_datos():
    """Verificar que los datos se crearon correctamente"""
    print("\n🔍 Verificando datos creados...")
    
    monedas_activas = Moneda.objects.filter(es_activa=True).count()
    tasas_activas = TasaCambio.objects.filter(es_activa=True).count()
    
    print(f"  • Monedas activas: {monedas_activas}")
    print(f"  • Tasas de cambio activas: {tasas_activas}")
    
    if monedas_activas > 0 and tasas_activas > 0:
        print("  ✅ Datos verificados correctamente")
        return True
    else:
        print("  ❌ Error en la verificación de datos")
        return False

def main():
    """Función principal del script"""
    print("🚀 Iniciando población de datos de ejemplo...")
    print("=" * 50)
    
    try:
        # Crear monedas y tasas
        monedas_creadas, tasas_creadas = crear_monedas_ejemplo()
        
        # Verificar datos
        if verificar_datos():
            print("\n🎉 ¡Datos de ejemplo creados exitosamente!")
            print("   Ahora puedes ver las monedas en la pantalla de bienvenida.")
        else:
            print("\n❌ Error al crear los datos de ejemplo.")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
