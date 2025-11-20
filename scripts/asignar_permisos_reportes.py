"""
Script para asignar permisos de reportes al grupo Administradores
"""
import os
import sys
import django

# Configurar Django
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'global_exchange.settings')
django.setup()

from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from transacciones.models import Transaccion


def asignar_permisos_reportes():
    """
    Asigna los permisos de reportes al grupo Administradores
    """
    print("🔄 Iniciando asignación de permisos de reportes...")
    
    try:
        # Obtener el grupo Administradores
        grupo_admin = Group.objects.get(name='Admin')
        print(f"✅ Grupo 'Administradores' encontrado")
    except Group.DoesNotExist:
        print("❌ Error: El grupo 'Administradores' no existe")
        print("   Por favor, crea el grupo primero")
        return
    
    # Obtener el content type de Transaccion
    content_type = ContentType.objects.get_for_model(Transaccion)
    
    # Permisos a asignar
    permisos_reportes = [
        'view_reporte_transacciones',
        'view_reporte_ganancias',
    ]
    
    permisos_asignados = 0
    permisos_ya_existentes = 0
    
    for codename in permisos_reportes:
        try:
            # Obtener el permiso
            permiso = Permission.objects.get(
                content_type=content_type,
                codename=codename
            )
            
            # Verificar si ya está asignado
            if grupo_admin.permissions.filter(id=permiso.id).exists():
                print(f"ℹ️  Permiso '{codename}' ya estaba asignado")
                permisos_ya_existentes += 1
            else:
                # Asignar el permiso
                grupo_admin.permissions.add(permiso)
                print(f"✅ Permiso '{codename}' asignado correctamente")
                permisos_asignados += 1
                
        except Permission.DoesNotExist:
            print(f"❌ Error: Permiso '{codename}' no existe en la base de datos")
            print(f"   Asegúrate de haber ejecutado las migraciones")
    
    print("\n" + "="*60)
    print(f"📊 Resumen:")
    print(f"   • Permisos nuevos asignados: {permisos_asignados}")
    print(f"   • Permisos ya existentes: {permisos_ya_existentes}")
    print(f"   • Total de permisos: {len(permisos_reportes)}")
    print("="*60)
    
    if permisos_asignados > 0:
        print("\n✨ ¡Permisos de reportes asignados exitosamente!")
        print("   Los usuarios del grupo 'Administradores' ahora pueden:")
        print("   - Ver reporte de transacciones")
        print("   - Ver reporte de ganancias")
        print("   - Exportar reportes a Excel y PDF")


if __name__ == '__main__':
    asignar_permisos_reportes()
