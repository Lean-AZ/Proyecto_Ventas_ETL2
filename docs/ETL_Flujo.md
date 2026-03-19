# Diagrama de flujo del proceso ETL

## Flujo general

```mermaid
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

## Detalle de extracción

Cada extractor (CSV, BD, API) devuelve un diccionario con claves `productos`, `clientes`, `pedidos`, `detalles`. Los datos se consolidan en las tablas de staging; el DataLoader lee desde staging, aplica la transformación (fecha_id = YYYYMMDD, mapeo de columnas) e inserta en la BD analítica.
