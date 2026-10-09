import polars as pl
import os

def process_financiero_flourish():
    input_path = "data/processed/09_siis_financiero_veterinarias.csv"
    output_path = "data/processed/10_flourish_financiero.csv"
    
    print(f"Cargando dataset base desde {input_path}...")
    df = pl.read_csv(input_path)
    
    # Filtrar solo 'Ingresos de actividades ordinarias'
    df_ventas = df.filter(pl.col("Cuentas") == "Ingresos de actividades ordinarias")
    
    # Pivotear para tener los años como columnas
    # Asumimos que no hay duplicados de (Marca, Año).
    df_pivot = df_ventas.pivot(
        values="Valor",
        index="Marca",
        on="Año",
        aggregate_function="first"
    )
    
    # Renombrar columnas de años para tener formato "Ventas YYYY"
    # Detectamos los años disponibles dinámicamente
    years = [col for col in df_pivot.columns if col != "Marca"]
    years.sort(key=lambda x: int(x))
    
    rename_mapping = {year: f"Ventas {year}" for year in years}
    df_pivot = df_pivot.rename(rename_mapping)
    
    # Identificar el año más reciente (actual) y el anterior
    current_year = max([int(y) for y in years])
    previous_year = current_year - 1
    
    col_current = f"Ventas {current_year}"
    col_prev = f"Ventas {previous_year}"
    
    print(f"Calculando métricas para el año actual ({current_year}) y anterior ({previous_year})...")
    
    # Ventas último año
    df_pivot = df_pivot.with_columns([
        pl.col(col_current).alias(f"Ventas último año ({current_year})")
    ])
    
    # Total mercado (suma de todas las marcas) para el año actual y anterior
    total_current = df_pivot[col_current].sum()
    total_prev = df_pivot[col_prev].sum()
    
    # Ventas competencia
    df_pivot = df_pivot.with_columns([
        (pl.lit(total_current) - pl.col(col_current)).alias(f"Ventas competencia ({current_year})")
    ])
    
    # Participación Marca (%)
    df_pivot = df_pivot.with_columns([
        (pl.col(col_current) / pl.lit(total_current)).alias("Participación Marca (%)")
    ])
    
    # Crecimiento Marca (Actual/Anterior)
    df_pivot = df_pivot.with_columns([
        ((pl.col(col_current) - pl.col(col_prev)) / pl.col(col_prev)).alias(f"Crecimiento Marca {str(current_year)[-2:]}/{str(previous_year)[-2:]} (%)")
    ])
    
    # Crecimiento Categoría (%)
    crecimiento_categoria = (total_current - total_prev) / total_prev
    df_pivot = df_pivot.with_columns([
        pl.lit(crecimiento_categoria).alias("Crecimiento Categoría (%)")
    ])
    
    # Situación Categoría
    situacion = "Creciendo" if crecimiento_categoria > 0 else "Decreciendo"
    df_pivot = df_pivot.with_columns([
        pl.lit(situacion).alias("Situación Categoría")
    ])
    
    # Ordenar las columnas de forma consistente
    year_cols = [f"Ventas {y}" for y in years]
    ordered_cols = ["Marca"] + year_cols + [
        f"Ventas último año ({current_year})",
        f"Ventas competencia ({current_year})",
        "Participación Marca (%)",
        f"Crecimiento Marca {str(current_year)[-2:]}/{str(previous_year)[-2:]} (%)",
        "Crecimiento Categoría (%)",
        "Situación Categoría"
    ]
    df_final = df_pivot.select(ordered_cols)
    
    # Guardar
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    df_final.write_csv(output_path)
    print(f"✅ ¡Éxito! Dataset 10 estructurado para Flourish guardado en {output_path}")
    print("\nVista previa de los datos:")
    print(df_final)

if __name__ == "__main__":
    process_financiero_flourish()
