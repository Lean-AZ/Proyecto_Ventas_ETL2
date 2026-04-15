#!/usr/bin/env python3
"""
Genera PNG tipo captura de pantalla con muestras de tablas (SQLite),
para incrustar en el informe de carga al Data Warehouse.
Requiere: matplotlib (pip install matplotlib)
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


def _run_etl(root: Path) -> None:
    """Ejecuta el pipeline para que staging y analítica tengan datos."""
    r = subprocess.run(
        [sys.executable, str(root / "run_etl.py")],
        cwd=str(root),
        capture_output=True,
        text=True,
        timeout=180,
    )
    if r.returncode != 0:
        print("Aviso: run_etl terminó con código", r.returncode, file=sys.stderr)
        if r.stderr:
            print(r.stderr[:2000], file=sys.stderr)


def _truncate(s: Any, n: int = 32) -> str:
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
        cells = [[_truncate(v, 36) for v in row] for row in raw]
        return cols, cells
    finally:
        conn.close()


def _save_table_png(
    cols: list[str],
    cells: list[list[str]],
    title: str,
    out: Path,
) -> None:
    out.parent.mkdir(parents=True, exist_ok=True)
    nrows = len(cells)
    ncols = len(cols) if cols else 1
    fig_w = min(16.0, 2.0 + ncols * 1.35)
    fig_h = min(11.0, 2.2 + max(nrows, 1) * 0.42)
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
        note = "(0 filas; correr run_etl.py o revisar datos)"
        ax.text(0.02, 0.92, note, transform=ax.transAxes, fontsize=9, color="#666")
    tbl = ax.table(
        cellText=cells,
        colLabels=cols,
        loc="upper center",
        cellLoc="left",
        colColours=["#2f5597"] * ncols,
    )
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(8)
    tbl.scale(1, 2.0)
    for (row, col), cell in tbl.get_celld().items():
        if row == 0:
            cell.set_text_props(color="white", fontweight="bold")
            cell.set_height(0.08)
        else:
            cell.set_facecolor("#ffffff" if row % 2 else "#e9eef5")
    plt.tight_layout()
    fig.savefig(out, dpi=140, bbox_inches="tight", facecolor="white")
    plt.close(fig)


def generar_capturas(root: Path, ejecutar_etl: bool = True) -> dict[str, Path]:
    """
    Genera PNG en docs_actividad1/capturas_carga/.
    Devuelve rutas por clave: staging_productos, dim_fecha, dim_producto, dim_cliente, hechos_ventas.
    """
    root = root.resolve()
    sys.path.insert(0, str(root))
    from etl.config import load_config

    out_dir = root / "docs_actividad1" / "capturas_carga"
    out_dir.mkdir(parents=True, exist_ok=True)

    if ejecutar_etl:
        _run_etl(root)

    cfg = load_config()
    staging = cfg["databases"]["staging"]
    analitica = cfg["databases"]["analitica"]

    jobs: list[tuple[str, str, str, str]] = [
        (
            "staging_productos",
            staging,
            "SELECT id, nombre, categoria, precio, stock, fuente FROM staging_productos ORDER BY id LIMIT 12",
            "Staging — staging_productos (muestra)",
        ),
        (
            "dim_fecha",
            analitica,
            "SELECT id, fecha, anio, mes, trimestre, nombre_mes, nombre_dia FROM dim_fecha ORDER BY id LIMIT 10",
            "Data Warehouse — dim_fecha (muestra)",
        ),
        (
            "dim_producto",
            analitica,
            "SELECT id, nombre, categoria, precio, stock FROM dim_producto ORDER BY id LIMIT 12",
            "Data Warehouse — dim_producto (muestra)",
        ),
        (
            "dim_cliente",
            analitica,
            "SELECT id, nombre_completo, email, ciudad, pais FROM dim_cliente ORDER BY id LIMIT 12",
            "Data Warehouse — dim_cliente (muestra)",
        ),
        (
            "hechos_ventas",
            analitica,
            "SELECT id, id_pedido, producto_id, cliente_id, fecha_id, cantidad, monto_total FROM hechos_ventas ORDER BY id LIMIT 12",
            "Data Warehouse — hechos_ventas (muestra)",
        ),
    ]

    paths: dict[str, Path] = {}
    for key, db, sql, title in jobs:
        p = out_dir / f"captura_{key}.png"
        try:
            cols, cells = _query_to_cells(db, sql)
        except sqlite3.Error as e:
            print(f"Aviso SQLite [{key}]: {e}", file=sys.stderr)
            cols, cells = [], []
        _save_table_png(cols, cells, title, p)
        paths[key] = p
        print(f"Captura: {p}")

    return paths


def main() -> int:
    root = Path(__file__).resolve().parent.parent
    generar_capturas(root, ejecutar_etl=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
