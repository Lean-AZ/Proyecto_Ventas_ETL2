#!/usr/bin/env python3
"""
Crea la BD 'externa' fuente_ventas.db (simula SQL Server/MySQL de historial de ventas)
y la puebla desde los CSV. El DatabaseExtractor luego lee desde esta BD.
"""
import csv
import sqlite3
from pathlib import Path

RUTA_PROYECTO = Path(__file__).resolve().parent.parent
DATASET = RUTA_PROYECTO / "dataset"
OUTPUT_DB = RUTA_PROYECTO / "data" / "fuente_ventas.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS pedidos (
    OrderID INTEGER PRIMARY KEY,
    CustomerID INTEGER NOT NULL,
    OrderDate TEXT NOT NULL,
    Status TEXT
);
CREATE TABLE IF NOT EXISTS detalle_pedidos (
    OrderID INTEGER NOT NULL,
    ProductID INTEGER NOT NULL,
    Quantity INTEGER NOT NULL,
    TotalPrice REAL NOT NULL,
    PRIMARY KEY (OrderID, ProductID),
    FOREIGN KEY (OrderID) REFERENCES pedidos(OrderID)
);
"""


def main() -> None:
    OUTPUT_DB.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(OUTPUT_DB)
    conn.executescript(SCHEMA)
    # Pedidos desde orders.csv
    orders_path = DATASET / "orders.csv"
    if orders_path.exists():
        with open(orders_path, encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            rows = [(int(r["OrderID"]), int(r["CustomerID"]), r["OrderDate"], r["Status"]) for r in reader]
        conn.executemany(
            "INSERT OR REPLACE INTO pedidos (OrderID, CustomerID, OrderDate, Status) VALUES (?, ?, ?, ?)",
            rows,
        )
    # Detalles desde order_details.csv
    details_path = DATASET / "order_details.csv"
    if details_path.exists():
        with open(details_path, encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            rows = [(int(r["OrderID"]), int(r["ProductID"]), int(r["Quantity"]), float(r["TotalPrice"])) for r in reader]
        conn.executemany(
            "INSERT OR REPLACE INTO detalle_pedidos (OrderID, ProductID, Quantity, TotalPrice) VALUES (?, ?, ?, ?)",
            rows,
        )
    conn.commit()
    conn.close()
    print(f"BD fuente creada: {OUTPUT_DB}")


if __name__ == "__main__":
    main()
