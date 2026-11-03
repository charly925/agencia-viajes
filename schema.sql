-- Esquema de la agencia de viajes "Rumbo" (PostgreSQL).
-- Se ejecuta solo cada vez que arranca la app; es seguro repetirlo
-- (CREATE TABLE IF NOT EXISTS no borra nada).

-- Almacén "Clientes" (proceso 1.0)
CREATE TABLE IF NOT EXISTS clientes (
    id        SERIAL PRIMARY KEY,
    nombre    TEXT NOT NULL,
    telefono  TEXT NOT NULL DEFAULT '',
    correo    TEXT NOT NULL DEFAULT ''
);
CREATE UNIQUE INDEX IF NOT EXISTS clientes_nombre_uq ON clientes (lower(nombre));

-- Solicitudes de viaje (proceso 1.0)
CREATE TABLE IF NOT EXISTS solicitudes (
    id          SERIAL PRIMARY KEY,
    folio       TEXT UNIQUE,
    cliente_id  INTEGER NOT NULL REFERENCES clientes(id),
    destino     TEXT NOT NULL,
    categoria   TEXT NOT NULL,
    pasajeros   INTEGER NOT NULL CHECK (pasajeros > 0),
    salida      DATE NOT NULL,
    regreso     DATE NOT NULL,
    CHECK (regreso >= salida)
);

-- Almacén "Vuelos" (proceso 2.0)
CREATE TABLE IF NOT EXISTS vuelos (
    id           SERIAL PRIMARY KEY,
    destino      TEXT NOT NULL,
    aerolinea    TEXT NOT NULL,
    ruta         TEXT NOT NULL,
    escala       TEXT NOT NULL,
    tarifa_neta  NUMERIC(12,2) NOT NULL CHECK (tarifa_neta >= 0),
    cupos        INTEGER NOT NULL CHECK (cupos >= 0)
);

-- Hospedajes (proceso 3.0)
CREATE TABLE IF NOT EXISTS hospedajes (
    id          SERIAL PRIMARY KEY,
    destino     TEXT NOT NULL,
    hospedaje   TEXT NOT NULL,
    noches      INTEGER NOT NULL CHECK (noches > 0),
    zona        TEXT NOT NULL,
    neto_total  NUMERIC(12,2) NOT NULL CHECK (neto_total >= 0),
    categoria   INTEGER NOT NULL CHECK (categoria BETWEEN 1 AND 5)
);

-- Almacén "Servicios" (proceso 4.0)
CREATE TABLE IF NOT EXISTS servicios (
    id           SERIAL PRIMARY KEY,
    destino      TEXT NOT NULL,
    servicio     TEXT NOT NULL,
    descripcion  TEXT NOT NULL DEFAULT '',
    precio       NUMERIC(12,2) NOT NULL CHECK (precio >= 0)
);

-- Lo que el agente elige para cada solicitud (procesos 2.0, 3.0 y 4.0)
CREATE TABLE IF NOT EXISTS selecciones (
    id            SERIAL PRIMARY KEY,
    solicitud_id  INTEGER NOT NULL REFERENCES solicitudes(id) ON DELETE CASCADE,
    tipo          TEXT NOT NULL CHECK (tipo IN ('Vuelo', 'Hospedaje', 'Servicio')),
    detalle       TEXT NOT NULL,
    costo_neto    NUMERIC(12,2) NOT NULL CHECK (costo_neto >= 0)
);

-- Almacén "Bloqueos" (proceso 5.0)
CREATE TABLE IF NOT EXISTS bloqueos (
    id            SERIAL PRIMARY KEY,
    solicitud_id  INTEGER NOT NULL REFERENCES solicitudes(id) ON DELETE CASCADE,
    tipo          TEXT NOT NULL,
    detalle       TEXT NOT NULL,
    costo_neto    NUMERIC(12,2) NOT NULL,
    vigencia      DATE NOT NULL,
    estado        TEXT NOT NULL DEFAULT 'Vigente' CHECK (estado IN ('Vigente', 'Liberado'))
);

-- Cotizaciones (proceso 6.0)
CREATE TABLE IF NOT EXISTS cotizaciones (
    id             SERIAL PRIMARY KEY,
    folio          TEXT UNIQUE,
    solicitud_id   INTEGER REFERENCES solicitudes(id) ON DELETE SET NULL,
    cliente        TEXT NOT NULL,
    destino        TEXT NOT NULL,
    costo_neto     NUMERIC(12,2) NOT NULL,
    utilidad       NUMERIC(12,2) NOT NULL,
    total_cliente  NUMERIC(12,2) NOT NULL,
    estado         TEXT NOT NULL
);

-- Catálogo del Cotizador
CREATE TABLE IF NOT EXISTS alternativas (
    id         SERIAL PRIMARY KEY,
    destino    TEXT NOT NULL,
    categoria  TEXT NOT NULL,
    aerolinea  TEXT NOT NULL,
    precio     NUMERIC(12,2) NOT NULL CHECK (precio >= 0),
    imagen     TEXT NOT NULL DEFAULT ''
);

-- Documentación necesaria: una fila por destino
CREATE TABLE IF NOT EXISTS documentacion (
    id              SERIAL PRIMARY KEY,
    destino         TEXT NOT NULL,
    pasaporte       BOOLEAN NOT NULL DEFAULT FALSE,
    visa            BOOLEAN NOT NULL DEFAULT FALSE,
    identificacion  BOOLEAN NOT NULL DEFAULT FALSE,
    otros           TEXT NOT NULL DEFAULT '',
    viable          BOOLEAN NOT NULL DEFAULT TRUE,
    razon           TEXT NOT NULL DEFAULT ''
);
CREATE UNIQUE INDEX IF NOT EXISTS documentacion_destino_uq ON documentacion (lower(destino));

-- Ejemplos para que el Cotizador no se vea vacío (solo si la tabla está vacía)
INSERT INTO alternativas (destino, categoria, aerolinea, precio, imagen)
SELECT * FROM (VALUES
    ('Tokio', 'Recomendada',      'United Airlines',        8100, '🗼'),
    ('Tokio', 'VIP',              'ANA All Nippon Airways', 12400, '🗼'),
    ('Tokio', 'Tarifa accesible', 'Aeromexico',             6200, '🗼')
) AS ejemplo(destino, categoria, aerolinea, precio, imagen)
WHERE NOT EXISTS (SELECT 1 FROM alternativas);
