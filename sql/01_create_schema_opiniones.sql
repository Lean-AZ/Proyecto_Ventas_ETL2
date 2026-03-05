-- =============================================================================
-- Sistema de Análisis de Opiniones de Clientes - Schema (modelo estrella)
-- Compatible con SQLite. Creación de tablas con PK, FK e índices.
-- =============================================================================

-- Dimensión: Productos (alineada con products.csv para ETL)
CREATE TABLE IF NOT EXISTS dim_producto (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre          TEXT NOT NULL,
    categoria       TEXT,
    precio          REAL,
    stock           INTEGER,
    creado_en       TEXT DEFAULT (datetime('now')),
    actualizado_en  TEXT DEFAULT (datetime('now'))
);

-- Dimensión: Clientes (alineada con customers.csv para ETL)
CREATE TABLE IF NOT EXISTS dim_cliente (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre_completo TEXT,
    email           TEXT,
    telefono        TEXT,
    ciudad          TEXT,
    pais            TEXT,
    creado_en       TEXT DEFAULT (datetime('now')),
    actualizado_en  TEXT DEFAULT (datetime('now'))
);

-- Dimensión: Fecha (calendario analítico; id = YYYYMMDD para rangos)
CREATE TABLE IF NOT EXISTS dim_fecha (
    id              INTEGER PRIMARY KEY,
    fecha           TEXT NOT NULL UNIQUE,
    anio            INTEGER NOT NULL,
    mes             INTEGER NOT NULL,
    trimestre       INTEGER NOT NULL,
    semana          INTEGER NOT NULL,
    dia_semana      INTEGER,
    nombre_mes      TEXT,
    nombre_dia      TEXT
);

-- Dimensión: Fuente del comentario (encuesta, web, redes sociales)
CREATE TABLE IF NOT EXISTS dim_fuente (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre          TEXT NOT NULL UNIQUE,
    descripcion     TEXT,
    creado_en       TEXT DEFAULT (datetime('now'))
);

-- Tabla de hechos: Opiniones / comentarios procesados por el ETL
CREATE TABLE IF NOT EXISTS hechos_opiniones (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    producto_id     INTEGER NOT NULL,
    cliente_id      INTEGER,
    fecha_id        INTEGER NOT NULL,
    fuente_id       INTEGER NOT NULL,
    calificacion    INTEGER,
    sentimiento     TEXT CHECK (sentimiento IN ('positivo', 'negativo', 'neutro')),
    comentario      TEXT,
    id_externo      TEXT,
    creado_en       TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (producto_id)  REFERENCES dim_producto(id),
    FOREIGN KEY (cliente_id)   REFERENCES dim_cliente(id),
    FOREIGN KEY (fecha_id)    REFERENCES dim_fecha(id),
    FOREIGN KEY (fuente_id)   REFERENCES dim_fuente(id)
);

-- Índices para consultas analíticas frecuentes
CREATE INDEX IF NOT EXISTS idx_hechos_producto   ON hechos_opiniones(producto_id);
CREATE INDEX IF NOT EXISTS idx_hechos_cliente    ON hechos_opiniones(cliente_id);
CREATE INDEX IF NOT EXISTS idx_hechos_fecha     ON hechos_opiniones(fecha_id);
CREATE INDEX IF NOT EXISTS idx_hechos_fuente    ON hechos_opiniones(fuente_id);
CREATE INDEX IF NOT EXISTS idx_hechos_sentimiento ON hechos_opiniones(sentimiento);
CREATE INDEX IF NOT EXISTS idx_hechos_calificacion ON hechos_opiniones(calificacion);

-- Habilitar integridad referencial (SQLite)
PRAGMA foreign_keys = ON;
