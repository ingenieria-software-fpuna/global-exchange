# Guía de contribución
> **Esta guía no fue escrita ni revisada por inteligencia artifical, por favor, tomarse el tiempo de leer.**


### Nombre de rama:
Cuando sea aplicable (siempre debe ser aplicable), usar solo el número del ticket de Jira y la categoría correspondiente, ejemplo de categorías:
- `bugfix/` - branch que arregla un bug en el código.
- `docs/` - mejora o creación de documentación.
- `feature/` - agregar un feature nuevo o se está trabajando en uno.
- `tool/` - agregar alguna herramienta de desarrollo.
- `release/` - reservado para releases.
- `task/` - se está haciendo algúna tarea de rútina.

Ejemplo de nombres de ramas:
- `feature/GE-78`
- `bugfix/GE-67`


### Commits
Los commits también deben contener el número del ticket, esto puede parecer redundante pero ayuda a identificar más rápidamente a que ticket pertenece el commit, los commits deben **tener significado** y estar **bien escritos**.

Esta guía es muy interesante para aprender a escribir commits de calidad https://cbea.ms/git-commit/

Ejemplos:
- `GE-78: Agregar autenticación de 2 factores`
- `GE-99: Agregar template del homepage`

### Base de datos
Los nombres de las tablas deben ser (siempre que se pueda), en singular. 

~~usuarios~~ no, **usuario** si.
~~roles~~ no, **rol** si

Los nombres de las columnas deben ser descriptivos y significativos, si se trata de una **PRIMARY_KEY**, por favor no utilizar solo el nombre *"**id**"*, el nombre de la **PRIMARY_KEY** siempre debe ser, *nombre-de-tabla + "id"*, por ejemplo:
- `usuario_id`
- `rol_id`

Demostración rápida:
```sql
-- Ejemplo si es usa solo nombre "id" como PRIMARY_KEY (dificil de entender)
select 
	r.id,
  u.id,
  u.nombre
from rol r
join rol_usuario ru on ru.rol_id = r.id
join usuario u on u.id = r.usuario_id
where u.nombre = 'Mario Bros';

-- Ejemplo si se usa nombre-de-tabla + "id" como PRIMARY_KEY
select
	r.rol_id,
  u.usuario_id,
  u.nombre
from rol r
join rol_usuario ru on ru.rol_id = r.rol_id
join usuario u on u.usuario_id = r.usuario_id
where u.nombre = 'Mario Bros';
```