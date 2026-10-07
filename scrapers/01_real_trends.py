import pandas as pd
from pytrends.request import TrendReq
from pathlib import Path
import time

out_dir = Path("data/processed")
out_dir.mkdir(parents=True, exist_ok=True)

print("Conectando a Google Trends (Colombia)...")
# tz=300 es la zona horaria de Bogotá
pytrend = TrendReq(hl='es-CO', tz=300, timeout=(10,25))

# Términos reales extraídos del ecosistema del brief
kw_list = ["Gabrica", "Purina", "Simparica", "Bravecto", "Hills"]

try:
    pytrend.build_payload(kw_list, cat=0, timeframe='today 12-m', geo='CO')
    df_trends = pytrend.interest_over_time()

    if not df_trends.empty:
        df_trends = df_trends.drop(columns=['isPartial'])
        df_trends.reset_index(inplace=True)
        # Formatear fecha para Flourish
        df_trends['date'] = df_trends['date'].dt.strftime('%Y-%m-%d')
        
        output_path = out_dir / "01_real_notoriedad_sov.csv"
        df_trends.to_csv(output_path, index=False)
        print(f"Éxito: {len(df_trends)} semanas de datos reales guardadas en {output_path}")
    else:
        print("No se encontraron datos para estos términos en Colombia.")
except Exception as e:
    print(f"Error extrayendo datos de Google: {e}")