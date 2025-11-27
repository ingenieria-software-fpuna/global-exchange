#!/usr/bin/env python3
"""
Script para crear Tausers de ejemplo con stock de monedas.
Crea múltiples Tausers con stock de al menos 3 monedas y movimientos de historial.
Útil para desarrollo y testing del sistema de Tausers.
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

from tauser.models import Tauser, Stock, HistorialStock, StockDenominacion, HistorialStockDenominacion
from monedas.models import Moneda, DenominacionMoneda
from usuarios.models import Usuario
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
    """Obtener todos los datos necesarios para crear Tausers"""
    print("📋 Obteniendo datos necesarios...")

    operadores = obtener_operadores()
    if not operadores:
        print("  ❌ No se encontraron operadores")
        return None

    monedas = list(Moneda.objects.filter(es_activa=True))
    if len(monedas) < 3:
        print("  ❌ Se necesitan al menos 3 monedas activas")
        return None

    print(f"  👥 {len(operadores)} operadores encontrados")
    print(f"  💰 {len(monedas)} monedas activas")

    return {
        'operadores': operadores,
        'monedas': monedas
    }


def crear_tausers_ejemplo(datos, cantidad=5):
    print(f"\n🏪 Creando {cantidad} Tausers de ejemplo...")

    tausers_creados = 0
    errores = 0

    nombres_tausers = [
        "Casa Central - Asunción",
        "Sucursal Shopping del Sol",
        "Punto Villa Morra",
        "Oficina Ciudad del Este",
        "Kiosco Terminal de Ómnibus",
        "Punto San Lorenzo",
        "Sucursal Lambaré",
        "Oficina Fernando de la Mora"
    ]

    direcciones = [
        "Av. Mariscal López 1234, Asunción",
        "Shopping del Sol, Local 45, Asunción",
        "Av. Mariscal López 5678, Villa Morra",
        "Av. San Blas 9012, Ciudad del Este",
        "Terminal de Ómnibus, Local 23, Asunción",
        "Ruta Mcal. Estigarribia 3456, San Lorenzo",
        "Av. Defensores del Chaco 7890, Lambaré",
        "Ruta Transchaco 1357, Fernando de la Mora"
    ]

    horarios = [
        "Lunes a Viernes: 8:00 - 18:00, Sábados: 8:00 - 12:00",
        "Lunes a Domingo: 9:00 - 21:00",
        "Lunes a Viernes: 7:30 - 19:00, Sábados: 8:00 - 15:00",
        "Lunes a Viernes: 8:00 - 17:30",
        "Lunes a Domingo: 6:00 - 22:00",
        "Lunes a Viernes: 8:00 - 18:00",
        "Lunes a Viernes: 7:00 - 19:00, Sábados: 8:00 - 13:00",
        "Lunes a Viernes: 8:30 - 17:00"
    ]

    for i in range(cantidad):
        try:
            nombre = nombres_tausers[i] if i < len(nombres_tausers) else f"Tauser {i+1}"
            direccion = direcciones[i] if i < len(direcciones) else f"Dirección {i+1}"
            horario = horarios[i] if i < len(horarios) else "Lunes a Viernes: 8:00 - 18:00"

            dias_atras = random.randint(30, 180)
            fecha_instalacion = timezone.now() - timedelta(days=dias_atras)

            tauser = Tauser.objects.create(
                nombre=nombre,
                direccion=direccion,
                horario_atencion=horario,
                es_activo=True,
                fecha_instalacion=fecha_instalacion
            )

            monedas_seleccionadas = random.sample(datos['monedas'], min(3, len(datos['monedas'])))

            for moneda in monedas_seleccionadas:
                denominaciones = DenominacionMoneda.objects.filter(
                    moneda=moneda,
                    es_activa=True,
                    tipo='BILLETE'
                ).order_by('-valor')

                if not denominaciones.exists():
                    print(f"  ⚠️  No hay denominaciones de billetes para {moneda.codigo}, saltando...")
                    continue

                if moneda.codigo == 'PYG':
                    cantidad_inicial = Decimal(str(random.randint(5000000, 20000000)))
                else:
                    cantidad_inicial = Decimal(str(random.randint(1000, 10000)))

                stock = Stock.objects.create(
                    tauser=tauser,
                    moneda=moneda,
                    cantidad=Decimal('0'),
                    es_activo=True
                )

                operador = random.choice(datos['operadores'])

                monto_restante = cantidad_inicial
                denominaciones_distribuidas = []
                denominaciones_ordenadas = list(denominaciones)

                for idx, denominacion in enumerate(denominaciones_ordenadas):
                    if monto_restante <= 0:
                        break

                    if idx == 0:
                        porcentaje = Decimal(str(random.uniform(0.20, 0.30)))
                    elif idx == 1:
                        porcentaje = Decimal(str(random.uniform(0.25, 0.35)))
                    elif idx == 2:
                        porcentaje = Decimal(str(random.uniform(0.20, 0.30)))
                    else:
                        porcentaje = Decimal('1') / Decimal(str(len(denominaciones_ordenadas) - idx))

                    monto_denominacion = (monto_restante * porcentaje).quantize(
                        Decimal('0.01'), rounding=ROUND_HALF_UP
                    )

                    if monto_denominacion > monto_restante:
                        monto_denominacion = monto_restante

                    cantidad_billetes = int(monto_denominacion / denominacion.valor)

                    if cantidad_billetes > 0:
                        valor_total_denominacion = cantidad_billetes * denominacion.valor
                        denominaciones_distribuidas.append({
                            'denominacion': denominacion,
                            'cantidad': cantidad_billetes,
                            'valor_total': valor_total_denominacion
                        })
                        monto_restante -= valor_total_denominacion

                if monto_restante > 0 and denominaciones_distribuidas:
                    ultima = denominaciones_distribuidas[-1]
                    billetes_extra = int(monto_restante / ultima['denominacion'].valor)
                    if billetes_extra > 0:
                        ultima['cantidad'] += billetes_extra
                        ultima['valor_total'] += billetes_extra * ultima['denominacion'].valor
                        monto_restante -= billetes_extra * ultima['denominacion'].valor

                total_distribuido = Decimal('0')
                for item in denominaciones_distribuidas:
                    denominacion = item['denominacion']
                    cantidad_billetes = item['cantidad']
                    valor_total = item['valor_total']

                    stock_denom = StockDenominacion.objects.create(
                        stock=stock,
                        denominacion=denominacion,
                        cantidad=cantidad_billetes,
                        es_activo=True
                    )

                    HistorialStockDenominacion.objects.create(
                        stock_denominacion=stock_denom,
                        tipo_movimiento='ENTRADA',
                        origen_movimiento='MANUAL',
                        cantidad_movida=cantidad_billetes,
                        cantidad_anterior=0,
                        cantidad_posterior=cantidad_billetes,
                        usuario=operador,
                        observaciones=f'Stock inicial - {cantidad_billetes} billetes de {denominacion.valor} {moneda.simbolo}'
                    )

                    total_distribuido += valor_total

                stock.cantidad = total_distribuido.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                stock.save()

                HistorialStock.objects.create(
                    stock=stock,
                    tipo_movimiento='ENTRADA',
                    origen_movimiento='MANUAL',
                    cantidad_movida=total_distribuido,
                    cantidad_anterior=Decimal('0'),
                    cantidad_posterior=total_distribuido,
                    usuario=operador,
                    observaciones=f'Stock inicial creado para {moneda.nombre} por denominaciones - Total: {moneda.simbolo}{total_distribuido:.{moneda.decimales}f}'
                )

                cantidad_actual = total_distribuido

                for j in range(random.randint(2, 5)):
                    dias_mov = random.randint(1, 30)
                    fecha_mov = timezone.now() - timedelta(days=dias_mov)

                    cantidad_anterior = cantidad_actual
                    tipo_movimiento = None
                    observacion = None
                    historial_denom = None

                    if random.random() < 0.7:
                        if denominaciones_distribuidas:
                            item = random.choice(denominaciones_distribuidas)
                            denominacion = item['denominacion']
                            billetes_entrada = random.randint(1, 10)
                            valor_entrada = billetes_entrada * denominacion.valor

                            stock_denom = StockDenominacion.objects.get(
                                stock=stock,
                                denominacion=denominacion
                            )
                            cant_ant = stock_denom.cantidad
                            stock_denom.cantidad += billetes_entrada
                            stock_denom.save()

                            historial_denom = HistorialStockDenominacion.objects.create(
                                stock_denominacion=stock_denom,
                                tipo_movimiento='ENTRADA',
                                origen_movimiento='MANUAL',
                                cantidad_movida=billetes_entrada,
                                cantidad_anterior=cant_ant,
                                cantidad_posterior=stock_denom.cantidad,
                                usuario=operador,
                                observaciones=f'Carga de stock - {billetes_entrada} billetes de {denominacion.valor} {moneda.simbolo}'
                            )

                            cantidad_actual += valor_entrada
                            tipo_movimiento = 'ENTRADA'
                            observacion = f'Carga de stock - {valor_entrada} {moneda.simbolo} ({billetes_entrada} billetes de {denominacion.valor})'
                        else:
                            continue
                    else:
                        if denominaciones_distribuidas:
                            item = random.choice(denominaciones_distribuidas)
                            denominacion = item['denominacion']

                            stock_denom = StockDenominacion.objects.get(
                                stock=stock,
                                denominacion=denominacion
                            )

                            if stock_denom.cantidad > 0:
                                billetes_salida = random.randint(1, min(5, stock_denom.cantidad))
                                valor_salida = billetes_salida * denominacion.valor

                                if valor_salida <= cantidad_actual:
                                    cant_ant = stock_denom.cantidad
                                    stock_denom.cantidad -= billetes_salida
                                    stock_denom.save()

                                    historial_denom = HistorialStockDenominacion.objects.create(
                                        stock_denominacion=stock_denom,
                                        tipo_movimiento='SALIDA',
                                        origen_movimiento='MANUAL',
                                        cantidad_movida=billetes_salida,
                                        cantidad_anterior=cant_ant,
                                        cantidad_posterior=stock_denom.cantidad,
                                        usuario=operador,
                                        observaciones=f'Retiro de stock - {billetes_salida} billetes de {denominacion.valor} {moneda.simbolo}'
                                    )

                                    cantidad_actual -= valor_salida
                                    tipo_movimiento = 'SALIDA'
                                    observacion = f'Retiro de stock - {valor_salida} {moneda.simbolo} ({billetes_salida} billetes de {denominacion.valor})'
                                else:
                                    continue
                            else:
                                continue
                        else:
                            continue

                    if tipo_movimiento and observacion:
                        cantidad_actual = cantidad_actual.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                        cantidad_movida = abs(cantidad_actual - cantidad_anterior)

                        historial = HistorialStock.objects.create(
                            stock=stock,
                            tipo_movimiento=tipo_movimiento,
                            origen_movimiento='MANUAL',
                            cantidad_movida=cantidad_movida,
                            cantidad_anterior=cantidad_anterior,
                            cantidad_posterior=cantidad_actual,
                            usuario=operador,
                            observaciones=observacion
                        )

                        HistorialStock.objects.filter(pk=historial.pk).update(
                            fecha_movimiento=fecha_mov
                        )

                        if historial_denom:
                            HistorialStockDenominacion.objects.filter(pk=historial_denom.pk).update(
                                fecha_movimiento=fecha_mov
                            )

                # Recalcular stock total basándose en las denominaciones actuales
                # Esto asegura que el stock total siempre coincida con las denominaciones
                stock_denominaciones = StockDenominacion.objects.filter(
                    stock=stock,
                    es_activo=True
                )
                total_real = Decimal('0')
                for stock_denom in stock_denominaciones:
                    total_real += stock_denom.cantidad * stock_denom.denominacion.valor
                
                stock.cantidad = total_real.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
                stock.save()

            tausers_creados += 1
            print(f"  ✅ Tauser '{nombre}' creado con stock de {len(monedas_seleccionadas)} monedas")

        except Exception as e:
            errores += 1
            print(f"  ❌ Error creando Tauser {i+1}: {str(e)}")
            continue

    print(f"\n📊 Resumen de creación:")
    print(f"  • Tausers creados: {tausers_creados}")
    print(f"  • Errores: {errores}")

    return tausers_creados


def mostrar_estadisticas():
    print("\n📊 Estadísticas de Tausers:")

    total_tausers = Tauser.objects.count()
    tausers_activos = Tauser.objects.filter(es_activo=True).count()
    print(f"  • Total Tausers: {total_tausers}")
    print(f"  • Tausers activos: {tausers_activos}")

    print(f"\n💰 Stock por moneda:")
    for moneda in Moneda.objects.filter(es_activa=True):
        stocks = Stock.objects.filter(moneda=moneda, es_activo=True)
        total_cantidad = sum(stock.cantidad for stock in stocks)
        print(f"  • {moneda.codigo}: {total_cantidad} {moneda.simbolo} en {stocks.count()} Tausers")

    total_movimientos = HistorialStock.objects.count()
    entradas = HistorialStock.objects.filter(tipo_movimiento='ENTRADA').count()
    salidas = HistorialStock.objects.filter(tipo_movimiento='SALIDA').count()

    print(f"\n📈 Movimientos de historial:")
    print(f"  • Total movimientos: {total_movimientos}")
    print(f"  • Entradas: {entradas}")
    print(f"  • Salidas: {salidas}")

    print(f"\n🏆 Tausers con más stock:")
    for tauser in Tauser.objects.filter(es_activo=True):
        total_stock = sum(stock.cantidad for stock in tauser.stocks.filter(es_activo=True))
        if total_stock > 0:
            print(f"  • {tauser.nombre}: {int(total_stock):,} total")


def verificar_datos():
    print("\n🔍 Verificando datos creados...")

    total_tausers = Tauser.objects.count()
    total_stocks = Stock.objects.count()
    total_historial = HistorialStock.objects.count()

    print(f"  ✅ {total_tausers} Tausers creados")
    print(f"  ✅ {total_stocks} stocks creados")
    print(f"  ✅ {total_historial} movimientos de historial")

    if total_tausers > 0 and total_stocks > 0 and total_historial > 0:
        print(f"\n  ✅ Datos creados correctamente")
        return True
    else:
        print(f"\n  ❌ Error en la creación de datos")
        return False


def main():
    print("🚀 Iniciando creación de Tausers de ejemplo...")
    print("=" * 65)

    try:
        datos = obtener_datos_requeridos()
        if not datos:
            print("\n❌ No se pudieron obtener todos los datos necesarios.")
            print("   Asegúrate de ejecutar:")
            print("   • make create-currencies")
            print("   • make create-groups-users")
            sys.exit(1)

        cantidad = int(os.environ.get('CANTIDAD_TAUSERS', '5'))
        tausers_creados = crear_tausers_ejemplo(datos, cantidad)

        mostrar_estadisticas()

        if verificar_datos():
            print("\n🎉 ¡Tausers de ejemplo creados exitosamente!")
        else:
            print("\n❌ Error al crear los Tausers.")
            sys.exit(1)

    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()
