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

from metodo_pago.models import MetodoPago, Campo
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
            "requiere_retiro_fisico": False,  # Transferencia = No requiere retiro físico
            "monedas_permitidas": [pyg]  # Solo PYG
        },
        {
            "nombre": "Billetera electrónica",
            "descripcion": "Pago mediante billeteras digitales (Solo PYG)",
            "comision": Decimal('1.00'),
            "es_activo": True,
            "requiere_retiro_fisico": False,  # Digital = No requiere retiro físico
            "monedas_permitidas": [pyg]  # Solo PYG
        },
        {
            "nombre": "Efectivo",
            "descripcion": "Entrega de dinero en efectivo (Todas las monedas)",
            "comision": Decimal('0.00'),
            "es_activo": True,
            "requiere_retiro_fisico": True,  # Efectivo = Requiere retiro físico
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
            if existing.requiere_retiro_fisico != datos["requiere_retiro_fisico"]:
                existing.requiere_retiro_fisico = datos["requiere_retiro_fisico"]
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
        retiro_text = "Requiere retiro físico" if metodo.requiere_retiro_fisico else "No requiere retiro físico"
        print(f"  • {metodo.nombre}: {monedas if monedas else 'Sin monedas'} - {retiro_text}")
    
    return creados


def crear_campos_metodos_pago():
    """Crear campos específicos para cada método de pago"""
    
    # Campos para Billetera Electrónica
    campos_billetera = [
        {
            'nombre': 'numero_telefono',
            'etiqueta': 'Número de Teléfono',
            'tipo': 'phone',
            'es_obligatorio': True,
            'max_length': 15,
            'regex_validacion': r'^\+?[1-9]\d{1,14}$',
            'placeholder': 'Ej: +595981234567'
        },
    ]
    
    # Campos para Pago en Cuenta Bancaria
    campos_bancario = [
        {
            'nombre': 'documento',
            'etiqueta': 'CI/RUC',
            'tipo': 'text',
            'es_obligatorio': True,
            'max_length': 10,
            'regex_validacion': r'^[0-9]{6,10}(-[0-9]{1})?$',
            'placeholder': 'CI/RUC'
        },
        {
            'nombre': 'numero_cuenta',
            'etiqueta': 'Número de Cuenta',
            'tipo': 'text',
            'es_obligatorio': True,
            'max_length': 30,
            'regex_validacion': r'^[0-9]{10,30}$',
            'placeholder': 'Número de cuenta bancaria'
        },
        {
            'nombre': 'titular',
            'etiqueta': 'Titular de la Cuenta',
            'tipo': 'text',
            'es_obligatorio': True,
            'max_length': 100,
            'placeholder': 'Nombre completo del titular'
        },
        {
            'nombre': 'banco',
            'etiqueta': 'Banco',
            'tipo': 'select',
            'es_obligatorio': True,
            'opciones': 'Sudameris\nFamiliar\nItaú\nBNF\nGBN Continental\nBanco Nacional\nBanco Regional\nVisión Banco'
        }
    ]
    
    print("\n🔧 Creando campos para métodos de pago...")
    
    # Crear campos para Billetera Electrónica
    print("📱 Campos para Billetera Electrónica:")
    campos_billetera_obj = []
    for campo_data in campos_billetera:
        campo, created = Campo.objects.get_or_create(
            nombre=campo_data['nombre'],
            defaults=campo_data
        )
        campos_billetera_obj.append(campo)
        if created:
            print(f"  ✅ Campo creado: {campo.nombre}")
        else:
            print(f"  ℹ️  Campo ya existe: {campo.nombre}")
    
    # Crear campos para Pago en Cuenta Bancaria
    print("🏦 Campos para Pago en Cuenta Bancaria:")
    campos_bancario_obj = []
    for campo_data in campos_bancario:
        campo, created = Campo.objects.get_or_create(
            nombre=campo_data['nombre'],
            defaults=campo_data
        )
        campos_bancario_obj.append(campo)
        if created:
            print(f"  ✅ Campo creado: {campo.nombre}")
        else:
            print(f"  ℹ️  Campo ya existe: {campo.nombre}")
    
    # Asociar campos a métodos de pago
    print("\n🔗 Asociando campos a métodos de pago...")
    
    # Billetera Electrónica
    try:
        billetera = MetodoPago.objects.get(nombre='Billetera electrónica')
        billetera.campos.set(campos_billetera_obj)
        print(f"  ✅ Campos asociados a Billetera electrónica: {len(campos_billetera_obj)}")
    except MetodoPago.DoesNotExist:
        print("  ❌ Método 'Billetera electrónica' no encontrado")
    
    # Pago en Cuenta Bancaria
    try:
        bancario = MetodoPago.objects.get(nombre='Pago en cuenta bancaria')
        bancario.campos.set(campos_bancario_obj)
        print(f"  ✅ Campos asociados a Pago en cuenta bancaria: {len(campos_bancario_obj)}")
    except MetodoPago.DoesNotExist:
        print("  ❌ Método 'Pago en cuenta bancaria' no encontrado")
    
    # Efectivo no necesita campos
    print("  ℹ️  Efectivo: Sin campos requeridos")


def main():
    try:
        # Crear métodos de pago
        crear_metodos_pago_ejemplo()
        
        # Crear campos asociados
        crear_campos_metodos_pago()
        
        print("\n🎉 ¡Métodos de pago y campos configurados correctamente!")
        print("\n📋 Configuración aplicada:")
        print("   • Pago en cuenta bancaria: Solo PYG + 4 campos")
        print("   • Billetera electrónica: Solo PYG + 2 campos") 
        print("   • Efectivo: Todas las monedas + Sin campos")
        
        # Mostrar resumen final
        print("\n📊 Resumen final:")
        for metodo in MetodoPago.objects.filter(es_activo=True).order_by('nombre'):
            campos_count = metodo.campos.count()
            monedas = ', '.join([m.codigo for m in metodo.monedas_permitidas.all()])
            print(f"   • {metodo.nombre}: {monedas} ({campos_count} campos)")
            
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
