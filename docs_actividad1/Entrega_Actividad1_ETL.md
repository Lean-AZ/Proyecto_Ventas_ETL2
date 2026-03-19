# Actividad 1 – Desarrollo del Proceso ETL (Extracción)
## Documento técnico – Sistema de Análisis de Ventas

**Entrega:** Código en GitHub + Diagrama de arquitectura + Justificación técnica

---

## Portada

- **Actividad:** Actividad 1 – Creación de la arquitectura y desarrollo del proceso de extracción (ETL).
- **Proyecto:** Sistema de Análisis de Ventas (implementación en Python).
- **Fecha:** [Completar]
- **Repositorio:** https://github.com/Lean-AZ/Proyecto_Ventas_ETL2

---

## 1. Diagrama de arquitectura

La arquitectura del proceso ETL incluye:

- **Servicio ETL (Python):** Pipeline orquestado por `run_etl.py`: extracción desde CSV, BD relacional y API REST; escritura en staging; carga en BD analítica.
- **Fuentes de datos:** CSV (dataset/), base de datos relacional (`fuente_ventas.db`), API REST (mock en FastAPI).
- **Staging:** Base de datos SQLite `data/staging.db` con tablas staging_productos, staging_clientes, staging_pedidos, staging_detalles.
- **Base de datos analítica:** SQLite `data/ventas_analitica.db` (modelo estrella: dim_producto, dim_cliente, dim_fecha, hechos_ventas).
- **Dashboard / visualización:** Componente futuro; no implementado en esta actividad.

### Diagrama (exportar desde Mermaid)

Para obtener la imagen del diagrama: copiar el siguiente código en https://mermaid.live y exportar como PNG; luego insertar la imagen en este documento.

```
flowchart LR
    subgraph fuentes [Fuentes de datos]
        CSV[CSV]
        BD[BD relacional]
        API[API REST]
    end
    subgraph etl [Servicio ETL]
        E[Extractores]
        S[Staging]
        L[DataLoader]
    end
    subgraph destino [Destino]
        DW[BD analítica]
    end
    CSV --> E
    BD --> E
    API --> E
    E --> S
    S --> L
    L --> DW
```

### Atributos de calidad

| Atributo        | Cómo se garantiza |
|-----------------|--------------------|
| **Rendimiento** | Procesamiento por lotes en staging y loader; logging con tiempos de ejecución (time.perf_counter()). |
| **Escalabilidad** | Nuevas fuentes = nuevo extractor que implementa la interfaz Extractor; configuración en config.json. |
| **Seguridad**   | Rutas y URL en config.json; config.json con datos sensibles no se sube a GitHub (solo config.json.example). |
| **Mantenibilidad** | Capas separadas: extractors (base, csv, db, api), staging, loader, config, logging; interfaz común para extractores. |

---

## 2. Diagrama de flujo del proceso ETL

Flujo: Cargar config y logger → Extracción CSV → Extracción BD relacional → Extracción API REST → Escribir en staging → DataLoader lee staging → Transformar (mapeo y fecha_id) → Cargar en BD analítica → Registrar logs y tiempos → Fin.

### Código Mermaid para exportar a imagen

Copiar en https://mermaid.live y exportar como PNG; insertar la imagen en el documento.

```
flowchart TD
    A[Inicio] --> B[Cargar config y logger]
    B --> C[Extracción CSV]
    C --> D[Extracción BD relacional]
    D --> E[Extracción API REST]
    E --> F[Escribir en staging]
    F --> G[DataLoader: leer staging]
    G --> H[Transformar: mapeo y fecha_id]
    H --> I[Cargar en BD analítica]
    I --> J[Registrar logs y tiempos]
    J --> K[Fin]
```

---

## 3. Justificación de decisiones técnicas

- **Python en lugar de .NET:** El proyecto se desarrolla en Python; se mantiene la misma separación de responsabilidades (extractores, staging, loader, config, logging) y la interfaz común para extractores (clase base abstracta Extractor).
- **SQLite para staging y analítica:** Facilita la portabilidad y la ejecución sin instalar servidores; las rutas se centralizan en config.json. En producción podría sustituirse por PostgreSQL o SQL Server.
- **Interfaz Extractor:** Cada fuente (CSV, BD, API) implementa el método extract() y devuelve una estructura común; así se pueden añadir nuevas fuentes sin modificar el orquestador.
- **Configuración en JSON:** Rutas de CSV, BD y URL de la API se centralizan en config/config.json (plantilla config.json.example en el repositorio); las credenciales sensibles no se versionan.
- **Logging estándar:** Se usa el módulo logging de Python (equivalente a ILogger): nivel, formato y salida a consola y opcionalmente a archivo logs/etl.log para monitoreo y trazabilidad.

---

## 4. Evidencia del código

- **Interfaz de extracción:** etl/extractors/base.py – clase abstracta Extractor con método extract() que devuelve un diccionario con claves normalizadas para staging.
- **CsvExtractor:** etl/extractors/csv_extractor.py – lectura de products, customers, orders, order_details con csv.DictReader y validación de columnas.
- **DatabaseExtractor:** etl/extractors/db_extractor.py – conexión a SQLite fuente_ventas.db y consultas a tablas pedidos y detalle_pedidos.
- **ApiExtractor:** etl/extractors/api_extractor.py – peticiones GET a la API REST (productos, clientes) con urllib.request y normalización de la respuesta.
- **Staging:** etl/staging.py – definición de tablas de staging y funciones write_to_staging / merge_into_staging.
- **DataLoader:** etl/loader.py – lectura desde staging, relleno de dim_fecha, inserción en dim_producto, dim_cliente y hechos_ventas.
- **Orquestación:** run_etl.py – carga de config, creación del logger, ejecución de los tres extractores, escritura en staging y llamada al loader; registro de tiempos con time.perf_counter().
- **Configuración de logging:** etl/logger.py – setup_logger() con formato, nivel y handlers de consola y archivo.

El código fuente completo está disponible en el repositorio GitHub del proyecto.

---

## 5. Repositorio

**Repositorio del proyecto:** https://github.com/Lean-AZ/Proyecto_Ventas_ETL2
