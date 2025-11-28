
# Correcciones necesarias en la generación de facturas

Para corregir la generación incorrecta de las facturas, debés modificar el archivo:

```
invoice_generator.py
```

Específicamente dentro de la función:

```
generar_factura_desde_transaccion
```

(aprox. líneas 167–186)

---

## Problema 1 — Monto incorrecto

Actualmente:

```python
monto = float(transaccion.monto_origen)
```

Esto es incorrecto para ventas porque `monto_origen` es la **cantidad de moneda extranjera vendida**, no el monto en guaraníes.

### ✅ Solución

- Para **ventas**, usar `monto_destino` (los guaraníes que recibe el cliente).
- Para **compras**, usar `monto_origen` (los guaraníes que paga el cliente).

---

## Problema 2 — IVA aplicado incorrectamente

Actualmente está configurado como IVA 5%:

```python
'iAfecIVA', '1',
'dPropIVA', '100',
'dTasaIVA', '5',
```

Pero las **operaciones de compra/venta de divisas son exentas de IVA**.

### ✅ Solución

Cambiar a:

- `iAfecIVA = '3'`  → Exento  
- `dPropIVA = '0'`  
- `dTasaIVA = '0'`

---

# Código sugerido corregido

```python
def generar_factura_desde_transaccion(transaccion):
    # ...existing code...

    descripcion_servicio = f"Cambio de divisas - {transaccion.tipo_operacion.nombre}"

    # CORRECCIÓN 1: Usar monto en guaraníes según el tipo de operación
    if transaccion.tipo_operacion.codigo == 'VENTA':
        # Para ventas: usar monto_destino (PYG que recibe el cliente)
        monto = float(transaccion.monto_destino)
    else:
        # Para compras: usar monto_origen (PYG que paga el cliente)
        monto = float(transaccion.monto_origen)

    insert_query = f"""
    INSERT INTO public.gCamItem
    (dCodInt, dDesProSer, dCantProSer, dPUniProSer, dDescItem,
    iAfecIVA, dPropIVA, dTasaIVA,
    dParAranc, dNCM, dDncpG, dDncpE, dGtin, dGtinPq,
    fch_ins, fch_upd,
    de_id) VALUES
    ('1', '{descripcion_servicio}', '1', '{monto}', '0',
    '3', '0', '0',
    '', '', '', '', '', '',
    CURRENT_TIMESTAMP, CURRENT_TIMESTAMP,
    {de_id});
    """

    # ...existing code...
```

---
