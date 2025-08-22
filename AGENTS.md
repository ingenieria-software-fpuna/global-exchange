# Repository Guidelines

## Estructura del Proyecto
- `global_exchange/`: Configuración de Django (settings, urls, WSGI/ASGI).
- `auth/`, `roles/`, `usuarios/`: Apps con modelos, vistas, formularios, urls y migraciones.
- `templates/`: Plantillas globales (`base.html`, `welcome.html`).
- `scripts/`: Utilidades (`create_user.sh`, `create_user.bat`).
- `tests/`: Paquete de pruebas; también hay `tests.py` por app.
- `docker-compose-dev.yml`: Servicio PostgreSQL local.
- `Makefile`: Tareas comunes. Dependencias con Poetry (`pyproject.toml`).

## Comandos de Build, Test y Desarrollo
- `poetry install`: Instala las dependencias.
- `make app-setup`: Limpia volúmenes, levanta DB, migra y carga permisos.
- `make app-run`: Inicia el servidor de desarrollo (`manage.py runserver`).
- `make app-migrate`: Aplica migraciones.
- `make db-up` / `make db-clean`: Levanta o limpia PostgreSQL.
- Pruebas: `poetry run python manage.py test`

## Estilo de Código y Nombres
- Python 3.13 + Django 5. PEP8: indentación 4 espacios; `snake_case` para funciones/variables; `CamelCase` para clases/modelos.
- Mantener imports limpios; eliminar no usados (ver commits tipo "GE-84").
- Convenciones Django: rutas en `urls.py`, plantillas por app o en `templates/`, fixtures en `roles/fixtures/`.

## Pruebas
- Ubicar pruebas en `tests/` o `tests.py` por app con `test_*.py` y `TestCase`.
- Cubrir modelos, formularios, vistas y permisos. Ej.: `poetry run python manage.py test roles`.

## Commits y Pull Requests
- Commits: prefijo con clave Jira si aplica (p. ej., `GE-84: resumen imperativo corto`).
- PRs: enlazar issue, describir cambios, incluir capturas (UI) y pasos de prueba. Verificar local con `make app-setup && make app-run`.

## Variables de Entorno y Seguridad
- Configurar DB y correo vía variables de entorno; no subir secretos.
- Claves esperadas: `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`, `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_USE_TLS`, `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `DEFAULT_FROM_EMAIL`.
- Archivo sugerido: `.env` (ejemplo en `.env.example`). El proyecto carga `.env` automáticamente si `python-dotenv` está instalado. Alternativamente, exporta variables o usa `direnv`/Docker Compose.
