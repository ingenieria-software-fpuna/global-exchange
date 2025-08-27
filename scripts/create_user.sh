#!/bin/bash

# Script para crear usuarios de desarrollo
# Uso: ./scripts/create_user.sh [username] [-f]

set -e

# Variables para modo rápido
FAST_MODE=false

# Función para mostrar ayuda
show_help() {
    echo "Uso: $0 [username] [-f]"
    echo ""
    echo "Crea un nuevo usuario en el sistema para desarrollo."
    echo "Si no se proporciona username, se solicitará interactivamente."
    echo ""
    echo "Opciones:"
    echo "  -f, --fast    Modo rápido usando valores predeterminados del .env"
    echo "  -h, --help    Mostrar esta ayuda"
    echo ""
    echo "Ejemplos:"
    echo "  $0 juan.perez        # Con username predefinido"
    echo "  $0 juan.perez -f     # Modo rápido con username"
    echo "  $0 -f                # Modo rápido interactivo"
    echo "  $0                   # Modo interactivo completo"
}

# Función para validar email
validate_email() {
    local email=$1
    if [[ $email =~ ^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$ ]]; then
        return 0
    else
        return 1
    fi
}

# Función para validar fecha (YYYY-MM-DD)
validate_date() {
    local date=$1
    if [[ $date =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]]; then
        return 0
    else
        return 1
    fi
}

# Función para generar email basado en username
generate_email() {
    local username=$1
    echo "${username}@gmail.com"
}

# Función para cargar valores por defecto para modo rápido
load_default_values() {
    local username=${1:-"testuser"}
    
    # Valores por defecto para desarrollo
    EMAIL=$(generate_email "$username")
    NOMBRE="Usuario"
    APELLIDO="Prueba"
    CEDULA="12345678"
    FECHA_NACIMIENTO="1990-01-01"
    PASSWORD="123456"  # Contraseña simple para desarrollo
    
    echo "=== Modo Rápido - Usando valores por defecto ==="
    echo "Email: $EMAIL"
    echo "Nombre: $NOMBRE $APELLIDO"
    echo "Cédula: $CEDULA"
    echo "Fecha de nacimiento: $FECHA_NACIMIENTO"
    echo "Contraseña: $PASSWORD"
    echo ""
}

# Función principal para crear usuario
create_user() {
    local username=$1
    
    # Modo rápido
    if [ "$FAST_MODE" = true ]; then
        if [ -n "$username" ]; then
            load_default_values "$username"
        else
            read -p "Username para generar email: " username
            load_default_values "$username"
        fi
        
        read -p "¿Continuar con estos valores? (Y/n): " CONFIRM
        if [[ $CONFIRM =~ ^[Nn]$ ]]; then
            echo "Operación cancelada."
            exit 0
        fi
        
    # Si se proporciona username como parámetro (modo normal)
    elif [ -n "$username" ]; then
        EMAIL=$(generate_email "$username")
        echo "Creando usuario con email: $EMAIL"
        
        # Solicitar datos adicionales
        read -p "Nombre: " NOMBRE
        read -p "Apellido: " APELLIDO
        read -p "Cédula: " CEDULA
        
        # Validar y solicitar fecha de nacimiento
        while true; do
            read -p "Fecha de nacimiento (YYYY-MM-DD): " FECHA_NACIMIENTO
            if validate_date "$FECHA_NACIMIENTO"; then
                break
            else
                echo "Error: Formato de fecha inválido. Use YYYY-MM-DD"
            fi
        done
        
        read -s -p "Contraseña: " PASSWORD
        echo ""
        read -s -p "Confirmar contraseña: " PASSWORD_CONFIRM
        echo ""
        
        if [ "$PASSWORD" != "$PASSWORD_CONFIRM" ]; then
            echo "Error: Las contraseñas no coinciden"
            exit 1
        fi
    else
        # Modo interactivo completo
        echo "=== Creación de Usuario para Desarrollo ==="
        echo ""
        
        # Solicitar email
        while true; do
            read -p "Email: " EMAIL
            if validate_email "$EMAIL"; then
                break
            else
                echo "Error: Email inválido"
            fi
        done
        
        read -p "Nombre: " NOMBRE
        read -p "Apellido: " APELLIDO
        read -p "Cédula: " CEDULA
        
        # Validar y solicitar fecha de nacimiento
        while true; do
            read -p "Fecha de nacimiento (YYYY-MM-DD): " FECHA_NACIMIENTO
            if validate_date "$FECHA_NACIMIENTO"; then
                break
            else
                echo "Error: Formato de fecha inválido. Use YYYY-MM-DD"
            fi
        done
        
        read -s -p "Contraseña: " PASSWORD
        echo ""
        read -s -p "Confirmar contraseña: " PASSWORD_CONFIRM
        echo ""
        
        if [ "$PASSWORD" != "$PASSWORD_CONFIRM" ]; then
            echo "Error: Las contraseñas no coinciden"
            exit 1
        fi
    fi
    
    # Crear el usuario usando Django shell
    echo ""
    echo "Creando usuario..."
    
    poetry run python manage.py shell -c "
from usuarios.models import Usuario
from django.db import IntegrityError

try:
    usuario = Usuario.objects.create_user(
        email='$EMAIL',
        password='$PASSWORD',
        nombre='$NOMBRE',
        apellido='$APELLIDO',
        cedula='$CEDULA',
        fecha_nacimiento='$FECHA_NACIMIENTO'
    )
    print(f'✅ Usuario creado exitosamente:')
    print(f'   Email: {usuario.email}')
    print(f'   Nombre: {usuario.nombre} {usuario.apellido}')
    print(f'   Cédula: {usuario.cedula}')
    print(f'   ID: {usuario.id}')
except IntegrityError as e:
    if 'email' in str(e):
        print('❌ Error: Ya existe un usuario con ese email')
    elif 'cedula' in str(e):
        print('❌ Error: Ya existe un usuario con esa cédula')
    else:
        print(f'❌ Error: {e}')
    exit(1)
except Exception as e:
    print(f'❌ Error inesperado: {e}')
    exit(1)
"
    
    if [ $? -eq 0 ]; then
        echo ""
        echo "🎉 Usuario creado correctamente!"
        
        # Preguntar si quiere asignar al grupo Admin
        read -p "¿Desea asignar este usuario al grupo 'Admin'? (y/N): " ASSIGN_ADMIN
        if [[ $ASSIGN_ADMIN =~ ^[Yy]$ ]]; then
            echo "Asignando usuario al grupo Admin..."
            
            poetry run python manage.py shell -c "
from usuarios.models import Usuario
from django.contrib.auth.models import Permission
from django.contrib.auth.models import Group

try:
    usuario = Usuario.objects.get(email='$EMAIL')
    
    # Obtener o crear el grupo Admin
    admin_group, created = Group.objects.get_or_create(name='Admin')
    if created:
        print('✅ Grupo Admin creado')
        # Asignar todos los permisos al grupo nuevo
        from django.contrib.auth.models import Permission
        all_permissions = Permission.objects.all()
        admin_group.permissions.set(all_permissions)
        print(f'✅ {all_permissions.count()} permisos asignados al grupo Admin')
    else:
        print('✅ Grupo Admin ya existe')
    
    # Agregar usuario al grupo Admin
    usuario.groups.add(admin_group)
    print('✅ Usuario agregado al grupo Admin')
    
    # También marcar como staff (opcional, para acceso a ciertas funcionalidades)
    usuario.is_staff = True
    usuario.save()
    print('✅ Usuario marcado como staff')
    
    print('🎉 Usuario configurado como administrador del sistema')
        
except Exception as e:
    print(f'❌ Error al configurar permisos: {e}')
"
        fi
    else
        exit 1
    fi
}

# Procesar argumentos
USERNAME=""
for arg in "$@"; do
    case $arg in
        -f|--fast)
            FAST_MODE=true
            shift
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        -*)
            echo "Opción desconocida: $arg"
            show_help
            exit 1
            ;;
        *)
            if [ -z "$USERNAME" ]; then
                USERNAME="$arg"
            fi
            ;;
    esac
done

create_user "$USERNAME"
