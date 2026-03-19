"""
Interfaz base para extractores (equivalente IExtractor).
Cada fuente de datos (CSV, BD, API) implementa esta interfaz.
"""
from abc import ABC, abstractmethod
from typing import Any


class Extractor(ABC):
    """Clase abstracta para extracción de datos desde una fuente."""

    @abstractmethod
    def extract(self) -> dict[str, Any]:
        """
        Extrae datos de la fuente y devuelve un diccionario con claves
        normalizadas para staging: productos, clientes, pedidos, detalles, etc.
        Las claves ausentes indican que esa fuente no aporta esa entidad.
        """
        pass
