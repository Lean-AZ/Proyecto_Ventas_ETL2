# Proyecto Ventas ETL

Sistema de análisis de ventas con proceso ETL en Python: modelado de BD analítica (esquema estrella) y pipeline de extracción desde CSV, BD relacional y API REST.

## Estructura

- **dataset/** – CSV de productos, clientes, pedidos y detalle de pedidos.
- **sql/** – Script de creación del schema de la BD analítica (modelo estrella).
- **etl/** – Pipeline ETL: extractores (CSV, BD, API), staging, loader y logging.
- **config/** – `config.json.example`: plantilla de configuración (copiar a `config.json` y ajustar rutas si hace falta).
- **api_mock/** – API REST mock (FastAPI) que expone productos y clientes para el ApiExtractor.
- **scripts/** – `crear_fuente_ventas_db.py`: crea la BD “externa” simulada desde los CSV.
- **docs/** – Diagramas y documentación (DER, decisiones de diseño, arquitectura ETL, flujo ETL).

## Requisitos

- Python 3.10+
- Para la API mock: `pip install -r api_mock/requirements_api.txt`

## Uso rápido

### 1. Crear la BD analítica (solo schema y dim_fecha, sin ETL)

```bash
python create_db_ventas.py
```

Esto crea `data/ventas_analitica.db` y opcionalmente carga productos, clientes y hechos desde los CSV (si se mantiene la lógica actual en `create_db_ventas.py`).

### 2. Ejecutar el pipeline ETL completo (Actividad 1)

1. **Configuración:** Copiar `config/config.json.example` a `config/config.json` (o dejar la plantilla; las rutas son relativas al proyecto).

2. **BD externa simulada (para DatabaseExtractor):**
   ```bash
   python scripts/crear_fuente_ventas_db.py
   ```
   Genera `data/fuente_ventas.db` con tablas `pedidos` y `detalle_pedidos`.

3. **API mock (opcional, para ApiExtractor):** En otra terminal:
   ```bash
   cd api_mock && pip install -r requirements_api.txt && uvicorn main:app --reload --host 127.0.0.1 --port 8000
   ```

4. **Ejecutar ETL:**
   ```bash
   python run_etl.py
   ```
   - Extrae desde CSV, BD relacional y API (si la API está en marcha).
   - Escribe en `data/staging.db`.
   - Carga en `data/ventas_analitica.db`.
   - Los logs se muestran en consola y, si está configurado, en `logs/etl.log`.

Si la API mock no está activa, el ApiExtractor registrará un aviso y seguirá con CSV y BD.

## Entregables (Actividad 1)

- **Código:** Este repositorio (Worker Service equivalente en Python: `run_etl.py` + módulos en `etl/`).
- **Diagrama de arquitectura:** `docs/ETL_Arquitectura.md` (Mermaid + texto).
- **Documento técnico:** Contenido para Word/PDF en `docs_actividad1/Justificacion_tecnica_ETL.md` (diagramas, justificación y evidencia de código).

## Repositorio

https://github.com/Lean-AZ/Proyecto_Ventas_ETL2
