"""
ApiExtractor: consume API REST para obtener productos y clientes.
Equivalente a HttpClient en .NET; en producción sería la API real de la empresa.
"""
import urllib.request
import json
from typing import Any

from .base import Extractor


class ApiExtractor(Extractor):
    """Recupera datos del API (GET /productos, GET /clientes) para staging."""

    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config
        api_cfg = config.get("api", {})
        self.base_url = api_cfg.get("base_url", "http://127.0.0.1:8000").rstrip("/")
        self.endpoints = api_cfg.get("endpoints", {})
        self.timeout = api_cfg.get("timeout_seconds", 30)

    def extract(self) -> dict[str, Any]:
        productos = self._get_json(self.endpoints.get("productos", "/productos"))
        clientes = self._get_json(self.endpoints.get("clientes", "/clientes"))
        # Normalizar claves si la API devuelve nombres distintos
        if productos and isinstance(productos, list):
            productos = [
                {
                    "id": p.get("id"),
                    "nombre": p.get("nombre", p.get("ProductName", "")),
                    "categoria": p.get("categoria", p.get("Category")),
                    "precio": p.get("precio", p.get("Price")),
                    "stock": p.get("stock", p.get("Stock")),
                }
                for p in productos if isinstance(p, dict)
            ]
        if clientes and isinstance(clientes, list):
            clientes = [
                {
                    "id": c.get("id"),
                    "nombre_completo": c.get("nombre_completo", c.get("FirstName", "") + " " + c.get("LastName", "")),
                    "email": c.get("email", c.get("Email")),
                    "telefono": c.get("telefono", c.get("Phone")),
                    "ciudad": c.get("ciudad", c.get("City")),
                    "pais": c.get("pais", c.get("Country")),
                }
                for c in clientes if isinstance(c, dict)
            ]
        return {"productos": productos or [], "clientes": clientes or [], "pedidos": [], "detalles": []}

    def _get_json(self, path: str) -> list | dict | None:
        url = f"{self.base_url}{path}" if path.startswith("/") else f"{self.base_url}/{path}"
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                return json.loads(resp.read().decode())
        except Exception:
            return None
