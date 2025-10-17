#!/usr/bin/env python
"""
Script para crear el método de cobro Stripe automáticamente
"""
import os
import sys
import django

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'global_exchange.settings')
django.setup()

from metodo_cobro.models import MetodoCobro
from monedas.models import Moneda


def create_stripe_method():
    """Crea el método de cobro Stripe con configuración por defecto"""

    print("=" * 60)
    print("CREANDO MÉTODO DE COBRO STRIPE")
    print("=" * 60)

    # Verificar si ya existe
    if MetodoCobro.objects.filter(nombre__iexact='stripe').exists():
        print("✓ Método de cobro Stripe ya existe")
        stripe_method = MetodoCobro.objects.get(nombre__iexact='stripe')
    else:
        # Crear método Stripe
        stripe_method = MetodoCobro.objects.create(
            nombre='Stripe',
            descripcion='Pago con tarjeta de crédito/débito internacional vía Stripe Checkout',
            comision=2.9,  # Comisión típica de Stripe (2.9% + $0.30)
            es_activo=True
        )
        print(f"✓ Método de cobro 'Stripe' creado (ID: {stripe_method.id})")

    # Asociar monedas comunes para pagos internacionales
    monedas_stripe = ['USD', 'EUR', 'GBP', 'PYG']
    monedas_agregadas = []

    for codigo in monedas_stripe:
        try:
            moneda = Moneda.objects.get(codigo=codigo)
            if not stripe_method.monedas_permitidas.filter(id=moneda.id).exists():
                stripe_method.monedas_permitidas.add(moneda)
                monedas_agregadas.append(codigo)
        except Moneda.DoesNotExist:
            print(f"  ⚠ Moneda {codigo} no existe en el sistema (omitiendo)")

    if monedas_agregadas:
        print(f"✓ Monedas asociadas a Stripe: {', '.join(monedas_agregadas)}")
    else:
        print("✓ Monedas ya estaban asociadas a Stripe")

    # Mostrar resumen
    print("\n" + "=" * 60)
    print("RESUMEN")
    print("=" * 60)
    print(f"Nombre: {stripe_method.nombre}")
    print(f"Descripción: {stripe_method.descripcion}")
    print(f"Comisión: {stripe_method.comision}%")
    print(f"Estado: {'Activo' if stripe_method.es_activo else 'Inactivo'}")
    print(f"Monedas: {stripe_method.get_monedas_permitidas_str()}")
    print("=" * 60)
    print("✅ Configuración de Stripe completada")
    print("")


if __name__ == '__main__':
    try:
        create_stripe_method()
    except Exception as e:
        print(f"\n❌ Error al crear método Stripe: {str(e)}")
        sys.exit(1)
