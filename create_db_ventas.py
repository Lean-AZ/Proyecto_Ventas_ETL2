#!/usr/bin/env python3
"""
Crea la base de datos analítica del Sistema de Ventas (modelo estrella).
Ejecuta el script SQL de creación, rellena dim_fecha y carga datos desde CSV.
"""
import csv
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta

RUTA_PROYECTO = Path(__file__).resolve().parent
SQL_SCHEMA = RUTA_PROYECTO / "sql" / "01_create_schema_ventas.sql"
DB_PATH = RUTA_PROYECTO / "data" / "ventas_analitica.db"
DATASET = RUTA_PROYECTO / "dataset"


def ejecutar_sql(conn: sqlite3.Connection, ruta_sql: Path) -> None:
    """Ejecuta un archivo .sql completo."""
    sql = ruta_sql.read_text(encoding="utf-8")
    conn.executescript(sql)


def rellenar_dim_fecha(conn: sqlite3.Connection, anio_inicio: int = 2020, anio_fin: int = 2026) -> None:
    """Inserta filas en dim_fecha para el rango de años dado. id = YYYYMMDD."""
    nombres_mes = (
        None, "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
        "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"
    )
    nombres_dia = (
        "Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"
    )
    filas = []
    d = datetime(anio_inicio, 1, 1)
    fin = datetime(anio_fin, 12, 31)
    while d <= fin:
        fecha_str = d.strftime("%Y-%m-%d")
        id_fecha = int(d.strftime("%Y%m%d"))
        anio = d.year
        mes = d.month
        trimestre = (mes - 1) // 3 + 1
        semana = d.isocalendar()[1]
        dia_semana = d.weekday() + 1  # 1 = Lunes
        nombre_mes = nombres_mes[mes]
        nombre_dia = nombres_dia[d.weekday()]
        filas.append((id_fecha, fecha_str, anio, mes, trimestre, semana, dia_semana, nombre_mes, nombre_dia))
        d += timedelta(days=1)
    conn.executemany(
        """INSERT OR IGNORE INTO dim_fecha (id, fecha, anio, mes, trimestre, semana, dia_semana, nombre_mes, nombre_dia)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        filas,
    )
    conn.commit()


def cargar_dim_producto(conn: sqlite3.Connection) -> None:
    """Carga dim_producto desde dataset/products.csv. Conserva ProductID como id."""
    ruta = DATASET / "products.csv"
    if not ruta.exists():
        return
    with open(ruta, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        filas = [
            (int(r["ProductID"]), r["ProductName"], r["Category"], float(r["Price"]), int(r["Stock"]))
            for r in reader
        ]
    conn.executemany(
        """INSERT OR REPLACE INTO dim_producto (id, nombre, categoria, precio, stock)
           VALUES (?, ?, ?, ?, ?)""",
        filas,
    )
    conn.commit()


def cargar_dim_cliente(conn: sqlite3.Connection) -> None:
    """Carga dim_cliente desde dataset/customers.csv. Conserva CustomerID como id."""
    ruta = DATASET / "customers.csv"
    if not ruta.exists():
        return
    with open(ruta, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        filas = [
            (
                int(r["CustomerID"]),
                f"{r['FirstName']} {r['LastName']}".strip(),
                r["Email"],
                r["Phone"],
                r["City"],
                r["Country"],
            )
            for r in reader
        ]
    conn.executemany(
        """INSERT OR REPLACE INTO dim_cliente (id, nombre_completo, email, telefono, ciudad, pais)
           VALUES (?, ?, ?, ?, ?, ?)""",
        filas,
    )
    conn.commit()


def cargar_hechos_ventas(conn: sqlite3.Connection) -> None:
    """Carga hechos_ventas desde dataset/orders.csv y order_details.csv."""
    orders_path = DATASET / "orders.csv"
    details_path = DATASET / "order_details.csv"
    if not orders_path.exists() or not details_path.exists():
        return
    with open(orders_path, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        orders = {int(r["OrderID"]): (int(r["CustomerID"]), r["OrderDate"]) for r in reader}
    conn.execute("DELETE FROM hechos_ventas")
    filas = []
    with open(details_path, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for r in reader:
            order_id = int(r["OrderID"])
            if order_id not in orders:
                continue
            customer_id, order_date = orders[order_id]
            fecha_id = int(order_date.replace("-", ""))
            filas.append((
                order_id,
                int(r["ProductID"]),
                customer_id,
                fecha_id,
                int(r["Quantity"]),
                float(r["TotalPrice"]),
            ))
    conn.executemany(
        """INSERT INTO hechos_ventas (id_pedido, producto_id, cliente_id, fecha_id, cantidad, monto_total)
           VALUES (?, ?, ?, ?, ?, ?)""",
        filas,
    )
    conn.commit()


def main() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    try:
        ejecutar_sql(conn, SQL_SCHEMA)
        rellenar_dim_fecha(conn)
        cargar_dim_producto(conn)
        cargar_dim_cliente(conn)
        cargar_hechos_ventas(conn)
        print(f"Base de datos creada: {DB_PATH}")
    finally:
        conn.close()


if __name__ == "__main__":
    main()
