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
- [Guía de contribución al código](http://109.199.116.203:8060/es/dev/guia-de-contribucion)


### Pre-requisitos
- [Python 3.13.7](https://www.python.org/ftp/python/3.13.7/Python-3.13.7.tar.xz)
- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- [Docker Compose](https://docs.docker.com/compose/) (incluido en Docker Desktop a partir de la versión 2.0)
- [Poetry](https://python-poetry.org/)
- Algún cliente de postgres ([pgAdmin](https://www.pgadmin.org/), [DBeaver](https://dbeaver.io/), etc.)
- Make (en windows, instalar de aquí: [Make for Windows](https://gnuwin32.sourceforge.net/packages/make.htm))
- **Cuenta de Stripe** (para pagos) - [Crear cuenta de prueba](https://dashboard.stripe.com/register)

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

9. Configurar las claves de Stripe en el archivo `.env`:

```bash
# Obtener las claves de: https://dashboard.stripe.com/test/apikeys
STRIPE_SECRET_KEY=sk_test_tu_clave_secreta
STRIPE_PUBLISHABLE_KEY=pk_test_tu_clave_publicable
STRIPE_WEBHOOK_SECRET=  # Se generará automáticamente
```

### Uso del proyecto

#### 🚀 Inicio Rápido (Recomendado)

Configura todo el proyecto con un solo comando:

```bash
make app-setup
```

Este comando configura automáticamente:
- ✅ Base de datos PostgreSQL
- ✅ Stripe CLI para webhooks
- ✅ Migraciones de base de datos
- ✅ Usuarios, grupos y permisos
- ✅ Monedas y métodos de pago (incluyendo Stripe)
- ✅ Datos de prueba (clientes, transacciones, etc.)

Después del setup:

```bash
# 1. Obtener el webhook secret de Stripe
make stripe-secret
# Copiar el valor whsec_... a .env como STRIPE_WEBHOOK_SECRET

# 2. Iniciar el servidor Django
make app-run

# 3. (Opcional) Ver webhooks en tiempo real
make stripe-logs
```

#### 📖 Guía Completa

Para más detalles, ver [QUICK_START.md](QUICK_START.md)

#### Comandos Útiles

```bash
make help           # Ver todos los comandos disponibles
make app-test       # Ejecutar tests
make stripe-trigger # Probar eventos de Stripe
make db-clean       # Limpiar base de datos
```


### Contribución
Antes de contribuir, por favor lee el archivo [CONTRIBUTING.md](CONTRIBUTING.md) para entender las normas y directrices del proyecto.
