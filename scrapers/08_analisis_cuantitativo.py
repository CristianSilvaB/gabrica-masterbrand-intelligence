import polars as pl
from pysentimiento import create_analyzer
from pathlib import Path

# Cargar el modelo pre-entrenado en español
print("Cargando modelo NLP en español...")
analyzer = create_analyzer(task="sentiment", lang="es")

# Función para extraer la etiqueta (POS, NEG, NEU)
def evaluar_sentimiento(texto):
    try:
        resultado = analyzer.predict(texto)
        return resultado.output
    except:
        return "NEU"

# Cargar el dataset de YouTube
archivo_entrada = Path("data/processed/05_reviews_oficiales.csv")
df = pl.read_csv(archivo_entrada)

print(f"Evaluando {len(df)} reseñas. Esto tomará unos segundos...")

# Aplicar el modelo a la columna de texto y crear una nueva columna
df_cuantitativo = df.with_columns(
    pl.col("texto_opinion").map_elements(evaluar_sentimiento, return_dtype=pl.Utf8).alias("polaridad_sentimiento")
)

# Exportar el resultado final para Juls
archivo_salida = Path("data/processed/05_reviews_cuantitativo.csv")
df_cuantitativo.write_csv(archivo_salida)

print("¡Proceso completado! Resumen de métricas:")
print(df_cuantitativo.group_by(["objetivo", "polaridad_sentimiento"]).len().sort(["objetivo", "polaridad_sentimiento"]))