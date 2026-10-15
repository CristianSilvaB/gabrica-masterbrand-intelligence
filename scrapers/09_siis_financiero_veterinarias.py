import polars as pl
from pathlib import Path

def consolidar_financiero_siis():
    raw_excel_path = Path("data/raw/Datos_Consolidados_Marcas_Siid.xlsx")
    raw_er_path = Path("data/raw/09_estado_resultados_siis.csv")
    output_path = Path("data/processed/09_siis_financiero_veterinarias.csv")

    output_path.parent.mkdir(parents=True, exist_ok=True)
    frames_to_concat = []

    # 1. Cargar y des-pivotear el Estado de Situación Financiera (Balance General)
    if raw_excel_path.exists():
        print(f"📖 Cargando datos de balance desde {raw_excel_path}...")
        df_excel = pl.read_excel(raw_excel_path, engine="openpyxl")
        
        year_cols = [c for c in df_excel.columns if c in ["2022", "2023", "2024", "2025"]]
        df_unpivot = df_excel.unpivot(
            index=["Marca", "NIT", "Cuentas"],
            on=year_cols,
            variable_name="Año",
            value_name="Valor"
        )
        
        df_balance = df_unpivot.with_columns([
            (pl.col("Año") + "-12-31").alias("Fecha"),
            pl.col("Año").cast(pl.Int64),
            pl.col("NIT").cast(pl.Int64),
            pl.col("Valor").cast(pl.Int64, strict=False)
        ]).select(["Cuentas", "Fecha", "Valor", "Año", "NIT", "Marca"])
        
        print(f"  -> {len(df_balance)} filas de Balance General normalizadas.")
        frames_to_concat.append(df_balance)
    else:
        print(f"⚠️ Archivo no encontrado: {raw_excel_path}")

    # 2. Cargar el Estado de Resultados (Ingresos, Costos, Ganancias)
    if raw_er_path.exists():
        print(f"📖 Cargando datos de Estado de Resultados desde {raw_er_path}...")
        df_er = pl.read_csv(raw_er_path)
        df_er = df_er.with_columns([
            pl.col("Año").cast(pl.Int64),
            pl.col("NIT").cast(pl.Int64),
            pl.col("Valor").cast(pl.Int64, strict=False)
        ]).select(["Cuentas", "Fecha", "Valor", "Año", "NIT", "Marca"])
        
        print(f"  -> {len(df_er)} filas de Estado de Resultados cargadas.")
        frames_to_concat.append(df_er)
    else:
        print(f"ℹ️ No se encontró {raw_er_path}, omitiendo.")

    if not frames_to_concat:
        raise FileNotFoundError("No se encontraron fuentes de datos para consolidar.")

    # 3. Concatenar y deduplicar por clave primaria contable (Marca, Cuentas, Año)
    df_consolidado = pl.concat(frames_to_concat)
    df_consolidado = df_consolidado.unique(subset=["Marca", "Cuentas", "Año"], keep="last")

    # 4. Ordenar para consistencia analítica
    df_consolidado = df_consolidado.sort(["Marca", "Cuentas", "Año"])

    # 5. Guardar en data/processed/09_siis_financiero_veterinarias.csv
    df_consolidado.write_csv(output_path)
    print(f"\n✅ ¡Éxito! Dataset 09 guardado en {output_path}")
    print(f"Total registros consolidados: {len(df_consolidado)}")
    
    # Resumen por marca
    resumen = df_consolidado.group_by("Marca").len().sort("len", descending=True)
    print("\nDesglose de registros por marca:")
    for row in resumen.iter_rows(named=True):
        print(f"  - {row['Marca']}: {row['len']} filas")

if __name__ == "__main__":
    consolidar_financiero_siis()
