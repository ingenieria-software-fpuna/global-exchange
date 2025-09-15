#!/usr/bin/env python3
"""
Script para poblar la base de datos con métodos de pago de ejemplo.
Útil para desarrollo y testing.
"""

import os
import sys
import django
from decimal import Decimal

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'global_exchange.settings')
django.setup()

from metodo_pago.models import MetodoPago


def crear_metodos_pago_ejemplo():
    """Crear métodos de pago de ejemplo"""
    metodos = [
        {"nombre": "Efectivo", "descripcion": "Pago directo en caja", "comision": Decimal('0.00'), "es_activo": True},
        {"nombre": "Tarjeta de Crédito", "descripcion": "Visa, MasterCard, AMEX", "comision": Decimal('2.50'), "es_activo": True},
        {"nombre": "Transferencia Bancaria", "descripcion": "Transferencia interbancaria", "comision": Decimal('1.00'), "es_activo": True},
        {"nombre": "Billetera Móvil", "descripcion": "Pagos desde billeteras electrónicas", "comision": Decimal('1.50'), "es_activo": True},
    ]

    print("💳 Creando métodos de pago de ejemplo...")
    creados = 0
    for datos in metodos:
        existing = MetodoPago.objects.filter(nombre__iexact=datos["nombre"]).first()
        if existing:
            updated = False
            if existing.descripcion != datos["descripcion"]:
                existing.descripcion = datos["descripcion"]
                updated = True
            if existing.comision != datos["comision"]:
                existing.comision = datos["comision"]
                updated = True
            if not existing.es_activo and datos["es_activo"]:
                existing.es_activo = True
                updated = True
            if updated:
                existing.save()
                print(f"  🔄 Método actualizado: {existing.nombre}")
            else:
                print(f"  ℹ️  Método ya existe: {existing.nombre}")
        else:
            obj = MetodoPago.objects.create(**datos)
            print(f"  ✅ Método creado: {obj.nombre} ({obj.comision}%)")
            creados += 1

    print(f"\n📊 Resumen: {creados} métodos creados")
    return creados


def main():
    try:
        crear_metodos_pago_ejemplo()
        print("\n🎉 ¡Métodos de pago listos!")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
