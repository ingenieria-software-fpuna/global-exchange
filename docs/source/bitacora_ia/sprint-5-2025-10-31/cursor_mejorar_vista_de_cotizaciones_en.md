# Mejorar vista de cotizaciones en tabla
_Exported on 26/9/2025 at 08:28:56 GMT-4 from Cursor (1.6.45)_

---

**User**

Necesito que mejores la vista de las cotizaciones, utiliza una tabla con las columnas Moneda, compra y venta

---

**Cursor**

Voy a mejorar la vista de las cotizaciones cambiando de tarjetas a una tabla más clara y organizada. Primero, déjame revisar el código actual y luego implementar la mejora.


Ahora voy a crear una tabla más clara y organizada para las cotizaciones, reemplazando las tarjetas actuales. La tabla tendrá columnas para Moneda, Compra y Venta, con un diseño moderno y responsive.


```django-html
{% extends "base.html" %}
{% load moneda_extras %}

{% block title %}Global Exchange - Casa de Cambios{% endblock %}

{% block extra_css %}
<style>
/* Ticker styles scoped to welcome */
.ticker { position: relative; overflow: hidden; background:#fff; border-radius:.75rem; }
.ticker__track {
    display:flex; align-items:center; gap:2rem; white-space:nowrap;
    animation: ticker-scroll 35s linear infinite;
    padding: .75rem 1rem;
}
.ticker:hover .ticker__track { animation-play-state: paused; }
.ticker__item { display:flex; align-items:center; gap:.5rem; color:#0f172a; }
.ticker__label { color:#6c757d; font-size:.9rem; }
.ticker__value { font-weight:700; color:#198754; }
@keyframes ticker-scroll {
  0% { transform: translateX(0); }
  100% { transform: translateX(-50%); }
}
@media (prefers-reduced-motion: reduce) { .ticker__track { animation:none; } }

/* Simulator styles */
.sim-card { border: none; }
.sim-header-badge { background: rgba(13,110,253,.08); color:#0d6efd; }
.sim-result { background: linear-gradient(180deg, #f8fafc 0%, #ffffff 100%); border:1px solid rgba(0,0,0,.06); }
.btn-swap { border-radius: 999px; height: 52px; display:flex; align-items:center; justify-content:center; font-size: 1.1rem; }
.btn-swap i { transition: transform .2s ease; }
.btn-swap:hover i { transform: rotate(180deg); }
</style>
{% endblock %}

{% block main_container_class %}container-fluid p-0{% endblock %}

{% block content %}
<!-- Hero principal -->
<section class="bg-primary text-white py-5 shadow-soft" style="background: linear-gradient(135deg, rgba(13,110,253,1) 0%, rgba(2,62,138,1) 100%);">
    <div class="container py-4">
        <div class="row align-items-center g-4">
            <div class="col-12 text-center">
                <h1 class="display-5 fw-bold mb-2">Global Exchange</h1>
                <p class="lead mb-4">Tu casa de cambios de confianza</p>
                <div class="d-flex justify-content-center gap-2 flex-wrap">
                    {% if user.is_authenticated %}
                    <a href="{% url 'auth:dashboard' %}" class="btn btn-light btn-lg btn-rounded px-4">
                        <i class="fas fa-gauge-high me-2"></i>Ir al Dashboard
                    </a>
                    <a href="{% url 'auth:logout' %}" class="btn btn-outline-light btn-lg btn-rounded px-4">
                        <i class="fas fa-right-from-bracket me-2"></i>Cerrar Sesión
                    </a>
                    {% else %}
                    <a href="{% url 'auth:login' %}" class="btn btn-light btn-lg btn-rounded px-4">
                        <i class="fas fa-right-to-bracket me-2"></i>Iniciar Sesión
                    </a>
                    <a href="{% url 'auth:registro' %}" class="btn btn-outline-light btn-lg btn-rounded px-4">
                        <i class="fas fa-user-plus me-2"></i>Registrarse
                    </a>
                    {% endif %}
                </div>
            </div>
        </div>
    </div>
    <div class="bg-white" style="height: 24px; clip-path: polygon(0 0, 100% 0, 100% 100%, 0 60%);"></div>
</section>



<!-- Ticker de tasas en movimiento -->
{% if monedas_con_tasas %}
<section class="py-3">
  <div class="container">
    <div class="ticker shadow-soft" role="region" aria-label="Cotizaciones en movimiento">
      <div class="ticker__track">
        <!-- Bloque 1 -->
        {% for item in monedas_con_tasas %}
        <span class="ticker__item">
          <i class="{{ item.moneda.codigo|get_icono_moneda }} text-primary"></i>
          <span class="ticker__label">{{ item.moneda.codigo }}</span>
          <span class="ticker__value">{{ item.tasa.tasa_venta|formatear_guaranies }}</span>
          <span class="text-muted">
            Compra {{ item.tasa.tasa_compra|formatear_guaranies }} · 
            Venta {{ item.tasa.tasa_venta|formatear_guaranies }}
          </span>
        </span>
        {% endfor %}

        <!-- Bloque 2 (duplicado para desplazamiento infinito) -->
        {% for item in monedas_con_tasas %}
        <span class="ticker__item">
          <i class="{{ item.moneda.codigo|get_icono_moneda }} text-primary"></i>
          <span class="ticker__label">{{ item.moneda.codigo }}</span>
          <span class="ticker__value">{{ item.tasa.tasa_venta|formatear_guaranies }}</span>
          <span class="text-muted">
            Compra {{ item.tasa.tasa_compra|formatear_guaranies }} · 
            Venta {{ item.tasa.tasa_venta|formatear_guaranies }}
          </span>
        </span>
        {% endfor %}
      </div>
    </div>
  </div>
  <div class="bg-white" style="height: 16px;"></div>
</section>
{% endif %}

<!-- Cotizaciones -->
{% if monedas_con_tasas %}
<section class="py-5">
    <div class="container">
        <div class="text-center mb-5">
            <h2 class="h1 text-primary mb-2">Cotizaciones</h2>
            <p class="text-muted">Moneda base: Guaraní (PYG)</p>
        </div>

        <div class="row justify-content-center">
            <div class="col-12 col-lg-10 col-xl-8">
                <div class="card shadow-soft border-0">
                    <div class="card-body p-0">
                        <div class="table-responsive">
                            <table class="table table-hover mb-0">
                                <thead class="table-primary">
                                    <tr>
                                        <th class="border-0 py-3 px-4">
                                            <i class="fas fa-coins me-2"></i>Moneda
                                        </th>
                                        <th class="border-0 py-3 px-4 text-center">
                                            <i class="fas fa-arrow-down me-2 text-success"></i>Compra
                                        </th>
                                        <th class="border-0 py-3 px-4 text-center">
                                            <i class="fas fa-arrow-up me-2 text-danger"></i>Venta
                                        </th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {% for item in monedas_con_tasas %}
                                    <tr class="align-middle">
                                        <td class="py-3 px-4">
                                            <div class="d-flex align-items-center">
                                                <div class="me-3">
                                                    <i class="{{ item.moneda.codigo|get_icono_moneda }} text-primary fs-4"></i>
                                                </div>
                                                <div>
                                                    <div class="fw-semibold">{{ item.moneda.nombre }}</div>
                                                    <small class="text-muted">{{ item.moneda.codigo }}</small>
                                                </div>
                                            </div>
                                        </td>
                                        <td class="py-3 px-4 text-center">
                                            <span class="fw-bold text-success fs-5">
                                                {{ item.tasa.tasa_compra|formatear_guaranies }}
                                            </span>
                                            <div class="small text-muted">PYG</div>
                                        </td>
                                        <td class="py-3 px-4 text-center">
                                            <span class="fw-bold text-danger fs-5">
                                                {{ item.tasa.tasa_venta|formatear_guaranies }}
                                            </span>
                                            <div class="small text-muted">PYG</div>
                                        </td>
                                    </tr>
                                    {% endfor %}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <div class="row mt-5">
            <div class="col-12">
                <div class="alert alert-info shadow-sm text-center" role="alert">
                    <i class="fas fa-circle-info me-2"></i>
                    <strong>Nota:</strong> Las cotizaciones se actualizan cada hora. Para operaciones específicas, contacta con nuestros agentes.
                </div>
            </div>
        </div>
    </div>
    <div class="bg-white" style="height: 24px; clip-path: polygon(0 0, 100% 40%, 100% 100%, 0 100%);"></div>
</section>
{% else %}
<!-- Mensaje cuando no hay monedas disponibles -->
<section class="py-5">
    <div class="container">
        <div class="text-center">
            <div class="alert alert-warning shadow-sm" role="alert">
                <i class="fas fa-exclamation-triangle me-2"></i>
                <strong>No hay cotizaciones disponibles</strong>
                <p class="mb-0 mt-2">Por favor, contacta con el administrador para configurar las monedas y sus cotizaciones.</p>
            </div>
        </div>
    </div>
</section>
{% endif %}

<!-- Simulador público -->
<section id="simulador" class="py-5 bg-light">
  <div class="container">
    <div class="row justify-content-center">
      <div class="col-12">
        <div class="card sim-card shadow-soft">
          <div class="card-body p-4 p-md-5">
            <div class="d-flex align-items-center justify-content-between mb-4">
              <h3 class="h4 mb-0"><i class="fas fa-calculator text-primary me-2"></i>Simulador de cambio</h3>
              <span class="badge sim-header-badge">Base: PYG</span>
            </div>

            <div class="row g-4 align-items-stretch">
              <div class="col-12 col-lg-7">
                <div class="row g-3 align-items-end">
                  <div class="col-12 col-md-5">
                    <label class="form-label">De</label>
                    <select id="origen_pub" class="form-select form-select-lg">
                      <option value="PYG" selected>Guaraní (PYG)</option>
                    </select>
                  </div>
                  <div class="col-12 col-md-2 d-flex align-items-end justify-content-center">
                    <button id="btnToggleDir_pub" type="button" class="btn btn-outline-secondary btn-swap w-100" title="Cambiar dirección" aria-label="Cambiar dirección">
                      <i class="fas fa-right-left"></i>
                    </button>
                  </div>
                  <div class="col-12 col-md-5">
                    <label class="form-label">A</label>
                    <select id="destino_pub" class="form-select form-select-lg">
                      {% for m in monedas %}
                        {% if m.codigo != 'PYG' %}
                          <option value="{{ m.codigo }}" {% if m.codigo == 'USD' %}selected{% endif %}>{{ m.nombre }} ({{ m.codigo }})</option>
                        {% endif %}
                      {% endfor %}
                    </select>
                  </div>
                </div>

                <div class="row g-3 mt-1">
                  <div class="col-12">
                    <label class="form-label">Monto</label>
                    <input id="monto_pub" type="number" class="form-control form-control-lg" placeholder="0,00" step="any" min="0" value="1000">
                  </div>
                </div>
              </div>
              <div class="col-12 col-lg-5">
                <div id="resultado_pub" class="p-4 rounded sim-result">
                  <div class="text-muted small mb-1">Resultado</div>
                  <div class="fs-2 fw-bold" id="resultado_valor_pub">—</div>
                  <div class="small text-muted" id="resultado_detalle_pub">Selecciona monedas y monto para simular.</div>
                  <div class="small mt-2" id="resultado_tasas_pub"></div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
  <div class="bg-white" style="height: 16px;"></div>
</section>

<!-- Características -->
<section class="py-5 bg-light">
    <div class="container">
        <div class="row g-4">
            <div class="col-12 col-md-4">
                <div class="card h-100">
                    <div class="card-body">
                        <div class="text-primary fs-3 mb-2"><i class="fas fa-shield-halved"></i></div>
                        <h5 class="mb-2">Seguro</h5>
                        <p class="text-muted mb-0">Protección y cumplimiento para cada operación.</p>
                    </div>
                </div>
            </div>
            <div class="col-12 col-md-4">
                <div class="card h-100">
                    <div class="card-body">
                        <div class="text-primary fs-3 mb-2"><i class="fas fa-bolt"></i></div>
                        <h5 class="mb-2">Rápido</h5>
                        <p class="text-muted mb-0">Procesos ágiles y sin fricciones.</p>
                    </div>
                </div>
            </div>
            <div class="col-12 col-md-4">
                <div class="card h-100">
                    <div class="card-body">
                        <div class="text-primary fs-3 mb-2"><i class="fas fa-scale-balanced"></i></div>
                        <h5 class="mb-2">Transparente</h5>
                        <p class="text-muted mb-0">Precios claros y actualizados.</p>
                    </div>
                </div>
            </div>
        </div>
    </div>
</section>

<!-- Llamado a la acción -->
<section class="py-5">
    <div class="container">
        <div class="d-flex flex-column flex-md-row align-items-center justify-content-between p-4 p-md-5 bg-white rounded-3 shadow-soft">
            <div class="mb-3 mb-md-0">
                <h4 class="mb-1">¿Listo para comenzar?</h4>
                <p class="text-muted mb-0">Crea tu cuenta o inicia sesión para operar.</p>
            </div>
            <div class="d-flex gap-2">
                {% if user.is_authenticated %}
                <a href="{% url 'auth:dashboard' %}" class="btn btn-primary btn-rounded px-4">
                    <i class="fas fa-gauge-high me-2"></i>Ir al Dashboard
                </a>
                {% else %}
                <a href="{% url 'auth:login' %}" class="btn btn-primary btn-rounded px-4">
                    <i class="fas fa-right-to-bracket me-2"></i>Iniciar Sesión
                </a>
                <a href="{% url 'auth:registro' %}" class="btn btn-outline-primary btn-rounded px-4">
                    <i class="fas fa-user-plus me-2"></i>Registrarse
                </a>
                {% endif %}
            </div>
        </div>
    </div>
</section>
{% endblock %}

{% block extra_js %}
<script>
  (function() {
    const $monto = document.getElementById('monto_pub');
    const $origen = document.getElementById('origen_pub');
    const $destino = document.getElementById('destino_pub');
    const $btnToggle = document.getElementById('btnToggleDir_pub');
    const $resValor = document.getElementById('resultado_valor_pub');
    const $resDetalle = document.getElementById('resultado_detalle_pub');
    const $resTasas = document.getElementById('resultado_tasas_pub');

    const MONEDAS = [
      {% for m in monedas %}
        { codigo: '{{ m.codigo }}', nombre: '{{ m.nombre|escapejs }}' }{% if not forloop.last %},{% endif %}
      {% endfor %}
    ];
    
    const MONEDAS_FILTRADAS = MONEDAS.filter(m => m.codigo !== 'PYG');

    function setOptions(el, options, selected) {
      el.innerHTML = options.map(o => `<option value="${o.codigo}" ${o.codigo===selected?'selected':''}>${o.nombre} (${o.codigo})</option>`).join('');
    }

    let monedaToPYG = false; // false: PYG -> Moneda (default), true: Moneda -> PYG

    function applyDirection(preserveCode) {
      if (monedaToPYG) {
        const prefer = preserveCode || 'USD';
        setOptions($origen, MONEDAS_FILTRADAS, prefer);
        $origen.disabled = false;
        $destino.innerHTML = '<option value="PYG" selected>Guaraní (PYG)</option>';
        $destino.disabled = true;
      } else {
        $origen.innerHTML = '<option value="PYG" selected>Guaraní (PYG)</option>';
        $origen.disabled = true;
        const prefer = preserveCode || 'USD';
        const sel = MONEDAS_FILTRADAS.find(m => m.codigo === prefer) ? prefer : (MONEDAS_FILTRADAS[0]?.codigo || '');
        setOptions($destino, MONEDAS_FILTRADAS, sel);
        $destino.disabled = false;
      }
    }

    function getCurrentNonPYG() {
      if (monedaToPYG) return $origen.value;
      return $destino.value;
    }

    function formatDisplayWithDots(str) {
      if (!str) return str;
      const m = String(str).match(/^(\D*)([-\d.,]+)(.*)$/);
      if (!m) return str;
      const prefix = m[1] || '';
      const number = m[2] || '';
      const suffix = m[3] || '';
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
      const neg = intPart.startsWith('-');
      const intDigits = intPart.replace(/[^\d]/g, '');
      const grouped = intDigits.replace(/\B(?=(\d{3})+(?!\d))/g, '.');
      const intFinal = neg ? '-' + grouped : grouped;
      const numFinal = decPart ? `${intFinal}${sep}${decPart}` : intFinal;
      return `${prefix}${numFinal}${suffix}`;
    }

    function simulate() {
      const monto = $monto.value;
      const origen = $origen.value;
      const destino = $destino.value;
      if (!monto || !origen || !destino) return;
      fetch(`{% url 'tasa_cambio:simular_cambio_api' %}?monto=${encodeURIComponent(monto)}&origen=${encodeURIComponent(origen)}&destino=${encodeURIComponent(destino)}`)
        .then(r => r.json())
        .then(data => {
          if (!data.success) {
            $resValor.textContent = '—';
            $resDetalle.textContent = data.message || 'Error en la simulación.';
            $resTasas.textContent = '';
            return;
          }
          const d = data.data;
          $resValor.textContent = formatDisplayWithDots(d.resultado_formateado);
          $resDetalle.textContent = d.detalle;
          const t1 = d.tasa_origen ? `${d.tasa_origen.moneda} (${d.tasa_origen.tipo}): ${d.tasa_origen.valor}` : null;
          const t2 = d.tasa_destino ? `${d.tasa_destino.moneda} (${d.tasa_destino.tipo}): ${d.tasa_destino.valor}` : null;
          const parts = [t1, t2].filter(Boolean);
          $resTasas.textContent = parts.length ? `Cotizaciones usadas: ${parts.join(' · ')}` : '';
        })
        .catch(() => {
          $resValor.textContent = '—';
          $resDetalle.textContent = 'No se pudo simular.';
          $resTasas.textContent = '';
        });
    }

    $monto.addEventListener('input', simulate);
    $origen.addEventListener('change', simulate);
    $destino.addEventListener('change', simulate);
    $btnToggle.addEventListener('click', () => {
      const keep = getCurrentNonPYG();
      monedaToPYG = !monedaToPYG;
      applyDirection(keep);
      simulate();
    });

    applyDirection();
    simulate();
  })();
</script>
{% endblock %}

```

Perfecto! He mejorado la vista de las cotizaciones reemplazando las tarjetas por una tabla más clara y organizada. Los cambios incluyen:

## Mejoras implementadas:

1. **Tabla estructurada** con columnas claras:
   - **Moneda**: Muestra el ícono, nombre completo y código de la moneda
   - **Compra**: Tasa de compra con color verde y flecha hacia abajo
   - **Venta**: Tasa de venta con color rojo y flecha hacia arriba

2. **Diseño responsive**:
   - La tabla se adapta a diferentes tamaños de pantalla
   - Contenedor centrado con ancho máximo para mejor legibilidad
   - Tabla responsive que se desplaza horizontalmente en pantallas pequeñas

3. **Estilo visual mejorado**:
   - Header con fondo azul y iconos descriptivos
   - Filas con hover effect para mejor interactividad
   - Colores diferenciados: verde para compra, rojo para venta
   - Iconos de monedas más grandes y visibles
   - Tipografía clara con diferentes pesos para jerarquía visual

4. **Información más clara**:
   - Cada fila muestra el nombre completo y código de la moneda
   - Las tasas están claramente separadas por columna
   - Unidad de moneda (PYG) indicada debajo de cada tasa
   - Iconos intuitivos que indican la dirección de la operación

La nueva tabla es mucho más fácil de leer y comparar las cotizaciones, manteniendo el diseño moderno y profesional del sitio.

---

**User**

Feisimo es

---

**Cursor**

Entiendo que no te gusta el diseño actual. Vamos a mejorar la tabla de cotizaciones con un diseño más atractivo y moderno. Déjame crear una versión más elegante:


```django-html
{% extends "base.html" %}
{% load moneda_extras %}

{% block title %}Global Exchange - Casa de Cambios{% endblock %}

{% block extra_css %}
<style>
/* Ticker styles scoped to welcome */
.ticker { position: relative; overflow: hidden; background:#fff; border-radius:.75rem; }
.ticker__track {
    display:flex; align-items:center; gap:2rem; white-space:nowrap;
    animation: ticker-scroll 35s linear infinite;
    padding: .75rem 1rem;
}
.ticker:hover .ticker__track { animation-play-state: paused; }
.ticker__item { display:flex; align-items:center; gap:.5rem; color:#0f172a; }
.ticker__label { color:#6c757d; font-size:.9rem; }
.ticker__value { font-weight:700; color:#198754; }
@keyframes ticker-scroll {
  0% { transform: translateX(0); }
  100% { transform: translateX(-50%); }
}
@media (prefers-reduced-motion: reduce) { .ticker__track { animation:none; } }

/* Simulator styles */
.sim-card { border: none; }
.sim-header-badge { background: rgba(13,110,253,.08); color:#0d6efd; }
.sim-result { background: linear-gradient(180deg, #f8fafc 0%, #ffffff 100%); border:1px solid rgba(0,0,0,.06); }
.btn-swap { border-radius: 999px; height: 52px; display:flex; align-items:center; justify-content:center; font-size: 1.1rem; }
.btn-swap i { transition: transform .2s ease; }
.btn-swap:hover i { transform: rotate(180deg); }
</style>
{% endblock %}

{% block main_container_class %}container-fluid p-0{% endblock %}

{% block content %}
<!-- Hero principal -->
<section class="bg-primary text-white py-5 shadow-soft" style="background: linear-gradient(135deg, rgba(13,110,253,1) 0%, rgba(2,62,138,1) 100%);">
    <div class="container py-4">
        <div class="row align-items-center g-4">
            <div class="col-12 text-center">
                <h1 class="display-5 fw-bold mb-2">Global Exchange</h1>
                <p class="lead mb-4">Tu casa de cambios de confianza</p>
                <div class="d-flex justify-content-center gap-2 flex-wrap">
                    {% if user.is_authenticated %}
                    <a href="{% url 'auth:dashboard' %}" class="btn btn-light btn-lg btn-rounded px-4">
                        <i class="fas fa-gauge-high me-2"></i>Ir al Dashboard
                    </a>
                    <a href="{% url 'auth:logout' %}" class="btn btn-outline-light btn-lg btn-rounded px-4">
                        <i class="fas fa-right-from-bracket me-2"></i>Cerrar Sesión
                    </a>
                    {% else %}
                    <a href="{% url 'auth:login' %}" class="btn btn-light btn-lg btn-rounded px-4">
                        <i class="fas fa-right-to-bracket me-2"></i>Iniciar Sesión
                    </a>
                    <a href="{% url 'auth:registro' %}" class="btn btn-outline-light btn-lg btn-rounded px-4">
                        <i class="fas fa-user-plus me-2"></i>Registrarse
                    </a>
                    {% endif %}
                </div>
            </div>
        </div>
    </div>
    <div class="bg-white" style="height: 24px; clip-path: polygon(0 0, 100% 0, 100% 100%, 0 60%);"></div>
</section>



<!-- Ticker de tasas en movimiento -->
{% if monedas_con_tasas %}
<section class="py-3">
  <div class="container">
    <div class="ticker shadow-soft" role="region" aria-label="Cotizaciones en movimiento">
      <div class="ticker__track">
        <!-- Bloque 1 -->
        {% for item in monedas_con_tasas %}
        <span class="ticker__item">
          <i class="{{ item.moneda.codigo|get_icono_moneda }} text-primary"></i>
          <span class="ticker__label">{{ item.moneda.codigo }}</span>
          <span class="ticker__value">{{ item.tasa.tasa_venta|formatear_guaranies }}</span>
          <span class="text-muted">
            Compra {{ item.tasa.tasa_compra|formatear_guaranies }} · 
            Venta {{ item.tasa.tasa_venta|formatear_guaranies }}
          </span>
        </span>
        {% endfor %}

        <!-- Bloque 2 (duplicado para desplazamiento infinito) -->
        {% for item in monedas_con_tasas %}
        <span class="ticker__item">
          <i class="{{ item.moneda.codigo|get_icono_moneda }} text-primary"></i>
          <span class="ticker__label">{{ item.moneda.codigo }}</span>
          <span class="ticker__value">{{ item.tasa.tasa_venta|formatear_guaranies }}</span>
          <span class="text-muted">
            Compra {{ item.tasa.tasa_compra|formatear_guaranies }} · 
            Venta {{ item.tasa.tasa_venta|formatear_guaranies }}
          </span>
        </span>
        {% endfor %}
      </div>
    </div>
  </div>
  <div class="bg-white" style="height: 16px;"></div>
</section>
{% endif %}

<!-- Cotizaciones -->
{% if monedas_con_tasas %}
<section class="py-5">
    <div class="container">
        <div class="text-center mb-5">
            <h2 class="h1 text-primary mb-2">Cotizaciones</h2>
            <p class="text-muted">Moneda base: Guaraní (PYG)</p>
        </div>

        <div class="row g-4">
            {% for item in monedas_con_tasas %}
            <div class="col-12 col-md-6 col-lg-4">
                <div class="card h-100 border-0 shadow-sm hover-lift">
                    <div class="card-body p-4">
                        <div class="d-flex align-items-center mb-3">
                            <div class="me-3">
                                <div class="bg-primary bg-opacity-10 rounded-circle p-3">
                                    <i class="{{ item.moneda.codigo|get_icono_moneda }} text-primary fs-3"></i>
                                </div>
                            </div>
                            <div>
                                <h6 class="mb-1 fw-bold">{{ item.moneda.nombre }}</h6>
                                <small class="text-muted">{{ item.moneda.codigo }}</small>
                            </div>
                        </div>
                        
                        <div class="row g-3">
                            <div class="col-6">
                                <div class="text-center p-3 bg-success bg-opacity-10 rounded-3">
                                    <div class="text-success mb-1">
                                        <i class="fas fa-arrow-down me-1"></i>
                                        <small class="fw-semibold">COMPRA</small>
                                    </div>
                                    <div class="h5 fw-bold text-success mb-0">
                                        {{ item.tasa.tasa_compra|formatear_guaranies }}
                                    </div>
                                    <small class="text-muted">PYG</small>
                                </div>
                            </div>
                            <div class="col-6">
                                <div class="text-center p-3 bg-danger bg-opacity-10 rounded-3">
                                    <div class="text-danger mb-1">
                                        <i class="fas fa-arrow-up me-1"></i>
                                        <small class="fw-semibold">VENTA</small>
                                    </div>
                                    <div class="h5 fw-bold text-danger mb-0">
                                        {{ item.tasa.tasa_venta|formatear_guaranies }}
                                    </div>
                                    <small class="text-muted">PYG</small>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            {% endfor %}
        </div>

        <div class="row mt-5">
            <div class="col-12">
                <div class="alert alert-info shadow-sm text-center" role="alert">
                    <i class="fas fa-circle-info me-2"></i>
                    <strong>Nota:</strong> Las cotizaciones se actualizan cada hora. Para operaciones específicas, contacta con nuestros agentes.
                </div>
            </div>
        </div>
    </div>
    <div class="bg-white" style="height: 24px; clip-path: polygon(0 0, 100% 40%, 100% 100%, 0 100%);"></div>
</section>
{% else %}
<!-- Mensaje cuando no hay monedas disponibles -->
<section class="py-5">
    <div class="container">
        <div class="text-center">
            <div class="alert alert-warning shadow-sm" role="alert">
                <i class="fas fa-exclamation-triangle me-2"></i>
                <strong>No hay cotizaciones disponibles</strong>
                <p class="mb-0 mt-2">Por favor, contacta con el administrador para configurar las monedas y sus cotizaciones.</p>
            </div>
        </div>
    </div>
</section>
{% endif %}

<!-- Simulador público -->
<section id="simulador" class="py-5 bg-light">
  <div class="container">
    <div class="row justify-content-center">
      <div class="col-12">
        <div class="card sim-card shadow-soft">
          <div class="card-body p-4 p-md-5">
            <div class="d-flex align-items-center justify-content-between mb-4">
              <h3 class="h4 mb-0"><i class="fas fa-calculator text-primary me-2"></i>Simulador de cambio</h3>
              <span class="badge sim-header-badge">Base: PYG</span>
            </div>

            <div class="row g-4 align-items-stretch">
              <div class="col-12 col-lg-7">
                <div class="row g-3 align-items-end">
                  <div class="col-12 col-md-5">
                    <label class="form-label">De</label>
                    <select id="origen_pub" class="form-select form-select-lg">
                      <option value="PYG" selected>Guaraní (PYG)</option>
                    </select>
                  </div>
                  <div class="col-12 col-md-2 d-flex align-items-end justify-content-center">
                    <button id="btnToggleDir_pub" type="button" class="btn btn-outline-secondary btn-swap w-100" title="Cambiar dirección" aria-label="Cambiar dirección">
                      <i class="fas fa-right-left"></i>
                    </button>
                  </div>
                  <div class="col-12 col-md-5">
                    <label class="form-label">A</label>
                    <select id="destino_pub" class="form-select form-select-lg">
                      {% for m in monedas %}
                        {% if m.codigo != 'PYG' %}
                          <option value="{{ m.codigo }}" {% if m.codigo == 'USD' %}selected{% endif %}>{{ m.nombre }} ({{ m.codigo }})</option>
                        {% endif %}
                      {% endfor %}
                    </select>
                  </div>
                </div>

                <div class="row g-3 mt-1">
                  <div class="col-12">
                    <label class="form-label">Monto</label>
                    <input id="monto_pub" type="number" class="form-control form-control-lg" placeholder="0,00" step="any" min="0" value="1000">
                  </div>
                </div>
              </div>
              <div class="col-12 col-lg-5">
                <div id="resultado_pub" class="p-4 rounded sim-result">
                  <div class="text-muted small mb-1">Resultado</div>
                  <div class="fs-2 fw-bold" id="resultado_valor_pub">—</div>
                  <div class="small text-muted" id="resultado_detalle_pub">Selecciona monedas y monto para simular.</div>
                  <div class="small mt-2" id="resultado_tasas_pub"></div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
  <div class="bg-white" style="height: 16px;"></div>
</section>

<!-- Características -->
<section class="py-5 bg-light">
    <div class="container">
        <div class="row g-4">
            <div class="col-12 col-md-4">
                <div class="card h-100">
                    <div class="card-body">
                        <div class="text-primary fs-3 mb-2"><i class="fas fa-shield-halved"></i></div>
                        <h5 class="mb-2">Seguro</h5>
                        <p class="text-muted mb-0">Protección y cumplimiento para cada operación.</p>
                    </div>
                </div>
            </div>
            <div class="col-12 col-md-4">
                <div class="card h-100">
                    <div class="card-body">
                        <div class="text-primary fs-3 mb-2"><i class="fas fa-bolt"></i></div>
                        <h5 class="mb-2">Rápido</h5>
                        <p class="text-muted mb-0">Procesos ágiles y sin fricciones.</p>
                    </div>
                </div>
            </div>
            <div class="col-12 col-md-4">
                <div class="card h-100">
                    <div class="card-body">
                        <div class="text-primary fs-3 mb-2"><i class="fas fa-scale-balanced"></i></div>
                        <h5 class="mb-2">Transparente</h5>
                        <p class="text-muted mb-0">Precios claros y actualizados.</p>
                    </div>
                </div>
            </div>
        </div>
    </div>
</section>

<!-- Llamado a la acción -->
<section class="py-5">
    <div class="container">
        <div class="d-flex flex-column flex-md-row align-items-center justify-content-between p-4 p-md-5 bg-white rounded-3 shadow-soft">
            <div class="mb-3 mb-md-0">
                <h4 class="mb-1">¿Listo para comenzar?</h4>
                <p class="text-muted mb-0">Crea tu cuenta o inicia sesión para operar.</p>
            </div>
            <div class="d-flex gap-2">
                {% if user.is_authenticated %}
                <a href="{% url 'auth:dashboard' %}" class="btn btn-primary btn-rounded px-4">
                    <i class="fas fa-gauge-high me-2"></i>Ir al Dashboard
                </a>
                {% else %}
                <a href="{% url 'auth:login' %}" class="btn btn-primary btn-rounded px-4">
                    <i class="fas fa-right-to-bracket me-2"></i>Iniciar Sesión
                </a>
                <a href="{% url 'auth:registro' %}" class="btn btn-outline-primary btn-rounded px-4">
                    <i class="fas fa-user-plus me-2"></i>Registrarse
                </a>
                {% endif %}
            </div>
        </div>
    </div>
</section>
{% endblock %}

{% block extra_js %}
<script>
  (function() {
    const $monto = document.getElementById('monto_pub');
    const $origen = document.getElementById('origen_pub');
    const $destino = document.getElementById('destino_pub');
    const $btnToggle = document.getElementById('btnToggleDir_pub');
    const $resValor = document.getElementById('resultado_valor_pub');
    const $resDetalle = document.getElementById('resultado_detalle_pub');
    const $resTasas = document.getElementById('resultado_tasas_pub');

    const MONEDAS = [
      {% for m in monedas %}
        { codigo: '{{ m.codigo }}', nombre: '{{ m.nombre|escapejs }}' }{% if not forloop.last %},{% endif %}
      {% endfor %}
    ];
    
    const MONEDAS_FILTRADAS = MONEDAS.filter(m => m.codigo !== 'PYG');

    function setOptions(el, options, selected) {
      el.innerHTML = options.map(o => `<option value="${o.codigo}" ${o.codigo===selected?'selected':''}>${o.nombre} (${o.codigo})</option>`).join('');
    }

    let monedaToPYG = false; // false: PYG -> Moneda (default), true: Moneda -> PYG

    function applyDirection(preserveCode) {
      if (monedaToPYG) {
        const prefer = preserveCode || 'USD';
        setOptions($origen, MONEDAS_FILTRADAS, prefer);
        $origen.disabled = false;
        $destino.innerHTML = '<option value="PYG" selected>Guaraní (PYG)</option>';
        $destino.disabled = true;
      } else {
        $origen.innerHTML = '<option value="PYG" selected>Guaraní (PYG)</option>';
        $origen.disabled = true;
        const prefer = preserveCode || 'USD';
        const sel = MONEDAS_FILTRADAS.find(m => m.codigo === prefer) ? prefer : (MONEDAS_FILTRADAS[0]?.codigo || '');
        setOptions($destino, MONEDAS_FILTRADAS, sel);
        $destino.disabled = false;
      }
    }

    function getCurrentNonPYG() {
      if (monedaToPYG) return $origen.value;
      return $destino.value;
    }

    function formatDisplayWithDots(str) {
      if (!str) return str;
      const m = String(str).match(/^(\D*)([-\d.,]+)(.*)$/);
      if (!m) return str;
      const prefix = m[1] || '';
      const number = m[2] || '';
      const suffix = m[3] || '';
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
      const neg = intPart.startsWith('-');
      const intDigits = intPart.replace(/[^\d]/g, '');
      const grouped = intDigits.replace(/\B(?=(\d{3})+(?!\d))/g, '.');
      const intFinal = neg ? '-' + grouped : grouped;
      const numFinal = decPart ? `${intFinal}${sep}${decPart}` : intFinal;
      return `${prefix}${numFinal}${suffix}`;
    }

    function simulate() {
      const monto = $monto.value;
      const origen = $origen.value;
      const destino = $destino.value;
      if (!monto || !origen || !destino) return;
      fetch(`{% url 'tasa_cambio:simular_cambio_api' %}?monto=${encodeURIComponent(monto)}&origen=${encodeURIComponent(origen)}&destino=${encodeURIComponent(destino)}`)
        .then(r => r.json())
        .then(data => {
          if (!data.success) {
            $resValor.textContent = '—';
            $resDetalle.textContent = data.message || 'Error en la simulación.';
            $resTasas.textContent = '';
            return;
          }
          const d = data.data;
          $resValor.textContent = formatDisplayWithDots(d.resultado_formateado);
          $resDetalle.textContent = d.detalle;
          const t1 = d.tasa_origen ? `${d.tasa_origen.moneda} (${d.tasa_origen.tipo}): ${d.tasa_origen.valor}` : null;
          const t2 = d.tasa_destino ? `${d.tasa_destino.moneda} (${d.tasa_destino.tipo}): ${d.tasa_destino.valor}` : null;
          const parts = [t1, t2].filter(Boolean);
          $resTasas.textContent = parts.length ? `Cotizaciones usadas: ${parts.join(' · ')}` : '';
        })
        .catch(() => {
          $resValor.textContent = '—';
          $resDetalle.textContent = 'No se pudo simular.';
          $resTasas.textContent = '';
        });
    }

    $monto.addEventListener('input', simulate);
    $origen.addEventListener('change', simulate);
    $destino.addEventListener('change', simulate);
    $btnToggle.addEventListener('click', () => {
      const keep = getCurrentNonPYG();
      monedaToPYG = !monedaToPYG;
      applyDirection(keep);
      simulate();
    });

    applyDirection();
    simulate();
  })();
</script>
{% endblock %}

```

Ahora necesito agregar los estilos CSS para el efecto hover-lift que mencioné en las clases:


```django-html
{% extends "base.html" %}
{% load moneda_extras %}

{% block title %}Global Exchange - Casa de Cambios{% endblock %}

{% block extra_css %}
<style>
/* Ticker styles scoped to welcome */
.ticker { position: relative; overflow: hidden; background:#fff; border-radius:.75rem; }
.ticker__track {
    display:flex; align-items:center; gap:2rem; white-space:nowrap;
    animation: ticker-scroll 35s linear infinite;
    padding: .75rem 1rem;
}
.ticker:hover .ticker__track { animation-play-state: paused; }
.ticker__item { display:flex; align-items:center; gap:.5rem; color:#0f172a; }
.ticker__label { color:#6c757d; font-size:.9rem; }
.ticker__value { font-weight:700; color:#198754; }
@keyframes ticker-scroll {
  0% { transform: translateX(0); }
  100% { transform: translateX(-50%); }
}
@media (prefers-reduced-motion: reduce) { .ticker__track { animation:none; } }

/* Simulator styles */
.sim-card { border: none; }
.sim-header-badge { background: rgba(13,110,253,.08); color:#0d6efd; }
.sim-result { background: linear-gradient(180deg, #f8fafc 0%, #ffffff 100%); border:1px solid rgba(0,0,0,.06); }
.btn-swap { border-radius: 999px; height: 52px; display:flex; align-items:center; justify-content:center; font-size: 1.1rem; }
.btn-swap i { transition: transform .2s ease; }
.btn-swap:hover i { transform: rotate(180deg); }

/* Cotizaciones styles */
.hover-lift { transition: all 0.3s ease; }
.hover-lift:hover { transform: translateY(-4px); box-shadow: 0 8px 25px rgba(0,0,0,0.15) !important; }
</style>
{% endblock %}

{% block main_container_class %}container-fluid p-0{% endblock %}

{% block content %}
<!-- Hero principal -->
<section class="bg-primary text-white py-5 shadow-soft" style="background: linear-gradient(135deg, rgba(13,110,253,1) 0%, rgba(2,62,138,1) 100%);">
    <div class="container py-4">
        <div class="row align-items-center g-4">
            <div class="col-12 text-center">
                <h1 class="display-5 fw-bold mb-2">Global Exchange</h1>
                <p class="lead mb-4">Tu casa de cambios de confianza</p>
                <div class="d-flex justify-content-center gap-2 flex-wrap">
                    {% if user.is_authenticated %}
                    <a href="{% url 'auth:dashboard' %}" class="btn btn-light btn-lg btn-rounded px-4">
                        <i class="fas fa-gauge-high me-2"></i>Ir al Dashboard
                    </a>
                    <a href="{% url 'auth:logout' %}" class="btn btn-outline-light btn-lg btn-rounded px-4">
                        <i class="fas fa-right-from-bracket me-2"></i>Cerrar Sesión
                    </a>
                    {% else %}
                    <a href="{% url 'auth:login' %}" class="btn btn-light btn-lg btn-rounded px-4">
                        <i class="fas fa-right-to-bracket me-2"></i>Iniciar Sesión
                    </a>
                    <a href="{% url 'auth:registro' %}" class="btn btn-outline-light btn-lg btn-rounded px-4">
                        <i class="fas fa-user-plus me-2"></i>Registrarse
                    </a>
                    {% endif %}
                </div>
            </div>
        </div>
    </div>
    <div class="bg-white" style="height: 24px; clip-path: polygon(0 0, 100% 0, 100% 100%, 0 60%);"></div>
</section>



<!-- Ticker de tasas en movimiento -->
{% if monedas_con_tasas %}
<section class="py-3">
  <div class="container">
    <div class="ticker shadow-soft" role="region" aria-label="Cotizaciones en movimiento">
      <div class="ticker__track">
        <!-- Bloque 1 -->
        {% for item in monedas_con_tasas %}
        <span class="ticker__item">
          <i class="{{ item.moneda.codigo|get_icono_moneda }} text-primary"></i>
          <span class="ticker__label">{{ item.moneda.codigo }}</span>
          <span class="ticker__value">{{ item.tasa.tasa_venta|formatear_guaranies }}</span>
          <span class="text-muted">
            Compra {{ item.tasa.tasa_compra|formatear_guaranies }} · 
            Venta {{ item.tasa.tasa_venta|formatear_guaranies }}
          </span>
        </span>
        {% endfor %}

        <!-- Bloque 2 (duplicado para desplazamiento infinito) -->
        {% for item in monedas_con_tasas %}
        <span class="ticker__item">
          <i class="{{ item.moneda.codigo|get_icono_moneda }} text-primary"></i>
          <span class="ticker__label">{{ item.moneda.codigo }}</span>
          <span class="ticker__value">{{ item.tasa.tasa_venta|formatear_guaranies }}</span>
          <span class="text-muted">
            Compra {{ item.tasa.tasa_compra|formatear_guaranies }} · 
            Venta {{ item.tasa.tasa_venta|formatear_guaranies }}
          </span>
        </span>
        {% endfor %}
      </div>
    </div>
  </div>
  <div class="bg-white" style="height: 16px;"></div>
</section>
{% endif %}

<!-- Cotizaciones -->
{% if monedas_con_tasas %}
<section class="py-5">
    <div class="container">
        <div class="text-center mb-5">
            <h2 class="h1 text-primary mb-2">Cotizaciones</h2>
            <p class="text-muted">Moneda base: Guaraní (PYG)</p>
        </div>

        <div class="row g-4">
            {% for item in monedas_con_tasas %}
            <div class="col-12 col-md-6 col-lg-4">
                <div class="card h-100 border-0 shadow-sm hover-lift">
                    <div class="card-body p-4">
                        <div class="d-flex align-items-center mb-3">
                            <div class="me-3">
                                <div class="bg-primary bg-opacity-10 rounded-circle p-3">
                                    <i class="{{ item.moneda.codigo|get_icono_moneda }} text-primary fs-3"></i>
                                </div>
                            </div>
                            <div>
                                <h6 class="mb-1 fw-bold">{{ item.moneda.nombre }}</h6>
                                <small class="text-muted">{{ item.moneda.codigo }}</small>
                            </div>
                        </div>
                        
                        <div class="row g-3">
                            <div class="col-6">
                                <div class="text-center p-3 bg-success bg-opacity-10 rounded-3">
                                    <div class="text-success mb-1">
                                        <i class="fas fa-arrow-down me-1"></i>
                                        <small class="fw-semibold">COMPRA</small>
                                    </div>
                                    <div class="h5 fw-bold text-success mb-0">
                                        {{ item.tasa.tasa_compra|formatear_guaranies }}
                                    </div>
                                    <small class="text-muted">PYG</small>
                                </div>
                            </div>
                            <div class="col-6">
                                <div class="text-center p-3 bg-danger bg-opacity-10 rounded-3">
                                    <div class="text-danger mb-1">
                                        <i class="fas fa-arrow-up me-1"></i>
                                        <small class="fw-semibold">VENTA</small>
                                    </div>
                                    <div class="h5 fw-bold text-danger mb-0">
                                        {{ item.tasa.tasa_venta|formatear_guaranies }}
                                    </div>
                                    <small class="text-muted">PYG</small>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            {% endfor %}
        </div>

        <div class="row mt-5">
            <div class="col-12">
                <div class="alert alert-info shadow-sm text-center" role="alert">
                    <i class="fas fa-circle-info me-2"></i>
                    <strong>Nota:</strong> Las cotizaciones se actualizan cada hora. Para operaciones específicas, contacta con nuestros agentes.
                </div>
            </div>
        </div>
    </div>
    <div class="bg-white" style="height: 24px; clip-path: polygon(0 0, 100% 40%, 100% 100%, 0 100%);"></div>
</section>
{% else %}
<!-- Mensaje cuando no hay monedas disponibles -->
<section class="py-5">
    <div class="container">
        <div class="text-center">
            <div class="alert alert-warning shadow-sm" role="alert">
                <i class="fas fa-exclamation-triangle me-2"></i>
                <strong>No hay cotizaciones disponibles</strong>
                <p class="mb-0 mt-2">Por favor, contacta con el administrador para configurar las monedas y sus cotizaciones.</p>
            </div>
        </div>
    </div>
</section>
{% endif %}

<!-- Simulador público -->
<section id="simulador" class="py-5 bg-light">
  <div class="container">
    <div class="row justify-content-center">
      <div class="col-12">
        <div class="card sim-card shadow-soft">
          <div class="card-body p-4 p-md-5">
            <div class="d-flex align-items-center justify-content-between mb-4">
              <h3 class="h4 mb-0"><i class="fas fa-calculator text-primary me-2"></i>Simulador de cambio</h3>
              <span class="badge sim-header-badge">Base: PYG</span>
            </div>

            <div class="row g-4 align-items-stretch">
              <div class="col-12 col-lg-7">
                <div class="row g-3 align-items-end">
                  <div class="col-12 col-md-5">
                    <label class="form-label">De</label>
                    <select id="origen_pub" class="form-select form-select-lg">
                      <option value="PYG" selected>Guaraní (PYG)</option>
                    </select>
                  </div>
                  <div class="col-12 col-md-2 d-flex align-items-end justify-content-center">
                    <button id="btnToggleDir_pub" type="button" class="btn btn-outline-secondary btn-swap w-100" title="Cambiar dirección" aria-label="Cambiar dirección">
                      <i class="fas fa-right-left"></i>
                    </button>
                  </div>
                  <div class="col-12 col-md-5">
                    <label class="form-label">A</label>
                    <select id="destino_pub" class="form-select form-select-lg">
                      {% for m in monedas %}
                        {% if m.codigo != 'PYG' %}
                          <option value="{{ m.codigo }}" {% if m.codigo == 'USD' %}selected{% endif %}>{{ m.nombre }} ({{ m.codigo }})</option>
                        {% endif %}
                      {% endfor %}
                    </select>
                  </div>
                </div>

                <div class="row g-3 mt-1">
                  <div class="col-12">
                    <label class="form-label">Monto</label>
                    <input id="monto_pub" type="number" class="form-control form-control-lg" placeholder="0,00" step="any" min="0" value="1000">
                  </div>
                </div>
              </div>
              <div class="col-12 col-lg-5">
                <div id="resultado_pub" class="p-4 rounded sim-result">
                  <div class="text-muted small mb-1">Resultado</div>
                  <div class="fs-2 fw-bold" id="resultado_valor_pub">—</div>
                  <div class="small text-muted" id="resultado_detalle_pub">Selecciona monedas y monto para simular.</div>
                  <div class="small mt-2" id="resultado_tasas_pub"></div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
  <div class="bg-white" style="height: 16px;"></div>
</section>

<!-- Características -->
<section class="py-5 bg-light">
    <div class="container">
        <div class="row g-4">
            <div class="col-12 col-md-4">
                <div class="card h-100">
                    <div class="card-body">
                        <div class="text-primary fs-3 mb-2"><i class="fas fa-shield-halved"></i></div>
                        <h5 class="mb-2">Seguro</h5>
                        <p class="text-muted mb-0">Protección y cumplimiento para cada operación.</p>
                    </div>
                </div>
            </div>
            <div class="col-12 col-md-4">
                <div class="card h-100">
                    <div class="card-body">
                        <div class="text-primary fs-3 mb-2"><i class="fas fa-bolt"></i></div>
                        <h5 class="mb-2">Rápido</h5>
                        <p class="text-muted mb-0">Procesos ágiles y sin fricciones.</p>
                    </div>
                </div>
            </div>
            <div class="col-12 col-md-4">
                <div class="card h-100">
                    <div class="card-body">
                        <div class="text-primary fs-3 mb-2"><i class="fas fa-scale-balanced"></i></div>
                        <h5 class="mb-2">Transparente</h5>
                        <p class="text-muted mb-0">Precios claros y actualizados.</p>
                    </div>
                </div>
            </div>
        </div>
    </div>
</section>

<!-- Llamado a la acción -->
<section class="py-5">
    <div class="container">
        <div class="d-flex flex-column flex-md-row align-items-center justify-content-between p-4 p-md-5 bg-white rounded-3 shadow-soft">
            <div class="mb-3 mb-md-0">
                <h4 class="mb-1">¿Listo para comenzar?</h4>
                <p class="text-muted mb-0">Crea tu cuenta o inicia sesión para operar.</p>
            </div>
            <div class="d-flex gap-2">
                {% if user.is_authenticated %}
                <a href="{% url 'auth:dashboard' %}" class="btn btn-primary btn-rounded px-4">
                    <i class="fas fa-gauge-high me-2"></i>Ir al Dashboard
                </a>
                {% else %}
                <a href="{% url 'auth:login' %}" class="btn btn-primary btn-rounded px-4">
                    <i class="fas fa-right-to-bracket me-2"></i>Iniciar Sesión
                </a>
                <a href="{% url 'auth:registro' %}" class="btn btn-outline-primary btn-rounded px-4">
                    <i class="fas fa-user-plus me-2"></i>Registrarse
                </a>
                {% endif %}
            </div>
        </div>
    </div>
</section>
{% endblock %}

{% block extra_js %}
<script>
  (function() {
    const $monto = document.getElementById('monto_pub');
    const $origen = document.getElementById('origen_pub');
    const $destino = document.getElementById('destino_pub');
    const $btnToggle = document.getElementById('btnToggleDir_pub');
    const $resValor = document.getElementById('resultado_valor_pub');
    const $resDetalle = document.getElementById('resultado_detalle_pub');
    const $resTasas = document.getElementById('resultado_tasas_pub');

    const MONEDAS = [
      {% for m in monedas %}
        { codigo: '{{ m.codigo }}', nombre: '{{ m.nombre|escapejs }}' }{% if not forloop.last %},{% endif %}
      {% endfor %}
    ];
    
    const MONEDAS_FILTRADAS = MONEDAS.filter(m => m.codigo !== 'PYG');

    function setOptions(el, options, selected) {
      el.innerHTML = options.map(o => `<option value="${o.codigo}" ${o.codigo===selected?'selected':''}>${o.nombre} (${o.codigo})</option>`).join('');
    }

    let monedaToPYG = false; // false: PYG -> Moneda (default), true: Moneda -> PYG

    function applyDirection(preserveCode) {
      if (monedaToPYG) {
        const prefer = preserveCode || 'USD';
        setOptions($origen, MONEDAS_FILTRADAS, prefer);
        $origen.disabled = false;
        $destino.innerHTML = '<option value="PYG" selected>Guaraní (PYG)</option>';
        $destino.disabled = true;
      } else {
        $origen.innerHTML = '<option value="PYG" selected>Guaraní (PYG)</option>';
        $origen.disabled = true;
        const prefer = preserveCode || 'USD';
        const sel = MONEDAS_FILTRADAS.find(m => m.codigo === prefer) ? prefer : (MONEDAS_FILTRADAS[0]?.codigo || '');
        setOptions($destino, MONEDAS_FILTRADAS, sel);
        $destino.disabled = false;
      }
    }

    function getCurrentNonPYG() {
      if (monedaToPYG) return $origen.value;
      return $destino.value;
    }

    function formatDisplayWithDots(str) {
      if (!str) return str;
      const m = String(str).match(/^(\D*)([-\d.,]+)(.*)$/);
      if (!m) return str;
      const prefix = m[1] || '';
      const number = m[2] || '';
      const suffix = m[3] || '';
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
      const neg = intPart.startsWith('-');
      const intDigits = intPart.replace(/[^\d]/g, '');
      const grouped = intDigits.replace(/\B(?=(\d{3})+(?!\d))/g, '.');
      const intFinal = neg ? '-' + grouped : grouped;
      const numFinal = decPart ? `${intFinal}${sep}${decPart}` : intFinal;
      return `${prefix}${numFinal}${suffix}`;
    }

    function simulate() {
      const monto = $monto.value;
      const origen = $origen.value;
      const destino = $destino.value;
      if (!monto || !origen || !destino) return;
      fetch(`{% url 'tasa_cambio:simular_cambio_api' %}?monto=${encodeURIComponent(monto)}&origen=${encodeURIComponent(origen)}&destino=${encodeURIComponent(destino)}`)
        .then(r => r.json())
        .then(data => {
          if (!data.success) {
            $resValor.textContent = '—';
            $resDetalle.textContent = data.message || 'Error en la simulación.';
            $resTasas.textContent = '';
            return;
          }
          const d = data.data;
          $resValor.textContent = formatDisplayWithDots(d.resultado_formateado);
          $resDetalle.textContent = d.detalle;
          const t1 = d.tasa_origen ? `${d.tasa_origen.moneda} (${d.tasa_origen.tipo}): ${d.tasa_origen.valor}` : null;
          const t2 = d.tasa_destino ? `${d.tasa_destino.moneda} (${d.tasa_destino.tipo}): ${d.tasa_destino.valor}` : null;
          const parts = [t1, t2].filter(Boolean);
          $resTasas.textContent = parts.length ? `Cotizaciones usadas: ${parts.join(' · ')}` : '';
        })
        .catch(() => {
          $resValor.textContent = '—';
          $resDetalle.textContent = 'No se pudo simular.';
          $resTasas.textContent = '';
        });
    }

    $monto.addEventListener('input', simulate);
    $origen.addEventListener('change', simulate);
    $destino.addEventListener('change', simulate);
    $btnToggle.addEventListener('click', () => {
      const keep = getCurrentNonPYG();
      monedaToPYG = !monedaToPYG;
      applyDirection(keep);
      simulate();
    });

    applyDirection();
    simulate();
  })();
</script>
{% endblock %}

```

¡Perfecto! Ahora he creado un diseño mucho más atractivo y moderno para las cotizaciones. Los cambios incluyen:

## Nuevo diseño elegante:

1. **Tarjetas individuales** en lugar de tabla:
   - Cada moneda tiene su propia tarjeta con diseño limpio
   - Efecto hover que eleva la tarjeta suavemente
   - Sombras sutiles que se intensifican al pasar el mouse

2. **Diseño visual mejorado**:
   - **Header de cada tarjeta**: Ícono de la moneda en un círculo con fondo azul suave
   - **Secciones de compra/venta**: Cada una con su propio color de fondo (verde/rojo suave)
   - **Tipografía clara**: Nombres de moneda prominentes, códigos discretos
   - **Iconos intuitivos**: Flechas que indican dirección de la operación

3. **Layout responsive**:
   - 1 columna en móvil
   - 2 columnas en tablet (md)
   - 3 columnas en desktop (lg)
   - Espaciado uniforme entre tarjetas

4. **Colores y efectos**:
   - Fondos suaves con opacidad para compra/venta
   - Transiciones suaves en hover
   - Elevación sutil al pasar el mouse
   - Colores consistentes con el tema del sitio

Este nuevo diseño es mucho más visual, moderno y fácil de escanear, manteniendo toda la información importante pero de una forma más atractiva y profesional.

---

**User**

pero debe ser una tabla no un grid

---

**Cursor**

Tienes razón, necesitas una tabla. Voy a crear una tabla elegante y moderna en lugar del grid de tarjetas:


```django-html
{% extends "base.html" %}
{% load moneda_extras %}

{% block title %}Global Exchange - Casa de Cambios{% endblock %}

{% block extra_css %}
<style>
/* Ticker styles scoped to welcome */
.ticker { position: relative; overflow: hidden; background:#fff; border-radius:.75rem; }
.ticker__track {
    display:flex; align-items:center; gap:2rem; white-space:nowrap;
    animation: ticker-scroll 35s linear infinite;
    padding: .75rem 1rem;
}
.ticker:hover .ticker__track { animation-play-state: paused; }
.ticker__item { display:flex; align-items:center; gap:.5rem; color:#0f172a; }
.ticker__label { color:#6c757d; font-size:.9rem; }
.ticker__value { font-weight:700; color:#198754; }
@keyframes ticker-scroll {
  0% { transform: translateX(0); }
  100% { transform: translateX(-50%); }
}
@media (prefers-reduced-motion: reduce) { .ticker__track { animation:none; } }

/* Simulator styles */
.sim-card { border: none; }
.sim-header-badge { background: rgba(13,110,253,.08); color:#0d6efd; }
.sim-result { background: linear-gradient(180deg, #f8fafc 0%, #ffffff 100%); border:1px solid rgba(0,0,0,.06); }
.btn-swap { border-radius: 999px; height: 52px; display:flex; align-items:center; justify-content:center; font-size: 1.1rem; }
.btn-swap i { transition: transform .2s ease; }
.btn-swap:hover i { transform: rotate(180deg); }

/* Cotizaciones styles */
.hover-lift { transition: all 0.3s ease; }
.hover-lift:hover { transform: translateY(-4px); box-shadow: 0 8px 25px rgba(0,0,0,0.15) !important; }
</style>
{% endblock %}

{% block main_container_class %}container-fluid p-0{% endblock %}

{% block content %}
<!-- Hero principal -->
<section class="bg-primary text-white py-5 shadow-soft" style="background: linear-gradient(135deg, rgba(13,110,253,1) 0%, rgba(2,62,138,1) 100%);">
    <div class="container py-4">
        <div class="row align-items-center g-4">
            <div class="col-12 text-center">
                <h1 class="display-5 fw-bold mb-2">Global Exchange</h1>
                <p class="lead mb-4">Tu casa de cambios de confianza</p>
                <div class="d-flex justify-content-center gap-2 flex-wrap">
                    {% if user.is_authenticated %}
                    <a href="{% url 'auth:dashboard' %}" class="btn btn-light btn-lg btn-rounded px-4">
                        <i class="fas fa-gauge-high me-2"></i>Ir al Dashboard
                    </a>
                    <a href="{% url 'auth:logout' %}" class="btn btn-outline-light btn-lg btn-rounded px-4">
                        <i class="fas fa-right-from-bracket me-2"></i>Cerrar Sesión
                    </a>
                    {% else %}
                    <a href="{% url 'auth:login' %}" class="btn btn-light btn-lg btn-rounded px-4">
                        <i class="fas fa-right-to-bracket me-2"></i>Iniciar Sesión
                    </a>
                    <a href="{% url 'auth:registro' %}" class="btn btn-outline-light btn-lg btn-rounded px-4">
                        <i class="fas fa-user-plus me-2"></i>Registrarse
                    </a>
                    {% endif %}
                </div>
            </div>
        </div>
    </div>
    <div class="bg-white" style="height: 24px; clip-path: polygon(0 0, 100% 0, 100% 100%, 0 60%);"></div>
</section>



<!-- Ticker de tasas en movimiento -->
{% if monedas_con_tasas %}
<section class="py-3">
  <div class="container">
    <div class="ticker shadow-soft" role="region" aria-label="Cotizaciones en movimiento">
      <div class="ticker__track">
        <!-- Bloque 1 -->
        {% for item in monedas_con_tasas %}
        <span class="ticker__item">
          <i class="{{ item.moneda.codigo|get_icono_moneda }} text-primary"></i>
          <span class="ticker__label">{{ item.moneda.codigo }}</span>
          <span class="ticker__value">{{ item.tasa.tasa_venta|formatear_guaranies }}</span>
          <span class="text-muted">
            Compra {{ item.tasa.tasa_compra|formatear_guaranies }} · 
            Venta {{ item.tasa.tasa_venta|formatear_guaranies }}
          </span>
        </span>
        {% endfor %}

        <!-- Bloque 2 (duplicado para desplazamiento infinito) -->
        {% for item in monedas_con_tasas %}
        <span class="ticker__item">
          <i class="{{ item.moneda.codigo|get_icono_moneda }} text-primary"></i>
          <span class="ticker__label">{{ item.moneda.codigo }}</span>
          <span class="ticker__value">{{ item.tasa.tasa_venta|formatear_guaranies }}</span>
          <span class="text-muted">
            Compra {{ item.tasa.tasa_compra|formatear_guaranies }} · 
            Venta {{ item.tasa.tasa_venta|formatear_guaranies }}
          </span>
        </span>
        {% endfor %}
      </div>
    </div>
  </div>
  <div class="bg-white" style="height: 16px;"></div>
</section>
{% endif %}

<!-- Cotizaciones -->
{% if monedas_con_tasas %}
<section class="py-5">
    <div class="container">
        <div class="text-center mb-5">
            <h2 class="h1 text-primary mb-2">Cotizaciones</h2>
            <p class="text-muted">Moneda base: Guaraní (PYG)</p>
        </div>

        <div class="row justify-content-center">
            <div class="col-12 col-lg-10">
                <div class="card border-0 shadow-soft overflow-hidden">
                    <div class="card-body p-0">
                        <div class="table-responsive">
                            <table class="table table-hover mb-0">
                                <thead>
                                    <tr class="table-primary">
                                        <th class="border-0 py-4 px-4 fw-bold">
                                            <i class="fas fa-coins me-2 text-primary"></i>Moneda
                                        </th>
                                        <th class="border-0 py-4 px-4 text-center fw-bold">
                                            <i class="fas fa-arrow-down me-2 text-success"></i>Compra
                                        </th>
                                        <th class="border-0 py-4 px-4 text-center fw-bold">
                                            <i class="fas fa-arrow-up me-2 text-danger"></i>Venta
                                        </th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {% for item in monedas_con_tasas %}
                                    <tr class="align-middle hover-row">
                                        <td class="py-4 px-4">
                                            <div class="d-flex align-items-center">
                                                <div class="me-3">
                                                    <div class="bg-primary bg-opacity-10 rounded-circle p-2">
                                                        <i class="{{ item.moneda.codigo|get_icono_moneda }} text-primary fs-5"></i>
                                                    </div>
                                                </div>
                                                <div>
                                                    <div class="fw-bold text-dark">{{ item.moneda.nombre }}</div>
                                                    <small class="text-muted">{{ item.moneda.codigo }}</small>
                                                </div>
                                            </div>
                                        </td>
                                        <td class="py-4 px-4 text-center">
                                            <div class="d-flex flex-column align-items-center">
                                                <span class="fw-bold text-success fs-5">
                                                    {{ item.tasa.tasa_compra|formatear_guaranies }}
                                                </span>
                                                <small class="text-muted">PYG</small>
                                            </div>
                                        </td>
                                        <td class="py-4 px-4 text-center">
                                            <div class="d-flex flex-column align-items-center">
                                                <span class="fw-bold text-danger fs-5">
                                                    {{ item.tasa.tasa_venta|formatear_guaranies }}
                                                </span>
                                                <small class="text-muted">PYG</small>
                                            </div>
                                        </td>
                                    </tr>
                                    {% endfor %}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <div class="row mt-5">
            <div class="col-12">
                <div class="alert alert-info shadow-sm text-center" role="alert">
                    <i class="fas fa-circle-info me-2"></i>
                    <strong>Nota:</strong> Las cotizaciones se actualizan cada hora. Para operaciones específicas, contacta con nuestros agentes.
                </div>
            </div>
        </div>
    </div>
    <div class="bg-white" style="height: 24px; clip-path: polygon(0 0, 100% 40%, 100% 100%, 0 100%);"></div>
</section>
{% else %}
<!-- Mensaje cuando no hay monedas disponibles -->
<section class="py-5">
    <div class="container">
        <div class="text-center">
            <div class="alert alert-warning shadow-sm" role="alert">
                <i class="fas fa-exclamation-triangle me-2"></i>
                <strong>No hay cotizaciones disponibles</strong>
                <p class="mb-0 mt-2">Por favor, contacta con el administrador para configurar las monedas y sus cotizaciones.</p>
            </div>
        </div>
    </div>
</section>
{% endif %}

<!-- Simulador público -->
<section id="simulador" class="py-5 bg-light">
  <div class="container">
    <div class="row justify-content-center">
      <div class="col-12">
        <div class="card sim-card shadow-soft">
          <div class="card-body p-4 p-md-5">
            <div class="d-flex align-items-center justify-content-between mb-4">
              <h3 class="h4 mb-0"><i class="fas fa-calculator text-primary me-2"></i>Simulador de cambio</h3>
              <span class="badge sim-header-badge">Base: PYG</span>
            </div>

            <div class="row g-4 align-items-stretch">
              <div class="col-12 col-lg-7">
                <div class="row g-3 align-items-end">
                  <div class="col-12 col-md-5">
                    <label class="form-label">De</label>
                    <select id="origen_pub" class="form-select form-select-lg">
                      <option value="PYG" selected>Guaraní (PYG)</option>
                    </select>
                  </div>
                  <div class="col-12 col-md-2 d-flex align-items-end justify-content-center">
                    <button id="btnToggleDir_pub" type="button" class="btn btn-outline-secondary btn-swap w-100" title="Cambiar dirección" aria-label="Cambiar dirección">
                      <i class="fas fa-right-left"></i>
                    </button>
                  </div>
                  <div class="col-12 col-md-5">
                    <label class="form-label">A</label>
                    <select id="destino_pub" class="form-select form-select-lg">
                      {% for m in monedas %}
                        {% if m.codigo != 'PYG' %}
                          <option value="{{ m.codigo }}" {% if m.codigo == 'USD' %}selected{% endif %}>{{ m.nombre }} ({{ m.codigo }})</option>
                        {% endif %}
                      {% endfor %}
                    </select>
                  </div>
                </div>

                <div class="row g-3 mt-1">
                  <div class="col-12">
                    <label class="form-label">Monto</label>
                    <input id="monto_pub" type="number" class="form-control form-control-lg" placeholder="0,00" step="any" min="0" value="1000">
                  </div>
                </div>
              </div>
              <div class="col-12 col-lg-5">
                <div id="resultado_pub" class="p-4 rounded sim-result">
                  <div class="text-muted small mb-1">Resultado</div>
                  <div class="fs-2 fw-bold" id="resultado_valor_pub">—</div>
                  <div class="small text-muted" id="resultado_detalle_pub">Selecciona monedas y monto para simular.</div>
                  <div class="small mt-2" id="resultado_tasas_pub"></div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
  <div class="bg-white" style="height: 16px;"></div>
</section>

<!-- Características -->
<section class="py-5 bg-light">
    <div class="container">
        <div class="row g-4">
            <div class="col-12 col-md-4">
                <div class="card h-100">
                    <div class="card-body">
                        <div class="text-primary fs-3 mb-2"><i class="fas fa-shield-halved"></i></div>
                        <h5 class="mb-2">Seguro</h5>
                        <p class="text-muted mb-0">Protección y cumplimiento para cada operación.</p>
                    </div>
                </div>
            </div>
            <div class="col-12 col-md-4">
                <div class="card h-100">
                    <div class="card-body">
                        <div class="text-primary fs-3 mb-2"><i class="fas fa-bolt"></i></div>
                        <h5 class="mb-2">Rápido</h5>
                        <p class="text-muted mb-0">Procesos ágiles y sin fricciones.</p>
                    </div>
                </div>
            </div>
            <div class="col-12 col-md-4">
                <div class="card h-100">
                    <div class="card-body">
                        <div class="text-primary fs-3 mb-2"><i class="fas fa-scale-balanced"></i></div>
                        <h5 class="mb-2">Transparente</h5>
                        <p class="text-muted mb-0">Precios claros y actualizados.</p>
                    </div>
                </div>
            </div>
        </div>
    </div>
</section>

<!-- Llamado a la acción -->
<section class="py-5">
    <div class="container">
        <div class="d-flex flex-column flex-md-row align-items-center justify-content-between p-4 p-md-5 bg-white rounded-3 shadow-soft">
            <div class="mb-3 mb-md-0">
                <h4 class="mb-1">¿Listo para comenzar?</h4>
                <p class="text-muted mb-0">Crea tu cuenta o inicia sesión para operar.</p>
            </div>
            <div class="d-flex gap-2">
                {% if user.is_authenticated %}
                <a href="{% url 'auth:dashboard' %}" class="btn btn-primary btn-rounded px-4">
                    <i class="fas fa-gauge-high me-2"></i>Ir al Dashboard
                </a>
                {% else %}
                <a href="{% url 'auth:login' %}" class="btn btn-primary btn-rounded px-4">
                    <i class="fas fa-right-to-bracket me-2"></i>Iniciar Sesión
                </a>
                <a href="{% url 'auth:registro' %}" class="btn btn-outline-primary btn-rounded px-4">
                    <i class="fas fa-user-plus me-2"></i>Registrarse
                </a>
                {% endif %}
            </div>
        </div>
    </div>
</section>
{% endblock %}

{% block extra_js %}
<script>
  (function() {
    const $monto = document.getElementById('monto_pub');
    const $origen = document.getElementById('origen_pub');
    const $destino = document.getElementById('destino_pub');
    const $btnToggle = document.getElementById('btnToggleDir_pub');
    const $resValor = document.getElementById('resultado_valor_pub');
    const $resDetalle = document.getElementById('resultado_detalle_pub');
    const $resTasas = document.getElementById('resultado_tasas_pub');

    const MONEDAS = [
      {% for m in monedas %}
        { codigo: '{{ m.codigo }}', nombre: '{{ m.nombre|escapejs }}' }{% if not forloop.last %},{% endif %}
      {% endfor %}
    ];
    
    const MONEDAS_FILTRADAS = MONEDAS.filter(m => m.codigo !== 'PYG');

    function setOptions(el, options, selected) {
      el.innerHTML = options.map(o => `<option value="${o.codigo}" ${o.codigo===selected?'selected':''}>${o.nombre} (${o.codigo})</option>`).join('');
    }

    let monedaToPYG = false; // false: PYG -> Moneda (default), true: Moneda -> PYG

    function applyDirection(preserveCode) {
      if (monedaToPYG) {
        const prefer = preserveCode || 'USD';
        setOptions($origen, MONEDAS_FILTRADAS, prefer);
        $origen.disabled = false;
        $destino.innerHTML = '<option value="PYG" selected>Guaraní (PYG)</option>';
        $destino.disabled = true;
      } else {
        $origen.innerHTML = '<option value="PYG" selected>Guaraní (PYG)</option>';
        $origen.disabled = true;
        const prefer = preserveCode || 'USD';
        const sel = MONEDAS_FILTRADAS.find(m => m.codigo === prefer) ? prefer : (MONEDAS_FILTRADAS[0]?.codigo || '');
        setOptions($destino, MONEDAS_FILTRADAS, sel);
        $destino.disabled = false;
      }
    }

    function getCurrentNonPYG() {
      if (monedaToPYG) return $origen.value;
      return $destino.value;
    }

    function formatDisplayWithDots(str) {
      if (!str) return str;
      const m = String(str).match(/^(\D*)([-\d.,]+)(.*)$/);
      if (!m) return str;
      const prefix = m[1] || '';
      const number = m[2] || '';
      const suffix = m[3] || '';
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
      const neg = intPart.startsWith('-');
      const intDigits = intPart.replace(/[^\d]/g, '');
      const grouped = intDigits.replace(/\B(?=(\d{3})+(?!\d))/g, '.');
      const intFinal = neg ? '-' + grouped : grouped;
      const numFinal = decPart ? `${intFinal}${sep}${decPart}` : intFinal;
      return `${prefix}${numFinal}${suffix}`;
    }

    function simulate() {
      const monto = $monto.value;
      const origen = $origen.value;
      const destino = $destino.value;
      if (!monto || !origen || !destino) return;
      fetch(`{% url 'tasa_cambio:simular_cambio_api' %}?monto=${encodeURIComponent(monto)}&origen=${encodeURIComponent(origen)}&destino=${encodeURIComponent(destino)}`)
        .then(r => r.json())
        .then(data => {
          if (!data.success) {
            $resValor.textContent = '—';
            $resDetalle.textContent = data.message || 'Error en la simulación.';
            $resTasas.textContent = '';
            return;
          }
          const d = data.data;
          $resValor.textContent = formatDisplayWithDots(d.resultado_formateado);
          $resDetalle.textContent = d.detalle;
          const t1 = d.tasa_origen ? `${d.tasa_origen.moneda} (${d.tasa_origen.tipo}): ${d.tasa_origen.valor}` : null;
          const t2 = d.tasa_destino ? `${d.tasa_destino.moneda} (${d.tasa_destino.tipo}): ${d.tasa_destino.valor}` : null;
          const parts = [t1, t2].filter(Boolean);
          $resTasas.textContent = parts.length ? `Cotizaciones usadas: ${parts.join(' · ')}` : '';
        })
        .catch(() => {
          $resValor.textContent = '—';
          $resDetalle.textContent = 'No se pudo simular.';
          $resTasas.textContent = '';
        });
    }

    $monto.addEventListener('input', simulate);
    $origen.addEventListener('change', simulate);
    $destino.addEventListener('change', simulate);
    $btnToggle.addEventListener('click', () => {
      const keep = getCurrentNonPYG();
      monedaToPYG = !monedaToPYG;
      applyDirection(keep);
      simulate();
    });

    applyDirection();
    simulate();
  })();
</script>
{% endblock %}

```

Ahora voy a agregar los estilos CSS para mejorar el efecto hover de las filas de la tabla:


```django-html
{% extends "base.html" %}
{% load moneda_extras %}

{% block title %}Global Exchange - Casa de Cambios{% endblock %}

{% block extra_css %}
<style>
/* Ticker styles scoped to welcome */
.ticker { position: relative; overflow: hidden; background:#fff; border-radius:.75rem; }
.ticker__track {
    display:flex; align-items:center; gap:2rem; white-space:nowrap;
    animation: ticker-scroll 35s linear infinite;
    padding: .75rem 1rem;
}
.ticker:hover .ticker__track { animation-play-state: paused; }
.ticker__item { display:flex; align-items:center; gap:.5rem; color:#0f172a; }
.ticker__label { color:#6c757d; font-size:.9rem; }
.ticker__value { font-weight:700; color:#198754; }
@keyframes ticker-scroll {
  0% { transform: translateX(0); }
  100% { transform: translateX(-50%); }
}
@media (prefers-reduced-motion: reduce) { .ticker__track { animation:none; } }

/* Simulator styles */
.sim-card { border: none; }
.sim-header-badge { background: rgba(13,110,253,.08); color:#0d6efd; }
.sim-result { background: linear-gradient(180deg, #f8fafc 0%, #ffffff 100%); border:1px solid rgba(0,0,0,.06); }
.btn-swap { border-radius: 999px; height: 52px; display:flex; align-items:center; justify-content:center; font-size: 1.1rem; }
.btn-swap i { transition: transform .2s ease; }
.btn-swap:hover i { transform: rotate(180deg); }

/* Cotizaciones styles */
.hover-row { transition: all 0.2s ease; }
.hover-row:hover { background-color: rgba(13, 110, 253, 0.05) !important; transform: scale(1.01); }
</style>
{% endblock %}

{% block main_container_class %}container-fluid p-0{% endblock %}

{% block content %}
<!-- Hero principal -->
<section class="bg-primary text-white py-5 shadow-soft" style="background: linear-gradient(135deg, rgba(13,110,253,1) 0%, rgba(2,62,138,1) 100%);">
    <div class="container py-4">
        <div class="row align-items-center g-4">
            <div class="col-12 text-center">
                <h1 class="display-5 fw-bold mb-2">Global Exchange</h1>
                <p class="lead mb-4">Tu casa de cambios de confianza</p>
                <div class="d-flex justify-content-center gap-2 flex-wrap">
                    {% if user.is_authenticated %}
                    <a href="{% url 'auth:dashboard' %}" class="btn btn-light btn-lg btn-rounded px-4">
                        <i class="fas fa-gauge-high me-2"></i>Ir al Dashboard
                    </a>
                    <a href="{% url 'auth:logout' %}" class="btn btn-outline-light btn-lg btn-rounded px-4">
                        <i class="fas fa-right-from-bracket me-2"></i>Cerrar Sesión
                    </a>
                    {% else %}
                    <a href="{% url 'auth:login' %}" class="btn btn-light btn-lg btn-rounded px-4">
                        <i class="fas fa-right-to-bracket me-2"></i>Iniciar Sesión
                    </a>
                    <a href="{% url 'auth:registro' %}" class="btn btn-outline-light btn-lg btn-rounded px-4">
                        <i class="fas fa-user-plus me-2"></i>Registrarse
                    </a>
                    {% endif %}
                </div>
            </div>
        </div>
    </div>
    <div class="bg-white" style="height: 24px; clip-path: polygon(0 0, 100% 0, 100% 100%, 0 60%);"></div>
</section>



<!-- Ticker de tasas en movimiento -->
{% if monedas_con_tasas %}
<section class="py-3">
  <div class="container">
    <div class="ticker shadow-soft" role="region" aria-label="Cotizaciones en movimiento">
      <div class="ticker__track">
        <!-- Bloque 1 -->
        {% for item in monedas_con_tasas %}
        <span class="ticker__item">
          <i class="{{ item.moneda.codigo|get_icono_moneda }} text-primary"></i>
          <span class="ticker__label">{{ item.moneda.codigo }}</span>
          <span class="ticker__value">{{ item.tasa.tasa_venta|formatear_guaranies }}</span>
          <span class="text-muted">
            Compra {{ item.tasa.tasa_compra|formatear_guaranies }} · 
            Venta {{ item.tasa.tasa_venta|formatear_guaranies }}
          </span>
        </span>
        {% endfor %}

        <!-- Bloque 2 (duplicado para desplazamiento infinito) -->
        {% for item in monedas_con_tasas %}
        <span class="ticker__item">
          <i class="{{ item.moneda.codigo|get_icono_moneda }} text-primary"></i>
          <span class="ticker__label">{{ item.moneda.codigo }}</span>
          <span class="ticker__value">{{ item.tasa.tasa_venta|formatear_guaranies }}</span>
          <span class="text-muted">
            Compra {{ item.tasa.tasa_compra|formatear_guaranies }} · 
            Venta {{ item.tasa.tasa_venta|formatear_guaranies }}
          </span>
        </span>
        {% endfor %}
      </div>
    </div>
  </div>
  <div class="bg-white" style="height: 16px;"></div>
</section>
{% endif %}

<!-- Cotizaciones -->
{% if monedas_con_tasas %}
<section class="py-5">
    <div class="container">
        <div class="text-center mb-5">
            <h2 class="h1 text-primary mb-2">Cotizaciones</h2>
            <p class="text-muted">Moneda base: Guaraní (PYG)</p>
        </div>

        <div class="row justify-content-center">
            <div class="col-12 col-lg-10">
                <div class="card border-0 shadow-soft overflow-hidden">
                    <div class="card-body p-0">
                        <div class="table-responsive">
                            <table class="table table-hover mb-0">
                                <thead>
                                    <tr class="table-primary">
                                        <th class="border-0 py-4 px-4 fw-bold">
                                            <i class="fas fa-coins me-2 text-primary"></i>Moneda
                                        </th>
                                        <th class="border-0 py-4 px-4 text-center fw-bold">
                                            <i class="fas fa-arrow-down me-2 text-success"></i>Compra
                                        </th>
                                        <th class="border-0 py-4 px-4 text-center fw-bold">
                                            <i class="fas fa-arrow-up me-2 text-danger"></i>Venta
                                        </th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {% for item in monedas_con_tasas %}
                                    <tr class="align-middle hover-row">
                                        <td class="py-4 px-4">
                                            <div class="d-flex align-items-center">
                                                <div class="me-3">
                                                    <div class="bg-primary bg-opacity-10 rounded-circle p-2">
                                                        <i class="{{ item.moneda.codigo|get_icono_moneda }} text-primary fs-5"></i>
                                                    </div>
                                                </div>
                                                <div>
                                                    <div class="fw-bold text-dark">{{ item.moneda.nombre }}</div>
                                                    <small class="text-muted">{{ item.moneda.codigo }}</small>
                                                </div>
                                            </div>
                                        </td>
                                        <td class="py-4 px-4 text-center">
                                            <div class="d-flex flex-column align-items-center">
                                                <span class="fw-bold text-success fs-5">
                                                    {{ item.tasa.tasa_compra|formatear_guaranies }}
                                                </span>
                                                <small class="text-muted">PYG</small>
                                            </div>
                                        </td>
                                        <td class="py-4 px-4 text-center">
                                            <div class="d-flex flex-column align-items-center">
                                                <span class="fw-bold text-danger fs-5">
                                                    {{ item.tasa.tasa_venta|formatear_guaranies }}
                                                </span>
                                                <small class="text-muted">PYG</small>
                                            </div>
                                        </td>
                                    </tr>
                                    {% endfor %}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <div class="row mt-5">
            <div class="col-12">
                <div class="alert alert-info shadow-sm text-center" role="alert">
                    <i class="fas fa-circle-info me-2"></i>
                    <strong>Nota:</strong> Las cotizaciones se actualizan cada hora. Para operaciones específicas, contacta con nuestros agentes.
                </div>
            </div>
        </div>
    </div>
    <div class="bg-white" style="height: 24px; clip-path: polygon(0 0, 100% 40%, 100% 100%, 0 100%);"></div>
</section>
{% else %}
<!-- Mensaje cuando no hay monedas disponibles -->
<section class="py-5">
    <div class="container">
        <div class="text-center">
            <div class="alert alert-warning shadow-sm" role="alert">
                <i class="fas fa-exclamation-triangle me-2"></i>
                <strong>No hay cotizaciones disponibles</strong>
                <p class="mb-0 mt-2">Por favor, contacta con el administrador para configurar las monedas y sus cotizaciones.</p>
            </div>
        </div>
    </div>
</section>
{% endif %}

<!-- Simulador público -->
<section id="simulador" class="py-5 bg-light">
  <div class="container">
    <div class="row justify-content-center">
      <div class="col-12">
        <div class="card sim-card shadow-soft">
          <div class="card-body p-4 p-md-5">
            <div class="d-flex align-items-center justify-content-between mb-4">
              <h3 class="h4 mb-0"><i class="fas fa-calculator text-primary me-2"></i>Simulador de cambio</h3>
              <span class="badge sim-header-badge">Base: PYG</span>
            </div>

            <div class="row g-4 align-items-stretch">
              <div class="col-12 col-lg-7">
                <div class="row g-3 align-items-end">
                  <div class="col-12 col-md-5">
                    <label class="form-label">De</label>
                    <select id="origen_pub" class="form-select form-select-lg">
                      <option value="PYG" selected>Guaraní (PYG)</option>
                    </select>
                  </div>
                  <div class="col-12 col-md-2 d-flex align-items-end justify-content-center">
                    <button id="btnToggleDir_pub" type="button" class="btn btn-outline-secondary btn-swap w-100" title="Cambiar dirección" aria-label="Cambiar dirección">
                      <i class="fas fa-right-left"></i>
                    </button>
                  </div>
                  <div class="col-12 col-md-5">
                    <label class="form-label">A</label>
                    <select id="destino_pub" class="form-select form-select-lg">
                      {% for m in monedas %}
                        {% if m.codigo != 'PYG' %}
                          <option value="{{ m.codigo }}" {% if m.codigo == 'USD' %}selected{% endif %}>{{ m.nombre }} ({{ m.codigo }})</option>
                        {% endif %}
                      {% endfor %}
                    </select>
                  </div>
                </div>

                <div class="row g-3 mt-1">
                  <div class="col-12">
                    <label class="form-label">Monto</label>
                    <input id="monto_pub" type="number" class="form-control form-control-lg" placeholder="0,00" step="any" min="0" value="1000">
                  </div>
                </div>
              </div>
              <div class="col-12 col-lg-5">
                <div id="resultado_pub" class="p-4 rounded sim-result">
                  <div class="text-muted small mb-1">Resultado</div>
                  <div class="fs-2 fw-bold" id="resultado_valor_pub">—</div>
                  <div class="small text-muted" id="resultado_detalle_pub">Selecciona monedas y monto para simular.</div>
                  <div class="small mt-2" id="resultado_tasas_pub"></div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
  <div class="bg-white" style="height: 16px;"></div>
</section>

<!-- Características -->
<section class="py-5 bg-light">
    <div class="container">
        <div class="row g-4">
            <div class="col-12 col-md-4">
                <div class="card h-100">
                    <div class="card-body">
                        <div class="text-primary fs-3 mb-2"><i class="fas fa-shield-halved"></i></div>
                        <h5 class="mb-2">Seguro</h5>
                        <p class="text-muted mb-0">Protección y cumplimiento para cada operación.</p>
                    </div>
                </div>
            </div>
            <div class="col-12 col-md-4">
                <div class="card h-100">
                    <div class="card-body">
                        <div class="text-primary fs-3 mb-2"><i class="fas fa-bolt"></i></div>
                        <h5 class="mb-2">Rápido</h5>
                        <p class="text-muted mb-0">Procesos ágiles y sin fricciones.</p>
                    </div>
                </div>
            </div>
            <div class="col-12 col-md-4">
                <div class="card h-100">
                    <div class="card-body">
                        <div class="text-primary fs-3 mb-2"><i class="fas fa-scale-balanced"></i></div>
                        <h5 class="mb-2">Transparente</h5>
                        <p class="text-muted mb-0">Precios claros y actualizados.</p>
                    </div>
                </div>
            </div>
        </div>
    </div>
</section>

<!-- Llamado a la acción -->
<section class="py-5">
    <div class="container">
        <div class="d-flex flex-column flex-md-row align-items-center justify-content-between p-4 p-md-5 bg-white rounded-3 shadow-soft">
            <div class="mb-3 mb-md-0">
                <h4 class="mb-1">¿Listo para comenzar?</h4>
                <p class="text-muted mb-0">Crea tu cuenta o inicia sesión para operar.</p>
            </div>
            <div class="d-flex gap-2">
                {% if user.is_authenticated %}
                <a href="{% url 'auth:dashboard' %}" class="btn btn-primary btn-rounded px-4">
                    <i class="fas fa-gauge-high me-2"></i>Ir al Dashboard
                </a>
                {% else %}
                <a href="{% url 'auth:login' %}" class="btn btn-primary btn-rounded px-4">
                    <i class="fas fa-right-to-bracket me-2"></i>Iniciar Sesión
                </a>
                <a href="{% url 'auth:registro' %}" class="btn btn-outline-primary btn-rounded px-4">
                    <i class="fas fa-user-plus me-2"></i>Registrarse
                </a>
                {% endif %}
            </div>
        </div>
    </div>
</section>
{% endblock %}

{% block extra_js %}
<script>
  (function() {
    const $monto = document.getElementById('monto_pub');
    const $origen = document.getElementById('origen_pub');
    const $destino = document.getElementById('destino_pub');
    const $btnToggle = document.getElementById('btnToggleDir_pub');
    const $resValor = document.getElementById('resultado_valor_pub');
    const $resDetalle = document.getElementById('resultado_detalle_pub');
    const $resTasas = document.getElementById('resultado_tasas_pub');

    const MONEDAS = [
      {% for m in monedas %}
        { codigo: '{{ m.codigo }}', nombre: '{{ m.nombre|escapejs }}' }{% if not forloop.last %},{% endif %}
      {% endfor %}
    ];
    
    const MONEDAS_FILTRADAS = MONEDAS.filter(m => m.codigo !== 'PYG');

    function setOptions(el, options, selected) {
      el.innerHTML = options.map(o => `<option value="${o.codigo}" ${o.codigo===selected?'selected':''}>${o.nombre} (${o.codigo})</option>`).join('');
    }

    let monedaToPYG = false; // false: PYG -> Moneda (default), true: Moneda -> PYG

    function applyDirection(preserveCode) {
      if (monedaToPYG) {
        const prefer = preserveCode || 'USD';
        setOptions($origen, MONEDAS_FILTRADAS, prefer);
        $origen.disabled = false;
        $destino.innerHTML = '<option value="PYG" selected>Guaraní (PYG)</option>';
        $destino.disabled = true;
      } else {
        $origen.innerHTML = '<option value="PYG" selected>Guaraní (PYG)</option>';
        $origen.disabled = true;
        const prefer = preserveCode || 'USD';
        const sel = MONEDAS_FILTRADAS.find(m => m.codigo === prefer) ? prefer : (MONEDAS_FILTRADAS[0]?.codigo || '');
        setOptions($destino, MONEDAS_FILTRADAS, sel);
        $destino.disabled = false;
      }
    }

    function getCurrentNonPYG() {
      if (monedaToPYG) return $origen.value;
      return $destino.value;
    }

    function formatDisplayWithDots(str) {
      if (!str) return str;
      const m = String(str).match(/^(\D*)([-\d.,]+)(.*)$/);
      if (!m) return str;
      const prefix = m[1] || '';
      const number = m[2] || '';
      const suffix = m[3] || '';
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
      const neg = intPart.startsWith('-');
      const intDigits = intPart.replace(/[^\d]/g, '');
      const grouped = intDigits.replace(/\B(?=(\d{3})+(?!\d))/g, '.');
      const intFinal = neg ? '-' + grouped : grouped;
      const numFinal = decPart ? `${intFinal}${sep}${decPart}` : intFinal;
      return `${prefix}${numFinal}${suffix}`;
    }

    function simulate() {
      const monto = $monto.value;
      const origen = $origen.value;
      const destino = $destino.value;
      if (!monto || !origen || !destino) return;
      fetch(`{% url 'tasa_cambio:simular_cambio_api' %}?monto=${encodeURIComponent(monto)}&origen=${encodeURIComponent(origen)}&destino=${encodeURIComponent(destino)}`)
        .then(r => r.json())
        .then(data => {
          if (!data.success) {
            $resValor.textContent = '—';
            $resDetalle.textContent = data.message || 'Error en la simulación.';
            $resTasas.textContent = '';
            return;
          }
          const d = data.data;
          $resValor.textContent = formatDisplayWithDots(d.resultado_formateado);
          $resDetalle.textContent = d.detalle;
          const t1 = d.tasa_origen ? `${d.tasa_origen.moneda} (${d.tasa_origen.tipo}): ${d.tasa_origen.valor}` : null;
          const t2 = d.tasa_destino ? `${d.tasa_destino.moneda} (${d.tasa_destino.tipo}): ${d.tasa_destino.valor}` : null;
          const parts = [t1, t2].filter(Boolean);
          $resTasas.textContent = parts.length ? `Cotizaciones usadas: ${parts.join(' · ')}` : '';
        })
        .catch(() => {
          $resValor.textContent = '—';
          $resDetalle.textContent = 'No se pudo simular.';
          $resTasas.textContent = '';
        });
    }

    $monto.addEventListener('input', simulate);
    $origen.addEventListener('change', simulate);
    $destino.addEventListener('change', simulate);
    $btnToggle.addEventListener('click', () => {
      const keep = getCurrentNonPYG();
      monedaToPYG = !monedaToPYG;
      applyDirection(keep);
      simulate();
    });

    applyDirection();
    simulate();
  })();
</script>
{% endblock %}

```

¡Perfecto! Ahora tienes una tabla elegante y moderna con las siguientes características:

## Tabla de cotizaciones mejorada:

1. **Estructura de tabla clara**:
   - **Columna Moneda**: Ícono de la moneda en círculo azul + nombre completo y código
   - **Columna Compra**: Tasa de compra en verde con unidad PYG
   - **Columna Venta**: Tasa de venta en rojo con unidad PYG

2. **Diseño visual atractivo**:
   - Header con fondo azul y iconos descriptivos
   - Íconos de monedas en círculos con fondo azul suave
   - Colores diferenciados: verde para compra, rojo para venta
   - Efecto hover sutil en las filas con escala y fondo azul claro

3. **Responsive y accesible**:
   - Tabla responsive que se adapta a pantallas pequeñas
   - Contenedor centrado con ancho máximo
   - Espaciado generoso para mejor legibilidad
   - Transiciones suaves para mejor UX

4. **Información clara**:
   - Cada fila muestra toda la información de una moneda
   - Tasas centradas y bien diferenciadas por color
   - Unidad de moneda (PYG) indicada debajo de cada tasa
   - Iconos intuitivos que indican la operación

La tabla mantiene la funcionalidad que necesitas pero con un diseño mucho más atractivo y profesional.

---

**User**

esta bien pero podria ser un poco mas pequeño, por ejemplo estar a la izquierda y en la derecha colocar Simulador de cambio asi comparten espacio?

---

**Cursor**

Excelente idea! Voy a reorganizar el layout para que las cotizaciones estén a la izquierda y el simulador a la derecha, compartiendo el espacio de manera más eficiente.


```django-html
{% extends "base.html" %}
{% load moneda_extras %}

{% block title %}Global Exchange - Casa de Cambios{% endblock %}

{% block extra_css %}
<style>
/* Ticker styles scoped to welcome */
.ticker { position: relative; overflow: hidden; background:#fff; border-radius:.75rem; }
.ticker__track {
    display:flex; align-items:center; gap:2rem; white-space:nowrap;
    animation: ticker-scroll 35s linear infinite;
    padding: .75rem 1rem;
}
.ticker:hover .ticker__track { animation-play-state: paused; }
.ticker__item { display:flex; align-items:center; gap:.5rem; color:#0f172a; }
.ticker__label { color:#6c757d; font-size:.9rem; }
.ticker__value { font-weight:700; color:#198754; }
@keyframes ticker-scroll {
  0% { transform: translateX(0); }
  100% { transform: translateX(-50%); }
}
@media (prefers-reduced-motion: reduce) { .ticker__track { animation:none; } }

/* Simulator styles */
.sim-card { border: none; }
.sim-header-badge { background: rgba(13,110,253,.08); color:#0d6efd; }
.sim-result { background: linear-gradient(180deg, #f8fafc 0%, #ffffff 100%); border:1px solid rgba(0,0,0,.06); }
.btn-swap { border-radius: 999px; height: 52px; display:flex; align-items:center; justify-content:center; font-size: 1.1rem; }
.btn-swap i { transition: transform .2s ease; }
.btn-swap:hover i { transform: rotate(180deg); }

/* Cotizaciones styles */
.hover-row { transition: all 0.2s ease; }
.hover-row:hover { background-color: rgba(13, 110, 253, 0.05) !important; transform: scale(1.01); }
</style>
{% endblock %}

{% block main_container_class %}container-fluid p-0{% endblock %}

{% block content %}
<!-- Hero principal -->
<section class="bg-primary text-white py-5 shadow-soft" style="background: linear-gradient(135deg, rgba(13,110,253,1) 0%, rgba(2,62,138,1) 100%);">
    <div class="container py-4">
        <div class="row align-items-center g-4">
            <div class="col-12 text-center">
                <h1 class="display-5 fw-bold mb-2">Global Exchange</h1>
                <p class="lead mb-4">Tu casa de cambios de confianza</p>
                <div class="d-flex justify-content-center gap-2 flex-wrap">
                    {% if user.is_authenticated %}
                    <a href="{% url 'auth:dashboard' %}" class="btn btn-light btn-lg btn-rounded px-4">
                        <i class="fas fa-gauge-high me-2"></i>Ir al Dashboard
                    </a>
                    <a href="{% url 'auth:logout' %}" class="btn btn-outline-light btn-lg btn-rounded px-4">
                        <i class="fas fa-right-from-bracket me-2"></i>Cerrar Sesión
                    </a>
                    {% else %}
                    <a href="{% url 'auth:login' %}" class="btn btn-light btn-lg btn-rounded px-4">
                        <i class="fas fa-right-to-bracket me-2"></i>Iniciar Sesión
                    </a>
                    <a href="{% url 'auth:registro' %}" class="btn btn-outline-light btn-lg btn-rounded px-4">
                        <i class="fas fa-user-plus me-2"></i>Registrarse
                    </a>
                    {% endif %}
                </div>
            </div>
        </div>
    </div>
    <div class="bg-white" style="height: 24px; clip-path: polygon(0 0, 100% 0, 100% 100%, 0 60%);"></div>
</section>



<!-- Ticker de tasas en movimiento -->
{% if monedas_con_tasas %}
<section class="py-3">
  <div class="container">
    <div class="ticker shadow-soft" role="region" aria-label="Cotizaciones en movimiento">
      <div class="ticker__track">
        <!-- Bloque 1 -->
        {% for item in monedas_con_tasas %}
        <span class="ticker__item">
          <i class="{{ item.moneda.codigo|get_icono_moneda }} text-primary"></i>
          <span class="ticker__label">{{ item.moneda.codigo }}</span>
          <span class="ticker__value">{{ item.tasa.tasa_venta|formatear_guaranies }}</span>
          <span class="text-muted">
            Compra {{ item.tasa.tasa_compra|formatear_guaranies }} · 
            Venta {{ item.tasa.tasa_venta|formatear_guaranies }}
          </span>
        </span>
        {% endfor %}

        <!-- Bloque 2 (duplicado para desplazamiento infinito) -->
        {% for item in monedas_con_tasas %}
        <span class="ticker__item">
          <i class="{{ item.moneda.codigo|get_icono_moneda }} text-primary"></i>
          <span class="ticker__label">{{ item.moneda.codigo }}</span>
          <span class="ticker__value">{{ item.tasa.tasa_venta|formatear_guaranies }}</span>
          <span class="text-muted">
            Compra {{ item.tasa.tasa_compra|formatear_guaranies }} · 
            Venta {{ item.tasa.tasa_venta|formatear_guaranies }}
          </span>
        </span>
        {% endfor %}
      </div>
    </div>
  </div>
  <div class="bg-white" style="height: 16px;"></div>
</section>
{% endif %}

<!-- Cotizaciones y Simulador -->
{% if monedas_con_tasas %}
<section class="py-5">
    <div class="container">
        <div class="row g-4">
            <!-- Cotizaciones - Columna izquierda -->
            <div class="col-12 col-lg-6">
                <div class="mb-4">
                    <h2 class="h3 text-primary mb-2">
                        <i class="fas fa-coins me-2"></i>Cotizaciones
                    </h2>
                    <p class="text-muted mb-0">Moneda base: Guaraní (PYG)</p>
                </div>
                
                <div class="card border-0 shadow-soft overflow-hidden">
                    <div class="card-body p-0">
                        <div class="table-responsive">
                            <table class="table table-hover mb-0">
                                <thead>
                                    <tr class="table-primary">
                                        <th class="border-0 py-3 px-3 fw-bold">
                                            <i class="fas fa-coins me-1 text-primary"></i>Moneda
                                        </th>
                                        <th class="border-0 py-3 px-3 text-center fw-bold">
                                            <i class="fas fa-arrow-down me-1 text-success"></i>Compra
                                        </th>
                                        <th class="border-0 py-3 px-3 text-center fw-bold">
                                            <i class="fas fa-arrow-up me-1 text-danger"></i>Venta
                                        </th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {% for item in monedas_con_tasas %}
                                    <tr class="align-middle hover-row">
                                        <td class="py-3 px-3">
                                            <div class="d-flex align-items-center">
                                                <div class="me-2">
                                                    <div class="bg-primary bg-opacity-10 rounded-circle p-1">
                                                        <i class="{{ item.moneda.codigo|get_icono_moneda }} text-primary fs-6"></i>
                                                    </div>
                                                </div>
                                                <div>
                                                    <div class="fw-bold text-dark small">{{ item.moneda.nombre }}</div>
                                                    <small class="text-muted">{{ item.moneda.codigo }}</small>
                                                </div>
                                            </div>
                                        </td>
                                        <td class="py-3 px-3 text-center">
                                            <div class="d-flex flex-column align-items-center">
                                                <span class="fw-bold text-success fs-6">
                                                    {{ item.tasa.tasa_compra|formatear_guaranies }}
                                                </span>
                                                <small class="text-muted">PYG</small>
                                            </div>
                                        </td>
                                        <td class="py-3 px-3 text-center">
                                            <div class="d-flex flex-column align-items-center">
                                                <span class="fw-bold text-danger fs-6">
                                                    {{ item.tasa.tasa_venta|formatear_guaranies }}
                                                </span>
                                                <small class="text-muted">PYG</small>
                                            </div>
                                        </td>
                                    </tr>
                                    {% endfor %}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Simulador - Columna derecha -->
            <div class="col-12 col-lg-6">
                <div class="mb-4">
                    <h2 class="h3 text-primary mb-2">
                        <i class="fas fa-calculator me-2"></i>Simulador de cambio
                    </h2>
                    <p class="text-muted mb-0">Calcula tu cambio al instante</p>
                </div>
                
                <div class="card sim-card shadow-soft h-100">
                    <div class="card-body p-4">
                        <div class="row g-3 align-items-end mb-4">
                            <div class="col-12 col-md-5">
                                <label class="form-label">De</label>
                                <select id="origen_pub" class="form-select">
                                    <option value="PYG" selected>Guaraní (PYG)</option>
                                </select>
                            </div>
                            <div class="col-12 col-md-2 d-flex align-items-end justify-content-center">
                                <button id="btnToggleDir_pub" type="button" class="btn btn-outline-secondary btn-swap w-100" title="Cambiar dirección" aria-label="Cambiar dirección">
                                    <i class="fas fa-right-left"></i>
                                </button>
                            </div>
                            <div class="col-12 col-md-5">
                                <label class="form-label">A</label>
                                <select id="destino_pub" class="form-select">
                                    {% for m in monedas %}
                                        {% if m.codigo != 'PYG' %}
                                            <option value="{{ m.codigo }}" {% if m.codigo == 'USD' %}selected{% endif %}>{{ m.nombre }} ({{ m.codigo }})</option>
                                        {% endif %}
                                    {% endfor %}
                                </select>
                            </div>
                        </div>

                        <div class="mb-4">
                            <label class="form-label">Monto</label>
                            <input id="monto_pub" type="number" class="form-control" placeholder="0,00" step="any" min="0" value="1000">
                        </div>

                        <div id="resultado_pub" class="p-4 rounded sim-result">
                            <div class="text-muted small mb-1">Resultado</div>
                            <div class="fs-3 fw-bold" id="resultado_valor_pub">—</div>
                            <div class="small text-muted" id="resultado_detalle_pub">Selecciona monedas y monto para simular.</div>
                            <div class="small mt-2" id="resultado_tasas_pub"></div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <div class="row mt-4">
            <div class="col-12">
                <div class="alert alert-info shadow-sm text-center" role="alert">
                    <i class="fas fa-circle-info me-2"></i>
                    <strong>Nota:</strong> Las cotizaciones se actualizan cada hora. Para operaciones específicas, contacta con nuestros agentes.
                </div>
            </div>
        </div>
    </div>
    <div class="bg-white" style="height: 24px; clip-path: polygon(0 0, 100% 40%, 100% 100%, 0 100%);"></div>
</section>
{% else %}
<!-- Mensaje cuando no hay monedas disponibles -->
<section class="py-5">
    <div class="container">
        <div class="text-center">
            <div class="alert alert-warning shadow-sm" role="alert">
                <i class="fas fa-exclamation-triangle me-2"></i>
                <strong>No hay cotizaciones disponibles</strong>
                <p class="mb-0 mt-2">Por favor, contacta con el administrador para configurar las monedas y sus cotizaciones.</p>
            </div>
        </div>
    </div>
</section>
{% endif %}

<!-- Características -->
<section class="py-5 bg-light">
    <div class="container">
        <div class="row g-4">
            <div class="col-12 col-md-4">
                <div class="card h-100">
                    <div class="card-body">
                        <div class="text-primary fs-3 mb-2"><i class="fas fa-shield-halved"></i></div>
                        <h5 class="mb-2">Seguro</h5>
                        <p class="text-muted mb-0">Protección y cumplimiento para cada operación.</p>
                    </div>
                </div>
            </div>
            <div class="col-12 col-md-4">
                <div class="card h-100">
                    <div class="card-body">
                        <div class="text-primary fs-3 mb-2"><i class="fas fa-bolt"></i></div>
                        <h5 class="mb-2">Rápido</h5>
                        <p class="text-muted mb-0">Procesos ágiles y sin fricciones.</p>
                    </div>
                </div>
            </div>
            <div class="col-12 col-md-4">
                <div class="card h-100">
                    <div class="card-body">
                        <div class="text-primary fs-3 mb-2"><i class="fas fa-scale-balanced"></i></div>
                        <h5 class="mb-2">Transparente</h5>
                        <p class="text-muted mb-0">Precios claros y actualizados.</p>
                    </div>
                </div>
            </div>
        </div>
    </div>
</section>

<!-- Llamado a la acción -->
<section class="py-5">
    <div class="container">
        <div class="d-flex flex-column flex-md-row align-items-center justify-content-between p-4 p-md-5 bg-white rounded-3 shadow-soft">
            <div class="mb-3 mb-md-0">
                <h4 class="mb-1">¿Listo para comenzar?</h4>
                <p class="text-muted mb-0">Crea tu cuenta o inicia sesión para operar.</p>
            </div>
            <div class="d-flex gap-2">
                {% if user.is_authenticated %}
                <a href="{% url 'auth:dashboard' %}" class="btn btn-primary btn-rounded px-4">
                    <i class="fas fa-gauge-high me-2"></i>Ir al Dashboard
                </a>
                {% else %}
                <a href="{% url 'auth:login' %}" class="btn btn-primary btn-rounded px-4">
                    <i class="fas fa-right-to-bracket me-2"></i>Iniciar Sesión
                </a>
                <a href="{% url 'auth:registro' %}" class="btn btn-outline-primary btn-rounded px-4">
                    <i class="fas fa-user-plus me-2"></i>Registrarse
                </a>
                {% endif %}
            </div>
        </div>
    </div>
</section>
{% endblock %}

{% block extra_js %}
<script>
  (function() {
    const $monto = document.getElementById('monto_pub');
    const $origen = document.getElementById('origen_pub');
    const $destino = document.getElementById('destino_pub');
    const $btnToggle = document.getElementById('btnToggleDir_pub');
    const $resValor = document.getElementById('resultado_valor_pub');
    const $resDetalle = document.getElementById('resultado_detalle_pub');
    const $resTasas = document.getElementById('resultado_tasas_pub');

    const MONEDAS = [
      {% for m in monedas %}
        { codigo: '{{ m.codigo }}', nombre: '{{ m.nombre|escapejs }}' }{% if not forloop.last %},{% endif %}
      {% endfor %}
    ];
    
    const MONEDAS_FILTRADAS = MONEDAS.filter(m => m.codigo !== 'PYG');

    function setOptions(el, options, selected) {
      el.innerHTML = options.map(o => `<option value="${o.codigo}" ${o.codigo===selected?'selected':''}>${o.nombre} (${o.codigo})</option>`).join('');
    }

    let monedaToPYG = false; // false: PYG -> Moneda (default), true: Moneda -> PYG

    function applyDirection(preserveCode) {
      if (monedaToPYG) {
        const prefer = preserveCode || 'USD';
        setOptions($origen, MONEDAS_FILTRADAS, prefer);
        $origen.disabled = false;
        $destino.innerHTML = '<option value="PYG" selected>Guaraní (PYG)</option>';
        $destino.disabled = true;
      } else {
        $origen.innerHTML = '<option value="PYG" selected>Guaraní (PYG)</option>';
        $origen.disabled = true;
        const prefer = preserveCode || 'USD';
        const sel = MONEDAS_FILTRADAS.find(m => m.codigo === prefer) ? prefer : (MONEDAS_FILTRADAS[0]?.codigo || '');
        setOptions($destino, MONEDAS_FILTRADAS, sel);
        $destino.disabled = false;
      }
    }

    function getCurrentNonPYG() {
      if (monedaToPYG) return $origen.value;
      return $destino.value;
    }

    function formatDisplayWithDots(str) {
      if (!str) return str;
      const m = String(str).match(/^(\D*)([-\d.,]+)(.*)$/);
      if (!m) return str;
      const prefix = m[1] || '';
      const number = m[2] || '';
      const suffix = m[3] || '';
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
      const neg = intPart.startsWith('-');
      const intDigits = intPart.replace(/[^\d]/g, '');
      const grouped = intDigits.replace(/\B(?=(\d{3})+(?!\d))/g, '.');
      const intFinal = neg ? '-' + grouped : grouped;
      const numFinal = decPart ? `${intFinal}${sep}${decPart}` : intFinal;
      return `${prefix}${numFinal}${suffix}`;
    }

    function simulate() {
      const monto = $monto.value;
      const origen = $origen.value;
      const destino = $destino.value;
      if (!monto || !origen || !destino) return;
      fetch(`{% url 'tasa_cambio:simular_cambio_api' %}?monto=${encodeURIComponent(monto)}&origen=${encodeURIComponent(origen)}&destino=${encodeURIComponent(destino)}`)
        .then(r => r.json())
        .then(data => {
          if (!data.success) {
            $resValor.textContent = '—';
            $resDetalle.textContent = data.message || 'Error en la simulación.';
            $resTasas.textContent = '';
            return;
          }
          const d = data.data;
          $resValor.textContent = formatDisplayWithDots(d.resultado_formateado);
          $resDetalle.textContent = d.detalle;
          const t1 = d.tasa_origen ? `${d.tasa_origen.moneda} (${d.tasa_origen.tipo}): ${d.tasa_origen.valor}` : null;
          const t2 = d.tasa_destino ? `${d.tasa_destino.moneda} (${d.tasa_destino.tipo}): ${d.tasa_destino.valor}` : null;
          const parts = [t1, t2].filter(Boolean);
          $resTasas.textContent = parts.length ? `Cotizaciones usadas: ${parts.join(' · ')}` : '';
        })
        .catch(() => {
          $resValor.textContent = '—';
          $resDetalle.textContent = 'No se pudo simular.';
          $resTasas.textContent = '';
        });
    }

    $monto.addEventListener('input', simulate);
    $origen.addEventListener('change', simulate);
    $destino.addEventListener('change', simulate);
    $btnToggle.addEventListener('click', () => {
      const keep = getCurrentNonPYG();
      monedaToPYG = !monedaToPYG;
      applyDirection(keep);
      simulate();
    });

    applyDirection();
    simulate();
  })();
</script>
{% endblock %}

```

¡Perfecto! He reorganizado el layout para que sea mucho más eficiente en el uso del espacio:

## Nuevo layout optimizado:

### **Columna izquierda (50%) - Cotizaciones**:
- **Tabla más compacta** con padding reducido
- **Tamaños de fuente más pequeños** para ahorrar espacio
- **Íconos más pequeños** pero aún visibles
- **Mantiene toda la funcionalidad** pero en menos espacio

### **Columna derecha (50%) - Simulador**:
- **Simulador completo** con todas sus funciones
- **Layout vertical** más compacto
- **Mismo diseño** pero optimizado para el espacio disponible
- **Altura igual** a la tabla de cotizaciones

## Beneficios del nuevo diseño:

1. **Uso eficiente del espacio**: Ambas secciones comparten el ancho de pantalla
2. **Mejor experiencia de usuario**: Los usuarios pueden ver cotizaciones y simular al mismo tiempo
3. **Diseño más equilibrado**: No hay secciones que ocupen todo el ancho innecesariamente
4. **Responsive**: En móviles se apilan verticalmente
5. **Información relacionada junta**: Cotizaciones y simulador están lógicamente conectados

El layout ahora es mucho más eficiente y permite a los usuarios consultar las cotizaciones mientras usan el simulador, creando una experiencia más fluida y práctica.

---

**User**

al hacer click en cada moneda podra ir a historico @tasacambio_historial.html  solo si esta logeado y el usuario tiene permiso para acceder a esa vista

---

**Cursor**

Perfecto! Voy a agregar enlaces a cada moneda en la tabla de cotizaciones para que los usuarios puedan acceder al historial. Primero necesito verificar la URL del historial y luego implementar los enlaces con las verificaciones de permisos.


Perfecto! Ahora veo que la URL es `tasa_cambio:tasacambio_historial` y requiere el permiso `tasa_cambio.view_tasacambio`. Voy a modificar la tabla de cotizaciones para agregar enlaces al historial de cada moneda:


```django-html
{% extends "base.html" %}
{% load moneda_extras %}

{% block title %}Global Exchange - Casa de Cambios{% endblock %}

{% block extra_css %}
<style>
/* Ticker styles scoped to welcome */
.ticker { position: relative; overflow: hidden; background:#fff; border-radius:.75rem; }
.ticker__track {
    display:flex; align-items:center; gap:2rem; white-space:nowrap;
    animation: ticker-scroll 35s linear infinite;
    padding: .75rem 1rem;
}
.ticker:hover .ticker__track { animation-play-state: paused; }
.ticker__item { display:flex; align-items:center; gap:.5rem; color:#0f172a; }
.ticker__label { color:#6c757d; font-size:.9rem; }
.ticker__value { font-weight:700; color:#198754; }
@keyframes ticker-scroll {
  0% { transform: translateX(0); }
  100% { transform: translateX(-50%); }
}
@media (prefers-reduced-motion: reduce) { .ticker__track { animation:none; } }

/* Simulator styles */
.sim-card { border: none; }
.sim-header-badge { background: rgba(13,110,253,.08); color:#0d6efd; }
.sim-result { background: linear-gradient(180deg, #f8fafc 0%, #ffffff 100%); border:1px solid rgba(0,0,0,.06); }
.btn-swap { border-radius: 999px; height: 52px; display:flex; align-items:center; justify-content:center; font-size: 1.1rem; }
.btn-swap i { transition: transform .2s ease; }
.btn-swap:hover i { transform: rotate(180deg); }

/* Cotizaciones styles */
.hover-row { transition: all 0.2s ease; }
.hover-row:hover { background-color: rgba(13, 110, 253, 0.05) !important; transform: scale(1.01); }
</style>
{% endblock %}

{% block main_container_class %}container-fluid p-0{% endblock %}

{% block content %}
<!-- Hero principal -->
<section class="bg-primary text-white py-5 shadow-soft" style="background: linear-gradient(135deg, rgba(13,110,253,1) 0%, rgba(2,62,138,1) 100%);">
    <div class="container py-4">
        <div class="row align-items-center g-4">
            <div class="col-12 text-center">
                <h1 class="display-5 fw-bold mb-2">Global Exchange</h1>
                <p class="lead mb-4">Tu casa de cambios de confianza</p>
                <div class="d-flex justify-content-center gap-2 flex-wrap">
                    {% if user.is_authenticated %}
                    <a href="{% url 'auth:dashboard' %}" class="btn btn-light btn-lg btn-rounded px-4">
                        <i class="fas fa-gauge-high me-2"></i>Ir al Dashboard
                    </a>
                    <a href="{% url 'auth:logout' %}" class="btn btn-outline-light btn-lg btn-rounded px-4">
                        <i class="fas fa-right-from-bracket me-2"></i>Cerrar Sesión
                    </a>
                    {% else %}
                    <a href="{% url 'auth:login' %}" class="btn btn-light btn-lg btn-rounded px-4">
                        <i class="fas fa-right-to-bracket me-2"></i>Iniciar Sesión
                    </a>
                    <a href="{% url 'auth:registro' %}" class="btn btn-outline-light btn-lg btn-rounded px-4">
                        <i class="fas fa-user-plus me-2"></i>Registrarse
                    </a>
                    {% endif %}
                </div>
            </div>
        </div>
    </div>
    <div class="bg-white" style="height: 24px; clip-path: polygon(0 0, 100% 0, 100% 100%, 0 60%);"></div>
</section>



<!-- Ticker de tasas en movimiento -->
{% if monedas_con_tasas %}
<section class="py-3">
  <div class="container">
    <div class="ticker shadow-soft" role="region" aria-label="Cotizaciones en movimiento">
      <div class="ticker__track">
        <!-- Bloque 1 -->
        {% for item in monedas_con_tasas %}
        <span class="ticker__item">
          <i class="{{ item.moneda.codigo|get_icono_moneda }} text-primary"></i>
          <span class="ticker__label">{{ item.moneda.codigo }}</span>
          <span class="ticker__value">{{ item.tasa.tasa_venta|formatear_guaranies }}</span>
          <span class="text-muted">
            Compra {{ item.tasa.tasa_compra|formatear_guaranies }} · 
            Venta {{ item.tasa.tasa_venta|formatear_guaranies }}
          </span>
        </span>
        {% endfor %}

        <!-- Bloque 2 (duplicado para desplazamiento infinito) -->
        {% for item in monedas_con_tasas %}
        <span class="ticker__item">
          <i class="{{ item.moneda.codigo|get_icono_moneda }} text-primary"></i>
          <span class="ticker__label">{{ item.moneda.codigo }}</span>
          <span class="ticker__value">{{ item.tasa.tasa_venta|formatear_guaranies }}</span>
          <span class="text-muted">
            Compra {{ item.tasa.tasa_compra|formatear_guaranies }} · 
            Venta {{ item.tasa.tasa_venta|formatear_guaranies }}
          </span>
        </span>
        {% endfor %}
      </div>
    </div>
  </div>
  <div class="bg-white" style="height: 16px;"></div>
</section>
{% endif %}

<!-- Cotizaciones y Simulador -->
{% if monedas_con_tasas %}
<section class="py-5">
    <div class="container">
        <div class="row g-4">
            <!-- Cotizaciones - Columna izquierda -->
            <div class="col-12 col-lg-6">
                <div class="mb-4">
                    <h2 class="h3 text-primary mb-2">
                        <i class="fas fa-coins me-2"></i>Cotizaciones
                    </h2>
                    <p class="text-muted mb-0">Moneda base: Guaraní (PYG)</p>
                </div>
                
                <div class="card border-0 shadow-soft overflow-hidden">
                    <div class="card-body p-0">
                        <div class="table-responsive">
                            <table class="table table-hover mb-0">
                                <thead>
                                    <tr class="table-primary">
                                        <th class="border-0 py-3 px-3 fw-bold">
                                            <i class="fas fa-coins me-1 text-primary"></i>Moneda
                                        </th>
                                        <th class="border-0 py-3 px-3 text-center fw-bold">
                                            <i class="fas fa-arrow-down me-1 text-success"></i>Compra
                                        </th>
                                        <th class="border-0 py-3 px-3 text-center fw-bold">
                                            <i class="fas fa-arrow-up me-1 text-danger"></i>Venta
                                        </th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {% for item in monedas_con_tasas %}
                                    <tr class="align-middle hover-row">
                                        <td class="py-3 px-3">
                                            <div class="d-flex align-items-center">
                                                <div class="me-2">
                                                    <div class="bg-primary bg-opacity-10 rounded-circle p-1">
                                                        <i class="{{ item.moneda.codigo|get_icono_moneda }} text-primary fs-6"></i>
                                                    </div>
                                                </div>
                                                <div>
                                                    {% if user.is_authenticated and perms.tasa_cambio.view_tasacambio %}
                                                    <a href="{% url 'tasa_cambio:tasacambio_historial' item.moneda.id %}" 
                                                       class="text-decoration-none">
                                                        <div class="fw-bold text-dark small hover-text-primary">{{ item.moneda.nombre }}</div>
                                                        <small class="text-muted">{{ item.moneda.codigo }}</small>
                                                    </a>
                                                    {% else %}
                                                    <div class="fw-bold text-dark small">{{ item.moneda.nombre }}</div>
                                                    <small class="text-muted">{{ item.moneda.codigo }}</small>
                                                    {% endif %}
                                                </div>
                                            </div>
                                        </td>
                                        <td class="py-3 px-3 text-center">
                                            <div class="d-flex flex-column align-items-center">
                                                <span class="fw-bold text-success fs-6">
                                                    {{ item.tasa.tasa_compra|formatear_guaranies }}
                                                </span>
                                                <small class="text-muted">PYG</small>
                                            </div>
                                        </td>
                                        <td class="py-3 px-3 text-center">
                                            <div class="d-flex flex-column align-items-center">
                                                <span class="fw-bold text-danger fs-6">
                                                    {{ item.tasa.tasa_venta|formatear_guaranies }}
                                                </span>
                                                <small class="text-muted">PYG</small>
                                            </div>
                                        </td>
                                    </tr>
                                    {% endfor %}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Simulador - Columna derecha -->
            <div class="col-12 col-lg-6">
                <div class="mb-4">
                    <h2 class="h3 text-primary mb-2">
                        <i class="fas fa-calculator me-2"></i>Simulador de cambio
                    </h2>
                    <p class="text-muted mb-0">Calcula tu cambio al instante</p>
                </div>
                
                <div class="card sim-card shadow-soft h-100">
                    <div class="card-body p-4">
                        <div class="row g-3 align-items-end mb-4">
                            <div class="col-12 col-md-5">
                                <label class="form-label">De</label>
                                <select id="origen_pub" class="form-select">
                                    <option value="PYG" selected>Guaraní (PYG)</option>
                                </select>
                            </div>
                            <div class="col-12 col-md-2 d-flex align-items-end justify-content-center">
                                <button id="btnToggleDir_pub" type="button" class="btn btn-outline-secondary btn-swap w-100" title="Cambiar dirección" aria-label="Cambiar dirección">
                                    <i class="fas fa-right-left"></i>
                                </button>
                            </div>
                            <div class="col-12 col-md-5">
                                <label class="form-label">A</label>
                                <select id="destino_pub" class="form-select">
                                    {% for m in monedas %}
                                        {% if m.codigo != 'PYG' %}
                                            <option value="{{ m.codigo }}" {% if m.codigo == 'USD' %}selected{% endif %}>{{ m.nombre }} ({{ m.codigo }})</option>
                                        {% endif %}
                                    {% endfor %}
                                </select>
                            </div>
                        </div>

                        <div class="mb-4">
                            <label class="form-label">Monto</label>
                            <input id="monto_pub" type="number" class="form-control" placeholder="0,00" step="any" min="0" value="1000">
                        </div>

                        <div id="resultado_pub" class="p-4 rounded sim-result">
                            <div class="text-muted small mb-1">Resultado</div>
                            <div class="fs-3 fw-bold" id="resultado_valor_pub">—</div>
                            <div class="small text-muted" id="resultado_detalle_pub">Selecciona monedas y monto para simular.</div>
                            <div class="small mt-2" id="resultado_tasas_pub"></div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <div class="row mt-4">
            <div class="col-12">
                <div class="alert alert-info shadow-sm text-center" role="alert">
                    <i class="fas fa-circle-info me-2"></i>
                    <strong>Nota:</strong> Las cotizaciones se actualizan cada hora. Para operaciones específicas, contacta con nuestros agentes.
                </div>
            </div>
        </div>
    </div>
    <div class="bg-white" style="height: 24px; clip-path: polygon(0 0, 100% 40%, 100% 100%, 0 100%);"></div>
</section>
{% else %}
<!-- Mensaje cuando no hay monedas disponibles -->
<section class="py-5">
    <div class="container">
        <div class="text-center">
            <div class="alert alert-warning shadow-sm" role="alert">
                <i class="fas fa-exclamation-triangle me-2"></i>
                <strong>No hay cotizaciones disponibles</strong>
                <p class="mb-0 mt-2">Por favor, contacta con el administrador para configurar las monedas y sus cotizaciones.</p>
            </div>
        </div>
    </div>
</section>
{% endif %}

<!-- Características -->
<section class="py-5 bg-light">
    <div class="container">
        <div class="row g-4">
            <div class="col-12 col-md-4">
                <div class="card h-100">
                    <div class="card-body">
                        <div class="text-primary fs-3 mb-2"><i class="fas fa-shield-halved"></i></div>
                        <h5 class="mb-2">Seguro</h5>
                        <p class="text-muted mb-0">Protección y cumplimiento para cada operación.</p>
                    </div>
                </div>
            </div>
            <div class="col-12 col-md-4">
                <div class="card h-100">
                    <div class="card-body">
                        <div class="text-primary fs-3 mb-2"><i class="fas fa-bolt"></i></div>
                        <h5 class="mb-2">Rápido</h5>
                        <p class="text-muted mb-0">Procesos ágiles y sin fricciones.</p>
                    </div>
                </div>
            </div>
            <div class="col-12 col-md-4">
                <div class="card h-100">
                    <div class="card-body">
                        <div class="text-primary fs-3 mb-2"><i class="fas fa-scale-balanced"></i></div>
                        <h5 class="mb-2">Transparente</h5>
                        <p class="text-muted mb-0">Precios claros y actualizados.</p>
                    </div>
                </div>
            </div>
        </div>
    </div>
</section>

<!-- Llamado a la acción -->
<section class="py-5">
    <div class="container">
        <div class="d-flex flex-column flex-md-row align-items-center justify-content-between p-4 p-md-5 bg-white rounded-3 shadow-soft">
            <div class="mb-3 mb-md-0">
                <h4 class="mb-1">¿Listo para comenzar?</h4>
                <p class="text-muted mb-0">Crea tu cuenta o inicia sesión para operar.</p>
            </div>
            <div class="d-flex gap-2">
                {% if user.is_authenticated %}
                <a href="{% url 'auth:dashboard' %}" class="btn btn-primary btn-rounded px-4">
                    <i class="fas fa-gauge-high me-2"></i>Ir al Dashboard
                </a>
                {% else %}
                <a href="{% url 'auth:login' %}" class="btn btn-primary btn-rounded px-4">
                    <i class="fas fa-right-to-bracket me-2"></i>Iniciar Sesión
                </a>
                <a href="{% url 'auth:registro' %}" class="btn btn-outline-primary btn-rounded px-4">
                    <i class="fas fa-user-plus me-2"></i>Registrarse
                </a>
                {% endif %}
            </div>
        </div>
    </div>
</section>
{% endblock %}

{% block extra_js %}
<script>
  (function() {
    const $monto = document.getElementById('monto_pub');
    const $origen = document.getElementById('origen_pub');
    const $destino = document.getElementById('destino_pub');
    const $btnToggle = document.getElementById('btnToggleDir_pub');
    const $resValor = document.getElementById('resultado_valor_pub');
    const $resDetalle = document.getElementById('resultado_detalle_pub');
    const $resTasas = document.getElementById('resultado_tasas_pub');

    const MONEDAS = [
      {% for m in monedas %}
        { codigo: '{{ m.codigo }}', nombre: '{{ m.nombre|escapejs }}' }{% if not forloop.last %},{% endif %}
      {% endfor %}
    ];
    
    const MONEDAS_FILTRADAS = MONEDAS.filter(m => m.codigo !== 'PYG');

    function setOptions(el, options, selected) {
      el.innerHTML = options.map(o => `<option value="${o.codigo}" ${o.codigo===selected?'selected':''}>${o.nombre} (${o.codigo})</option>`).join('');
    }

    let monedaToPYG = false; // false: PYG -> Moneda (default), true: Moneda -> PYG

    function applyDirection(preserveCode) {
      if (monedaToPYG) {
        const prefer = preserveCode || 'USD';
        setOptions($origen, MONEDAS_FILTRADAS, prefer);
        $origen.disabled = false;
        $destino.innerHTML = '<option value="PYG" selected>Guaraní (PYG)</option>';
        $destino.disabled = true;
      } else {
        $origen.innerHTML = '<option value="PYG" selected>Guaraní (PYG)</option>';
        $origen.disabled = true;
        const prefer = preserveCode || 'USD';
        const sel = MONEDAS_FILTRADAS.find(m => m.codigo === prefer) ? prefer : (MONEDAS_FILTRADAS[0]?.codigo || '');
        setOptions($destino, MONEDAS_FILTRADAS, sel);
        $destino.disabled = false;
      }
    }

    function getCurrentNonPYG() {
      if (monedaToPYG) return $origen.value;
      return $destino.value;
    }

    function formatDisplayWithDots(str) {
      if (!str) return str;
      const m = String(str).match(/^(\D*)([-\d.,]+)(.*)$/);
      if (!m) return str;
      const prefix = m[1] || '';
      const number = m[2] || '';
      const suffix = m[3] || '';
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
      const neg = intPart.startsWith('-');
      const intDigits = intPart.replace(/[^\d]/g, '');
      const grouped = intDigits.replace(/\B(?=(\d{3})+(?!\d))/g, '.');
      const intFinal = neg ? '-' + grouped : grouped;
      const numFinal = decPart ? `${intFinal}${sep}${decPart}` : intFinal;
      return `${prefix}${numFinal}${suffix}`;
    }

    function simulate() {
      const monto = $monto.value;
      const origen = $origen.value;
      const destino = $destino.value;
      if (!monto || !origen || !destino) return;
      fetch(`{% url 'tasa_cambio:simular_cambio_api' %}?monto=${encodeURIComponent(monto)}&origen=${encodeURIComponent(origen)}&destino=${encodeURIComponent(destino)}`)
        .then(r => r.json())
        .then(data => {
          if (!data.success) {
            $resValor.textContent = '—';
            $resDetalle.textContent = data.message || 'Error en la simulación.';
            $resTasas.textContent = '';
            return;
          }
          const d = data.data;
          $resValor.textContent = formatDisplayWithDots(d.resultado_formateado);
          $resDetalle.textContent = d.detalle;
          const t1 = d.tasa_origen ? `${d.tasa_origen.moneda} (${d.tasa_origen.tipo}): ${d.tasa_origen.valor}` : null;
          const t2 = d.tasa_destino ? `${d.tasa_destino.moneda} (${d.tasa_destino.tipo}): ${d.tasa_destino.valor}` : null;
          const parts = [t1, t2].filter(Boolean);
          $resTasas.textContent = parts.length ? `Cotizaciones usadas: ${parts.join(' · ')}` : '';
        })
        .catch(() => {
          $resValor.textContent = '—';
          $resDetalle.textContent = 'No se pudo simular.';
          $resTasas.textContent = '';
        });
    }

    $monto.addEventListener('input', simulate);
    $origen.addEventListener('change', simulate);
    $destino.addEventListener('change', simulate);
    $btnToggle.addEventListener('click', () => {
      const keep = getCurrentNonPYG();
      monedaToPYG = !monedaToPYG;
      applyDirection(keep);
      simulate();
    });

    applyDirection();
    simulate();
  })();
</script>
{% endblock %}

```

Ahora voy a agregar los estilos CSS para el efecto hover del enlace:


```django-html
{% extends "base.html" %}
{% load moneda_extras %}

{% block title %}Global Exchange - Casa de Cambios{% endblock %}

{% block extra_css %}
<style>
/* Ticker styles scoped to welcome */
.ticker { position: relative; overflow: hidden; background:#fff; border-radius:.75rem; }
.ticker__track {
    display:flex; align-items:center; gap:2rem; white-space:nowrap;
    animation: ticker-scroll 35s linear infinite;
    padding: .75rem 1rem;
}
.ticker:hover .ticker__track { animation-play-state: paused; }
.ticker__item { display:flex; align-items:center; gap:.5rem; color:#0f172a; }
.ticker__label { color:#6c757d; font-size:.9rem; }
.ticker__value { font-weight:700; color:#198754; }
@keyframes ticker-scroll {
  0% { transform: translateX(0); }
  100% { transform: translateX(-50%); }
}
@media (prefers-reduced-motion: reduce) { .ticker__track { animation:none; } }

/* Simulator styles */
.sim-card { border: none; }
.sim-header-badge { background: rgba(13,110,253,.08); color:#0d6efd; }
.sim-result { background: linear-gradient(180deg, #f8fafc 0%, #ffffff 100%); border:1px solid rgba(0,0,0,.06); }
.btn-swap { border-radius: 999px; height: 52px; display:flex; align-items:center; justify-content:center; font-size: 1.1rem; }
.btn-swap i { transition: transform .2s ease; }
.btn-swap:hover i { transform: rotate(180deg); }

/* Cotizaciones styles */
.hover-row { transition: all 0.2s ease; }
.hover-row:hover { background-color: rgba(13, 110, 253, 0.05) !important; transform: scale(1.01); }
.hover-text-primary:hover { color: #0d6efd !important; }
</style>
{% endblock %}

{% block main_container_class %}container-fluid p-0{% endblock %}

{% block content %}
<!-- Hero principal -->
<section class="bg-primary text-white py-5 shadow-soft" style="background: linear-gradient(135deg, rgba(13,110,253,1) 0%, rgba(2,62,138,1) 100%);">
    <div class="container py-4">
        <div class="row align-items-center g-4">
            <div class="col-12 text-center">
                <h1 class="display-5 fw-bold mb-2">Global Exchange</h1>
                <p class="lead mb-4">Tu casa de cambios de confianza</p>
                <div class="d-flex justify-content-center gap-2 flex-wrap">
                    {% if user.is_authenticated %}
                    <a href="{% url 'auth:dashboard' %}" class="btn btn-light btn-lg btn-rounded px-4">
                        <i class="fas fa-gauge-high me-2"></i>Ir al Dashboard
                    </a>
                    <a href="{% url 'auth:logout' %}" class="btn btn-outline-light btn-lg btn-rounded px-4">
                        <i class="fas fa-right-from-bracket me-2"></i>Cerrar Sesión
                    </a>
                    {% else %}
                    <a href="{% url 'auth:login' %}" class="btn btn-light btn-lg btn-rounded px-4">
                        <i class="fas fa-right-to-bracket me-2"></i>Iniciar Sesión
                    </a>
                    <a href="{% url 'auth:registro' %}" class="btn btn-outline-light btn-lg btn-rounded px-4">
                        <i class="fas fa-user-plus me-2"></i>Registrarse
                    </a>
                    {% endif %}
                </div>
            </div>
        </div>
    </div>
    <div class="bg-white" style="height: 24px; clip-path: polygon(0 0, 100% 0, 100% 100%, 0 60%);"></div>
</section>



<!-- Ticker de tasas en movimiento -->
{% if monedas_con_tasas %}
<section class="py-3">
  <div class="container">
    <div class="ticker shadow-soft" role="region" aria-label="Cotizaciones en movimiento">
      <div class="ticker__track">
        <!-- Bloque 1 -->
        {% for item in monedas_con_tasas %}
        <span class="ticker__item">
          <i class="{{ item.moneda.codigo|get_icono_moneda }} text-primary"></i>
          <span class="ticker__label">{{ item.moneda.codigo }}</span>
          <span class="ticker__value">{{ item.tasa.tasa_venta|formatear_guaranies }}</span>
          <span class="text-muted">
            Compra {{ item.tasa.tasa_compra|formatear_guaranies }} · 
            Venta {{ item.tasa.tasa_venta|formatear_guaranies }}
          </span>
        </span>
        {% endfor %}

        <!-- Bloque 2 (duplicado para desplazamiento infinito) -->
        {% for item in monedas_con_tasas %}
        <span class="ticker__item">
          <i class="{{ item.moneda.codigo|get_icono_moneda }} text-primary"></i>
          <span class="ticker__label">{{ item.moneda.codigo }}</span>
          <span class="ticker__value">{{ item.tasa.tasa_venta|formatear_guaranies }}</span>
          <span class="text-muted">
            Compra {{ item.tasa.tasa_compra|formatear_guaranies }} · 
            Venta {{ item.tasa.tasa_venta|formatear_guaranies }}
          </span>
        </span>
        {% endfor %}
      </div>
    </div>
  </div>
  <div class="bg-white" style="height: 16px;"></div>
</section>
{% endif %}

<!-- Cotizaciones y Simulador -->
{% if monedas_con_tasas %}
<section class="py-5">
    <div class="container">
        <div class="row g-4">
            <!-- Cotizaciones - Columna izquierda -->
            <div class="col-12 col-lg-6">
                <div class="mb-4">
                    <h2 class="h3 text-primary mb-2">
                        <i class="fas fa-coins me-2"></i>Cotizaciones
                    </h2>
                    <p class="text-muted mb-0">Moneda base: Guaraní (PYG)</p>
                </div>
                
                <div class="card border-0 shadow-soft overflow-hidden">
                    <div class="card-body p-0">
                        <div class="table-responsive">
                            <table class="table table-hover mb-0">
                                <thead>
                                    <tr class="table-primary">
                                        <th class="border-0 py-3 px-3 fw-bold">
                                            <i class="fas fa-coins me-1 text-primary"></i>Moneda
                                        </th>
                                        <th class="border-0 py-3 px-3 text-center fw-bold">
                                            <i class="fas fa-arrow-down me-1 text-success"></i>Compra
                                        </th>
                                        <th class="border-0 py-3 px-3 text-center fw-bold">
                                            <i class="fas fa-arrow-up me-1 text-danger"></i>Venta
                                        </th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {% for item in monedas_con_tasas %}
                                    <tr class="align-middle hover-row">
                                        <td class="py-3 px-3">
                                            <div class="d-flex align-items-center">
                                                <div class="me-2">
                                                    <div class="bg-primary bg-opacity-10 rounded-circle p-1">
                                                        <i class="{{ item.moneda.codigo|get_icono_moneda }} text-primary fs-6"></i>
                                                    </div>
                                                </div>
                                                <div>
                                                    {% if user.is_authenticated and perms.tasa_cambio.view_tasacambio %}
                                                    <a href="{% url 'tasa_cambio:tasacambio_historial' item.moneda.id %}" 
                                                       class="text-decoration-none">
                                                        <div class="fw-bold text-dark small hover-text-primary">{{ item.moneda.nombre }}</div>
                                                        <small class="text-muted">{{ item.moneda.codigo }}</small>
                                                    </a>
                                                    {% else %}
                                                    <div class="fw-bold text-dark small">{{ item.moneda.nombre }}</div>
                                                    <small class="text-muted">{{ item.moneda.codigo }}</small>
                                                    {% endif %}
                                                </div>
                                            </div>
                                        </td>
                                        <td class="py-3 px-3 text-center">
                                            <div class="d-flex flex-column align-items-center">
                                                <span class="fw-bold text-success fs-6">
                                                    {{ item.tasa.tasa_compra|formatear_guaranies }}
                                                </span>
                                                <small class="text-muted">PYG</small>
                                            </div>
                                        </td>
                                        <td class="py-3 px-3 text-center">
                                            <div class="d-flex flex-column align-items-center">
                                                <span class="fw-bold text-danger fs-6">
                                                    {{ item.tasa.tasa_venta|formatear_guaranies }}
                                                </span>
                                                <small class="text-muted">PYG</small>
                                            </div>
                                        </td>
                                    </tr>
                                    {% endfor %}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Simulador - Columna derecha -->
            <div class="col-12 col-lg-6">
                <div class="mb-4">
                    <h2 class="h3 text-primary mb-2">
                        <i class="fas fa-calculator me-2"></i>Simulador de cambio
                    </h2>
                    <p class="text-muted mb-0">Calcula tu cambio al instante</p>
                </div>
                
                <div class="card sim-card shadow-soft h-100">
                    <div class="card-body p-4">
                        <div class="row g-3 align-items-end mb-4">
                            <div class="col-12 col-md-5">
                                <label class="form-label">De</label>
                                <select id="origen_pub" class="form-select">
                                    <option value="PYG" selected>Guaraní (PYG)</option>
                                </select>
                            </div>
                            <div class="col-12 col-md-2 d-flex align-items-end justify-content-center">
                                <button id="btnToggleDir_pub" type="button" class="btn btn-outline-secondary btn-swap w-100" title="Cambiar dirección" aria-label="Cambiar dirección">
                                    <i class="fas fa-right-left"></i>
                                </button>
                            </div>
                            <div class="col-12 col-md-5">
                                <label class="form-label">A</label>
                                <select id="destino_pub" class="form-select">
                                    {% for m in monedas %}
                                        {% if m.codigo != 'PYG' %}
                                            <option value="{{ m.codigo }}" {% if m.codigo == 'USD' %}selected{% endif %}>{{ m.nombre }} ({{ m.codigo }})</option>
                                        {% endif %}
                                    {% endfor %}
                                </select>
                            </div>
                        </div>

                        <div class="mb-4">
                            <label class="form-label">Monto</label>
                            <input id="monto_pub" type="number" class="form-control" placeholder="0,00" step="any" min="0" value="1000">
                        </div>

                        <div id="resultado_pub" class="p-4 rounded sim-result">
                            <div class="text-muted small mb-1">Resultado</div>
                            <div class="fs-3 fw-bold" id="resultado_valor_pub">—</div>
                            <div class="small text-muted" id="resultado_detalle_pub">Selecciona monedas y monto para simular.</div>
                            <div class="small mt-2" id="resultado_tasas_pub"></div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <div class="row mt-4">
            <div class="col-12">
                <div class="alert alert-info shadow-sm text-center" role="alert">
                    <i class="fas fa-circle-info me-2"></i>
                    <strong>Nota:</strong> Las cotizaciones se actualizan cada hora. Para operaciones específicas, contacta con nuestros agentes.
                </div>
            </div>
        </div>
    </div>
    <div class="bg-white" style="height: 24px; clip-path: polygon(0 0, 100% 40%, 100% 100%, 0 100%);"></div>
</section>
{% else %}
<!-- Mensaje cuando no hay monedas disponibles -->
<section class="py-5">
    <div class="container">
        <div class="text-center">
            <div class="alert alert-warning shadow-sm" role="alert">
                <i class="fas fa-exclamation-triangle me-2"></i>
                <strong>No hay cotizaciones disponibles</strong>
                <p class="mb-0 mt-2">Por favor, contacta con el administrador para configurar las monedas y sus cotizaciones.</p>
            </div>
        </div>
    </div>
</section>
{% endif %}

<!-- Características -->
<section class="py-5 bg-light">
    <div class="container">
        <div class="row g-4">
            <div class="col-12 col-md-4">
                <div class="card h-100">
                    <div class="card-body">
                        <div class="text-primary fs-3 mb-2"><i class="fas fa-shield-halved"></i></div>
                        <h5 class="mb-2">Seguro</h5>
                        <p class="text-muted mb-0">Protección y cumplimiento para cada operación.</p>
                    </div>
                </div>
            </div>
            <div class="col-12 col-md-4">
                <div class="card h-100">
                    <div class="card-body">
                        <div class="text-primary fs-3 mb-2"><i class="fas fa-bolt"></i></div>
                        <h5 class="mb-2">Rápido</h5>
                        <p class="text-muted mb-0">Procesos ágiles y sin fricciones.</p>
                    </div>
                </div>
            </div>
            <div class="col-12 col-md-4">
                <div class="card h-100">
                    <div class="card-body">
                        <div class="text-primary fs-3 mb-2"><i class="fas fa-scale-balanced"></i></div>
                        <h5 class="mb-2">Transparente</h5>
                        <p class="text-muted mb-0">Precios claros y actualizados.</p>
                    </div>
                </div>
            </div>
        </div>
    </div>
</section>

<!-- Llamado a la acción -->
<section class="py-5">
    <div class="container">
        <div class="d-flex flex-column flex-md-row align-items-center justify-content-between p-4 p-md-5 bg-white rounded-3 shadow-soft">
            <div class="mb-3 mb-md-0">
                <h4 class="mb-1">¿Listo para comenzar?</h4>
                <p class="text-muted mb-0">Crea tu cuenta o inicia sesión para operar.</p>
            </div>
            <div class="d-flex gap-2">
                {% if user.is_authenticated %}
                <a href="{% url 'auth:dashboard' %}" class="btn btn-primary btn-rounded px-4">
                    <i class="fas fa-gauge-high me-2"></i>Ir al Dashboard
                </a>
                {% else %}
                <a href="{% url 'auth:login' %}" class="btn btn-primary btn-rounded px-4">
                    <i class="fas fa-right-to-bracket me-2"></i>Iniciar Sesión
                </a>
                <a href="{% url 'auth:registro' %}" class="btn btn-outline-primary btn-rounded px-4">
                    <i class="fas fa-user-plus me-2"></i>Registrarse
                </a>
                {% endif %}
            </div>
        </div>
    </div>
</section>
{% endblock %}

{% block extra_js %}
<script>
  (function() {
    const $monto = document.getElementById('monto_pub');
    const $origen = document.getElementById('origen_pub');
    const $destino = document.getElementById('destino_pub');
    const $btnToggle = document.getElementById('btnToggleDir_pub');
    const $resValor = document.getElementById('resultado_valor_pub');
    const $resDetalle = document.getElementById('resultado_detalle_pub');
    const $resTasas = document.getElementById('resultado_tasas_pub');

    const MONEDAS = [
      {% for m in monedas %}
        { codigo: '{{ m.codigo }}', nombre: '{{ m.nombre|escapejs }}' }{% if not forloop.last %},{% endif %}
      {% endfor %}
    ];
    
    const MONEDAS_FILTRADAS = MONEDAS.filter(m => m.codigo !== 'PYG');

    function setOptions(el, options, selected) {
      el.innerHTML = options.map(o => `<option value="${o.codigo}" ${o.codigo===selected?'selected':''}>${o.nombre} (${o.codigo})</option>`).join('');
    }

    let monedaToPYG = false; // false: PYG -> Moneda (default), true: Moneda -> PYG

    function applyDirection(preserveCode) {
      if (monedaToPYG) {
        const prefer = preserveCode || 'USD';
        setOptions($origen, MONEDAS_FILTRADAS, prefer);
        $origen.disabled = false;
        $destino.innerHTML = '<option value="PYG" selected>Guaraní (PYG)</option>';
        $destino.disabled = true;
      } else {
        $origen.innerHTML = '<option value="PYG" selected>Guaraní (PYG)</option>';
        $origen.disabled = true;
        const prefer = preserveCode || 'USD';
        const sel = MONEDAS_FILTRADAS.find(m => m.codigo === prefer) ? prefer : (MONEDAS_FILTRADAS[0]?.codigo || '');
        setOptions($destino, MONEDAS_FILTRADAS, sel);
        $destino.disabled = false;
      }
    }

    function getCurrentNonPYG() {
      if (monedaToPYG) return $origen.value;
      return $destino.value;
    }

    function formatDisplayWithDots(str) {
      if (!str) return str;
      const m = String(str).match(/^(\D*)([-\d.,]+)(.*)$/);
      if (!m) return str;
      const prefix = m[1] || '';
      const number = m[2] || '';
      const suffix = m[3] || '';
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
      const neg = intPart.startsWith('-');
      const intDigits = intPart.replace(/[^\d]/g, '');
      const grouped = intDigits.replace(/\B(?=(\d{3})+(?!\d))/g, '.');
      const intFinal = neg ? '-' + grouped : grouped;
      const numFinal = decPart ? `${intFinal}${sep}${decPart}` : intFinal;
      return `${prefix}${numFinal}${suffix}`;
    }

    function simulate() {
      const monto = $monto.value;
      const origen = $origen.value;
      const destino = $destino.value;
      if (!monto || !origen || !destino) return;
      fetch(`{% url 'tasa_cambio:simular_cambio_api' %}?monto=${encodeURIComponent(monto)}&origen=${encodeURIComponent(origen)}&destino=${encodeURIComponent(destino)}`)
        .then(r => r.json())
        .then(data => {
          if (!data.success) {
            $resValor.textContent = '—';
            $resDetalle.textContent = data.message || 'Error en la simulación.';
            $resTasas.textContent = '';
            return;
          }
          const d = data.data;
          $resValor.textContent = formatDisplayWithDots(d.resultado_formateado);
          $resDetalle.textContent = d.detalle;
          const t1 = d.tasa_origen ? `${d.tasa_origen.moneda} (${d.tasa_origen.tipo}): ${d.tasa_origen.valor}` : null;
          const t2 = d.tasa_destino ? `${d.tasa_destino.moneda} (${d.tasa_destino.tipo}): ${d.tasa_destino.valor}` : null;
          const parts = [t1, t2].filter(Boolean);
          $resTasas.textContent = parts.length ? `Cotizaciones usadas: ${parts.join(' · ')}` : '';
        })
        .catch(() => {
          $resValor.textContent = '—';
          $resDetalle.textContent = 'No se pudo simular.';
          $resTasas.textContent = '';
        });
    }

    $monto.addEventListener('input', simulate);
    $origen.addEventListener('change', simulate);
    $destino.addEventListener('change', simulate);
    $btnToggle.addEventListener('click', () => {
      const keep = getCurrentNonPYG();
      monedaToPYG = !monedaToPYG;
      applyDirection(keep);
      simulate();
    });

    applyDirection();
    simulate();
  })();
</script>
{% endblock %}

```

¡Perfecto! He implementado los enlaces al historial de cada moneda con las siguientes características:

## Funcionalidad implementada:

### **Enlaces condicionales**:
- **Solo usuarios autenticados** pueden ver los enlaces
- **Solo usuarios con permiso** `tasa_cambio.view_tasacambio` pueden acceder
- **Usuarios sin permisos** ven el texto normal sin enlace

### **Diseño visual**:
- **Enlaces sin subrayado** para mantener el diseño limpio
- **Efecto hover azul** que cambia el color del texto al pasar el mouse
- **Transición suave** para mejor experiencia de usuario
- **Mantiene el diseño original** cuando no hay permisos

### **Navegación**:
- **URL correcta**: `tasa_cambio:tasacambio_historial` con el ID de la moneda
- **Acceso directo** al historial de cada moneda específica
- **Integración perfecta** con el sistema de permisos existente

### **Comportamiento**:
- **Usuarios autenticados con permisos**: Ven enlaces clickeables al historial
- **Usuarios sin permisos**: Ven texto normal sin funcionalidad de enlace
- **Usuarios no autenticados**: Ven texto normal (no pueden acceder al historial)

Los usuarios ahora pueden hacer clic en el nombre de cualquier moneda para acceder directamente a su historial de cotizaciones, siempre que tengan los permisos necesarios. El diseño se mantiene consistente y profesional.

---

**User**

que el click aplique al card completo no solamente al label

---

**Cursor**

Perfecto! Voy a hacer que todo el card de la moneda sea clickeable, no solo el texto. Esto mejorará significativamente la experiencia de usuario.


```django-html
{% extends "base.html" %}
{% load moneda_extras %}

{% block title %}Global Exchange - Casa de Cambios{% endblock %}

{% block extra_css %}
<style>
/* Ticker styles scoped to welcome */
.ticker { position: relative; overflow: hidden; background:#fff; border-radius:.75rem; }
.ticker__track {
    display:flex; align-items:center; gap:2rem; white-space:nowrap;
    animation: ticker-scroll 35s linear infinite;
    padding: .75rem 1rem;
}
.ticker:hover .ticker__track { animation-play-state: paused; }
.ticker__item { display:flex; align-items:center; gap:.5rem; color:#0f172a; }
.ticker__label { color:#6c757d; font-size:.9rem; }
.ticker__value { font-weight:700; color:#198754; }
@keyframes ticker-scroll {
  0% { transform: translateX(0); }
  100% { transform: translateX(-50%); }
}
@media (prefers-reduced-motion: reduce) { .ticker__track { animation:none; } }

/* Simulator styles */
.sim-card { border: none; }
.sim-header-badge { background: rgba(13,110,253,.08); color:#0d6efd; }
.sim-result { background: linear-gradient(180deg, #f8fafc 0%, #ffffff 100%); border:1px solid rgba(0,0,0,.06); }
.btn-swap { border-radius: 999px; height: 52px; display:flex; align-items:center; justify-content:center; font-size: 1.1rem; }
.btn-swap i { transition: transform .2s ease; }
.btn-swap:hover i { transform: rotate(180deg); }

/* Cotizaciones styles */
.hover-row { transition: all 0.2s ease; }
.hover-row:hover { background-color: rgba(13, 110, 253, 0.05) !important; transform: scale(1.01); }
.hover-text-primary:hover { color: #0d6efd !important; }
</style>
{% endblock %}

{% block main_container_class %}container-fluid p-0{% endblock %}

{% block content %}
<!-- Hero principal -->
<section class="bg-primary text-white py-5 shadow-soft" style="background: linear-gradient(135deg, rgba(13,110,253,1) 0%, rgba(2,62,138,1) 100%);">
    <div class="container py-4">
        <div class="row align-items-center g-4">
            <div class="col-12 text-center">
                <h1 class="display-5 fw-bold mb-2">Global Exchange</h1>
                <p class="lead mb-4">Tu casa de cambios de confianza</p>
                <div class="d-flex justify-content-center gap-2 flex-wrap">
                    {% if user.is_authenticated %}
                    <a href="{% url 'auth:dashboard' %}" class="btn btn-light btn-lg btn-rounded px-4">
                        <i class="fas fa-gauge-high me-2"></i>Ir al Dashboard
                    </a>
                    <a href="{% url 'auth:logout' %}" class="btn btn-outline-light btn-lg btn-rounded px-4">
                        <i class="fas fa-right-from-bracket me-2"></i>Cerrar Sesión
                    </a>
                    {% else %}
                    <a href="{% url 'auth:login' %}" class="btn btn-light btn-lg btn-rounded px-4">
                        <i class="fas fa-right-to-bracket me-2"></i>Iniciar Sesión
                    </a>
                    <a href="{% url 'auth:registro' %}" class="btn btn-outline-light btn-lg btn-rounded px-4">
                        <i class="fas fa-user-plus me-2"></i>Registrarse
                    </a>
                    {% endif %}
                </div>
            </div>
        </div>
    </div>
    <div class="bg-white" style="height: 24px; clip-path: polygon(0 0, 100% 0, 100% 100%, 0 60%);"></div>
</section>



<!-- Ticker de tasas en movimiento -->
{% if monedas_con_tasas %}
<section class="py-3">
  <div class="container">
    <div class="ticker shadow-soft" role="region" aria-label="Cotizaciones en movimiento">
      <div class="ticker__track">
        <!-- Bloque 1 -->
        {% for item in monedas_con_tasas %}
        <span class="ticker__item">
          <i class="{{ item.moneda.codigo|get_icono_moneda }} text-primary"></i>
          <span class="ticker__label">{{ item.moneda.codigo }}</span>
          <span class="ticker__value">{{ item.tasa.tasa_venta|formatear_guaranies }}</span>
          <span class="text-muted">
            Compra {{ item.tasa.tasa_compra|formatear_guaranies }} · 
            Venta {{ item.tasa.tasa_venta|formatear_guaranies }}
          </span>
        </span>
        {% endfor %}

        <!-- Bloque 2 (duplicado para desplazamiento infinito) -->
        {% for item in monedas_con_tasas %}
        <span class="ticker__item">
          <i class="{{ item.moneda.codigo|get_icono_moneda }} text-primary"></i>
          <span class="ticker__label">{{ item.moneda.codigo }}</span>
          <span class="ticker__value">{{ item.tasa.tasa_venta|formatear_guaranies }}</span>
          <span class="text-muted">
            Compra {{ item.tasa.tasa_compra|formatear_guaranies }} · 
            Venta {{ item.tasa.tasa_venta|formatear_guaranies }}
          </span>
        </span>
        {% endfor %}
      </div>
    </div>
  </div>
  <div class="bg-white" style="height: 16px;"></div>
</section>
{% endif %}

<!-- Cotizaciones y Simulador -->
{% if monedas_con_tasas %}
<section class="py-5">
    <div class="container">
        <div class="row g-4">
            <!-- Cotizaciones - Columna izquierda -->
            <div class="col-12 col-lg-6">
                <div class="mb-4">
                    <h2 class="h3 text-primary mb-2">
                        <i class="fas fa-coins me-2"></i>Cotizaciones
                    </h2>
                    <p class="text-muted mb-0">Moneda base: Guaraní (PYG)</p>
                </div>
                
                <div class="card border-0 shadow-soft overflow-hidden">
                    <div class="card-body p-0">
                        <div class="table-responsive">
                            <table class="table table-hover mb-0">
                                <thead>
                                    <tr class="table-primary">
                                        <th class="border-0 py-3 px-3 fw-bold">
                                            <i class="fas fa-coins me-1 text-primary"></i>Moneda
                                        </th>
                                        <th class="border-0 py-3 px-3 text-center fw-bold">
                                            <i class="fas fa-arrow-down me-1 text-success"></i>Compra
                                        </th>
                                        <th class="border-0 py-3 px-3 text-center fw-bold">
                                            <i class="fas fa-arrow-up me-1 text-danger"></i>Venta
                                        </th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {% for item in monedas_con_tasas %}
                                    <tr class="align-middle hover-row">
                                        {% if user.is_authenticated and perms.tasa_cambio.view_tasacambio %}
                                        <td class="py-3 px-3 clickable-row" onclick="window.location.href='{% url 'tasa_cambio:tasacambio_historial' item.moneda.id %}'" style="cursor: pointer;">
                                        {% else %}
                                        <td class="py-3 px-3">
                                        {% endif %}
                                            <div class="d-flex align-items-center">
                                                <div class="me-2">
                                                    <div class="bg-primary bg-opacity-10 rounded-circle p-1">
                                                        <i class="{{ item.moneda.codigo|get_icono_moneda }} text-primary fs-6"></i>
                                                    </div>
                                                </div>
                                                <div>
                                                    <div class="fw-bold text-dark small">{{ item.moneda.nombre }}</div>
                                                    <small class="text-muted">{{ item.moneda.codigo }}</small>
                                                </div>
                                            </div>
                                        </td>
                                        <td class="py-3 px-3 text-center">
                                            <div class="d-flex flex-column align-items-center">
                                                <span class="fw-bold text-success fs-6">
                                                    {{ item.tasa.tasa_compra|formatear_guaranies }}
                                                </span>
                                                <small class="text-muted">PYG</small>
                                            </div>
                                        </td>
                                        <td class="py-3 px-3 text-center">
                                            <div class="d-flex flex-column align-items-center">
                                                <span class="fw-bold text-danger fs-6">
                                                    {{ item.tasa.tasa_venta|formatear_guaranies }}
                                                </span>
                                                <small class="text-muted">PYG</small>
                                            </div>
                                        </td>
                                    </tr>
                                    {% endfor %}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Simulador - Columna derecha -->
            <div class="col-12 col-lg-6">
                <div class="mb-4">
                    <h2 class="h3 text-primary mb-2">
                        <i class="fas fa-calculator me-2"></i>Simulador de cambio
                    </h2>
                    <p class="text-muted mb-0">Calcula tu cambio al instante</p>
                </div>
                
                <div class="card sim-card shadow-soft h-100">
                    <div class="card-body p-4">
                        <div class="row g-3 align-items-end mb-4">
                            <div class="col-12 col-md-5">
                                <label class="form-label">De</label>
                                <select id="origen_pub" class="form-select">
                                    <option value="PYG" selected>Guaraní (PYG)</option>
                                </select>
                            </div>
                            <div class="col-12 col-md-2 d-flex align-items-end justify-content-center">
                                <button id="btnToggleDir_pub" type="button" class="btn btn-outline-secondary btn-swap w-100" title="Cambiar dirección" aria-label="Cambiar dirección">
                                    <i class="fas fa-right-left"></i>
                                </button>
                            </div>
                            <div class="col-12 col-md-5">
                                <label class="form-label">A</label>
                                <select id="destino_pub" class="form-select">
                                    {% for m in monedas %}
                                        {% if m.codigo != 'PYG' %}
                                            <option value="{{ m.codigo }}" {% if m.codigo == 'USD' %}selected{% endif %}>{{ m.nombre }} ({{ m.codigo }})</option>
                                        {% endif %}
                                    {% endfor %}
                                </select>
                            </div>
                        </div>

                        <div class="mb-4">
                            <label class="form-label">Monto</label>
                            <input id="monto_pub" type="number" class="form-control" placeholder="0,00" step="any" min="0" value="1000">
                        </div>

                        <div id="resultado_pub" class="p-4 rounded sim-result">
                            <div class="text-muted small mb-1">Resultado</div>
                            <div class="fs-3 fw-bold" id="resultado_valor_pub">—</div>
                            <div class="small text-muted" id="resultado_detalle_pub">Selecciona monedas y monto para simular.</div>
                            <div class="small mt-2" id="resultado_tasas_pub"></div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <div class="row mt-4">
            <div class="col-12">
                <div class="alert alert-info shadow-sm text-center" role="alert">
                    <i class="fas fa-circle-info me-2"></i>
                    <strong>Nota:</strong> Las cotizaciones se actualizan cada hora. Para operaciones específicas, contacta con nuestros agentes.
                </div>
            </div>
        </div>
    </div>
    <div class="bg-white" style="height: 24px; clip-path: polygon(0 0, 100% 40%, 100% 100%, 0 100%);"></div>
</section>
{% else %}
<!-- Mensaje cuando no hay monedas disponibles -->
<section class="py-5">
    <div class="container">
        <div class="text-center">
            <div class="alert alert-warning shadow-sm" role="alert">
                <i class="fas fa-exclamation-triangle me-2"></i>
                <strong>No hay cotizaciones disponibles</strong>
                <p class="mb-0 mt-2">Por favor, contacta con el administrador para configurar las monedas y sus cotizaciones.</p>
            </div>
        </div>
    </div>
</section>
{% endif %}

<!-- Características -->
<section class="py-5 bg-light">
    <div class="container">
        <div class="row g-4">
            <div class="col-12 col-md-4">
                <div class="card h-100">
                    <div class="card-body">
                        <div class="text-primary fs-3 mb-2"><i class="fas fa-shield-halved"></i></div>
                        <h5 class="mb-2">Seguro</h5>
                        <p class="text-muted mb-0">Protección y cumplimiento para cada operación.</p>
                    </div>
                </div>
            </div>
            <div class="col-12 col-md-4">
                <div class="card h-100">
                    <div class="card-body">
                        <div class="text-primary fs-3 mb-2"><i class="fas fa-bolt"></i></div>
                        <h5 class="mb-2">Rápido</h5>
                        <p class="text-muted mb-0">Procesos ágiles y sin fricciones.</p>
                    </div>
                </div>
            </div>
            <div class="col-12 col-md-4">
                <div class="card h-100">
                    <div class="card-body">
                        <div class="text-primary fs-3 mb-2"><i class="fas fa-scale-balanced"></i></div>
                        <h5 class="mb-2">Transparente</h5>
                        <p class="text-muted mb-0">Precios claros y actualizados.</p>
                    </div>
                </div>
            </div>
        </div>
    </div>
</section>

<!-- Llamado a la acción -->
<section class="py-5">
    <div class="container">
        <div class="d-flex flex-column flex-md-row align-items-center justify-content-between p-4 p-md-5 bg-white rounded-3 shadow-soft">
            <div class="mb-3 mb-md-0">
                <h4 class="mb-1">¿Listo para comenzar?</h4>
                <p class="text-muted mb-0">Crea tu cuenta o inicia sesión para operar.</p>
            </div>
            <div class="d-flex gap-2">
                {% if user.is_authenticated %}
                <a href="{% url 'auth:dashboard' %}" class="btn btn-primary btn-rounded px-4">
                    <i class="fas fa-gauge-high me-2"></i>Ir al Dashboard
                </a>
                {% else %}
                <a href="{% url 'auth:login' %}" class="btn btn-primary btn-rounded px-4">
                    <i class="fas fa-right-to-bracket me-2"></i>Iniciar Sesión
                </a>
                <a href="{% url 'auth:registro' %}" class="btn btn-outline-primary btn-rounded px-4">
                    <i class="fas fa-user-plus me-2"></i>Registrarse
                </a>
                {% endif %}
            </div>
        </div>
    </div>
</section>
{% endblock %}

{% block extra_js %}
<script>
  (function() {
    const $monto = document.getElementById('monto_pub');
    const $origen = document.getElementById('origen_pub');
    const $destino = document.getElementById('destino_pub');
    const $btnToggle = document.getElementById('btnToggleDir_pub');
    const $resValor = document.getElementById('resultado_valor_pub');
    const $resDetalle = document.getElementById('resultado_detalle_pub');
    const $resTasas = document.getElementById('resultado_tasas_pub');

    const MONEDAS = [
      {% for m in monedas %}
        { codigo: '{{ m.codigo }}', nombre: '{{ m.nombre|escapejs }}' }{% if not forloop.last %},{% endif %}
      {% endfor %}
    ];
    
    const MONEDAS_FILTRADAS = MONEDAS.filter(m => m.codigo !== 'PYG');

    function setOptions(el, options, selected) {
      el.innerHTML = options.map(o => `<option value="${o.codigo}" ${o.codigo===selected?'selected':''}>${o.nombre} (${o.codigo})</option>`).join('');
    }

    let monedaToPYG = false; // false: PYG -> Moneda (default), true: Moneda -> PYG

    function applyDirection(preserveCode) {
      if (monedaToPYG) {
        const prefer = preserveCode || 'USD';
        setOptions($origen, MONEDAS_FILTRADAS, prefer);
        $origen.disabled = false;
        $destino.innerHTML = '<option value="PYG" selected>Guaraní (PYG)</option>';
        $destino.disabled = true;
      } else {
        $origen.innerHTML = '<option value="PYG" selected>Guaraní (PYG)</option>';
        $origen.disabled = true;
        const prefer = preserveCode || 'USD';
        const sel = MONEDAS_FILTRADAS.find(m => m.codigo === prefer) ? prefer : (MONEDAS_FILTRADAS[0]?.codigo || '');
        setOptions($destino, MONEDAS_FILTRADAS, sel);
        $destino.disabled = false;
      }
    }

    function getCurrentNonPYG() {
      if (monedaToPYG) return $origen.value;
      return $destino.value;
    }

    function formatDisplayWithDots(str) {
      if (!str) return str;
      const m = String(str).match(/^(\D*)([-\d.,]+)(.*)$/);
      if (!m) return str;
      const prefix = m[1] || '';
      const number = m[2] || '';
      const suffix = m[3] || '';
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
      const neg = intPart.startsWith('-');
      const intDigits = intPart.replace(/[^\d]/g, '');
      const grouped = intDigits.replace(/\B(?=(\d{3})+(?!\d))/g, '.');
      const intFinal = neg ? '-' + grouped : grouped;
      const numFinal = decPart ? `${intFinal}${sep}${decPart}` : intFinal;
      return `${prefix}${numFinal}${suffix}`;
    }

    function simulate() {
      const monto = $monto.value;
      const origen = $origen.value;
      const destino = $destino.value;
      if (!monto || !origen || !destino) return;
      fetch(`{% url 'tasa_cambio:simular_cambio_api' %}?monto=${encodeURIComponent(monto)}&origen=${encodeURIComponent(origen)}&destino=${encodeURIComponent(destino)}`)
        .then(r => r.json())
        .then(data => {
          if (!data.success) {
            $resValor.textContent = '—';
            $resDetalle.textContent = data.message || 'Error en la simulación.';
            $resTasas.textContent = '';
            return;
          }
          const d = data.data;
          $resValor.textContent = formatDisplayWithDots(d.resultado_formateado);
          $resDetalle.textContent = d.detalle;
          const t1 = d.tasa_origen ? `${d.tasa_origen.moneda} (${d.tasa_origen.tipo}): ${d.tasa_origen.valor}` : null;
          const t2 = d.tasa_destino ? `${d.tasa_destino.moneda} (${d.tasa_destino.tipo}): ${d.tasa_destino.valor}` : null;
          const parts = [t1, t2].filter(Boolean);
          $resTasas.textContent = parts.length ? `Cotizaciones usadas: ${parts.join(' · ')}` : '';
        })
        .catch(() => {
          $resValor.textContent = '—';
          $resDetalle.textContent = 'No se pudo simular.';
          $resTasas.textContent = '';
        });
    }

    $monto.addEventListener('input', simulate);
    $origen.addEventListener('change', simulate);
    $destino.addEventListener('change', simulate);
    $btnToggle.addEventListener('click', () => {
      const keep = getCurrentNonPYG();
      monedaToPYG = !monedaToPYG;
      applyDirection(keep);
      simulate();
    });

    applyDirection();
    simulate();
  })();
</script>
{% endblock %}

```

Ahora voy a agregar los estilos CSS para mejorar la experiencia visual del área clickeable:


```django-html
{% extends "base.html" %}
{% load moneda_extras %}

{% block title %}Global Exchange - Casa de Cambios{% endblock %}

{% block extra_css %}
<style>
/* Ticker styles scoped to welcome */
.ticker { position: relative; overflow: hidden; background:#fff; border-radius:.75rem; }
.ticker__track {
    display:flex; align-items:center; gap:2rem; white-space:nowrap;
    animation: ticker-scroll 35s linear infinite;
    padding: .75rem 1rem;
}
.ticker:hover .ticker__track { animation-play-state: paused; }
.ticker__item { display:flex; align-items:center; gap:.5rem; color:#0f172a; }
.ticker__label { color:#6c757d; font-size:.9rem; }
.ticker__value { font-weight:700; color:#198754; }
@keyframes ticker-scroll {
  0% { transform: translateX(0); }
  100% { transform: translateX(-50%); }
}
@media (prefers-reduced-motion: reduce) { .ticker__track { animation:none; } }

/* Simulator styles */
.sim-card { border: none; }
.sim-header-badge { background: rgba(13,110,253,.08); color:#0d6efd; }
.sim-result { background: linear-gradient(180deg, #f8fafc 0%, #ffffff 100%); border:1px solid rgba(0,0,0,.06); }
.btn-swap { border-radius: 999px; height: 52px; display:flex; align-items:center; justify-content:center; font-size: 1.1rem; }
.btn-swap i { transition: transform .2s ease; }
.btn-swap:hover i { transform: rotate(180deg); }

/* Cotizaciones styles */
.hover-row { transition: all 0.2s ease; }
.hover-row:hover { background-color: rgba(13, 110, 253, 0.05) !important; transform: scale(1.01); }
.clickable-row { transition: all 0.2s ease; }
.clickable-row:hover { background-color: rgba(13, 110, 253, 0.1) !important; }
</style>
{% endblock %}

{% block main_container_class %}container-fluid p-0{% endblock %}

{% block content %}
<!-- Hero principal -->
<section class="bg-primary text-white py-5 shadow-soft" style="background: linear-gradient(135deg, rgba(13,110,253,1) 0%, rgba(2,62,138,1) 100%);">
    <div class="container py-4">
        <div class="row align-items-center g-4">
            <div class="col-12 text-center">
                <h1 class="display-5 fw-bold mb-2">Global Exchange</h1>
                <p class="lead mb-4">Tu casa de cambios de confianza</p>
                <div class="d-flex justify-content-center gap-2 flex-wrap">
                    {% if user.is_authenticated %}
                    <a href="{% url 'auth:dashboard' %}" class="btn btn-light btn-lg btn-rounded px-4">
                        <i class="fas fa-gauge-high me-2"></i>Ir al Dashboard
                    </a>
                    <a href="{% url 'auth:logout' %}" class="btn btn-outline-light btn-lg btn-rounded px-4">
                        <i class="fas fa-right-from-bracket me-2"></i>Cerrar Sesión
                    </a>
                    {% else %}
                    <a href="{% url 'auth:login' %}" class="btn btn-light btn-lg btn-rounded px-4">
                        <i class="fas fa-right-to-bracket me-2"></i>Iniciar Sesión
                    </a>
                    <a href="{% url 'auth:registro' %}" class="btn btn-outline-light btn-lg btn-rounded px-4">
                        <i class="fas fa-user-plus me-2"></i>Registrarse
                    </a>
                    {% endif %}
                </div>
            </div>
        </div>
    </div>
    <div class="bg-white" style="height: 24px; clip-path: polygon(0 0, 100% 0, 100% 100%, 0 60%);"></div>
</section>



<!-- Ticker de tasas en movimiento -->
{% if monedas_con_tasas %}
<section class="py-3">
  <div class="container">
    <div class="ticker shadow-soft" role="region" aria-label="Cotizaciones en movimiento">
      <div class="ticker__track">
        <!-- Bloque 1 -->
        {% for item in monedas_con_tasas %}
        <span class="ticker__item">
          <i class="{{ item.moneda.codigo|get_icono_moneda }} text-primary"></i>
          <span class="ticker__label">{{ item.moneda.codigo }}</span>
          <span class="ticker__value">{{ item.tasa.tasa_venta|formatear_guaranies }}</span>
          <span class="text-muted">
            Compra {{ item.tasa.tasa_compra|formatear_guaranies }} · 
            Venta {{ item.tasa.tasa_venta|formatear_guaranies }}
          </span>
        </span>
        {% endfor %}

        <!-- Bloque 2 (duplicado para desplazamiento infinito) -->
        {% for item in monedas_con_tasas %}
        <span class="ticker__item">
          <i class="{{ item.moneda.codigo|get_icono_moneda }} text-primary"></i>
          <span class="ticker__label">{{ item.moneda.codigo }}</span>
          <span class="ticker__value">{{ item.tasa.tasa_venta|formatear_guaranies }}</span>
          <span class="text-muted">
            Compra {{ item.tasa.tasa_compra|formatear_guaranies }} · 
            Venta {{ item.tasa.tasa_venta|formatear_guaranies }}
          </span>
        </span>
        {% endfor %}
      </div>
    </div>
  </div>
  <div class="bg-white" style="height: 16px;"></div>
</section>
{% endif %}

<!-- Cotizaciones y Simulador -->
{% if monedas_con_tasas %}
<section class="py-5">
    <div class="container">
        <div class="row g-4">
            <!-- Cotizaciones - Columna izquierda -->
            <div class="col-12 col-lg-6">
                <div class="mb-4">
                    <h2 class="h3 text-primary mb-2">
                        <i class="fas fa-coins me-2"></i>Cotizaciones
                    </h2>
                    <p class="text-muted mb-0">Moneda base: Guaraní (PYG)</p>
                </div>
                
                <div class="card border-0 shadow-soft overflow-hidden">
                    <div class="card-body p-0">
                        <div class="table-responsive">
                            <table class="table table-hover mb-0">
                                <thead>
                                    <tr class="table-primary">
                                        <th class="border-0 py-3 px-3 fw-bold">
                                            <i class="fas fa-coins me-1 text-primary"></i>Moneda
                                        </th>
                                        <th class="border-0 py-3 px-3 text-center fw-bold">
                                            <i class="fas fa-arrow-down me-1 text-success"></i>Compra
                                        </th>
                                        <th class="border-0 py-3 px-3 text-center fw-bold">
                                            <i class="fas fa-arrow-up me-1 text-danger"></i>Venta
                                        </th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {% for item in monedas_con_tasas %}
                                    <tr class="align-middle hover-row">
                                        {% if user.is_authenticated and perms.tasa_cambio.view_tasacambio %}
                                        <td class="py-3 px-3 clickable-row" onclick="window.location.href='{% url 'tasa_cambio:tasacambio_historial' item.moneda.id %}'" style="cursor: pointer;">
                                        {% else %}
                                        <td class="py-3 px-3">
                                        {% endif %}
                                            <div class="d-flex align-items-center">
                                                <div class="me-2">
                                                    <div class="bg-primary bg-opacity-10 rounded-circle p-1">
                                                        <i class="{{ item.moneda.codigo|get_icono_moneda }} text-primary fs-6"></i>
                                                    </div>
                                                </div>
                                                <div>
                                                    <div class="fw-bold text-dark small">{{ item.moneda.nombre }}</div>
                                                    <small class="text-muted">{{ item.moneda.codigo }}</small>
                                                </div>
                                            </div>
                                        </td>
                                        <td class="py-3 px-3 text-center">
                                            <div class="d-flex flex-column align-items-center">
                                                <span class="fw-bold text-success fs-6">
                                                    {{ item.tasa.tasa_compra|formatear_guaranies }}
                                                </span>
                                                <small class="text-muted">PYG</small>
                                            </div>
                                        </td>
                                        <td class="py-3 px-3 text-center">
                                            <div class="d-flex flex-column align-items-center">
                                                <span class="fw-bold text-danger fs-6">
                                                    {{ item.tasa.tasa_venta|formatear_guaranies }}
                                                </span>
                                                <small class="text-muted">PYG</small>
                                            </div>
                                        </td>
                                    </tr>
                                    {% endfor %}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Simulador - Columna derecha -->
            <div class="col-12 col-lg-6">
                <div class="mb-4">
                    <h2 class="h3 text-primary mb-2">
                        <i class="fas fa-calculator me-2"></i>Simulador de cambio
                    </h2>
                    <p class="text-muted mb-0">Calcula tu cambio al instante</p>
                </div>
                
                <div class="card sim-card shadow-soft h-100">
                    <div class="card-body p-4">
                        <div class="row g-3 align-items-end mb-4">
                            <div class="col-12 col-md-5">
                                <label class="form-label">De</label>
                                <select id="origen_pub" class="form-select">
                                    <option value="PYG" selected>Guaraní (PYG)</option>
                                </select>
                            </div>
                            <div class="col-12 col-md-2 d-flex align-items-end justify-content-center">
                                <button id="btnToggleDir_pub" type="button" class="btn btn-outline-secondary btn-swap w-100" title="Cambiar dirección" aria-label="Cambiar dirección">
                                    <i class="fas fa-right-left"></i>
                                </button>
                            </div>
                            <div class="col-12 col-md-5">
                                <label class="form-label">A</label>
                                <select id="destino_pub" class="form-select">
                                    {% for m in monedas %}
                                        {% if m.codigo != 'PYG' %}
                                            <option value="{{ m.codigo }}" {% if m.codigo == 'USD' %}selected{% endif %}>{{ m.nombre }} ({{ m.codigo }})</option>
                                        {% endif %}
                                    {% endfor %}
                                </select>
                            </div>
                        </div>

                        <div class="mb-4">
                            <label class="form-label">Monto</label>
                            <input id="monto_pub" type="number" class="form-control" placeholder="0,00" step="any" min="0" value="1000">
                        </div>

                        <div id="resultado_pub" class="p-4 rounded sim-result">
                            <div class="text-muted small mb-1">Resultado</div>
                            <div class="fs-3 fw-bold" id="resultado_valor_pub">—</div>
                            <div class="small text-muted" id="resultado_detalle_pub">Selecciona monedas y monto para simular.</div>
                            <div class="small mt-2" id="resultado_tasas_pub"></div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <div class="row mt-4">
            <div class="col-12">
                <div class="alert alert-info shadow-sm text-center" role="alert">
                    <i class="fas fa-circle-info me-2"></i>
                    <strong>Nota:</strong> Las cotizaciones se actualizan cada hora. Para operaciones específicas, contacta con nuestros agentes.
                </div>
            </div>
        </div>
    </div>
    <div class="bg-white" style="height: 24px; clip-path: polygon(0 0, 100% 40%, 100% 100%, 0 100%);"></div>
</section>
{% else %}
<!-- Mensaje cuando no hay monedas disponibles -->
<section class="py-5">
    <div class="container">
        <div class="text-center">
            <div class="alert alert-warning shadow-sm" role="alert">
                <i class="fas fa-exclamation-triangle me-2"></i>
                <strong>No hay cotizaciones disponibles</strong>
                <p class="mb-0 mt-2">Por favor, contacta con el administrador para configurar las monedas y sus cotizaciones.</p>
            </div>
        </div>
    </div>
</section>
{% endif %}

<!-- Características -->
<section class="py-5 bg-light">
    <div class="container">
        <div class="row g-4">
            <div class="col-12 col-md-4">
                <div class="card h-100">
                    <div class="card-body">
                        <div class="text-primary fs-3 mb-2"><i class="fas fa-shield-halved"></i></div>
                        <h5 class="mb-2">Seguro</h5>
                        <p class="text-muted mb-0">Protección y cumplimiento para cada operación.</p>
                    </div>
                </div>
            </div>
            <div class="col-12 col-md-4">
                <div class="card h-100">
                    <div class="card-body">
                        <div class="text-primary fs-3 mb-2"><i class="fas fa-bolt"></i></div>
                        <h5 class="mb-2">Rápido</h5>
                        <p class="text-muted mb-0">Procesos ágiles y sin fricciones.</p>
                    </div>
                </div>
            </div>
            <div class="col-12 col-md-4">
                <div class="card h-100">
                    <div class="card-body">
                        <div class="text-primary fs-3 mb-2"><i class="fas fa-scale-balanced"></i></div>
                        <h5 class="mb-2">Transparente</h5>
                        <p class="text-muted mb-0">Precios claros y actualizados.</p>
                    </div>
                </div>
            </div>
        </div>
    </div>
</section>

<!-- Llamado a la acción -->
<section class="py-5">
    <div class="container">
        <div class="d-flex flex-column flex-md-row align-items-center justify-content-between p-4 p-md-5 bg-white rounded-3 shadow-soft">
            <div class="mb-3 mb-md-0">
                <h4 class="mb-1">¿Listo para comenzar?</h4>
                <p class="text-muted mb-0">Crea tu cuenta o inicia sesión para operar.</p>
            </div>
            <div class="d-flex gap-2">
                {% if user.is_authenticated %}
                <a href="{% url 'auth:dashboard' %}" class="btn btn-primary btn-rounded px-4">
                    <i class="fas fa-gauge-high me-2"></i>Ir al Dashboard
                </a>
                {% else %}
                <a href="{% url 'auth:login' %}" class="btn btn-primary btn-rounded px-4">
                    <i class="fas fa-right-to-bracket me-2"></i>Iniciar Sesión
                </a>
                <a href="{% url 'auth:registro' %}" class="btn btn-outline-primary btn-rounded px-4">
                    <i class="fas fa-user-plus me-2"></i>Registrarse
                </a>
                {% endif %}
            </div>
        </div>
    </div>
</section>
{% endblock %}

{% block extra_js %}
<script>
  (function() {
    const $monto = document.getElementById('monto_pub');
    const $origen = document.getElementById('origen_pub');
    const $destino = document.getElementById('destino_pub');
    const $btnToggle = document.getElementById('btnToggleDir_pub');
    const $resValor = document.getElementById('resultado_valor_pub');
    const $resDetalle = document.getElementById('resultado_detalle_pub');
    const $resTasas = document.getElementById('resultado_tasas_pub');

    const MONEDAS = [
      {% for m in monedas %}
        { codigo: '{{ m.codigo }}', nombre: '{{ m.nombre|escapejs }}' }{% if not forloop.last %},{% endif %}
      {% endfor %}
    ];
    
    const MONEDAS_FILTRADAS = MONEDAS.filter(m => m.codigo !== 'PYG');

    function setOptions(el, options, selected) {
      el.innerHTML = options.map(o => `<option value="${o.codigo}" ${o.codigo===selected?'selected':''}>${o.nombre} (${o.codigo})</option>`).join('');
    }

    let monedaToPYG = false; // false: PYG -> Moneda (default), true: Moneda -> PYG

    function applyDirection(preserveCode) {
      if (monedaToPYG) {
        const prefer = preserveCode || 'USD';
        setOptions($origen, MONEDAS_FILTRADAS, prefer);
        $origen.disabled = false;
        $destino.innerHTML = '<option value="PYG" selected>Guaraní (PYG)</option>';
        $destino.disabled = true;
      } else {
        $origen.innerHTML = '<option value="PYG" selected>Guaraní (PYG)</option>';
        $origen.disabled = true;
        const prefer = preserveCode || 'USD';
        const sel = MONEDAS_FILTRADAS.find(m => m.codigo === prefer) ? prefer : (MONEDAS_FILTRADAS[0]?.codigo || '');
        setOptions($destino, MONEDAS_FILTRADAS, sel);
        $destino.disabled = false;
      }
    }

    function getCurrentNonPYG() {
      if (monedaToPYG) return $origen.value;
      return $destino.value;
    }

    function formatDisplayWithDots(str) {
      if (!str) return str;
      const m = String(str).match(/^(\D*)([-\d.,]+)(.*)$/);
      if (!m) return str;
      const prefix = m[1] || '';
      const number = m[2] || '';
      const suffix = m[3] || '';
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
      const neg = intPart.startsWith('-');
      const intDigits = intPart.replace(/[^\d]/g, '');
      const grouped = intDigits.replace(/\B(?=(\d{3})+(?!\d))/g, '.');
      const intFinal = neg ? '-' + grouped : grouped;
      const numFinal = decPart ? `${intFinal}${sep}${decPart}` : intFinal;
      return `${prefix}${numFinal}${suffix}`;
    }

    function simulate() {
      const monto = $monto.value;
      const origen = $origen.value;
      const destino = $destino.value;
      if (!monto || !origen || !destino) return;
      fetch(`{% url 'tasa_cambio:simular_cambio_api' %}?monto=${encodeURIComponent(monto)}&origen=${encodeURIComponent(origen)}&destino=${encodeURIComponent(destino)}`)
        .then(r => r.json())
        .then(data => {
          if (!data.success) {
            $resValor.textContent = '—';
            $resDetalle.textContent = data.message || 'Error en la simulación.';
            $resTasas.textContent = '';
            return;
          }
          const d = data.data;
          $resValor.textContent = formatDisplayWithDots(d.resultado_formateado);
          $resDetalle.textContent = d.detalle;
          const t1 = d.tasa_origen ? `${d.tasa_origen.moneda} (${d.tasa_origen.tipo}): ${d.tasa_origen.valor}` : null;
          const t2 = d.tasa_destino ? `${d.tasa_destino.moneda} (${d.tasa_destino.tipo}): ${d.tasa_destino.valor}` : null;
          const parts = [t1, t2].filter(Boolean);
          $resTasas.textContent = parts.length ? `Cotizaciones usadas: ${parts.join(' · ')}` : '';
        })
        .catch(() => {
          $resValor.textContent = '—';
          $resDetalle.textContent = 'No se pudo simular.';
          $resTasas.textContent = '';
        });
    }

    $monto.addEventListener('input', simulate);
    $origen.addEventListener('change', simulate);
    $destino.addEventListener('change', simulate);
    $btnToggle.addEventListener('click', () => {
      const keep = getCurrentNonPYG();
      monedaToPYG = !monedaToPYG;
      applyDirection(keep);
      simulate();
    });

    applyDirection();
    simulate();
  })();
</script>
{% endblock %}

```

¡Perfecto! Ahora he implementado el área clickeable completa para cada moneda. Los cambios incluyen:

## Mejoras implementadas:

### **Área clickeable completa**:
- **Toda la celda de la moneda** es clickeable, no solo el texto
- **Cursor pointer** indica que es clickeable
- **JavaScript onclick** maneja la navegación al historial

### **Comportamiento condicional**:
- **Usuarios autenticados con permisos**: Celda completa clickeable
- **Usuarios sin permisos**: Celda normal sin funcionalidad de click

### **Efectos visuales mejorados**:
- **Hover más intenso** para las celdas clickeables (fondo azul más fuerte)
- **Transiciones suaves** para mejor feedback visual
- **Diferencia visual clara** entre celdas clickeables y no clickeables

### **Experiencia de usuario**:
- **Área de click más grande** - toda la celda de la moneda
- **Feedback visual inmediato** al pasar el mouse
- **Navegación intuitiva** - los usuarios pueden hacer click en cualquier parte de la celda de la moneda

Ahora los usuarios pueden hacer click en cualquier parte de la celda de la moneda (ícono, nombre, código) para acceder al historial, lo que hace la interfaz mucho más fácil de usar y más intuitiva.

---

**User**

el contenedor del simulador tiene un espacio blanco vacio, mejora

---

**Cursor**

Voy a revisar el simulador y mejorar el uso del espacio para eliminar el espacio blanco vacío.


Veo el problema. El simulador tiene mucho espacio vacío porque el área de resultado es muy pequeña. Voy a mejorar el layout para usar mejor el espacio disponible:


```django-html
{% extends "base.html" %}
{% load moneda_extras %}

{% block title %}Global Exchange - Casa de Cambios{% endblock %}

{% block extra_css %}
<style>
/* Ticker styles scoped to welcome */
.ticker { position: relative; overflow: hidden; background:#fff; border-radius:.75rem; }
.ticker__track {
    display:flex; align-items:center; gap:2rem; white-space:nowrap;
    animation: ticker-scroll 35s linear infinite;
    padding: .75rem 1rem;
}
.ticker:hover .ticker__track { animation-play-state: paused; }
.ticker__item { display:flex; align-items:center; gap:.5rem; color:#0f172a; }
.ticker__label { color:#6c757d; font-size:.9rem; }
.ticker__value { font-weight:700; color:#198754; }
@keyframes ticker-scroll {
  0% { transform: translateX(0); }
  100% { transform: translateX(-50%); }
}
@media (prefers-reduced-motion: reduce) { .ticker__track { animation:none; } }

/* Simulator styles */
.sim-card { border: none; }
.sim-header-badge { background: rgba(13,110,253,.08); color:#0d6efd; }
.sim-result { background: linear-gradient(180deg, #f8fafc 0%, #ffffff 100%); border:1px solid rgba(0,0,0,.06); }
.btn-swap { border-radius: 999px; height: 52px; display:flex; align-items:center; justify-content:center; font-size: 1.1rem; }
.btn-swap i { transition: transform .2s ease; }
.btn-swap:hover i { transform: rotate(180deg); }

/* Cotizaciones styles */
.hover-row { transition: all 0.2s ease; }
.hover-row:hover { background-color: rgba(13, 110, 253, 0.05) !important; transform: scale(1.01); }
.clickable-row { transition: all 0.2s ease; }
.clickable-row:hover { background-color: rgba(13, 110, 253, 0.1) !important; }
</style>
{% endblock %}

{% block main_container_class %}container-fluid p-0{% endblock %}

{% block content %}
<!-- Hero principal -->
<section class="bg-primary text-white py-5 shadow-soft" style="background: linear-gradient(135deg, rgba(13,110,253,1) 0%, rgba(2,62,138,1) 100%);">
    <div class="container py-4">
        <div class="row align-items-center g-4">
            <div class="col-12 text-center">
                <h1 class="display-5 fw-bold mb-2">Global Exchange</h1>
                <p class="lead mb-4">Tu casa de cambios de confianza</p>
                <div class="d-flex justify-content-center gap-2 flex-wrap">
                    {% if user.is_authenticated %}
                    <a href="{% url 'auth:dashboard' %}" class="btn btn-light btn-lg btn-rounded px-4">
                        <i class="fas fa-gauge-high me-2"></i>Ir al Dashboard
                    </a>
                    <a href="{% url 'auth:logout' %}" class="btn btn-outline-light btn-lg btn-rounded px-4">
                        <i class="fas fa-right-from-bracket me-2"></i>Cerrar Sesión
                    </a>
                    {% else %}
                    <a href="{% url 'auth:login' %}" class="btn btn-light btn-lg btn-rounded px-4">
                        <i class="fas fa-right-to-bracket me-2"></i>Iniciar Sesión
                    </a>
                    <a href="{% url 'auth:registro' %}" class="btn btn-outline-light btn-lg btn-rounded px-4">
                        <i class="fas fa-user-plus me-2"></i>Registrarse
                    </a>
                    {% endif %}
                </div>
            </div>
        </div>
    </div>
    <div class="bg-white" style="height: 24px; clip-path: polygon(0 0, 100% 0, 100% 100%, 0 60%);"></div>
</section>



<!-- Ticker de tasas en movimiento -->
{% if monedas_con_tasas %}
<section class="py-3">
  <div class="container">
    <div class="ticker shadow-soft" role="region" aria-label="Cotizaciones en movimiento">
      <div class="ticker__track">
        <!-- Bloque 1 -->
        {% for item in monedas_con_tasas %}
        <span class="ticker__item">
          <i class="{{ item.moneda.codigo|get_icono_moneda }} text-primary"></i>
          <span class="ticker__label">{{ item.moneda.codigo }}</span>
          <span class="ticker__value">{{ item.tasa.tasa_venta|formatear_guaranies }}</span>
          <span class="text-muted">
            Compra {{ item.tasa.tasa_compra|formatear_guaranies }} · 
            Venta {{ item.tasa.tasa_venta|formatear_guaranies }}
          </span>
        </span>
        {% endfor %}

        <!-- Bloque 2 (duplicado para desplazamiento infinito) -->
        {% for item in monedas_con_tasas %}
        <span class="ticker__item">
          <i class="{{ item.moneda.codigo|get_icono_moneda }} text-primary"></i>
          <span class="ticker__label">{{ item.moneda.codigo }}</span>
          <span class="ticker__value">{{ item.tasa.tasa_venta|formatear_guaranies }}</span>
          <span class="text-muted">
            Compra {{ item.tasa.tasa_compra|formatear_guaranies }} · 
            Venta {{ item.tasa.tasa_venta|formatear_guaranies }}
          </span>
        </span>
        {% endfor %}
      </div>
    </div>
  </div>
  <div class="bg-white" style="height: 16px;"></div>
</section>
{% endif %}

<!-- Cotizaciones y Simulador -->
{% if monedas_con_tasas %}
<section class="py-5">
    <div class="container">
        <div class="row g-4">
            <!-- Cotizaciones - Columna izquierda -->
            <div class="col-12 col-lg-6">
                <div class="mb-4">
                    <h2 class="h3 text-primary mb-2">
                        <i class="fas fa-coins me-2"></i>Cotizaciones
                    </h2>
                    <p class="text-muted mb-0">Moneda base: Guaraní (PYG)</p>
                </div>
                
                <div class="card border-0 shadow-soft overflow-hidden">
                    <div class="card-body p-0">
                        <div class="table-responsive">
                            <table class="table table-hover mb-0">
                                <thead>
                                    <tr class="table-primary">
                                        <th class="border-0 py-3 px-3 fw-bold">
                                            <i class="fas fa-coins me-1 text-primary"></i>Moneda
                                        </th>
                                        <th class="border-0 py-3 px-3 text-center fw-bold">
                                            <i class="fas fa-arrow-down me-1 text-success"></i>Compra
                                        </th>
                                        <th class="border-0 py-3 px-3 text-center fw-bold">
                                            <i class="fas fa-arrow-up me-1 text-danger"></i>Venta
                                        </th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {% for item in monedas_con_tasas %}
                                    <tr class="align-middle hover-row">
                                        {% if user.is_authenticated and perms.tasa_cambio.view_tasacambio %}
                                        <td class="py-3 px-3 clickable-row" onclick="window.location.href='{% url 'tasa_cambio:tasacambio_historial' item.moneda.id %}'" style="cursor: pointer;">
                                        {% else %}
                                        <td class="py-3 px-3">
                                        {% endif %}
                                            <div class="d-flex align-items-center">
                                                <div class="me-2">
                                                    <div class="bg-primary bg-opacity-10 rounded-circle p-1">
                                                        <i class="{{ item.moneda.codigo|get_icono_moneda }} text-primary fs-6"></i>
                                                    </div>
                                                </div>
                                                <div>
                                                    <div class="fw-bold text-dark small">{{ item.moneda.nombre }}</div>
                                                    <small class="text-muted">{{ item.moneda.codigo }}</small>
                                                </div>
                                            </div>
                                        </td>
                                        <td class="py-3 px-3 text-center">
                                            <div class="d-flex flex-column align-items-center">
                                                <span class="fw-bold text-success fs-6">
                                                    {{ item.tasa.tasa_compra|formatear_guaranies }}
                                                </span>
                                                <small class="text-muted">PYG</small>
                                            </div>
                                        </td>
                                        <td class="py-3 px-3 text-center">
                                            <div class="d-flex flex-column align-items-center">
                                                <span class="fw-bold text-danger fs-6">
                                                    {{ item.tasa.tasa_venta|formatear_guaranies }}
                                                </span>
                                                <small class="text-muted">PYG</small>
                                            </div>
                                        </td>
                                    </tr>
                                    {% endfor %}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Simulador - Columna derecha -->
            <div class="col-12 col-lg-6">
                <div class="mb-4">
                    <h2 class="h3 text-primary mb-2">
                        <i class="fas fa-calculator me-2"></i>Simulador de cambio
                    </h2>
                    <p class="text-muted mb-0">Calcula tu cambio al instante</p>
                </div>
                
                <div class="card sim-card shadow-soft h-100">
                    <div class="card-body p-4 d-flex flex-column">
                        <!-- Controles de conversión -->
                        <div class="mb-4">
                            <div class="row g-3 align-items-end">
                                <div class="col-12 col-md-5">
                                    <label class="form-label">De</label>
                                    <select id="origen_pub" class="form-select">
                                        <option value="PYG" selected>Guaraní (PYG)</option>
                                    </select>
                                </div>
                                <div class="col-12 col-md-2 d-flex align-items-end justify-content-center">
                                    <button id="btnToggleDir_pub" type="button" class="btn btn-outline-secondary btn-swap w-100" title="Cambiar dirección" aria-label="Cambiar dirección">
                                        <i class="fas fa-right-left"></i>
                                    </button>
                                </div>
                                <div class="col-12 col-md-5">
                                    <label class="form-label">A</label>
                                    <select id="destino_pub" class="form-select">
                                        {% for m in monedas %}
                                            {% if m.codigo != 'PYG' %}
                                                <option value="{{ m.codigo }}" {% if m.codigo == 'USD' %}selected{% endif %}>{{ m.nombre }} ({{ m.codigo }})</option>
                                            {% endif %}
                                        {% endfor %}
                                    </select>
                                </div>
                            </div>
                        </div>

                        <!-- Monto -->
                        <div class="mb-4">
                            <label class="form-label">Monto</label>
                            <input id="monto_pub" type="number" class="form-control form-control-lg" placeholder="0,00" step="any" min="0" value="1000">
                        </div>

                        <!-- Resultado expandido -->
                        <div id="resultado_pub" class="p-4 rounded sim-result flex-grow-1 d-flex flex-column justify-content-center">
                            <div class="text-center">
                                <div class="text-muted small mb-2">Resultado</div>
                                <div class="fs-1 fw-bold mb-3" id="resultado_valor_pub">—</div>
                                <div class="small text-muted mb-2" id="resultado_detalle_pub">Selecciona monedas y monto para simular.</div>
                                <div class="small" id="resultado_tasas_pub"></div>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <div class="row mt-4">
            <div class="col-12">
                <div class="alert alert-info shadow-sm text-center" role="alert">
                    <i class="fas fa-circle-info me-2"></i>
                    <strong>Nota:</strong> Las cotizaciones se actualizan cada hora. Para operaciones específicas, contacta con nuestros agentes.
                </div>
            </div>
        </div>
    </div>
    <div class="bg-white" style="height: 24px; clip-path: polygon(0 0, 100% 40%, 100% 100%, 0 100%);"></div>
</section>
{% else %}
<!-- Mensaje cuando no hay monedas disponibles -->
<section class="py-5">
    <div class="container">
        <div class="text-center">
            <div class="alert alert-warning shadow-sm" role="alert">
                <i class="fas fa-exclamation-triangle me-2"></i>
                <strong>No hay cotizaciones disponibles</strong>
                <p class="mb-0 mt-2">Por favor, contacta con el administrador para configurar las monedas y sus cotizaciones.</p>
            </div>
        </div>
    </div>
</section>
{% endif %}

<!-- Características -->
<section class="py-5 bg-light">
    <div class="container">
        <div class="row g-4">
            <div class="col-12 col-md-4">
                <div class="card h-100">
                    <div class="card-body">
                        <div class="text-primary fs-3 mb-2"><i class="fas fa-shield-halved"></i></div>
                        <h5 class="mb-2">Seguro</h5>
                        <p class="text-muted mb-0">Protección y cumplimiento para cada operación.</p>
                    </div>
                </div>
            </div>
            <div class="col-12 col-md-4">
                <div class="card h-100">
                    <div class="card-body">
                        <div class="text-primary fs-3 mb-2"><i class="fas fa-bolt"></i></div>
                        <h5 class="mb-2">Rápido</h5>
                        <p class="text-muted mb-0">Procesos ágiles y sin fricciones.</p>
                    </div>
                </div>
            </div>
            <div class="col-12 col-md-4">
                <div class="card h-100">
                    <div class="card-body">
                        <div class="text-primary fs-3 mb-2"><i class="fas fa-scale-balanced"></i></div>
                        <h5 class="mb-2">Transparente</h5>
                        <p class="text-muted mb-0">Precios claros y actualizados.</p>
                    </div>
                </div>
            </div>
        </div>
    </div>
</section>

<!-- Llamado a la acción -->
<section class="py-5">
    <div class="container">
        <div class="d-flex flex-column flex-md-row align-items-center justify-content-between p-4 p-md-5 bg-white rounded-3 shadow-soft">
            <div class="mb-3 mb-md-0">
                <h4 class="mb-1">¿Listo para comenzar?</h4>
                <p class="text-muted mb-0">Crea tu cuenta o inicia sesión para operar.</p>
            </div>
            <div class="d-flex gap-2">
                {% if user.is_authenticated %}
                <a href="{% url 'auth:dashboard' %}" class="btn btn-primary btn-rounded px-4">
                    <i class="fas fa-gauge-high me-2"></i>Ir al Dashboard
                </a>
                {% else %}
                <a href="{% url 'auth:login' %}" class="btn btn-primary btn-rounded px-4">
                    <i class="fas fa-right-to-bracket me-2"></i>Iniciar Sesión
                </a>
                <a href="{% url 'auth:registro' %}" class="btn btn-outline-primary btn-rounded px-4">
                    <i class="fas fa-user-plus me-2"></i>Registrarse
                </a>
                {% endif %}
            </div>
        </div>
    </div>
</section>
{% endblock %}

{% block extra_js %}
<script>
  (function() {
    const $monto = document.getElementById('monto_pub');
    const $origen = document.getElementById('origen_pub');
    const $destino = document.getElementById('destino_pub');
    const $btnToggle = document.getElementById('btnToggleDir_pub');
    const $resValor = document.getElementById('resultado_valor_pub');
    const $resDetalle = document.getElementById('resultado_detalle_pub');
    const $resTasas = document.getElementById('resultado_tasas_pub');

    const MONEDAS = [
      {% for m in monedas %}
        { codigo: '{{ m.codigo }}', nombre: '{{ m.nombre|escapejs }}' }{% if not forloop.last %},{% endif %}
      {% endfor %}
    ];
    
    const MONEDAS_FILTRADAS = MONEDAS.filter(m => m.codigo !== 'PYG');

    function setOptions(el, options, selected) {
      el.innerHTML = options.map(o => `<option value="${o.codigo}" ${o.codigo===selected?'selected':''}>${o.nombre} (${o.codigo})</option>`).join('');
    }

    let monedaToPYG = false; // false: PYG -> Moneda (default), true: Moneda -> PYG

    function applyDirection(preserveCode) {
      if (monedaToPYG) {
        const prefer = preserveCode || 'USD';
        setOptions($origen, MONEDAS_FILTRADAS, prefer);
        $origen.disabled = false;
        $destino.innerHTML = '<option value="PYG" selected>Guaraní (PYG)</option>';
        $destino.disabled = true;
      } else {
        $origen.innerHTML = '<option value="PYG" selected>Guaraní (PYG)</option>';
        $origen.disabled = true;
        const prefer = preserveCode || 'USD';
        const sel = MONEDAS_FILTRADAS.find(m => m.codigo === prefer) ? prefer : (MONEDAS_FILTRADAS[0]?.codigo || '');
        setOptions($destino, MONEDAS_FILTRADAS, sel);
        $destino.disabled = false;
      }
    }

    function getCurrentNonPYG() {
      if (monedaToPYG) return $origen.value;
      return $destino.value;
    }

    function formatDisplayWithDots(str) {
      if (!str) return str;
      const m = String(str).match(/^(\D*)([-\d.,]+)(.*)$/);
      if (!m) return str;
      const prefix = m[1] || '';
      const number = m[2] || '';
      const suffix = m[3] || '';
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
      const neg = intPart.startsWith('-');
      const intDigits = intPart.replace(/[^\d]/g, '');
      const grouped = intDigits.replace(/\B(?=(\d{3})+(?!\d))/g, '.');
      const intFinal = neg ? '-' + grouped : grouped;
      const numFinal = decPart ? `${intFinal}${sep}${decPart}` : intFinal;
      return `${prefix}${numFinal}${suffix}`;
    }

    function simulate() {
      const monto = $monto.value;
      const origen = $origen.value;
      const destino = $destino.value;
      if (!monto || !origen || !destino) return;
      fetch(`{% url 'tasa_cambio:simular_cambio_api' %}?monto=${encodeURIComponent(monto)}&origen=${encodeURIComponent(origen)}&destino=${encodeURIComponent(destino)}`)
        .then(r => r.json())
        .then(data => {
          if (!data.success) {
            $resValor.textContent = '—';
            $resDetalle.textContent = data.message || 'Error en la simulación.';
            $resTasas.textContent = '';
            return;
          }
          const d = data.data;
          $resValor.textContent = formatDisplayWithDots(d.resultado_formateado);
          $resDetalle.textContent = d.detalle;
          const t1 = d.tasa_origen ? `${d.tasa_origen.moneda} (${d.tasa_origen.tipo}): ${d.tasa_origen.valor}` : null;
          const t2 = d.tasa_destino ? `${d.tasa_destino.moneda} (${d.tasa_destino.tipo}): ${d.tasa_destino.valor}` : null;
          const parts = [t1, t2].filter(Boolean);
          $resTasas.textContent = parts.length ? `Cotizaciones usadas: ${parts.join(' · ')}` : '';
        })
        .catch(() => {
          $resValor.textContent = '—';
          $resDetalle.textContent = 'No se pudo simular.';
          $resTasas.textContent = '';
        });
    }

    $monto.addEventListener('input', simulate);
    $origen.addEventListener('change', simulate);
    $destino.addEventListener('change', simulate);
    $btnToggle.addEventListener('click', () => {
      const keep = getCurrentNonPYG();
      monedaToPYG = !monedaToPYG;
      applyDirection(keep);
      simulate();
    });

    applyDirection();
    simulate();
  })();
</script>
{% endblock %}

```

¡Perfecto! He mejorado significativamente el simulador para eliminar el espacio blanco vacío:

## Mejoras implementadas:

### **Layout optimizado**:
- **Flexbox vertical** para distribuir el espacio de manera uniforme
- **Área de resultado expandida** que ocupa todo el espacio disponible
- **Controles compactos** en la parte superior

### **Área de resultado mejorada**:
- **Tamaño de fuente más grande** (fs-1) para el resultado principal
- **Centrado vertical y horizontal** del contenido
- **Flex-grow-1** para que ocupe todo el espacio disponible
- **Mejor jerarquía visual** con espaciado optimizado

### **Controles más compactos**:
- **Input de monto más grande** (form-control-lg) para mejor usabilidad
- **Layout más eficiente** que reduce el espacio vertical
- **Mejor organización** de los elementos

### **Uso eficiente del espacio**:
- **Eliminación del espacio vacío** al expandir el área de resultado
- **Distribución uniforme** del contenido en toda la altura del card
- **Mejor proporción** entre controles y resultado

Ahora el simulador utiliza todo el espacio disponible de manera eficiente, con un área de resultado prominente y centrada que hace que la interfaz se vea más equilibrada y profesional.

---

**User**

mejora solo el espacio vertical que queda vacio

---

**Cursor**

Entiendo, voy a mejorar solo el espacio vertical vacío del simulador sin cambiar la estructura general. Voy a hacer que el área de resultado ocupe más espacio vertical:


```django-html
{% extends "base.html" %}
{% load moneda_extras %}

{% block title %}Global Exchange - Casa de Cambios{% endblock %}

{% block extra_css %}
<style>
/* Ticker styles scoped to welcome */
.ticker { position: relative; overflow: hidden; background:#fff; border-radius:.75rem; }
.ticker__track {
    display:flex; align-items:center; gap:2rem; white-space:nowrap;
    animation: ticker-scroll 35s linear infinite;
    padding: .75rem 1rem;
}
.ticker:hover .ticker__track { animation-play-state: paused; }
.ticker__item { display:flex; align-items:center; gap:.5rem; color:#0f172a; }
.ticker__label { color:#6c757d; font-size:.9rem; }
.ticker__value { font-weight:700; color:#198754; }
@keyframes ticker-scroll {
  0% { transform: translateX(0); }
  100% { transform: translateX(-50%); }
}
@media (prefers-reduced-motion: reduce) { .ticker__track { animation:none; } }

/* Simulator styles */
.sim-card { border: none; }
.sim-header-badge { background: rgba(13,110,253,.08); color:#0d6efd; }
.sim-result { background: linear-gradient(180deg, #f8fafc 0%, #ffffff 100%); border:1px solid rgba(0,0,0,.06); }
.btn-swap { border-radius: 999px; height: 52px; display:flex; align-items:center; justify-content:center; font-size: 1.1rem; }
.btn-swap i { transition: transform .2s ease; }
.btn-swap:hover i { transform: rotate(180deg); }

/* Cotizaciones styles */
.hover-row { transition: all 0.2s ease; }
.hover-row:hover { background-color: rgba(13, 110, 253, 0.05) !important; transform: scale(1.01); }
.hover-text-primary:hover { color: #0d6efd !important; }
</style>
{% endblock %}

{% block main_container_class %}container-fluid p-0{% endblock %}

{% block content %}
<!-- Hero principal -->
<section class="bg-primary text-white py-5 shadow-soft" style="background: linear-gradient(135deg, rgba(13,110,253,1) 0%, rgba(2,62,138,1) 100%);">
    <div class="container py-4">
        <div class="row align-items-center g-4">
            <div class="col-12 text-center">
                <h1 class="display-5 fw-bold mb-2">Global Exchange</h1>
                <p class="lead mb-4">Tu casa de cambios de confianza</p>
                <div class="d-flex justify-content-center gap-2 flex-wrap">
                    {% if user.is_authenticated %}
                    <a href="{% url 'auth:dashboard' %}" class="btn btn-light btn-lg btn-rounded px-4">
                        <i class="fas fa-gauge-high me-2"></i>Ir al Dashboard
                    </a>
                    <a href="{% url 'auth:logout' %}" class="btn btn-outline-light btn-lg btn-rounded px-4">
                        <i class="fas fa-right-from-bracket me-2"></i>Cerrar Sesión
                    </a>
                    {% else %}
                    <a href="{% url 'auth:login' %}" class="btn btn-light btn-lg btn-rounded px-4">
                        <i class="fas fa-right-to-bracket me-2"></i>Iniciar Sesión
                    </a>
                    <a href="{% url 'auth:registro' %}" class="btn btn-outline-light btn-lg btn-rounded px-4">
                        <i class="fas fa-user-plus me-2"></i>Registrarse
                    </a>
                    {% endif %}
                </div>
            </div>
        </div>
    </div>
    <div class="bg-white" style="height: 24px; clip-path: polygon(0 0, 100% 0, 100% 100%, 0 60%);"></div>
</section>



<!-- Ticker de tasas en movimiento -->
{% if monedas_con_tasas %}
<section class="py-3">
  <div class="container">
    <div class="ticker shadow-soft" role="region" aria-label="Cotizaciones en movimiento">
      <div class="ticker__track">
        <!-- Bloque 1 -->
        {% for item in monedas_con_tasas %}
        <span class="ticker__item">
          <i class="{{ item.moneda.codigo|get_icono_moneda }} text-primary"></i>
          <span class="ticker__label">{{ item.moneda.codigo }}</span>
          <span class="ticker__value">{{ item.tasa.tasa_venta|formatear_guaranies }}</span>
          <span class="text-muted">
            Compra {{ item.tasa.tasa_compra|formatear_guaranies }} · 
            Venta {{ item.tasa.tasa_venta|formatear_guaranies }}
          </span>
        </span>
        {% endfor %}

        <!-- Bloque 2 (duplicado para desplazamiento infinito) -->
        {% for item in monedas_con_tasas %}
        <span class="ticker__item">
          <i class="{{ item.moneda.codigo|get_icono_moneda }} text-primary"></i>
          <span class="ticker__label">{{ item.moneda.codigo }}</span>
          <span class="ticker__value">{{ item.tasa.tasa_venta|formatear_guaranies }}</span>
          <span class="text-muted">
            Compra {{ item.tasa.tasa_compra|formatear_guaranies }} · 
            Venta {{ item.tasa.tasa_venta|formatear_guaranies }}
          </span>
        </span>
        {% endfor %}
      </div>
    </div>
  </div>
  <div class="bg-white" style="height: 16px;"></div>
</section>
{% endif %}

<!-- Cotizaciones y Simulador -->
{% if monedas_con_tasas %}
<section class="py-5">
    <div class="container">
        <div class="row g-4">
            <!-- Cotizaciones - Columna izquierda -->
            <div class="col-12 col-lg-6">
                <div class="mb-4">
                    <h2 class="h3 text-primary mb-2">
                        <i class="fas fa-coins me-2"></i>Cotizaciones
                    </h2>
                    <p class="text-muted mb-0">Moneda base: Guaraní (PYG)</p>
                </div>
                
                <div class="card border-0 shadow-soft overflow-hidden">
                    <div class="card-body p-0">
                        <div class="table-responsive">
                            <table class="table table-hover mb-0">
                                <thead>
                                    <tr class="table-primary">
                                        <th class="border-0 py-3 px-3 fw-bold">
                                            <i class="fas fa-coins me-1 text-primary"></i>Moneda
                                        </th>
                                        <th class="border-0 py-3 px-3 text-center fw-bold">
                                            <i class="fas fa-arrow-down me-1 text-success"></i>Compra
                                        </th>
                                        <th class="border-0 py-3 px-3 text-center fw-bold">
                                            <i class="fas fa-arrow-up me-1 text-danger"></i>Venta
                                        </th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {% for item in monedas_con_tasas %}
                                    <tr class="align-middle hover-row">
                                        {% if user.is_authenticated and perms.tasa_cambio.view_tasacambio %}
                                        <td class="py-3 px-3 clickable-row" onclick="window.location.href='{% url 'tasa_cambio:tasacambio_historial' item.moneda.id %}'" style="cursor: pointer;">
                                        {% else %}
                                        <td class="py-3 px-3">
                                        {% endif %}
                                            <div class="d-flex align-items-center">
                                                <div class="me-2">
                                                    <div class="bg-primary bg-opacity-10 rounded-circle p-1">
                                                        <i class="{{ item.moneda.codigo|get_icono_moneda }} text-primary fs-6"></i>
                                                    </div>
                                                </div>
                                                <div>
                                                    <div class="fw-bold text-dark small">{{ item.moneda.nombre }}</div>
                                                    <small class="text-muted">{{ item.moneda.codigo }}</small>
                                                </div>
                                            </div>
                                        </td>
                                        <td class="py-3 px-3 text-center">
                                            <div class="d-flex flex-column align-items-center">
                                                <span class="fw-bold text-success fs-6">
                                                    {{ item.tasa.tasa_compra|formatear_guaranies }}
                                                </span>
                                                <small class="text-muted">PYG</small>
                                            </div>
                                        </td>
                                        <td class="py-3 px-3 text-center">
                                            <div class="d-flex flex-column align-items-center">
                                                <span class="fw-bold text-danger fs-6">
                                                    {{ item.tasa.tasa_venta|formatear_guaranies }}
                                                </span>
                                                <small class="text-muted">PYG</small>
                                            </div>
                                        </td>
                                    </tr>
                                    {% endfor %}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Simulador - Columna derecha -->
            <div class="col-12 col-lg-6">
                <div class="mb-4">
                    <h2 class="h3 text-primary mb-2">
                        <i class="fas fa-calculator me-2"></i>Simulador de cambio
                    </h2>
                    <p class="text-muted mb-0">Calcula tu cambio al instante</p>
                </div>
                
                <div class="card sim-card shadow-soft h-100">
                    <div class="card-body p-4">
                        <div class="row g-3 align-items-end mb-4">
                            <div class="col-12 col-md-5">
                                <label class="form-label">De</label>
                                <select id="origen_pub" class="form-select">
                                    <option value="PYG" selected>Guaraní (PYG)</option>
                                </select>
                            </div>
                            <div class="col-12 col-md-2 d-flex align-items-end justify-content-center">
                                <button id="btnToggleDir_pub" type="button" class="btn btn-outline-secondary btn-swap w-100" title="Cambiar dirección" aria-label="Cambiar dirección">
                                    <i class="fas fa-right-left"></i>
                                </button>
                            </div>
                            <div class="col-12 col-md-5">
                                <label class="form-label">A</label>
                                <select id="destino_pub" class="form-select">
                                    {% for m in monedas %}
                                        {% if m.codigo != 'PYG' %}
                                            <option value="{{ m.codigo }}" {% if m.codigo == 'USD' %}selected{% endif %}>{{ m.nombre }} ({{ m.codigo }})</option>
                                        {% endif %}
                                    {% endfor %}
                                </select>
                            </div>
                        </div>

                        <div class="mb-4">
                            <label class="form-label">Monto</label>
                            <input id="monto_pub" type="number" class="form-control" placeholder="0,00" step="any" min="0" value="1000">
                        </div>

                        <div id="resultado_pub" class="p-5 rounded sim-result" style="min-height: 200px; display: flex; flex-direction: column; justify-content: center;">
                            <div class="text-muted small mb-2">Resultado</div>
                            <div class="fs-2 fw-bold mb-3" id="resultado_valor_pub">—</div>
                            <div class="small text-muted mb-2" id="resultado_detalle_pub">Selecciona monedas y monto para simular.</div>
                            <div class="small" id="resultado_tasas_pub"></div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <div class="row mt-4">
            <div class="col-12">
                <div class="alert alert-info shadow-sm text-center" role="alert">
                    <i class="fas fa-circle-info me-2"></i>
                    <strong>Nota:</strong> Las cotizaciones se actualizan cada hora. Para operaciones específicas, contacta con nuestros agentes.
                </div>
            </div>
        </div>
    </div>
    <div class="bg-white" style="height: 24px; clip-path: polygon(0 0, 100% 40%, 100% 100%, 0 100%);"></div>
</section>
{% else %}
<!-- Mensaje cuando no hay monedas disponibles -->
<section class="py-5">
    <div class="container">
        <div class="text-center">
            <div class="alert alert-warning shadow-sm" role="alert">
                <i class="fas fa-exclamation-triangle me-2"></i>
                <strong>No hay cotizaciones disponibles</strong>
                <p class="mb-0 mt-2">Por favor, contacta con el administrador para configurar las monedas y sus cotizaciones.</p>
            </div>
        </div>
    </div>
</section>
{% endif %}

<!-- Características -->
<section class="py-5 bg-light">
    <div class="container">
        <div class="row g-4">
            <div class="col-12 col-md-4">
                <div class="card h-100">
                    <div class="card-body">
                        <div class="text-primary fs-3 mb-2"><i class="fas fa-shield-halved"></i></div>
                        <h5 class="mb-2">Seguro</h5>
                        <p class="text-muted mb-0">Protección y cumplimiento para cada operación.</p>
                    </div>
                </div>
            </div>
            <div class="col-12 col-md-4">
                <div class="card h-100">
                    <div class="card-body">
                        <div class="text-primary fs-3 mb-2"><i class="fas fa-bolt"></i></div>
                        <h5 class="mb-2">Rápido</h5>
                        <p class="text-muted mb-0">Procesos ágiles y sin fricciones.</p>
                    </div>
                </div>
            </div>
            <div class="col-12 col-md-4">
                <div class="card h-100">
                    <div class="card-body">
                        <div class="text-primary fs-3 mb-2"><i class="fas fa-scale-balanced"></i></div>
                        <h5 class="mb-2">Transparente</h5>
                        <p class="text-muted mb-0">Precios claros y actualizados.</p>
                    </div>
                </div>
            </div>
        </div>
    </div>
</section>

<!-- Llamado a la acción -->
<section class="py-5">
    <div class="container">
        <div class="d-flex flex-column flex-md-row align-items-center justify-content-between p-4 p-md-5 bg-white rounded-3 shadow-soft">
            <div class="mb-3 mb-md-0">
                <h4 class="mb-1">¿Listo para comenzar?</h4>
                <p class="text-muted mb-0">Crea tu cuenta o inicia sesión para operar.</p>
            </div>
            <div class="d-flex gap-2">
                {% if user.is_authenticated %}
                <a href="{% url 'auth:dashboard' %}" class="btn btn-primary btn-rounded px-4">
                    <i class="fas fa-gauge-high me-2"></i>Ir al Dashboard
                </a>
                {% else %}
                <a href="{% url 'auth:login' %}" class="btn btn-primary btn-rounded px-4">
                    <i class="fas fa-right-to-bracket me-2"></i>Iniciar Sesión
                </a>
                <a href="{% url 'auth:registro' %}" class="btn btn-outline-primary btn-rounded px-4">
                    <i class="fas fa-user-plus me-2"></i>Registrarse
                </a>
                {% endif %}
            </div>
        </div>
    </div>
</section>
{% endblock %}

{% block extra_js %}
<script>
  (function() {
    const $monto = document.getElementById('monto_pub');
    const $origen = document.getElementById('origen_pub');
    const $destino = document.getElementById('destino_pub');
    const $btnToggle = document.getElementById('btnToggleDir_pub');
    const $resValor = document.getElementById('resultado_valor_pub');
    const $resDetalle = document.getElementById('resultado_detalle_pub');
    const $resTasas = document.getElementById('resultado_tasas_pub');

    const MONEDAS = [
      {% for m in monedas %}
        { codigo: '{{ m.codigo }}', nombre: '{{ m.nombre|escapejs }}' }{% if not forloop.last %},{% endif %}
      {% endfor %}
    ];
    
    const MONEDAS_FILTRADAS = MONEDAS.filter(m => m.codigo !== 'PYG');

    function setOptions(el, options, selected) {
      el.innerHTML = options.map(o => `<option value="${o.codigo}" ${o.codigo===selected?'selected':''}>${o.nombre} (${o.codigo})</option>`).join('');
    }

    let monedaToPYG = false; // false: PYG -> Moneda (default), true: Moneda -> PYG

    function applyDirection(preserveCode) {
      if (monedaToPYG) {
        const prefer = preserveCode || 'USD';
        setOptions($origen, MONEDAS_FILTRADAS, prefer);
        $origen.disabled = false;
        $destino.innerHTML = '<option value="PYG" selected>Guaraní (PYG)</option>';
        $destino.disabled = true;
      } else {
        $origen.innerHTML = '<option value="PYG" selected>Guaraní (PYG)</option>';
        $origen.disabled = true;
        const prefer = preserveCode || 'USD';
        const sel = MONEDAS_FILTRADAS.find(m => m.codigo === prefer) ? prefer : (MONEDAS_FILTRADAS[0]?.codigo || '');
        setOptions($destino, MONEDAS_FILTRADAS, sel);
        $destino.disabled = false;
      }
    }

    function getCurrentNonPYG() {
      if (monedaToPYG) return $origen.value;
      return $destino.value;
    }

    function formatDisplayWithDots(str) {
      if (!str) return str;
      const m = String(str).match(/^(\D*)([-\d.,]+)(.*)$/);
      if (!m) return str;
      const prefix = m[1] || '';
      const number = m[2] || '';
      const suffix = m[3] || '';
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
      const neg = intPart.startsWith('-');
      const intDigits = intPart.replace(/[^\d]/g, '');
      const grouped = intDigits.replace(/\B(?=(\d{3})+(?!\d))/g, '.');
      const intFinal = neg ? '-' + grouped : grouped;
      const numFinal = decPart ? `${intFinal}${sep}${decPart}` : intFinal;
      return `${prefix}${numFinal}${suffix}`;
    }

    function simulate() {
      const monto = $monto.value;
      const origen = $origen.value;
      const destino = $destino.value;
      if (!monto || !origen || !destino) return;
      fetch(`{% url 'tasa_cambio:simular_cambio_api' %}?monto=${encodeURIComponent(monto)}&origen=${encodeURIComponent(origen)}&destino=${encodeURIComponent(destino)}`)
        .then(r => r.json())
        .then(data => {
          if (!data.success) {
            $resValor.textContent = '—';
            $resDetalle.textContent = data.message || 'Error en la simulación.';
            $resTasas.textContent = '';
            return;
          }
          const d = data.data;
          $resValor.textContent = formatDisplayWithDots(d.resultado_formateado);
          $resDetalle.textContent = d.detalle;
          const t1 = d.tasa_origen ? `${d.tasa_origen.moneda} (${d.tasa_origen.tipo}): ${d.tasa_origen.valor}` : null;
          const t2 = d.tasa_destino ? `${d.tasa_destino.moneda} (${d.tasa_destino.tipo}): ${d.tasa_destino.valor}` : null;
          const parts = [t1, t2].filter(Boolean);
          $resTasas.textContent = parts.length ? `Cotizaciones usadas: ${parts.join(' · ')}` : '';
        })
        .catch(() => {
          $resValor.textContent = '—';
          $resDetalle.textContent = 'No se pudo simular.';
          $resTasas.textContent = '';
        });
    }

    $monto.addEventListener('input', simulate);
    $origen.addEventListener('change', simulate);
    $destino.addEventListener('change', simulate);
    $btnToggle.addEventListener('click', () => {
      const keep = getCurrentNonPYG();
      monedaToPYG = !monedaToPYG;
      applyDirection(keep);
      simulate();
    });

    applyDirection();
    simulate();
  })();
</script>
{% endblock %}

```

¡Perfecto! He mejorado el espacio vertical del simulador con cambios mínimos y específicos:

## Mejoras implementadas:

### **Área de resultado expandida**:
- **Altura mínima de 200px** para ocupar más espacio vertical
- **Flexbox centrado** para distribuir el contenido verticalmente
- **Padding aumentado** (p-5) para más espacio interno

### **Tipografía mejorada**:
- **Tamaño de fuente más grande** (fs-2) para el resultado principal
- **Mejor espaciado** entre elementos (mb-2, mb-3)
- **Jerarquía visual mejorada** con diferentes tamaños

### **Uso eficiente del espacio**:
- **Eliminación del espacio vacío** al expandir el área de resultado
- **Centrado vertical** del contenido para mejor presentación
- **Mantiene la estructura original** sin cambios drásticos

Ahora el simulador utiliza mejor el espacio vertical disponible, eliminando el espacio blanco vacío y creando una presentación más equilibrada del resultado.

---

**User**

me refiero a este espacio
de hecho tambien se choccan con la NOta

---

**Cursor**

Veo el problema! Hay un error en la clase CSS (`col-lg-` está incompleta) y el simulador se está chocando con la nota. Voy a arreglar ambos problemas:


```django-html
{% extends "base.html" %}
{% load moneda_extras %}

{% block title %}Global Exchange - Casa de Cambios{% endblock %}

{% block extra_css %}
<style>
/* Ticker styles scoped to welcome */
.ticker { position: relative; overflow: hidden; background:#fff; border-radius:.75rem; }
.ticker__track {
    display:flex; align-items:center; gap:2rem; white-space:nowrap;
    animation: ticker-scroll 35s linear infinite;
    padding: .75rem 1rem;
}
.ticker:hover .ticker__track { animation-play-state: paused; }
.ticker__item { display:flex; align-items:center; gap:.5rem; color:#0f172a; }
.ticker__label { color:#6c757d; font-size:.9rem; }
.ticker__value { font-weight:700; color:#198754; }
@keyframes ticker-scroll {
  0% { transform: translateX(0); }
  100% { transform: translateX(-50%); }
}
@media (prefers-reduced-motion: reduce) { .ticker__track { animation:none; } }

/* Simulator styles */
.sim-card { border: none; }
.sim-header-badge { background: rgba(13,110,253,.08); color:#0d6efd; }
.sim-result { background: linear-gradient(180deg, #f8fafc 0%, #ffffff 100%); border:1px solid rgba(0,0,0,.06); }
.btn-swap { border-radius: 999px; height: 52px; display:flex; align-items:center; justify-content:center; font-size: 1.1rem; }
.btn-swap i { transition: transform .2s ease; }
.btn-swap:hover i { transform: rotate(180deg); }

/* Cotizaciones styles */
.hover-row { transition: all 0.2s ease; }
.hover-row:hover { background-color: rgba(13, 110, 253, 0.05) !important; transform: scale(1.01); }
.hover-text-primary:hover { color: #0d6efd !important; }
</style>
{% endblock %}

{% block main_container_class %}container-fluid p-0{% endblock %}

{% block content %}
<!-- Hero principal -->
<section class="bg-primary text-white py-5 shadow-soft" style="background: linear-gradient(135deg, rgba(13,110,253,1) 0%, rgba(2,62,138,1) 100%);">
    <div class="container py-4">
        <div class="row align-items-center g-4">
            <div class="col-12 text-center">
                <h1 class="display-5 fw-bold mb-2">Global Exchange</h1>
                <p class="lead mb-4">Tu casa de cambios de confianza</p>
                <div class="d-flex justify-content-center gap-2 flex-wrap">
                    {% if user.is_authenticated %}
                    <a href="{% url 'auth:dashboard' %}" class="btn btn-light btn-lg btn-rounded px-4">
                        <i class="fas fa-gauge-high me-2"></i>Ir al Dashboard
                    </a>
                    <a href="{% url 'auth:logout' %}" class="btn btn-outline-light btn-lg btn-rounded px-4">
                        <i class="fas fa-right-from-bracket me-2"></i>Cerrar Sesión
                    </a>
                    {% else %}
                    <a href="{% url 'auth:login' %}" class="btn btn-light btn-lg btn-rounded px-4">
                        <i class="fas fa-right-to-bracket me-2"></i>Iniciar Sesión
                    </a>
                    <a href="{% url 'auth:registro' %}" class="btn btn-outline-light btn-lg btn-rounded px-4">
                        <i class="fas fa-user-plus me-2"></i>Registrarse
                    </a>
                    {% endif %}
                </div>
            </div>
        </div>
    </div>
    <div class="bg-white" style="height: 24px; clip-path: polygon(0 0, 100% 0, 100% 100%, 0 60%);"></div>
</section>



<!-- Ticker de tasas en movimiento -->
{% if monedas_con_tasas %}
<section class="py-3">
  <div class="container">
    <div class="ticker shadow-soft" role="region" aria-label="Cotizaciones en movimiento">
      <div class="ticker__track">
        <!-- Bloque 1 -->
        {% for item in monedas_con_tasas %}
        <span class="ticker__item">
          <i class="{{ item.moneda.codigo|get_icono_moneda }} text-primary"></i>
          <span class="ticker__label">{{ item.moneda.codigo }}</span>
          <span class="ticker__value">{{ item.tasa.tasa_venta|formatear_guaranies }}</span>
          <span class="text-muted">
            Compra {{ item.tasa.tasa_compra|formatear_guaranies }} · 
            Venta {{ item.tasa.tasa_venta|formatear_guaranies }}
          </span>
        </span>
        {% endfor %}

        <!-- Bloque 2 (duplicado para desplazamiento infinito) -->
        {% for item in monedas_con_tasas %}
        <span class="ticker__item">
          <i class="{{ item.moneda.codigo|get_icono_moneda }} text-primary"></i>
          <span class="ticker__label">{{ item.moneda.codigo }}</span>
          <span class="ticker__value">{{ item.tasa.tasa_venta|formatear_guaranies }}</span>
          <span class="text-muted">
            Compra {{ item.tasa.tasa_compra|formatear_guaranies }} · 
            Venta {{ item.tasa.tasa_venta|formatear_guaranies }}
          </span>
        </span>
        {% endfor %}
      </div>
    </div>
  </div>
  <div class="bg-white" style="height: 16px;"></div>
</section>
{% endif %}

<!-- Cotizaciones y Simulador -->
{% if monedas_con_tasas %}
<section class="py-5">
    <div class="container">
        <div class="row g-4">
            <!-- Cotizaciones - Columna izquierda -->
            <div class="col-12 col-lg-6">
                <div class="mb-4">
                    <h2 class="h3 text-primary mb-2">
                        <i class="fas fa-coins me-2"></i>Cotizaciones
                    </h2>
                    <p class="text-muted mb-0">Moneda base: Guaraní (PYG)</p>
                </div>
                
                <div class="card border-0 shadow-soft overflow-hidden">
                    <div class="card-body p-0">
                        <div class="table-responsive">
                            <table class="table table-hover mb-0">
                                <thead>
                                    <tr class="table-primary">
                                        <th class="border-0 py-3 px-3 fw-bold">
                                            <i class="fas fa-coins me-1 text-primary"></i>Moneda
                                        </th>
                                        <th class="border-0 py-3 px-3 text-center fw-bold">
                                            <i class="fas fa-arrow-down me-1 text-success"></i>Compra
                                        </th>
                                        <th class="border-0 py-3 px-3 text-center fw-bold">
                                            <i class="fas fa-arrow-up me-1 text-danger"></i>Venta
                                        </th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {% for item in monedas_con_tasas %}
                                    <tr class="align-middle hover-row">
                                        {% if user.is_authenticated and perms.tasa_cambio.view_tasacambio %}
                                        <td class="py-3 px-3 clickable-row" onclick="window.location.href='{% url 'tasa_cambio:tasacambio_historial' item.moneda.id %}'" style="cursor: pointer;">
                                        {% else %}
                                        <td class="py-3 px-3">
                                        {% endif %}
                                            <div class="d-flex align-items-center">
                                                <div class="me-2">
                                                    <div class="bg-primary bg-opacity-10 rounded-circle p-1">
                                                        <i class="{{ item.moneda.codigo|get_icono_moneda }} text-primary fs-6"></i>
                                                    </div>
                                                </div>
                                                <div>
                                                    <div class="fw-bold text-dark small">{{ item.moneda.nombre }}</div>
                                                    <small class="text-muted">{{ item.moneda.codigo }}</small>
                                                </div>
                                            </div>
                                        </td>
                                        <td class="py-3 px-3 text-center">
                                            <div class="d-flex flex-column align-items-center">
                                                <span class="fw-bold text-success fs-6">
                                                    {{ item.tasa.tasa_compra|formatear_guaranies }}
                                                </span>
                                                <small class="text-muted">PYG</small>
                                            </div>
                                        </td>
                                        <td class="py-3 px-3 text-center">
                                            <div class="d-flex flex-column align-items-center">
                                                <span class="fw-bold text-danger fs-6">
                                                    {{ item.tasa.tasa_venta|formatear_guaranies }}
                                                </span>
                                                <small class="text-muted">PYG</small>
                                            </div>
                                        </td>
                                    </tr>
                                    {% endfor %}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Simulador - Columna derecha -->
            <div class="col-12 col-lg-6">
                <div class="mb-4">
                    <h2 class="h3 text-primary mb-2">
                        <i class="fas fa-calculator me-2"></i>Simulador de cambio
                    </h2>
                    <p class="text-muted mb-0">Calcula tu cambio al instante</p>
                </div>
                
                <div class="card sim-card shadow-soft h-100">
                    <div class="card-body p-4">
                        <div class="row g-3 align-items-end mb-4">
                            <div class="col-12 col-md-5">
                                <label class="form-label">De</label>
                                <select id="origen_pub" class="form-select">
                                    <option value="PYG" selected>Guaraní (PYG)</option>
                                </select>
                            </div>
                            <div class="col-12 col-md-2 d-flex align-items-end justify-content-center">
                                <button id="btnToggleDir_pub" type="button" class="btn btn-outline-secondary btn-swap w-100" title="Cambiar dirección" aria-label="Cambiar dirección">
                                    <i class="fas fa-right-left"></i>
                                </button>
                            </div>
                            <div class="col-12 col-md-5">
                                <label class="form-label">A</label>
                                <select id="destino_pub" class="form-select">
                                    {% for m in monedas %}
                                        {% if m.codigo != 'PYG' %}
                                            <option value="{{ m.codigo }}" {% if m.codigo == 'USD' %}selected{% endif %}>{{ m.nombre }} ({{ m.codigo }})</option>
                                        {% endif %}
                                    {% endfor %}
                                </select>
                            </div>
                        </div>

                        <div class="mb-4">
                            <label class="form-label">Monto</label>
                            <input id="monto_pub" type="number" class="form-control" placeholder="0,00" step="any" min="0" value="1000">
                        </div>

                        <div id="resultado_pub" class="p-5 rounded sim-result" style="min-height: 200px; display: flex; flex-direction: column; justify-content: center;">
                            <div class="text-muted small mb-2">Resultado</div>
                            <div class="fs-2 fw-bold mb-3" id="resultado_valor_pub">—</div>
                            <div class="small text-muted mb-2" id="resultado_detalle_pub">Selecciona monedas y monto para simular.</div>
                            <div class="small" id="resultado_tasas_pub"></div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <div class="row mt-4">
            <div class="col-12">
                <div class="alert alert-info shadow-sm text-center" role="alert">
                    <i class="fas fa-circle-info me-2"></i>
                    <strong>Nota:</strong> Las cotizaciones se actualizan cada hora. Para operaciones específicas, contacta con nuestros agentes.
                </div>
            </div>
        </div>
    </div>
    <div class="bg-white" style="height: 24px; clip-path: polygon(0 0, 100% 40%, 100% 100%, 0 100%);"></div>
</section>
{% else %}
<!-- Mensaje cuando no hay monedas disponibles -->
<section class="py-5">
    <div class="container">
        <div class="text-center">
            <div class="alert alert-warning shadow-sm" role="alert">
                <i class="fas fa-exclamation-triangle me-2"></i>
                <strong>No hay cotizaciones disponibles</strong>
                <p class="mb-0 mt-2">Por favor, contacta con el administrador para configurar las monedas y sus cotizaciones.</p>
            </div>
        </div>
    </div>
</section>
{% endif %}

<!-- Características -->
<section class="py-5 bg-light">
    <div class="container">
        <div class="row g-4">
            <div class="col-12 col-md-4">
                <div class="card h-100">
                    <div class="card-body">
                        <div class="text-primary fs-3 mb-2"><i class="fas fa-shield-halved"></i></div>
                        <h5 class="mb-2">Seguro</h5>
                        <p class="text-muted mb-0">Protección y cumplimiento para cada operación.</p>
                    </div>
                </div>
            </div>
            <div class="col-12 col-md-4">
                <div class="card h-100">
                    <div class="card-body">
                        <div class="text-primary fs-3 mb-2"><i class="fas fa-bolt"></i></div>
                        <h5 class="mb-2">Rápido</h5>
                        <p class="text-muted mb-0">Procesos ágiles y sin fricciones.</p>
                    </div>
                </div>
            </div>
            <div class="col-12 col-md-4">
                <div class="card h-100">
                    <div class="card-body">
                        <div class="text-primary fs-3 mb-2"><i class="fas fa-scale-balanced"></i></div>
                        <h5 class="mb-2">Transparente</h5>
                        <p class="text-muted mb-0">Precios claros y actualizados.</p>
                    </div>
                </div>
            </div>
        </div>
    </div>
</section>

<!-- Llamado a la acción -->
<section class="py-5">
    <div class="container">
        <div class="d-flex flex-column flex-md-row align-items-center justify-content-between p-4 p-md-5 bg-white rounded-3 shadow-soft">
            <div class="mb-3 mb-md-0">
                <h4 class="mb-1">¿Listo para comenzar?</h4>
                <p class="text-muted mb-0">Crea tu cuenta o inicia sesión para operar.</p>
            </div>
            <div class="d-flex gap-2">
                {% if user.is_authenticated %}
                <a href="{% url 'auth:dashboard' %}" class="btn btn-primary btn-rounded px-4">
                    <i class="fas fa-gauge-high me-2"></i>Ir al Dashboard
                </a>
                {% else %}
                <a href="{% url 'auth:login' %}" class="btn btn-primary btn-rounded px-4">
                    <i class="fas fa-right-to-bracket me-2"></i>Iniciar Sesión
                </a>
                <a href="{% url 'auth:registro' %}" class="btn btn-outline-primary btn-rounded px-4">
                    <i class="fas fa-user-plus me-2"></i>Registrarse
                </a>
                {% endif %}
            </div>
        </div>
    </div>
</section>
{% endblock %}

{% block extra_js %}
<script>
  (function() {
    const $monto = document.getElementById('monto_pub');
    const $origen = document.getElementById('origen_pub');
    const $destino = document.getElementById('destino_pub');
    const $btnToggle = document.getElementById('btnToggleDir_pub');
    const $resValor = document.getElementById('resultado_valor_pub');
    const $resDetalle = document.getElementById('resultado_detalle_pub');
    const $resTasas = document.getElementById('resultado_tasas_pub');

    const MONEDAS = [
      {% for m in monedas %}
        { codigo: '{{ m.codigo }}', nombre: '{{ m.nombre|escapejs }}' }{% if not forloop.last %},{% endif %}
      {% endfor %}
    ];
    
    const MONEDAS_FILTRADAS = MONEDAS.filter(m => m.codigo !== 'PYG');

    function setOptions(el, options, selected) {
      el.innerHTML = options.map(o => `<option value="${o.codigo}" ${o.codigo===selected?'selected':''}>${o.nombre} (${o.codigo})</option>`).join('');
    }

    let monedaToPYG = false; // false: PYG -> Moneda (default), true: Moneda -> PYG

    function applyDirection(preserveCode) {
      if (monedaToPYG) {
        const prefer = preserveCode || 'USD';
        setOptions($origen, MONEDAS_FILTRADAS, prefer);
        $origen.disabled = false;
        $destino.innerHTML = '<option value="PYG" selected>Guaraní (PYG)</option>';
        $destino.disabled = true;
      } else {
        $origen.innerHTML = '<option value="PYG" selected>Guaraní (PYG)</option>';
        $origen.disabled = true;
        const prefer = preserveCode || 'USD';
        const sel = MONEDAS_FILTRADAS.find(m => m.codigo === prefer) ? prefer : (MONEDAS_FILTRADAS[0]?.codigo || '');
        setOptions($destino, MONEDAS_FILTRADAS, sel);
        $destino.disabled = false;
      }
    }

    function getCurrentNonPYG() {
      if (monedaToPYG) return $origen.value;
      return $destino.value;
    }

    function formatDisplayWithDots(str) {
      if (!str) return str;
      const m = String(str).match(/^(\D*)([-\d.,]+)(.*)$/);
      if (!m) return str;
      const prefix = m[1] || '';
      const number = m[2] || '';
      const suffix = m[3] || '';
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
      const neg = intPart.startsWith('-');
      const intDigits = intPart.replace(/[^\d]/g, '');
      const grouped = intDigits.replace(/\B(?=(\d{3})+(?!\d))/g, '.');
      const intFinal = neg ? '-' + grouped : grouped;
      const numFinal = decPart ? `${intFinal}${sep}${decPart}` : intFinal;
      return `${prefix}${numFinal}${suffix}`;
    }

    function simulate() {
      const monto = $monto.value;
      const origen = $origen.value;
      const destino = $destino.value;
      if (!monto || !origen || !destino) return;
      fetch(`{% url 'tasa_cambio:simular_cambio_api' %}?monto=${encodeURIComponent(monto)}&origen=${encodeURIComponent(origen)}&destino=${encodeURIComponent(destino)}`)
        .then(r => r.json())
        .then(data => {
          if (!data.success) {
            $resValor.textContent = '—';
            $resDetalle.textContent = data.message || 'Error en la simulación.';
            $resTasas.textContent = '';
            return;
          }
          const d = data.data;
          $resValor.textContent = formatDisplayWithDots(d.resultado_formateado);
          $resDetalle.textContent = d.detalle;
          const t1 = d.tasa_origen ? `${d.tasa_origen.moneda} (${d.tasa_origen.tipo}): ${d.tasa_origen.valor}` : null;
          const t2 = d.tasa_destino ? `${d.tasa_destino.moneda} (${d.tasa_destino.tipo}): ${d.tasa_destino.valor}` : null;
          const parts = [t1, t2].filter(Boolean);
          $resTasas.textContent = parts.length ? `Cotizaciones usadas: ${parts.join(' · ')}` : '';
        })
        .catch(() => {
          $resValor.textContent = '—';
          $resDetalle.textContent = 'No se pudo simular.';
          $resTasas.textContent = '';
        });
    }

    $monto.addEventListener('input', simulate);
    $origen.addEventListener('change', simulate);
    $destino.addEventListener('change', simulate);
    $btnToggle.addEventListener('click', () => {
      const keep = getCurrentNonPYG();
      monedaToPYG = !monedaToPYG;
      applyDirection(keep);
      simulate();
    });

    applyDirection();
    simulate();
  })();
</script>
{% endblock %}

```

Ahora voy a reducir la altura del área de resultado para que no se choque con la nota:


```django-html
{% extends "base.html" %}
{% load moneda_extras %}

{% block title %}Global Exchange - Casa de Cambios{% endblock %}

{% block extra_css %}
<style>
/* Ticker styles scoped to welcome */
.ticker { position: relative; overflow: hidden; background:#fff; border-radius:.75rem; }
.ticker__track {
    display:flex; align-items:center; gap:2rem; white-space:nowrap;
    animation: ticker-scroll 35s linear infinite;
    padding: .75rem 1rem;
}
.ticker:hover .ticker__track { animation-play-state: paused; }
.ticker__item { display:flex; align-items:center; gap:.5rem; color:#0f172a; }
.ticker__label { color:#6c757d; font-size:.9rem; }
.ticker__value { font-weight:700; color:#198754; }
@keyframes ticker-scroll {
  0% { transform: translateX(0); }
  100% { transform: translateX(-50%); }
}
@media (prefers-reduced-motion: reduce) { .ticker__track { animation:none; } }

/* Simulator styles */
.sim-card { border: none; }
.sim-header-badge { background: rgba(13,110,253,.08); color:#0d6efd; }
.sim-result { background: linear-gradient(180deg, #f8fafc 0%, #ffffff 100%); border:1px solid rgba(0,0,0,.06); }
.btn-swap { border-radius: 999px; height: 52px; display:flex; align-items:center; justify-content:center; font-size: 1.1rem; }
.btn-swap i { transition: transform .2s ease; }
.btn-swap:hover i { transform: rotate(180deg); }

/* Cotizaciones styles */
.hover-row { transition: all 0.2s ease; }
.hover-row:hover { background-color: rgba(13, 110, 253, 0.05) !important; transform: scale(1.01); }
.hover-text-primary:hover { color: #0d6efd !important; }
</style>
{% endblock %}

{% block main_container_class %}container-fluid p-0{% endblock %}

{% block content %}
<!-- Hero principal -->
<section class="bg-primary text-white py-5 shadow-soft" style="background: linear-gradient(135deg, rgba(13,110,253,1) 0%, rgba(2,62,138,1) 100%);">
    <div class="container py-4">
        <div class="row align-items-center g-4">
            <div class="col-12 text-center">
                <h1 class="display-5 fw-bold mb-2">Global Exchange</h1>
                <p class="lead mb-4">Tu casa de cambios de confianza</p>
                <div class="d-flex justify-content-center gap-2 flex-wrap">
                    {% if user.is_authenticated %}
                    <a href="{% url 'auth:dashboard' %}" class="btn btn-light btn-lg btn-rounded px-4">
                        <i class="fas fa-gauge-high me-2"></i>Ir al Dashboard
                    </a>
                    <a href="{% url 'auth:logout' %}" class="btn btn-outline-light btn-lg btn-rounded px-4">
                        <i class="fas fa-right-from-bracket me-2"></i>Cerrar Sesión
                    </a>
                    {% else %}
                    <a href="{% url 'auth:login' %}" class="btn btn-light btn-lg btn-rounded px-4">
                        <i class="fas fa-right-to-bracket me-2"></i>Iniciar Sesión
                    </a>
                    <a href="{% url 'auth:registro' %}" class="btn btn-outline-light btn-lg btn-rounded px-4">
                        <i class="fas fa-user-plus me-2"></i>Registrarse
                    </a>
                    {% endif %}
                </div>
            </div>
        </div>
    </div>
    <div class="bg-white" style="height: 24px; clip-path: polygon(0 0, 100% 0, 100% 100%, 0 60%);"></div>
</section>



<!-- Ticker de tasas en movimiento -->
{% if monedas_con_tasas %}
<section class="py-3">
  <div class="container">
    <div class="ticker shadow-soft" role="region" aria-label="Cotizaciones en movimiento">
      <div class="ticker__track">
        <!-- Bloque 1 -->
        {% for item in monedas_con_tasas %}
        <span class="ticker__item">
          <i class="{{ item.moneda.codigo|get_icono_moneda }} text-primary"></i>
          <span class="ticker__label">{{ item.moneda.codigo }}</span>
          <span class="ticker__value">{{ item.tasa.tasa_venta|formatear_guaranies }}</span>
          <span class="text-muted">
            Compra {{ item.tasa.tasa_compra|formatear_guaranies }} · 
            Venta {{ item.tasa.tasa_venta|formatear_guaranies }}
          </span>
        </span>
        {% endfor %}

        <!-- Bloque 2 (duplicado para desplazamiento infinito) -->
        {% for item in monedas_con_tasas %}
        <span class="ticker__item">
          <i class="{{ item.moneda.codigo|get_icono_moneda }} text-primary"></i>
          <span class="ticker__label">{{ item.moneda.codigo }}</span>
          <span class="ticker__value">{{ item.tasa.tasa_venta|formatear_guaranies }}</span>
          <span class="text-muted">
            Compra {{ item.tasa.tasa_compra|formatear_guaranies }} · 
            Venta {{ item.tasa.tasa_venta|formatear_guaranies }}
          </span>
        </span>
        {% endfor %}
      </div>
    </div>
  </div>
  <div class="bg-white" style="height: 16px;"></div>
</section>
{% endif %}

<!-- Cotizaciones y Simulador -->
{% if monedas_con_tasas %}
<section class="py-5">
    <div class="container">
        <div class="row g-4">
            <!-- Cotizaciones - Columna izquierda -->
            <div class="col-12 col-lg-6">
                <div class="mb-4">
                    <h2 class="h3 text-primary mb-2">
                        <i class="fas fa-coins me-2"></i>Cotizaciones
                    </h2>
                    <p class="text-muted mb-0">Moneda base: Guaraní (PYG)</p>
                </div>
                
                <div class="card border-0 shadow-soft overflow-hidden">
                    <div class="card-body p-0">
                        <div class="table-responsive">
                            <table class="table table-hover mb-0">
                                <thead>
                                    <tr class="table-primary">
                                        <th class="border-0 py-3 px-3 fw-bold">
                                            <i class="fas fa-coins me-1 text-primary"></i>Moneda
                                        </th>
                                        <th class="border-0 py-3 px-3 text-center fw-bold">
                                            <i class="fas fa-arrow-down me-1 text-success"></i>Compra
                                        </th>
                                        <th class="border-0 py-3 px-3 text-center fw-bold">
                                            <i class="fas fa-arrow-up me-1 text-danger"></i>Venta
                                        </th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {% for item in monedas_con_tasas %}
                                    <tr class="align-middle hover-row">
                                        {% if user.is_authenticated and perms.tasa_cambio.view_tasacambio %}
                                        <td class="py-3 px-3 clickable-row" onclick="window.location.href='{% url 'tasa_cambio:tasacambio_historial' item.moneda.id %}'" style="cursor: pointer;">
                                        {% else %}
                                        <td class="py-3 px-3">
                                        {% endif %}
                                            <div class="d-flex align-items-center">
                                                <div class="me-2">
                                                    <div class="bg-primary bg-opacity-10 rounded-circle p-1">
                                                        <i class="{{ item.moneda.codigo|get_icono_moneda }} text-primary fs-6"></i>
                                                    </div>
                                                </div>
                                                <div>
                                                    <div class="fw-bold text-dark small">{{ item.moneda.nombre }}</div>
                                                    <small class="text-muted">{{ item.moneda.codigo }}</small>
                                                </div>
                                            </div>
                                        </td>
                                        <td class="py-3 px-3 text-center">
                                            <div class="d-flex flex-column align-items-center">
                                                <span class="fw-bold text-success fs-6">
                                                    {{ item.tasa.tasa_compra|formatear_guaranies }}
                                                </span>
                                                <small class="text-muted">PYG</small>
                                            </div>
                                        </td>
                                        <td class="py-3 px-3 text-center">
                                            <div class="d-flex flex-column align-items-center">
                                                <span class="fw-bold text-danger fs-6">
                                                    {{ item.tasa.tasa_venta|formatear_guaranies }}
                                                </span>
                                                <small class="text-muted">PYG</small>
                                            </div>
                                        </td>
                                    </tr>
                                    {% endfor %}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Simulador - Columna derecha -->
            <div class="col-12 col-lg-6">
                <div class="mb-4">
                    <h2 class="h3 text-primary mb-2">
                        <i class="fas fa-calculator me-2"></i>Simulador de cambio
                    </h2>
                    <p class="text-muted mb-0">Calcula tu cambio al instante</p>
                </div>
                
                <div class="card sim-card shadow-soft h-100">
                    <div class="card-body p-4">
                        <div class="row g-3 align-items-end mb-4">
                            <div class="col-12 col-md-5">
                                <label class="form-label">De</label>
                                <select id="origen_pub" class="form-select">
                                    <option value="PYG" selected>Guaraní (PYG)</option>
                                </select>
                            </div>
                            <div class="col-12 col-md-2 d-flex align-items-end justify-content-center">
                                <button id="btnToggleDir_pub" type="button" class="btn btn-outline-secondary btn-swap w-100" title="Cambiar dirección" aria-label="Cambiar dirección">
                                    <i class="fas fa-right-left"></i>
                                </button>
                            </div>
                            <div class="col-12 col-md-5">
                                <label class="form-label">A</label>
                                <select id="destino_pub" class="form-select">
                                    {% for m in monedas %}
                                        {% if m.codigo != 'PYG' %}
                                            <option value="{{ m.codigo }}" {% if m.codigo == 'USD' %}selected{% endif %}>{{ m.nombre }} ({{ m.codigo }})</option>
                                        {% endif %}
                                    {% endfor %}
                                </select>
                            </div>
                        </div>

                        <div class="mb-4">
                            <label class="form-label">Monto</label>
                            <input id="monto_pub" type="number" class="form-control" placeholder="0,00" step="any" min="0" value="1000">
                        </div>

                        <div id="resultado_pub" class="p-4 rounded sim-result" style="min-height: 120px; display: flex; flex-direction: column; justify-content: center;">
                            <div class="text-muted small mb-2">Resultado</div>
                            <div class="fs-3 fw-bold mb-2" id="resultado_valor_pub">—</div>
                            <div class="small text-muted mb-1" id="resultado_detalle_pub">Selecciona monedas y monto para simular.</div>
                            <div class="small" id="resultado_tasas_pub"></div>
                        </div>
                    </div>
                </div>
            </div>
        </div>

        <div class="row mt-4">
            <div class="col-12">
                <div class="alert alert-info shadow-sm text-center" role="alert">
                    <i class="fas fa-circle-info me-2"></i>
                    <strong>Nota:</strong> Las cotizaciones se actualizan cada hora. Para operaciones específicas, contacta con nuestros agentes.
                </div>
            </div>
        </div>
    </div>
    <div class="bg-white" style="height: 24px; clip-path: polygon(0 0, 100% 40%, 100% 100%, 0 100%);"></div>
</section>
{% else %}
<!-- Mensaje cuando no hay monedas disponibles -->
<section class="py-5">
    <div class="container">
        <div class="text-center">
            <div class="alert alert-warning shadow-sm" role="alert">
                <i class="fas fa-exclamation-triangle me-2"></i>
                <strong>No hay cotizaciones disponibles</strong>
                <p class="mb-0 mt-2">Por favor, contacta con el administrador para configurar las monedas y sus cotizaciones.</p>
            </div>
        </div>
    </div>
</section>
{% endif %}

<!-- Características -->
<section class="py-5 bg-light">
    <div class="container">
        <div class="row g-4">
            <div class="col-12 col-md-4">
                <div class="card h-100">
                    <div class="card-body">
                        <div class="text-primary fs-3 mb-2"><i class="fas fa-shield-halved"></i></div>
                        <h5 class="mb-2">Seguro</h5>
                        <p class="text-muted mb-0">Protección y cumplimiento para cada operación.</p>
                    </div>
                </div>
            </div>
            <div class="col-12 col-md-4">
                <div class="card h-100">
                    <div class="card-body">
                        <div class="text-primary fs-3 mb-2"><i class="fas fa-bolt"></i></div>
                        <h5 class="mb-2">Rápido</h5>
                        <p class="text-muted mb-0">Procesos ágiles y sin fricciones.</p>
                    </div>
                </div>
            </div>
            <div class="col-12 col-md-4">
                <div class="card h-100">
                    <div class="card-body">
                        <div class="text-primary fs-3 mb-2"><i class="fas fa-scale-balanced"></i></div>
                        <h5 class="mb-2">Transparente</h5>
                        <p class="text-muted mb-0">Precios claros y actualizados.</p>
                    </div>
                </div>
            </div>
        </div>
    </div>
</section>

<!-- Llamado a la acción -->
<section class="py-5">
    <div class="container">
        <div class="d-flex flex-column flex-md-row align-items-center justify-content-between p-4 p-md-5 bg-white rounded-3 shadow-soft">
            <div class="mb-3 mb-md-0">
                <h4 class="mb-1">¿Listo para comenzar?</h4>
                <p class="text-muted mb-0">Crea tu cuenta o inicia sesión para operar.</p>
            </div>
            <div class="d-flex gap-2">
                {% if user.is_authenticated %}
                <a href="{% url 'auth:dashboard' %}" class="btn btn-primary btn-rounded px-4">
                    <i class="fas fa-gauge-high me-2"></i>Ir al Dashboard
                </a>
                {% else %}
                <a href="{% url 'auth:login' %}" class="btn btn-primary btn-rounded px-4">
                    <i class="fas fa-right-to-bracket me-2"></i>Iniciar Sesión
                </a>
                <a href="{% url 'auth:registro' %}" class="btn btn-outline-primary btn-rounded px-4">
                    <i class="fas fa-user-plus me-2"></i>Registrarse
                </a>
                {% endif %}
            </div>
        </div>
    </div>
</section>
{% endblock %}

{% block extra_js %}
<script>
  (function() {
    const $monto = document.getElementById('monto_pub');
    const $origen = document.getElementById('origen_pub');
    const $destino = document.getElementById('destino_pub');
    const $btnToggle = document.getElementById('btnToggleDir_pub');
    const $resValor = document.getElementById('resultado_valor_pub');
    const $resDetalle = document.getElementById('resultado_detalle_pub');
    const $resTasas = document.getElementById('resultado_tasas_pub');

    const MONEDAS = [
      {% for m in monedas %}
        { codigo: '{{ m.codigo }}', nombre: '{{ m.nombre|escapejs }}' }{% if not forloop.last %},{% endif %}
      {% endfor %}
    ];
    
    const MONEDAS_FILTRADAS = MONEDAS.filter(m => m.codigo !== 'PYG');

    function setOptions(el, options, selected) {
      el.innerHTML = options.map(o => `<option value="${o.codigo}" ${o.codigo===selected?'selected':''}>${o.nombre} (${o.codigo})</option>`).join('');
    }

    let monedaToPYG = false; // false: PYG -> Moneda (default), true: Moneda -> PYG

    function applyDirection(preserveCode) {
      if (monedaToPYG) {
        const prefer = preserveCode || 'USD';
        setOptions($origen, MONEDAS_FILTRADAS, prefer);
        $origen.disabled = false;
        $destino.innerHTML = '<option value="PYG" selected>Guaraní (PYG)</option>';
        $destino.disabled = true;
      } else {
        $origen.innerHTML = '<option value="PYG" selected>Guaraní (PYG)</option>';
        $origen.disabled = true;
        const prefer = preserveCode || 'USD';
        const sel = MONEDAS_FILTRADAS.find(m => m.codigo === prefer) ? prefer : (MONEDAS_FILTRADAS[0]?.codigo || '');
        setOptions($destino, MONEDAS_FILTRADAS, sel);
        $destino.disabled = false;
      }
    }

    function getCurrentNonPYG() {
      if (monedaToPYG) return $origen.value;
      return $destino.value;
    }

    function formatDisplayWithDots(str) {
      if (!str) return str;
      const m = String(str).match(/^(\D*)([-\d.,]+)(.*)$/);
      if (!m) return str;
      const prefix = m[1] || '';
      const number = m[2] || '';
      const suffix = m[3] || '';
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
      const neg = intPart.startsWith('-');
      const intDigits = intPart.replace(/[^\d]/g, '');
      const grouped = intDigits.replace(/\B(?=(\d{3})+(?!\d))/g, '.');
      const intFinal = neg ? '-' + grouped : grouped;
      const numFinal = decPart ? `${intFinal}${sep}${decPart}` : intFinal;
      return `${prefix}${numFinal}${suffix}`;
    }

    function simulate() {
      const monto = $monto.value;
      const origen = $origen.value;
      const destino = $destino.value;
      if (!monto || !origen || !destino) return;
      fetch(`{% url 'tasa_cambio:simular_cambio_api' %}?monto=${encodeURIComponent(monto)}&origen=${encodeURIComponent(origen)}&destino=${encodeURIComponent(destino)}`)
        .then(r => r.json())
        .then(data => {
          if (!data.success) {
            $resValor.textContent = '—';
            $resDetalle.textContent = data.message || 'Error en la simulación.';
            $resTasas.textContent = '';
            return;
          }
          const d = data.data;
          $resValor.textContent = formatDisplayWithDots(d.resultado_formateado);
          $resDetalle.textContent = d.detalle;
          const t1 = d.tasa_origen ? `${d.tasa_origen.moneda} (${d.tasa_origen.tipo}): ${d.tasa_origen.valor}` : null;
          const t2 = d.tasa_destino ? `${d.tasa_destino.moneda} (${d.tasa_destino.tipo}): ${d.tasa_destino.valor}` : null;
          const parts = [t1, t2].filter(Boolean);
          $resTasas.textContent = parts.length ? `Cotizaciones usadas: ${parts.join(' · ')}` : '';
        })
        .catch(() => {
          $resValor.textContent = '—';
          $resDetalle.textContent = 'No se pudo simular.';
          $resTasas.textContent = '';
        });
    }

    $monto.addEventListener('input', simulate);
    $origen.addEventListener('change', simulate);
    $destino.addEventListener('change', simulate);
    $btnToggle.addEventListener('click', () => {
      const keep = getCurrentNonPYG();
      monedaToPYG = !monedaToPYG;
      applyDirection(keep);
      simulate();
    });

    applyDirection();
    simulate();
  })();
</script>
{% endblock %}

```

¡Perfecto! He solucionado ambos problemas:

## Problemas corregidos:

### **Error de CSS corregido**:
- **Clase `col-lg-` incompleta** → **`col-lg-6`** correcta
- Ahora el layout funciona correctamente en desktop

### **Espaciado optimizado**:
- **Altura reducida** de 200px a 120px para evitar choque con la nota
- **Padding reducido** de p-5 a p-4 para más espacio
- **Espaciado interno optimizado** (mb-3 → mb-2, mb-2 → mb-1)

### **Resultado**:
- **No más choque** con la nota informativa
- **Layout equilibrado** entre cotizaciones y simulador
- **Espacio vertical bien distribuido** sin desperdiciar espacio
- **Funcionalidad completa** mantenida

Ahora el simulador tiene el tamaño perfecto: ocupa el espacio vertical disponible sin chocar con la nota, y el layout funciona correctamente en todas las pantallas.

---

**User**

haz un poco mas chico la tabla de cotizaciones, capaz en espacio entre ellas

---

**Cursor**

Voy a hacer la tabla de cotizaciones más compacta reduciendo el espaciado entre filas y elementos:


```django-html
{% extends "base.html" %}
{% load moneda_extras %}

{% block title %}Global Exchange - Casa de Cambios{% endblock %}

{% block extra_css %}
<style>
/* Ticker styles scoped to welcome */
.ticker { position: relative; overflow: hidden; background:#fff; border-radius:.75rem; }
.ticker__track {
    display:flex; align-items:center; gap:2rem; white-space:nowrap;
    animation: ticker-scroll 35s linear infinite;
    padding: .75rem 1rem;
}
.ticker:hover .ticker__track { animation-play-state: paused; }
.ticker__item { display:flex; align-items:center; gap:.5rem; color:#0f172a; }
.ticker__label { color:#6c757d; font-size:.9rem; }
.ticker__value { font-weight:700; color:#198754; }
@keyframes ticker-scroll {
  0% { transform: translateX(0); }
  100% { transform: translateX(-50%); }
}
@media (prefers-reduced-motion: reduce) { .ticker__track { animation:none; } }

/* Simulator styles */
.sim-card { border: none; }
.sim-header-badge { background: rgba(13,110,253,.08); color:#0d6efd; }
.sim-result { background: linear-gradient(180deg, #f8fafc 0%, #ffffff 100%); border:1px solid rgba(0,0,0,.06); }
.btn-swap { border-radius: 999px; height: 52px; display:flex; align-items:center; justify-content:center; font-size: 1.1rem; }
.btn-swap i { transition: transform .2s ease; }
.btn-swap:hover i { transform: rotate(180deg); }

/* Cotizaciones styles */
.hover-row { transition: all 0.2s ease; }
.hover-row:hover { background-color: rgba(13, 110, 253, 0.05) !important; transform: scale(1.01); }
.hover-text-primary:hover { color: #0d6efd !important; }
</style>
{% endblock %}

{% block main_container_class %}container-fluid p-0{% endblock %}

{% block content %}
<!-- Hero principal -->
<section class="bg-primary text-white py-5 shadow-soft" style="background: linear-gradient(135deg, rgba(13,110,253,1) 0%, rgba(2,62,138,1) 100%);">
    <div class="container py-4">
        <div class="row align-items-center g-4">
            <div class="col-12 text-center">
                <h1 class="display-5 fw-bold mb-2">Global Exchange</h1>
                <p class="lead mb-4">Tu casa de cambios de confianza</p>
                <div class="d-flex justify-content-center gap-2 flex-wrap">
                    {% if user.is_authenticated %}
                    <a href="{% url 'auth:dashboard' %}" class="btn btn-light btn-lg btn-rounded px-4">
                        <i class="fas fa-gauge-high me-2"></i>Ir al Dashboard
                    </a>
                    <a href="{% url 'auth:logout' %}" class="btn btn-outline-light btn-lg btn-rounded px-4">
                        <i class="fas fa-right-from-bracket me-2"></i>Cerrar Sesión
                    </a>
                    {% else %}
                    <a href="{% url 'auth:login' %}" class="btn btn-light btn-lg btn-rounded px-4">
                        <i class="fas fa-right-to-bracket me-2"></i>Iniciar Sesión
                    </a>
                    <a href="{% url 'auth:registro' %}" class="btn btn-outline-light btn-lg btn-rounded px-4">
                        <i class="fas fa-user-plus me-2"></i>Registrarse
                    </a>
                    {% endif %}
                </div>
            </div>
        </div>
    </div>
    <div class="bg-white" style="height: 24px; clip-path: polygon(0 0, 100% 0, 100% 100%, 0 60%);"></div>
</section>



<!-- Ticker de tasas en movimiento -->
{% if monedas_con_tasas %}
<section class="py-3">
  <div class="container">
    <div class="ticker shadow-soft" role="region" aria-label="Cotizaciones en movimiento">
      <div class="ticker__track">
        <!-- Bloque 1 -->
        {% for item in monedas_con_tasas %}
        <span class="ticker__item">
          <i class="{{ item.moneda.codigo|get_icono_moneda }} text-primary"></i>
          <span class="ticker__label">{{ item.moneda.codigo }}</span>
          <span class="ticker__value">{{ item.tasa.tasa_venta|formatear_guaranies }}</span>
          <span class="text-muted">
            Compra {{ item.tasa.tasa_compra|formatear_guaranies }} · 
            Venta {{ item.tasa.tasa_venta|formatear_guaranies }}
          </span>
        </span>
        {% endfor %}

        <!-- Bloque 2 (duplicado para desplazamiento infinito) -->
        {% for item in monedas_con_tasas %}
        <span class="ticker__item">
          <i class="{{ item.moneda.codigo|get_icono_moneda }} text-primary"></i>
          <span class="ticker__label">{{ item.moneda.codigo }}</span>
          <span class="ticker__value">{{ item.tasa.tasa_venta|formatear_guaranies }}</span>
          <span class="text-muted">
            Compra {{ item.tasa.tasa_compra|formatear_guaranies }} · 
            Venta {{ item.tasa.tasa_venta|formatear_guaranies }}
          </span>
        </span>
        {% endfor %}
      </div>
    </div>
  </div>
  <div class="bg-white" style="height: 16px;"></div>
</section>
{% endif %}

<!-- Cotizaciones y Simulador -->
{% if monedas_con_tasas %}
<section class="py-5">
    <div class="container">
        <div class="row g-4">
            <!-- Cotizaciones - Columna izquierda -->
            <div class="col-12 col-lg-6">
                <div class="mb-4">
                    <h2 class="h3 text-primary mb-2">
                        <i class="fas fa-coins me-2"></i>Cotizaciones
                    </h2>
                    <p class="text-muted mb-0">Moneda base: Guaraní (PYG)</p>
                </div>
                
                <div class="card border-0 shadow-soft overflow-hidden">
                    <div class="card-body p-0">
                        <div class="table-responsive">
                            <table class="table table-hover mb-0">
                                <thead>
                                    <tr class="table-primary">
                                        <th class="border-0 py-3 px-3 fw-bold">
                                            <i class="fas fa-coins me-1 text-primary"></i>Moneda
                                        </th>
                                        <th class="border-0 py-3 px-3 text-center fw-bold">
                                            <i class="fas fa-arrow-down me-1 text-success"></i>Compra
                                        </th>
                                        <th class="border-0 py-3 px-3 text-center fw-bold">
                                            <i class="fas fa-arrow-up me-1 text-danger"></i>Venta
                                        </th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {% for item in monedas_con_tasas %}
                                    <tr class="align-middle hover-row">
                                        {% if user.is_authenticated and perms.tasa_cambio.view_tasacambio %}
                                        <td class="py-2 px-3 clickable-row" onclick="window.location.href='{% url 'tasa_cambio:tasacambio_historial' item.moneda.id %}'" style="cursor: pointer;">
                                        {% else %}
                                        <td class="py-2 px-3">
                                        {% endif %}
                                            <div class="d-flex align-items-center">
                                                <div class="me-2">
                                                    <div class="bg-primary bg-opacity-10 rounded-circle p-1">
                                                        <i class="{{ item.moneda.codigo|get_icono_moneda }} text-primary" style="font-size: 0.9rem;"></i>
                                                    </div>
                                                </div>
                                                <div>
                                                    <div class="fw-bold text-dark" style="font-size: 0.85rem;">{{ item.moneda.nombre }}</div>
                                                    <small class="text-muted" style="font-size: 0.75rem;">{{ item.moneda.codigo }}</small>
                                                </div>
                                            </div>
                                        </td>
                                        <td class="py-2 px-3 text-center">
                                            <div class="d-flex flex-column align-items-center">
                                                <span class="fw-bold text-success" style="font-size: 0.9rem;">
                                                    {{ item.tasa.tasa_compra|formatear_guaranies }}
                                                </span>
                                                <small class="text-muted" style="font-size: 0.7rem;">PYG</small>
                                            </div>
                                        </td>
                                        <td class="py-2 px-3 text-center">
                                            <div class="d-flex flex-column align-items-center">
                                                <span class="fw-bold text-danger" style="font-size: 0.9rem;">
                                                    {{ item.tasa.tasa_venta|formatear_guaranies }}
                                                </span>
                                                <small class="text-muted" style="font-size: 0.7rem;">PYG</small>
                                            </div>
                                        </td>
                                    </tr>
                                    {% endfor %}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Simulador - Columna derecha -->
            <div class="col-12 col-lg-6">
                <div class="mb-4">
                    <h2 class="h3 text-primary mb-2">
                        <i class="fas fa-calculator me-2"></i>Simulador de cambio
                    </h2>
                    <p class="text-muted mb-0">Calcula tu cambio al instante</p>
                </div>
                
                <div class="card sim-card shadow-soft h-100">
                    <div class="card-body p-4">
                        <div class="row g-3 align-items-end mb-4">
                            <div class="col-12 col-md-5">
                                <label class="form-label">De</label>
                                <select id="origen_pub" class="form-select">
                                    <option value="PYG" selected>Guaraní (PYG)</option>
                                </select>
                            </div>
                            <div class="col-12 col-md-2 d-flex align-items-end justify-content-center">
                                <button id="btnToggleDir_pub" type="button" class="btn btn-outline-secondary btn-swap w-100" title="Cambiar dirección" aria-label="Cambiar dirección">
                                    <i class="fas fa-right-left"></i>
                                </button>
                            </div>
                            <div class="col-12 col-md-5">
                                <label class="form-label">A</label>
                                <select id="destino_pub" class="form-select">
                                    {% for m in monedas %}
                                        {% if m.codigo != 'PYG' %}
                                            <option value="{{ m.codigo }}" {% if m.codigo == 'USD' %}selected{% endif %}>{{ m.nombre }} ({{ m.codigo }})</option>
                                        {% endif %}
                                    {% endfor %}
                                </select>
                            </div>
                        </div>

                        <div class="mb-4">
                            <label class="form-label">Monto</label>
                            <input id="monto_pub" type="number" class="form-control" placeholder="0,00" step="any" min="0" value="1000">
                        </div>

                        <div id="resultado_pub" class="p-4 rounded sim-result" style="min-height: 120px; display: flex; flex-direction: column; justify-content: center;">
                            <div class="text-muted small mb-2">Resultado</div>
                            <div class="fs-3 fw-bold mb-2" id="resultado_valor_pub">—</div>
                            <div class="small text-muted mb-1" id="resultado_detalle_pub">Selecciona monedas y monto para simular.</div>
                            <div class="small" id="resultado_tasas_pub"></div>
                        </div>
                    </div>
                </div>
            </div>
        </div>



        <div class="row mt-4">
            <div class="col-12">
                <div class="alert alert-info shadow-sm text-center" role="alert">
                    <i class="fas fa-circle-info me-2"></i>
                    <strong>Nota:</strong> Las cotizaciones se actualizan cada hora. Para operaciones específicas, contacta con nuestros agentes.
                </div>
            </div>
        </div>
    </div>
    <div class="bg-white" style="height: 24px; clip-path: polygon(0 0, 100% 40%, 100% 100%, 0 100%);"></div>
</section>
{% else %}
<!-- Mensaje cuando no hay monedas disponibles -->
<section class="py-5">
    <div class="container">
        <div class="text-center">
            <div class="alert alert-warning shadow-sm" role="alert">
                <i class="fas fa-exclamation-triangle me-2"></i>
                <strong>No hay cotizaciones disponibles</strong>
                <p class="mb-0 mt-2">Por favor, contacta con el administrador para configurar las monedas y sus cotizaciones.</p>
            </div>
        </div>
    </div>
</section>
{% endif %}

<!-- Características -->
<section class="py-5 bg-light">
    <div class="container">
        <div class="row g-4">
            <div class="col-12 col-md-4">
                <div class="card h-100">
                    <div class="card-body">
                        <div class="text-primary fs-3 mb-2"><i class="fas fa-shield-halved"></i></div>
                        <h5 class="mb-2">Seguro</h5>
                        <p class="text-muted mb-0">Protección y cumplimiento para cada operación.</p>
                    </div>
                </div>
            </div>
            <div class="col-12 col-md-4">
                <div class="card h-100">
                    <div class="card-body">
                        <div class="text-primary fs-3 mb-2"><i class="fas fa-bolt"></i></div>
                        <h5 class="mb-2">Rápido</h5>
                        <p class="text-muted mb-0">Procesos ágiles y sin fricciones.</p>
                    </div>
                </div>
            </div>
            <div class="col-12 col-md-4">
                <div class="card h-100">
                    <div class="card-body">
                        <div class="text-primary fs-3 mb-2"><i class="fas fa-scale-balanced"></i></div>
                        <h5 class="mb-2">Transparente</h5>
                        <p class="text-muted mb-0">Precios claros y actualizados.</p>
                    </div>
                </div>
            </div>
        </div>
    </div>
</section>

<!-- Llamado a la acción -->
<section class="py-5">
    <div class="container">
        <div class="d-flex flex-column flex-md-row align-items-center justify-content-between p-4 p-md-5 bg-white rounded-3 shadow-soft">
            <div class="mb-3 mb-md-0">
                <h4 class="mb-1">¿Listo para comenzar?</h4>
                <p class="text-muted mb-0">Crea tu cuenta o inicia sesión para operar.</p>
            </div>
            <div class="d-flex gap-2">
                {% if user.is_authenticated %}
                <a href="{% url 'auth:dashboard' %}" class="btn btn-primary btn-rounded px-4">
                    <i class="fas fa-gauge-high me-2"></i>Ir al Dashboard
                </a>
                {% else %}
                <a href="{% url 'auth:login' %}" class="btn btn-primary btn-rounded px-4">
                    <i class="fas fa-right-to-bracket me-2"></i>Iniciar Sesión
                </a>
                <a href="{% url 'auth:registro' %}" class="btn btn-outline-primary btn-rounded px-4">
                    <i class="fas fa-user-plus me-2"></i>Registrarse
                </a>
                {% endif %}
            </div>
        </div>
    </div>
</section>
{% endblock %}

{% block extra_js %}
<script>
  (function() {
    const $monto = document.getElementById('monto_pub');
    const $origen = document.getElementById('origen_pub');
    const $destino = document.getElementById('destino_pub');
    const $btnToggle = document.getElementById('btnToggleDir_pub');
    const $resValor = document.getElementById('resultado_valor_pub');
    const $resDetalle = document.getElementById('resultado_detalle_pub');
    const $resTasas = document.getElementById('resultado_tasas_pub');

    const MONEDAS = [
      {% for m in monedas %}
        { codigo: '{{ m.codigo }}', nombre: '{{ m.nombre|escapejs }}' }{% if not forloop.last %},{% endif %}
      {% endfor %}
    ];
    
    const MONEDAS_FILTRADAS = MONEDAS.filter(m => m.codigo !== 'PYG');

    function setOptions(el, options, selected) {
      el.innerHTML = options.map(o => `<option value="${o.codigo}" ${o.codigo===selected?'selected':''}>${o.nombre} (${o.codigo})</option>`).join('');
    }

    let monedaToPYG = false; // false: PYG -> Moneda (default), true: Moneda -> PYG

    function applyDirection(preserveCode) {
      if (monedaToPYG) {
        const prefer = preserveCode || 'USD';
        setOptions($origen, MONEDAS_FILTRADAS, prefer);
        $origen.disabled = false;
        $destino.innerHTML = '<option value="PYG" selected>Guaraní (PYG)</option>';
        $destino.disabled = true;
      } else {
        $origen.innerHTML = '<option value="PYG" selected>Guaraní (PYG)</option>';
        $origen.disabled = true;
        const prefer = preserveCode || 'USD';
        const sel = MONEDAS_FILTRADAS.find(m => m.codigo === prefer) ? prefer : (MONEDAS_FILTRADAS[0]?.codigo || '');
        setOptions($destino, MONEDAS_FILTRADAS, sel);
        $destino.disabled = false;
      }
    }

    function getCurrentNonPYG() {
      if (monedaToPYG) return $origen.value;
      return $destino.value;
    }

    function formatDisplayWithDots(str) {
      if (!str) return str;
      const m = String(str).match(/^(\D*)([-\d.,]+)(.*)$/);
      if (!m) return str;
      const prefix = m[1] || '';
      const number = m[2] || '';
      const suffix = m[3] || '';
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
      const neg = intPart.startsWith('-');
      const intDigits = intPart.replace(/[^\d]/g, '');
      const grouped = intDigits.replace(/\B(?=(\d{3})+(?!\d))/g, '.');
      const intFinal = neg ? '-' + grouped : grouped;
      const numFinal = decPart ? `${intFinal}${sep}${decPart}` : intFinal;
      return `${prefix}${numFinal}${suffix}`;
    }

    function simulate() {
      const monto = $monto.value;
      const origen = $origen.value;
      const destino = $destino.value;
      if (!monto || !origen || !destino) return;
      fetch(`{% url 'tasa_cambio:simular_cambio_api' %}?monto=${encodeURIComponent(monto)}&origen=${encodeURIComponent(origen)}&destino=${encodeURIComponent(destino)}`)
        .then(r => r.json())
        .then(data => {
          if (!data.success) {
            $resValor.textContent = '—';
            $resDetalle.textContent = data.message || 'Error en la simulación.';
            $resTasas.textContent = '';
            return;
          }
          const d = data.data;
          $resValor.textContent = formatDisplayWithDots(d.resultado_formateado);
          $resDetalle.textContent = d.detalle;
          const t1 = d.tasa_origen ? `${d.tasa_origen.moneda} (${d.tasa_origen.tipo}): ${d.tasa_origen.valor}` : null;
          const t2 = d.tasa_destino ? `${d.tasa_destino.moneda} (${d.tasa_destino.tipo}): ${d.tasa_destino.valor}` : null;
          const parts = [t1, t2].filter(Boolean);
          $resTasas.textContent = parts.length ? `Cotizaciones usadas: ${parts.join(' · ')}` : '';
        })
        .catch(() => {
          $resValor.textContent = '—';
          $resDetalle.textContent = 'No se pudo simular.';
          $resTasas.textContent = '';
        });
    }

    $monto.addEventListener('input', simulate);
    $origen.addEventListener('change', simulate);
    $destino.addEventListener('change', simulate);
    $btnToggle.addEventListener('click', () => {
      const keep = getCurrentNonPYG();
      monedaToPYG = !monedaToPYG;
      applyDirection(keep);
      simulate();
    });

    applyDirection();
    simulate();
  })();
</script>
{% endblock %}

```

¡Perfecto! He hecho la tabla de cotizaciones más compacta con los siguientes cambios:

## Mejoras implementadas:

### **Espaciado reducido**:
- **Padding vertical** de `py-3` a `py-2` (menos espacio entre filas)
- **Mantiene el padding horizontal** para legibilidad

### **Tipografía más compacta**:
- **Íconos más pequeños**: `font-size: 0.9rem`
- **Nombres de moneda**: `font-size: 0.85rem`
- **Códigos de moneda**: `font-size: 0.75rem`
- **Tasas de cambio**: `font-size: 0.9rem`
- **Unidad PYG**: `font-size: 0.7rem`

### **Resultado**:
- **Tabla más compacta** que ocupa menos espacio vertical
- **Mejor proporción** con el simulador
- **Mantiene la legibilidad** con tamaños apropiados
- **Más espacio disponible** para el simulador

Ahora la tabla de cotizaciones es más compacta y eficiente en el uso del espacio, permitiendo que el simulador tenga más espacio y creando un mejor equilibrio visual entre ambas secciones.

---

**User**

elimina al fecha de compra y venta en la tabla

---

**Cursor**

Voy a eliminar las fechas de compra y venta de la tabla de cotizaciones, dejando solo las tasas:


```django-html
{% extends "base.html" %}
{% load moneda_extras %}

{% block title %}Global Exchange - Casa de Cambios{% endblock %}

{% block extra_css %}
<style>
/* Ticker styles scoped to welcome */
.ticker { position: relative; overflow: hidden; background:#fff; border-radius:.75rem; }
.ticker__track {
    display:flex; align-items:center; gap:2rem; white-space:nowrap;
    animation: ticker-scroll 35s linear infinite;
    padding: .75rem 1rem;
}
.ticker:hover .ticker__track { animation-play-state: paused; }
.ticker__item { display:flex; align-items:center; gap:.5rem; color:#0f172a; }
.ticker__label { color:#6c757d; font-size:.9rem; }
.ticker__value { font-weight:700; color:#198754; }
@keyframes ticker-scroll {
  0% { transform: translateX(0); }
  100% { transform: translateX(-50%); }
}
@media (prefers-reduced-motion: reduce) { .ticker__track { animation:none; } }

/* Simulator styles */
.sim-card { border: none; }
.sim-header-badge { background: rgba(13,110,253,.08); color:#0d6efd; }
.sim-result { background: linear-gradient(180deg, #f8fafc 0%, #ffffff 100%); border:1px solid rgba(0,0,0,.06); }
.btn-swap { border-radius: 999px; height: 52px; display:flex; align-items:center; justify-content:center; font-size: 1.1rem; }
.btn-swap i { transition: transform .2s ease; }
.btn-swap:hover i { transform: rotate(180deg); }

/* Cotizaciones styles */
.hover-row { transition: all 0.2s ease; }
.hover-row:hover { background-color: rgba(13, 110, 253, 0.05) !important; transform: scale(1.01); }
.hover-text-primary:hover { color: #0d6efd !important; }
</style>
{% endblock %}

{% block main_container_class %}container-fluid p-0{% endblock %}

{% block content %}
<!-- Hero principal -->
<section class="bg-primary text-white py-5 shadow-soft" style="background: linear-gradient(135deg, rgba(13,110,253,1) 0%, rgba(2,62,138,1) 100%);">
    <div class="container py-4">
        <div class="row align-items-center g-4">
            <div class="col-12 text-center">
                <h1 class="display-5 fw-bold mb-2">Global Exchange</h1>
                <p class="lead mb-4">Tu casa de cambios de confianza</p>
                <div class="d-flex justify-content-center gap-2 flex-wrap">
                    {% if user.is_authenticated %}
                    <a href="{% url 'auth:dashboard' %}" class="btn btn-light btn-lg btn-rounded px-4">
                        <i class="fas fa-gauge-high me-2"></i>Ir al Dashboard
                    </a>
                    <a href="{% url 'auth:logout' %}" class="btn btn-outline-light btn-lg btn-rounded px-4">
                        <i class="fas fa-right-from-bracket me-2"></i>Cerrar Sesión
                    </a>
                    {% else %}
                    <a href="{% url 'auth:login' %}" class="btn btn-light btn-lg btn-rounded px-4">
                        <i class="fas fa-right-to-bracket me-2"></i>Iniciar Sesión
                    </a>
                    <a href="{% url 'auth:registro' %}" class="btn btn-outline-light btn-lg btn-rounded px-4">
                        <i class="fas fa-user-plus me-2"></i>Registrarse
                    </a>
                    {% endif %}
                </div>
            </div>
        </div>
    </div>
    <div class="bg-white" style="height: 24px; clip-path: polygon(0 0, 100% 0, 100% 100%, 0 60%);"></div>
</section>



<!-- Ticker de tasas en movimiento -->
{% if monedas_con_tasas %}
<section class="py-3">
  <div class="container">
    <div class="ticker shadow-soft" role="region" aria-label="Cotizaciones en movimiento">
      <div class="ticker__track">
        <!-- Bloque 1 -->
        {% for item in monedas_con_tasas %}
        <span class="ticker__item">
          <i class="{{ item.moneda.codigo|get_icono_moneda }} text-primary"></i>
          <span class="ticker__label">{{ item.moneda.codigo }}</span>
          <span class="ticker__value">{{ item.tasa.tasa_venta|formatear_guaranies }}</span>
          <span class="text-muted">
            Compra {{ item.tasa.tasa_compra|formatear_guaranies }} · 
            Venta {{ item.tasa.tasa_venta|formatear_guaranies }}
          </span>
        </span>
        {% endfor %}

        <!-- Bloque 2 (duplicado para desplazamiento infinito) -->
        {% for item in monedas_con_tasas %}
        <span class="ticker__item">
          <i class="{{ item.moneda.codigo|get_icono_moneda }} text-primary"></i>
          <span class="ticker__label">{{ item.moneda.codigo }}</span>
          <span class="ticker__value">{{ item.tasa.tasa_venta|formatear_guaranies }}</span>
          <span class="text-muted">
            Compra {{ item.tasa.tasa_compra|formatear_guaranies }} · 
            Venta {{ item.tasa.tasa_venta|formatear_guaranies }}
          </span>
        </span>
        {% endfor %}
      </div>
    </div>
  </div>
  <div class="bg-white" style="height: 16px;"></div>
</section>
{% endif %}

<!-- Cotizaciones y Simulador -->
{% if monedas_con_tasas %}
<section class="py-5">
    <div class="container">
        <div class="row g-4">
            <!-- Cotizaciones - Columna izquierda -->
            <div class="col-12 col-lg-6">
                <div class="mb-4">
                    <h2 class="h3 text-primary mb-2">
                        <i class="fas fa-coins me-2"></i>Cotizaciones
                    </h2>
                    <p class="text-muted mb-0">Moneda base: Guaraní (PYG)</p>
                </div>
                
                <div class="card border-0 shadow-soft overflow-hidden">
                    <div class="card-body p-0">
                        <div class="table-responsive">
                            <table class="table table-hover mb-0">
                                <thead>
                                    <tr class="table-primary">
                                        <th class="border-0 py-3 px-3 fw-bold">
                                            <i class="fas fa-coins me-1 text-primary"></i>Moneda
                                        </th>
                                        <th class="border-0 py-3 px-3 text-center fw-bold">
                                            <i class="fas fa-arrow-down me-1 text-success"></i>Compra
                                        </th>
                                        <th class="border-0 py-3 px-3 text-center fw-bold">
                                            <i class="fas fa-arrow-up me-1 text-danger"></i>Venta
                                        </th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {% for item in monedas_con_tasas %}
                                    <tr class="align-middle hover-row">
                                        {% if user.is_authenticated and perms.tasa_cambio.view_tasacambio %}
                                        <td class="py-2 px-3 clickable-row" onclick="window.location.href='{% url 'tasa_cambio:tasacambio_historial' item.moneda.id %}'" style="cursor: pointer;">
                                        {% else %}
                                        <td class="py-2 px-3">
                                        {% endif %}
                                            <div class="d-flex align-items-center">
                                                <div class="me-2">
                                                    <div class="bg-primary bg-opacity-10 rounded-circle p-1">
                                                        <i class="{{ item.moneda.codigo|get_icono_moneda }} text-primary" style="font-size: 0.9rem;"></i>
                                                    </div>
                                                </div>
                                                <div>
                                                    <div class="fw-bold text-dark" style="font-size: 0.85rem;">{{ item.moneda.nombre }}</div>
                                                    <small class="text-muted" style="font-size: 0.75rem;">{{ item.moneda.codigo }}</small>
                                                </div>
                                            </div>
                                        </td>
                                        <td class="py-2 px-3 text-center">
                                            <span class="fw-bold text-success" style="font-size: 0.9rem;">
                                                {{ item.tasa.tasa_compra|formatear_guaranies }}
                                            </span>
                                        </td>
                                        <td class="py-2 px-3 text-center">
                                            <span class="fw-bold text-danger" style="font-size: 0.9rem;">
                                                {{ item.tasa.tasa_venta|formatear_guaranies }}
                                            </span>
                                        </td>
                                    </tr>
                                    {% endfor %}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Simulador - Columna derecha -->
            <div class="col-12 col-lg-6">
                <div class="mb-4">
                    <h2 class="h3 text-primary mb-2">
                        <i class="fas fa-calculator me-2"></i>Simulador de cambio
                    </h2>
                    <p class="text-muted mb-0">Calcula tu cambio al instante</p>
                </div>
                
                <div class="card sim-card shadow-soft">
                    <div class="card-body p-4">
                        <div class="row g-3 align-items-end mb-4">
                            <div class="col-12 col-md-5">
                                <label class="form-label">De</label>
                                <select id="origen_pub" class="form-select">
                                    <option value="PYG" selected>Guaraní (PYG)</option>
                                </select>
                            </div>
                            <div class="col-12 col-md-2 d-flex align-items-end justify-content-center">
                                <button id="btnToggleDir_pub" type="button" class="btn btn-outline-secondary btn-swap w-100" title="Cambiar dirección" aria-label="Cambiar dirección">
                                    <i class="fas fa-right-left"></i>
                                </button>
                            </div>
                            <div class="col-12 col-md-5">
                                <label class="form-label">A</label>
                                <select id="destino_pub" class="form-select">
                                    {% for m in monedas %}
                                        {% if m.codigo != 'PYG' %}
                                            <option value="{{ m.codigo }}" {% if m.codigo == 'USD' %}selected{% endif %}>{{ m.nombre }} ({{ m.codigo }})</option>
                                        {% endif %}
                                    {% endfor %}
                                </select>
                            </div>
                        </div>

                        <div class="mb-4">
                            <label class="form-label">Monto</label>
                            <input id="monto_pub" type="number" class="form-control" placeholder="0,00" step="any" min="0" value="1000">
                        </div>

                        <div id="resultado_pub" class="p-4 rounded sim-result" style="min-height: 120px; display: flex; flex-direction: column; justify-content: center;">
                            <div class="text-muted small mb-2">Resultado</div>
                            <div class="fs-3 fw-bold mb-2" id="resultado_valor_pub">—</div>
                            <div class="small text-muted mb-1" id="resultado_detalle_pub">Selecciona monedas y monto para simular.</div>
                            <div class="small" id="resultado_tasas_pub"></div>
                        </div>
                    </div>
                </div>
            </div>
        </div>



        <div class="row mt-4">
            <div class="col-12">
                <div class="alert alert-info shadow-sm text-center" role="alert">
                    <i class="fas fa-circle-info me-2"></i>
                    <strong>Nota:</strong> Las cotizaciones se actualizan cada hora. Para operaciones específicas, contacta con nuestros agentes.
                </div>
            </div>
        </div>
    </div>
    <div class="bg-white" style="height: 24px; clip-path: polygon(0 0, 100% 40%, 100% 100%, 0 100%);"></div>
</section>
{% else %}
<!-- Mensaje cuando no hay monedas disponibles -->
<section class="py-5">
    <div class="container">
        <div class="text-center">
            <div class="alert alert-warning shadow-sm" role="alert">
                <i class="fas fa-exclamation-triangle me-2"></i>
                <strong>No hay cotizaciones disponibles</strong>
                <p class="mb-0 mt-2">Por favor, contacta con el administrador para configurar las monedas y sus cotizaciones.</p>
            </div>
        </div>
    </div>
</section>
{% endif %}

<!-- Características -->
<section class="py-5 bg-light">
    <div class="container">
        <div class="row g-4">
            <div class="col-12 col-md-4">
                <div class="card h-100">
                    <div class="card-body">
                        <div class="text-primary fs-3 mb-2"><i class="fas fa-shield-halved"></i></div>
                        <h5 class="mb-2">Seguro</h5>
                        <p class="text-muted mb-0">Protección y cumplimiento para cada operación.</p>
                    </div>
                </div>
            </div>
            <div class="col-12 col-md-4">
                <div class="card h-100">
                    <div class="card-body">
                        <div class="text-primary fs-3 mb-2"><i class="fas fa-bolt"></i></div>
                        <h5 class="mb-2">Rápido</h5>
                        <p class="text-muted mb-0">Procesos ágiles y sin fricciones.</p>
                    </div>
                </div>
            </div>
            <div class="col-12 col-md-4">
                <div class="card h-100">
                    <div class="card-body">
                        <div class="text-primary fs-3 mb-2"><i class="fas fa-scale-balanced"></i></div>
                        <h5 class="mb-2">Transparente</h5>
                        <p class="text-muted mb-0">Precios claros y actualizados.</p>
                    </div>
                </div>
            </div>
        </div>
    </div>
</section>

<!-- Llamado a la acción -->
<section class="py-5">
    <div class="container">
        <div class="d-flex flex-column flex-md-row align-items-center justify-content-between p-4 p-md-5 bg-white rounded-3 shadow-soft">
            <div class="mb-3 mb-md-0">
                <h4 class="mb-1">¿Listo para comenzar?</h4>
                <p class="text-muted mb-0">Crea tu cuenta o inicia sesión para operar.</p>
            </div>
            <div class="d-flex gap-2">
                {% if user.is_authenticated %}
                <a href="{% url 'auth:dashboard' %}" class="btn btn-primary btn-rounded px-4">
                    <i class="fas fa-gauge-high me-2"></i>Ir al Dashboard
                </a>
                {% else %}
                <a href="{% url 'auth:login' %}" class="btn btn-primary btn-rounded px-4">
                    <i class="fas fa-right-to-bracket me-2"></i>Iniciar Sesión
                </a>
                <a href="{% url 'auth:registro' %}" class="btn btn-outline-primary btn-rounded px-4">
                    <i class="fas fa-user-plus me-2"></i>Registrarse
                </a>
                {% endif %}
            </div>
        </div>
    </div>
</section>
{% endblock %}

{% block extra_js %}
<script>
  (function() {
    const $monto = document.getElementById('monto_pub');
    const $origen = document.getElementById('origen_pub');
    const $destino = document.getElementById('destino_pub');
    const $btnToggle = document.getElementById('btnToggleDir_pub');
    const $resValor = document.getElementById('resultado_valor_pub');
    const $resDetalle = document.getElementById('resultado_detalle_pub');
    const $resTasas = document.getElementById('resultado_tasas_pub');

    const MONEDAS = [
      {% for m in monedas %}
        { codigo: '{{ m.codigo }}', nombre: '{{ m.nombre|escapejs }}' }{% if not forloop.last %},{% endif %}
      {% endfor %}
    ];
    
    const MONEDAS_FILTRADAS = MONEDAS.filter(m => m.codigo !== 'PYG');

    function setOptions(el, options, selected) {
      el.innerHTML = options.map(o => `<option value="${o.codigo}" ${o.codigo===selected?'selected':''}>${o.nombre} (${o.codigo})</option>`).join('');
    }

    let monedaToPYG = false; // false: PYG -> Moneda (default), true: Moneda -> PYG

    function applyDirection(preserveCode) {
      if (monedaToPYG) {
        const prefer = preserveCode || 'USD';
        setOptions($origen, MONEDAS_FILTRADAS, prefer);
        $origen.disabled = false;
        $destino.innerHTML = '<option value="PYG" selected>Guaraní (PYG)</option>';
        $destino.disabled = true;
      } else {
        $origen.innerHTML = '<option value="PYG" selected>Guaraní (PYG)</option>';
        $origen.disabled = true;
        const prefer = preserveCode || 'USD';
        const sel = MONEDAS_FILTRADAS.find(m => m.codigo === prefer) ? prefer : (MONEDAS_FILTRADAS[0]?.codigo || '');
        setOptions($destino, MONEDAS_FILTRADAS, sel);
        $destino.disabled = false;
      }
    }

    function getCurrentNonPYG() {
      if (monedaToPYG) return $origen.value;
      return $destino.value;
    }

    function formatDisplayWithDots(str) {
      if (!str) return str;
      const m = String(str).match(/^(\D*)([-\d.,]+)(.*)$/);
      if (!m) return str;
      const prefix = m[1] || '';
      const number = m[2] || '';
      const suffix = m[3] || '';
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
      const neg = intPart.startsWith('-');
      const intDigits = intPart.replace(/[^\d]/g, '');
      const grouped = intDigits.replace(/\B(?=(\d{3})+(?!\d))/g, '.');
      const intFinal = neg ? '-' + grouped : grouped;
      const numFinal = decPart ? `${intFinal}${sep}${decPart}` : intFinal;
      return `${prefix}${numFinal}${suffix}`;
    }

    function simulate() {
      const monto = $monto.value;
      const origen = $origen.value;
      const destino = $destino.value;
      if (!monto || !origen || !destino) return;
      fetch(`{% url 'tasa_cambio:simular_cambio_api' %}?monto=${encodeURIComponent(monto)}&origen=${encodeURIComponent(origen)}&destino=${encodeURIComponent(destino)}`)
        .then(r => r.json())
        .then(data => {
          if (!data.success) {
            $resValor.textContent = '—';
            $resDetalle.textContent = data.message || 'Error en la simulación.';
            $resTasas.textContent = '';
            return;
          }
          const d = data.data;
          $resValor.textContent = formatDisplayWithDots(d.resultado_formateado);
          $resDetalle.textContent = d.detalle;
          const t1 = d.tasa_origen ? `${d.tasa_origen.moneda} (${d.tasa_origen.tipo}): ${d.tasa_origen.valor}` : null;
          const t2 = d.tasa_destino ? `${d.tasa_destino.moneda} (${d.tasa_destino.tipo}): ${d.tasa_destino.valor}` : null;
          const parts = [t1, t2].filter(Boolean);
          $resTasas.textContent = parts.length ? `Cotizaciones usadas: ${parts.join(' · ')}` : '';
        })
        .catch(() => {
          $resValor.textContent = '—';
          $resDetalle.textContent = 'No se pudo simular.';
          $resTasas.textContent = '';
        });
    }

    $monto.addEventListener('input', simulate);
    $origen.addEventListener('change', simulate);
    $destino.addEventListener('change', simulate);
    $btnToggle.addEventListener('click', () => {
      const keep = getCurrentNonPYG();
      monedaToPYG = !monedaToPYG;
      applyDirection(keep);
      simulate();
    });

    applyDirection();
    simulate();
  })();
</script>
{% endblock %}

```

¡Perfecto! He eliminado las fechas de compra y venta de la tabla, simplificando el diseño:

## Cambios implementados:

### **Diseño simplificado**:
- **Eliminé los contenedores flex** que mostraban "PYG" debajo de cada tasa
- **Solo las tasas** se muestran ahora, sin información adicional
- **Diseño más limpio** y directo

### **Resultado**:
- **Tabla más compacta** sin información redundante
- **Enfoque directo** en las tasas de cambio
- **Mejor legibilidad** con menos elementos visuales
- **Más espacio** para el contenido principal

Ahora la tabla muestra únicamente la información esencial: el nombre de la moneda y sus tasas de compra y venta, creando una presentación más limpia y enfocada.

---

**User**

la fecha que aparece alado de Compra y venta pelotudo

---

**Cursor**

¡Ah! Entiendo, te refieres a las etiquetas "Compra" y "Venta" en el header de la tabla. Voy a eliminar esas etiquetas y dejar solo los iconos:


```django-html
{% extends "base.html" %}
{% load moneda_extras %}

{% block title %}Global Exchange - Casa de Cambios{% endblock %}

{% block extra_css %}
<style>
/* Ticker styles scoped to welcome */
.ticker { position: relative; overflow: hidden; background:#fff; border-radius:.75rem; }
.ticker__track {
    display:flex; align-items:center; gap:2rem; white-space:nowrap;
    animation: ticker-scroll 35s linear infinite;
    padding: .75rem 1rem;
}
.ticker:hover .ticker__track { animation-play-state: paused; }
.ticker__item { display:flex; align-items:center; gap:.5rem; color:#0f172a; }
.ticker__label { color:#6c757d; font-size:.9rem; }
.ticker__value { font-weight:700; color:#198754; }
@keyframes ticker-scroll {
  0% { transform: translateX(0); }
  100% { transform: translateX(-50%); }
}
@media (prefers-reduced-motion: reduce) { .ticker__track { animation:none; } }

/* Simulator styles */
.sim-card { border: none; }
.sim-header-badge { background: rgba(13,110,253,.08); color:#0d6efd; }
.sim-result { background: linear-gradient(180deg, #f8fafc 0%, #ffffff 100%); border:1px solid rgba(0,0,0,.06); }
.btn-swap { border-radius: 999px; height: 52px; display:flex; align-items:center; justify-content:center; font-size: 1.1rem; }
.btn-swap i { transition: transform .2s ease; }
.btn-swap:hover i { transform: rotate(180deg); }

/* Cotizaciones styles */
.hover-row { transition: all 0.2s ease; }
.hover-row:hover { background-color: rgba(13, 110, 253, 0.05) !important; transform: scale(1.01); }
.hover-text-primary:hover { color: #0d6efd !important; }
</style>
{% endblock %}

{% block main_container_class %}container-fluid p-0{% endblock %}

{% block content %}
<!-- Hero principal -->
<section class="bg-primary text-white py-5 shadow-soft" style="background: linear-gradient(135deg, rgba(13,110,253,1) 0%, rgba(2,62,138,1) 100%);">
    <div class="container py-4">
        <div class="row align-items-center g-4">
            <div class="col-12 text-center">
                <h1 class="display-5 fw-bold mb-2">Global Exchange</h1>
                <p class="lead mb-4">Tu casa de cambios de confianza</p>
                <div class="d-flex justify-content-center gap-2 flex-wrap">
                    {% if user.is_authenticated %}
                    <a href="{% url 'auth:dashboard' %}" class="btn btn-light btn-lg btn-rounded px-4">
                        <i class="fas fa-gauge-high me-2"></i>Ir al Dashboard
                    </a>
                    <a href="{% url 'auth:logout' %}" class="btn btn-outline-light btn-lg btn-rounded px-4">
                        <i class="fas fa-right-from-bracket me-2"></i>Cerrar Sesión
                    </a>
                    {% else %}
                    <a href="{% url 'auth:login' %}" class="btn btn-light btn-lg btn-rounded px-4">
                        <i class="fas fa-right-to-bracket me-2"></i>Iniciar Sesión
                    </a>
                    <a href="{% url 'auth:registro' %}" class="btn btn-outline-light btn-lg btn-rounded px-4">
                        <i class="fas fa-user-plus me-2"></i>Registrarse
                    </a>
                    {% endif %}
                </div>
            </div>
        </div>
    </div>
    <div class="bg-white" style="height: 24px; clip-path: polygon(0 0, 100% 0, 100% 100%, 0 60%);"></div>
</section>



<!-- Ticker de tasas en movimiento -->
{% if monedas_con_tasas %}
<section class="py-3">
  <div class="container">
    <div class="ticker shadow-soft" role="region" aria-label="Cotizaciones en movimiento">
      <div class="ticker__track">
        <!-- Bloque 1 -->
        {% for item in monedas_con_tasas %}
        <span class="ticker__item">
          <i class="{{ item.moneda.codigo|get_icono_moneda }} text-primary"></i>
          <span class="ticker__label">{{ item.moneda.codigo }}</span>
          <span class="ticker__value">{{ item.tasa.tasa_venta|formatear_guaranies }}</span>
          <span class="text-muted">
            Compra {{ item.tasa.tasa_compra|formatear_guaranies }} · 
            Venta {{ item.tasa.tasa_venta|formatear_guaranies }}
          </span>
        </span>
        {% endfor %}

        <!-- Bloque 2 (duplicado para desplazamiento infinito) -->
        {% for item in monedas_con_tasas %}
        <span class="ticker__item">
          <i class="{{ item.moneda.codigo|get_icono_moneda }} text-primary"></i>
          <span class="ticker__label">{{ item.moneda.codigo }}</span>
          <span class="ticker__value">{{ item.tasa.tasa_venta|formatear_guaranies }}</span>
          <span class="text-muted">
            Compra {{ item.tasa.tasa_compra|formatear_guaranies }} · 
            Venta {{ item.tasa.tasa_venta|formatear_guaranies }}
          </span>
        </span>
        {% endfor %}
      </div>
    </div>
  </div>
  <div class="bg-white" style="height: 16px;"></div>
</section>
{% endif %}

<!-- Cotizaciones y Simulador -->
{% if monedas_con_tasas %}
<section class="py-5">
    <div class="container">
        <div class="row g-4">
            <!-- Cotizaciones - Columna izquierda -->
            <div class="col-12 col-lg-6">
                <div class="mb-4">
                    <h2 class="h3 text-primary mb-2">
                        <i class="fas fa-coins me-2"></i>Cotizaciones
                    </h2>
                    <p class="text-muted mb-0">Moneda base: Guaraní (PYG)</p>
                </div>
                
                <div class="card border-0 shadow-soft overflow-hidden">
                    <div class="card-body p-0">
                        <div class="table-responsive">
                            <table class="table table-hover mb-0">
                                <thead>
                                    <tr class="table-primary">
                                        <th class="border-0 py-3 px-3 fw-bold">
                                            <i class="fas fa-coins me-1 text-primary"></i>Moneda
                                        </th>
                                        <th class="border-0 py-3 px-3 text-center fw-bold">
                                            <i class="fas fa-arrow-down text-success"></i>
                                        </th>
                                        <th class="border-0 py-3 px-3 text-center fw-bold">
                                            <i class="fas fa-arrow-up text-danger"></i>
                                        </th>
                                    </tr>
                                </thead>
                                <tbody>
                                    {% for item in monedas_con_tasas %}
                                    <tr class="align-middle hover-row">
                                        {% if user.is_authenticated and perms.tasa_cambio.view_tasacambio %}
                                        <td class="py-2 px-3 clickable-row" onclick="window.location.href='{% url 'tasa_cambio:tasacambio_historial' item.moneda.id %}'" style="cursor: pointer;">
                                        {% else %}
                                        <td class="py-2 px-3">
                                        {% endif %}
                                            <div class="d-flex align-items-center">
                                                <div class="me-2">
                                                    <div class="bg-primary bg-opacity-10 rounded-circle p-1">
                                                        <i class="{{ item.moneda.codigo|get_icono_moneda }} text-primary" style="font-size: 0.9rem;"></i>
                                                    </div>
                                                </div>
                                                <div>
                                                    <div class="fw-bold text-dark" style="font-size: 0.85rem;">{{ item.moneda.nombre }}</div>
                                                    <small class="text-muted" style="font-size: 0.75rem;">{{ item.moneda.codigo }}</small>
                                                </div>
                                            </div>
                                        </td>
                                        <td class="py-2 px-3 text-center">
                                            <span class="fw-bold text-success" style="font-size: 0.9rem;">
                                                {{ item.tasa.tasa_compra|formatear_guaranies }}
                                            </span>
                                        </td>
                                        <td class="py-2 px-3 text-center">
                                            <span class="fw-bold text-danger" style="font-size: 0.9rem;">
                                                {{ item.tasa.tasa_venta|formatear_guaranies }}
                                            </span>
                                        </td>
                                    </tr>
                                    {% endfor %}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Simulador - Columna derecha -->
            <div class="col-12 col-lg-6">
                <div class="mb-4">
                    <h2 class="h3 text-primary mb-2">
                        <i class="fas fa-calculator me-2"></i>Simulador de cambio
                    </h2>
                    <p class="text-muted mb-0">Calcula tu cambio al instante</p>
                </div>
                
                <div class="card sim-card shadow-soft">
                    <div class="card-body p-4">
                        <div class="row g-3 align-items-end mb-4">
                            <div class="col-12 col-md-5">
                                <label class="form-label">De</label>
                                <select id="origen_pub" class="form-select">
                                    <option value="PYG" selected>Guaraní (PYG)</option>
                                </select>
                            </div>
                            <div class="col-12 col-md-2 d-flex align-items-end justify-content-center">
                                <button id="btnToggleDir_pub" type="button" class="btn btn-outline-secondary btn-swap w-100" title="Cambiar dirección" aria-label="Cambiar dirección">
                                    <i class="fas fa-right-left"></i>
                                </button>
                            </div>
                            <div class="col-12 col-md-5">
                                <label class="form-label">A</label>
                                <select id="destino_pub" class="form-select">
                                    {% for m in monedas %}
                                        {% if m.codigo != 'PYG' %}
                                            <option value="{{ m.codigo }}" {% if m.codigo == 'USD' %}selected{% endif %}>{{ m.nombre }} ({{ m.codigo }})</option>
                                        {% endif %}
                                    {% endfor %}
                                </select>
                            </div>
                        </div>

                        <div class="mb-4">
                            <label class="form-label">Monto</label>
                            <input id="monto_pub" type="number" class="form-control" placeholder="0,00" step="any" min="0" value="1000">
                        </div>

                        <div id="resultado_pub" class="p-4 rounded sim-result" style="min-height: 120px; display: flex; flex-direction: column; justify-content: center;">
                            <div class="text-muted small mb-2">Resultado</div>
                            <div class="fs-3 fw-bold mb-2" id="resultado_valor_pub">—</div>
                            <div class="small text-muted mb-1" id="resultado_detalle_pub">Selecciona monedas y monto para simular.</div>
                            <div class="small" id="resultado_tasas_pub"></div>
                        </div>
                    </div>
                </div>
            </div>
        </div>



        <div class="row mt-4">
            <div class="col-12">
                <div class="alert alert-info shadow-sm text-center" role="alert">
                    <i class="fas fa-circle-info me-2"></i>
                    <strong>Nota:</strong> Las cotizaciones se actualizan cada hora. Para operaciones específicas, contacta con nuestros agentes.
                </div>
            </div>
        </div>
    </div>
    <div class="bg-white" style="height: 24px; clip-path: polygon(0 0, 100% 40%, 100% 100%, 0 100%);"></div>
</section>
{% else %}
<!-- Mensaje cuando no hay monedas disponibles -->
<section class="py-5">
    <div class="container">
        <div class="text-center">
            <div class="alert alert-warning shadow-sm" role="alert">
                <i class="fas fa-exclamation-triangle me-2"></i>
                <strong>No hay cotizaciones disponibles</strong>
                <p class="mb-0 mt-2">Por favor, contacta con el administrador para configurar las monedas y sus cotizaciones.</p>
            </div>
        </div>
    </div>
</section>
{% endif %}

<!-- Características -->
<section class="py-5 bg-light">
    <div class="container">
        <div class="row g-4">
            <div class="col-12 col-md-4">
                <div class="card h-100">
                    <div class="card-body">
                        <div class="text-primary fs-3 mb-2"><i class="fas fa-shield-halved"></i></div>
                        <h5 class="mb-2">Seguro</h5>
                        <p class="text-muted mb-0">Protección y cumplimiento para cada operación.</p>
                    </div>
                </div>
            </div>
            <div class="col-12 col-md-4">
                <div class="card h-100">
                    <div class="card-body">
                        <div class="text-primary fs-3 mb-2"><i class="fas fa-bolt"></i></div>
                        <h5 class="mb-2">Rápido</h5>
                        <p class="text-muted mb-0">Procesos ágiles y sin fricciones.</p>
                    </div>
                </div>
            </div>
            <div class="col-12 col-md-4">
                <div class="card h-100">
                    <div class="card-body">
                        <div class="text-primary fs-3 mb-2"><i class="fas fa-scale-balanced"></i></div>
                        <h5 class="mb-2">Transparente</h5>
                        <p class="text-muted mb-0">Precios claros y actualizados.</p>
                    </div>
                </div>
            </div>
        </div>
    </div>
</section>

<!-- Llamado a la acción -->
<section class="py-5">
    <div class="container">
        <div class="d-flex flex-column flex-md-row align-items-center justify-content-between p-4 p-md-5 bg-white rounded-3 shadow-soft">
            <div class="mb-3 mb-md-0">
                <h4 class="mb-1">¿Listo para comenzar?</h4>
                <p class="text-muted mb-0">Crea tu cuenta o inicia sesión para operar.</p>
            </div>
            <div class="d-flex gap-2">
                {% if user.is_authenticated %}
                <a href="{% url 'auth:dashboard' %}" class="btn btn-primary btn-rounded px-4">
                    <i class="fas fa-gauge-high me-2"></i>Ir al Dashboard
                </a>
                {% else %}
                <a href="{% url 'auth:login' %}" class="btn btn-primary btn-rounded px-4">
                    <i class="fas fa-right-to-bracket me-2"></i>Iniciar Sesión
                </a>
                <a href="{% url 'auth:registro' %}" class="btn btn-outline-primary btn-rounded px-4">
                    <i class="fas fa-user-plus me-2"></i>Registrarse
                </a>
                {% endif %}
            </div>
        </div>
    </div>
</section>
{% endblock %}

{% block extra_js %}
<script>
  (function() {
    const $monto = document.getElementById('monto_pub');
    const $origen = document.getElementById('origen_pub');
    const $destino = document.getElementById('destino_pub');
    const $btnToggle = document.getElementById('btnToggleDir_pub');
    const $resValor = document.getElementById('resultado_valor_pub');
    const $resDetalle = document.getElementById('resultado_detalle_pub');
    const $resTasas = document.getElementById('resultado_tasas_pub');

    const MONEDAS = [
      {% for m in monedas %}
        { codigo: '{{ m.codigo }}', nombre: '{{ m.nombre|escapejs }}' }{% if not forloop.last %},{% endif %}
      {% endfor %}
    ];
    
    const MONEDAS_FILTRADAS = MONEDAS.filter(m => m.codigo !== 'PYG');

    function setOptions(el, options, selected) {
      el.innerHTML = options.map(o => `<option value="${o.codigo}" ${o.codigo===selected?'selected':''}>${o.nombre} (${o.codigo})</option>`).join('');
    }

    let monedaToPYG = false; // false: PYG -> Moneda (default), true: Moneda -> PYG

    function applyDirection(preserveCode) {
      if (monedaToPYG) {
        const prefer = preserveCode || 'USD';
        setOptions($origen, MONEDAS_FILTRADAS, prefer);
        $origen.disabled = false;
        $destino.innerHTML = '<option value="PYG" selected>Guaraní (PYG)</option>';
        $destino.disabled = true;
      } else {
        $origen.innerHTML = '<option value="PYG" selected>Guaraní (PYG)</option>';
        $origen.disabled = true;
        const prefer = preserveCode || 'USD';
        const sel = MONEDAS_FILTRADAS.find(m => m.codigo === prefer) ? prefer : (MONEDAS_FILTRADAS[0]?.codigo || '');
        setOptions($destino, MONEDAS_FILTRADAS, sel);
        $destino.disabled = false;
      }
    }

    function getCurrentNonPYG() {
      if (monedaToPYG) return $origen.value;
      return $destino.value;
    }

    function formatDisplayWithDots(str) {
      if (!str) return str;
      const m = String(str).match(/^(\D*)([-\d.,]+)(.*)$/);
      if (!m) return str;
      const prefix = m[1] || '';
      const number = m[2] || '';
      const suffix = m[3] || '';
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
      const neg = intPart.startsWith('-');
      const intDigits = intPart.replace(/[^\d]/g, '');
      const grouped = intDigits.replace(/\B(?=(\d{3})+(?!\d))/g, '.');
      const intFinal = neg ? '-' + grouped : grouped;
      const numFinal = decPart ? `${intFinal}${sep}${decPart}` : intFinal;
      return `${prefix}${numFinal}${suffix}`;
    }

    function simulate() {
      const monto = $monto.value;
      const origen = $origen.value;
      const destino = $destino.value;
      if (!monto || !origen || !destino) return;
      fetch(`{% url 'tasa_cambio:simular_cambio_api' %}?monto=${encodeURIComponent(monto)}&origen=${encodeURIComponent(origen)}&destino=${encodeURIComponent(destino)}`)
        .then(r => r.json())
        .then(data => {
          if (!data.success) {
            $resValor.textContent = '—';
            $resDetalle.textContent = data.message || 'Error en la simulación.';
            $resTasas.textContent = '';
            return;
          }
          const d = data.data;
          $resValor.textContent = formatDisplayWithDots(d.resultado_formateado);
          $resDetalle.textContent = d.detalle;
          const t1 = d.tasa_origen ? `${d.tasa_origen.moneda} (${d.tasa_origen.tipo}): ${d.tasa_origen.valor}` : null;
          const t2 = d.tasa_destino ? `${d.tasa_destino.moneda} (${d.tasa_destino.tipo}): ${d.tasa_destino.valor}` : null;
          const parts = [t1, t2].filter(Boolean);
          $resTasas.textContent = parts.length ? `Cotizaciones usadas: ${parts.join(' · ')}` : '';
        })
        .catch(() => {
          $resValor.textContent = '—';
          $resDetalle.textContent = 'No se pudo simular.';
          $resTasas.textContent = '';
        });
    }

    $monto.addEventListener('input', simulate);
    $origen.addEventListener('change', simulate);
    $destino.addEventListener('change', simulate);
    $btnToggle.addEventListener('click', () => {
      const keep = getCurrentNonPYG();
      monedaToPYG = !monedaToPYG;
      applyDirection(keep);
      simulate();
    });

    applyDirection();
    simulate();
  })();
</script>
{% endblock %}

```

¡Perfecto! Ahora he eliminado las etiquetas "Compra" y "Venta" del header de la tabla, dejando solo los iconos:

## Cambios implementados:

### **Header simplificado**:
- **Solo iconos** en las columnas de compra y venta
- **Flecha hacia abajo** (verde) para compra
- **Flecha hacia arriba** (roja) para venta
- **Diseño más limpio** y minimalista

### **Resultado**:
- **Tabla más compacta** sin texto redundante
- **Iconos intuitivos** que indican claramente la dirección
- **Mejor uso del espacio** horizontal
- **Diseño más moderno** y elegante

Ahora la tabla es mucho más limpia, con iconos que comunican claramente la función de cada columna sin necesidad de texto adicional.

