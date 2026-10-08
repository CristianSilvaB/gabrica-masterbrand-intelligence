import polars as pl
from pathlib import Path

# Cargar el archivo crudo extraído por Antigravity
input_file = Path("data/processed/02_real_portafolio_masivo.csv")
df = pl.read_csv(input_file)

print("Limpiando datos para importación directa a Flourish...")

# 1. Convertir el precio de texto (ej. "$45.228") a número entero puro (45228)
df_clean = df.with_columns(
    pl.col("precio_publicado")
    .str.replace_all(r"[$\.\s]", "") # Elimina signo $, puntos y espacios
    .cast(pl.Int64, strict=False)
    .alias("precio_numerico")
)

# 2. Extraer automáticamente el gramaje/peso del nombre del producto usando Regex
df_clean = df_clean.with_columns(
    pl.col("producto_retail")
    .str.extract(r"(\d+(?:\.\d+)?\s*(?i)(?:kg|lb|g|mg|gr))")
    .str.to_uppercase()
    .alias("presentacion_peso")
)

# Reordenar columnas y guardar
df_final = df_clean.select(["marca_buscada", "producto_retail", "presentacion_peso", "precio_numerico"])
output_file = Path("data/processed/03_flourish_ready_precios.csv")
df_final.write_csv(output_file)

print(f"¡Listo! Archivo analítico generado en {output_file}")