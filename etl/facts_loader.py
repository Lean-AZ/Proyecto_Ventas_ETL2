"""
facts_loader: limpieza y carga de tablas de hechos en el Data Warehouse.
- limpiar_tabla_fact(): vacía una tabla de hechos y resetea el autoincrement.
- limpiar_todas_facts(): limpia hechos_ventas y hechos_opiniones.
- cargar_hechos_opiniones(): genera e inserta 800 registros sintéticos.
"""
import random
import sqlite3
from pathlib import Path
from typing import Any

RUTA_PROYECTO = Path(__file__).resolve().parent.parent
SQL_FACTS_OPINIONES = RUTA_PROYECTO / "sql" / "02_add_facts_opiniones.sql"

# Catálogo de fuentes de opinión
FUENTES: list[tuple[str, str]] = [
    ("Encuesta Web", "Formulario de satisfacción post-compra en el sitio web"),
    ("Tienda Online", "Reseñas publicadas en la plataforma de e-commerce"),
    ("Redes Sociales", "Menciones y comentarios en Twitter/Instagram"),
    ("App Móvil", "Calificaciones enviadas desde la aplicación móvil"),
]

COMENTARIOS: dict[str, list[str]] = {
    "positivo": [
        "Excelente producto, superó todas mis expectativas.",
        "Muy buena calidad, lo recomiendo sin dudas.",
        "Llegó en tiempo y forma, perfecto.",
        "Quedé muy satisfecho con la compra.",
        "La calidad es superior al precio que pagué.",
        "Me encantó, lo compraría de nuevo sin pensarlo.",
        "Muy buena relación calidad-precio.",
        "Funciona perfecto desde el primer día de uso.",
        "Increíble producto, muy contento con la compra.",
        "Todo conforme, el envío fue rápido y el producto impecable.",
    ],
    "neutro": [
        "El producto está bien, cumple su función básica.",
        "Dentro de lo esperado, sin nada especial.",
        "Correcto, aunque podría mejorar el empaque.",
        "Funciona bien, pero el envío tardó más de lo indicado.",
        "Normal, sin sorpresas positivas ni negativas.",
        "Cumple lo prometido, nada más ni nada menos.",
    ],
    "negativo": [
        "No cumplió mis expectativas para nada.",
        "La calidad es muy inferior a lo que muestran las fotos.",
        "Tuve problemas con el producto desde el primer uso.",
        "No lo recomendaría a ningún conocido.",
        "Decepciona bastante para el precio que tiene.",
        "Me llegó con un defecto de fábrica notorio.",
        "El producto dejó de funcionar a la semana de uso.",
    ],
}


def _sentimiento_por_calificacion(cal: int) -> str:
    if cal >= 4:
        return "positivo"
    if cal == 3:
        return "neutro"
    return "negativo"


def limpiar_tabla_fact(conn: sqlite3.Connection, tabla: str) -> int:
    """
    Vacía una tabla de hechos y resetea su contador autoincrement.
    Retorna la cantidad de filas que había antes de la limpieza.
    """
    n = conn.execute(f"SELECT COUNT(*) FROM {tabla}").fetchone()[0]
    conn.execute(f"DELETE FROM {tabla}")
    try:
        conn.execute("DELETE FROM sqlite_sequence WHERE name=?", (tabla,))
    except sqlite3.OperationalError:
        pass  # sqlite_sequence no existe si nunca hubo autoincrement
    return n


def limpiar_todas_facts(conn: sqlite3.Connection) -> dict[str, int]:
    """
    Limpia hechos_ventas y hechos_opiniones antes de recargar.
    Retorna un dict {nombre_tabla: filas_eliminadas}.
    """
    resultado: dict[str, int] = {}
    for tabla in ("hechos_ventas", "hechos_opiniones"):
        try:
            resultado[tabla] = limpiar_tabla_fact(conn, tabla)
        except sqlite3.OperationalError:
            resultado[tabla] = 0
    conn.commit()
    return resultado


def _cargar_dim_fuente(conn: sqlite3.Connection) -> dict[str, int]:
    """Inserta las fuentes de opinión si no existen. Retorna mapa nombre → id."""
    for nombre, desc in FUENTES:
        conn.execute(
            "INSERT OR IGNORE INTO dim_fuente (nombre, descripcion) VALUES (?, ?)",
            (nombre, desc),
        )
    conn.commit()
    rows = conn.execute("SELECT nombre, id FROM dim_fuente").fetchall()
    return {nombre: id_ for nombre, id_ in rows}


def _obtener_ids_validos(
    conn: sqlite3.Connection,
) -> tuple[list[int], list[int], list[int]]:
    """Devuelve listas de IDs válidos de dim_producto, dim_cliente y dim_fecha."""
    prod_ids = [r[0] for r in conn.execute("SELECT id FROM dim_producto ORDER BY id")]
    cli_ids = [r[0] for r in conn.execute("SELECT id FROM dim_cliente ORDER BY id")]
    fecha_ids = [
        r[0]
        for r in conn.execute(
            "SELECT id FROM dim_fecha WHERE anio BETWEEN 2021 AND 2025"
        )
    ]
    return prod_ids, cli_ids, fecha_ids


def cargar_hechos_opiniones(
    conn: sqlite3.Connection, n: int = 800, seed: int = 42
) -> int:
    """
    Genera n registros sintéticos de opiniones y los inserta en hechos_opiniones.
    Usa IDs reales de dim_producto, dim_cliente y dim_fecha para mantener integridad.
    Retorna la cantidad de filas insertadas.
    """
    rng = random.Random(seed)
    prod_ids, cli_ids, fecha_ids = _obtener_ids_validos(conn)

    if not prod_ids or not fecha_ids:
        return 0

    fuente_map = _cargar_dim_fuente(conn)
    fuente_nombres = list(fuente_map.keys())

    filas: list[tuple[Any, ...]] = []
    for i in range(n):
        cal = rng.randint(1, 5)
        sent = _sentimiento_por_calificacion(cal)
        comentario = rng.choice(COMENTARIOS[sent])
        fuente_nombre = rng.choice(fuente_nombres)
        fuente_id = fuente_map[fuente_nombre]
        prod_id = rng.choice(prod_ids)
        cli_id = rng.choice(cli_ids) if cli_ids and rng.random() > 0.05 else None
        fecha_id = rng.choice(fecha_ids)
        filas.append((
            prod_id, cli_id, fecha_id, fuente_id,
            cal, sent, comentario, f"EXT-{i + 1:05d}",
        ))

    conn.executemany(
        """INSERT INTO hechos_opiniones
           (producto_id, cliente_id, fecha_id, fuente_id,
            calificacion, sentimiento, comentario, id_externo)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
        filas,
    )
    conn.commit()
    return len(filas)


def asegurar_schema_opiniones(conn: sqlite3.Connection) -> None:
    """Ejecuta el SQL de extensión de schema (dim_fuente + hechos_opiniones)."""
    sql_text = SQL_FACTS_OPINIONES.read_text(encoding="utf-8")
    conn.executescript(sql_text)
