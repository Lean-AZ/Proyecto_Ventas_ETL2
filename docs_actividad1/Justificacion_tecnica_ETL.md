# Justificación técnica – Proceso ETL de extracción (Actividad 1)

## 1. Diagrama de arquitectura

Véase el archivo [docs/ETL_Arquitectura.md](../docs/ETL_Arquitectura.md): se identifican el Servicio ETL (Python), las fuentes (CSV, BD relacional, API REST), la base de datos de staging, la BD analítica y el lugar del dashboard como componente futuro. La arquitectura garantiza rendimiento (lotes y medición de tiempos), escalabilidad (interfaz de extractores y config en JSON), seguridad (config no versionada con secretos) y mantenibilidad (capas y patrones).

## 2. Diagrama de flujo del proceso ETL

Véase [docs/ETL_Flujo.md](../docs/ETL_Flujo.md): flujo desde la carga de configuración y logger, pasando por la extracción desde las tres fuentes, escritura en staging, transformación (mapeo y fecha_id) y carga en la BD analítica, con registro de logs y tiempos.

## 3. Justificación de decisiones técnicas

- **Python en lugar de .NET:** El proyecto se desarrolla en Python; se mantiene la misma separación de responsabilidades (extractores, staging, loader, config, logging) y la interfaz común para extractores (clase base abstracta `Extractor`).
- **SQLite para staging y analítica:** Facilita la portabilidad y la ejecución sin instalar servidores; las rutas se centralizan en `config.json`. En producción podría sustituirse por PostgreSQL o SQL Server.
- **Interfaz Extractor:** Cada fuente (CSV, BD, API) implementa el método `extract()` y devuelve una estructura común; así se pueden añadir nuevas fuentes sin modificar el orquestador.
- **Configuración en JSON:** Rutas de CSV, BD y URL de la API se centralizan en `config/config.json` (plantilla `config.json.example` en el repositorio); las credenciales sensibles no se versionan.
- **Logging estándar:** Se usa el módulo `logging` de Python (equivalente a ILogger): nivel, formato y salida a consola y opcionalmente a archivo `logs/etl.log` para monitoreo y trazabilidad.

## 4. Evidencia del código

- **Interfaz de extracción:** `etl/extractors/base.py` – clase abstracta `Extractor` con método `extract() -> dict`.
- **CsvExtractor:** `etl/extractors/csv_extractor.py` – lectura de products, customers, orders, order_details con `csv.DictReader` y validación de columnas.
- **DatabaseExtractor:** `etl/extractors/db_extractor.py` – conexión a SQLite `fuente_ventas.db` y consultas a tablas `pedidos` y `detalle_pedidos`.
- **ApiExtractor:** `etl/extractors/api_extractor.py` – peticiones GET a la API REST (productos, clientes) con `urllib.request` y normalización de la respuesta.
- **Staging:** `etl/staging.py` – definición de tablas de staging y funciones `write_to_staging` / `merge_into_staging`.
- **DataLoader:** `etl/loader.py` – lectura desde staging, relleno de `dim_fecha`, inserción en `dim_producto`, `dim_cliente` y `hechos_ventas`.
- **Orquestación:** `run_etl.py` – carga de config, creación del logger, ejecución de los tres extractores, escritura en staging y llamada al loader; registro de tiempos con `time.perf_counter()`.
- **Configuración de logging:** `etl/logger.py` – `setup_logger()` con formato, nivel y handlers de consola y archivo.

El código fuente está disponible en el repositorio GitHub del proyecto.
