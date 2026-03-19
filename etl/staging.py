"""
Escribe los datos extraídos en tablas de staging (data/staging.db).
Equivalente a "Guardar los datos extraídos en archivos temporales o tablas staging".
"""
import sqlite3
from pathlib import Path
from typing import Any


STAGING_SCHEMA = """
CREATE TABLE IF NOT EXISTS staging_productos (
    id INTEGER PRIMARY KEY,
    nombre TEXT,
    categoria TEXT,
    precio REAL,
    stock INTEGER,
    fuente TEXT DEFAULT 'csv'
);
CREATE TABLE IF NOT EXISTS staging_clientes (
    id INTEGER PRIMARY KEY,
    nombre_completo TEXT,
    email TEXT,
    telefono TEXT,
    ciudad TEXT,
    pais TEXT,
    fuente TEXT DEFAULT 'csv'
);
CREATE TABLE IF NOT EXISTS staging_pedidos (
    id_pedido INTEGER,
    id_cliente INTEGER,
    fecha TEXT,
    estado TEXT,
    fuente TEXT DEFAULT 'csv',
    PRIMARY KEY (id_pedido)
);
CREATE TABLE IF NOT EXISTS staging_detalles (
    id_pedido INTEGER,
    id_producto INTEGER,
    cantidad INTEGER,
    monto_total REAL,
    fuente TEXT,
    PRIMARY KEY (id_pedido, id_producto)
);
"""


def get_staging_conn(staging_path: str) -> sqlite3.Connection:
    """Abre conexión a la BD de staging; crea el directorio si no existe."""
    path = Path(staging_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(path)
    conn.executescript(STAGING_SCHEMA)
    conn.commit()
    return conn


def write_to_staging(staging_path: str, data: dict[str, Any], fuente: str = "csv") -> None:
    """
    Escribe los datos extraídos en las tablas de staging.
    data: dict con claves productos, clientes, pedidos, detalles (listas de dicts).
    fuente: etiqueta de origen (csv, db, api) para trazabilidad.
    """
    conn = get_staging_conn(staging_path)
    try:
        if data.get("productos"):
            conn.execute("DELETE FROM staging_productos WHERE fuente = ?", (fuente,))
            for r in data["productos"]:
                conn.execute(
                    """INSERT OR REPLACE INTO staging_productos (id, nombre, categoria, precio, stock, fuente)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (r["id"], r["nombre"], r.get("categoria"), r.get("precio"), r.get("stock"), fuente),
                )
        if data.get("clientes"):
            conn.execute("DELETE FROM staging_clientes WHERE fuente = ?", (fuente,))
            for r in data["clientes"]:
                conn.execute(
                    """INSERT OR REPLACE INTO staging_clientes (id, nombre_completo, email, telefono, ciudad, pais, fuente)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (r["id"], r["nombre_completo"], r.get("email"), r.get("telefono"), r.get("ciudad"), r.get("pais"), fuente),
                )
        if data.get("pedidos"):
            conn.execute("DELETE FROM staging_pedidos WHERE fuente = ?", (fuente,))
            for r in data["pedidos"]:
                conn.execute(
                    """INSERT OR REPLACE INTO staging_pedidos (id_pedido, id_cliente, fecha, estado, fuente)
                       VALUES (?, ?, ?, ?, ?)""",
                    (r["id_pedido"], r["id_cliente"], r["fecha"], r.get("estado", ""), fuente),
                )
        if data.get("detalles"):
            conn.execute("DELETE FROM staging_detalles WHERE fuente = ?", (fuente,))
            for r in data["detalles"]:
                conn.execute(
                    """INSERT OR REPLACE INTO staging_detalles (id_pedido, id_producto, cantidad, monto_total, fuente)
                       VALUES (?, ?, ?, ?, ?)""",
                    (r["id_pedido"], r["id_producto"], r["cantidad"], r["monto_total"], fuente),
                )
        conn.commit()
    finally:
        conn.close()


def merge_into_staging(staging_path: str, data: dict[str, Any], fuente: str = "csv") -> None:
    """
    Inserta o actualiza en staging sin borrar primero por fuente;
    útil para ir acumulando extracciones de varias fuentes (csv, db, api).
    """
    conn = get_staging_conn(staging_path)
    try:
        if data.get("productos"):
            for r in data["productos"]:
                conn.execute(
                    """INSERT OR REPLACE INTO staging_productos (id, nombre, categoria, precio, stock, fuente)
                       VALUES (?, ?, ?, ?, ?, ?)""",
                    (r["id"], r["nombre"], r.get("categoria"), r.get("precio"), r.get("stock"), fuente),
                )
        if data.get("clientes"):
            for r in data["clientes"]:
                conn.execute(
                    """INSERT OR REPLACE INTO staging_clientes (id, nombre_completo, email, telefono, ciudad, pais, fuente)
                       VALUES (?, ?, ?, ?, ?, ?, ?)""",
                    (r["id"], r["nombre_completo"], r.get("email"), r.get("telefono"), r.get("ciudad"), r.get("pais"), fuente),
                )
        if data.get("pedidos"):
            for r in data["pedidos"]:
                conn.execute(
                    """INSERT OR REPLACE INTO staging_pedidos (id_pedido, id_cliente, fecha, estado, fuente)
                       VALUES (?, ?, ?, ?, ?)""",
                    (r["id_pedido"], r["id_cliente"], r["fecha"], r.get("estado", ""), fuente),
                )
        if data.get("detalles"):
            for r in data["detalles"]:
                conn.execute(
                    """INSERT OR REPLACE INTO staging_detalles (id_pedido, id_producto, cantidad, monto_total, fuente)
                       VALUES (?, ?, ?, ?, ?)""",
                    (r["id_pedido"], r["id_producto"], r["cantidad"], r["monto_total"], fuente),
                )
        conn.commit()
    finally:
        conn.close()
