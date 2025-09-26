#!/usr/bin/env python3
"""
Script para poblar la base de datos con tipos de cliente de ejemplo.
Útil para desarrollo y testing.
"""

import os
import sys
import django
from decimal import Decimal

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'global_exchange.settings')
django.setup()

from clientes.models import TipoCliente


def crear_tipos_cliente_ejemplo():
    """Crear tipos de cliente específicos del negocio"""

    tipos_datos = [
        {
            'nombre': 'VIP',
            'descripcion': 'Clientes premium con descuentos preferenciales y servicios exclusivos',
            'descuento': Decimal('15.00'),  # 15% de descuento
            'activo': True
        },
        {
            'nombre': 'Minorista',
            'descripcion': 'Clientes comerciales minoristas para transacciones de volumen medio',
            'descuento': Decimal('5.00'),   # 5% de descuento
            'activo': True
        },
        {
            'nombre': 'Corporativo',
            'descripcion': 'Empresas y corporaciones con grandes volúmenes de transacciones',
            'descuento': Decimal('10.00'),  # 10% de descuento
            'activo': True
        }
    ]

    print("👥 Creando tipos de cliente específicos del negocio...")
    creados = 0
    actualizados = 0

    for datos in tipos_datos:
        tipo_existente = TipoCliente.objects.filter(nombre__iexact=datos['nombre']).first()

        if tipo_existente:
            # Verificar si necesita actualización
            campos_actualizados = []

            if tipo_existente.descripcion != datos['descripcion']:
                tipo_existente.descripcion = datos['descripcion']
                campos_actualizados.append('descripción')

            if tipo_existente.descuento != datos['descuento']:
                tipo_existente.descuento = datos['descuento']
                campos_actualizados.append('descuento')

            if not tipo_existente.activo and datos['activo']:
                tipo_existente.activo = datos['activo']
                campos_actualizados.append('estado')

            if campos_actualizados:
                tipo_existente.save()
                print(f"  🔄 Tipo actualizado: {tipo_existente.nombre} ({', '.join(campos_actualizados)})")
                actualizados += 1
            else:
                print(f"  ℹ️  Tipo ya existe: {tipo_existente.nombre} ({tipo_existente.descuento}% descuento)")
        else:
            # Crear nuevo tipo
            nuevo_tipo = TipoCliente.objects.create(**datos)
            print(f"  ✅ Tipo creado: {nuevo_tipo.nombre} ({nuevo_tipo.descuento}% descuento)")
            creados += 1

    print(f"\n📊 Resumen:")
    print(f"  • Tipos creados: {creados}")
    print(f"  • Tipos actualizados: {actualizados}")
    print(f"  • Total procesados: {len(tipos_datos)}")

    return creados + actualizados


def mostrar_tipos_configurados():
    """Mostrar resumen de tipos de cliente configurados"""
    print("\n👥 Tipos de cliente configurados:")

    tipos_activos = TipoCliente.objects.filter(activo=True).order_by('nombre')

    for tipo in tipos_activos:
        print(f"  • {tipo.nombre}: {tipo.descuento}% descuento")
        if tipo.descripcion:
            print(f"    └── {tipo.descripcion}")

    print(f"\n📈 Estadísticas:")
    print(f"  • Tipos activos: {tipos_activos.count()}")
    print(f"  • Tipos totales: {TipoCliente.objects.count()}")


def verificar_datos():
    """Verificar que los datos se crearon correctamente"""
    print("\n🔍 Verificando datos creados...")

    tipos_requeridos = ['VIP', 'Minorista', 'Corporativo']
    tipos_encontrados = []

    for nombre_tipo in tipos_requeridos:
        tipo = TipoCliente.objects.filter(nombre__iexact=nombre_tipo, activo=True).first()
        if tipo:
            tipos_encontrados.append(tipo.nombre)
            print(f"  ✅ {tipo.nombre}: {tipo.descuento}% descuento")
        else:
            print(f"  ❌ {nombre_tipo}: No encontrado o inactivo")

    if len(tipos_encontrados) == len(tipos_requeridos):
        print("\n  ✅ Todos los tipos requeridos están disponibles")
        return True
    else:
        print(f"\n  ⚠️  Solo {len(tipos_encontrados)}/{len(tipos_requeridos)} tipos encontrados")
        return False


def main():
    """Función principal del script"""
    print("🚀 Iniciando creación de tipos de cliente...")
    print("=" * 55)

    try:
        # Crear tipos de cliente
        tipos_procesados = crear_tipos_cliente_ejemplo()

        # Mostrar configuración
        mostrar_tipos_configurados()

        # Verificar datos
        if verificar_datos():
            print("\n🎉 ¡Tipos de cliente configurados exitosamente!")
            print("\n💼 Tipos disponibles:")
            print("   • VIP: 15% descuento - Clientes premium")
            print("   • Minorista: 5% descuento - Comercios minoristas")
            print("   • Corporativo: 10% descuento - Empresas corporativas")
            print("\n📝 Los tipos pueden ser asignados a clientes para aplicar descuentos automáticos")
        else:
            print("\n❌ Error al crear los tipos de cliente.")
            sys.exit(1)

    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()