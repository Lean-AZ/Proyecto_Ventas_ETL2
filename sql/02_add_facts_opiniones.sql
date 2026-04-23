-- =============================================================================
-- Data Warehouse: Extensión para tabla de hechos de Opiniones
-- Agrega dim_fuente y hechos_opiniones a la BD analítica (ventas_analitica.db)
-- Reutiliza las dimensiones ya existentes: dim_producto, dim_cliente, dim_fecha
-- =============================================================================

-- Dimensión: Fuente del comentario (encuesta web, tienda, redes sociales, app)
CREATE TABLE IF NOT EXISTS dim_fuente (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    nombre          TEXT NOT NULL UNIQUE,
    descripcion     TEXT,
    creado_en       TEXT DEFAULT (datetime('now'))
);

-- Tabla de hechos: Opiniones de clientes sobre productos
CREATE TABLE IF NOT EXISTS hechos_opiniones (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    producto_id     INTEGER NOT NULL,
    cliente_id      INTEGER,
    fecha_id        INTEGER NOT NULL,
    fuente_id       INTEGER NOT NULL,
    calificacion    INTEGER CHECK (calificacion BETWEEN 1 AND 5),
    sentimiento     TEXT CHECK (sentimiento IN ('positivo', 'negativo', 'neutro')),
    comentario      TEXT,
    id_externo      TEXT,
    creado_en       TEXT DEFAULT (datetime('now')),
    FOREIGN KEY (producto_id) REFERENCES dim_producto(id),
    FOREIGN KEY (cliente_id)  REFERENCES dim_cliente(id),
    FOREIGN KEY (fecha_id)    REFERENCES dim_fecha(id),
    FOREIGN KEY (fuente_id)   REFERENCES dim_fuente(id)
);

-- Índices para consultas analíticas de opiniones
CREATE INDEX IF NOT EXISTS idx_hops_producto    ON hechos_opiniones(producto_id);
CREATE INDEX IF NOT EXISTS idx_hops_cliente     ON hechos_opiniones(cliente_id);
CREATE INDEX IF NOT EXISTS idx_hops_fecha       ON hechos_opiniones(fecha_id);
CREATE INDEX IF NOT EXISTS idx_hops_fuente      ON hechos_opiniones(fuente_id);
CREATE INDEX IF NOT EXISTS idx_hops_sentimiento ON hechos_opiniones(sentimiento);
CREATE INDEX IF NOT EXISTS idx_hops_calificacion ON hechos_opiniones(calificacion);

PRAGMA foreign_keys = ON;
