# Chat Export (2025-10-31)

## Conversación

### Usuario
Quiero que el mock data de stock en tausers y las transacciones sean todos numeros enteros. Estan bien los numeros pero sin decimales para no complicarnos.

### Asistente
- Ajusté el generador de Tausers para que todo el flujo de stock trabaje con enteros (`scripts/create_tausers_test.py`).
- Modifiqué el generador de transacciones para avanzar con montos, comisiones y descuentos como enteros (`scripts/create_transacciones_test.py`).
- Sugerí reejecutar ambos scripts para regenerar datos.

### Usuario
Se habilitó el grupo *Admin* y `make app-setup` lanzó error al poblar monedas:  
`scripts/create_currencies_test.py`, línea 28, **SyntaxError** por posible coma faltante.

### Asistente
- Revisé `scripts/create_currencies_test.py`.
- Añadí la coma que faltaba en la definición de la moneda PYG.
- Ejecuté `python -m compileall scripts/create_currencies_test.py` sin errores.
- Recomendé reintentar `make app-setup` o `make create-currencies`.

### Usuario
Exportame este chat en formato .md

### Asistente
Preparé este archivo con el historial conversacional en Markdown.

