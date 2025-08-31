#!/usr/bin/env python3
"""
Script para verificar y crear el grupo 'Admin' si no existe.
Este grupo reemplaza la funcionalidad de superuser.
Ahora usa el modelo personalizado Grupo.
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'global_exchange.settings')
django.setup()

from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from grupos.models import Grupo

def main():
    print("🔍 Verificando grupo 'Admin'...")
    
    # Verificar si existe el grupo de Django
    admin_group, created = Group.objects.get_or_create(name='Admin')
    
    if created:
        print("✅ Grupo 'Admin' de Django creado exitosamente")
    else:
        print("✅ Grupo 'Admin' de Django ya existe")
    
    # Verificar si existe la extensión personalizada
    try:
        grupo_extension = Grupo.objects.get(group=admin_group)
        print("✅ Extensión personalizada del grupo ya existe")
    except Grupo.DoesNotExist:
        print("🔄 Creando extensión personalizada del grupo...")
        grupo_extension = Grupo.objects.create(
            group=admin_group,
            es_activo=True
        )
        print("✅ Extensión personalizada creada")
    
    # Verificar que tenga todos los permisos
    all_permissions = Permission.objects.all()
    current_permissions = admin_group.permissions.all()
    
    if current_permissions.count() == all_permissions.count():
        print(f"✅ El grupo ya tiene todos los permisos ({all_permissions.count()})")
    else:
        print(f"🔄 Asignando permisos al grupo...")
        admin_group.permissions.set(all_permissions)
        print(f"✅ {all_permissions.count()} permisos asignados al grupo")
    
    # Mostrar información del grupo
    print(f"\n📊 Información del grupo:")
    print(f"   Nombre: {admin_group.name}")
    print(f"   Estado: {'Activo' if grupo_extension.es_activo else 'Inactivo'}")
    print(f"   Permisos: {admin_group.permissions.count()}")
    print(f"   Usuarios: {admin_group.user_set.count()}")
    print(f"   Fecha creación: {grupo_extension.fecha_creacion.strftime('%d/%m/%Y %H:%M')}")
    
    if admin_group.user_set.count() > 0:
        print(f"\n👥 Usuarios en el grupo:")
        for user in admin_group.user_set.all():
            print(f"   - {user.email} ({user.nombre} {user.apellido})")
    else:
        print(f"\n⚠️  No hay usuarios en el grupo 'Admin'")
        print(f"   Use 'make user' para crear un usuario administrador")
    
    print(f"\n🎯 El grupo 'Admin' está listo para usar")
    print(f"   Los usuarios en este grupo tendrán acceso completo al sistema")

if __name__ == '__main__':
    main()
