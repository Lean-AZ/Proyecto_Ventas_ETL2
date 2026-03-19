"""
Configuración de logging para el pipeline ETL (equivalente ILogger).
Registra eventos de ejecución y errores para monitoreo y trazabilidad.
"""
import logging
import sys
from pathlib import Path


def setup_logger(name: str = "etl", config: dict | None = None) -> logging.Logger:
    """
    Configura y devuelve un logger con salida a consola y opcionalmente a archivo.
    """
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    # Consola
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)
    logger.addHandler(ch)
    # Archivo (si está en config)
    if config and config.get("logging", {}).get("file"):
        log_path = Path(config["logging"]["file"])
        log_path.parent.mkdir(parents=True, exist_ok=True)
        fh = logging.FileHandler(log_path, encoding="utf-8")
        level = config["logging"].get("level", "INFO").upper()
        fh.setLevel(getattr(logging, level, logging.INFO))
        fh.setFormatter(formatter)
        logger.addHandler(fh)
    return logger
