#!/usr/bin/env bash
set -euo pipefail

cd /app

# Defaults for dev workflow
: "${PORT:=8000}"

# Ensure a .env exists if only the example is present
if [ ! -f .env ] && [ -f .env.example ]; then
  echo "[entrypoint] No .env found. Copying from .env.example"
  cp .env.example .env || true
fi

echo "[entrypoint] Applying database migrations..."
python manage.py migrate --noinput
python manage.py loaddata roles/fixtures/initial_permissions.json

# Optionally create a development user from env vars
if [ -n "${INIT_USER_EMAIL:-}" ]; then
  echo "[entrypoint] Creating init user ${INIT_USER_EMAIL} (if not exists)..."
  python - <<'PY'
import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'global_exchange.settings')
django.setup()

from django.db import IntegrityError
from usuarios.models import Usuario

email = os.environ.get('INIT_USER_EMAIL')
nombre = os.environ.get('INIT_USER_NOMBRE', 'Usuario')
apellido = os.environ.get('INIT_USER_APELLIDO', 'Prueba')
cedula = os.environ.get('INIT_USER_CEDULA', '12345678')
fecha_nacimiento = os.environ.get('INIT_USER_FECHA_NACIMIENTO', '1990-01-01')
password = os.environ.get('INIT_USER_PASSWORD', '123456')
make_admin = os.environ.get('INIT_USER_ADMIN', 'false').lower() == 'true'

try:
    user, created = Usuario.objects.get_or_create(
        email=email,
        defaults={
            'nombre': nombre,
            'apellido': apellido,
            'cedula': cedula,
            'fecha_nacimiento': fecha_nacimiento,
        }
    )
    if created:
        user.set_password(password)
        user.save()
        print(f"✅ Usuario creado: {user.email}")
    else:
        print(f"ℹ️  Usuario ya existe: {user.email}")

    if make_admin:
        try:
            from roles.models import Rol, UsuarioRol
            admin_role = Rol.objects.get(codigo='admin')
            _, assigned = UsuarioRol.objects.get_or_create(
                usuario=user,
                rol=admin_role,
                defaults={'asignado_por': 'entrypoint'}
            )
            if assigned:
                print('✅ Rol admin asignado')
            else:
                print('ℹ️  Usuario ya tiene rol admin')
        except Exception as e:
            print(f"⚠️  No se pudo asignar rol admin: {e}")
except IntegrityError as e:
    print(f"❌ Error de integridad: {e}")
except Exception as e:
    print(f"❌ Error creando usuario: {e}")
PY
fi

echo "[entrypoint] Starting Django dev server on 0.0.0.0:${PORT}"
exec python manage.py runserver 0.0.0.0:"${PORT}"
