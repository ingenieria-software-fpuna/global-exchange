#!/usr/bin/env python3
"""
Script para crear Tausers de ejemplo con stock de monedas.
Crea múltiples Tausers con stock de al menos 3 monedas y movimientos de historial.
Útil para desarrollo y testing del sistema de Tausers.
"""

import os
import sys
import django
from decimal import Decimal
import random
from datetime import datetime, timedelta

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'global_exchange.settings')
django.setup()

from tauser.models import Tauser, Stock, HistorialStock
from monedas.models import Moneda
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

    # Operadores
    operadores = obtener_operadores()
    if not operadores:
        print("  ❌ No se encontraron operadores")
        return None

    # Monedas activas (al menos 3)
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
    """Crear Tausers de ejemplo con información realista"""
    print(f"\n🏪 Creando {cantidad} Tausers de ejemplo...")

    tausers_creados = 0
    errores = 0

    # Datos de ejemplo para Tausers
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
            # Seleccionar datos aleatorios
            nombre = nombres_tausers[i] if i < len(nombres_tausers) else f"Tauser {i+1}"
            direccion = direcciones[i] if i < len(direcciones) else f"Dirección {i+1}"
            horario = horarios[i] if i < len(horarios) else "Lunes a Viernes: 8:00 - 18:00"
            
            # Fecha de instalación (últimos 6 meses)
            dias_atras = random.randint(30, 180)
            fecha_instalacion = timezone.now() - timedelta(days=dias_atras)

            # Crear Tauser
            tauser = Tauser.objects.create(
                nombre=nombre,
                direccion=direccion,
                horario_atencion=horario,
                es_activo=True,
                fecha_instalacion=fecha_instalacion
            )

            # Crear stock para al menos 3 monedas aleatorias
            monedas_seleccionadas = random.sample(datos['monedas'], min(3, len(datos['monedas'])))
            
            for moneda in monedas_seleccionadas:
                # Cantidad inicial de stock
                if moneda.codigo == 'PYG':
                    cantidad_inicial = Decimal(str(random.randint(5000000, 20000000)))  # 5M - 20M PYG
                else:
                    cantidad_inicial = Decimal(str(random.randint(1000, 10000)))  # 1000 - 10000 USD/EUR/etc


                # Crear stock
                stock = Stock.objects.create(
                    tauser=tauser,
                    moneda=moneda,
                    cantidad=cantidad_inicial,
                    es_activo=True
                )

                # Crear movimientos de historial (simular cargas previas)
                operador = random.choice(datos['operadores'])
                
                # Movimiento inicial (creación del stock)
                HistorialStock.objects.create(
                    stock=stock,
                    tipo_movimiento='ENTRADA',
                    origen_movimiento='MANUAL',
                    cantidad_movida=cantidad_inicial,
                    cantidad_anterior=Decimal('0.00'),
                    cantidad_posterior=cantidad_inicial,
                    usuario=operador,
                    observaciones=f'Stock inicial creado para {moneda.nombre}'
                )

                # Simular algunos movimientos adicionales (entradas y salidas)
                cantidad_actual = cantidad_inicial
                for j in range(random.randint(2, 5)):  # 2-5 movimientos adicionales
                    # Fecha del movimiento (en los últimos 30 días)
                    dias_movimiento = random.randint(1, 30)
                    fecha_movimiento = timezone.now() - timedelta(days=dias_movimiento)
                    
                    # Tipo de movimiento (70% entradas, 30% salidas)
                    if random.random() < 0.7:
                        # Entrada
                        cantidad_movida = (cantidad_inicial * Decimal(str(random.uniform(0.1, 0.3)))).quantize(Decimal('0.01'))
                        cantidad_anterior = cantidad_actual
                        cantidad_actual += cantidad_movida
                        tipo_movimiento = 'ENTRADA'
                        observacion = f'Carga de stock - {cantidad_movida} {moneda.simbolo}'
                    else:
                        # Salida
                        cantidad_movida = (cantidad_inicial * Decimal(str(random.uniform(0.05, 0.15)))).quantize(Decimal('0.01'))
                        if cantidad_movida < cantidad_actual:  # Solo si hay suficiente stock
                            cantidad_anterior = cantidad_actual
                            cantidad_actual -= cantidad_movida
                            tipo_movimiento = 'SALIDA'
                            observacion = f'Retiro de stock - {cantidad_movida} {moneda.simbolo}'
                        else:
                            continue  # Saltar este movimiento si no hay suficiente stock

                    # Crear movimiento en historial
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
                    
                    # Actualizar fecha del movimiento
                    HistorialStock.objects.filter(pk=historial.pk).update(
                        fecha_movimiento=fecha_movimiento
                    )

                # Actualizar stock con la cantidad final
                stock.cantidad = cantidad_actual
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
    """Mostrar estadísticas de Tausers y stock creados"""
    print("\n📊 Estadísticas de Tausers:")

    # Tausers totales
    total_tausers = Tauser.objects.count()
    tausers_activos = Tauser.objects.filter(es_activo=True).count()
    print(f"  • Total Tausers: {total_tausers}")
    print(f"  • Tausers activos: {tausers_activos}")

    # Stock por moneda
    print(f"\n💰 Stock por moneda:")
    for moneda in Moneda.objects.filter(es_activa=True):
        stocks = Stock.objects.filter(moneda=moneda, es_activo=True)
        total_cantidad = sum(stock.cantidad for stock in stocks)
        print(f"  • {moneda.codigo}: {total_cantidad} {moneda.simbolo} en {stocks.count()} Tausers")

    # Movimientos de historial
    total_movimientos = HistorialStock.objects.count()
    entradas = HistorialStock.objects.filter(tipo_movimiento='ENTRADA').count()
    salidas = HistorialStock.objects.filter(tipo_movimiento='SALIDA').count()
    
    print(f"\n📈 Movimientos de historial:")
    print(f"  • Total movimientos: {total_movimientos}")
    print(f"  • Entradas: {entradas}")
    print(f"  • Salidas: {salidas}")

    # Tausers con más stock
    print(f"\n🏆 Tausers con más stock:")
    for tauser in Tauser.objects.filter(es_activo=True):
        total_stock = sum(stock.cantidad for stock in tauser.stocks.filter(es_activo=True))
        if total_stock > 0:
            print(f"  • {tauser.nombre}: {total_stock:,.2f} total")


def verificar_datos():
    """Verificar que los datos se crearon correctamente"""
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
    """Función principal del script"""
    print("🚀 Iniciando creación de Tausers de ejemplo...")
    print("=" * 65)

    try:
        # Obtener datos necesarios
        datos = obtener_datos_requeridos()
        if not datos:
            print("\n❌ No se pudieron obtener todos los datos necesarios.")
            print("   Asegúrate de ejecutar estos scripts primero:")
            print("   • make create-currencies")
            print("   • make create-groups-users")
            sys.exit(1)

        # Crear Tausers
        cantidad = int(os.environ.get('CANTIDAD_TAUSERS', '5'))  # Por defecto 5
        tausers_creados = crear_tausers_ejemplo(datos, cantidad)

        # Mostrar estadísticas
        mostrar_estadisticas()

        # Verificar datos
        if verificar_datos():
            print("\n🎉 ¡Tausers de ejemplo creados exitosamente!")
            print(f"\n📋 Se crearon {tausers_creados} Tausers con:")
            print(f"   • Stock de al menos 3 monedas por Tauser")
            print(f"   • Movimientos de historial simulados")
            print(f"   • Distribución realista de cantidades")
            print(f"   • Fechas de instalación en los últimos 6 meses")
            print(f"\n🎯 Ahora puedes probar el sistema de Tausers y stock")
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
