#!/usr/bin/env python
"""
Script para probar el sistema de stock de tausers
"""
import os
import sys
import django

# Configurar Django
sys.path.append('/Users/juandavid/Documents/global-exchange')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'global_exchange.settings')
django.setup()

from tauser.models import Tauser, Stock
from monedas.models import Moneda

def test_stock_system():
    """Probar el sistema de stock"""
    print("=== Probando Sistema de Stock ===\n")
    
    # Crear un tauser de prueba si no existe
    tauser, created = Tauser.objects.get_or_create(
        nombre="Tauser de Prueba",
        defaults={
            'direccion': 'Dirección de Prueba 123',
            'horario_atencion': 'Lunes a Viernes 8:00 - 18:00',
            'es_activo': True
        }
    )
    
    if created:
        print(f"✓ Tauser creado: {tauser}")
    else:
        print(f"✓ Tauser existente: {tauser}")
    
    # Obtener una moneda activa
    moneda = Moneda.objects.filter(es_activa=True).first()
    if not moneda:
        print("❌ No hay monedas activas en el sistema")
        return
    
    print(f"✓ Moneda encontrada: {moneda}")
    
    # Crear stock de prueba
    stock, created = Stock.objects.get_or_create(
        tauser=tauser,
        moneda=moneda,
        defaults={
            'cantidad': 1000.00,
            'cantidad_minima': 100.00,
            'es_activo': True
        }
    )
    
    if created:
        print(f"✓ Stock creado: {stock}")
    else:
        print(f"✓ Stock existente: {stock}")
    
    # Probar métodos del modelo
    print(f"\n=== Probando Métodos del Modelo ===")
    print(f"Cantidad actual: {stock.mostrar_cantidad()}")
    print(f"¿Está bajo stock?: {stock.esta_bajo_stock()}")
    
    # Probar agregar cantidad
    print(f"\nAgregando 500 unidades...")
    if stock.agregar_cantidad(500):
        print(f"✓ Cantidad agregada. Nueva cantidad: {stock.mostrar_cantidad()}")
    else:
        print("❌ Error al agregar cantidad")
    
    # Probar reducir cantidad
    print(f"\nReduciendo 200 unidades...")
    if stock.reducir_cantidad(200):
        print(f"✓ Cantidad reducida. Nueva cantidad: {stock.mostrar_cantidad()}")
    else:
        print("❌ Error al reducir cantidad")
    
    # Probar reducir más de lo disponible
    print(f"\nIntentando reducir 2000 unidades (más de lo disponible)...")
    if stock.reducir_cantidad(2000):
        print(f"✓ Cantidad reducida. Nueva cantidad: {stock.mostrar_cantidad()}")
    else:
        print(f"✓ Correctamente rechazado. Cantidad actual: {stock.mostrar_cantidad()}")
    
    # Verificar estado final
    print(f"\n=== Estado Final ===")
    print(f"Tauser: {stock.tauser.nombre}")
    print(f"Moneda: {stock.moneda.nombre} ({stock.moneda.codigo})")
    print(f"Cantidad: {stock.mostrar_cantidad()}")
    print(f"Cantidad mínima: {stock.moneda.mostrar_monto(stock.cantidad_minima)}")
    print(f"¿Está bajo stock?: {'Sí' if stock.esta_bajo_stock() else 'No'}")
    print(f"Estado: {'Activo' if stock.es_activo else 'Inactivo'}")
    
    print(f"\n=== Prueba Completada ===")

if __name__ == "__main__":
    test_stock_system()
