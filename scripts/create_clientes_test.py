#!/usr/bin/env python3
"""
Script para poblar la base de datos con clientes de ejemplo.
Crea clientes con tipos asignados y operadores asociados.
Útil para desarrollo y testing.
"""

import os
import sys
import django
from decimal import Decimal
import random

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'global_exchange.settings')
django.setup()

from clientes.models import Cliente, TipoCliente
from usuarios.models import Usuario
from django.contrib.auth.models import Group


def obtener_operadores():
    """Obtener usuarios del grupo Operador"""
    try:
        grupo_operador = Group.objects.get(name='Operador')
        operadores = Usuario.objects.filter(groups=grupo_operador, es_activo=True)
        return list(operadores)
    except Group.DoesNotExist:
        print("  ⚠️  Grupo 'Operador' no encontrado")
        return []


def obtener_tipos_cliente():
    """Obtener tipos de cliente disponibles"""
    tipos = TipoCliente.objects.filter(activo=True).order_by('nombre')
    return list(tipos)


def crear_clientes_ejemplo():
    """Crear clientes de ejemplo con tipos y operadores asignados"""

    print("👤 Obteniendo datos necesarios...")
    operadores = obtener_operadores()
    tipos_cliente = obtener_tipos_cliente()

    if not tipos_cliente:
        print("  ❌ No se encontraron tipos de cliente. Ejecuta 'make create-client-types' primero.")
        return 0

    if not operadores:
        print("  ⚠️  No se encontraron operadores. Los clientes se crearán sin operadores asignados.")

    print(f"  📋 {len(tipos_cliente)} tipos de cliente disponibles")
    print(f"  👥 {len(operadores)} operadores disponibles")

    # Datos de clientes de ejemplo
    clientes_datos = [
        # Clientes VIP
        {
            'nombre_comercial': 'Inversiones Premium S.A.',
            'ruc': '80001234567',
            'direccion': 'Av. Mariscal López 3400, Asunción',
            'correo_electronico': 'contacto@inversionespremium.com.py',
            'numero_telefono': '+595 21 123-4567',
            'tipo_cliente_nombre': 'VIP',
            'monto_limite_transaccion': Decimal('500000.00')
        },
        {
            'nombre_comercial': 'Corporación Global Trading',
            'ruc': '80001234568',
            'direccion': 'World Trade Center, Torre A, Piso 15',
            'correo_electronico': 'admin@globaltrading.com.py',
            'numero_telefono': '+595 21 234-5678',
            'tipo_cliente_nombre': 'VIP',
            'monto_limite_transaccion': Decimal('1000000.00')
        },
        {
            'nombre_comercial': 'Elite Finance Group',
            'ruc': '80001234569',
            'direccion': 'Av. República Argentina 1234, Asunción',
            'correo_electronico': 'info@elitefinance.com.py',
            'numero_telefono': '+595 21 345-6789',
            'tipo_cliente_nombre': 'VIP',
            'monto_limite_transaccion': Decimal('750000.00')
        },

        # Clientes Corporativos
        {
            'nombre_comercial': 'Importadora del Este S.R.L.',
            'ruc': '80002234567',
            'direccion': 'Ruta 2, Km 30, Ciudad del Este',
            'correo_electronico': 'ventas@importadoraeste.com.py',
            'numero_telefono': '+595 61 456-7890',
            'tipo_cliente_nombre': 'Corporativo',
            'monto_limite_transaccion': Decimal('300000.00')
        },
        {
            'nombre_comercial': 'Constructora San Miguel S.A.',
            'ruc': '80002234568',
            'direccion': 'Av. Eusebio Ayala 2100, Asunción',
            'correo_electronico': 'proyectos@sanmiguel.com.py',
            'numero_telefono': '+595 21 567-8901',
            'tipo_cliente_nombre': 'Corporativo',
            'monto_limite_transaccion': Decimal('400000.00')
        },
        {
            'nombre_comercial': 'Agropecuaria del Sur S.A.',
            'ruc': '80002234569',
            'direccion': 'Ruta 1, Km 45, Encarnación',
            'correo_electronico': 'administracion@agrosur.com.py',
            'numero_telefono': '+595 71 678-9012',
            'tipo_cliente_nombre': 'Corporativo',
            'monto_limite_transaccion': Decimal('250000.00')
        },
        {
            'nombre_comercial': 'Textil Paraguay S.R.L.',
            'ruc': '80002234570',
            'direccion': 'Zona Industrial, Luque',
            'correo_electronico': 'gerencia@textilpy.com.py',
            'numero_telefono': '+595 21 789-0123',
            'tipo_cliente_nombre': 'Corporativo',
            'monto_limite_transaccion': Decimal('200000.00')
        },

        # Clientes Minoristas
        {
            'nombre_comercial': 'Ferretería Central',
            'ruc': '80003234567',
            'direccion': 'Av. Pettirossi 1500, Asunción',
            'correo_electronico': 'info@ferreteriacentral.com.py',
            'numero_telefono': '+595 21 890-1234',
            'tipo_cliente_nombre': 'Minorista',
            'monto_limite_transaccion': Decimal('50000.00')
        },
        {
            'nombre_comercial': 'Boutique Elegance',
            'ruc': '80003234568',
            'direccion': 'Shopping del Sol, Local 45',
            'correo_electronico': 'ventas@elegance.com.py',
            'numero_telefono': '+595 21 901-2345',
            'tipo_cliente_nombre': 'Minorista',
            'monto_limite_transaccion': Decimal('30000.00')
        },
        {
            'nombre_comercial': 'Librería Universitaria',
            'ruc': '80003234569',
            'direccion': 'Av. España 1234, Asunción',
            'correo_electronico': 'pedidos@libreriauni.com.py',
            'numero_telefono': '+595 21 012-3456',
            'tipo_cliente_nombre': 'Minorista',
            'monto_limite_transaccion': Decimal('25000.00')
        },
        {
            'nombre_comercial': 'Farmacia San José',
            'ruc': '80003234570',
            'direccion': 'Av. Brasil 890, Asunción',
            'correo_electronico': 'contacto@farmaciasanjose.com.py',
            'numero_telefono': '+595 21 123-4567',
            'tipo_cliente_nombre': 'Minorista',
            'monto_limite_transaccion': Decimal('40000.00')
        },
        {
            'nombre_comercial': 'Restaurante Don Carlos',
            'ruc': '80003234571',
            'direccion': 'Av. Santísimo Sacramento 567, Asunción',
            'correo_electronico': 'reservas@doncarlos.com.py',
            'numero_telefono': '+595 21 234-5678',
            'tipo_cliente_nombre': 'Minorista',
            'monto_limite_transaccion': Decimal('35000.00')
        },
        {
            'nombre_comercial': 'Autopartes Mecánico',
            'ruc': '80003234572',
            'direccion': 'Av. Artigas 2300, Asunción',
            'correo_electronico': 'ventas@autopartesmecanico.com.py',
            'numero_telefono': '+595 21 345-6789',
            'tipo_cliente_nombre': 'Minorista',
            'monto_limite_transaccion': Decimal('60000.00')
        }
    ]

    print(f"\n👤 Creando {len(clientes_datos)} clientes de ejemplo...")
    clientes_creados = 0
    operadores_asignados = 0

    for datos in clientes_datos:
        tipo_nombre = datos.pop('tipo_cliente_nombre')

        # Verificar si el cliente ya existe
        cliente_existente = Cliente.objects.filter(ruc=datos['ruc']).first()

        if cliente_existente:
            print(f"  ℹ️  Cliente ya existe: {cliente_existente.nombre_comercial} ({cliente_existente.ruc})")
            continue

        # Obtener el tipo de cliente
        try:
            tipo_cliente = TipoCliente.objects.get(nombre=tipo_nombre, activo=True)
        except TipoCliente.DoesNotExist:
            print(f"  ❌ Tipo de cliente '{tipo_nombre}' no encontrado")
            continue

        # Crear el cliente
        try:
            cliente = Cliente.objects.create(
                tipo_cliente=tipo_cliente,
                **datos
            )

            # Asignar operadores aleatoriamente
            if operadores:
                # Asignar 1-2 operadores por cliente
                num_operadores = random.randint(1, min(2, len(operadores)))
                operadores_seleccionados = random.sample(operadores, num_operadores)

                cliente.usuarios_asociados.set(operadores_seleccionados)
                operadores_nombres = [op.nombre for op in operadores_seleccionados]

                print(f"  ✅ Cliente creado: {cliente.nombre_comercial}")
                print(f"    └── Tipo: {tipo_cliente.nombre} ({tipo_cliente.descuento}% desc.)")
                print(f"    └── Operadores: {', '.join(operadores_nombres)}")

                operadores_asignados += len(operadores_seleccionados)
            else:
                print(f"  ✅ Cliente creado: {cliente.nombre_comercial} (sin operadores)")
                print(f"    └── Tipo: {tipo_cliente.nombre} ({tipo_cliente.descuento}% desc.)")

            clientes_creados += 1

        except Exception as e:
            print(f"  ❌ Error creando cliente {datos['nombre_comercial']}: {e}")

    return clientes_creados, operadores_asignados


def mostrar_estadisticas():
    """Mostrar estadísticas de clientes creados"""
    print("\n📊 Estadísticas de clientes:")

    for tipo in TipoCliente.objects.filter(activo=True).order_by('nombre'):
        count = Cliente.objects.filter(tipo_cliente=tipo, activo=True).count()
        print(f"  • {tipo.nombre}: {count} cliente(s) ({tipo.descuento}% descuento)")

    total_clientes = Cliente.objects.filter(activo=True).count()
    clientes_con_operadores = Cliente.objects.filter(activo=True, usuarios_asociados__isnull=False).distinct().count()

    print(f"\n📈 Resumen general:")
    print(f"  • Total clientes activos: {total_clientes}")
    print(f"  • Clientes con operadores: {clientes_con_operadores}")


def verificar_datos():
    """Verificar que los datos se crearon correctamente"""
    print("\n🔍 Verificando datos creados...")

    tipos_requeridos = ['VIP', 'Minorista', 'Corporativo']
    clientes_por_tipo = {}

    for tipo_nombre in tipos_requeridos:
        try:
            tipo = TipoCliente.objects.get(nombre=tipo_nombre, activo=True)
            count = Cliente.objects.filter(tipo_cliente=tipo, activo=True).count()
            clientes_por_tipo[tipo_nombre] = count
            print(f"  ✅ {tipo_nombre}: {count} cliente(s)")
        except TipoCliente.DoesNotExist:
            print(f"  ❌ Tipo {tipo_nombre} no encontrado")
            clientes_por_tipo[tipo_nombre] = 0

    total_esperado = sum(clientes_por_tipo.values())
    if total_esperado > 0:
        print(f"\n  ✅ {total_esperado} clientes creados exitosamente")
        return True
    else:
        print(f"\n  ❌ No se crearon clientes")
        return False


def main():
    """Función principal del script"""
    print("🚀 Iniciando creación de clientes de ejemplo...")
    print("=" * 60)

    try:
        # Crear clientes
        clientes_creados, operadores_asignados = crear_clientes_ejemplo()

        # Mostrar estadísticas
        mostrar_estadisticas()

        # Verificar datos
        if verificar_datos():
            print("\n🎉 ¡Clientes creados exitosamente!")
            print(f"\n📋 Resumen de la operación:")
            print(f"   • Clientes creados: {clientes_creados}")
            if operadores_asignados > 0:
                print(f"   • Asignaciones operador-cliente: {operadores_asignados}")
            print(f"\n💼 Tipos de cliente utilizados:")
            print(f"   • VIP: Límites altos, 15% descuento")
            print(f"   • Corporativo: Límites medios-altos, 10% descuento")
            print(f"   • Minorista: Límites menores, 5% descuento")
            print(f"\n🔗 Los clientes están asociados con operadores para simulaciones")
        else:
            print("\n❌ Error al crear los clientes.")
            sys.exit(1)

    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()