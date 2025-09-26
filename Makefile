.PHONY: db-up db-clean app-run app-migrate check-admin-group app-setup user user-fast app-reset help docs-html docs-clean docs-live app-test create-currencies

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
	@echo "Configurando el proyecto Django..."
	make db-clean
	make db-up
ifeq ($(OS),Windows_NT)
	timeout /t 5 /nobreak > nul
else
	sleep 5
endif
	make app-migrate
	make check-admin-group
	make create-currencies
	make create-payment-methods
	make create-collection-methods
	make create-groups-users
	make create-client-types
	make create-clients
	make create-historical-rates
	make setup-transactions
	make create-transactions

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
