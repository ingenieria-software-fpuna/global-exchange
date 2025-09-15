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

# Optionally create development users from env vars
if [ -n "${INIT_USER_EMAIL:-}" ]; then
  echo "[entrypoint] Creating init users from ${INIT_USER_EMAIL}..."
  python - <<'PY'
import os
import django
import random
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'global_exchange.settings')
django.setup()

from django.db import IntegrityError
from usuarios.models import Usuario
from django.contrib.auth.models import Permission, Group

# Get comma-separated emails
emails_str = os.environ.get('INIT_USER_EMAIL', '')
emails = [email.strip() for email in emails_str.split(',') if email.strip()]

if not emails:
    print("❌ No hay emails válidos en INIT_USER_EMAIL")
    exit()

password = os.environ.get('INIT_USER_PASSWORD', '123456')
make_admin = os.environ.get('INIT_USER_ADMIN', 'true').lower() == 'true'

# Crear grupo de administradores si no existe (una sola vez)
if make_admin:
    admin_group, created = Group.objects.get_or_create(name='Admin')
    if created:
        print('✅ Grupo Admin creado')
        # Asignar todos los permisos al grupo nuevo
        all_permissions = Permission.objects.all()
        admin_group.permissions.set(all_permissions)
        print(f'✅ {all_permissions.count()} permisos asignados al grupo Admin')
    else:
        print('✅ Grupo Admin ya existe')

for email in emails:
    try:
        # Extract name from email (part before @)
        email_prefix = email.split('@')[0]
        # Use email prefix as both nombre and apellido for simplicity
        nombre = email_prefix.capitalize()
        apellido = "Admin"
        
        # Generate a simple cedula based on email (just for uniqueness)
        cedula = str(abs(hash(email)) % 100000000).zfill(8)
        fecha_nacimiento = '1990-01-01'
        
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
            print(f"✅ Usuario creado: {user.email} ({nombre} {apellido})")
        else:
            print(f"ℹ️  Usuario ya existe: {user.email}")

        if make_admin:
            try:
                # Agregar usuario al grupo Admin
                user.groups.add(admin_group)
                
                # También marcar como staff
                user.is_staff = True
                user.save()
                print(f'✅ Usuario {user.email} configurado como admin')
                
            except Exception as e:
                print(f"⚠️  No se pudo configurar permisos admin para {email}: {e}")
                
    except IntegrityError as e:
        print(f"❌ Error de integridad para {email}: {e}")
    except Exception as e:
        print(f"❌ Error creando usuario {email}: {e}")

print(f"✅ Procesamiento completado para {len(emails)} email(s)")
PY
fi

# Optionally create currencies from env var
if [ "${CREATE_CURRENCIES:-false}" = "true" ]; then
  echo "[entrypoint] Creating currencies and exchange rates..."
  PYTHONPATH=/app python scripts/create_currencies_test.py || {
    echo "⚠️  Error creating currencies, but continuing..."
  }
fi

# Optionally create payment methods from env var
if [ "${CREATE_PAYMENT_METHODS:-false}" = "true" ]; then
  echo "[entrypoint] Creating payment methods..."
  PYTHONPATH=/app python scripts/create_metodos_pago_test.py || {
    echo "⚠️  Error creating payment methods, but continuing..."
  }
fi

echo "[entrypoint] Starting Django dev server on 0.0.0.0:${PORT}"
exec python manage.py runserver 0.0.0.0:"${PORT}"
