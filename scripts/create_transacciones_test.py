#!/usr/bin/env python3
"""
Script para poblar la base de datos con transacciones de ejemplo.
Crea múltiples transacciones para operadores con diferentes estados y tipos.
Útil para desarrollo y testing del dashboard de transacciones.
"""

import os
import sys
import django
from decimal import Decimal, ROUND_HALF_UP
import random
from datetime import datetime, timedelta

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'global_exchange.settings')
django.setup()

from transacciones.models import Transaccion, TipoOperacion, EstadoTransaccion
from clientes.models import Cliente
from usuarios.models import Usuario
from monedas.models import Moneda
from metodo_pago.models import MetodoPago
from metodo_cobro.models import MetodoCobro
from tasa_cambio.models import TasaCambio
from tauser.models import Tauser
from django.contrib.auth.models import Group
from django.utils import timezone


def obtener_operadores():
    """Obtener usuarios del grupo Operador"""
    try:
        grupo_operador = Group.objects.get(name='Operador')
        operadores = Usuario.objects.filter(groups=grupo_operador, es_activo=True)
        return list(operadores)
    except Group.DoesNotExist:
        print("  ⚠️  Grupo 'Operador' no encontrado")
        return []


def obtener_datos_requeridos():
    """Obtener todos los datos necesarios para crear transacciones"""
    print("📋 Obteniendo datos necesarios...")

    # Operadores
    operadores = obtener_operadores()
    if not operadores:
        print("  ❌ No se encontraron operadores")
        return None

    # Tipos de operación
    tipos_operacion = list(TipoOperacion.objects.filter(activo=True))
    if not tipos_operacion:
        print("  ❌ No se encontraron tipos de operación")
        return None

    # Estados de transacción
    estados = list(EstadoTransaccion.objects.filter(activo=True))
    if not estados:
        print("  ❌ No se encontraron estados de transacción")
        return None

    # Clientes activos
    clientes = list(Cliente.objects.filter(activo=True))
    if not clientes:
        print("  ❌ No se encontraron clientes")
        return None

    # Monedas activas
    monedas = list(Moneda.objects.filter(es_activa=True))
    pyg = None
    try:
        pyg = Moneda.objects.get(codigo='PYG', es_activa=True)
    except Moneda.DoesNotExist:
        print("  ❌ No se encontró la moneda PYG")
        return None

    # Métodos de pago y cobro
    metodos_pago = list(MetodoPago.objects.filter(es_activo=True))
    metodos_cobro = list(MetodoCobro.objects.filter(es_activo=True))

    # Tasas de cambio activas
    tasas_cambio = list(TasaCambio.objects.filter(es_activa=True))
    if not tasas_cambio:
        print("  ❌ No se encontraron tasas de cambio")
        return None

    # Tausers activos
    tausers = list(Tauser.objects.filter(es_activo=True))
    if not tausers:
        print("  ❌ No se encontraron Tausers activos")
        return None

    print(f"  👥 {len(operadores)} operadores encontrados")
    print(f"  📊 {len(tipos_operacion)} tipos de operación")
    print(f"  🏷️  {len(estados)} estados de transacción")
    print(f"  👤 {len(clientes)} clientes activos")
    print(f"  💰 {len(monedas)} monedas activas")
    print(f"  📈 {len(tasas_cambio)} tasas de cambio")
    print(f"  🏪 {len(tausers)} Tausers activos")

    return {
        'operadores': operadores,
        'tipos_operacion': tipos_operacion,
        'estados': estados,
        'clientes': clientes,
        'monedas': monedas,
        'pyg': pyg,
        'metodos_pago': metodos_pago,
        'metodos_cobro': metodos_cobro,
        'tasas_cambio': tasas_cambio,
        'tausers': tausers
    }


def obtener_tasa_para_monedas(moneda_origen, moneda_destino, tasas_cambio):
    """Obtener tasa de cambio entre dos monedas"""
    if moneda_origen.codigo == 'PYG':
        # Comprando divisa extranjera con PYG
        tasa = next((t for t in tasas_cambio if t.moneda.codigo == moneda_destino.codigo), None)
        if tasa:
            return tasa.precio_base + tasa.comision_venta
    else:
        # Vendiendo divisa extranjera por PYG
        tasa = next((t for t in tasas_cambio if t.moneda.codigo == moneda_origen.codigo), None)
        if tasa:
            return tasa.precio_base - tasa.comision_compra

    # Tasa por defecto si no se encuentra
    return Decimal('7500')


def generar_fecha_realista():
    """
    Generar fecha realista con distribución inteligente:
    - 40% últimos 7 días (más actividad reciente)
    - 30% días 8-21 (actividad media)
    - 30% días 22-30 (actividad pasada)
    - Evitar fines de semana para el 70% de transacciones
    - Horarios de oficina más probables
    """
    # Distribución por períodos
    rand = random.random()
    if rand < 0.4:
        # 40% en últimos 7 días
        dias_atras = random.randint(0, 7)
    elif rand < 0.7:
        # 30% en días 8-21
        dias_atras = random.randint(8, 21)
    else:
        # 30% en días 22-30
        dias_atras = random.randint(22, 30)

    # Calcular fecha base
    fecha_base = timezone.now().date() - timedelta(days=dias_atras)

    # 70% en días laborables, 30% fines de semana
    if random.random() < 0.7:
        # Buscar día laborable más cercano
        while fecha_base.weekday() in [5, 6]:  # Sábado=5, Domingo=6
            if random.choice([True, False]):
                fecha_base -= timedelta(days=1)
            else:
                fecha_base += timedelta(days=1)

    # Horarios más realistas
    if fecha_base.weekday() in [5, 6]:
        # Fines de semana: horarios más variados
        hora = random.choice([10, 11, 14, 15, 16, 17, 18, 19, 20])
    else:
        # Días laborables: horarios de oficina principalmente
        hora = random.choices(
            [9, 10, 11, 12, 14, 15, 16, 17, 18],
            weights=[5, 10, 15, 10, 15, 15, 15, 10, 5]
        )[0]

    minuto = random.choice([0, 15, 30, 45])

    # Crear datetime
    fecha_final = timezone.make_aware(
        datetime.combine(fecha_base, datetime.min.time().replace(hour=hora, minute=minuto))
    )

    return fecha_final


def crear_transacciones_ejemplo(datos, cantidad=100):
    """Crear transacciones de ejemplo variadas"""
    print(f"\n💱 Creando {cantidad} transacciones de ejemplo...")

    transacciones_creadas = 0
    errores = 0

    # Distribución de estados (realista)
    distribucion_estados = [
        ('PAGADA', 60),    # 60% pagadas
        ('PENDIENTE', 25), # 25% pendientes
        ('CANCELADA', 10), # 10% canceladas
        ('ANULADA', 5)     # 5% anuladas
    ]

    # Distribución de tipos
    distribucion_tipos = [
        ('COMPRA', 70),    # 70% compras (más común)
        ('VENTA', 30)      # 30% ventas
    ]

    for i in range(cantidad):
        try:
            # Seleccionar operador aleatorio
            operador = random.choice(datos['operadores'])

            # Seleccionar cliente aleatorio (80% con cliente, 20% casual)
            cliente = random.choice(datos['clientes']) if random.random() > 0.2 else None

            # Seleccionar tipo de operación
            tipo_operacion = random.choices(
                [t for t in datos['tipos_operacion'] if t.codigo in ['COMPRA', 'VENTA']],
                weights=[70, 30]
            )[0]

            # Seleccionar estado
            estado_codigo = random.choices(
                [estado for estado, peso in distribucion_estados],
                weights=[peso for estado, peso in distribucion_estados]
            )[0]
            estado = next(e for e in datos['estados'] if e.codigo == estado_codigo)

            # Configurar monedas según tipo de operación
            if tipo_operacion.codigo == 'COMPRA':
                # Cliente compra divisa extranjera con PYG
                moneda_origen = datos['pyg']
                moneda_destino = random.choice([m for m in datos['monedas'] if m.codigo != 'PYG'])
            else:
                # Cliente vende divisa extranjera por PYG
                moneda_origen = random.choice([m for m in datos['monedas'] if m.codigo != 'PYG'])
                moneda_destino = datos['pyg']

            # Calcular montos realistas
            if moneda_origen.codigo == 'PYG':
                # Monto en PYG (origen)
                monto_origen = Decimal(str(random.randint(100000, 5000000)))  # 100k - 5M PYG
            else:
                # Monto en moneda extranjera (origen)
                monto_origen = Decimal(str(random.randint(50, 2000)))  # 50 - 2000 USD/EUR/etc

            # Obtener tasa de cambio
            tasa_cambio = obtener_tasa_para_monedas(moneda_origen, moneda_destino, datos['tasas_cambio'])

            # Calcular monto destino
            if moneda_origen.codigo == 'PYG':
                # PYG -> Divisa extranjera
                monto_destino = (monto_origen / tasa_cambio).quantize(Decimal('1'), rounding=ROUND_HALF_UP)
            else:
                # Divisa extranjera -> PYG
                monto_destino = (monto_origen * tasa_cambio).quantize(Decimal('1'), rounding=ROUND_HALF_UP)

            # Seleccionar métodos de pago/cobro
            metodo_cobro = random.choice(datos['metodos_cobro']) if datos['metodos_cobro'] else None
            metodo_pago = random.choice(datos['metodos_pago']) if datos['metodos_pago'] else None

            # Seleccionar Tauser (30% de transacciones con Tauser)
            tauser = random.choice(datos['tausers']) if random.random() < 0.3 else None

            # Calcular comisiones básicas
            porcentaje_comision = Decimal(random.randint(1, 3))
            monto_comision = (monto_origen * porcentaje_comision / 100).quantize(Decimal('1'), rounding=ROUND_HALF_UP)

            # Descuento del cliente
            porcentaje_descuento = Decimal('0')
            monto_descuento = Decimal('0')
            if cliente and cliente.tipo_cliente:
                porcentaje_descuento = cliente.tipo_cliente.descuento
                monto_descuento_bruto = (monto_comision * porcentaje_descuento / 100)
                monto_descuento = monto_descuento_bruto.quantize(Decimal('1'), rounding=ROUND_HALF_UP)
                if monto_descuento_bruto > 0 and monto_descuento == 0:
                    monto_descuento = Decimal('1')

            # Generar fecha realista
            fecha_creacion = generar_fecha_realista()
            fecha_expiracion = fecha_creacion + timedelta(minutes=5)

            # Fecha de pago para transacciones pagadas
            fecha_pago = None
            if estado.codigo == 'PAGADA':
                fecha_pago = fecha_creacion + timedelta(minutes=random.randint(1, 10))

            # Crear transacción
            transaccion = Transaccion.objects.create(
                cliente=cliente,
                tauser=tauser,
                usuario=operador,
                tipo_operacion=tipo_operacion,
                moneda_origen=moneda_origen,
                moneda_destino=moneda_destino,
                monto_origen=monto_origen,
                monto_destino=monto_destino,
                metodo_cobro=metodo_cobro,
                metodo_pago=metodo_pago,
                tasa_cambio=tasa_cambio,
                porcentaje_comision=porcentaje_comision,
                monto_comision=monto_comision,
                porcentaje_descuento=porcentaje_descuento,
                monto_descuento=monto_descuento,
                estado=estado,
                fecha_expiracion=fecha_expiracion,
                fecha_pago=fecha_pago,
                observaciones=f"Transacción de ejemplo #{i+1}" + (f" - Procesada en {tauser.nombre}" if tauser else ""),
                ip_cliente="127.0.0.1"
            )

            # IMPORTANTE: Actualizar fechas después de la creación
            # porque auto_now_add=True ignora valores pasados
            Transaccion.objects.filter(pk=transaccion.pk).update(
                fecha_creacion=fecha_creacion,
                fecha_actualizacion=fecha_creacion
            )

            transacciones_creadas += 1

            if (i + 1) % 20 == 0:
                print(f"  📈 {i + 1}/{cantidad} transacciones creadas...")

        except Exception as e:
            errores += 1
            print(f"  ❌ Error creando transacción {i+1}: {str(e)}")
            continue

    print(f"\n📊 Resumen de creación:")
    print(f"  • Transacciones creadas: {transacciones_creadas}")
    print(f"  • Errores: {errores}")

    return transacciones_creadas


def mostrar_estadisticas():
    """Mostrar estadísticas de transacciones creadas"""
    print("\n📊 Estadísticas de transacciones:")

    # Por operador
    operadores = obtener_operadores()
    for operador in operadores:
        count = Transaccion.objects.filter(usuario=operador).count()
        print(f"  • {operador.nombre}: {count} transacción(es)")

    # Por estado
    print(f"\n📋 Por estado:")
    for estado in EstadoTransaccion.objects.filter(activo=True):
        count = Transaccion.objects.filter(estado=estado).count()
        print(f"  • {estado.nombre}: {count} transacción(es)")

    # Por tipo
    print(f"\n🔄 Por tipo de operación:")
    for tipo in TipoOperacion.objects.filter(activo=True):
        count = Transaccion.objects.filter(tipo_operacion=tipo).count()
        print(f"  • {tipo.nombre}: {count} transacción(es)")

    # Totales
    total = Transaccion.objects.count()
    con_cliente = Transaccion.objects.filter(cliente__isnull=False).count()
    casuales = total - con_cliente
    con_tauser = Transaccion.objects.filter(tauser__isnull=False).count()

    print(f"\n📈 Resumen general:")
    print(f"  • Total transacciones: {total}")
    print(f"  • Con cliente: {con_cliente}")
    print(f"  • Casuales: {casuales}")
    print(f"  • Con Tauser: {con_tauser}")

    # Por Tauser
    print(f"\n🏪 Por Tauser:")
    for tauser in Tauser.objects.filter(es_activo=True):
        count = Transaccion.objects.filter(tauser=tauser).count()
        if count > 0:
            print(f"  • {tauser.nombre}: {count} transacción(es)")

    # Últimas 30 días
    desde_30_dias = timezone.now().date() - timedelta(days=30)
    recientes = Transaccion.objects.filter(fecha_creacion__date__gte=desde_30_dias).count()
    print(f"  • Últimos 30 días: {recientes}")


def verificar_datos():
    """Verificar que los datos se crearon correctamente"""
    print("\n🔍 Verificando datos creados...")

    total_transacciones = Transaccion.objects.count()
    operadores_con_transacciones = Usuario.objects.filter(
        transacciones_realizadas__isnull=False
    ).distinct().count()

    print(f"  ✅ {total_transacciones} transacciones en total")
    print(f"  ✅ {operadores_con_transacciones} operadores con transacciones")

    if total_transacciones > 0 and operadores_con_transacciones > 0:
        print(f"\n  ✅ Datos creados correctamente")
        return True
    else:
        print(f"\n  ❌ Error en la creación de datos")
        return False


def main():
    """Función principal del script"""
    print("🚀 Iniciando creación de transacciones de ejemplo...")
    print("=" * 65)

    try:
        # Obtener datos necesarios
        datos = obtener_datos_requeridos()
        if not datos:
            print("\n❌ No se pudieron obtener todos los datos necesarios.")
            print("   Asegúrate de ejecutar estos scripts primero:")
            print("   • make create-currencies")
            print("   • make create-payment-methods")
            print("   • make create-collection-methods")
            print("   • make create-groups-users")
            print("   • make create-client-types")
            print("   • make create-clients")
            print("   • make setup-transactions")
            sys.exit(1)

        # Crear transacciones
        cantidad = int(os.environ.get('CANTIDAD_TRANSACCIONES', '150'))  # Por defecto 150
        transacciones_creadas = crear_transacciones_ejemplo(datos, cantidad)

        # Mostrar estadísticas
        mostrar_estadisticas()

        # Verificar datos
        if verificar_datos():
            print("\n🎉 ¡Transacciones de ejemplo creadas exitosamente!")
            print(f"\n📋 Se crearon {transacciones_creadas} transacciones con:")
            print(f"   • Distribución realista de estados (60% pagadas, 25% pendientes, etc.)")
            print(f"   • Tipos de operación variados (70% compras, 30% ventas)")
            print(f"   • Fechas inteligentemente distribuidas (40% últimos 7 días, 30% días 8-21, 30% días 22-30)")
            print(f"   • Horarios de oficina en días laborables, fines de semana ocasionales")
            print(f"   • Clientes asociados (80%) y casuales (20%)")
            print(f"   • Tausers asociados (30% de transacciones)")
            print(f"   • Montos y tasas de cambio realistas")
            print(f"\n🎯 Ahora puedes probar:")
            print(f"   • Dashboard de 'Mis transacciones'")
            print(f"   • Estado de retiro en transacciones")
            print(f"   • Sistema de Tausers y stock")
        else:
            print("\n❌ Error al crear las transacciones.")
            sys.exit(1)

    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
