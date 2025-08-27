@echo off
setlocal enabledelayedexpansion

REM Script para crear us:main
if "!FAST_MODE!"=="true" (
    if defined USERNAME_PARAM (
        set "EMAIL=!USERNAME_PARAM!@gmail.com"
    ) else (
        set /p "USERNAME_PARAM=Username para generar email: "
        set "EMAIL=!USERNAME_PARAM!@gmail.com"
    )
    
    REM Valores por defecto para modo rapido
    set "NOMBRE=Usuario"
    set "APELLIDO=Prueba"
    set "CEDULA=12345678"
    set "FECHA_NACIMIENTO=1990-01-01"
    set "PASSWORD=123456"
    
    echo === Modo Rapido - Usando valores por defecto ===
    echo Email: !EMAIL!
    echo Nombre: !NOMBRE! !APELLIDO!
    echo Cedula: !CEDULA!
    echo Fecha de nacimiento: !FECHA_NACIMIENTO!
    echo Contraseña: !PASSWORD!
    echo.
    
    set /p "CONFIRM=¿Continuar con estos valores? (Y/n): "
    if /i "!CONFIRM!"=="n" (
        echo Operacion cancelada.
        exit /b 0
    )
    
) else if defined USERNAME_PARAM (
    REM Modo con username proporcionado
    set "EMAIL=!USERNAME_PARAM!@gmail.com"
    echo Creando usuario con email: !EMAIL!
    echo.
    
    set /p "NOMBRE=Nombre: "
    set /p "APELLIDO=Apellido: "
    set /p "CEDULA=Cedula: "sarrollo en Windows
REM Uso: scripts\create_user.bat [username] [-f]

REM Variables
set FAST_MODE=false

REM Procesar argumentos
:parse_args
if "%1"=="-f" (
    set FAST_MODE=true
    shift
    goto :parse_args
)
if "%1"=="--fast" (
    set FAST_MODE=true
    shift
    goto :parse_args
)
if "%1"=="-h" goto :show_help
if "%1"=="--help" goto :show_help
if "%1"=="/?" goto :show_help

REM Guardar username si se proporciona
set USERNAME_PARAM=%1

REM Verificar si Poetry está instalado
poetry --version >nul 2>&1
if errorlevel 1 (
    echo Error: Poetry no está instalado o no está en el PATH
    echo Por favor instale Poetry primero: https://python-poetry.org/docs/#installation
    exit /b 1
)

REM Función principal
goto :main

:show_help
echo Uso: %~nx0 [username] [-f]
echo.
echo Crea un nuevo usuario en el sistema para desarrollo.
echo Si no se proporciona username, se solicitara interactivamente.
echo.
echo Opciones:
echo   -f, --fast    Modo rapido usando valores predeterminados
echo   -h, --help    Mostrar esta ayuda
echo.
echo Ejemplos:
echo   %~nx0 juan.perez        # Con username predefinido
echo   %~nx0 juan.perez -f     # Modo rapido con username
echo   %~nx0 -f                # Modo rapido interactivo
echo   %~nx0   # Modo interactivo
echo.
goto :eof

:validate_email
set "email=%~1"
echo !email! | findstr /R "^[a-zA-Z0-9._%+-]*@[a-zA-Z0-9.-]*\.[a-zA-Z][a-zA-Z]*$" >nul
exit /b %errorlevel%

:validate_date
set "date=%~1"
echo !date! | findstr /R "^[0-9][0-9][0-9][0-9]-[0-9][0-9]-[0-9][0-9]$" >nul
exit /b %errorlevel%

:main
set "USERNAME_PARAM=%1"

if defined USERNAME_PARAM (
    REM Modo con username proporcionado
    set "EMAIL=!USERNAME_PARAM!@gmail.com"
    echo Creando usuario con email: !EMAIL!
    echo.
    
    set /p "NOMBRE=Nombre: "
    set /p "APELLIDO=Apellido: "
    set /p "CEDULA=Cedula: "
    
    :ask_date_param
    set /p "FECHA_NACIMIENTO=Fecha de nacimiento (YYYY-MM-DD): "
    call :validate_date "!FECHA_NACIMIENTO!"
    if errorlevel 1 (
        echo Error: Formato de fecha invalido. Use YYYY-MM-DD
        goto :ask_date_param
    )
    
    REM En Windows no podemos ocultar la entrada, así que advertimos
    echo.
    echo NOTA: La contraseña sera visible al escribir en Windows
    set /p "PASSWORD=Contraseña: "
    set /p "PASSWORD_CONFIRM=Confirmar contraseña: "
    
    if not "!PASSWORD!"=="!PASSWORD_CONFIRM!" (
        echo Error: Las contraseñas no coinciden
        exit /b 1
    )
) else (
    REM Modo interactivo completo
    echo === Creacion de Usuario para Desarrollo ===
    echo.
    
    :ask_email
    set /p "EMAIL=Email: "
    call :validate_email "!EMAIL!"
    if errorlevel 1 (
        echo Error: Email invalido
        goto :ask_email
    )
    
    set /p "NOMBRE=Nombre: "
    set /p "APELLIDO=Apellido: "
    set /p "CEDULA=Cedula: "
    
    :ask_date_interactive
    set /p "FECHA_NACIMIENTO=Fecha de nacimiento (YYYY-MM-DD): "
    call :validate_date "!FECHA_NACIMIENTO!"
    if errorlevel 1 (
        echo Error: Formato de fecha invalido. Use YYYY-MM-DD
        goto :ask_date_interactive
    )
    
    echo.
    echo NOTA: La contraseña sera visible al escribir en Windows
    set /p "PASSWORD=Contraseña: "
    set /p "PASSWORD_CONFIRM=Confirmar contraseña: "
    
    if not "!PASSWORD!"=="!PASSWORD_CONFIRM!" (
        echo Error: Las contraseñas no coinciden
        exit /b 1
    )
)

echo.
echo Creando usuario...

REM Crear el usuario usando Django shell
poetry run python manage.py shell -c "
from usuarios.models import Usuario
from django.db import IntegrityError
import sys

try:
    usuario = Usuario.objects.create_user(
        email='!EMAIL!',
        password='!PASSWORD!',
        nombre='!NOMBRE!',
        apellido='!APELLIDO!',
        cedula='!CEDULA!',
        fecha_nacimiento='!FECHA_NACIMIENTO!'
    )
    print(f'✅ Usuario creado exitosamente:')
    print(f'   Email: {usuario.email}')
    print(f'   Nombre: {usuario.nombre} {usuario.apellido}')
    print(f'   Cedula: {usuario.cedula}')
    print(f'   ID: {usuario.id}')
except IntegrityError as e:
    if 'email' in str(e):
        print('❌ Error: Ya existe un usuario con ese email')
    elif 'cedula' in str(e):
        print('❌ Error: Ya existe un usuario con esa cedula')
    else:
        print(f'❌ Error: {e}')
    sys.exit(1)
except Exception as e:
    print(f'❌ Error inesperado: {e}')
    sys.exit(1)
"

if errorlevel 1 (
    exit /b 1
)

echo.
echo 🎉 Usuario creado correctamente!

set /p "ASSIGN_ADMIN=¿Desea asignar TODOS los permisos del sistema a este usuario? (y/N): "
if /i "!ASSIGN_ADMIN!"=="y" (
    echo Asignando todos los permisos del sistema...
    
    poetry run python manage.py shell -c "
from usuarios.models import Usuario
from django.contrib.auth.models import Permission
from django.contrib.auth.models import Group

try:
    usuario = Usuario.objects.get(email='!EMAIL!')
    
    # Crear grupo de administradores si no existe
    admin_group, created = Group.objects.get_or_create(name='Admin')
    if created:
        print('✅ Grupo de administradores creado')
    
    # Asignar todos los permisos al grupo
    all_permissions = Permission.objects.all()
    admin_group.permissions.set(all_permissions)
    print(f'✅ {all_permissions.count()} permisos asignados al grupo de administradores')
    
    # Agregar usuario al grupo de administradores
    usuario.groups.add(admin_group)
    print('✅ Usuario agregado al grupo de administradores')
    
    # También marcar como staff (opcional, para acceso a ciertas funcionalidades)
    usuario.is_staff = True
    usuario.save()
    print('✅ Usuario marcado como staff')
    
    print('🎉 Usuario configurado como administrador del sistema')
        
except Exception as e:
    print(f'❌ Error al configurar permisos: {e}')
"
)

endlocal
goto :eof
