.PHONY: db-up db-clean app-run app-migrate app-setup help

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

# Ayuda
help:
	@echo "Comandos disponibles:"
	@echo "  db-up     - Levantar la base de datos PostgreSQL"
	@echo "  db-clean  - Limpiar la base de datos y sus volúmenes"
	@echo "  app-run   - Correr el proyecto Django"
	@echo "  app-migrate - Aplicar migraciones de la base de datos"
	@echo "  help      - Mostrar esta ayuda"