import os
import time
from dotenv import load_dotenv

# Esto busca el archivo .env y carga las variables a tu entorno local
load_dotenv()
import logging
from typing import List, Dict
from dotenv import load_dotenv

import polars as pl
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# Configuración de Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

TARGET_BRANDS = ["Hills", "Purina", "Bravecto", "Nexgard"]
OUTPUT_FILE = "data/processed/05_reviews_oficiales.csv"

def fetch_youtube_reviews(brands: List[str]) -> List[Dict[str, str]]:
    logger.info("Iniciando extracción desde YouTube Data API v3...")
    # Ahora el script jala la llave de forma segura sin tenerla quemada en el código
    api_key = os.getenv("YOUTUBE_API_KEY")

    if not api_key:
        logger.warning("Credencial de YouTube (YOUTUBE_API_KEY) no encontrada. Cancelando extracción.")
        return []

    try:
        youtube = build('youtube', 'v3', developerKey=api_key, cache_discovery=False)
    except Exception as e:
        logger.error(f"Error inicializando cliente de YouTube: {e}")
        return []

    results = []
    for brand in brands:
        logger.info(f"Buscando en YouTube para la marca: {brand}")
        try:
            # 1. Buscar videos relacionados con la marca
            search_response = youtube.search().list(
                q=f"{brand} mascotas opiniones",
                part='id,snippet',
                maxResults=5,
                type='video'
            ).execute()

            video_ids = [item['id']['videoId'] for item in search_response.get('items', [])]

            # 2. Extraer comentarios de los videos encontrados
            for video_id in video_ids:
                try:
                    comments_response = youtube.commentThreads().list(
                        part='snippet',
                        videoId=video_id,
                        maxResults=20,
                        textFormat='plainText'
                    ).execute()

                    for item in comments_response.get('items', []):
                        comment = item['snippet']['topLevelComment']['snippet']['textDisplay']
                        if len(comment.strip()) > 20:
                            results.append({
                                "fuente": "YouTube",
                                "objetivo": brand,
                                "texto_opinion": comment
                            })
                except HttpError as e:
                    if e.resp.status in [403, 429]:
                        logger.warning("Rate limit o Cuota excedida en YouTube API para comentarios. Saltando al siguiente bloque...")
                        break  # Rompemos el ciclo de videos para esta marca si la cuota falló
                    else:
                        logger.error(f"Error HTTP extrayendo comentarios del video {video_id}: {e}")
                        
        except HttpError as e:
             if e.resp.status in [403, 429]:
                 logger.warning("Rate limit o Cuota de YouTube API excedida en la búsqueda. Deteniendo extracción de YouTube.")
                 break  # Detenemos la búsqueda entera si se acabó la cuota
             else:
                 logger.error(f"Error HTTP buscando {brand} en YouTube: {e}")
        except Exception as e:
            logger.error(f"Error inesperado procesando {brand} en YouTube: {e}")

    logger.info(f"Total opiniones recolectadas de YouTube: {len(results)}")
    return results

def main():
    logger.info("Iniciando Pipeline de Extracción de Reseñas (YouTube API Oficial)...")
    
    # 1. Extracción
    all_data = fetch_youtube_reviews(TARGET_BRANDS)
    
    if not all_data:
        logger.error("No se recolectó ningún dato. Verifica tus credenciales de entorno y límites de red.")
        return
        
    # 2. Procesamiento y Limpieza con Polars
    logger.info("Consolidando y limpiando datos con Polars...")
    
    # Crear DataFrame
    df = pl.DataFrame(all_data)
    
    # Limpieza de texto: forzar a string, eliminar saltos de línea, retornos de carro y múltiples espacios
    df_cleaned = df.with_columns(
        pl.col("texto_opinion")
        .cast(pl.String)
        .str.replace_all(r"[\n\r\t]+", " ")  # Reemplazar saltos y tabs por espacio
        .str.replace_all(r"\s{2,}", " ")     # Reemplazar múltiples espacios por uno solo
        .str.strip_chars()                   # Quitar espacios al inicio y final
    )
    
    # Filtrar posibles nulos o vacíos que hayan quedado post-limpieza
    df_cleaned = df_cleaned.filter(pl.col("texto_opinion").str.len_chars() > 0)
    
    # Seleccionar solo las columnas estrictamente solicitadas
    df_final = df_cleaned.select(["fuente", "objetivo", "texto_opinion"])
    
    # 3. Exportación
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    df_final.write_csv(OUTPUT_FILE)
    
    logger.info(f"Proceso finalizado. {df_final.height} registros exportados exitosamente a {OUTPUT_FILE}.")

if __name__ == "__main__":
    main()
