.PHONY: db-up db-clean app-run app-migrate app-setup load-permissions user-admin user user-fast create-superuser app-reset help docs-html docs-clean docs-live

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

user-fast:
	@echo "Creando usuario de desarrollo (modo rápido)..."
	@if [ "$(OS)" = "Windows_NT" ]; then \
		scripts/create_user.bat $(filter-out $@,$(MAKECMDGOALS)) -f; \
	else \
		scripts/create_user.sh $(filter-out $@,$(MAKECMDGOALS)) -f; \
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
		@echo "  user [username] [-f] - Crear usuario de desarrollo (interactivo o con username)"
	@echo "  user-fast [username] - Crear usuario rápido con valores predeterminados"
	@echo "  user-admin        - Crear un superusuario de Django"
	@echo "  create-superuser  - Crear un superusuario de Django"
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
