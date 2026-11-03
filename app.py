from flask import Flask, render_template, request, jsonify
from contextlib import contextmanager
from decimal import Decimal
from datetime import date, datetime
import os
import sys
import time
import sqlite3
import threading
import webbrowser

# Motor de base de datos (se elige solo):
#   - Si existe la variable DB_HOST (docker-compose la define) -> PostgreSQL.
#   - Si no existe -> SQLite: un archivo "agencia.db" junto al programa.
#     Es lo que usa el ejecutable, para que no haya que instalar nada.
USAR_PG = bool(os.environ.get("DB_HOST"))

if USAR_PG:
    import psycopg2
    from psycopg2.extras import RealDictCursor


def ruta_base():
    """Carpeta donde vive el programa. Si es un ejecutable (PyInstaller), es la
    carpeta del ejecutable; si es app.py normal, la carpeta de app.py."""
    if getattr(sys, "frozen", False):
        return os.path.dirname(sys.executable)
    return os.path.dirname(os.path.abspath(__file__))


def ruta_recurso(relativa):
    """Ubica archivos empaquetados dentro del ejecutable (templates, schema)."""
    base = getattr(sys, "_MEIPASS", ruta_base())
    return os.path.join(base, relativa)


app = Flask(__name__, template_folder=ruta_recurso("templates"))
app.config["TEMPLATES_AUTO_RELOAD"] = True


@app.after_request
def permitir_cors(respuesta):
    """Permite que la página en GitHub Pages llame a esta API."""
    origen = request.headers.get("Origin", "")
    if origen in ("https://mdbros19.github.io",):
        respuesta.headers["Access-Control-Allow-Origin"] = origen
        respuesta.headers["Access-Control-Allow-Headers"] = "Content-Type"
        respuesta.headers["Access-Control-Allow-Methods"] = "GET, POST, OPTIONS"
    return respuesta


# ==========================================
# CONEXIÓN A LA BASE DE DATOS
# ==========================================

CONFIG_BD = {
    "host": os.environ.get("DB_HOST", "localhost"),
    "port": int(os.environ.get("DB_PORT", "5432")),
    "dbname": os.environ.get("DB_NAME", "agencia"),
    "user": os.environ.get("DB_USER", "agencia"),
    "password": os.environ.get("DB_PASSWORD", "agencia_pass"),
}

# El archivo de SQLite queda SIEMPRE junto al programa (o donde diga AGENCIA_DB).
RUTA_DB = os.environ.get("AGENCIA_DB", os.path.join(ruta_base(), "agencia.db"))


def limpiar(fila):
    """Convierte lo que devuelve la base a algo que JSON entienda:
    Decimal -> número, fecha -> 'AAAA-MM-DD'."""
    resultado = {}
    for clave, valor in fila.items():
        if isinstance(valor, Decimal):
            valor = int(valor) if valor == valor.to_integral_value() else float(valor)
        elif isinstance(valor, (date, datetime)):
            valor = valor.isoformat()
        resultado[clave] = valor
    return resultado


class CursorSQLite:
    """Hace que SQLite se use igual que PostgreSQL: las consultas del programa
    están escritas para PostgreSQL y aquí se traducen lo mínimo necesario."""

    def __init__(self, cur):
        self.cur = cur

    def execute(self, sql, params=()):
        sql = sql.replace("current_date + %s", "date('now','localtime','+' || %s || ' days')")
        sql = sql.replace("current_date", "date('now','localtime')")
        sql = sql.replace("%s", "?")
        self.cur.execute(sql, params)
        return self

    def fetchone(self):
        fila = self.cur.fetchone()
        return dict(fila) if fila else None

    def fetchall(self):
        return [dict(f) for f in self.cur.fetchall()]

    @property
    def rowcount(self):
        return self.cur.rowcount

    @property
    def description(self):
        return self.cur.description


@contextmanager
def cursor():
    """Abre una conexión, entrega un cursor y al final guarda (commit) los
    cambios. Si algo falla, deshace todo (rollback)."""
    if USAR_PG:
        con = psycopg2.connect(**CONFIG_BD)
        try:
            with con:
                with con.cursor(cursor_factory=RealDictCursor) as cur:
                    yield cur
        finally:
            con.close()
    else:
        con = sqlite3.connect(RUTA_DB, timeout=10)
        con.row_factory = sqlite3.Row
        con.execute("PRAGMA foreign_keys = ON")
        try:
            with con:
                yield CursorSQLite(con.cursor())
        finally:
            con.close()


def consultar(sql, params=()):
    """Ejecuta una instrucción SQL. Si devuelve filas, las regresa como lista
    de diccionarios; si no (INSERT/UPDATE), regresa lista vacía."""
    with cursor() as cur:
        cur.execute(sql, params)
        if cur.description:
            return [limpiar(f) for f in cur.fetchall()]
        return []


def iniciar_bd():
    """Crea las tablas si no existen (es seguro repetirlo)."""
    if not USAR_PG:
        with open(ruta_recurso("schema_sqlite.sql"), encoding="utf-8") as f:
            esquema = f.read()
        con = sqlite3.connect(RUTA_DB)
        try:
            con.executescript(esquema)
            con.commit()
        finally:
            con.close()
        print("Base de datos lista:", RUTA_DB)
        return

    ultimo_error = None
    for _ in range(40):
        try:
            with open(ruta_recurso("schema.sql"), encoding="utf-8") as f:
                esquema = f.read()
            with cursor() as cur:
                cur.execute(esquema)
            print("Base de datos lista (PostgreSQL).")
            return
        except psycopg2.OperationalError as e:
            ultimo_error = e
            print("Esperando a PostgreSQL...")
            time.sleep(1.5)
    raise RuntimeError(f"No se pudo conectar a PostgreSQL: {ultimo_error}")


# ==========================================
# MENSAJES DE ERROR AMIGABLES
# ==========================================

ERR_INTEGRIDAD = psycopg2.IntegrityError if USAR_PG else sqlite3.IntegrityError
ERR_DATOS = psycopg2.DataError if USAR_PG else sqlite3.DataError
ERR_BD = psycopg2.Error if USAR_PG else sqlite3.Error


@app.errorhandler(ERR_INTEGRIDAD)
def error_integridad(e):
    return jsonify({"error": "Los datos no cumplen las reglas de la base de datos "
                             "(dato repetido, fechas invertidas o valor fuera de rango)."}), 400


@app.errorhandler(ERR_DATOS)
def error_datos(e):
    return jsonify({"error": "Algún dato tiene un formato inválido (revisa fechas y números)."}), 400


@app.errorhandler(ERR_BD)
def error_bd(e):
    print("Error de base de datos:", e)
    return jsonify({"error": "Error en la base de datos. Revisa la ventana del programa."}), 500


# ==========================================
# HELPERS
# ==========================================

def validar_campos(datos, requeridos):
    """Devuelve la lista de campos requeridos que faltan o vienen vacíos."""
    return [c for c in requeridos if datos.get(c) in (None, "")]


def numero(valor):
    """Convierte a número o devuelve None si no es válido."""
    try:
        return float(valor)
    except (TypeError, ValueError):
        return None


def json_o_error():
    datos = request.get_json(silent=True)
    if not datos:
        return None, (jsonify({"error": "JSON inválido o vacío"}), 400)
    return datos, None


def listar_por_destino(tabla, columnas):
    """SELECT de una tabla; si viene ?destino=..., filtra sin importar mayúsculas."""
    destino = request.args.get("destino", "").strip()
    if destino:
        return consultar(f"SELECT {columnas} FROM {tabla} "
                         "WHERE lower(destino) = lower(%s) ORDER BY id", (destino,))
    return consultar(f"SELECT {columnas} FROM {tabla} ORDER BY id")


def buscar_solicitud(folio):
    filas = consultar(
        "SELECT s.id, s.folio, s.destino, s.pasajeros, c.nombre AS cliente "
        "FROM solicitudes s JOIN clientes c ON c.id = s.cliente_id "
        "WHERE upper(s.folio) = upper(%s)", (str(folio).strip(),))
    return filas[0] if filas else None


def bloqueos_de(solicitud_id):
    """Bloqueos de una solicitud con su estado real: si estaba 'Vigente' pero
    ya pasó su fecha, se muestra como 'Vencido'."""
    return consultar(
        "SELECT s.folio, b.tipo, b.detalle, b.costo_neto, b.vigencia, "
        "CASE WHEN b.estado = 'Vigente' AND b.vigencia < current_date "
        "THEN 'Vencido' ELSE b.estado END AS estado "
        "FROM bloqueos b JOIN solicitudes s ON s.id = b.solicitud_id "
        "WHERE b.solicitud_id = %s ORDER BY b.id", (solicitud_id,))


# ==========================================
# PÁGINA PRINCIPAL
# ==========================================

@app.route("/")
def inicio():
    return render_template("index.html")


# ==========================================
# 1.0 REGISTRAR SOLICITUD  (-> almacén Clientes)
# ==========================================

@app.route("/solicitud", methods=["POST"])
def recibir_solicitud():
    datos, error = json_o_error()
    if error:
        return error

    campos = ["cliente", "destino", "categoria", "pasajeros", "salida", "regreso"]
    faltantes = validar_campos(datos, campos)
    if faltantes:
        return jsonify({"error": "Faltan campos obligatorios", "campos": faltantes}), 400

    pasajeros = numero(datos["pasajeros"])
    if pasajeros is None or pasajeros < 1:
        return jsonify({"error": "El número de pasajeros debe ser al menos 1"}), 400

    try:
        f_salida = date.fromisoformat(str(datos["salida"]))
        f_regreso = date.fromisoformat(str(datos["regreso"]))
    except ValueError:
        return jsonify({"error": "Las fechas no son válidas"}), 400
    if f_regreso < f_salida:
        return jsonify({"error": "La fecha de regreso no puede ser anterior a la de salida."}), 400

    with cursor() as cur:
        # Datos personales del cliente -> tabla clientes (uno por nombre)
        cur.execute(
            "INSERT INTO clientes (nombre, telefono, correo) VALUES (%s, %s, %s) "
            "ON CONFLICT ((lower(nombre))) DO UPDATE SET "
            "telefono = COALESCE(NULLIF(EXCLUDED.telefono, ''), clientes.telefono), "
            "correo   = COALESCE(NULLIF(EXCLUDED.correo, ''),   clientes.correo) "
            "RETURNING id",
            (datos["cliente"].strip(), (datos.get("telefono") or "").strip(),
             (datos.get("correo") or "").strip()))
        cliente_id = cur.fetchone()["id"]

        cur.execute(
            "INSERT INTO solicitudes (cliente_id, destino, categoria, pasajeros, salida, regreso) "
            "VALUES (%s, %s, %s, %s, %s, %s) RETURNING id",
            (cliente_id, datos["destino"].strip(), datos["categoria"], int(pasajeros),
             datos["salida"], datos["regreso"]))
        solicitud_id = cur.fetchone()["id"]

        folio = f"S-{solicitud_id:03d}"
        cur.execute("UPDATE solicitudes SET folio = %s WHERE id = %s", (folio, solicitud_id))

    return jsonify({"mensaje": "Solicitud guardada correctamente", "folio": folio})


@app.route("/solicitudes", methods=["GET"])
def obtener_solicitudes():
    return jsonify(consultar(
        "SELECT c.nombre AS cliente, s.destino, s.categoria, s.pasajeros, "
        "s.salida, s.regreso, s.folio "
        "FROM solicitudes s JOIN clientes c ON c.id = s.cliente_id ORDER BY s.id"))


@app.route("/clientes", methods=["GET"])
def obtener_clientes():
    return jsonify(consultar("SELECT nombre, telefono, correo FROM clientes ORDER BY id"))


# ==========================================
# 2.0 REGISTRAR VUELO  (-> almacén Vuelos)
# ==========================================

@app.route("/vuelo", methods=["POST"])
def recibir_vuelo():
    datos, error = json_o_error()
    if error:
        return error

    campos = ["destino", "aerolinea", "ruta", "escala", "tarifa_neta", "cupos"]
    faltantes = validar_campos(datos, campos)
    if faltantes:
        return jsonify({"error": "Faltan campos obligatorios", "campos": faltantes}), 400

    tarifa, cupos = numero(datos["tarifa_neta"]), numero(datos["cupos"])
    if tarifa is None or tarifa < 0 or cupos is None or cupos < 0:
        return jsonify({"error": "Tarifa y cupos deben ser números válidos"}), 400

    consultar("INSERT INTO vuelos (destino, aerolinea, ruta, escala, tarifa_neta, cupos) "
              "VALUES (%s, %s, %s, %s, %s, %s)",
              (datos["destino"].strip(), datos["aerolinea"].strip(), datos["ruta"].strip(),
               datos["escala"], tarifa, int(cupos)))
    return jsonify({"mensaje": "Vuelo guardado correctamente"})


@app.route("/vuelos", methods=["GET"])
def obtener_vuelos():
    return jsonify(listar_por_destino(
        "vuelos", "destino, aerolinea, ruta, escala, tarifa_neta, cupos"))


# ==========================================
# 3.0 REGISTRAR HOSPEDAJE
# ==========================================

@app.route("/hospedaje", methods=["POST"])
def recibir_hospedaje():
    datos, error = json_o_error()
    if error:
        return error

    campos = ["destino", "hospedaje", "noches", "zona", "neto_total", "categoria"]
    faltantes = validar_campos(datos, campos)
    if faltantes:
        return jsonify({"error": "Faltan campos obligatorios", "campos": faltantes}), 400

    noches, neto, cat = numero(datos["noches"]), numero(datos["neto_total"]), numero(datos["categoria"])
    if None in (noches, neto, cat) or noches < 1 or neto < 0 or not 1 <= cat <= 5:
        return jsonify({"error": "Noches, neto y categoría deben ser números válidos"}), 400

    consultar("INSERT INTO hospedajes (destino, hospedaje, noches, zona, neto_total, categoria) "
              "VALUES (%s, %s, %s, %s, %s, %s)",
              (datos["destino"].strip(), datos["hospedaje"].strip(), int(noches),
               datos["zona"].strip(), neto, int(cat)))
    return jsonify({"mensaje": "Hospedaje guardado correctamente"})


@app.route("/hospedajes", methods=["GET"])
def obtener_hospedajes():
    return jsonify(listar_por_destino(
        "hospedajes", "destino, hospedaje, noches, zona, neto_total, categoria"))


# ==========================================
# 4.0 REGISTRAR SERVICIOS COMPLEMENTARIOS  (-> almacén Servicios)
# ==========================================

@app.route("/servicio", methods=["POST"])
def recibir_servicio():
    datos, error = json_o_error()
    if error:
        return error

    faltantes = validar_campos(datos, ["destino", "servicio", "precio"])
    if faltantes:
        return jsonify({"error": "Faltan campos obligatorios", "campos": faltantes}), 400

    precio = numero(datos["precio"])
    if precio is None or precio < 0:
        return jsonify({"error": "El precio debe ser un número válido"}), 400

    consultar("INSERT INTO servicios (destino, servicio, descripcion, precio) "
              "VALUES (%s, %s, %s, %s)",
              (datos["destino"].strip(), datos["servicio"].strip(),
               (datos.get("descripcion") or "").strip(), precio))
    return jsonify({"mensaje": "Servicio guardado correctamente"})


@app.route("/servicios", methods=["GET"])
def obtener_servicios():
    return jsonify(listar_por_destino("servicios", "destino, servicio, descripcion, precio"))


# ---------- Selecciones de una solicitud (vuelo -> hospedaje -> servicios) ----------

@app.route("/seleccion", methods=["POST"])
def recibir_seleccion():
    """Guarda lo que el agente eligió para una solicitud. Respeta el orden del
    diagrama: primero vuelo (2.0), luego hospedaje (3.0), luego servicios (4.0)."""
    datos, error = json_o_error()
    if error:
        return error

    faltantes = validar_campos(datos, ["folio", "tipo", "detalle", "costo"])
    if faltantes:
        return jsonify({"error": "Faltan campos obligatorios", "campos": faltantes}), 400

    tipo = datos["tipo"]
    if tipo not in ("Vuelo", "Hospedaje", "Servicio"):
        return jsonify({"error": "El tipo debe ser Vuelo, Hospedaje o Servicio"}), 400

    solicitud = buscar_solicitud(datos["folio"])
    if not solicitud:
        return jsonify({"error": "No existe una solicitud con ese folio"}), 404

    costo = numero(datos["costo"])
    if costo is None or costo < 0:
        return jsonify({"error": "El costo no es válido"}), 400

    sid = solicitud["id"]

    with cursor() as cur:
        cur.execute("SELECT 1 FROM bloqueos WHERE solicitud_id = %s "
                    "AND estado = 'Vigente' AND vigencia >= current_date", (sid,))
        if cur.fetchone():
            return jsonify({"error": "Esta solicitud ya tiene bloqueos vigentes. "
                                     "Libéralos antes de cambiar la selección."}), 400

        cur.execute("SELECT DISTINCT tipo FROM selecciones WHERE solicitud_id = %s", (sid,))
        previos = {f["tipo"] for f in cur.fetchall()}

        if tipo == "Hospedaje" and "Vuelo" not in previos:
            return jsonify({"error": "Primero selecciona un vuelo (proceso 2.0)."}), 400
        if tipo == "Servicio" and "Hospedaje" not in previos:
            return jsonify({"error": "Primero selecciona un hospedaje (proceso 3.0)."}), 400

        # La tarifa del vuelo es por pasajero; hospedaje y servicios son total.
        if tipo == "Vuelo":
            costo = costo * int(solicitud["pasajeros"])

        if tipo in ("Vuelo", "Hospedaje"):  # solo uno de cada uno por solicitud
            cur.execute("DELETE FROM selecciones WHERE solicitud_id = %s AND tipo = %s", (sid, tipo))

        cur.execute("INSERT INTO selecciones (solicitud_id, tipo, detalle, costo_neto) "
                    "VALUES (%s, %s, %s, %s)", (sid, tipo, datos["detalle"], costo))

    return jsonify({"mensaje": f"{tipo} seleccionado", "costo_neto": costo})


@app.route("/selecciones", methods=["GET"])
def obtener_selecciones():
    folio = request.args.get("folio", "").strip()
    sql = ("SELECT s.folio, x.tipo, x.detalle, x.costo_neto "
           "FROM selecciones x JOIN solicitudes s ON s.id = x.solicitud_id ")
    if folio:
        return jsonify(consultar(sql + "WHERE upper(s.folio) = upper(%s) ORDER BY x.id", (folio,)))
    return jsonify(consultar(sql + "ORDER BY x.id"))


# ==========================================
# 5.0 ADMINISTRAR BLOQUEOS  (-> almacén Bloqueos)
# ==========================================

@app.route("/bloqueos/generar", methods=["POST"])
def generar_bloqueos():
    """Bloquea (aparta) lo seleccionado por 'dias' días."""
    datos, error = json_o_error()
    if error:
        return error

    if not datos.get("folio"):
        return jsonify({"error": "Falta el folio de la solicitud"}), 400

    solicitud = buscar_solicitud(datos["folio"])
    if not solicitud:
        return jsonify({"error": "No existe una solicitud con ese folio"}), 404

    dias = numero(datos.get("dias")) or 3
    dias = int(min(max(dias, 1), 60))
    sid = solicitud["id"]

    with cursor() as cur:
        cur.execute("SELECT DISTINCT tipo FROM selecciones WHERE solicitud_id = %s", (sid,))
        tipos = {f["tipo"] for f in cur.fetchall()}
        if not {"Vuelo", "Hospedaje"} <= tipos:
            return jsonify({"error": "Para bloquear necesitas un vuelo y un hospedaje seleccionados."}), 400

        cur.execute("SELECT 1 FROM bloqueos WHERE solicitud_id = %s "
                    "AND estado = 'Vigente' AND vigencia >= current_date", (sid,))
        if cur.fetchone():
            return jsonify({"error": "Esta solicitud ya tiene bloqueos vigentes."}), 400

        cur.execute(
            "INSERT INTO bloqueos (solicitud_id, tipo, detalle, costo_neto, vigencia, estado) "
            "SELECT solicitud_id, tipo, detalle, costo_neto, current_date + %s, 'Vigente' "
            "FROM selecciones WHERE solicitud_id = %s ORDER BY id RETURNING vigencia",
            (dias, sid))
        filas = cur.fetchall()
        hasta = str(filas[0]["vigencia"])[:10]

    return jsonify({"mensaje": f"{len(filas)} bloqueo(s) vigentes hasta {hasta}", "vigencia": hasta})


@app.route("/bloqueos", methods=["GET"])
def obtener_bloqueos():
    folio = request.args.get("folio", "").strip()
    if not folio:
        return jsonify(consultar(
            "SELECT s.folio, b.tipo, b.detalle, b.costo_neto, b.vigencia, "
            "CASE WHEN b.estado = 'Vigente' AND b.vigencia < current_date "
            "THEN 'Vencido' ELSE b.estado END AS estado "
            "FROM bloqueos b JOIN solicitudes s ON s.id = b.solicitud_id ORDER BY b.id"))

    solicitud = buscar_solicitud(folio)
    return jsonify(bloqueos_de(solicitud["id"]) if solicitud else [])


@app.route("/bloqueo/liberar", methods=["POST"])
def liberar_bloqueos():
    datos, error = json_o_error()
    if error:
        return error

    if not datos.get("folio"):
        return jsonify({"error": "Falta el folio de la solicitud"}), 400

    solicitud = buscar_solicitud(datos["folio"])
    if not solicitud:
        return jsonify({"error": "No existe una solicitud con ese folio"}), 404

    with cursor() as cur:
        cur.execute("UPDATE bloqueos SET estado = 'Liberado' "
                    "WHERE solicitud_id = %s AND estado = 'Vigente'", (solicitud["id"],))
        liberados = cur.rowcount

    if liberados == 0:
        return jsonify({"error": "Esa solicitud no tiene bloqueos vigentes"}), 404

    return jsonify({"mensaje": f"{liberados} bloqueo(s) liberados"})


# ==========================================
# ALTERNATIVAS (catálogo: recomendada / vip / accesible)
# ==========================================

@app.route("/alternativa", methods=["POST"])
def recibir_alternativa():
    datos, error = json_o_error()
    if error:
        return error

    campos = ["destino", "categoria", "aerolinea", "precio"]
    faltantes = validar_campos(datos, campos)
    if faltantes:
        return jsonify({"error": "Faltan campos obligatorios", "campos": faltantes}), 400

    precio = numero(datos["precio"])
    if precio is None or precio < 0:
        return jsonify({"error": "El precio debe ser un número válido"}), 400

    consultar("INSERT INTO alternativas (destino, categoria, aerolinea, precio, imagen) "
              "VALUES (%s, %s, %s, %s, %s)",
              (datos["destino"].strip(), datos["categoria"], datos["aerolinea"].strip(),
               precio, datos.get("imagen") or "🧳"))
    return jsonify({"mensaje": "Alternativa guardada correctamente"})


@app.route("/alternativas", methods=["GET"])
def obtener_alternativas():
    return jsonify(listar_por_destino("alternativas", "destino, categoria, aerolinea, precio, imagen"))


# ==========================================
# DOCUMENTACIÓN NECESARIA (checklist por destino)
# ==========================================

@app.route("/documentacion", methods=["POST"])
def guardar_documentacion():
    datos, error = json_o_error()
    if error:
        return error

    if not datos.get("destino"):
        return jsonify({"error": "Falta el destino"}), 400

    viable = bool(datos.get("viable", True))

    # Un destino = una sola fila: si ya existe se actualiza, si no se crea.
    consultar(
        "INSERT INTO documentacion (destino, pasaporte, visa, identificacion, otros, viable, razon) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s) "
        "ON CONFLICT ((lower(destino))) DO UPDATE SET "
        "pasaporte = EXCLUDED.pasaporte, visa = EXCLUDED.visa, "
        "identificacion = EXCLUDED.identificacion, otros = EXCLUDED.otros, "
        "viable = EXCLUDED.viable, razon = EXCLUDED.razon",
        (datos["destino"].strip(), bool(datos.get("pasaporte", False)),
         bool(datos.get("visa", False)), bool(datos.get("identificacion", False)),
         datos.get("otros", "") or "", viable,
         "" if viable else (datos.get("razon", "") or "")))
    return jsonify({"mensaje": "Documentación guardada correctamente"})


@app.route("/documentacion", methods=["GET"])
def obtener_documentacion():
    registros = listar_por_destino(
        "documentacion", "destino, pasaporte, visa, identificacion, otros, viable, razon")

    if request.args.get("destino", "").strip():
        return jsonify(registros[0] if registros else None)
    return jsonify(registros)


# ==========================================
# 6.0 GENERAR COTIZACIÓN  (-> Cliente, con su folio)
# ==========================================

@app.route("/cotizacion/generar", methods=["POST"])
def generar_cotizacion():
    """Arma la cotización a partir de los bloqueos vigentes de la solicitud."""
    datos, error = json_o_error()
    if error:
        return error

    if not datos.get("folio"):
        return jsonify({"error": "Falta el folio de la solicitud"}), 400

    solicitud = buscar_solicitud(datos["folio"])
    if not solicitud:
        return jsonify({"error": "No existe una solicitud con ese folio"}), 404

    margen = numero(datos.get("margen"))
    if margen is None:
        margen = 20.0
    if margen < 0:
        return jsonify({"error": "El margen no puede ser negativo"}), 400

    with cursor() as cur:
        cur.execute("SELECT tipo, detalle, costo_neto FROM bloqueos "
                    "WHERE solicitud_id = %s AND estado = 'Vigente' AND vigencia >= current_date "
                    "ORDER BY id", (solicitud["id"],))
        vigentes = [limpiar(f) for f in cur.fetchall()]

        if not {"Vuelo", "Hospedaje"} <= {b["tipo"] for b in vigentes}:
            return jsonify({"error": "Necesitas bloqueos vigentes de vuelo y hospedaje (proceso 5.0)."}), 400

        costo_neto = round(sum(b["costo_neto"] for b in vigentes), 2)
        utilidad = round(costo_neto * margen / 100, 2)
        total_cliente = round(costo_neto + utilidad, 2)

        cur.execute(
            "INSERT INTO cotizaciones (solicitud_id, cliente, destino, costo_neto, utilidad, "
            "total_cliente, estado) VALUES (%s, %s, %s, %s, %s, %s, 'Cotizada') RETURNING id",
            (solicitud["id"], solicitud["cliente"], solicitud["destino"],
             costo_neto, utilidad, total_cliente))
        cotizacion_id = cur.fetchone()["id"]
        folio_cot = f"C-{cotizacion_id:03d}"
        cur.execute("UPDATE cotizaciones SET folio = %s WHERE id = %s", (folio_cot, cotizacion_id))

    return jsonify({
        "mensaje": "Cotización generada correctamente",
        "folio": folio_cot,
        "folio_solicitud": solicitud["folio"],
        "cliente": solicitud["cliente"],
        "destino": solicitud["destino"],
        "desglose": vigentes,
        "costo_neto": costo_neto,
        "margen": margen,
        "utilidad": utilidad,
        "total_cliente": total_cliente,
    })


@app.route("/cotizacion", methods=["POST"])
def recibir_cotizacion():
    """Captura manual: sirve para cotizaciones fuera del flujo."""
    datos, error = json_o_error()
    if error:
        return error

    campos = ["cliente", "destino", "costo_neto", "utilidad", "total_cliente", "estado"]
    faltantes = validar_campos(datos, campos)
    if faltantes:
        return jsonify({"error": "Faltan campos obligatorios", "campos": faltantes}), 400

    costo, util, total = (numero(datos["costo_neto"]), numero(datos["utilidad"]),
                          numero(datos["total_cliente"]))
    if None in (costo, util, total):
        return jsonify({"error": "Costo, utilidad y total deben ser números"}), 400

    solicitud = buscar_solicitud(datos["folio_solicitud"]) if datos.get("folio_solicitud") else None

    with cursor() as cur:
        cur.execute(
            "INSERT INTO cotizaciones (folio, solicitud_id, cliente, destino, costo_neto, "
            "utilidad, total_cliente, estado) VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id",
            (datos.get("folio") or None, solicitud["id"] if solicitud else None,
             datos["cliente"].strip(), datos["destino"].strip(), costo, util, total, datos["estado"]))
        nuevo_id = cur.fetchone()["id"]
        folio = datos.get("folio") or f"C-{nuevo_id:03d}"
        cur.execute("UPDATE cotizaciones SET folio = %s WHERE id = %s", (folio, nuevo_id))

    return jsonify({"mensaje": "Cotización guardada correctamente", "folio": folio})


@app.route("/cotizaciones", methods=["GET"])
def obtener_cotizaciones():
    return jsonify(consultar(
        "SELECT c.folio, c.cliente, c.destino, c.costo_neto, c.utilidad, c.total_cliente, "
        "c.estado, s.folio AS folio_solicitud "
        "FROM cotizaciones c LEFT JOIN solicitudes s ON s.id = c.solicitud_id ORDER BY c.id"))


if __name__ == "__main__":
    iniciar_bd()
    if USAR_PG:
        # Dentro de Docker: escuchar en todas las interfaces de la caja.
        app.run(host="0.0.0.0", port=5000, debug=False)
    else:
        # Ejecutable / uso local: abre el navegador solo.
        threading.Timer(1.5, lambda: webbrowser.open("http://127.0.0.1:5000/")).start()
        print("Rumbo esta corriendo en http://127.0.0.1:5000")
        print("Para apagarlo, cierra esta ventana.")
        app.run(host="127.0.0.1", port=5000, debug=False)
