#!/usr/bin/env python3
"""
Script para crear los métodos de cobro iniciales con sus restricciones de monedas.

Los métodos de cobro serán:
- Transferencia bancaria (Solo para PYG)
- Tarjeta de débito (Solo para PYG)
- Billetera electrónica (Solo para PYG)
- Tarjeta de crédito (Solo para PYG, USD)
- Efectivo (Todas las monedas excepto PYG)
"""

import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'global_exchange.settings')
django.setup()

from decimal import Decimal
from metodo_cobro.models import MetodoCobro
from monedas.models import Moneda


def crear_metodos_cobro():
    """Crear los métodos de cobro predeterminados"""
    
    print("Iniciando creación de métodos de cobro...")
    
    # Obtener las monedas
    try:
        pyg = Moneda.objects.get(codigo="PYG")
        usd = Moneda.objects.get(codigo="USD")
        eur = Moneda.objects.get(codigo="EUR")
        todas_monedas_excepto_pyg = Moneda.objects.exclude(codigo="PYG").filter(es_activa=True)
    except Moneda.DoesNotExist as e:
        print(f"Error: No se encontró una moneda requerida: {e}")
        return False
    
    # Definir los métodos de cobro
    metodos_data = [
        {
            'nombre': 'Transferencia bancaria',
            'descripcion': 'Transferencia bancaria local',
            'comision': Decimal('1.00'),
            'monedas': [pyg],
            'requiere_retiro_fisico': False  # Transferencia = No requiere retiro físico
        },
        {
            'nombre': 'Tarjeta de débito',
            'descripcion': 'Pago con tarjeta de débito',
            'comision': Decimal('1.50'),
            'monedas': [pyg],
            'requiere_retiro_fisico': False  # Tarjeta = No requiere retiro físico
        },
        {
            'nombre': 'Billetera electrónica',
            'descripcion': 'Pago mediante billetera electrónica',
            'comision': Decimal('2.00'),
            'monedas': [pyg],
            'requiere_retiro_fisico': False  # Digital = No requiere retiro físico
        },
        {
            'nombre': 'Tarjeta de crédito',
            'descripcion': 'Pago con tarjeta de crédito',
            'comision': Decimal('3.00'),
            'monedas': [pyg, usd],
            'requiere_retiro_fisico': False  # Tarjeta = No requiere retiro físico
        },
        {
            'nombre': 'Tarjeta de crédito local',
            'descripcion': 'Pago con tarjeta de crédito local (Panal, Cabal)',
            'comision': Decimal('2.50'),
            'monedas': [pyg],
            'requiere_retiro_fisico': False  # Tarjeta = No requiere retiro físico

        },
        {
            'nombre': 'Efectivo',
            'descripcion': 'Pago en efectivo',
            'comision': Decimal('0.00'),
            'monedas': list(todas_monedas_excepto_pyg),
            'requiere_retiro_fisico': True  # Efectivo = Requiere retiro físico
        }
    ]
    
    # Crear cada método de cobro
    for metodo_data in metodos_data:
        metodo, created = MetodoCobro.objects.get_or_create(
            nombre=metodo_data['nombre'],
            defaults={
                'descripcion': metodo_data['descripcion'],
                'comision': metodo_data['comision'],
                'es_activo': True,
                'requiere_retiro_fisico': metodo_data['requiere_retiro_fisico']
            }
        )
        
        # Actualizar el campo si ya existía
        if not created and metodo.requiere_retiro_fisico != metodo_data['requiere_retiro_fisico']:
            metodo.requiere_retiro_fisico = metodo_data['requiere_retiro_fisico']
            metodo.save()
        
        # Agregar las monedas permitidas
        metodo.monedas_permitidas.set(metodo_data['monedas'])
        
        if created:
            retiro_text = "Requiere retiro físico" if metodo.requiere_retiro_fisico else "No requiere retiro físico"
            print(f"✓ Creado: {metodo.nombre} - {retiro_text}")
        else:
            retiro_text = "Requiere retiro físico" if metodo.requiere_retiro_fisico else "No requiere retiro físico"
            print(f"✓ Ya existe: {metodo.nombre} - {retiro_text}")
    
    print(f"\n¡Métodos de cobro creados exitosamente!")
    print(f"Total de métodos: {MetodoCobro.objects.count()}")
    return True


if __name__ == '__main__':
    crear_metodos_cobro()