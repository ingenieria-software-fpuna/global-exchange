# Modificar dashboard para mostrar solo simulador
_Exported on 9/21/2025 at 14:21:55 GMT-3 from Cursor (1.5.5)_

---

**User**

En el dashboard de tasa de cambios quiero que esté solamente el simulador de cambios. No quiero las 4 tarjetas sobre datos de cotizaciones ni la tarjeta de recientes.

---

**Cursor**

Entiendo que quieres simplificar el dashboard de tasa de cambios para mostrar únicamente el simulador de cambios, eliminando las tarjetas de datos de cotizaciones y la tarjeta de recientes. Voy a revisar el archivo actual y hacer los cambios necesarios.


Ahora voy a crear un todo para planificar los cambios necesarios:


Ahora voy a realizar los cambios para simplificar el dashboard, eliminando las tarjetas de estadísticas y la tarjeta de recientes, dejando únicamente el simulador de cambios:


```django-html
{% extends "base.html" %}
{% load moneda_extras %}

{% block title %}Dashboard de Cotizaciones{% endblock %}

{% block content %}
<div class="container py-4">
  <div class="d-flex justify-content-between align-items-center mb-4">
    <h1 class="h3 mb-0">{{ titulo }}</h1>
  </div>


  <!-- Simulador de Cambio -->
  <div class="row g-4">
    <div class="col-12 col-lg-7">
      <div class="card shadow-sm">
        <div class="card-body">
          <div class="d-flex align-items-center justify-content-between mb-3">
            <h5 class="card-title mb-0"><i class="fas fa-calculator me-2"></i>Simulador de cambio</h5>
            <span class="badge bg-light text-dark">Base: PYG</span>
          </div>

          <!-- Selector de Cliente (solo los asociados al usuario) -->
          <div class="row g-3 mb-1">
            <div class="col-12">
              <label class="form-label">Cliente</label>
              <select id="cliente" class="form-select">
                <option value="">Sin cliente (sin descuento)</option>
                {% for c in clientes %}
                  <option value="{{ c.id }}">{{ c.nombre_comercial }} — {{ c.tipo_cliente.nombre }} ({{ c.tipo_cliente.descuento }}%)</option>
                {% empty %}
                  <option value="" disabled>No tiene clientes asociados</option>
                {% endfor %}
              </select>
            </div>
          </div>

          <!-- Selector de Método de Pago -->
          <div class="row g-3 mb-3">
            <div class="col-12">
              <label class="form-label">Método de Pago</label>
              <select id="metodo_pago" class="form-select">
                <option value="">Sin método (sin comisión)</option>
                {% for mp in metodos_pago %}
                  <option value="{{ mp.id }}">{{ mp.nombre }} ({{ mp.comision }}%)</option>
                {% empty %}
                  <option value="" disabled>No hay métodos de pago activos</option>
                {% endfor %}
              </select>
            </div>
          </div>

          <div class="row g-3">
            <div class="col-12 col-md-4">
              <label class="form-label">Monto</label>
              <input id="monto" type="number" class="form-control" placeholder="0.00" step="any" min="0" value="1000">
            </div>
            <div class="col-12 col-md-3">
              <label class="form-label">De</label>
              <select id="origen" class="form-select">
                <option value="PYG" selected>Guaraní (PYG)</option>
              </select>
            </div>
            <div class="col-12 col-md-2 d-flex align-items-end justify-content-center">
              <button id="btnToggleDir" type="button" class="btn btn-outline-secondary btn-rounded w-100" title="Cambiar dirección" aria-label="Cambiar dirección">
                <i class="fas fa-right-left"></i>
              </button>
            </div>
            <div class="col-12 col-md-3">
              <label class="form-label">A</label>
              <select id="destino" class="form-select">
                {% for m in monedas %}
                  {% if m.codigo != 'PYG' %}
                    <option value="{{ m.codigo }}" {% if m.codigo == 'USD' %}selected{% endif %}>{{ m.nombre }} ({{ m.codigo }})</option>
                  {% endif %}
                {% endfor %}
              </select>
            </div>
          </div>

          <hr class="my-4">

          <div id="resultado" class="p-3 bg-light rounded">
            <div class="d-flex align-items-center gap-2 mb-1">
              <i class="fas fa-rotate me-1 text-primary"></i>
              <span class="text-muted">Resultado</span>
            </div>
            <div class="fs-4 fw-bold" id="resultado_valor">—</div>
            <div class="small text-muted" id="resultado_detalle">Selecciona monedas y monto para simular.</div>
            <div class="small" id="resultado_subtotal"></div>
            <div class="small text-danger" id="resultado_comision"></div>
            <div class="small" id="resultado_tasas"></div>
            <div class="small text-success" id="resultado_descuento"></div>
          </div>
        </div>
      </div>
    </div>

    <div class="col-12 col-lg-5">
      <div class="card h-100 shadow-sm">
        <div class="card-body">
          <h5 class="card-title mb-3"><i class="fas fa-clock me-2"></i>Recientes</h5>
          <ul class="list-group list-group-flush">
            {% for t in cotizaciones_recientes %}
              <li class="list-group-item d-flex justify-content-between align-items-center">
                <div>
                  <span class="me-2"><i class="{{ t.moneda.codigo|get_icono_moneda }} text-primary"></i></span>
                  <strong>{{ t.moneda.codigo }}</strong>
                  <small class="text-muted">Base {{ t.precio_base|formatear_guaranies }} · Com. C/V {{ t.comision_compra|formatear_guaranies }}/{{ t.comision_venta|formatear_guaranies }}</small>
                </div>
                <span class="badge {% if t.es_activa %}bg-success{% else %}bg-secondary{% endif %}">
                  {% if t.es_activa %}Activa{% else %}Inactiva{% endif %}
                </span>
              </li>
            {% empty %}
              <li class="list-group-item text-muted">Sin cotizaciones recientes</li>
            {% endfor %}
          </ul>
        </div>
      </div>
    </div>
  </div>
</div>

<script type="application/json" id="monedas-data">{% for m in monedas %}{"codigo": "{{ m.codigo }}", "nombre": "{{ m.nombre|escapejs }}"}{% if not forloop.last %},{% endif %}{% endfor %}</script>
<script>
  (function() {
    const $monto = document.getElementById('monto');
    const $origen = document.getElementById('origen');
    const $destino = document.getElementById('destino');
    const $resValor = document.getElementById('resultado_valor');
    const $resDetalle = document.getElementById('resultado_detalle');
    const $resTasas = document.getElementById('resultado_tasas');
    const $resDesc = document.getElementById('resultado_descuento');
    const $btnToggle = document.getElementById('btnToggleDir');
    const $cliente = document.getElementById('cliente');
    const $metodoPago = document.getElementById('metodo_pago');

    // Dataset de monedas activas (no incluye PYG normalmente)
    const monedasData = JSON.parse('[' + document.getElementById('monedas-data').textContent + ']');
    const MONEDAS = monedasData.filter(m => m.codigo !== 'PYG');

    function setOptions(el, options, selected) {
      el.innerHTML = options.map(o => `<option value="${o.codigo}" ${o.codigo===selected?'selected':''}>${o.nombre} (${o.codigo})</option>`).join('');
    }

    let monedaToPYG = false; // false: PYG -> Moneda (default), true: Moneda -> PYG

    function applyDirection(preserveCode) {
      if (monedaToPYG) {
        // Moneda -> PYG
        const prefer = preserveCode || 'USD';
        setOptions($origen, MONEDAS, prefer);
        $origen.disabled = false;
        $destino.innerHTML = '<option value="PYG" selected>Guaraní (PYG)</option>';
        $destino.disabled = true;
      } else {
        // PYG -> Moneda
        $origen.innerHTML = '<option value="PYG" selected>Guaraní (PYG)</option>';
        $origen.disabled = true;
        const prefer = preserveCode || 'USD';
        const sel = MONEDAS.find(m => m.codigo === prefer) ? prefer : (MONEDAS[0]?.codigo || '');
        setOptions($destino, MONEDAS, sel);
        $destino.disabled = false;
      }
    }

    function getCurrentNonPYG() {
      // Devuelve el código de la moneda no-PYG actualmente seleccionada
      if (monedaToPYG) return $origen.value;
      return $destino.value;
    }

    function simulate() {
      const monto = $monto.value;
      const origen = $origen.value;
      const destino = $destino.value;
      const cliente = $cliente.value;
      const metodoPago = $metodoPago ? $metodoPago.value : '';
      if (!monto || !origen || !destino) return;

      const params = new URLSearchParams({
        monto: String(monto),
        origen: String(origen),
        destino: String(destino),
      });
      if (cliente) params.append('cliente_id', cliente);
      if (metodoPago) params.append('metodo_pago_id', metodoPago);

      fetch(`{% url 'tasa_cambio:simular_cambio_api' %}?${params.toString()}`)
        .then(r => r.json())
        .then(data => {
          if (!data.success) {
            $resValor.textContent = '—';
            $resDetalle.textContent = data.message || 'Error en la simulación.';
            $resTasas.textContent = '';
            $resDesc.textContent = '';
            return;
          }
          const d = data.data;
          $resValor.textContent = formatDisplayWithDots(d.resultado_formateado);
          $resDetalle.textContent = d.detalle;
          const $resSubtotal = document.getElementById('resultado_subtotal');
          const $resComision = document.getElementById('resultado_comision');
          if (d.subtotal_formateado) {
            $resSubtotal.textContent = `Sub-total: ${formatDisplayWithDots(d.subtotal_formateado)}`;
          } else { $resSubtotal.textContent = ''; }
          if (d.comision_pct && d.comision_monto_formateado) {
            $resComision.textContent = `Comisión (${d.comision_pct}%): ${formatDisplayWithDots(d.comision_monto_formateado)}`;
          } else { $resComision.textContent = ''; }
          const t1 = d.tasa_origen ? `${d.tasa_origen.moneda} (${d.tasa_origen.tipo}): ${d.tasa_origen.valor}` : null;
          const t2 = d.tasa_destino ? `${d.tasa_destino.moneda} (${d.tasa_destino.tipo}): ${d.tasa_destino.valor}` : null;
          const parts = [t1, t2].filter(Boolean);
          $resTasas.textContent = parts.length ? `Tasas usadas: ${parts.join(' · ')}` : '';
          if (d.cliente && d.cliente.descuento > 0) {
            $resDesc.textContent = `Cliente: ${d.cliente.nombre} — ${d.cliente.tipo} (descuento ${d.cliente.descuento}%)`;
          } else {
            $resDesc.textContent = '';
          }
        })
        .catch(() => {
          $resValor.textContent = '—';
          $resDetalle.textContent = 'No se pudo simular.';
          $resTasas.textContent = '';
          $resDesc.textContent = '';
          const $resSubtotal = document.getElementById('resultado_subtotal');
          const $resComision = document.getElementById('resultado_comision');
          if ($resSubtotal) $resSubtotal.textContent = '';
          if ($resComision) $resComision.textContent = '';
        });
    }

    $monto.addEventListener('input', simulate);
    $origen.addEventListener('change', simulate);
    $destino.addEventListener('change', simulate);
    $cliente.addEventListener('change', simulate);
    if ($metodoPago) $metodoPago.addEventListener('change', simulate);
    $btnToggle.addEventListener('click', () => {
      const keep = getCurrentNonPYG();
      monedaToPYG = !monedaToPYG;
      applyDirection(keep);
      simulate();
    });

    // Inicializar dirección por defecto (PYG -> USD)
    // Helpers: format numbers with dot thousands separators
    function formatDisplayWithDots(str) {
      if (!str) return str;
      const m = String(str).match(/^(\D*)([-\d.,]+)(.*)$/);
      if (!m) return str;
      const prefix = m[1] || '';
      const number = m[2] || '';
      const suffix = m[3] || '';
      // Detect decimal separator as last occurrence of '.' or ','
      const lastDot = number.lastIndexOf('.');
      const lastComma = number.lastIndexOf(',');
      let decSepIndex = Math.max(lastDot, lastComma);
      let intPart = number;
      let decPart = '';
      let sep = '';
      if (decSepIndex > -1) {
        sep = number[decSepIndex];
        intPart = number.slice(0, decSepIndex);
        decPart = number.slice(decSepIndex + 1);
      }
      // Remove existing thousand separators (',' or '.') from intPart just in case, keep minus
      const neg = intPart.startsWith('-');
      const intDigits = intPart.replace(/[^\d]/g, '');
      const grouped = intDigits.replace(/\B(?=(\d{3})+(?!\d))/g, '.');
      const intFinal = neg ? '-' + grouped : grouped;
      const numFinal = decPart ? `${intFinal}${sep}${decPart}` : intFinal;
      return `${prefix}${numFinal}${suffix}`;
    }

    applyDirection();
    simulate();
  })();
</script>
{% endblock %}

```

Ahora voy a eliminar la tarjeta de cotizaciones recientes:


```django-html
{% extends "base.html" %}
{% load moneda_extras %}

{% block title %}Dashboard de Cotizaciones{% endblock %}

{% block content %}
<div class="container py-4">
  <div class="d-flex justify-content-between align-items-center mb-4">
    <h1 class="h3 mb-0">{{ titulo }}</h1>
  </div>


  <!-- Simulador de Cambio -->
  <div class="row g-4">
    <div class="col-12 col-lg-7">
      <div class="card shadow-sm">
        <div class="card-body">
          <div class="d-flex align-items-center justify-content-between mb-3">
            <h5 class="card-title mb-0"><i class="fas fa-calculator me-2"></i>Simulador de cambio</h5>
            <span class="badge bg-light text-dark">Base: PYG</span>
          </div>

          <!-- Selector de Cliente (solo los asociados al usuario) -->
          <div class="row g-3 mb-1">
            <div class="col-12">
              <label class="form-label">Cliente</label>
              <select id="cliente" class="form-select">
                <option value="">Sin cliente (sin descuento)</option>
                {% for c in clientes %}
                  <option value="{{ c.id }}">{{ c.nombre_comercial }} — {{ c.tipo_cliente.nombre }} ({{ c.tipo_cliente.descuento }}%)</option>
                {% empty %}
                  <option value="" disabled>No tiene clientes asociados</option>
                {% endfor %}
              </select>
            </div>
          </div>

          <!-- Selector de Método de Pago -->
          <div class="row g-3 mb-3">
            <div class="col-12">
              <label class="form-label">Método de Pago</label>
              <select id="metodo_pago" class="form-select">
                <option value="">Sin método (sin comisión)</option>
                {% for mp in metodos_pago %}
                  <option value="{{ mp.id }}">{{ mp.nombre }} ({{ mp.comision }}%)</option>
                {% empty %}
                  <option value="" disabled>No hay métodos de pago activos</option>
                {% endfor %}
              </select>
            </div>
          </div>

          <div class="row g-3">
            <div class="col-12 col-md-4">
              <label class="form-label">Monto</label>
              <input id="monto" type="number" class="form-control" placeholder="0.00" step="any" min="0" value="1000">
            </div>
            <div class="col-12 col-md-3">
              <label class="form-label">De</label>
              <select id="origen" class="form-select">
                <option value="PYG" selected>Guaraní (PYG)</option>
              </select>
            </div>
            <div class="col-12 col-md-2 d-flex align-items-end justify-content-center">
              <button id="btnToggleDir" type="button" class="btn btn-outline-secondary btn-rounded w-100" title="Cambiar dirección" aria-label="Cambiar dirección">
                <i class="fas fa-right-left"></i>
              </button>
            </div>
            <div class="col-12 col-md-3">
              <label class="form-label">A</label>
              <select id="destino" class="form-select">
                {% for m in monedas %}
                  {% if m.codigo != 'PYG' %}
                    <option value="{{ m.codigo }}" {% if m.codigo == 'USD' %}selected{% endif %}>{{ m.nombre }} ({{ m.codigo }})</option>
                  {% endif %}
                {% endfor %}
              </select>
            </div>
          </div>

          <hr class="my-4">

          <div id="resultado" class="p-3 bg-light rounded">
            <div class="d-flex align-items-center gap-2 mb-1">
              <i class="fas fa-rotate me-1 text-primary"></i>
              <span class="text-muted">Resultado</span>
            </div>
            <div class="fs-4 fw-bold" id="resultado_valor">—</div>
            <div class="small text-muted" id="resultado_detalle">Selecciona monedas y monto para simular.</div>
            <div class="small" id="resultado_subtotal"></div>
            <div class="small text-danger" id="resultado_comision"></div>
            <div class="small" id="resultado_tasas"></div>
            <div class="small text-success" id="resultado_descuento"></div>
          </div>
        </div>
      </div>
    </div>

  </div>
</div>

<script type="application/json" id="monedas-data">{% for m in monedas %}{"codigo": "{{ m.codigo }}", "nombre": "{{ m.nombre|escapejs }}"}{% if not forloop.last %},{% endif %}{% endfor %}</script>
<script>
  (function() {
    const $monto = document.getElementById('monto');
    const $origen = document.getElementById('origen');
    const $destino = document.getElementById('destino');
    const $resValor = document.getElementById('resultado_valor');
    const $resDetalle = document.getElementById('resultado_detalle');
    const $resTasas = document.getElementById('resultado_tasas');
    const $resDesc = document.getElementById('resultado_descuento');
    const $btnToggle = document.getElementById('btnToggleDir');
    const $cliente = document.getElementById('cliente');
    const $metodoPago = document.getElementById('metodo_pago');

    // Dataset de monedas activas (no incluye PYG normalmente)
    const monedasData = JSON.parse('[' + document.getElementById('monedas-data').textContent + ']');
    const MONEDAS = monedasData.filter(m => m.codigo !== 'PYG');

    function setOptions(el, options, selected) {
      el.innerHTML = options.map(o => `<option value="${o.codigo}" ${o.codigo===selected?'selected':''}>${o.nombre} (${o.codigo})</option>`).join('');
    }

    let monedaToPYG = false; // false: PYG -> Moneda (default), true: Moneda -> PYG

    function applyDirection(preserveCode) {
      if (monedaToPYG) {
        // Moneda -> PYG
        const prefer = preserveCode || 'USD';
        setOptions($origen, MONEDAS, prefer);
        $origen.disabled = false;
        $destino.innerHTML = '<option value="PYG" selected>Guaraní (PYG)</option>';
        $destino.disabled = true;
      } else {
        // PYG -> Moneda
        $origen.innerHTML = '<option value="PYG" selected>Guaraní (PYG)</option>';
        $origen.disabled = true;
        const prefer = preserveCode || 'USD';
        const sel = MONEDAS.find(m => m.codigo === prefer) ? prefer : (MONEDAS[0]?.codigo || '');
        setOptions($destino, MONEDAS, sel);
        $destino.disabled = false;
      }
    }

    function getCurrentNonPYG() {
      // Devuelve el código de la moneda no-PYG actualmente seleccionada
      if (monedaToPYG) return $origen.value;
      return $destino.value;
    }

    function simulate() {
      const monto = $monto.value;
      const origen = $origen.value;
      const destino = $destino.value;
      const cliente = $cliente.value;
      const metodoPago = $metodoPago ? $metodoPago.value : '';
      if (!monto || !origen || !destino) return;

      const params = new URLSearchParams({
        monto: String(monto),
        origen: String(origen),
        destino: String(destino),
      });
      if (cliente) params.append('cliente_id', cliente);
      if (metodoPago) params.append('metodo_pago_id', metodoPago);

      fetch(`{% url 'tasa_cambio:simular_cambio_api' %}?${params.toString()}`)
        .then(r => r.json())
        .then(data => {
          if (!data.success) {
            $resValor.textContent = '—';
            $resDetalle.textContent = data.message || 'Error en la simulación.';
            $resTasas.textContent = '';
            $resDesc.textContent = '';
            return;
          }
          const d = data.data;
          $resValor.textContent = formatDisplayWithDots(d.resultado_formateado);
          $resDetalle.textContent = d.detalle;
          const $resSubtotal = document.getElementById('resultado_subtotal');
          const $resComision = document.getElementById('resultado_comision');
          if (d.subtotal_formateado) {
            $resSubtotal.textContent = `Sub-total: ${formatDisplayWithDots(d.subtotal_formateado)}`;
          } else { $resSubtotal.textContent = ''; }
          if (d.comision_pct && d.comision_monto_formateado) {
            $resComision.textContent = `Comisión (${d.comision_pct}%): ${formatDisplayWithDots(d.comision_monto_formateado)}`;
          } else { $resComision.textContent = ''; }
          const t1 = d.tasa_origen ? `${d.tasa_origen.moneda} (${d.tasa_origen.tipo}): ${d.tasa_origen.valor}` : null;
          const t2 = d.tasa_destino ? `${d.tasa_destino.moneda} (${d.tasa_destino.tipo}): ${d.tasa_destino.valor}` : null;
          const parts = [t1, t2].filter(Boolean);
          $resTasas.textContent = parts.length ? `Tasas usadas: ${parts.join(' · ')}` : '';
          if (d.cliente && d.cliente.descuento > 0) {
            $resDesc.textContent = `Cliente: ${d.cliente.nombre} — ${d.cliente.tipo} (descuento ${d.cliente.descuento}%)`;
          } else {
            $resDesc.textContent = '';
          }
        })
        .catch(() => {
          $resValor.textContent = '—';
          $resDetalle.textContent = 'No se pudo simular.';
          $resTasas.textContent = '';
          $resDesc.textContent = '';
          const $resSubtotal = document.getElementById('resultado_subtotal');
          const $resComision = document.getElementById('resultado_comision');
          if ($resSubtotal) $resSubtotal.textContent = '';
          if ($resComision) $resComision.textContent = '';
        });
    }

    $monto.addEventListener('input', simulate);
    $origen.addEventListener('change', simulate);
    $destino.addEventListener('change', simulate);
    $cliente.addEventListener('change', simulate);
    if ($metodoPago) $metodoPago.addEventListener('change', simulate);
    $btnToggle.addEventListener('click', () => {
      const keep = getCurrentNonPYG();
      monedaToPYG = !monedaToPYG;
      applyDirection(keep);
      simulate();
    });

    // Inicializar dirección por defecto (PYG -> USD)
    // Helpers: format numbers with dot thousands separators
    function formatDisplayWithDots(str) {
      if (!str) return str;
      const m = String(str).match(/^(\D*)([-\d.,]+)(.*)$/);
      if (!m) return str;
      const prefix = m[1] || '';
      const number = m[2] || '';
      const suffix = m[3] || '';
      // Detect decimal separator as last occurrence of '.' or ','
      const lastDot = number.lastIndexOf('.');
      const lastComma = number.lastIndexOf(',');
      let decSepIndex = Math.max(lastDot, lastComma);
      let intPart = number;
      let decPart = '';
      let sep = '';
      if (decSepIndex > -1) {
        sep = number[decSepIndex];
        intPart = number.slice(0, decSepIndex);
        decPart = number.slice(decSepIndex + 1);
      }
      // Remove existing thousand separators (',' or '.') from intPart just in case, keep minus
      const neg = intPart.startsWith('-');
      const intDigits = intPart.replace(/[^\d]/g, '');
      const grouped = intDigits.replace(/\B(?=(\d{3})+(?!\d))/g, '.');
      const intFinal = neg ? '-' + grouped : grouped;
      const numFinal = decPart ? `${intFinal}${sep}${decPart}` : intFinal;
      return `${prefix}${numFinal}${suffix}`;
    }

    applyDirection();
    simulate();
  })();
</script>
{% endblock %}

```

Ahora voy a ajustar el layout del simulador para que ocupe todo el ancho disponible, cambiando de `col-12 col-lg-7` a `col-12`:


```django-html
{% extends "base.html" %}
{% load moneda_extras %}

{% block title %}Dashboard de Cotizaciones{% endblock %}

{% block content %}
<div class="container py-4">
  <div class="d-flex justify-content-between align-items-center mb-4">
    <h1 class="h3 mb-0">{{ titulo }}</h1>
  </div>


  <!-- Simulador de Cambio -->
  <div class="row g-4">
    <div class="col-12">
      <div class="card shadow-sm">
        <div class="card-body">
          <div class="d-flex align-items-center justify-content-between mb-3">
            <h5 class="card-title mb-0"><i class="fas fa-calculator me-2"></i>Simulador de cambio</h5>
            <span class="badge bg-light text-dark">Base: PYG</span>
          </div>

          <!-- Selector de Cliente (solo los asociados al usuario) -->
          <div class="row g-3 mb-1">
            <div class="col-12">
              <label class="form-label">Cliente</label>
              <select id="cliente" class="form-select">
                <option value="">Sin cliente (sin descuento)</option>
                {% for c in clientes %}
                  <option value="{{ c.id }}">{{ c.nombre_comercial }} — {{ c.tipo_cliente.nombre }} ({{ c.tipo_cliente.descuento }}%)</option>
                {% empty %}
                  <option value="" disabled>No tiene clientes asociados</option>
                {% endfor %}
              </select>
            </div>
          </div>

          <!-- Selector de Método de Pago -->
          <div class="row g-3 mb-3">
            <div class="col-12">
              <label class="form-label">Método de Pago</label>
              <select id="metodo_pago" class="form-select">
                <option value="">Sin método (sin comisión)</option>
                {% for mp in metodos_pago %}
                  <option value="{{ mp.id }}">{{ mp.nombre }} ({{ mp.comision }}%)</option>
                {% empty %}
                  <option value="" disabled>No hay métodos de pago activos</option>
                {% endfor %}
              </select>
            </div>
          </div>

          <div class="row g-3">
            <div class="col-12 col-md-4">
              <label class="form-label">Monto</label>
              <input id="monto" type="number" class="form-control" placeholder="0.00" step="any" min="0" value="1000">
            </div>
            <div class="col-12 col-md-3">
              <label class="form-label">De</label>
              <select id="origen" class="form-select">
                <option value="PYG" selected>Guaraní (PYG)</option>
              </select>
            </div>
            <div class="col-12 col-md-2 d-flex align-items-end justify-content-center">
              <button id="btnToggleDir" type="button" class="btn btn-outline-secondary btn-rounded w-100" title="Cambiar dirección" aria-label="Cambiar dirección">
                <i class="fas fa-right-left"></i>
              </button>
            </div>
            <div class="col-12 col-md-3">
              <label class="form-label">A</label>
              <select id="destino" class="form-select">
                {% for m in monedas %}
                  {% if m.codigo != 'PYG' %}
                    <option value="{{ m.codigo }}" {% if m.codigo == 'USD' %}selected{% endif %}>{{ m.nombre }} ({{ m.codigo }})</option>
                  {% endif %}
                {% endfor %}
              </select>
            </div>
          </div>

          <hr class="my-4">

          <div id="resultado" class="p-3 bg-light rounded">
            <div class="d-flex align-items-center gap-2 mb-1">
              <i class="fas fa-rotate me-1 text-primary"></i>
              <span class="text-muted">Resultado</span>
            </div>
            <div class="fs-4 fw-bold" id="resultado_valor">—</div>
            <div class="small text-muted" id="resultado_detalle">Selecciona monedas y monto para simular.</div>
            <div class="small" id="resultado_subtotal"></div>
            <div class="small text-danger" id="resultado_comision"></div>
            <div class="small" id="resultado_tasas"></div>
            <div class="small text-success" id="resultado_descuento"></div>
          </div>
        </div>
      </div>
    </div>

  </div>
</div>

<script type="application/json" id="monedas-data">{% for m in monedas %}{"codigo": "{{ m.codigo }}", "nombre": "{{ m.nombre|escapejs }}"}{% if not forloop.last %},{% endif %}{% endfor %}</script>
<script>
  (function() {
    const $monto = document.getElementById('monto');
    const $origen = document.getElementById('origen');
    const $destino = document.getElementById('destino');
    const $resValor = document.getElementById('resultado_valor');
    const $resDetalle = document.getElementById('resultado_detalle');
    const $resTasas = document.getElementById('resultado_tasas');
    const $resDesc = document.getElementById('resultado_descuento');
    const $btnToggle = document.getElementById('btnToggleDir');
    const $cliente = document.getElementById('cliente');
    const $metodoPago = document.getElementById('metodo_pago');

    // Dataset de monedas activas (no incluye PYG normalmente)
    const monedasData = JSON.parse('[' + document.getElementById('monedas-data').textContent + ']');
    const MONEDAS = monedasData.filter(m => m.codigo !== 'PYG');

    function setOptions(el, options, selected) {
      el.innerHTML = options.map(o => `<option value="${o.codigo}" ${o.codigo===selected?'selected':''}>${o.nombre} (${o.codigo})</option>`).join('');
    }

    let monedaToPYG = false; // false: PYG -> Moneda (default), true: Moneda -> PYG

    function applyDirection(preserveCode) {
      if (monedaToPYG) {
        // Moneda -> PYG
        const prefer = preserveCode || 'USD';
        setOptions($origen, MONEDAS, prefer);
        $origen.disabled = false;
        $destino.innerHTML = '<option value="PYG" selected>Guaraní (PYG)</option>';
        $destino.disabled = true;
      } else {
        // PYG -> Moneda
        $origen.innerHTML = '<option value="PYG" selected>Guaraní (PYG)</option>';
        $origen.disabled = true;
        const prefer = preserveCode || 'USD';
        const sel = MONEDAS.find(m => m.codigo === prefer) ? prefer : (MONEDAS[0]?.codigo || '');
        setOptions($destino, MONEDAS, sel);
        $destino.disabled = false;
      }
    }

    function getCurrentNonPYG() {
      // Devuelve el código de la moneda no-PYG actualmente seleccionada
      if (monedaToPYG) return $origen.value;
      return $destino.value;
    }

    function simulate() {
      const monto = $monto.value;
      const origen = $origen.value;
      const destino = $destino.value;
      const cliente = $cliente.value;
      const metodoPago = $metodoPago ? $metodoPago.value : '';
      if (!monto || !origen || !destino) return;

      const params = new URLSearchParams({
        monto: String(monto),
        origen: String(origen),
        destino: String(destino),
      });
      if (cliente) params.append('cliente_id', cliente);
      if (metodoPago) params.append('metodo_pago_id', metodoPago);

      fetch(`{% url 'tasa_cambio:simular_cambio_api' %}?${params.toString()}`)
        .then(r => r.json())
        .then(data => {
          if (!data.success) {
            $resValor.textContent = '—';
            $resDetalle.textContent = data.message || 'Error en la simulación.';
            $resTasas.textContent = '';
            $resDesc.textContent = '';
            return;
          }
          const d = data.data;
          $resValor.textContent = formatDisplayWithDots(d.resultado_formateado);
          $resDetalle.textContent = d.detalle;
          const $resSubtotal = document.getElementById('resultado_subtotal');
          const $resComision = document.getElementById('resultado_comision');
          if (d.subtotal_formateado) {
            $resSubtotal.textContent = `Sub-total: ${formatDisplayWithDots(d.subtotal_formateado)}`;
          } else { $resSubtotal.textContent = ''; }
          if (d.comision_pct && d.comision_monto_formateado) {
            $resComision.textContent = `Comisión (${d.comision_pct}%): ${formatDisplayWithDots(d.comision_monto_formateado)}`;
          } else { $resComision.textContent = ''; }
          const t1 = d.tasa_origen ? `${d.tasa_origen.moneda} (${d.tasa_origen.tipo}): ${d.tasa_origen.valor}` : null;
          const t2 = d.tasa_destino ? `${d.tasa_destino.moneda} (${d.tasa_destino.tipo}): ${d.tasa_destino.valor}` : null;
          const parts = [t1, t2].filter(Boolean);
          $resTasas.textContent = parts.length ? `Tasas usadas: ${parts.join(' · ')}` : '';
          if (d.cliente && d.cliente.descuento > 0) {
            $resDesc.textContent = `Cliente: ${d.cliente.nombre} — ${d.cliente.tipo} (descuento ${d.cliente.descuento}%)`;
          } else {
            $resDesc.textContent = '';
          }
        })
        .catch(() => {
          $resValor.textContent = '—';
          $resDetalle.textContent = 'No se pudo simular.';
          $resTasas.textContent = '';
          $resDesc.textContent = '';
          const $resSubtotal = document.getElementById('resultado_subtotal');
          const $resComision = document.getElementById('resultado_comision');
          if ($resSubtotal) $resSubtotal.textContent = '';
          if ($resComision) $resComision.textContent = '';
        });
    }

    $monto.addEventListener('input', simulate);
    $origen.addEventListener('change', simulate);
    $destino.addEventListener('change', simulate);
    $cliente.addEventListener('change', simulate);
    if ($metodoPago) $metodoPago.addEventListener('change', simulate);
    $btnToggle.addEventListener('click', () => {
      const keep = getCurrentNonPYG();
      monedaToPYG = !monedaToPYG;
      applyDirection(keep);
      simulate();
    });

    // Inicializar dirección por defecto (PYG -> USD)
    // Helpers: format numbers with dot thousands separators
    function formatDisplayWithDots(str) {
      if (!str) return str;
      const m = String(str).match(/^(\D*)([-\d.,]+)(.*)$/);
      if (!m) return str;
      const prefix = m[1] || '';
      const number = m[2] || '';
      const suffix = m[3] || '';
      // Detect decimal separator as last occurrence of '.' or ','
      const lastDot = number.lastIndexOf('.');
      const lastComma = number.lastIndexOf(',');
      let decSepIndex = Math.max(lastDot, lastComma);
      let intPart = number;
      let decPart = '';
      let sep = '';
      if (decSepIndex > -1) {
        sep = number[decSepIndex];
        intPart = number.slice(0, decSepIndex);
        decPart = number.slice(decSepIndex + 1);
      }
      // Remove existing thousand separators (',' or '.') from intPart just in case, keep minus
      const neg = intPart.startsWith('-');
      const intDigits = intPart.replace(/[^\d]/g, '');
      const grouped = intDigits.replace(/\B(?=(\d{3})+(?!\d))/g, '.');
      const intFinal = neg ? '-' + grouped : grouped;
      const numFinal = decPart ? `${intFinal}${sep}${decPart}` : intFinal;
      return `${prefix}${numFinal}${suffix}`;
    }

    applyDirection();
    simulate();
  })();
</script>
{% endblock %}

```

Ahora voy a verificar si hay errores de linting en el archivo modificado:


Perfecto! He completado todos los cambios solicitados. El dashboard de tasa de cambios ahora muestra únicamente el simulador de cambios, eliminando:

1. ✅ **Las 4 tarjetas de estadísticas** (Total cotizaciones, Activas, Inactivas, Monedas con cotización activa)
2. ✅ **La tarjeta de cotizaciones recientes** 
3. ✅ **Ajusté el layout** del simulador para que ocupe todo el ancho disponible (cambié de `col-12 col-lg-7` a `col-12`)

El dashboard ahora es mucho más limpio y se enfoca exclusivamente en la funcionalidad del simulador de cambios, que incluye:
- Selector de cliente
- Selector de método de pago  
- Campos para monto y selección de monedas
- Botón para cambiar dirección de conversión
- Área de resultados con detalles de la simulación

Los cambios mantienen toda la funcionalidad del simulador intacta, solo se removieron los elementos visuales que no eran necesarios según tu solicitud.

