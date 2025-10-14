#!/usr/bin/env python3
"""
Script para poblar la base de datos con grupos y usuarios de ejemplo.
Útil para desarrollo y testing.
"""

import os
import sys
import django
from datetime import date

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'global_exchange.settings')
django.setup()

from django.contrib.auth.models import Group as DjangoGroup, Permission
from django.contrib.contenttypes.models import ContentType
from grupos.models import Grupo
from usuarios.models import Usuario


def obtener_permisos_por_app():
    """Obtener permisos organizados por aplicación"""
    permisos = {}

    # Aplicaciones relevantes para los permisos
    apps_relevantes = [
        'monedas', 'tasa_cambio', 'transacciones',
        'metodo_cobro', 'metodo_pago', 'clientes',
        'configuracion', 'grupos', 'usuarios'
    ]

    for app in apps_relevantes:
        try:
            content_types = ContentType.objects.filter(app_label=app)
            app_permisos = Permission.objects.filter(content_type__in=content_types)
            permisos[app] = list(app_permisos)
            print(f"  📋 {app}: {len(app_permisos)} permisos encontrados")
        except Exception as e:
            print(f"  ⚠️  Error obteniendo permisos de {app}: {e}")
            permisos[app] = []

    return permisos


def crear_grupos_ejemplo():
    """Crear grupos con permisos específicos"""

    print("📋 Obteniendo permisos del sistema...")
    permisos_por_app = obtener_permisos_por_app()

    # Definición de grupos y sus permisos
    grupos_config = [
        {
            'nombre': 'Analista',
            'descripcion': 'Acceso completo a monedas, tasas, transacciones, métodos de pago/cobro, clientes y configuraciones del sistema',
            'apps_completas': ['monedas', 'tasa_cambio', 'transacciones', 'metodo_cobro', 'metodo_pago', 'clientes', 'configuracion']
        },
        {
            'nombre': 'Operador',
            'descripcion': 'Acceso de solo lectura a clientes, métodos de pago/cobro, tasas de cambio y transacciones',
            'apps_solo_lectura': ['clientes', 'metodo_cobro', 'metodo_pago', 'tasa_cambio', 'transacciones'],
            'permisos_excluidos': ['view_tipocliente', 'can_view_all_clients', 'can_view_sensitive_columns']
        },
        {
            'nombre': 'Visitante',
            'descripcion': 'Sin permisos especiales, solo acceso básico al sistema',
            'sin_permisos': True
        }
    ]

    print("\n👥 Creando grupos...")
    grupos_creados = 0

    for config in grupos_config:
        nombre = config['nombre']

        # Crear o obtener el grupo Django
        django_group, group_created = DjangoGroup.objects.get_or_create(name=nombre)

        # Crear o obtener el grupo extendido
        grupo, grupo_created = Grupo.objects.get_or_create(
            group=django_group,
            defaults={'es_activo': True}
        )

        if grupo_created:
            print(f"  ✅ Grupo creado: {nombre}")
            grupos_creados += 1
        else:
            print(f"  ℹ️  Grupo ya existe: {nombre}")
            # Asegurar que esté activo
            if not grupo.es_activo:
                grupo.es_activo = True
                grupo.save()
                print(f"    🔄 Grupo reactivado: {nombre}")

        # Configurar permisos
        permisos_asignados = []

        # Grupo sin permisos (Visitante)
        if config.get('sin_permisos', False):
            print(f"    📋 Sin permisos asignados (grupo básico)")
        else:
            # Acceso completo a apps
            if 'apps_completas' in config:
                for app in config['apps_completas']:
                    if app in permisos_por_app:
                        permisos_asignados.extend(permisos_por_app[app])

            # Solo lectura (view permissions)
            if 'apps_solo_lectura' in config:
                permisos_excluidos = config.get('permisos_excluidos', [])
                for app in config['apps_solo_lectura']:
                    if app in permisos_por_app:
                        permisos_lectura = [
                            p for p in permisos_por_app[app]
                            if p.codename.startswith('view_') and p.codename not in permisos_excluidos
                        ]
                        permisos_asignados.extend(permisos_lectura)

            # Asignar permisos al grupo
            if permisos_asignados:
                django_group.permissions.set(permisos_asignados)
                print(f"    📋 {len(permisos_asignados)} permisos asignados")

        # Mostrar resumen de permisos
        if permisos_asignados:
            apps_con_permisos = {}
            for permiso in permisos_asignados:
                app = permiso.content_type.app_label
                if app not in apps_con_permisos:
                    apps_con_permisos[app] = []
                apps_con_permisos[app].append(permiso.codename)

            for app, perms in apps_con_permisos.items():
                tipo_acceso = "completo" if len(perms) > 1 else "lectura"
                print(f"      • {app}: {tipo_acceso} ({len(perms)} permisos)")
        else:
            print(f"      • Sin permisos especiales (acceso básico)")

    return grupos_creados


def crear_usuarios_ejemplo():
    """Crear usuarios de ejemplo y asignarlos a grupos"""

    usuarios_config = [
        {
            'email': 'analista1@test.test',
            'nombre': 'Analista',
            'apellido': 'Uno',
            'cedula': '1111111',
            'password': '123456',
            'grupo': 'Analista'
        },
        {
            'email': 'analista2@test.test',
            'nombre': 'Analista',
            'apellido': 'Dos',
            'cedula': '2222222',
            'password': '123456',
            'grupo': 'Analista'
        },
        {
            'email': 'operador1@test.test',
            'nombre': 'Operador',
            'apellido': 'Uno',
            'cedula': '3333333',
            'password': '123456',
            'grupo': 'Operador'
        },
        {
            'email': 'operador2@test.test',
            'nombre': 'Operador',
            'apellido': 'Dos',
            'cedula': '4444444',
            'password': '123456',
            'grupo': 'Operador'
        },
        {
            'email': 'visitante1@globalexchange.test',
            'nombre': 'Visitante',
            'apellido': 'Uno',
            'cedula': '5555555',
            'password': '123456',
            'grupo': 'Visitante'
        }
    ]

    print("\n👤 Creando usuarios de ejemplo...")
    usuarios_creados = 0

    for config in usuarios_config:
        email = config['email']
        grupo_nombre = config.pop('grupo')

        # Verificar si el usuario ya existe
        usuario_existente = Usuario.objects.filter(email=email).first()

        if usuario_existente:
            print(f"  ℹ️  Usuario ya existe: {email}")
            usuario = usuario_existente
        else:
            # Crear usuario
            usuario = Usuario.objects.create_user(
                email=email,
                nombre=config['nombre'],
                apellido=config['apellido'],
                cedula=config['cedula'],
                fecha_nacimiento=date(1990, 1, 1),
                password=config['password']
            )
            print(f"  ✅ Usuario creado: {email}")
            usuarios_creados += 1

        # Asignar al grupo
        try:
            grupo = DjangoGroup.objects.get(name=grupo_nombre)
            usuario.groups.clear()  # Limpiar grupos existentes
            usuario.groups.add(grupo)
            print(f"    👥 Asignado al grupo: {grupo_nombre}")
        except DjangoGroup.DoesNotExist:
            print(f"    ❌ Error: Grupo {grupo_nombre} no encontrado")

    return usuarios_creados


def verificar_datos():
    """Verificar que los datos se crearon correctamente"""
    print("\n🔍 Verificando datos creados...")

    grupos_activos = Grupo.objects.filter(es_activo=True).count()
    usuarios_activos = Usuario.objects.filter(es_activo=True).count()

    print(f"  • Grupos activos: {grupos_activos}")
    print(f"  • Usuarios activos: {usuarios_activos}")

    # Mostrar detalle de usuarios por grupo
    print("\n👥 Usuarios por grupo:")
    for grupo in Grupo.objects.filter(es_activo=True).order_by('group__name'):
        usuarios = Usuario.objects.filter(groups=grupo.group, es_activo=True)
        print(f"  • {grupo.name}: {usuarios.count()} usuario(s)")
        for usuario in usuarios:
            print(f"    - {usuario.email} ({usuario.nombre} {usuario.apellido})")

    if grupos_activos > 0 and usuarios_activos > 0:
        print("\n  ✅ Datos verificados correctamente")
        return True
    else:
        print("\n  ❌ Error en la verificación de datos")
        return False


def main():
    """Función principal del script"""
    print("🚀 Iniciando creación de grupos y usuarios de ejemplo...")
    print("=" * 60)

    try:
        # Crear grupos
        grupos_creados = crear_grupos_ejemplo()

        # Crear usuarios
        usuarios_creados = crear_usuarios_ejemplo()

        # Verificar datos
        if verificar_datos():
            print("\n🎉 ¡Grupos y usuarios creados exitosamente!")
            print("\n📋 Credenciales de acceso:")
            print("   • analista1@globalexchange.test / analista123")
            print("   • analista2@globalexchange.test / analista123")
            print("   • operador1@globalexchange.test / operador123")
            print("   • operador2@globalexchange.test / operador123")
            print("   • visitante1@globalexchange.test / 123456")
            print("\n🔐 Permisos configurados:")
            print("   • Analista: Acceso completo a todas las funcionalidades")
            print("   • Operador: Solo lectura en clientes, métodos de pago/cobro, tasas y transacciones")
            print("   • Visitante: Sin permisos especiales, solo acceso básico")
        else:
            print("\n❌ Error al crear los grupos y usuarios.")
            sys.exit(1)

    except Exception as e:
        print(f"\n❌ Error inesperado: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == '__main__':
    main()