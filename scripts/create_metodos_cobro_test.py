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
from metodo_pago.models import Campo


def crear_campos_metodos_cobro():
    """Crear campos para métodos de cobro"""
    
    print("Iniciando creación de campos para métodos de cobro...")
    
    # Definir campos para transferencia bancaria
    campos_transferencia = [
        {
            'nombre': 'numero_cuenta',
            'etiqueta': 'Número de Cuenta',
            'tipo': 'text',
            'es_obligatorio': True,
            'max_length': 30,
            'regex_validacion': r'^[0-9]{10,30}$',
            'placeholder': 'Ingrese el número de cuenta',
            'es_activo': True
        },
        {
            'nombre': 'banco',
            'etiqueta': 'Banco',
            'tipo': 'select',
            'es_obligatorio': True,
            'opciones': 'Sudameris\nFamiliar\nItaú\nBNF\nGBN Continental\nBanco Nacional\nBanco Regional\nBanco Visión',
            'es_activo': True
        },
        {
            'nombre': 'titular',
            'etiqueta': 'Titular de la Cuenta',
            'tipo': 'text',
            'es_obligatorio': True,
            'max_length': 100,
            'placeholder': 'Nombre completo del titular',
            'es_activo': True
        }
    ]
    
    # Definir campos para billetera electrónica
    campos_billetera = [
        {
            'nombre': 'numero_telefono',
            'etiqueta': 'Número de Teléfono',
            'tipo': 'phone',
            'es_obligatorio': True,
            'max_length': 15,
            'regex_validacion': r'^[0-9]{9,15}$',
            'placeholder': '0981 123 456',
            'es_activo': True
        }
    ]
    
    # Crear campos
    campos_creados = {}
    
    for campo_data in campos_transferencia + campos_billetera:
        campo, created = Campo.objects.get_or_create(
            nombre=campo_data['nombre'],
            defaults=campo_data
        )
        if created:
            print(f"✓ Campo creado: {campo.nombre}")
        else:
            print(f"✓ Campo ya existe: {campo.nombre}")
        
        campos_creados[campo.nombre] = campo
    
    return campos_creados


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
    
    # Obtener campos creados
    campos_creados = crear_campos_metodos_cobro()
    
    # Definir los métodos de cobro
    metodos_data = [
        {
            'nombre': 'Transferencia bancaria',
            'descripcion': 'Transferencia bancaria local',
            'comision': Decimal('1.00'),
            'monedas': [pyg],
            'campos': ['numero_cuenta', 'banco', 'titular']
        },
        {
            'nombre': 'Tarjeta de débito',
            'descripcion': 'Pago con tarjeta de débito',
            'comision': Decimal('1.50'),
            'monedas': [pyg],
            'campos': []
        },
        {
            'nombre': 'Billetera electrónica',
            'descripcion': 'Pago mediante billetera electrónica',
            'comision': Decimal('2.00'),
            'monedas': [pyg],
            'campos': ['numero_telefono']
        },
        {
            'nombre': 'Tarjeta de crédito',
            'descripcion': 'Pago con tarjeta de crédito',
            'comision': Decimal('3.00'),
            'monedas': [pyg, usd],
            'campos': []
        },
        {
            'nombre': 'Tarjeta de crédito local',
            'descripcion': 'Pago con tarjeta de crédito local (Panal, Cabal)',
            'comision': Decimal('2.50'),
            'monedas': [pyg],
            'campos': []
        },
        {
            'nombre': 'Efectivo',
            'descripcion': 'Pago en efectivo',
            'comision': Decimal('0.00'),
            'monedas': list(todas_monedas_excepto_pyg),
            'campos': []
        }
    ]
    
    # Crear cada método de cobro
    for metodo_data in metodos_data:
        metodo, created = MetodoCobro.objects.get_or_create(
            nombre=metodo_data['nombre'],
            defaults={
                'descripcion': metodo_data['descripcion'],
                'comision': metodo_data['comision'],
                'es_activo': True
            }
        )
        
        # Agregar las monedas permitidas
        metodo.monedas_permitidas.set(metodo_data['monedas'])
        
        # Agregar campos si existen
        if metodo_data['campos']:
            campos_metodo = [campos_creados[nombre] for nombre in metodo_data['campos'] if nombre in campos_creados]
            metodo.campos.set(campos_metodo)
            print(f"✓ Asociados {len(campos_metodo)} campos a {metodo.nombre}")
        
        if created:
            print(f"✓ Creado: {metodo.nombre}")
        else:
            print(f"✓ Ya existe: {metodo.nombre} (actualizado)")
    
    print(f"\n¡Métodos de cobro creados exitosamente!")
    print(f"Total de métodos: {MetodoCobro.objects.count()}")
    return True


if __name__ == '__main__':
    crear_metodos_cobro()