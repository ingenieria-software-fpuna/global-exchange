.PHONY: db-up db-clean app-run app-migrate check-admin-group app-setup user user-fast app-reset help docs-html docs-clean docs-live app-test create-currencies stripe-up stripe-down stripe-logs stripe-secret stripe-trigger

#-------------- Operaciones de base de datos ----------------#
db-up:
	@echo "Levantando la base de datos PostgreSQL..."
	docker compose -f docker-compose-dev.yml up -d glx-db
	@echo "Base de datos levantada correctamente"

db-clean:
	@echo "Limpiando la base de datos y volúmenes..."
	docker compose -f docker-compose-dev.yml down -v --remove-orphans
	@echo "Base de datos y volúmenes limpiados"

#-------------- Comandos DJANGO ----------------#
app-run:
	@echo "Iniciando el servidor de desarrollo Django..."
	poetry run python manage.py runserver

app-migrate:
	@echo "Aplicando migraciones de la base de datos..."
	poetry run python manage.py migrate
	@echo "Migraciones aplicadas correctamente"

check-admin-group:
	@echo "Verificando grupo Admin del sistema..."
	poetry run python scripts/check_admin_group.py

create-currencies:
	@echo "Poblando base de datos con monedas y tasas de cambio de ejemplo..."
	poetry run python scripts/create_currencies_test.py

create-payment-methods:
	@echo "Poblando base de datos con métodos de pago de ejemplo..."
	poetry run python scripts/create_metodos_pago_test.py

create-collection-methods:
	@echo "Poblando base de datos con métodos de cobro de ejemplo..."
	poetry run python scripts/create_metodos_cobro_test.py

create-groups-users:
	@echo "Creando grupos y usuarios de ejemplo..."
	poetry run python scripts/create_grupos_usuarios_test.py

create-historical-rates:
	@echo "Creando datos históricos de tasas de cambio..."
	poetry run python scripts/create_historical_rates.py

create-client-types:
	@echo "Creando tipos de cliente de ejemplo..."
	poetry run python scripts/create_tipos_cliente_test.py

create-clients:
	@echo "Creando clientes de ejemplo con operadores asignados..."
	poetry run python scripts/create_clientes_test.py

migrate-groups:
	@echo "Migrando grupos existentes al nuevo modelo..."
	poetry run python manage.py migrate_grupos_existentes

test-grupo-permisos:
	@echo "Probando funcionalidad de permisos con grupos activos/inactivos..."
	poetry run python manage.py test_grupo_permisos --create-test-data

limpiar-codigos:
	@echo "Limpiando códigos de verificación expirados..."
	poetry run python manage.py limpiar_codigos

limpiar-codigos-dry:
	@echo "Simulando limpieza de códigos de verificación expirados..."
	poetry run python manage.py limpiar_codigos --dry-run

setup-transactions:
	@echo "Configurando tipos y estados de transacciones..."
	poetry run python manage.py setup_transacciones

create-transactions:
	@echo "Creando transacciones de ejemplo..."
	poetry run python scripts/create_transacciones_test.py

app-setup:
	@echo "╔════════════════════════════════════════════════════════════╗"
	@echo "║          CONFIGURACIÓN COMPLETA DEL PROYECTO GLX           ║"
	@echo "╚════════════════════════════════════════════════════════════╝"
	@echo ""
	@echo "→ Limpiando base de datos..."
	@make db-clean
	@echo ""
	@echo "→ Levantando base de datos..."
	@make db-up
	@echo ""
	@echo "→ Iniciando Stripe CLI..."
	@make stripe-up
	@echo ""
	@echo "→ Esperando servicios..."
ifeq ($(OS),Windows_NT)
	@timeout /t 5 /nobreak > nul
else
	@sleep 5
endif
	@echo ""
	@echo "→ Aplicando migraciones..."
	@make app-migrate
	@echo ""
	@echo "→ Configurando grupos y permisos..."
	@make check-admin-group
	@echo ""
	@echo "→ Creando monedas y tasas de cambio..."
	@make create-currencies
	@echo ""
	@echo "→ Creando métodos de pago..."
	@make create-payment-methods
	@echo ""
	@echo "→ Creando métodos de cobro..."
	@make create-collection-methods
	@echo ""
	@echo "→ Creando grupos y usuarios..."
	@make create-groups-users
	@echo ""
	@echo "→ Creando tipos de cliente..."
	@make create-client-types
	@echo ""
	@echo "→ Creando clientes de ejemplo..."
	@make create-clients
	@echo ""
	@echo "→ Creando datos históricos..."
	@make create-historical-rates
	@echo ""
	@echo "→ Configurando transacciones..."
	@make setup-transactions
	@echo ""
	@echo "→ Creando transacciones de ejemplo..."
	@make create-transactions
	@echo ""
	@echo "╔════════════════════════════════════════════════════════════╗"
	@echo "║                  ✅ SETUP COMPLETADO                       ║"
	@echo "╚════════════════════════════════════════════════════════════╝"
	@echo ""
	@echo "📋 IMPORTANTE: Configura tu webhook secret de Stripe"
	@echo ""
	@echo "1. Ejecuta: make stripe-secret"
	@echo "2. Copia el valor 'whsec_...' a tu archivo .env"
	@echo "3. Reinicia tu servidor Django"
	@echo ""
	@echo "🚀 Para iniciar el servidor:"
	@echo "   make app-run"
	@echo ""
	@echo "📊 Para ver webhooks en tiempo real:"
	@echo "   make stripe-logs"
	@echo ""

#-------------- Comandos de administración ----------------#

user:
	@echo "Creando usuario de desarrollo..."
ifeq ($(OS),Windows_NT)
	scripts\create_user.bat $(filter-out $@,$(MAKECMDGOALS))
else
	scripts/create_user.sh $(filter-out $@,$(MAKECMDGOALS))
endif
user-fast:
	@echo "Creando usuario de desarrollo (modo rápido)..."
ifeq ($(OS),Windows_NT)
	scripts\create_user.bat $(filter-out $@,$(MAKECMDGOALS)) -f
else
	scripts/create_user.sh $(filter-out $@,$(MAKECMDGOALS)) -f
endif
# Regla especial para manejar argumentos del comando user
%:
	@if [ "$@" != "user" ] && echo "$(MAKECMDGOALS)" | grep -q "^user "; then \
		true; \
	fi

#-------------- App tests ----------------#
app-test:
	@echo "Ejecutando todos los tests del proyecto..."
	poetry run python manage.py test -v 2
	@echo "Tests completados"

#-------------- Stripe CLI (Docker) ----------------#
stripe-up:
	@echo "Iniciando Stripe CLI en Docker..."
	docker compose -f docker-compose-dev.yml up -d stripe-cli
	@echo "Esperando que Stripe CLI se inicie..."
ifeq ($(OS),Windows_NT)
	@timeout /t 3 /nobreak > nul
else
	@sleep 3
endif
	@echo ""
	@echo "✅ Stripe CLI iniciado"
	@echo ""
	@echo "Para obtener el webhook secret ejecuta:"
	@echo "  make stripe-secret"

stripe-down:
	@echo "Deteniendo Stripe CLI..."
	docker compose -f docker-compose-dev.yml stop stripe-cli
	@echo "Stripe CLI detenido"

stripe-logs:
	@echo "Mostrando logs de Stripe CLI (Ctrl+C para salir)..."
	docker compose -f docker-compose-dev.yml logs -f stripe-cli

stripe-secret:
	@echo "Obteniendo webhook signing secret..."
	@bash scripts/get-stripe-webhook-secret.sh

stripe-trigger:
	@echo "Trigger manual de eventos Stripe"
	@echo ""
	@echo "Eventos disponibles:"
	@echo "  1. checkout.session.completed (Pago exitoso)"
	@echo "  2. payment_intent.payment_failed (Pago fallido)"
	@echo ""
	@read -p "Seleccione evento (1 o 2): " event; \
	case $$event in \
		1) docker exec -it $$(docker ps -qf "name=stripe-cli") stripe trigger checkout.session.completed ;; \
		2) docker exec -it $$(docker ps -qf "name=stripe-cli") stripe trigger payment_intent.payment_failed ;; \
		*) echo "Opción inválida" ;; \
	esac

# Ayuda
help:
	@echo "Comandos disponibles:"
	@echo "  db-up             - Levantar la base de datos PostgreSQL"
	@echo "  db-clean          - Limpiar la base de datos y sus volúmenes"
	@echo "  app-run           - Correr el proyecto Django"
	@echo "  app-migrate       - Aplicar migraciones de la base de datos"
	@echo "  app-test          - Ejecutar todos los tests del proyecto"
	@echo "  app-setup         - Configurar el proyecto (db + migraciones + grupos + datos ejemplo)"
	@echo "  create-currencies - Poblar base de datos con monedas y tasas de ejemplo"
	@echo "  create-payment-methods - Poblar base con métodos de pago de ejemplo"
	@echo "  create-collection-methods - Poblar base con métodos de cobro de ejemplo"
	@echo "  create-groups-users - Crear grupos y usuarios de ejemplo con permisos"
	@echo "  create-client-types - Crear tipos de cliente (VIP, Minorista, Corporativo)"
	@echo "  create-clients - Crear clientes de ejemplo con operadores asignados"
	@echo "  create-historical-rates - Crear datos históricos de tasas de cambio"
	@echo "  create-transactions - Crear transacciones de ejemplo para operadores"
	@echo "  migrate-groups    - Migrar grupos existentes al nuevo modelo"
	@echo "  test-grupo-permisos - Probar funcionalidad de permisos con grupos activos/inactivos"
	@echo "  limpiar-codigos   - Limpiar códigos de verificación expirados"
	@echo "  limpiar-codigos-dry - Simular limpieza de códigos (modo prueba)"
	@echo "  user [username] [-f] - Crear usuario de desarrollo (interactivo o con username)"
	@echo "  user-fast [username] - Crear usuario rápido con valores predeterminados"
	@echo "  app-reset         - Reset completo (db + migraciones + permisos)"
	@echo "  docs-html         - Generar documentación HTML (Sphinx)"
	@echo "  docs-deploy       - Construir documentación para Django (disponible en /docs/)"
	@echo "  docs-live         - Servidor live de docs (sphinx-autobuild)"
	@echo "  docs-clean        - Limpiar artefactos de build de docs"
	@echo ""
	@echo "Comandos de Stripe CLI:"
	@echo "  stripe-up         - Iniciar Stripe CLI en Docker (webhook forwarding)"
	@echo "  stripe-down       - Detener Stripe CLI"
	@echo "  stripe-logs       - Ver logs de Stripe CLI"
	@echo "  stripe-secret     - Obtener webhook signing secret"
	@echo "  stripe-trigger    - Trigger manual de eventos de prueba"
	@echo ""
	@echo "  help              - Mostrar esta ayuda"
	@echo ""
	@echo "Ejemplos de uso:"
	@echo "  make user                    # Modo interactivo"
	@echo "  make user juan.perez         # Con username predefinido"
	@echo "  make user-fast               # Modo rápido interactivo"
	@echo "  make user-fast admin         # Modo rápido con username 'admin'"

#-------------- Documentación (Sphinx) ----------------#
docs-html:
	@echo "Construyendo documentación HTML..."
	$(MAKE) -C docs html
	@echo "Documentación generada en docs/_build/html"

docs-deploy:
	@echo "Construyendo documentación para despliegue..."
	$(MAKE) -C docs html
	@echo "Documentación lista para servir en /docs/"
	@echo "La documentación estará disponible en: http://localhost:8000/docs/"

docs-clean:
	@echo "Limpiando artefactos de documentación..."
	$(MAKE) -C docs clean

docs-live:
	@echo "Iniciando servidor live de documentación..."
	$(MAKE) -C docs live
