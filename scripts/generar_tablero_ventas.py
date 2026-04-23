#!/usr/bin/env python3
"""
Genera el Tablero de Ventas en PNG, similar al diseño Power BI de la práctica.
Layout:
  [KPI Total Ventas] [KPI Total Pedidos] [KPI Monto Total]
  [Ventas por Mes]                        [Ventas por País (top 10)]
  [Monto por Categoría]                   [Cantidad por Producto (top 15)]

Salida: docs_actividad1/Tablero_Ventas.png
Requiere: matplotlib, sqlite3
"""
import sqlite3
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import matplotlib.ticker as mticker
import numpy as np

ROOT   = Path(__file__).resolve().parent.parent
DB     = ROOT / "data" / "ventas_analitica.db"
OUTPUT = ROOT / "docs_actividad1" / "Tablero_Ventas.png"

# ── Paleta estilo Power BI ────────────────────────────────────────────────────
AZUL_PBI   = "#4472C4"
AZUL_HOVER = "#2E5FAC"
FONDO      = "#F2F2F2"
FONDO_CARD = "#FFFFFF"
TITULO_COLOR = "#1F3864"
GRIS_EJE   = "#595959"
AZUL_BARRA = "#4472C4"


def _q(conn, sql):
    cur = conn.execute(sql)
    cols = [d[0] for d in cur.description]
    rows = cur.fetchall()
    return cols, rows


def _card(ax, valor, etiqueta, fmt="{:,}"):
    ax.set_facecolor(FONDO_CARD)
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis("off")
    ax.text(0.5, 0.62, fmt.format(valor),
            ha="center", va="center", fontsize=22, fontweight="bold",
            color=TITULO_COLOR, transform=ax.transAxes)
    ax.text(0.5, 0.28, etiqueta,
            ha="center", va="center", fontsize=9, color=GRIS_EJE,
            transform=ax.transAxes)
    for spine in ["top","bottom","left","right"]:
        ax.spines[spine].set_visible(False)
    ax.add_patch(mpatches.FancyBboxPatch(
        (0.0, 0.0), 1.0, 1.0,
        boxstyle="round,pad=0.03",
        linewidth=1.2, edgecolor="#CCCCCC", facecolor=FONDO_CARD,
        transform=ax.transAxes, clip_on=False,
    ))


def _bar_h(ax, categorias, valores, titulo, color=AZUL_BARRA, xlabel="Suma de Monto Total"):
    y = np.arange(len(categorias))
    bars = ax.barh(y, valores, color=color, height=0.6, edgecolor="white", linewidth=0.5)
    ax.set_yticks(y)
    ax.set_yticklabels(categorias, fontsize=8, color=GRIS_EJE)
    ax.invert_yaxis()
    ax.set_facecolor(FONDO_CARD)
    ax.set_title(titulo, fontsize=9, color=TITULO_COLOR, fontweight="bold", pad=8, loc="left")
    ax.set_xlabel(xlabel, fontsize=7.5, color=GRIS_EJE)
    ax.tick_params(axis="x", labelsize=7.5, colors=GRIS_EJE)
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(
        lambda x, _: f"{x/1e6:.1f}M" if x >= 1e6 else f"{x/1e3:.0f}k" if x >= 1e3 else f"{int(x)}"
    ))
    ax.grid(axis="x", color="#E5E5E5", linewidth=0.6)
    ax.set_axisbelow(True)
    for spine in ["top","right"]:
        ax.spines[spine].set_visible(False)
    ax.spines["left"].set_color("#DDDDDD")
    ax.spines["bottom"].set_color("#DDDDDD")
    # etiquetas en barras
    for bar, val in zip(bars, valores):
        ax.text(bar.get_width() + max(valores) * 0.01, bar.get_y() + bar.get_height() / 2,
                f"{val:,.0f}", va="center", fontsize=6.5, color=GRIS_EJE)


def _bar_v(ax, categorias, valores, titulo, color=AZUL_BARRA, ylabel="Suma de CantidadVentas"):
    x = np.arange(len(categorias))
    bars = ax.bar(x, valores, color=color, width=0.55, edgecolor="white", linewidth=0.5)
    ax.set_xticks(x)
    ax.set_xticklabels(categorias, fontsize=7, color=GRIS_EJE, rotation=30, ha="right")
    ax.set_facecolor(FONDO_CARD)
    ax.set_title(titulo, fontsize=9, color=TITULO_COLOR, fontweight="bold", pad=8, loc="left")
    ax.set_ylabel(ylabel, fontsize=7.5, color=GRIS_EJE)
    ax.tick_params(axis="y", labelsize=7.5, colors=GRIS_EJE)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(
        lambda x, _: f"{x/1e3:.0f}k" if x >= 1000 else f"{int(x)}"
    ))
    ax.grid(axis="y", color="#E5E5E5", linewidth=0.6)
    ax.set_axisbelow(True)
    for spine in ["top","right"]:
        ax.spines[spine].set_visible(False)
    ax.spines["left"].set_color("#DDDDDD")
    ax.spines["bottom"].set_color("#DDDDDD")
    for bar, val in zip(bars, valores):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + max(valores) * 0.01,
                f"{val:,}", ha="center", fontsize=6, color=GRIS_EJE)


def main():
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB))

    # ── Consultas ─────────────────────────────────────────────────────────────
    total_pedidos = conn.execute(
        "SELECT COUNT(DISTINCT id_pedido) FROM hechos_ventas"
    ).fetchone()[0]
    total_cantidad = conn.execute(
        "SELECT SUM(cantidad) FROM hechos_ventas"
    ).fetchone()[0]
    total_monto = conn.execute(
        "SELECT SUM(monto_total) FROM hechos_ventas"
    ).fetchone()[0]

    # Ventas por mes (2023-2026, ordenado cronológicamente)
    _, rows_mes = _q(conn, """
        SELECT df.anio || '-' || printf('%02d',df.mes) AS periodo,
               df.nombre_mes || ' ' || df.anio        AS etiqueta,
               SUM(hv.cantidad)                        AS cant
        FROM hechos_ventas hv
        JOIN dim_fecha df ON df.id = hv.fecha_id
        WHERE df.anio BETWEEN 2023 AND 2026
        GROUP BY df.anio, df.mes
        ORDER BY df.anio, df.mes
        LIMIT 18
    """)
    labels_mes  = [r[1] for r in rows_mes]
    valores_mes = [r[2] for r in rows_mes]

    # Top 10 países por cantidad
    _, rows_pais = _q(conn, """
        SELECT dc.pais, SUM(hv.cantidad) AS cant
        FROM hechos_ventas hv
        JOIN dim_cliente dc ON dc.id = hv.cliente_id
        GROUP BY dc.pais
        ORDER BY cant DESC
        LIMIT 10
    """)
    labels_pais  = [r[0] for r in rows_pais]
    valores_pais = [r[1] for r in rows_pais]

    # Monto por categoría
    _, rows_cat = _q(conn, """
        SELECT dp.categoria, SUM(hv.monto_total) AS total
        FROM hechos_ventas hv
        JOIN dim_producto dp ON dp.id = hv.producto_id
        GROUP BY dp.categoria
        ORDER BY total DESC
    """)
    labels_cat  = [r[0] for r in rows_cat]
    valores_cat = [r[1] for r in rows_cat]

    # Top 15 productos por cantidad
    _, rows_prod = _q(conn, """
        SELECT dp.nombre, SUM(hv.cantidad) AS cant
        FROM hechos_ventas hv
        JOIN dim_producto dp ON dp.id = hv.producto_id
        GROUP BY dp.nombre
        ORDER BY cant DESC
        LIMIT 15
    """)
    labels_prod  = [r[0] for r in rows_prod]
    valores_prod = [r[1] for r in rows_prod]

    conn.close()

    # ── Layout ────────────────────────────────────────────────────────────────
    fig = plt.figure(figsize=(18, 11), facecolor=FONDO)
    fig.suptitle("Tablero de Ventas", fontsize=20, fontweight="bold",
                 color=TITULO_COLOR, y=0.97)

    # GridSpec: fila 0 = KPI cards (3 columnas), filas 1-2 = gráficos (2 columnas)
    from matplotlib.gridspec import GridSpec
    gs = GridSpec(
        3, 4,
        figure=fig,
        height_ratios=[0.18, 0.41, 0.41],
        hspace=0.48,
        wspace=0.32,
        left=0.06, right=0.97,
        top=0.92, bottom=0.06,
    )

    # ── KPI cards ─────────────────────────────────────────────────────────────
    ax_k1 = fig.add_subplot(gs[0, 0])
    ax_k2 = fig.add_subplot(gs[0, 1])
    ax_k3 = fig.add_subplot(gs[0, 2])
    ax_k4 = fig.add_subplot(gs[0, 3])

    _card(ax_k1, total_pedidos,  "Total Pedidos")
    _card(ax_k2, total_cantidad, "Suma de CantidadVentas")
    _card(ax_k3, round(total_monto / 1e6, 2), "Monto Total (Millones)", fmt="${:,.2f}M")
    _card(ax_k4, round(total_monto / total_pedidos, 2), "Ticket Promedio", fmt="${:,.2f}")

    # ── Gráfico 1: Ventas por mes (barra vertical) ────────────────────────────
    ax1 = fig.add_subplot(gs[1, :2])
    _bar_v(
        ax1, labels_mes, valores_mes,
        "Suma de CantidadVentas por Mes",
        ylabel="Suma de CantidadVentas",
    )

    # ── Gráfico 2: Top 10 países (barra horizontal) ───────────────────────────
    ax2 = fig.add_subplot(gs[1, 2:])
    _bar_h(
        ax2, labels_pais, valores_pais,
        "Suma de CantidadVentas por Country",
        xlabel="Suma de CantidadVentas",
    )

    # ── Gráfico 3: Monto por categoría (barra horizontal) ────────────────────
    ax3 = fig.add_subplot(gs[2, :2])
    _bar_h(
        ax3, labels_cat, valores_cat,
        "Suma de TotalVentas por Categoría de Producto",
        xlabel="Suma de TotalVentas",
    )

    # ── Gráfico 4: Top 15 productos por cantidad (barra vertical) ────────────
    ax4 = fig.add_subplot(gs[2, 2:])
    _bar_v(
        ax4, labels_prod, valores_prod,
        "Suma de CantidadVentas por Nombre de Producto (Top 15)",
        ylabel="Suma de CantidadVentas",
    )

    # Línea separadora debajo de KPIs
    fig.add_artist(plt.Line2D(
        [0.04, 0.97], [0.785, 0.785],
        transform=fig.transFigure,
        color="#CCCCCC", linewidth=1,
    ))

    fig.savefig(str(OUTPUT), dpi=160, bbox_inches="tight", facecolor=FONDO)
    plt.close(fig)
    print(f"Tablero generado: {OUTPUT}")


if __name__ == "__main__":
    main()
