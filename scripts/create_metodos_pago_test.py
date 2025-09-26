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
from monedas.models import Moneda


def crear_metodos_pago_ejemplo():
    """Crear métodos de pago específicos del negocio"""
    
    # Obtener monedas
    try:
        pyg = Moneda.objects.get(codigo='PYG', es_activa=True)
        todas_las_monedas = list(Moneda.objects.filter(es_activa=True))
        print(f"🪙 Encontradas {len(todas_las_monedas)} monedas activas")
    except Moneda.DoesNotExist:
        print("❌ Error: No se encontró la moneda PYG. Asegúrate de que las monedas estén creadas.")
        return 0
    
    metodos = [
        {
            "nombre": "Pago en cuenta bancaria",
            "descripcion": "Transferencia a cuenta bancaria del cliente (Solo PYG)",
            "comision": Decimal('0.50'),
            "es_activo": True,
            "monedas_permitidas": [pyg]  # Solo PYG
        },
        {
            "nombre": "Billetera electrónica",
            "descripcion": "Pago mediante billeteras digitales (Solo PYG)",
            "comision": Decimal('1.00'),
            "es_activo": True,
            "monedas_permitidas": [pyg]  # Solo PYG
        },
        {
            "nombre": "Efectivo",
            "descripcion": "Entrega de dinero en efectivo (Todas las monedas)",
            "comision": Decimal('0.00'),
            "es_activo": True,
            "monedas_permitidas": todas_las_monedas  # Todas las monedas
        },
    ]

    print("💳 Creando métodos de pago específicos del negocio...")
    creados = 0
    
    for datos in metodos:
        monedas_permitidas = datos.pop('monedas_permitidas')  # Extraer monedas para configurar después
        
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
            
            # Actualizar monedas permitidas
            monedas_actuales = set(existing.monedas_permitidas.all())
            monedas_nuevas = set(monedas_permitidas)
            if monedas_actuales != monedas_nuevas:
                existing.monedas_permitidas.set(monedas_permitidas)
                updated = True
            
            if updated:
                existing.save()
                monedas_str = ', '.join([m.codigo for m in monedas_permitidas])
                print(f"  🔄 Método actualizado: {existing.nombre} - Monedas: {monedas_str}")
            else:
                monedas_str = ', '.join([m.codigo for m in existing.monedas_permitidas.all()])
                print(f"  ℹ️  Método ya existe: {existing.nombre} - Monedas: {monedas_str}")
        else:
            obj = MetodoPago.objects.create(**datos)
            obj.monedas_permitidas.set(monedas_permitidas)
            monedas_str = ', '.join([m.codigo for m in monedas_permitidas])
            print(f"  ✅ Método creado: {obj.nombre} ({obj.comision}%) - Monedas: {monedas_str}")
            creados += 1

    print(f"\n📊 Resumen: {creados} métodos creados/actualizados")
    
    # Mostrar resumen final
    print("\n🏦 Métodos de pago configurados:")
    for metodo in MetodoPago.objects.filter(es_activo=True).order_by('nombre'):
        monedas = ', '.join([m.codigo for m in metodo.monedas_permitidas.all()])
        print(f"  • {metodo.nombre}: {monedas if monedas else 'Sin monedas'}")
    
    return creados


def main():
    try:
        crear_metodos_pago_ejemplo()
        print("\n🎉 ¡Métodos de pago configurados correctamente!")
        print("\n📋 Configuración aplicada:")
        print("   • Pago en cuenta bancaria: Solo PYG")
        print("   • Billetera electrónica: Solo PYG") 
        print("   • Efectivo: Todas las monedas")
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
