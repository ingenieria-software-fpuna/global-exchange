#!/bin/bash

# Script para crear usuarios de desarrollo
# Uso: ./scripts/create_user.sh [username]

set -e

# Función para mostrar ayuda
show_help() {
    echo "Uso: $0 [username]"
    echo ""
    echo "Crea un nuevo usuario en el sistema para desarrollo."
    echo "Si no se proporciona username, se solicitará interactivamente."
    echo ""
    echo "Ejemplo:"
    echo "  $0 juan.perez"
    echo "  $0  # Modo interactivo"
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

# Función principal para crear usuario
create_user() {
    local username=$1
    
    # Si se proporciona username como parámetro
    if [ -n "$username" ]; then
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
        
        # Preguntar si quiere asignar rol de administrador
        read -p "¿Desea asignar el rol de administrador a este usuario? (y/N): " ASSIGN_ADMIN
        if [[ $ASSIGN_ADMIN =~ ^[Yy]$ ]]; then
            echo "Asignando rol de administrador..."
            
            poetry run python manage.py shell -c "
from usuarios.models import Usuario
from roles.models import Rol, UsuarioRol

try:
    usuario = Usuario.objects.get(email='$EMAIL')
    admin_rol = Rol.objects.get(codigo='admin')
    
    usuario_rol, created = UsuarioRol.objects.get_or_create(
        usuario=usuario,
        rol=admin_rol,
        defaults={'asignado_por': 'script_desarrollo'}
    )
    
    if created:
        print('✅ Rol de administrador asignado correctamente')
    else:
        print('ℹ️  El usuario ya tenía el rol de administrador')
        
except Exception as e:
    print(f'❌ Error al asignar rol: {e}')
"
        fi
    else
        exit 1
    fi
}

# Procesar argumentos
case "${1:-}" in
    -h|--help)
        show_help
        exit 0
        ;;
    *)
        create_user "$1"
        ;;
esac
