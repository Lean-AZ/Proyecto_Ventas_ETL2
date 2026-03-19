#!/usr/bin/env python3
"""
Punto de entrada del pipeline ETL (Actividad 1 - Extracción).
Orquesta: Extracción (CSV + BD + API) -> Staging -> Carga a BD analítica.
Registra logs y opcionalmente métricas de tiempo.
"""
import sys
import time
from pathlib import Path

# Raíz del proyecto en path para imports
sys.path.insert(0, str(Path(__file__).resolve().parent))

from etl.config import load_config
from etl.logger import setup_logger
from etl.extractors import CsvExtractor, DatabaseExtractor, ApiExtractor
from etl.staging import get_staging_conn, merge_into_staging
from etl.loader import load_from_staging


def main() -> int:
    config = load_config()
    logger = setup_logger("etl", config)
    staging_path = config["databases"]["staging"]
    Path(staging_path).parent.mkdir(parents=True, exist_ok=True)

    # Limpiar staging al inicio (opcional: o usar merge por fuente)
    conn = get_staging_conn(staging_path)
    for table in ("staging_productos", "staging_clientes", "staging_pedidos", "staging_detalles"):
        try:
            conn.execute(f"DELETE FROM {table}")
        except Exception:
            pass
    conn.commit()
    conn.close()

    extractors = [
        ("CSV", CsvExtractor(config), "csv"),
        ("BD relacional", DatabaseExtractor(config), "db"),
        ("API REST", ApiExtractor(config), "api"),
    ]

    for name, extractor, fuente in extractors:
        try:
            t0 = time.perf_counter()
            logger.info("Inicio extracción: %s", name)
            data = extractor.extract()
            elapsed = time.perf_counter() - t0
            total = sum(len(data.get(k, [])) for k in ("productos", "clientes", "pedidos", "detalles") if isinstance(data.get(k), list))
            if total > 0:
                merge_into_staging(staging_path, data, fuente=fuente)
                logger.info("Extracción %s completada: %d registros en %.2f s", name, total, elapsed)
            else:
                logger.warning("Extracción %s sin datos (fuente no disponible o vacía)", name)
        except Exception as e:
            logger.exception("Error en extracción %s: %s", name, e)

    logger.info("Inicio carga a BD analítica")
    t0 = time.perf_counter()
    try:
        load_from_staging(config)
        logger.info("Carga completada en %.2f s", time.perf_counter() - t0)
    except Exception as e:
        logger.exception("Error en carga: %s", e)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
