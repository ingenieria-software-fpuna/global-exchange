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

from monedas.models import Moneda, DenominacionMoneda
from tasa_cambio.models import TasaCambio
from django.utils import timezone

def crear_monedas_ejemplo():
    """Crear monedas de ejemplo con sus tasas de cambio"""
    
    monedas_datos = [
        {
            'nombre': 'Guaraní',
            'codigo': 'PYG',
            'simbolo': '₲',
            'decimales': 0,
            'precio_base': Decimal('1.00'),
            'comision_compra': Decimal('0.00'),
            'comision_venta': Decimal('0.00'),
            'denominaciones': [
                {'valor': 100000, 'tipo': 'BILLETE'},
                {'valor': 50000, 'tipo': 'BILLETE'},
                {'valor': 20000, 'tipo': 'BILLETE'},
                {'valor': 10000, 'tipo': 'BILLETE'},
                {'valor': 5000, 'tipo': 'BILLETE'},
                {'valor': 2000, 'tipo': 'BILLETE'},
            ]
        },
        {
            'nombre': 'Dólar Estadounidense',
            'codigo': 'USD',
            'simbolo': '$',
            'decimales': 2,
            'precio_base': Decimal('7500.00'),
            'comision_compra': Decimal('300.00'),
            'comision_venta': Decimal('200.00'),
            'denominaciones': [
                {'valor': 100, 'tipo': 'BILLETE'},
                {'valor': 50, 'tipo': 'BILLETE'},
                {'valor': 20, 'tipo': 'BILLETE'},
                {'valor': 10, 'tipo': 'BILLETE'},
                {'valor': 5, 'tipo': 'BILLETE'},
            ]
        },
        {
            'nombre': 'Euro',
            'codigo': 'EUR',
            'simbolo': '€',
            'decimales': 2,
            'precio_base': Decimal('8200.00'),
            'comision_compra': Decimal('400.00'),
            'comision_venta': Decimal('300.00'),
            'denominaciones': [
                {'valor': 500, 'tipo': 'BILLETE'},
                {'valor': 200, 'tipo': 'BILLETE'},
                {'valor': 100, 'tipo': 'BILLETE'},
                {'valor': 50, 'tipo': 'BILLETE'},
                {'valor': 20, 'tipo': 'BILLETE'},
                {'valor': 10, 'tipo': 'BILLETE'},
                {'valor': 5, 'tipo': 'BILLETE'},
            ]
        },
        {
            'nombre': 'Real Brasileño',
            'codigo': 'BRL',
            'simbolo': 'R$',
            'decimales': 2,
            'precio_base': Decimal('1500.00'),
            'comision_compra': Decimal('70.00'),
            'comision_venta': Decimal('50.00'),
            'denominaciones': [
                {'valor': 200, 'tipo': 'BILLETE'},
                {'valor': 100, 'tipo': 'BILLETE'},
                {'valor': 50, 'tipo': 'BILLETE'},
                {'valor': 20, 'tipo': 'BILLETE'},
                {'valor': 10, 'tipo': 'BILLETE'},
                {'valor': 5, 'tipo': 'BILLETE'},
                {'valor': 2, 'tipo': 'BILLETE'},
            ]
        },
        {
            'nombre': 'Peso Argentino',
            'codigo': 'ARS',
            'simbolo': '$',
            'decimales': 2,
            'precio_base': Decimal('8.50'),
            'comision_compra': Decimal('0.10'),
            'comision_venta': Decimal('0.10'),
            'denominaciones': [
                {'valor': 2000, 'tipo': 'BILLETE'},
                {'valor': 1000, 'tipo': 'BILLETE'},
                {'valor': 500, 'tipo': 'BILLETE'},
                {'valor': 200, 'tipo': 'BILLETE'},
                {'valor': 100, 'tipo': 'BILLETE'},
                {'valor': 50, 'tipo': 'BILLETE'},
                {'valor': 20, 'tipo': 'BILLETE'},
                {'valor': 10, 'tipo': 'BILLETE'},
                {'valor': 5, 'tipo': 'BILLETE'},
                {'valor': 2, 'tipo': 'BILLETE'},
            ]
        },
        {
            'nombre': 'Libra Esterlina',
            'codigo': 'GBP',
            'simbolo': '£',
            'decimales': 2,
            'precio_base': Decimal('9500.00'),
            'comision_compra': Decimal('300.00'),
            'comision_venta': Decimal('200.00'),
            'denominaciones': [
                {'valor': 50, 'tipo': 'BILLETE'},
                {'valor': 20, 'tipo': 'BILLETE'},
                {'valor': 10, 'tipo': 'BILLETE'},
                {'valor': 5, 'tipo': 'BILLETE'},
            ]
        },
        {
            'nombre': 'Yen Japonés',
            'codigo': 'JPY',
            'simbolo': '¥',
            'decimales': 0,
            'precio_base': Decimal('50.00'),
            'comision_compra': Decimal('2.00'),
            'comision_venta': Decimal('2.00'),
            'denominaciones': [
                {'valor': 10000, 'tipo': 'BILLETE'},
                {'valor': 5000, 'tipo': 'BILLETE'},
                {'valor': 2000, 'tipo': 'BILLETE'},
                {'valor': 1000, 'tipo': 'BILLETE'},
            ]
        },
        {
            'nombre': 'Dólar Canadiense',
            'codigo': 'CAD',
            'simbolo': 'C$',
            'decimales': 2,
            'precio_base': Decimal('5500.00'),
            'comision_compra': Decimal('200.00'),
            'comision_venta': Decimal('150.00'),
            'denominaciones': [
                {'valor': 100, 'tipo': 'BILLETE'},
                {'valor': 50, 'tipo': 'BILLETE'},
                {'valor': 20, 'tipo': 'BILLETE'},
                {'valor': 10, 'tipo': 'BILLETE'},
                {'valor': 5, 'tipo': 'BILLETE'},
            ]
        },
        {
            'nombre': 'Franco Suizo',
            'codigo': 'CHF',
            'simbolo': 'CHF',
            'decimales': 2,
            'precio_base': Decimal('8500.00'),
            'comision_compra': Decimal('300.00'),
            'comision_venta': Decimal('200.00'),
            'denominaciones': [
                {'valor': 1000, 'tipo': 'BILLETE'},
                {'valor': 200, 'tipo': 'BILLETE'},
                {'valor': 100, 'tipo': 'BILLETE'},
                {'valor': 50, 'tipo': 'BILLETE'},
                {'valor': 20, 'tipo': 'BILLETE'},
                {'valor': 10, 'tipo': 'BILLETE'},
            ]
        },
        {
            'nombre': 'Dólar Australiano',
            'codigo': 'AUD',
            'simbolo': 'A$',
            'decimales': 2,
            'precio_base': Decimal('5000.00'),
            'comision_compra': Decimal('200.00'),
            'comision_venta': Decimal('100.00'),
            'denominaciones': [
                {'valor': 100, 'tipo': 'BILLETE'},
                {'valor': 50, 'tipo': 'BILLETE'},
                {'valor': 20, 'tipo': 'BILLETE'},
                {'valor': 10, 'tipo': 'BILLETE'},
                {'valor': 5, 'tipo': 'BILLETE'},
            ]
        },
        {
            'nombre': 'Yuan Chino',
            'codigo': 'CNY',
            'simbolo': '¥',
            'decimales': 2,
            'precio_base': Decimal('1050.00'),
            'comision_compra': Decimal('50.00'),
            'comision_venta': Decimal('30.00'),
            'denominaciones': [
                {'valor': 100, 'tipo': 'BILLETE'},
                {'valor': 50, 'tipo': 'BILLETE'},
                {'valor': 20, 'tipo': 'BILLETE'},
                {'valor': 10, 'tipo': 'BILLETE'},
                {'valor': 5, 'tipo': 'BILLETE'},
            ]
        }
    ]
    
    print("💰 Creando monedas, tasas de cambio y denominaciones de ejemplo...")
    
    monedas_creadas = 0
    tasas_creadas = 0
    denominaciones_creadas = 0
    
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
        
        # Crear denominaciones si no existen
        denominaciones_existentes = DenominacionMoneda.objects.filter(
            moneda=moneda,
            es_activa=True
        ).count()
        
        if denominaciones_existentes == 0 and 'denominaciones' in datos:
            print(f"    🪙 Creando denominaciones para {moneda.codigo}...")
            for i, denom_data in enumerate(datos['denominaciones'], 1):
                denominacion, denom_created = DenominacionMoneda.objects.get_or_create(
                    moneda=moneda,
                    valor=denom_data['valor'],
                    tipo=denom_data['tipo'],
                    defaults={
                        'es_activa': True,
                        'orden': i
                    }
                )
                if denom_created:
                    denominaciones_creadas += 1
                    print(f"      ✅ {denominacion.mostrar_denominacion()}")
                else:
                    print(f"      ℹ️  {denominacion.mostrar_denominacion()} ya existe")
        else:
            print(f"    ℹ️  Denominaciones ya existen para {moneda.codigo}")
    
    print(f"\n📊 Resumen:")
    print(f"  • Monedas procesadas: {len(monedas_datos)}")
    print(f"  • Monedas creadas: {monedas_creadas}")
    print(f"  • Tasas de cambio creadas: {tasas_creadas}")
    print(f"  • Denominaciones creadas: {denominaciones_creadas}")
    
    return monedas_creadas, tasas_creadas, denominaciones_creadas

def verificar_datos():
    """Verificar que los datos se crearon correctamente"""
    print("\n🔍 Verificando datos creados...")
    
    monedas_activas = Moneda.objects.filter(es_activa=True).count()
    tasas_activas = TasaCambio.objects.filter(es_activa=True).count()
    denominaciones_activas = DenominacionMoneda.objects.filter(es_activa=True).count()
    
    print(f"  • Monedas activas: {monedas_activas}")
    print(f"  • Tasas de cambio activas: {tasas_activas}")
    print(f"  • Denominaciones activas: {denominaciones_activas}")
    
    # Mostrar resumen por moneda
    print(f"\n📋 Resumen por moneda:")
    for moneda in Moneda.objects.filter(es_activa=True).order_by('codigo'):
        denom_count = DenominacionMoneda.objects.filter(moneda=moneda, es_activa=True).count()
        print(f"  • {moneda.codigo} - {moneda.nombre}: {denom_count} denominaciones")
    
    if monedas_activas > 0 and tasas_activas > 0 and denominaciones_activas > 0:
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
        # Crear monedas, tasas y denominaciones
        monedas_creadas, tasas_creadas, denominaciones_creadas = crear_monedas_ejemplo()
        
        # Verificar datos
        if verificar_datos():
            print("\n🎉 ¡Datos de ejemplo creados exitosamente!")
            print("   Ahora puedes ver las monedas y denominaciones en el sistema.")
            print("   Las denominaciones están listas para cargar stock por denominación.")
        else:
            print("\n❌ Error al crear los datos de ejemplo.")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
