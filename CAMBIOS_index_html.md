# Cambios para `templates/index.html`

Son 7 pegados. Cada uno dice **dónde** va. Todo lo demás de tu archivo queda igual.

---

## 1) CSS — pégalo justo antes de `</style>`

```css
  /* ============ ARMAR VIAJE ============ */
  .info-viaje { font-size: 14px; color: var(--ink-soft); margin-bottom: 18px; }
  .paso-num { font-family: 'IBM Plex Mono', monospace; color: var(--gold-deep); margin-right: 8px; }
  .fila-accion { display: flex; align-items: center; gap: 12px; flex-wrap: wrap; margin: 6px 0 14px 0; }
  .fila-accion input { width: 90px; padding: 8px 10px; border: 1.5px solid var(--line); border-radius: 8px; font-family: inherit; }
  .estado.vigente { background: var(--green-status-soft); color: var(--green-status); }
  .estado.vencido { background: var(--coral-soft); color: var(--coral); }
  .estado.liberado { background: #e6eef4; color: #3a6b8a; }
  .resultado-cotizacion { border: 1.5px dashed var(--gold); border-radius: 12px; padding: 16px 18px; margin-bottom: 14px; background: #fdf8ee; }
  .resultado-cotizacion .folio-grande { font-family: 'Fraunces', serif; font-size: 22px; margin-bottom: 8px; }
  .resultado-cotizacion .totales { text-align: right; font-size: 14px; line-height: 1.8; }
```

---

## 2) Menú lateral — dentro de `<nav class="tabs">`, entre "Cotizador" y "Cotizaciones y cierre"

```html
      <button data-pantalla="viaje"><span class="dot"></span>Armar viaje</button>
```

---

## 3) Objeto `pantallas` (al inicio del `<script>`) — agrega la línea `viaje`

```js
  const pantallas = {
    resumen: document.getElementById("pantallaResumen"),
    solicitudes: document.getElementById("pantallaSolicitudes"),
    cotizador: document.getElementById("pantallaCotizador"),
    viaje: document.getElementById("pantallaViaje"),
    cotizaciones: document.getElementById("pantallaCotizaciones"),
  };
```

---

## 4) Formulario de solicitud (proceso 1.0: datos personales del cliente)

**4a.** En `#formularioSolicitud`, justo después del campo `regreso`, agrega:

```html
          <div class="campo">
            <label for="telefono">Teléfono (opcional)</label>
            <input type="tel" id="telefono" placeholder="Ej. 55 1234 5678">
          </div>
          <div class="campo">
            <label for="correo">Correo (opcional)</label>
            <input type="email" id="correo" placeholder="cliente@correo.com">
          </div>
```

**4b.** En la tabla "Solicitudes registradas", el `<tr>` del `<thead>` queda así:

```html
            <tr>
              <th>Folio</th><th>Cliente</th><th>Destino</th><th>Categoría</th>
              <th>Pasajeros</th><th>Salida</th><th>Regreso</th>
            </tr>
```

**4c.** En `cargarSolicitudes()`, reemplaza el bloque `tbodySolicitudes.innerHTML = solicitudes.map(...)` por:

```js
      tbodySolicitudes.innerHTML = solicitudes.map(function (s) {
        return "<tr>" +
          "<td>" + (s.folio || "—") + "</td>" +
          "<td>" + s.cliente + "</td>" +
          "<td>" + s.destino + "</td>" +
          "<td>" + s.categoria + "</td>" +
          "<td>" + s.pasajeros + "</td>" +
          "<td>" + formatearFecha(s.salida) + "</td>" +
          "<td>" + formatearFecha(s.regreso) + "</td>" +
          "</tr>";
      }).join("");
```

**4d.** En el listener de `btnGuardarSolicitud`:

- En el `JSON.stringify({...})` agrega al final (después de `regreso: regreso`):
  ```js
          regreso: regreso,
          telefono: document.getElementById("telefono").value.trim(),
          correo: document.getElementById("correo").value.trim()
  ```
- Cambia el mensaje de éxito por:
  ```js
      mensajeFormSolicitud.textContent = "Solicitud guardada. Folio " + data.folio;
  ```
- En el arreglo que limpia campos agrega `"telefono", "correo"`:
  ```js
      ["cliente", "destino", "categoria", "pasajeros", "salida", "regreso", "telefono", "correo"].forEach(...)
  ```
- Sube el `setTimeout` de 900 a `2200` para alcanzar a leer el folio.

---

## 5) Nueva pantalla — pégala justo después de `</section>` de `pantallaCotizaciones` (antes de `</main>`)

```html
    <!-- ==================== ARMAR VIAJE (2.0 a 6.0) ==================== -->
    <section id="pantallaViaje" class="oculto">
      <div class="encabezado-pantalla">
        <h2>Armar viaje</h2>
        <p class="desc">Sigue el flujo: vuelo, hospedaje, servicios, bloqueos y cotización.</p>
      </div>

      <div class="seccion">
        <div class="seccion-titulo"><h3>Solicitud</h3></div>
        <div class="campo" style="max-width:460px;">
          <label for="viajeFolio">Elige la solicitud (folio)</label>
          <select id="viajeFolio"><option value="">Seleccionar</option></select>
        </div>
        <p class="info-viaje" id="viajeInfo" style="margin-top:12px;">Elige una solicitud para empezar.</p>
        <span class="mensaje-form" id="mensajeViaje"></span>
      </div>

      <div class="seccion">
        <div class="seccion-titulo"><h3><span class="paso-num">2.0</span>Vuelo</h3></div>
        <table>
          <thead><tr><th>Aerolínea</th><th>Ruta</th><th>Escala</th><th>Tarifa por pasajero</th><th></th></tr></thead>
          <tbody id="viajeTablaVuelos"><tr><td colspan="5" class="vacio">Elige una solicitud.</td></tr></tbody>
        </table>
      </div>

      <div class="seccion">
        <div class="seccion-titulo"><h3><span class="paso-num">3.0</span>Hospedaje</h3></div>
        <table>
          <thead><tr><th>Hospedaje</th><th>Noches</th><th>Zona</th><th>Neto total</th><th></th></tr></thead>
          <tbody id="viajeTablaHospedajes"><tr><td colspan="5" class="vacio">Elige una solicitud.</td></tr></tbody>
        </table>
      </div>

      <div class="seccion">
        <div class="seccion-titulo">
          <h3><span class="paso-num">4.0</span>Servicios complementarios</h3>
          <button class="boton-secundario" id="btnNuevoServicio">+ Cargar servicio</button>
        </div>

        <div id="formularioServicio" class="formulario oculto">
          <div class="rejilla-campos">
            <div class="campo">
              <label for="servDestino">Destino</label>
              <input type="text" id="servDestino" placeholder="Ej. Tokio">
            </div>
            <div class="campo">
              <label for="servNombre">Servicio</label>
              <input type="text" id="servNombre" placeholder="Ej. Traslado aeropuerto">
            </div>
            <div class="campo">
              <label for="servDescripcion">Especificaciones</label>
              <input type="text" id="servDescripcion" placeholder="Ej. Auto privado, ida y vuelta">
            </div>
            <div class="campo">
              <label for="servPrecio">Precio (USD)</label>
              <input type="number" id="servPrecio" min="0" placeholder="Ej. 150">
            </div>
          </div>
          <div class="acciones-form">
            <button class="boton-guardar" id="btnGuardarServicio">Guardar servicio</button>
            <button class="boton-cancelar" id="btnCancelarServicio">Cancelar</button>
            <span class="mensaje-form" id="mensajeFormServicio"></span>
          </div>
        </div>

        <table>
          <thead><tr><th>Servicio</th><th>Especificaciones</th><th>Precio</th><th></th></tr></thead>
          <tbody id="viajeTablaServicios"><tr><td colspan="4" class="vacio">Elige una solicitud.</td></tr></tbody>
        </table>
      </div>

      <div class="seccion">
        <div class="seccion-titulo"><h3>Servicios seleccionados</h3></div>
        <table>
          <thead><tr><th>Tipo</th><th>Detalle</th><th>Costo neto</th></tr></thead>
          <tbody id="viajeTablaSelecciones"><tr><td colspan="3" class="vacio">Todavía no hay nada seleccionado.</td></tr></tbody>
        </table>
      </div>

      <div class="seccion">
        <div class="seccion-titulo"><h3><span class="paso-num">5.0</span>Bloqueos</h3></div>
        <div class="fila-accion">
          <label for="bloqueoDias" style="font-size:13px;font-weight:600;">Días de vigencia</label>
          <input type="number" id="bloqueoDias" min="1" max="60" value="3">
          <button class="boton-guardar" id="btnGenerarBloqueos">Generar bloqueos</button>
          <button class="boton-secundario" id="btnLiberarBloqueos">Liberar bloqueos</button>
        </div>
        <table>
          <thead><tr><th>Tipo</th><th>Detalle</th><th>Costo neto</th><th>Vigencia hasta</th><th>Estado</th></tr></thead>
          <tbody id="viajeTablaBloqueos"><tr><td colspan="5" class="vacio">Sin bloqueos.</td></tr></tbody>
        </table>
      </div>

      <div class="seccion">
        <div class="seccion-titulo"><h3><span class="paso-num">6.0</span>Cotización</h3></div>
        <div class="fila-accion">
          <label for="cotMargen" style="font-size:13px;font-weight:600;">Utilidad (%)</label>
          <input type="number" id="cotMargen" min="0" value="20">
          <button class="boton-guardar" id="btnGenerarCotizacion">Generar cotización</button>
        </div>
        <div id="resultadoCotizacion"></div>
      </div>
    </section>
```

---

## 6) JavaScript — pégalo justo antes de `// ---------- Carga inicial ----------`

```js
  // ==========================================
  // ARMAR VIAJE (procesos 2.0 a 6.0 del DFD)
  // ==========================================

  function esc(t) {
    return String(t == null ? "" : t).replace(/[&<>"']/g, function (c) {
      return { "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c];
    });
  }

  async function postJSON(ruta, cuerpo) {
    const resp = await fetch(API_BASE + ruta, {
      method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(cuerpo)
    });
    const data = await resp.json();
    if (!resp.ok) throw new Error(data.error || "No se pudo completar la acción");
    return data;
  }

  const selViajeFolio = document.getElementById("viajeFolio");
  const msgViaje = document.getElementById("mensajeViaje");
  let solicitudesViaje = [];
  let solicitudActual = null;

  function avisoViaje(texto, ok) {
    msgViaje.textContent = texto;
    msgViaje.className = "mensaje-form " + (ok ? "ok" : "error");
  }

  function filaConBoton(celdas, textoBoton, alClic) {
    const tr = document.createElement("tr");
    tr.innerHTML = celdas.map(function (c) { return "<td>" + esc(c) + "</td>"; }).join("");
    const td = document.createElement("td");
    const b = document.createElement("button");
    b.className = "boton-secundario";
    b.textContent = textoBoton;
    b.addEventListener("click", alClic);
    td.appendChild(b);
    tr.appendChild(td);
    return tr;
  }

  function llenarTabla(idTbody, filas, columnasVacias, textoVacio) {
    const tbody = document.getElementById(idTbody);
    tbody.innerHTML = "";
    if (filas.length === 0) {
      tbody.innerHTML = '<tr><td colspan="' + columnasVacias + '" class="vacio">' + textoVacio + "</td></tr>";
      return;
    }
    filas.forEach(function (f) { tbody.appendChild(f); });
  }

  async function seleccionar(tipo, detalle, costo) {
    if (!solicitudActual) { avisoViaje("Elige una solicitud primero.", false); return; }
    try {
      await postJSON("/seleccion", { folio: solicitudActual.folio, tipo: tipo, detalle: detalle, costo: costo });
      avisoViaje(tipo + " seleccionado.", true);
      await refrescarViaje();
    } catch (err) {
      avisoViaje(err.message, false);
    }
  }

  async function cargarSolicitudesViaje() {
    try {
      const resp = await fetch(API_BASE + "/solicitudes");
      solicitudesViaje = await resp.json();
      const previo = selViajeFolio.value;
      selViajeFolio.innerHTML = '<option value="">Seleccionar</option>' +
        solicitudesViaje.map(function (s) {
          return '<option value="' + esc(s.folio) + '">' + esc(s.folio) + " · " + esc(s.cliente) + " → " + esc(s.destino) + "</option>";
        }).join("");
      selViajeFolio.value = previo;
    } catch (err) {
      avisoViaje("No se pudo conectar con el servidor.", false);
    }
  }

  async function refrescarViaje() {
    solicitudActual = solicitudesViaje.find(function (s) { return s.folio === selViajeFolio.value; }) || null;
    const info = document.getElementById("viajeInfo");

    if (!solicitudActual) {
      info.textContent = "Elige una solicitud para empezar.";
      return;
    }

    const s = solicitudActual;
    info.textContent = s.cliente + " · " + s.destino + " · " + s.pasajeros + " pasajero(s) · " +
      formatearFecha(s.salida) + " – " + formatearFecha(s.regreso);

    const d = encodeURIComponent(s.destino);
    const f = encodeURIComponent(s.folio);

    try {
      const respuestas = await Promise.all([
        fetch(API_BASE + "/vuelos?destino=" + d),
        fetch(API_BASE + "/hospedajes?destino=" + d),
        fetch(API_BASE + "/servicios?destino=" + d),
        fetch(API_BASE + "/selecciones?folio=" + f),
        fetch(API_BASE + "/bloqueos?folio=" + f),
      ]);
      const [vuelos, hospedajes, servicios, selecciones, bloqueos] =
        await Promise.all(respuestas.map(function (r) { return r.json(); }));

      llenarTabla("viajeTablaVuelos", vuelos.map(function (v) {
        return filaConBoton([v.aerolinea, v.ruta, v.escala, dinero(v.tarifa_neta)], "Seleccionar", function () {
          seleccionar("Vuelo", v.aerolinea + " · " + v.ruta, v.tarifa_neta);
        });
      }), 5, "No hay vuelos cargados para este destino (cárgalos en el Cotizador).");

      llenarTabla("viajeTablaHospedajes", hospedajes.map(function (h) {
        return filaConBoton([h.hospedaje, h.noches, h.zona, dinero(h.neto_total)], "Seleccionar", function () {
          seleccionar("Hospedaje", h.hospedaje + " (" + h.noches + " noches)", h.neto_total);
        });
      }), 5, "No hay hospedajes cargados para este destino (cárgalos en el Cotizador).");

      llenarTabla("viajeTablaServicios", servicios.map(function (sv) {
        return filaConBoton([sv.servicio, sv.descripcion || "—", dinero(sv.precio)], "Agregar", function () {
          seleccionar("Servicio", sv.servicio, sv.precio);
        });
      }), 4, "No hay servicios cargados para este destino.");

      llenarTabla("viajeTablaSelecciones", selecciones.map(function (x) {
        const tr = document.createElement("tr");
        tr.innerHTML = "<td>" + esc(x.tipo) + "</td><td>" + esc(x.detalle) + "</td><td>" + dinero(x.costo_neto) + "</td>";
        return tr;
      }), 3, "Todavía no hay nada seleccionado.");

      llenarTabla("viajeTablaBloqueos", bloqueos.map(function (b) {
        const tr = document.createElement("tr");
        tr.innerHTML = "<td>" + esc(b.tipo) + "</td><td>" + esc(b.detalle) + "</td><td>" + dinero(b.costo_neto) +
          "</td><td>" + formatearFecha(b.vigencia) + "</td>" +
          '<td><span class="estado ' + claseEstado(b.estado) + '">' + esc(b.estado) + "</span></td>";
        return tr;
      }), 5, "Sin bloqueos.");

    } catch (err) {
      avisoViaje("No se pudo conectar con el servidor.", false);
    }
  }

  selViajeFolio.addEventListener("change", function () {
    msgViaje.textContent = "";
    document.getElementById("resultadoCotizacion").innerHTML = "";
    refrescarViaje();
  });

  document.querySelector('nav.tabs button[data-pantalla="viaje"]').addEventListener("click", async function () {
    await cargarSolicitudesViaje();
    await refrescarViaje();
  });

  // ---- 4.0 Cargar servicio nuevo ----

  conectarFormulario(
    document.getElementById("btnNuevoServicio"),
    document.getElementById("formularioServicio"),
    document.getElementById("btnCancelarServicio"),
    document.getElementById("mensajeFormServicio")
  );

  document.getElementById("btnGuardarServicio").addEventListener("click", async function () {
    const boton = this;
    const msg = document.getElementById("mensajeFormServicio");
    const cuerpo = {
      destino: document.getElementById("servDestino").value.trim(),
      servicio: document.getElementById("servNombre").value.trim(),
      descripcion: document.getElementById("servDescripcion").value.trim(),
      precio: document.getElementById("servPrecio").value,
    };

    if (!cuerpo.destino || !cuerpo.servicio || !cuerpo.precio) {
      msg.textContent = "Completa destino, servicio y precio.";
      msg.className = "mensaje-form error";
      return;
    }

    boton.disabled = true;
    try {
      await postJSON("/servicio", cuerpo);
      msg.textContent = "Servicio guardado.";
      msg.className = "mensaje-form ok";
      ["servNombre", "servDescripcion", "servPrecio"].forEach(function (id) {
        document.getElementById(id).value = "";
      });
      await refrescarViaje();
    } catch (err) {
      msg.textContent = err.message;
      msg.className = "mensaje-form error";
    } finally {
      boton.disabled = false;
    }
  });

  // ---- 5.0 Bloqueos ----

  document.getElementById("btnGenerarBloqueos").addEventListener("click", async function () {
    if (!solicitudActual) { avisoViaje("Elige una solicitud primero.", false); return; }
    try {
      const data = await postJSON("/bloqueos/generar", {
        folio: solicitudActual.folio,
        dias: document.getElementById("bloqueoDias").value
      });
      avisoViaje(data.mensaje, true);
      await refrescarViaje();
    } catch (err) {
      avisoViaje(err.message, false);
    }
  });

  document.getElementById("btnLiberarBloqueos").addEventListener("click", async function () {
    if (!solicitudActual) { avisoViaje("Elige una solicitud primero.", false); return; }
    try {
      const data = await postJSON("/bloqueo/liberar", { folio: solicitudActual.folio });
      avisoViaje(data.mensaje, true);
      await refrescarViaje();
    } catch (err) {
      avisoViaje(err.message, false);
    }
  });

  // ---- 6.0 Generar cotización ----

  document.getElementById("btnGenerarCotizacion").addEventListener("click", async function () {
    if (!solicitudActual) { avisoViaje("Elige una solicitud primero.", false); return; }
    const cont = document.getElementById("resultadoCotizacion");
    try {
      const c = await postJSON("/cotizacion/generar", {
        folio: solicitudActual.folio,
        margen: document.getElementById("cotMargen").value
      });

      cont.innerHTML =
        '<div class="resultado-cotizacion">' +
          '<div class="folio-grande">Cotización ' + esc(c.folio) + "</div>" +
          '<div style="font-size:13px;color:var(--muted);margin-bottom:10px;">' +
            esc(c.cliente) + " · " + esc(c.destino) + " · Solicitud " + esc(c.folio_solicitud) + "</div>" +
          "<table><thead><tr><th>Concepto</th><th>Detalle</th><th>Costo neto</th></tr></thead><tbody>" +
          c.desglose.map(function (d) {
            return "<tr><td>" + esc(d.tipo) + "</td><td>" + esc(d.detalle) + "</td><td>" + dinero(d.costo_neto) + "</td></tr>";
          }).join("") +
          "</tbody></table>" +
          '<div class="totales">Costo neto: ' + dinero(c.costo_neto) +
            "<br>Utilidad (" + c.margen + "%): " + dinero(c.utilidad) +
            "<br><strong>Total cliente: " + dinero(c.total_cliente) + "</strong></div>" +
        "</div>";

      avisoViaje("Cotización " + c.folio + " generada.", true);
      await cargarCotizaciones();
      await cargarResumenCotizaciones();
    } catch (err) {
      cont.innerHTML = "";
      avisoViaje(err.message, false);
    }
  });
```

---

## 7) Nota sobre los cálculos

- La **tarifa del vuelo se multiplica por el número de pasajeros** de la solicitud.
- El **hospedaje y los servicios se toman como total** (tal como los capturas).
- Si quieres otra regla (por ejemplo, servicios por pasajero), se cambia en `recibir_seleccion()` dentro de `app.py`.
