.PHONY: db-up db-clean app-run app-migrate app-setup load-permissions user help

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

app-setup:
	@echo "Configurando el proyecto Django..."
	make db-clean
	make db-up
	sleep 5
	make app-migrate
	make load-permissions

#-------------- Comandos de administración ----------------#
load-permissions:
	@echo "Cargando permisos iniciales desde fixtures..."
	poetry run python manage.py loaddata roles/fixtures/initial_permissions.json
	@echo "Permisos iniciales cargados correctamente"

user:
	@echo "Creando usuario de desarrollo..."
	@if [ "$(OS)" = "Windows_NT" ]; then \
		scripts/create_user.bat $(filter-out $@,$(MAKECMDGOALS)); \
	else \
		scripts/create_user.sh $(filter-out $@,$(MAKECMDGOALS)); \
	fi

# Regla especial para manejar argumentos del comando user
%:
	@if [ "$@" != "user" ] && echo "$(MAKECMDGOALS)" | grep -q "^user "; then \
		true; \
	fi

# Ayuda
help:
	@echo "Comandos disponibles:"
	@echo "  db-up             - Levantar la base de datos PostgreSQL"
	@echo "  db-clean          - Limpiar la base de datos y sus volúmenes"
	@echo "  app-run           - Correr el proyecto Django"
	@echo "  app-migrate       - Aplicar migraciones de la base de datos"
	@echo "  app-setup         - Configurar el proyecto (db + migraciones)"
	@echo "  load-permissions  - Cargar permisos iniciales desde fixtures"
	@echo "  user [username]   - Crear usuario de desarrollo (interactivo o con username)"
	@echo "  user-admin        - Crear un superusuario de Django"
	@echo "  help              - Mostrar esta ayuda"
	@echo ""
	@echo "Ejemplos de uso:"
	@echo "  make user                    # Modo interactivo"
	@echo "  make user juan.perez         # Con username predefinido"