Deployment y Producción
=======================

Esta guía describe cómo desplegar Global Exchange en producción.

Arquitectura de Deployment
---------------------------

**Componentes principales:**

- Aplicación Django (Global Exchange)
- Base de datos PostgreSQL
- Servidor web (Gunicorn + Nginx)
- Redis (opcional, para caché y Celery)
- SQL-Proxy (para facturación electrónica)

Stack Tecnológico
-----------------

**Backend:**

- Python 3.13
- Django 5.x
- PostgreSQL 14+
- Poetry para gestión de dependencias

**Frontend:**

- Bootstrap 5
- JavaScript vanilla
- Plantillas Django (Jinja2)

**Infraestructura:**

- Docker y Docker Compose
- Nginx como reverse proxy
- Gunicorn como servidor WSGI
- Systemd para gestión de servicios

Requisitos del Sistema
----------------------

**Hardware mínimo:**

- CPU: 2 cores
- RAM: 4 GB
- Disco: 50 GB SSD
- Red: Conexión estable a internet

**Hardware recomendado:**

- CPU: 4+ cores
- RAM: 8+ GB
- Disco: 100+ GB SSD
- Red: Conexión dedicada con IP fija

**Software:**

- Ubuntu 22.04 LTS o superior
- Docker 24.x
- Docker Compose 2.x
- Git

Configuración de Variables de Entorno
--------------------------------------

Crear archivo ``.env`` en la raíz del proyecto:

.. code-block:: bash

    # Django
    SECRET_KEY=tu-secret-key-super-segura-aqui
    DEBUG=False
    ALLOWED_HOSTS=tudominio.com,www.tudominio.com
    
    # Base de datos
    DB_NAME=global_exchange_prod
    DB_USER=ge_user
    DB_PASSWORD=password-segura-aqui
    DB_HOST=db
    DB_PORT=5432
    
    # Email
    EMAIL_HOST=smtp.gmail.com
    EMAIL_PORT=587
    EMAIL_USE_TLS=True
    EMAIL_HOST_USER=noreply@tudominio.com
    EMAIL_HOST_PASSWORD=password-email-aqui
    DEFAULT_FROM_EMAIL=noreply@tudominio.com
    
    # Facturación (opcional)
    FACTURACION_ENABLED=True
    INVOICE_DB_HOST=sql-proxy
    INVOICE_DB_PORT=5432
    INVOICE_DB_NAME=fs_proxy_bd
    INVOICE_DB_USER=fs_proxy_user
    INVOICE_DB_PASSWORD=password-facturacion
    
    # Seguridad
    SECURE_SSL_REDIRECT=True
    SESSION_COOKIE_SECURE=True
    CSRF_COOKIE_SECURE=True

Deployment con Docker
----------------------

**1. Preparar el servidor:**

.. code-block:: bash

    # Actualizar sistema
    sudo apt update && sudo apt upgrade -y
    
    # Instalar Docker
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    
    # Instalar Docker Compose
    sudo apt install docker-compose-plugin
    
    # Agregar usuario al grupo docker
    sudo usermod -aG docker $USER

**2. Clonar el repositorio:**

.. code-block:: bash

    git clone https://github.com/tu-org/global-exchange.git
    cd global-exchange
    git checkout main  # o la rama de producción

**3. Configurar variables de entorno:**

.. code-block:: bash

    cp .env.example .env
    nano .env  # Editar con valores de producción

**4. Construir y levantar servicios:**

.. code-block:: bash

    # Construir imágenes
    docker compose build
    
    # Levantar servicios
    docker compose up -d
    
    # Verificar que están corriendo
    docker compose ps

**5. Inicializar la aplicación:**

.. code-block:: bash

    # Ejecutar migraciones
    docker compose exec web python manage.py migrate
    
    # Cargar datos iniciales
    docker compose exec web python manage.py setup_grupos
    docker compose exec web python manage.py setup_transacciones
    docker compose exec web python manage.py setup_monedas
    
    # Crear superusuario
    docker compose exec web python manage.py createsuperuser
    
    # Recolectar archivos estáticos
    docker compose exec web python manage.py collectstatic --noinput

Archivo docker-compose.yml
---------------------------

.. code-block:: yaml

    version: '3.8'
    
    services:
      db:
        image: postgres:15
        environment:
          POSTGRES_DB: ${DB_NAME}
          POSTGRES_USER: ${DB_USER}
          POSTGRES_PASSWORD: ${DB_PASSWORD}
        volumes:
          - postgres_data:/var/lib/postgresql/data
        networks:
          - backend
    
      web:
        build: .
        command: gunicorn global_exchange.wsgi:application --bind 0.0.0.0:8000 --workers 4
        volumes:
          - .:/app
          - static_volume:/app/staticfiles
          - media_volume:/app/media
        environment:
          - DEBUG=${DEBUG}
          - SECRET_KEY=${SECRET_KEY}
          - DB_NAME=${DB_NAME}
          - DB_USER=${DB_USER}
          - DB_PASSWORD=${DB_PASSWORD}
          - DB_HOST=db
        depends_on:
          - db
        networks:
          - backend
          - frontend
    
      nginx:
        image: nginx:alpine
        ports:
          - "80:80"
          - "443:443"
        volumes:
          - ./nginx.conf:/etc/nginx/nginx.conf:ro
          - static_volume:/app/staticfiles:ro
          - media_volume:/app/media:ro
          - ./ssl:/etc/nginx/ssl:ro
        depends_on:
          - web
        networks:
          - frontend
    
    volumes:
      postgres_data:
      static_volume:
      media_volume:
    
    networks:
      backend:
      frontend:

Configuración de Nginx
-----------------------

Archivo ``nginx.conf``:

.. code-block:: nginx

    upstream django {
        server web:8000;
    }
    
    server {
        listen 80;
        server_name tudominio.com www.tudominio.com;
        
        # Redirect HTTP to HTTPS
        return 301 https://$server_name$request_uri;
    }
    
    server {
        listen 443 ssl http2;
        server_name tudominio.com www.tudominio.com;
        
        ssl_certificate /etc/nginx/ssl/cert.pem;
        ssl_certificate_key /etc/nginx/ssl/key.pem;
        
        client_max_body_size 10M;
        
        location /static/ {
            alias /app/staticfiles/;
            expires 30d;
            add_header Cache-Control "public, immutable";
        }
        
        location /media/ {
            alias /app/media/;
            expires 30d;
        }
        
        location / {
            proxy_pass http://django;
            proxy_set_header Host $host;
            proxy_set_header X-Real-IP $remote_addr;
            proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
            proxy_set_header X-Forwarded-Proto $scheme;
        }
    }

SSL/TLS con Let's Encrypt
--------------------------

.. code-block:: bash

    # Instalar Certbot
    sudo apt install certbot python3-certbot-nginx
    
    # Obtener certificado
    sudo certbot --nginx -d tudominio.com -d www.tudominio.com
    
    # Renovación automática (ya incluida en certbot)
    sudo certbot renew --dry-run

Deployment Manual (sin Docker)
-------------------------------

**1. Preparar el servidor:**

.. code-block:: bash

    sudo apt update
    sudo apt install python3.13 python3-pip python3-venv postgresql nginx

**2. Configurar PostgreSQL:**

.. code-block:: bash

    sudo -u postgres psql
    CREATE DATABASE global_exchange_prod;
    CREATE USER ge_user WITH PASSWORD 'password-segura';
    GRANT ALL PRIVILEGES ON DATABASE global_exchange_prod TO ge_user;
    \q

**3. Instalar la aplicación:**

.. code-block:: bash

    # Crear usuario de sistema
    sudo useradd -m -s /bin/bash ge_user
    sudo su - ge_user
    
    # Clonar repositorio
    git clone https://github.com/tu-org/global-exchange.git
    cd global-exchange
    
    # Instalar Poetry
    curl -sSL https://install.python-poetry.org | python3 -
    
    # Instalar dependencias
    poetry install --no-dev
    
    # Configurar entorno
    cp .env.example .env
    nano .env

**4. Configurar Gunicorn:**

Crear ``/etc/systemd/system/gunicorn.service``:

.. code-block:: ini

    [Unit]
    Description=Gunicorn daemon for Global Exchange
    After=network.target
    
    [Service]
    User=ge_user
    Group=www-data
    WorkingDirectory=/home/ge_user/global-exchange
    ExecStart=/home/ge_user/global-exchange/.venv/bin/gunicorn \
              --access-logfile - \
              --workers 4 \
              --bind unix:/run/gunicorn.sock \
              global_exchange.wsgi:application
    
    [Install]
    WantedBy=multi-user.target

.. code-block:: bash

    sudo systemctl start gunicorn
    sudo systemctl enable gunicorn

Monitoreo y Logs
----------------

**Ver logs de Docker:**

.. code-block:: bash

    # Logs de la aplicación
    docker compose logs -f web
    
    # Logs de PostgreSQL
    docker compose logs -f db
    
    # Logs de Nginx
    docker compose logs -f nginx

**Ver logs del sistema:**

.. code-block:: bash

    # Logs de Gunicorn
    sudo journalctl -u gunicorn -f
    
    # Logs de aplicación
    tail -f logs/auth.log
    tail -f logs/transacciones.log

Backup y Recuperación
---------------------

**Backup de base de datos:**

.. code-block:: bash

    # Con Docker
    docker compose exec db pg_dump -U $DB_USER $DB_NAME > backup_$(date +%Y%m%d).sql
    
    # Manual
    pg_dump -U ge_user global_exchange_prod > backup_$(date +%Y%m%d).sql

**Backup de archivos:**

.. code-block:: bash

    # Backup de media y logs
    tar -czf media_backup_$(date +%Y%m%d).tar.gz media/ logs/

**Restaurar backup:**

.. code-block:: bash

    # Con Docker
    docker compose exec -T db psql -U $DB_USER $DB_NAME < backup_20251031.sql
    
    # Manual
    psql -U ge_user global_exchange_prod < backup_20251031.sql

Seguridad en Producción
------------------------

**Checklist de seguridad:**

- [ ] DEBUG=False en producción
- [ ] SECRET_KEY única y segura
- [ ] ALLOWED_HOSTS configurado correctamente
- [ ] SSL/TLS habilitado (HTTPS)
- [ ] Cookies seguras (SESSION_COOKIE_SECURE=True)
- [ ] CSRF protection habilitado
- [ ] Firewall configurado (solo puertos 80, 443)
- [ ] PostgreSQL solo accesible internamente
- [ ] Credenciales en variables de entorno
- [ ] Backups automatizados configurados
- [ ] Monitoreo de logs activo

Performance Optimization
------------------------

**Configuración de Django:**

.. code-block:: python

    # settings.py para producción
    
    # Caché con Redis
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': 'redis://redis:6379/1',
        }
    }
    
    # Sesiones en caché
    SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
    
    # Compresión de respuestas
    MIDDLEWARE = [
        'django.middleware.gzip.GZipMiddleware',
        # ... otros middleware
    ]

**Optimización de PostgreSQL:**

.. code-block:: sql

    -- En postgresql.conf
    shared_buffers = 256MB
    effective_cache_size = 1GB
    work_mem = 4MB
    maintenance_work_mem = 64MB

Actualización del Sistema
--------------------------

.. code-block:: bash

    # 1. Backup de la base de datos
    docker compose exec db pg_dump -U $DB_USER $DB_NAME > backup_pre_update.sql
    
    # 2. Detener servicios
    docker compose down
    
    # 3. Actualizar código
    git pull origin main
    
    # 4. Reconstruir y levantar
    docker compose build
    docker compose up -d
    
    # 5. Ejecutar migraciones
    docker compose exec web python manage.py migrate
    
    # 6. Recolectar estáticos
    docker compose exec web python manage.py collectstatic --noinput
    
    # 7. Verificar
    docker compose ps
    docker compose logs -f web

Troubleshooting
---------------

**Problema: Aplicación no inicia**

.. code-block:: bash

    # Ver logs detallados
    docker compose logs web
    
    # Verificar configuración
    docker compose exec web python manage.py check

**Problema: Error de conexión a base de datos**

.. code-block:: bash

    # Verificar que PostgreSQL esté corriendo
    docker compose ps db
    
    # Probar conexión
    docker compose exec db psql -U $DB_USER $DB_NAME

**Problema: Archivos estáticos no se cargan**

.. code-block:: bash

    # Recolectar estáticos
    docker compose exec web python manage.py collectstatic --noinput
    
    # Verificar permisos
    docker compose exec nginx ls -la /app/staticfiles

Mantenimiento
-------------

**Tareas periódicas:**

- Backups diarios automatizados
- Limpieza de logs antiguos (>30 días)
- Actualización de dependencias de seguridad
- Monitoreo de espacio en disco
- Revisión de logs de errores
- Actualización de certificados SSL

**Scripts de mantenimiento:**

.. code-block:: bash

    # Limpiar sesiones expiradas
    docker compose exec web python manage.py clearsessions
    
    # Limpiar códigos de verificación expirados
    docker compose exec web python manage.py shell -c "from auth.models import CodigoVerificacion; CodigoVerificacion.limpiar_codigos_expirados()"

Contacto y Soporte
------------------

Para problemas en producción:

- Email: soporte@globalexchange.com
- Documentación: https://docs.globalexchange.com
- Issues: https://github.com/tu-org/global-exchange/issues
