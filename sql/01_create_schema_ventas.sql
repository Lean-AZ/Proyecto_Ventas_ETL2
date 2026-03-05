-- =============================================================================
-- Sistema de Análisis de Ventas - Schema (modelo estrella)
-- Compatible con SQLite. Integra datos de CSV, API y BD externa.
-- =============================================================================

-- Dimensión: Productos (fuente: products.csv / API)
CREATE TABLE IF NOT EXISTS dim_producto (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre          TEXT NOT NULL,
    categoria       TEXT,
    precio          REAL,
    stock           INTEGER,
    creado_en       TEXT DEFAULT (datetime('now')),
    actualizado_en  TEXT DEFAULT (datetime('now'))
);

-- Dimensión: Clientes (fuente: customers.csv / API)
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

-- Dimensión: Fecha (calendario analítico; id = YYYYMMDD)
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

-- Tabla de hechos: Ventas (líneas de pedido consolidadas)
CREATE TABLE IF NOT EXISTS hechos_ventas (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    id_pedido       INTEGER NOT NULL,
    producto_id     INTEGER NOT NULL,
    cliente_id      INTEGER NOT NULL,
    fecha_id        INTEGER NOT NULL,
    cantidad        INTEGER NOT NULL,
    monto_total     REAL NOT NULL,
    creado_en       TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (producto_id) REFERENCES dim_producto(id),
    FOREIGN KEY (cliente_id)  REFERENCES dim_cliente(id),
    FOREIGN KEY (fecha_id)    REFERENCES dim_fecha(id)
);

-- Índices para consultas analíticas y KPIs
CREATE INDEX IF NOT EXISTS idx_hechos_ventas_producto ON hechos_ventas(producto_id);
CREATE INDEX IF NOT EXISTS idx_hechos_ventas_cliente  ON hechos_ventas(cliente_id);
CREATE INDEX IF NOT EXISTS idx_hechos_ventas_fecha    ON hechos_ventas(fecha_id);
CREATE INDEX IF NOT EXISTS idx_hechos_ventas_pedido   ON hechos_ventas(id_pedido);

PRAGMA foreign_keys = ON;
