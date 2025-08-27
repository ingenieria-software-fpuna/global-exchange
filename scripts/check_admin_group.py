#!/usr/bin/env python3
"""
Script para verificar y crear el grupo 'Admin' si no existe.
Este grupo reemplaza la funcionalidad de superuser.
"""

import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'global_exchange.settings')
django.setup()

from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType

def main():
    print("🔍 Verificando grupo 'Admin'...")
    
    # Verificar si existe el grupo
    admin_group, created = Group.objects.get_or_create(name='Admin')
    
    if created:
        print("✅ Grupo 'Admin' creado exitosamente")
    else:
        print("✅ Grupo 'Admin' ya existe")
    
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
    print(f"   Permisos: {admin_group.permissions.count()}")
    print(f"   Usuarios: {admin_group.user_set.count()}")
    
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
