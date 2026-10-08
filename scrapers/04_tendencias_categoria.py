import pandas as pd
from pytrends.request import TrendReq
from pathlib import Path
import time

out_dir = Path("data/processed")
out_dir.mkdir(parents=True, exist_ok=True)

print("Extrayendo macro-tendencias del mercado (Últimos 5 años)...")
pytrend = TrendReq(hl='es-CO', tz=300, timeout=(15,25))

# Palabras clave genéricas del sector en Colombia
kw_list = ["comida para perros", "veterinaria", "desparasitante", "pet shop", "dieta barf"]

try:
    # timeframe='today 5-y' saca los últimos 5 años exactos
    pytrend.build_payload(kw_list, cat=0, timeframe='today 5-y', geo='CO')
    df_trends = pytrend.interest_over_time()

    if not df_trends.empty:
        df_trends = df_trends.drop(columns=['isPartial'])
        df_trends.reset_index(inplace=True)
        df_trends['date'] = df_trends['date'].dt.strftime('%Y-%m-%d')
        
        output_path = out_dir / "04_tendencias_categoria_5años.csv"
        df_trends.to_csv(output_path, index=False)
        print(f"¡Éxito! {len(df_trends)} meses de histórico de mercado guardados en {output_path}")
    else:
        print("No se encontraron datos.")
except Exception as e:
    print(f"Error extrayendo datos: {e}")