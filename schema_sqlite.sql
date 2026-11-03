-- Esquema de la agencia "Rumbo" para SQLite (lo usa el ejecutable).
-- Es seguro repetirlo: CREATE TABLE IF NOT EXISTS no borra nada.

CREATE TABLE IF NOT EXISTS clientes (
    id        INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre    TEXT NOT NULL,
    telefono  TEXT NOT NULL DEFAULT '',
    correo    TEXT NOT NULL DEFAULT ''
);
CREATE UNIQUE INDEX IF NOT EXISTS clientes_nombre_uq ON clientes (lower(nombre));

CREATE TABLE IF NOT EXISTS solicitudes (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    folio       TEXT UNIQUE,
    cliente_id  INTEGER NOT NULL REFERENCES clientes(id),
    destino     TEXT NOT NULL,
    categoria   TEXT NOT NULL,
    pasajeros   INTEGER NOT NULL CHECK (pasajeros > 0),
    salida      TEXT NOT NULL,
    regreso     TEXT NOT NULL,
    CHECK (regreso >= salida)
);

CREATE TABLE IF NOT EXISTS vuelos (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    destino      TEXT NOT NULL,
    aerolinea    TEXT NOT NULL,
    ruta         TEXT NOT NULL,
    escala       TEXT NOT NULL,
    tarifa_neta  REAL NOT NULL CHECK (tarifa_neta >= 0),
    cupos        INTEGER NOT NULL CHECK (cupos >= 0)
);

CREATE TABLE IF NOT EXISTS hospedajes (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    destino     TEXT NOT NULL,
    hospedaje   TEXT NOT NULL,
    noches      INTEGER NOT NULL CHECK (noches > 0),
    zona        TEXT NOT NULL,
    neto_total  REAL NOT NULL CHECK (neto_total >= 0),
    categoria   INTEGER NOT NULL CHECK (categoria BETWEEN 1 AND 5)
);

CREATE TABLE IF NOT EXISTS servicios (
    id           INTEGER PRIMARY KEY AUTOINCREMENT,
    destino      TEXT NOT NULL,
    servicio     TEXT NOT NULL,
    descripcion  TEXT NOT NULL DEFAULT '',
    precio       REAL NOT NULL CHECK (precio >= 0)
);

CREATE TABLE IF NOT EXISTS selecciones (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    solicitud_id  INTEGER NOT NULL REFERENCES solicitudes(id) ON DELETE CASCADE,
    tipo          TEXT NOT NULL CHECK (tipo IN ('Vuelo', 'Hospedaje', 'Servicio')),
    detalle       TEXT NOT NULL,
    costo_neto    REAL NOT NULL CHECK (costo_neto >= 0)
);

CREATE TABLE IF NOT EXISTS bloqueos (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    solicitud_id  INTEGER NOT NULL REFERENCES solicitudes(id) ON DELETE CASCADE,
    tipo          TEXT NOT NULL,
    detalle       TEXT NOT NULL,
    costo_neto    REAL NOT NULL,
    vigencia      TEXT NOT NULL,
    estado        TEXT NOT NULL DEFAULT 'Vigente' CHECK (estado IN ('Vigente', 'Liberado'))
);

CREATE TABLE IF NOT EXISTS cotizaciones (
    id             INTEGER PRIMARY KEY AUTOINCREMENT,
    folio          TEXT UNIQUE,
    solicitud_id   INTEGER REFERENCES solicitudes(id) ON DELETE SET NULL,
    cliente        TEXT NOT NULL,
    destino        TEXT NOT NULL,
    costo_neto     REAL NOT NULL,
    utilidad       REAL NOT NULL,
    total_cliente  REAL NOT NULL,
    estado         TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS alternativas (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    destino    TEXT NOT NULL,
    categoria  TEXT NOT NULL,
    aerolinea  TEXT NOT NULL,
    precio     REAL NOT NULL CHECK (precio >= 0),
    imagen     TEXT NOT NULL DEFAULT ''
);

CREATE TABLE IF NOT EXISTS documentacion (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    destino         TEXT NOT NULL,
    pasaporte       INTEGER NOT NULL DEFAULT 0,
    visa            INTEGER NOT NULL DEFAULT 0,
    identificacion  INTEGER NOT NULL DEFAULT 0,
    otros           TEXT NOT NULL DEFAULT '',
    viable          INTEGER NOT NULL DEFAULT 1,
    razon           TEXT NOT NULL DEFAULT ''
);
CREATE UNIQUE INDEX IF NOT EXISTS documentacion_destino_uq ON documentacion (lower(destino));

-- Ejemplos para que el Cotizador no se vea vacío (solo si la tabla está vacía)
INSERT INTO alternativas (destino, categoria, aerolinea, precio, imagen)
SELECT destino, categoria, aerolinea, precio, imagen FROM (
    SELECT 'Tokio' AS destino, 'Recomendada' AS categoria, 'United Airlines' AS aerolinea, 8100 AS precio, '🗼' AS imagen
    UNION ALL SELECT 'Tokio', 'VIP', 'ANA All Nippon Airways', 12400, '🗼'
    UNION ALL SELECT 'Tokio', 'Tarifa accesible', 'Aeromexico', 6200, '🗼'
)
WHERE NOT EXISTS (SELECT 1 FROM alternativas);
