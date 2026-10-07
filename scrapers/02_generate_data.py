import polars as pl
import numpy as np
from pathlib import Path

np.random.seed(42)
out_dir = Path("data/processed")

print("Generando datos para Juls...")

# 1. Catálogo (Resumido para el ejemplo)
skus = pl.DataFrame([
    {"marca": "Hill's", "categoria": "Pet Food", "riesgo": "Bajo"},
    {"marca": "Simparica", "categoria": "Farma", "riesgo": "Medio"},
    {"marca": "Holliday", "categoria": "Medicamentos", "riesgo": "Alto"}
])
skus.write_csv(out_dir / "01_catalogo.csv")

# 2. SOV vs Ventas
sov = pl.DataFrame([
    {"marca": "Hill's (Gabrica)", "sov_pct": 18.5, "som_pct": 26.0},
    {"marca": "Purina", "sov_pct": 42.0, "som_pct": 38.0}
])
sov.write_csv(out_dir / "02_sov_vs_som.csv")

# 3. Tickets de compra cruzada (Canasta)
tickets = pl.DataFrame({
    "ticket_id": [f"TCK-{i}" for i in range(1, 10001)],
    "compra_alimento": np.random.choice(["Si", "No"], 10000, p=[0.7, 0.3]),
    "compra_farma": np.random.choice(["Si", "No"], 10000, p=[0.4, 0.6])
})
tickets.write_csv(out_dir / "03_tickets_canasta.csv")

# 4. Veterinarios
vets = pl.DataFrame({
    "vet_id": [f"VET-{i}" for i in range(1, 801)],
    "conoce_gabrica": np.random.choice(["Si", "No"], 800, p=[0.85, 0.15]),
    "receta_por_marca": np.random.choice(["Si", "No"], 800, p=[0.7, 0.3])
})
vets.write_csv(out_dir / "04_veterinarios.csv")

print("¡Archivos listos en data/processed/!")
