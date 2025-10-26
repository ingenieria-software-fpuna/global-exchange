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
            'nombre': 'Guaraní',
            'codigo': 'PYG',
            'simbolo': '₲',
            'decimales': 0
            # NO tiene precio_base, comision_compra, comision_venta porque es la moneda base
        },
        {
            'nombre': 'Dólar Estadounidense',
            'codigo': 'USD',
            'simbolo': '$',
            'decimales': 2,
            'precio_base': Decimal('7500.00'),
            'comision_compra': Decimal('300.00'),
            'comision_venta': Decimal('200.00')
        },
        {
            'nombre': 'Euro',
            'codigo': 'EUR',
            'simbolo': '€',
            'decimales': 2,
            'precio_base': Decimal('8200.00'),
            'comision_compra': Decimal('400.00'),
            'comision_venta': Decimal('300.00')
        },
        {
            'nombre': 'Real Brasileño',
            'codigo': 'BRL',
            'simbolo': 'R$',
            'decimales': 2,
            'precio_base': Decimal('1500.00'),
            'comision_compra': Decimal('70.00'),
            'comision_venta': Decimal('50.00')
        },
        {
            'nombre': 'Peso Argentino',
            'codigo': 'ARS',
            'simbolo': '$',
            'decimales': 2,
            'precio_base': Decimal('8.50'),
            'comision_compra': Decimal('0.10'),
            'comision_venta': Decimal('0.10')
        },
        {
            'nombre': 'Libra Esterlina',
            'codigo': 'GBP',
            'simbolo': '£',
            'decimales': 2,
            'precio_base': Decimal('9500.00'),
            'comision_compra': Decimal('300.00'),
            'comision_venta': Decimal('200.00')
        },
        {
            'nombre': 'Yen Japonés',
            'codigo': 'JPY',
            'simbolo': '¥',
            'decimales': 0,
            'precio_base': Decimal('50.00'),
            'comision_compra': Decimal('2.00'),
            'comision_venta': Decimal('2.00')
        },
        {
            'nombre': 'Dólar Canadiense',
            'codigo': 'CAD',
            'simbolo': 'C$',
            'decimales': 2,
            'precio_base': Decimal('5500.00'),
            'comision_compra': Decimal('200.00'),
            'comision_venta': Decimal('150.00')
        },
        {
            'nombre': 'Franco Suizo',
            'codigo': 'CHF',
            'simbolo': 'CHF',
            'decimales': 2,
            'precio_base': Decimal('8500.00'),
            'comision_compra': Decimal('300.00'),
            'comision_venta': Decimal('200.00')
        },
        {
            'nombre': 'Dólar Australiano',
            'codigo': 'AUD',
            'simbolo': 'A$',
            'decimales': 2,
            'precio_base': Decimal('5000.00'),
            'comision_compra': Decimal('200.00'),
            'comision_venta': Decimal('100.00')
        },
        {
            'nombre': 'Yuan Chino',
            'codigo': 'CNY',
            'simbolo': '¥',
            'decimales': 2,
            'precio_base': Decimal('1050.00'),
            'comision_compra': Decimal('50.00'),
            'comision_venta': Decimal('30.00')
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
        
        # NO crear tasa de cambio para el Guaraní (es la moneda base)
        if moneda.codigo == 'PYG':
            print(f"    ⚠️  Guaraní es la moneda base - NO se crea tasa de cambio")
            continue
        
        # Crear tasa de cambio si no existe una activa
        tasa_existente = TasaCambio.objects.filter(
            moneda=moneda,
            es_activa=True
        ).first()
        
        if not tasa_existente:
            TasaCambio.objects.create(
                moneda=moneda,
                precio_base=datos['precio_base'],
                comision_compra=datos['comision_compra'],
                comision_venta=datos['comision_venta'],
                es_activa=True
            )
            # Calcular precios para mostrar
            precio_compra = datos['precio_base'] - datos['comision_compra']
            precio_venta = datos['precio_base'] + datos['comision_venta']
            print(f"    ✅ Tasa de cambio creada: Base {datos['precio_base']} (Compra {precio_compra} - Venta {precio_venta})")
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
