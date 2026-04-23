#!/usr/bin/env python3
"""
Genera PNG con muestras de las tablas de hechos del Data Warehouse:
hechos_ventas, hechos_opiniones, dim_fuente (nueva).
Requiere: matplotlib
Salida: docs_actividad1/capturas_facts/
"""
from __future__ import annotations

import sqlite3
import subprocess
import sys
from pathlib import Path
from typing import Any

try:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "matplotlib", "-q"])
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt


def _truncate(s: Any, n: int = 36) -> str:
    if s is None:
        return ""
    t = str(s)
    return t if len(t) <= n else t[: n - 2] + "…"


def _query_to_cells(
    db: str, sql: str, max_rows: int = 14
) -> tuple[list[str], list[list[str]]]:
    conn = sqlite3.connect(db)
    try:
        cur = conn.execute(sql)
        cols = [d[0] for d in cur.description]
        raw = cur.fetchmany(max_rows)
        cells = [[_truncate(v) for v in row] for row in raw]
        return cols, cells
    finally:
        conn.close()


def _save_table_png(
    cols: list[str],
    cells: list[list[str]],
    title: str,
    out: Path,
    header_color: str = "#1f497d",
) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    nrows = len(cells)
    ncols = len(cols) if cols else 1
    fig_w = min(18.0, 2.0 + ncols * 1.6)
    fig_h = min(11.0, 2.4 + max(nrows, 1) * 0.45)
    fig, ax = plt.subplots(figsize=(fig_w, fig_h))
    ax.axis("off")
    ax.set_title(title, fontsize=12, fontweight="bold", pad=14, loc="left")
    if not cols:
        ax.text(0.5, 0.5, "(sin columnas)", ha="center", va="center", fontsize=10)
        fig.savefig(out, dpi=140, bbox_inches="tight", facecolor="#f5f5f5")
        plt.close(fig)
        return
    if not cells:
        cells = [["—" * min(5, len(c)) for c in cols]]
        ax.text(
            0.02, 0.92,
            "(0 filas — correr cargar_facts_dw.py primero)",
            transform=ax.transAxes, fontsize=9, color="#666",
        )
    tbl = ax.table(
        cellText=cells,
        colLabels=cols,
        loc="upper center",
        cellLoc="left",
        colColours=[header_color] * ncols,
    )
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(8)
    tbl.scale(1, 2.0)
    for (row, col), cell in tbl.get_celld().items():
        if row == 0:
            cell.set_text_props(color="white", fontweight="bold")
            cell.set_height(0.08)
        else:
            cell.set_facecolor("#ffffff" if row % 2 else "#e8f0fe")
    plt.tight_layout()
    fig.savefig(out, dpi=140, bbox_inches="tight", facecolor="white")
    plt.close(fig)
    print(f"Captura guardada: {out}")


def _run_cargar_facts(root: Path) -> None:
    """Ejecuta cargar_facts_dw.py para asegurar datos actualizados."""
    r = subprocess.run(
        [sys.executable, str(root / "cargar_facts_dw.py")],
        cwd=str(root),
        capture_output=True,
        text=True,
        timeout=300,
    )
    if r.returncode != 0:
        print("Aviso: cargar_facts_dw terminó con código", r.returncode, file=sys.stderr)
        if r.stderr:
            print(r.stderr[:2000], file=sys.stderr)


def generar_capturas_facts(root: Path, ejecutar_carga: bool = True) -> dict[str, Path]:
    """
    Genera PNG en docs_actividad1/capturas_facts/.
    Claves: hechos_ventas, hechos_opiniones, dim_fuente, resumen_sentimientos, resumen_ventas.
    """
    root = root.resolve()
    sys.path.insert(0, str(root))
    from etl.config import load_config

    out_dir = root / "docs_actividad1" / "capturas_facts"
    out_dir.mkdir(parents=True, exist_ok=True)

    if ejecutar_carga:
        _run_cargar_facts(root)

    cfg = load_config()
    analitica = cfg["databases"]["analitica"]

    jobs: list[tuple[str, str, str, str]] = [
        (
            "hechos_ventas",
            analitica,
            """SELECT hv.id, hv.id_pedido, hv.producto_id, hv.cliente_id,
                      hv.fecha_id, hv.cantidad, hv.monto_total
               FROM hechos_ventas hv ORDER BY hv.id LIMIT 14""",
            "Data Warehouse — hechos_ventas (muestra 14 filas)",
        ),
        (
            "hechos_ventas_join",
            analitica,
            """SELECT hv.id_pedido,
                      dp.nombre AS producto,
                      dc.nombre_completo AS cliente,
                      df.fecha,
                      hv.cantidad,
                      hv.monto_total
               FROM hechos_ventas hv
               JOIN dim_producto dp ON dp.id = hv.producto_id
               JOIN dim_cliente  dc ON dc.id = hv.cliente_id
               JOIN dim_fecha    df ON df.id = hv.fecha_id
               ORDER BY hv.id LIMIT 12""",
            "hechos_ventas — vista desnormalizada (JOIN con dimensiones)",
        ),
        (
            "hechos_opiniones",
            analitica,
            """SELECT ho.id, ho.producto_id, ho.cliente_id,
                      ho.fecha_id, ho.fuente_id,
                      ho.calificacion, ho.sentimiento, ho.id_externo
               FROM hechos_opiniones ho ORDER BY ho.id LIMIT 14""",
            "Data Warehouse — hechos_opiniones (muestra 14 filas)",
        ),
        (
            "hechos_opiniones_join",
            analitica,
            """SELECT dp.nombre AS producto,
                      df.fecha,
                      dfu.nombre AS fuente,
                      ho.calificacion,
                      ho.sentimiento,
                      ho.comentario
               FROM hechos_opiniones ho
               JOIN dim_producto dp  ON dp.id  = ho.producto_id
               JOIN dim_fecha    df  ON df.id   = ho.fecha_id
               JOIN dim_fuente   dfu ON dfu.id  = ho.fuente_id
               ORDER BY ho.id LIMIT 12""",
            "hechos_opiniones — vista desnormalizada (JOIN con dimensiones)",
        ),
        (
            "dim_fuente",
            analitica,
            "SELECT id, nombre, descripcion FROM dim_fuente ORDER BY id",
            "Data Warehouse — dim_fuente (catálogo de fuentes de opinión)",
        ),
        (
            "resumen_sentimientos",
            analitica,
            """SELECT sentimiento,
                      COUNT(*)                          AS total_opiniones,
                      ROUND(AVG(calificacion), 2)       AS calif_promedio,
                      ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM hechos_opiniones), 1) AS porcentaje
               FROM hechos_opiniones
               GROUP BY sentimiento
               ORDER BY total_opiniones DESC""",
            "Resumen hechos_opiniones — distribución por sentimiento",
        ),
        (
            "resumen_ventas_producto",
            analitica,
            """SELECT dp.nombre AS producto,
                      COUNT(hv.id)                     AS total_lineas,
                      SUM(hv.cantidad)                 AS unidades_vendidas,
                      ROUND(SUM(hv.monto_total), 2)    AS ingresos_totales
               FROM hechos_ventas hv
               JOIN dim_producto dp ON dp.id = hv.producto_id
               GROUP BY hv.producto_id
               ORDER BY ingresos_totales DESC
               LIMIT 12""",
            "Resumen hechos_ventas — top productos por ingresos",
        ),
    ]

    colors = {
        "hechos_ventas":          "#1f497d",
        "hechos_ventas_join":     "#1f497d",
        "hechos_opiniones":       "#375623",
        "hechos_opiniones_join":  "#375623",
        "dim_fuente":             "#7b2c2c",
        "resumen_sentimientos":   "#375623",
        "resumen_ventas_producto": "#1f497d",
    }

    paths: dict[str, Path] = {}
    for key, db, sql, title in jobs:
        p = out_dir / f"captura_{key}.png"
        try:
            cols, cells = _query_to_cells(db, sql)
        except sqlite3.Error as e:
            print(f"Aviso SQLite [{key}]: {e}", file=sys.stderr)
            cols, cells = [], []
        _save_table_png(cols, cells, title, p, header_color=colors.get(key, "#1f497d"))
        paths[key] = p

    return paths


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    generar_capturas_facts(root, ejecutar_carga=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
