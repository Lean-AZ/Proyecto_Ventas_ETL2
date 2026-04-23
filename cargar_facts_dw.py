#!/usr/bin/env python3
"""
Proceso de carga de tablas de hechos al Data Warehouse.

Flujo:
  1. Asegurar schema (dim_fuente + hechos_opiniones) en ventas_analitica.db
  2. LIMPIAR hechos_ventas y hechos_opiniones antes de cargar
  3. Cargar hechos_ventas desde staging (pipeline ETL completo)
  4. Cargar hechos_opiniones con datos sintéticos generados

Uso:
    python cargar_facts_dw.py
    python cargar_facts_dw.py --skip-etl   # reutiliza staging existente
"""
import argparse
import sqlite3
import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from etl.config import load_config
from etl.logger import setup_logger
from etl.loader import load_from_staging
from etl.facts_loader import (
    asegurar_schema_opiniones,
    limpiar_todas_facts,
    cargar_hechos_opiniones,
)


def ejecutar_pipeline_etl(root: Path) -> None:
    """Ejecuta run_etl.py para extraer y poblar staging antes de cargar facts."""
    import subprocess
    resultado = subprocess.run(
        [sys.executable, str(root / "run_etl.py")],
        cwd=str(root),
        capture_output=True,
        text=True,
        timeout=300,
    )
    if resultado.returncode != 0:
        print("Aviso: run_etl terminó con código", resultado.returncode, file=sys.stderr)
        if resultado.stderr:
            print(resultado.stderr[:2000], file=sys.stderr)


def main() -> int:
    parser = argparse.ArgumentParser(description="Carga de tablas de hechos al DW")
    parser.add_argument(
        "--skip-etl",
        action="store_true",
        help="Omite la extracción ETL y reutiliza el staging existente",
    )
    args = parser.parse_args()

    root = Path(__file__).resolve().parent
    config = load_config()
    logger = setup_logger("facts_dw", config)
    analitica_path = config["databases"]["analitica"]

    logger.info("=" * 60)
    logger.info("INICIO: Proceso de carga de tablas de hechos al DW")
    logger.info("Base analítica: %s", analitica_path)
    logger.info("=" * 60)

    # ── Paso 0: Asegurar que la BD analítica existe y tiene el schema completo ──
    Path(analitica_path).parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(analitica_path)
    try:
        asegurar_schema_opiniones(conn)
        logger.info("Schema verificado: dim_fuente y hechos_opiniones disponibles")
    finally:
        conn.close()

    # ── Paso 1: Limpieza de tablas de hechos ANTES de cargar ──────────────────
    logger.info("-" * 40)
    logger.info("PASO 1: Limpieza de tablas de hechos")
    t_inicio = time.perf_counter()
    conn = sqlite3.connect(analitica_path)
    try:
        eliminadas = limpiar_todas_facts(conn)
    finally:
        conn.close()

    for tabla, n in eliminadas.items():
        logger.info("  OK %s: %d filas eliminadas", tabla, n)
    logger.info("  Limpieza completada en %.3f s", time.perf_counter() - t_inicio)

    # ── Paso 2: Pipeline ETL → staging ────────────────────────────────────────
    if not args.skip_etl:
        logger.info("-" * 40)
        logger.info("PASO 2: Ejecutando pipeline ETL (extracción → staging)")
        t0 = time.perf_counter()
        try:
            ejecutar_pipeline_etl(root)
            logger.info("  Pipeline ETL completado en %.2f s", time.perf_counter() - t0)
        except Exception as e:
            logger.warning("  Pipeline ETL con advertencia: %s", e)
    else:
        logger.info("PASO 2: (omitido por --skip-etl; reutilizando staging existente)")

    # ── Paso 3: Carga de hechos_ventas desde staging ──────────────────────────
    logger.info("-" * 40)
    logger.info("PASO 3: Carga de hechos_ventas desde staging")
    t0 = time.perf_counter()
    try:
        load_from_staging(config)
        elapsed = time.perf_counter() - t0
        conn = sqlite3.connect(analitica_path)
        n_ventas = conn.execute("SELECT COUNT(*) FROM hechos_ventas").fetchone()[0]
        conn.close()
        logger.info("  OK hechos_ventas: %d registros cargados en %.2f s", n_ventas, elapsed)
    except Exception as e:
        logger.exception("  ERROR en carga de hechos_ventas: %s", e)
        return 1

    # ── Paso 4: Carga de hechos_opiniones (datos sintéticos) ──────────────────
    logger.info("-" * 40)
    logger.info("PASO 4: Carga de hechos_opiniones (datos sintéticos)")
    t0 = time.perf_counter()
    conn = sqlite3.connect(analitica_path)
    try:
        asegurar_schema_opiniones(conn)
        n_opiniones = cargar_hechos_opiniones(conn, n=800, seed=42)
        elapsed = time.perf_counter() - t0
        logger.info(
            "  OK hechos_opiniones: %d registros cargados en %.2f s",
            n_opiniones,
            elapsed,
        )
    except Exception as e:
        logger.exception("  ERROR en carga de hechos_opiniones: %s", e)
        return 1
    finally:
        conn.close()

    # ── Resumen final ──────────────────────────────────────────────────────────
    logger.info("=" * 60)
    conn = sqlite3.connect(analitica_path)
    try:
        n_v = conn.execute("SELECT COUNT(*) FROM hechos_ventas").fetchone()[0]
        n_o = conn.execute("SELECT COUNT(*) FROM hechos_opiniones").fetchone()[0]
        n_f = conn.execute("SELECT COUNT(*) FROM dim_fuente").fetchone()[0]
    finally:
        conn.close()

    logger.info("RESUMEN DE CARGA:")
    logger.info("  hechos_ventas    : %d filas", n_v)
    logger.info("  hechos_opiniones : %d filas", n_o)
    logger.info("  dim_fuente       : %d fuentes registradas", n_f)
    logger.info("FIN: Proceso de carga completado exitosamente")
    logger.info("=" * 60)
    return 0


if __name__ == "__main__":
    sys.exit(main())
