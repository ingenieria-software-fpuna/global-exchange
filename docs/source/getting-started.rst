Primeros Pasos
==============

Esta guía rápida muestra cómo configurar, ejecutar y generar documentación para el proyecto.

Configuración del Proyecto
---------------------------

- Requisitos: Python 3.13, Poetry, Docker (para PostgreSQL local).
- Instalar dependencias:

  - ``poetry install``
  - Opcional: ``make db-up`` para iniciar PostgreSQL localmente.

- Inicializar la aplicación localmente:

  - ``make app-setup`` (limpia la BD, inicia la BD, ejecuta migraciones, carga permisos)
  - ``make app-run`` para iniciar el servidor de desarrollo de Django

Ejecutar Pruebas
-----------------

- Ejecutar la suite completa de pruebas:

  - ``poetry run python manage.py test``

Generar Documentación
----------------------

Este repositorio incluye una configuración mínima de Sphinx en ``docs/``.

- Generar documentación HTML estática:

  - ``make -C docs html``
  - La salida estará en ``docs/_build/html``.

- Limpiar artefactos de construcción:

  - ``make -C docs clean``

- Documentación con recarga automática (opcional, requiere ``sphinx-autobuild``):

  - ``make -C docs live``


