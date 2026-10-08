import pandas as pd
from pytrends.request import TrendReq
from pathlib import Path
import time

out_dir = Path("data/processed")
out_dir.mkdir(parents=True, exist_ok=True)

print("Iniciando extracción masiva en Google Trends (Colombia)...")
pytrend = TrendReq(hl='es-CO', tz=300, timeout=(10,25))

# Agrupamos en bloques de máximo 5 (límite de Google Trends)
grupos_marcas = {
    "1_Corporativos": ["Gabrica", "Purina", "Royal Canin", "Agrocampo"],
    "2_Antiparasitarios": ["Simparica", "Bravecto", "Nexgard", "Frontline"],
    "3_Alimentos_Premium": ["Hills", "Equilibrio", "Pro Plan", "Max"],
    "4_Alimentos_Masivos": ["Chunky", "Ringo", "Dog Chow", "Guaumor"],
    "5_Farmacia_Suplementos": ["Holliday", "Vetnil", "Adaptil"]
}

dataframes = []

for nombre_grupo, marcas in grupos_marcas.items():
    print(f"Extrayendo datos de búsqueda para: {nombre_grupo} -> {marcas}")
    try:
        pytrend.build_payload(marcas, cat=0, timeframe='today 12-m', geo='CO')
        df_temp = pytrend.interest_over_time()
        
        if not df_temp.empty:
            df_temp = df_temp.drop(columns=['isPartial'])
            df_temp.reset_index(inplace=True)
            df_temp['date'] = df_temp['date'].dt.strftime('%Y-%m-%d')
            
            # Convertimos el formato para que Flourish lo lea mejor (formato "Largo")
            df_melted = df_temp.melt(id_vars=['date'], var_name='Marca', value_name='Indice_Busqueda')
            df_melted['Categoria'] = nombre_grupo.split('_', 1)[1]
            dataframes.append(df_melted)
            
        time.sleep(3)  # Pausa de 3 segundos para no bloquear la IP de Google
    except Exception as e:
        print(f"Error con el grupo {nombre_grupo}: {e}")

if dataframes:
    df_final = pd.concat(dataframes, ignore_index=True)
    output_path = out_dir / "01_real_notoriedad_completa.csv"
    df_final.to_csv(output_path, index=False)
    print(f"\n¡Éxito! {len(df_final)} registros reales consolidados en {output_path}")
else:
    print("No se logró extraer información.")