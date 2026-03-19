"""
DataLoader: lee desde staging y carga en la BD analítica (dim_*, hechos_ventas).
Incluye transformación mínima: mapeo de columnas y fecha_id = YYYYMMDD.
"""
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta
from typing import Any

RUTA_PROYECTO = Path(__file__).resolve().parent.parent
SQL_SCHEMA = RUTA_PROYECTO / "sql" / "01_create_schema_ventas.sql"


def _rellenar_dim_fecha(conn: sqlite3.Connection, anio_inicio: int = 2020, anio_fin: int = 2026) -> None:
    """Rellena dim_fecha si está vacía (id = YYYYMMDD)."""
    nombres_mes = (
        None, "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
        "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
    )
    nombres_dia = ("Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo")
    d = datetime(anio_inicio, 1, 1)
    fin = datetime(anio_fin, 12, 31)
    filas = []
    while d <= fin:
        fecha_str = d.strftime("%Y-%m-%d")
        id_fecha = int(d.strftime("%Y%m%d"))
        mes = d.month
        trimestre = (mes - 1) // 3 + 1
        filas.append((
            id_fecha, fecha_str, d.year, mes, trimestre,
            d.isocalendar()[1], d.weekday() + 1, nombres_mes[mes], nombres_dia[d.weekday()]
        ))
        d += timedelta(days=1)
    conn.executemany(
        """INSERT OR IGNORE INTO dim_fecha (id, fecha, anio, mes, trimestre, semana, dia_semana, nombre_mes, nombre_dia)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        filas,
    )
    conn.commit()


def load_from_staging(config: dict[str, Any]) -> None:
    """
    Lee tablas de staging (staging_path) y carga en la BD analítica (analitica_path).
    Crea el schema analítico si no existe y rellena dim_fecha.
    """
    staging_path = config["databases"]["staging"]
    analitica_path = config["databases"]["analitica"]
    Path(analitica_path).parent.mkdir(parents=True, exist_ok=True)

    # Crear/actualizar schema analítico
    conn_analitica = sqlite3.connect(analitica_path)
    conn_analitica.executescript(SQL_SCHEMA.read_text(encoding="utf-8"))
    _rellenar_dim_fecha(conn_analitica)

    conn_staging = sqlite3.connect(staging_path)
    try:
        # dim_producto desde staging_productos (tomamos por id; INSERT OR REPLACE)
        cur = conn_staging.execute(
            "SELECT id, nombre, categoria, precio, stock FROM staging_productos"
        )
        rows = cur.fetchall()
        if rows:
            conn_analitica.executemany(
                """INSERT OR REPLACE INTO dim_producto (id, nombre, categoria, precio, stock)
                   VALUES (?, ?, ?, ?, ?)""",
                rows,
            )
        # dim_cliente desde staging_clientes
        cur = conn_staging.execute(
            "SELECT id, nombre_completo, email, telefono, ciudad, pais FROM staging_clientes"
        )
        rows = cur.fetchall()
        if rows:
            conn_analitica.executemany(
                """INSERT OR REPLACE INTO dim_cliente (id, nombre_completo, email, telefono, ciudad, pais)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                rows,
            )
        # hechos_ventas: staging_detalles + staging_pedidos para obtener cliente y fecha
        conn_staging.row_factory = sqlite3.Row
        cur = conn_staging.execute("""
            SELECT d.id_pedido, d.id_producto, p.id_cliente, p.fecha, d.cantidad, d.monto_total
            FROM staging_detalles d
            JOIN staging_pedidos p ON d.id_pedido = p.id_pedido
        """)
        detalle_rows = cur.fetchall()
        conn_analitica.execute("DELETE FROM hechos_ventas")
        if detalle_rows:
            fecha_id_list = [
                (
                    r["id_pedido"],
                    r["id_producto"],
                    r["id_cliente"],
                    int(r["fecha"].replace("-", "")),
                    r["cantidad"],
                    r["monto_total"],
                )
                for r in detalle_rows
            ]
            conn_analitica.executemany(
                """INSERT INTO hechos_ventas (id_pedido, producto_id, cliente_id, fecha_id, cantidad, monto_total)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                fecha_id_list,
            )
        conn_analitica.commit()
    finally:
        conn_staging.close()
        conn_analitica.close()
