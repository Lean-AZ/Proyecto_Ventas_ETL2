"""
DatabaseExtractor: extrae datos de una BD relacional (historial de ventas).
Equivalente a consultar reseñas/ventas desde SQL Server o MySQL con ADO.NET/EF Core.
En el proyecto se usa SQLite fuente_ventas.db como simulación de la BD externa.
"""
import sqlite3
from typing import Any

from .base import Extractor


class DatabaseExtractor(Extractor):
    """Ejecuta queries definidos sobre la BD externa y devuelve datos para staging."""

    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config
        self.db_path = config.get("databases", {}).get("fuente_ventas", "data/fuente_ventas.db")

    def extract(self) -> dict[str, Any]:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        try:
            pedidos = self._fetch_pedidos(conn)
            detalles = self._fetch_detalles(conn)
            return {"pedidos": pedidos, "detalles": detalles, "productos": [], "clientes": []}
        finally:
            conn.close()

    def _fetch_pedidos(self, conn: sqlite3.Connection) -> list[dict]:
        try:
            cur = conn.execute(
                "SELECT OrderID AS id_pedido, CustomerID AS id_cliente, OrderDate AS fecha, Status AS estado FROM pedidos"
            )
            return [dict(row) for row in cur.fetchall()]
        except sqlite3.OperationalError:
            return []

    def _fetch_detalles(self, conn: sqlite3.Connection) -> list[dict]:
        try:
            cur = conn.execute(
                "SELECT OrderID AS id_pedido, ProductID AS id_producto, Quantity AS cantidad, TotalPrice AS monto_total FROM detalle_pedidos"
            )
            return [dict(row) for row in cur.fetchall()]
        except sqlite3.OperationalError:
            return []
