"""
API REST mock que expone productos y clientes (desde CSV).
El ApiExtractor consume esta API; en producción sería la API real de la empresa.
"""
import csv
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import JSONResponse

app = FastAPI(title="API Mock - Productos y Clientes")
BASE = Path(__file__).resolve().parent.parent
DATASET = BASE / "dataset"


def _load_productos() -> list[dict]:
    path = DATASET / "products.csv"
    if not path.exists():
        return []
    with open(path, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        return [
            {
                "id": int(r["ProductID"]),
                "nombre": r["ProductName"],
                "categoria": r["Category"],
                "precio": float(r["Price"]),
                "stock": int(r["Stock"]),
            }
            for r in reader
        ]


def _load_clientes() -> list[dict]:
    path = DATASET / "customers.csv"
    if not path.exists():
        return []
    with open(path, encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        return [
            {
                "id": int(r["CustomerID"]),
                "nombre_completo": f"{r['FirstName']} {r['LastName']}".strip(),
                "email": r["Email"],
                "telefono": r["Phone"],
                "ciudad": r["City"],
                "pais": r["Country"],
            }
            for r in reader
        ]


@app.get("/productos")
def get_productos():
    return JSONResponse(content=_load_productos())


@app.get("/clientes")
def get_clientes():
    return JSONResponse(content=_load_clientes())


@app.get("/")
def root():
    return {"message": "API Mock - usar GET /productos y GET /clientes"}
