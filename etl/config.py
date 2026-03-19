"""
Carga la configuración desde config.json (rutas, BD, API).
Las credenciales sensibles pueden venir de variables de entorno.
"""
import json
import os
from pathlib import Path
from typing import Any

RUTA_PROYECTO = Path(__file__).resolve().parent.parent
CONFIG_PATH = RUTA_PROYECTO / "config" / "config.json"


def _ruta_absoluta(base: Path, valor: str) -> Path:
    if os.path.isabs(valor):
        return Path(valor)
    return (base / valor).resolve()


def load_config() -> dict[str, Any]:
    """Carga config.json; si no existe, usa config.json.example como plantilla."""
    path = CONFIG_PATH
    if not path.exists():
        path = RUTA_PROYECTO / "config" / "config.json.example"
    if not path.exists():
        raise FileNotFoundError(f"No se encontró config.json ni config.json.example en config/")
    with open(path, encoding="utf-8") as f:
        cfg = json.load(f)
    # Resolver rutas relativas respecto al proyecto
    base = RUTA_PROYECTO
    if "csv" in cfg and "dataset_dir" in cfg["csv"]:
        cfg["csv"]["dataset_dir"] = str(_ruta_absoluta(base, cfg["csv"]["dataset_dir"]))
    if "databases" in cfg:
        for k in cfg["databases"]:
            cfg["databases"][k] = str(_ruta_absoluta(base, cfg["databases"][k]))
    if "logging" in cfg and "file" in cfg["logging"]:
        cfg["logging"]["file"] = str(_ruta_absoluta(base, cfg["logging"]["file"]))
    return cfg


def get_config() -> dict[str, Any]:
    """Singleton básico de configuración (carga una vez)."""
    if not hasattr(get_config, "_cache"):
        get_config._cache = load_config()
    return get_config._cache
