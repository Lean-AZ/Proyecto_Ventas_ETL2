#!/usr/bin/env python3
"""
Genera el documento PDF de entrega:
"Carga de Tablas de Hechos al Data Warehouse"

Requiere: reportlab   (pip install reportlab)
Salida  : docs_actividad1/Entrega_Carga_Facts_DataWarehouse.pdf

Flujo interno:
  1. Ejecuta cargar_facts_dw.py (a menos que SKIP_CARGA=1 esté definido)
  2. Genera capturas PNG con capturas_facts_dw.py
  3. Arma el PDF con descripción de cada tabla de hechos
"""
from __future__ import annotations

import importlib.util
import os
import subprocess
import sys
from pathlib import Path

# ── Instalación automática de reportlab ──────────────────────────────────────
try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import (
        HRFlowable,
        Image,
        ListFlowable,
        ListItem,
        PageBreak,
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
except ImportError:
    subprocess.check_call([sys.executable, "-m", "pip", "install", "reportlab", "-q"])
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.platypus import (
        HRFlowable,
        Image,
        ListFlowable,
        ListItem,
        PageBreak,
        Paragraph,
        SimpleDocTemplate,
        Spacer,
        Table,
        TableStyle,
    )
    from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY

ROOT = Path(__file__).resolve().parent.parent
OUTPUT = ROOT / "docs_actividad1" / "Entrega_Carga_Facts_DataWarehouse.pdf"
REPO_HTTPS = "https://github.com/Lean-AZ/Proyecto_Ventas_ETL2"

# ── Paleta de colores ────────────────────────────────────────────────────────
AZUL      = colors.HexColor("#1f497d")
AZUL_CLARO = colors.HexColor("#dce6f1")
VERDE     = colors.HexColor("#375623")
VERDE_CLARO = colors.HexColor("#e2efda")
ROJO      = colors.HexColor("#7b2c2c")
GRIS_HEADER = colors.HexColor("#404040")
BLANCO    = colors.white


# ── Helpers ──────────────────────────────────────────────────────────────────

def _cargar_modulo_capturas():
    path = ROOT / "scripts" / "capturas_facts_dw.py"
    spec = importlib.util.spec_from_file_location("capturas_facts_dw", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _img(ruta: Path | None, ancho_cm: float = 15.0) -> Image | None:
    if ruta and ruta.exists():
        img = Image(str(ruta))
        img.drawWidth = ancho_cm * cm
        img.drawHeight = img.drawWidth * img.imageHeight / img.imageWidth
        return img
    return None


def _tabla_columnas(
    estilos: list[tuple[str, str]],
    encabezado: tuple[str, str] = ("Columna", "Descripción"),
    color_header: object = AZUL,
) -> Table:
    data = [list(encabezado)] + [list(f) for f in estilos]
    t = Table(data, colWidths=[5 * cm, 11.5 * cm])
    t.setStyle(
        TableStyle([
            ("BACKGROUND",   (0, 0), (-1, 0), color_header),
            ("TEXTCOLOR",    (0, 0), (-1, 0), BLANCO),
            ("FONTNAME",     (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE",     (0, 0), (-1, 0), 9),
            ("ALIGN",        (0, 0), (-1, 0), "CENTER"),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, AZUL_CLARO]),
            ("FONTSIZE",     (0, 1), (-1, -1), 8),
            ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
            ("GRID",         (0, 0), (-1, -1), 0.4, colors.HexColor("#aaaaaa")),
            ("TOPPADDING",   (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING",(0, 0), (-1, -1), 4),
            ("LEFTPADDING",  (0, 0), (-1, -1), 6),
        ])
    )
    return t


def _hr(color=AZUL) -> HRFlowable:
    return HRFlowable(width="100%", thickness=1.2, color=color, spaceAfter=6)


# ── Construcción del PDF ──────────────────────────────────────────────────────

def main() -> None:
    # 1. Generar capturas
    skip = os.environ.get("SKIP_CARGA", "").strip() == "1"
    print("Generando capturas PNG de las tablas de hechos…")
    try:
        capt_mod = _cargar_modulo_capturas()
        capturas: dict[str, Path] = capt_mod.generar_capturas_facts(
            ROOT, ejecutar_carga=not skip
        )
    except Exception as e:
        print("Aviso: no se pudieron generar capturas:", e)
        capturas = {}

    # 2. Configurar documento
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    doc = SimpleDocTemplate(
        str(OUTPUT),
        pagesize=A4,
        leftMargin=2.2 * cm,
        rightMargin=2.2 * cm,
        topMargin=2 * cm,
        bottomMargin=2 * cm,
        title="Carga de Tablas de Hechos al Data Warehouse",
        author="Equipo ETL — Big Data",
    )

    base = getSampleStyleSheet()

    # Estilos personalizados
    s_titulo = ParagraphStyle(
        "Titulo",
        parent=base["Title"],
        fontSize=20,
        textColor=AZUL,
        spaceAfter=6,
        alignment=TA_CENTER,
    )
    s_subtitulo = ParagraphStyle(
        "Subtitulo",
        parent=base["Normal"],
        fontSize=11,
        textColor=GRIS_HEADER,
        alignment=TA_CENTER,
        spaceAfter=16,
    )
    s_h1 = ParagraphStyle(
        "H1",
        parent=base["Heading1"],
        fontSize=13,
        textColor=AZUL,
        spaceBefore=14,
        spaceAfter=4,
    )
    s_h2 = ParagraphStyle(
        "H2",
        parent=base["Heading2"],
        fontSize=11,
        textColor=VERDE,
        spaceBefore=10,
        spaceAfter=3,
    )
    s_body = ParagraphStyle(
        "Body",
        parent=base["Normal"],
        fontSize=9,
        leading=14,
        spaceAfter=6,
        alignment=TA_JUSTIFY,
    )
    s_pie = ParagraphStyle(
        "Pie",
        parent=base["Normal"],
        fontSize=8,
        textColor=colors.HexColor("#555555"),
        spaceBefore=2,
        spaceAfter=8,
        alignment=TA_CENTER,
        italics=True,
    )
    s_code = ParagraphStyle(
        "Code",
        parent=base["Code"],
        fontSize=8,
        backColor=colors.HexColor("#f4f4f4"),
        leftIndent=10,
        spaceBefore=4,
        spaceAfter=6,
        leading=12,
    )

    story = []

    # ── PORTADA ───────────────────────────────────────────────────────────────
    story.append(Spacer(1, 1.5 * cm))
    story.append(Paragraph("Carga de Tablas de Hechos", s_titulo))
    story.append(Paragraph("al Data Warehouse", s_titulo))
    story.append(Spacer(1, 0.3 * cm))
    story.append(_hr())
    story.append(Paragraph(
        "Sistema de Análisis de Ventas — Informe de carga de tablas de hechos",
        s_subtitulo,
    ))
    story.append(Spacer(1, 0.4 * cm))

    portada_data = [
        ["Proyecto:",   "Sistema de Análisis de Ventas (ETL con SQLite)"],
        ["Entrega:",    "Carga de Tablas de Hechos al DW"],
        ["Fecha:",      "Abril de 2026"],
        ["Repositorio:", REPO_HTTPS],
        ["BD analítica:", "data/ventas_analitica.db"],
        ["Facts cargadas:", "hechos_ventas  ·  hechos_opiniones"],
    ]
    t_portada = Table(portada_data, colWidths=[4.5 * cm, 12 * cm])
    t_portada.setStyle(TableStyle([
        ("FONTNAME",  (0, 0), (0, -1), "Helvetica-Bold"),
        ("FONTSIZE",  (0, 0), (-1, -1), 9),
        ("VALIGN",    (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING",(0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("ROWBACKGROUNDS", (0, 0), (-1, -1),
         [AZUL_CLARO, colors.white, AZUL_CLARO, colors.white, AZUL_CLARO, colors.white]),
        ("GRID", (0, 0), (-1, -1), 0.3, colors.HexColor("#cccccc")),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))
    story.append(t_portada)
    story.append(PageBreak())

    # ── SECCIÓN 1: CONTEXTO ───────────────────────────────────────────────────
    story.append(Paragraph("1. Contexto del proceso", s_h1))
    story.append(_hr())
    story.append(Paragraph(
        "El Data Warehouse del proyecto almacena información analítica en <b>ventas_analitica.db</b> "
        "(SQLite), organizado en un esquema estrella. Las dimensiones (dim_producto, dim_cliente, "
        "dim_fecha) fueron cargadas en la etapa anterior. En esta entrega se documentan los pasos "
        "para cargar las <b>tablas de hechos</b>: hechos_ventas y hechos_opiniones.",
        s_body,
    ))
    story.append(Paragraph(
        "Antes de cada carga se ejecuta un proceso de <b>limpieza (TRUNCATE lógico)</b> que elimina "
        "todas las filas de las tablas de hechos y resetea los contadores autoincrement. Esto garantiza "
        "una carga limpia y reproducible en cada ejecución del pipeline.",
        s_body,
    ))
    story.append(Spacer(1, 0.3 * cm))

    # ── SECCIÓN 2: ARQUITECTURA DEL PROCESO ───────────────────────────────────
    story.append(Paragraph("2. Arquitectura del proceso de carga", s_h1))
    story.append(_hr())
    story.append(Paragraph(
        "El script principal <b>cargar_facts_dw.py</b> orquesta el proceso en cuatro pasos "
        "secuenciales. Cada paso está aislado: si falla la carga de opiniones, los hechos de "
        "ventas ya están persistidos.",
        s_body,
    ))

    pasos = [
        ("<b>Paso 0 — Verificar schema</b>: se ejecuta "
         "sql/02_add_facts_opiniones.sql con CREATE TABLE IF NOT EXISTS para dim_fuente y "
         "hechos_opiniones. Las tablas ya existentes no se modifican."),
        ("<b>Paso 1 — Limpieza de facts</b>: DELETE FROM hechos_ventas y "
         "DELETE FROM hechos_opiniones, seguido de DELETE FROM sqlite_sequence para "
         "resetear el autoincrement. Se registra la cantidad de filas eliminadas."),
        ("<b>Paso 2 — Pipeline ETL</b>: ejecuta run_etl.py que extrae datos de CSV, "
         "BD relacional y API REST, los consolida en staging.db y los pasa a la "
         "BD analítica mediante etl/loader.py."),
        ("<b>Paso 3 — Carga de hechos_ventas</b>: load_from_staging() lee staging_detalles "
         "JOIN staging_pedidos y genera filas para hechos_ventas con las FK correctas "
         "(producto_id, cliente_id, fecha_id en formato YYYYMMDD)."),
        ("<b>Paso 4 — Carga de hechos_opiniones</b>: cargar_hechos_opiniones() genera "
         "800 registros sintéticos con calificaciones, sentimientos y comentarios en "
         "español, referenciando IDs reales de las dimensiones existentes."),
    ]
    items = [ListItem(Paragraph(p, s_body), leftIndent=20) for p in pasos]
    story.append(ListFlowable(items, bulletType="bullet", leftIndent=10))
    story.append(Spacer(1, 0.4 * cm))

    # Diagrama de flujo en texto
    story.append(Paragraph("Flujo de ejecución:", s_h2))
    flujo_txt = (
        "cargar_facts_dw.py\n"
        "   ├── [Paso 0] asegurar_schema_opiniones()   → dim_fuente, hechos_opiniones\n"
        "   ├── [Paso 1] limpiar_todas_facts()         → DELETE hechos_ventas + hechos_opiniones\n"
        "   ├── [Paso 2] run_etl.py                    → CSV / BD / API → staging.db\n"
        "   ├── [Paso 3] load_from_staging()           → staging → hechos_ventas\n"
        "   └── [Paso 4] cargar_hechos_opiniones()     → sintético → hechos_opiniones"
    )
    story.append(Paragraph(flujo_txt.replace("\n", "<br/>"), s_code))
    story.append(PageBreak())

    # ── SECCIÓN 3: PROCESO DE LIMPIEZA ────────────────────────────────────────
    story.append(Paragraph("3. Proceso de limpieza de tablas de hechos", s_h1))
    story.append(_hr())
    story.append(Paragraph(
        "La función <b>limpiar_todas_facts(conn)</b> en <i>etl/facts_loader.py</i> encapsula la "
        "lógica de limpieza. Antes de ejecutar cualquier INSERT, se eliminan todas las filas "
        "existentes y se restablece el contador de la clave primaria.",
        s_body,
    ))

    story.append(Paragraph("Lógica de limpiar_tabla_fact():", s_h2))
    codigo_limpieza = (
        "def limpiar_tabla_fact(conn, tabla):\n"
        "    n = conn.execute(f'SELECT COUNT(*) FROM {tabla}').fetchone()[0]\n"
        "    conn.execute(f'DELETE FROM {tabla}')   # elimina todas las filas\n"
        "    conn.execute('DELETE FROM sqlite_sequence WHERE name=?', (tabla,))\n"
        "    return n   # devuelve cantidad de filas eliminadas"
    )
    story.append(Paragraph(codigo_limpieza.replace("\n", "<br/>").replace(" ", "&nbsp;"), s_code))

    story.append(Paragraph(
        "Se usa <b>DELETE</b> en lugar de TRUNCATE porque SQLite no soporta TRUNCATE TABLE. "
        "El borrado de sqlite_sequence restablece el autoincrement al valor inicial (1), "
        "garantizando IDs consecutivos desde el principio en cada recarga.",
        s_body,
    ))

    story.append(Paragraph("Tablas limpiadas en cada ejecución:", s_h2))
    limpieza_cols = [
        ("hechos_ventas", "Líneas de detalle de ventas con FK a dim_producto, dim_cliente, dim_fecha"),
        ("hechos_opiniones", "Opiniones de clientes con FK a dim_producto, dim_cliente, dim_fecha, dim_fuente"),
    ]
    story.append(_tabla_columnas(
        limpieza_cols, encabezado=("Tabla de Hechos", "Descripción"), color_header=ROJO
    ))
    story.append(Spacer(1, 0.4 * cm))

    story.append(Paragraph("Salida de log esperada después de la limpieza:", s_h2))
    log_txt = (
        "PASO 1: Limpieza de tablas de hechos\n"
        "  ✓ hechos_ventas    : 19,983 filas eliminadas\n"
        "  ✓ hechos_opiniones :    800 filas eliminadas\n"
        "  Limpieza completada en 0.012 s"
    )
    story.append(Paragraph(log_txt.replace("\n", "<br/>"), s_code))
    story.append(PageBreak())

    # ── SECCIÓN 4: hechos_ventas ──────────────────────────────────────────────
    story.append(Paragraph("4. Tabla de hechos: hechos_ventas", s_h1))
    story.append(_hr())
    story.append(Paragraph(
        "Almacena cada línea de detalle de pedido del sistema de ventas. La granularidad es "
        "a nivel de producto-por-pedido: si un pedido tiene 3 productos distintos, se generan "
        "3 filas en hechos_ventas.",
        s_body,
    ))
    story.append(Paragraph(
        "Los datos se cargan mediante un JOIN entre staging_detalles y staging_pedidos, "
        "convirtiendo la fecha de texto ISO (YYYY-MM-DD) al entero YYYYMMDD que referencia dim_fecha.",
        s_body,
    ))

    story.append(Paragraph("Estructura de la tabla:", s_h2))
    cols_hv = [
        ("id", "PK surrogate autoincremental (reinicia en cada carga limpia)"),
        ("id_pedido", "Identificador del pedido; agrupa líneas del mismo pedido"),
        ("producto_id", "FK → dim_producto.id"),
        ("cliente_id", "FK → dim_cliente.id"),
        ("fecha_id", "FK → dim_fecha.id (formato YYYYMMDD del pedido)"),
        ("cantidad", "Unidades vendidas en esa línea de detalle"),
        ("monto_total", "Importe total de la línea (precio × cantidad)"),
        ("creado_en", "Timestamp de inserción (datetime SQLite)"),
    ]
    story.append(_tabla_columnas(cols_hv))
    story.append(Spacer(1, 0.3 * cm))

    story.append(Paragraph("SQL de carga (simplificado):", s_h2))
    sql_hv = (
        "-- Paso previo: DELETE FROM hechos_ventas\n"
        "INSERT INTO hechos_ventas\n"
        "    (id_pedido, producto_id, cliente_id, fecha_id, cantidad, monto_total)\n"
        "SELECT d.id_pedido, d.id_producto, p.id_cliente,\n"
        "       CAST(REPLACE(p.fecha, '-', '') AS INTEGER),\n"
        "       d.cantidad, d.monto_total\n"
        "FROM staging_detalles d\n"
        "JOIN staging_pedidos  p ON d.id_pedido = p.id_pedido;"
    )
    story.append(Paragraph(sql_hv.replace("\n", "<br/>").replace(" ", "&nbsp;"), s_code))
    story.append(Spacer(1, 0.3 * cm))

    img_hv = _img(capturas.get("hechos_ventas"))
    if img_hv:
        story.append(img_hv)
        story.append(Paragraph("Figura 1 — Muestra de filas en hechos_ventas (14 primeras)", s_pie))
    story.append(Spacer(1, 0.2 * cm))

    img_hv_join = _img(capturas.get("hechos_ventas_join"))
    if img_hv_join:
        story.append(img_hv_join)
        story.append(Paragraph(
            "Figura 2 — hechos_ventas desnormalizada: JOIN con dim_producto, dim_cliente, dim_fecha",
            s_pie,
        ))

    img_rv = _img(capturas.get("resumen_ventas_producto"))
    if img_rv:
        story.append(Spacer(1, 0.2 * cm))
        story.append(img_rv)
        story.append(Paragraph(
            "Figura 3 — Top productos por ingresos totales (agrupado desde hechos_ventas)", s_pie
        ))

    story.append(PageBreak())

    # ── SECCIÓN 5: hechos_opiniones ───────────────────────────────────────────
    story.append(Paragraph("5. Tabla de hechos: hechos_opiniones", s_h1))
    story.append(_hr())
    story.append(Paragraph(
        "Registra las opiniones de clientes sobre productos, capturadas desde múltiples fuentes "
        "(encuestas web, tienda online, redes sociales, app móvil). La granularidad es a nivel "
        "de opinión individual.",
        s_body,
    ))
    story.append(Paragraph(
        "Los 800 registros cargados son sintéticos pero referencian IDs reales de las dimensiones "
        "existentes (dim_producto, dim_cliente, dim_fecha), garantizando la integridad referencial. "
        "El sentimiento se deriva automáticamente de la calificación: ≥4 → positivo, 3 → neutro, "
        "≤2 → negativo.",
        s_body,
    ))

    story.append(Paragraph("Estructura de la tabla:", s_h2))
    cols_ho = [
        ("id", "PK surrogate autoincremental"),
        ("producto_id", "FK → dim_producto.id (producto evaluado)"),
        ("cliente_id", "FK → dim_cliente.id (nullable: 5% opiniones anónimas)"),
        ("fecha_id", "FK → dim_fecha.id (YYYYMMDD del comentario)"),
        ("fuente_id", "FK → dim_fuente.id (canal de captura)"),
        ("calificacion", "Puntuación 1–5 (entero con CHECK constraint)"),
        ("sentimiento", "positivo / neutro / negativo (CHECK constraint)"),
        ("comentario", "Texto libre en español"),
        ("id_externo", "Identificador del sistema de origen (EXT-NNNNN)"),
        ("creado_en", "Timestamp de inserción"),
    ]
    story.append(_tabla_columnas(cols_ho, color_header=VERDE))
    story.append(Spacer(1, 0.3 * cm))

    img_ho = _img(capturas.get("hechos_opiniones"))
    if img_ho:
        story.append(img_ho)
        story.append(Paragraph("Figura 4 — Muestra de filas en hechos_opiniones (14 primeras)", s_pie))
    story.append(Spacer(1, 0.2 * cm))

    img_ho_join = _img(capturas.get("hechos_opiniones_join"))
    if img_ho_join:
        story.append(img_ho_join)
        story.append(Paragraph(
            "Figura 5 — hechos_opiniones desnormalizada: JOIN con dimensiones", s_pie
        ))

    img_sent = _img(capturas.get("resumen_sentimientos"))
    if img_sent:
        story.append(Spacer(1, 0.2 * cm))
        story.append(img_sent)
        story.append(Paragraph(
            "Figura 6 — Distribución de sentimientos con calificación promedio por grupo",
            s_pie,
        ))
    story.append(PageBreak())

    # ── SECCIÓN 6: dim_fuente ────────────────────────────────────────────────
    story.append(Paragraph("6. Dimensión adicional: dim_fuente", s_h1))
    story.append(_hr())
    story.append(Paragraph(
        "Para soportar hechos_opiniones se creó la dimensión <b>dim_fuente</b>, que cataloga "
        "los canales desde donde se capturan las opiniones de los clientes.",
        s_body,
    ))

    story.append(Paragraph("Estructura de dim_fuente:", s_h2))
    cols_df = [
        ("id", "PK autoincremental"),
        ("nombre", "Nombre del canal (UNIQUE): Encuesta Web, Tienda Online, etc."),
        ("descripcion", "Descripción del canal de captura"),
        ("creado_en", "Timestamp de inserción"),
    ]
    story.append(_tabla_columnas(cols_df, color_header=ROJO))
    story.append(Spacer(1, 0.3 * cm))

    story.append(Paragraph("Fuentes registradas:", s_h2))
    fuentes_data = [
        ["Encuesta Web",    "Formulario de satisfacción post-compra en el sitio web"],
        ["Tienda Online",   "Reseñas publicadas en la plataforma de e-commerce"],
        ["Redes Sociales",  "Menciones y comentarios en Twitter/Instagram"],
        ["App Móvil",       "Calificaciones enviadas desde la aplicación móvil"],
    ]
    t_fuentes = Table(
        [["Nombre", "Descripción"]] + fuentes_data,
        colWidths=[4.5 * cm, 12 * cm],
    )
    t_fuentes.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, 0), ROJO),
        ("TEXTCOLOR",    (0, 0), (-1, 0), BLANCO),
        ("FONTNAME",     (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",     (0, 0), (-1, -1), 9),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#fce4e4")]),
        ("GRID",         (0, 0), (-1, -1), 0.4, colors.HexColor("#aaaaaa")),
        ("TOPPADDING",   (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 5),
        ("LEFTPADDING",  (0, 0), (-1, -1), 6),
    ]))
    story.append(t_fuentes)
    story.append(Spacer(1, 0.3 * cm))

    img_df = _img(capturas.get("dim_fuente"))
    if img_df:
        story.append(img_df)
        story.append(Paragraph("Figura 7 — dim_fuente en ventas_analitica.db", s_pie))

    story.append(PageBreak())

    # ── SECCIÓN 7: ARCHIVOS DEL PROCESO ──────────────────────────────────────
    story.append(Paragraph("7. Archivos involucrados en el proceso", s_h1))
    story.append(_hr())
    archivos = [
        ("cargar_facts_dw.py",              "Script principal. Orquesta limpieza + carga de ambas facts."),
        ("etl/facts_loader.py",             "Funciones de limpieza (limpiar_todas_facts) y carga (cargar_hechos_opiniones)."),
        ("etl/loader.py",                   "Función load_from_staging: carga hechos_ventas desde staging.db."),
        ("sql/02_add_facts_opiniones.sql",  "Schema SQL: CREATE TABLE dim_fuente y hechos_opiniones con índices."),
        ("sql/01_create_schema_ventas.sql", "Schema base: dim_producto, dim_cliente, dim_fecha, hechos_ventas."),
        ("run_etl.py",                      "Pipeline ETL: extracción CSV/BD/API → staging → carga analítica."),
        ("etl/staging.py",                  "Gestión de staging.db: tablas staging_productos, clientes, pedidos, detalles."),
        ("scripts/capturas_facts_dw.py",    "Genera PNG de las tablas de hechos para esta documentación."),
    ]
    t_archivos = Table(
        [["Archivo", "Rol en el proceso"]] + archivos,
        colWidths=[6.5 * cm, 10 * cm],
    )
    t_archivos.setStyle(TableStyle([
        ("BACKGROUND",   (0, 0), (-1, 0), AZUL),
        ("TEXTCOLOR",    (0, 0), (-1, 0), BLANCO),
        ("FONTNAME",     (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",     (0, 0), (-1, -1), 8),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, AZUL_CLARO]),
        ("GRID",         (0, 0), (-1, -1), 0.4, colors.HexColor("#aaaaaa")),
        ("TOPPADDING",   (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING",(0, 0), (-1, -1), 5),
        ("LEFTPADDING",  (0, 0), (-1, -1), 6),
        ("VALIGN",       (0, 0), (-1, -1), "MIDDLE"),
        ("FONTNAME",     (0, 1), (0, -1), "Courier"),
    ]))
    story.append(t_archivos)
    story.append(Spacer(1, 0.5 * cm))

    # ── SECCIÓN 8: CÓMO REPRODUCIR ───────────────────────────────────────────
    story.append(Paragraph("8. Cómo reproducir el proceso", s_h1))
    story.append(_hr())
    pasos_repro = [
        "Clonar el repositorio: <font name='Courier'>git clone " + REPO_HTTPS + "</font>",
        "Instalar dependencias: <font name='Courier'>pip install reportlab matplotlib python-docx</font>",
        "Ejecutar carga completa: <font name='Courier'>python cargar_facts_dw.py</font>",
        "Para omitir la extracción ETL (reutilizar staging): "
        "<font name='Courier'>python cargar_facts_dw.py --skip-etl</font>",
        "Regenerar este PDF: <font name='Courier'>python scripts/generar_pdf_carga_facts_dw.py</font>",
    ]
    items_r = [ListItem(Paragraph(p, s_body), leftIndent=20) for p in pasos_repro]
    story.append(ListFlowable(items_r, bulletType="bullet", leftIndent=10))
    story.append(Spacer(1, 0.5 * cm))
    story.append(_hr(color=GRIS_HEADER))
    story.append(Paragraph(
        f"Repositorio: {REPO_HTTPS}  ·  Fecha: Abril 2026  ·  Big Data — Sistema de Ventas",
        ParagraphStyle("footer", parent=s_pie, fontSize=8, textColor=colors.HexColor("#888888")),
    ))

    # 3. Compilar PDF
    doc.build(story)
    print(f"\nPDF generado: {OUTPUT}")


if __name__ == "__main__":
    main()
