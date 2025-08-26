### Global Exchange
Proyecto de Ingeniería de Software 2 (IS2) de la Facultad Politécnica de la Universidad Nacional de Asunción.

### Integrantes
- Diego Noguera - diegonoguerarec@fpuna.edu.py
- Juan David - juanemanueldavidzaracho@fpuna.edu.py
- Kyara Popov - kyarapopov@fpuna.edu.py
- Zinri Bobadilla - zinri@fpuna.edu.py
- Sebastian Alvarez - ca.sebastianlv@fpuna.edu.py

### Links importantes
- [Jira](https://fpuna-team-rlp0euzv.atlassian.net/jira)
- [Wiki](http://109.199.116.203:8060/es/links-de-interes)
- [Repositorio del proyecto](https://github.com/ingenieria-software-fpuna/global-exchange)


### Pre-requisitos
- [Python 3.13.7](https://www.python.org/ftp/python/3.13.7/Python-3.13.7.tar.xz)
- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- [Docker Compose](https://docs.docker.com/compose/) (incluido en Docker Desktop a partir de la versión 2.0)
- [Poetry](https://python-poetry.org/)
- Algún cliente de postgres ([pgAdmin](https://www.pgadmin.org/), [DBeaver](https://dbeaver.io/), etc.)
- Make (en windows, instalar de aquí: [Make for Windows](https://gnuwin32.sourceforge.net/packages/make.htm))

### Instalación
1. Clonar el repositorio:

```bash
git clone https://github.com/ingenieria-software-fpuna/global-exchange.git
```
2. Navegar al directorio del proyecto:

```bash
cd global-exchange
```

3. Crear un entorno virtual con python 3.13.7 (opcional pero recomendado)
    - Linux/Unix
    ```bash
    curl -fsSL https://pyenv.run | bash
    ```

4. Instalar Poetry (si no lo tienes instalado):

```bash
# En Linux/macOS/Windows (WSL)
curl -sSL https://install.python-poetry.org | python3 -
```

5. Agregar Poetry al PATH (si es necesario, si no, omitir este paso):

```bash
# Agregar al final de ~/.bashrc o ~/.zshrc
export PATH="$HOME/.local/bin:$PATH"
# Recargar el shell o ejecutar:
source ~/.bashrc  # o source ~/.zshrc
```

6. Verificar la instalación de Poetry:

```bash
poetry --version
```

7. Instalar las dependencias del proyecto:

```bash
poetry install
```

8. Crear un archivo `.env` a partir del archivo de ejemplo:

```bash
cp .env.example .env
```

### Uso del proyecto

Una vez instaladas las dependencias, puedes ejecutar el proyecto con los siguientes comandos:

```bash
make app-setup  # Configuración (limpiar DB, levantar DB, aplicar migraciones)
make user # Crear un usuario para usar el sistema
make app-run    # Correr el proyecto
```


### Contribución
Antes de contribuir, por favor lee el archivo [CONTRIBUTING.md](CONTRIBUTING.md) para entender las normas y directrices del proyecto.