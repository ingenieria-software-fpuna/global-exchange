Scripts de Desarrollo y Testing
===============================

El directorio ``scripts/`` contiene una colección de scripts Python especializados para poblar la base de datos con datos de ejemplo, configurar el entorno de desarrollo y facilitar el testing del sistema Global Exchange.

Descripción General
-------------------

Los scripts están diseñados para:

- Crear datos de ejemplo realistas para desarrollo y testing
- Configurar componentes del sistema de manera automatizada
- Facilitar la demostración de funcionalidades
- Proporcionar datos consistentes para pruebas

Todos los scripts siguen un patrón común:

- Configuración automática de Django
- Verificación de dependencias
- Creación de datos con validaciones
- Reportes detallados de operaciones
- Manejo robusto de errores

Scripts de Población de Datos
------------------------------

create_currencies_test.py
~~~~~~~~~~~~~~~~~~~~~~~~~

**Propósito**: Crea monedas principales del sistema con sus tasas de cambio asociadas.

**Funcionalidad:**

- Crea 11 monedas principales: PYG, USD, EUR, BRL, ARS, GBP, JPY, CAD, CHF, AUD, CNY
- Configura tasas de cambio realistas con comisiones de compra y venta
- Establece el guaraní (PYG) como moneda base
- Configura decimales apropiados por moneda

**Monedas incluidas:**

.. code-block:: text

   PYG - Guaraní Paraguayo (base: 1.00, sin comisiones)
   USD - Dólar Estadounidense (base: 7,500, comisión: 300/200)
   EUR - Euro (base: 8,200, comisión: 400/300)
   BRL - Real Brasileño (base: 1,500, comisión: 70/50)
   ARS - Peso Argentino (base: 8.50, comisión: 0.10/0.10)
   GBP - Libra Esterlina (base: 9,500, comisión: 300/200)
   JPY - Yen Japonés (base: 50, comisión: 2/2)
   CAD - Dólar Canadiense (base: 5,500, comisión: 200/150)
   CHF - Franco Suizo (base: 8,500, comisión: 300/200)
   AUD - Dólar Australiano (base: 5,000, comisión: 200/100)
   CNY - Yuan Chino (base: 1,050, comisión: 50/30)

**Uso:**

.. code-block:: bash

   python scripts/create_currencies_test.py

create_clientes_test.py
~~~~~~~~~~~~~~~~~~~~~~~

**Propósito**: Genera clientes de ejemplo con diferentes tipos y características comerciales.

**Funcionalidad:**

- Crea 12 clientes distribuidos en 3 tipos:
  - 3 clientes VIP (límites altos, 15% descuento)
  - 4 clientes Corporativos (límites medios, 10% descuento)
  - 5 clientes Minoristas (límites bajos, 5% descuento)
- Asigna operadores aleatoriamente a cada cliente
- Genera datos comerciales completos (RUC, direcciones, contactos)

**Clientes VIP incluidos:**

- Inversiones Premium S.A.
- Corporación Global Trading
- Elite Finance Group

**Clientes Corporativos incluidos:**

- Importadora del Este S.R.L.
- Constructora San Miguel S.A.
- Agropecuaria del Sur S.A.
- Textil Paraguay S.R.L.

**Clientes Minoristas incluidos:**

- Ferretería Central
- Boutique Elegance
- Librería Universitaria
- Farmacia San José
- Restaurante Don Carlos
- Autopartes Mecánico

**Uso:**

.. code-block:: bash

   python scripts/create_clientes_test.py

**Requisitos previos:**

- Ejecutar ``create_grupos_usuarios_test.py``
- Ejecutar ``create_client_types_test.py``

create_transacciones_test.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Propósito**: Crea transacciones de ejemplo con distribución realista para testing del dashboard.

**Características principales:**

- Distribución inteligente de estados (60% pagadas, 25% pendientes, 10% canceladas, 5% anuladas)
- Tipos de operación realistas (70% compras, 30% ventas)
- Fechas distribuidas inteligentemente:
  - 40% en últimos 7 días
  - 30% en días 8-21
  - 30% en días 22-30
- Horarios de oficina en días laborables, fines de semana ocasionales
- 80% transacciones con cliente, 20% casuales
- Montos y comisiones realistas por tipo de operación

**Distribución temporal inteligente:**

.. code-block:: python

   def generar_fecha_realista():
       # 40% últimos 7 días (más actividad reciente)
       # 30% días 8-21 (actividad media)
       # 30% días 22-30 (actividad pasada)
       # 70% días laborables, 30% fines de semana
       # Horarios de oficina más probables

**Funcionalidad avanzada:**

- Calcula tasas de cambio según tipo de operación
- Aplica comisiones de métodos de pago/cobro
- Calcula descuentos por tipo de cliente
- Genera códigos de verificación únicos
- Asigna fechas de pago para transacciones completadas

**Uso:**

.. code-block:: bash

   python scripts/create_transacciones_test.py

   # Con cantidad personalizada
   CANTIDAD_TRANSACCIONES=200 python scripts/create_transacciones_test.py

**Requisitos previos:**

- Todos los scripts anteriores
- ``setup_transacciones`` command

create_metodos_cobro_test.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Propósito**: Crea métodos de cobro básicos con comisiones configuradas.

**Métodos incluidos típicos:**

- Efectivo (0% comisión, todas las monedas)
- Transferencia Bancaria (0.5-1% comisión, PYG/USD)
- Tarjeta de Débito (2-3% comisión, solo PYG)
- Billetera Digital (1-2% comisión, solo PYG)

**Uso:**

.. code-block:: bash

   python scripts/create_metodos_cobro_test.py

create_metodos_pago_test.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Propósito**: Crea métodos de pago básicos con comisiones de entrega.

**Métodos incluidos típicos:**

- Efectivo (0% comisión, todas las monedas)
- Transferencia Bancaria (0.5-1% comisión, PYG/USD)
- Tarjeta de Crédito (3-5% comisión, PYG/USD)
- Cheque (1-2% comisión, PYG/USD)

**Uso:**

.. code-block:: bash

   python scripts/create_metodos_pago_test.py

Scripts de Configuración del Sistema
------------------------------------

create_grupos_usuarios_test.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Propósito**: Crea grupos de usuarios del sistema con permisos apropiados.

**Grupos creados:**

- **Admin**: Permisos completos del sistema
- **Operador**: Permisos para procesar transacciones
- **Supervisor**: Permisos de supervisión y reportes
- **Auditor**: Permisos de solo lectura para auditoría

**Uso:**

.. code-block:: bash

   python scripts/create_grupos_usuarios_test.py

create_tipos_cliente_test.py
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

**Propósito**: Crea tipos de cliente con descuentos diferenciados.

**Tipos creados:**

- **VIP**: 15% descuento, para grandes clientes
- **Corporativo**: 10% descuento, para empresas
- **Minorista**: 5% descuento, para pequeños comercios
- **Casual**: 0% descuento, para clientes ocasionales

**Uso:**

.. code-block:: bash

   python scripts/create_tipos_cliente_test.py

Scripts de Utilidades
---------------------

create_historical_rates.py
~~~~~~~~~~~~~~~~~~~~~~~~~~

**Propósito**: Genera tasas de cambio históricas para análisis y reportes.

**Funcionalidad:**

- Crea series temporales de tasas de cambio
- Simula variaciones realistas de mercado
- Útil para testing de reportes históricos
- Permite análisis de tendencias

**Uso:**

.. code-block:: bash

   python scripts/create_historical_rates.py

check_admin_group.py
~~~~~~~~~~~~~~~~~~~~

**Propósito**: Verifica la existencia y configuración del grupo Admin.

**Funcionalidad:**

- Verifica existencia del grupo Admin
- Lista permisos asignados
- Identifica usuarios miembros
- Reporta estado de configuración

**Uso:**

.. code-block:: bash

   python scripts/check_admin_group.py

Scripts de Creación de Usuarios
-------------------------------

create_user.sh
~~~~~~~~~~~~~~

**Propósito**: Script de shell para crear superusuarios de manera interactiva.

**Funcionalidad:**

- Interfaz interactiva para datos de usuario
- Validación de entrada
- Asignación automática a grupo Admin
- Compatible con sistemas Unix/Linux

**Uso:**

.. code-block:: bash

   ./scripts/create_user.sh

create_user.bat
~~~~~~~~~~~~~~~

**Propósito**: Versión de Windows del script de creación de usuarios.

**Funcionalidad:**

- Equivalente de Windows del script shell
- Misma funcionalidad adaptada a CMD/PowerShell

**Uso:**

.. code-block:: batch

   scripts\create_user.bat

Scripts de Despliegue
--------------------

entrypoint.sh
~~~~~~~~~~~~~

**Propósito**: Script de entrada para contenedores Docker.

**Funcionalidad:**

- Ejecuta migraciones automáticamente
- Carga datos iniciales si es necesario
- Configura el entorno de producción
- Inicia servicios requeridos

**Uso típico en Dockerfile:**

.. code-block:: dockerfile

   COPY scripts/entrypoint.sh /entrypoint.sh
   RUN chmod +x /entrypoint.sh
   ENTRYPOINT ["/entrypoint.sh"]

Patrones Comunes
----------------

**Estructura típica de script:**

.. code-block:: python

   #!/usr/bin/env python3
   """
   Descripción del script.
   """

   import os
   import sys
   import django

   # Configurar Django
   os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'global_exchange.settings')
   django.setup()

   # Imports de modelos
   from app.models import Modelo

   def crear_datos():
       """Función principal de creación"""
       pass

   def verificar_datos():
       """Verificación de datos creados"""
       pass

   def main():
       """Función principal"""
       try:
           # Lógica principal
           pass
       except Exception as e:
           print(f"Error: {e}")
           sys.exit(1)

   if __name__ == '__main__':
       main()

**Características comunes:**

- Configuración automática de Django
- Manejo robusto de errores
- Reportes detallados con emojis
- Verificación de prerequisitos
- Mensajes informativos de progreso

Uso Recomendado
---------------

**Orden de ejecución para setup completo:**

.. code-block:: bash

   # 1. Monedas y tasas
   python scripts/create_currencies_test.py

   # 2. Métodos de pago/cobro
   python scripts/create_metodos_pago_test.py
   python scripts/create_metodos_cobro_test.py

   # 3. Grupos y usuarios
   python scripts/create_grupos_usuarios_test.py

   # 4. Tipos de cliente
   python scripts/create_tipos_cliente_test.py

   # 5. Clientes
   python scripts/create_clientes_test.py

   # 6. Setup de transacciones
   python manage.py setup_transacciones

   # 7. Transacciones de ejemplo
   python scripts/create_transacciones_test.py

**Para desarrollo diario:**

.. code-block:: bash

   # Reset completo de datos de prueba
   python manage.py flush
   # Ejecutar secuencia completa arriba

**Para demos:**

.. code-block:: bash

   # Solo datos esenciales
   python scripts/create_currencies_test.py
   python scripts/create_clientes_test.py
   CANTIDAD_TRANSACCIONES=50 python scripts/create_transacciones_test.py

Consideraciones Importantes
---------------------------

**Performance:**

- Scripts diseñados para entornos de desarrollo
- Pueden ser lentos con grandes volúmenes de datos
- Incluyen validaciones exhaustivas que ralentizan ejecución

**Datos generados:**

- Todos los datos son ficticios y para testing únicamente
- RUCs, direcciones y teléfonos son simulados
- No usar en producción sin modificaciones

**Mantenimiento:**

- Actualizar datos periódicamente para mantener relevancia
- Ajustar distribuciones según necesidades de testing
- Monitorear performance de scripts con datos grandes