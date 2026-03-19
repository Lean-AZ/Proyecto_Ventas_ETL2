"""
CsvExtractor: extrae datos de archivos CSV (products, customers, orders, order_details).
Equivalente a leer encuestas/ventas internas con CsvHelper.
"""
import csv
from pathlib import Path
from typing import Any

from .base import Extractor


class CsvExtractor(Extractor):
    """Lee y valida archivos CSV del dataset de ventas."""

    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config
        csv_cfg = config.get("csv", {})
        self.dataset_dir = Path(csv_cfg.get("dataset_dir", "dataset"))
        self.products_file = csv_cfg.get("products", "products.csv")
        self.customers_file = csv_cfg.get("customers", "customers.csv")
        self.orders_file = csv_cfg.get("orders", "orders.csv")
        self.order_details_file = csv_cfg.get("order_details", "order_details.csv")

    def extract(self) -> dict[str, Any]:
        result: dict[str, Any] = {}
        result["productos"] = self._read_productos()
        result["clientes"] = self._read_clientes()
        result["pedidos"] = self._read_pedidos()
        result["detalles"] = self._read_detalles()
        return result

    def _read_productos(self) -> list[dict]:
        path = self.dataset_dir / self.products_file
        if not path.exists():
            return []
        with open(path, encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            required = {"ProductID", "ProductName", "Category", "Price", "Stock"}
            rows = []
            for r in reader:
                if not required.issubset(r.keys()):
                    continue
                rows.append({
                    "id": int(r["ProductID"]),
                    "nombre": r["ProductName"],
                    "categoria": r["Category"],
                    "precio": float(r["Price"]),
                    "stock": int(r["Stock"]),
                })
            return rows

    def _read_clientes(self) -> list[dict]:
        path = self.dataset_dir / self.customers_file
        if not path.exists():
            return []
        with open(path, encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            required = {"CustomerID", "FirstName", "LastName", "Email", "Phone", "City", "Country"}
            rows = []
            for r in reader:
                if not required.issubset(r.keys()):
                    continue
                rows.append({
                    "id": int(r["CustomerID"]),
                    "nombre_completo": f"{r['FirstName']} {r['LastName']}".strip(),
                    "email": r["Email"],
                    "telefono": r["Phone"],
                    "ciudad": r["City"],
                    "pais": r["Country"],
                })
            return rows

    def _read_pedidos(self) -> list[dict]:
        path = self.dataset_dir / self.orders_file
        if not path.exists():
            return []
        with open(path, encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            required = {"OrderID", "CustomerID", "OrderDate", "Status"}
            rows = []
            for r in reader:
                if not required.issubset(r.keys()):
                    continue
                rows.append({
                    "id_pedido": int(r["OrderID"]),
                    "id_cliente": int(r["CustomerID"]),
                    "fecha": r["OrderDate"],
                    "estado": r["Status"],
                })
            return rows

    def _read_detalles(self) -> list[dict]:
        path = self.dataset_dir / self.order_details_file
        if not path.exists():
            return []
        with open(path, encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            required = {"OrderID", "ProductID", "Quantity", "TotalPrice"}
            rows = []
            for r in reader:
                if not required.issubset(r.keys()):
                    continue
                rows.append({
                    "id_pedido": int(r["OrderID"]),
                    "id_producto": int(r["ProductID"]),
                    "cantidad": int(r["Quantity"]),
                    "monto_total": float(r["TotalPrice"]),
                })
            return rows
