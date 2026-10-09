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

# Ocultar warnings internos de googleapiclient
logging.getLogger('googleapiclient.discovery_cache').setLevel(logging.ERROR)
logging.getLogger('googleapiclient.http').setLevel(logging.ERROR)

from tqdm import tqdm

TARGET_BRANDS = ["Hills", "Purina", "Bravecto", "Nexgard", "Gabrica", "Agrocampo", "Laika"]
OUTPUT_FILE = "data/processed/05_reviews_oficiales.csv"

def fetch_youtube_reviews(brands: List[str]) -> List[Dict[str, str]]:
    logger.info("Iniciando extracción profunda desde YouTube Data API v3...")
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
    
    # Variedad de consultas para profundizar más en reviews, veterinarios, etc.
    search_templates = [
        "{brand} mascotas opiniones",
        "{brand} review",
        "{brand} reseña",
        "{brand} recomendación veterinario",
        "alimento {brand} perros gatos",
        "vale la pena {brand} mascota"
    ]

    for brand in brands:
        logger.info(f"--- Buscando exhaustivamente en YouTube para la marca: {brand} ---")
        video_ids = set() # Usar set para evitar duplicados
        
        # 1. Buscar videos relacionados con la marca (múltiples enfoques)
        for template in search_templates:
            query = template.format(brand=brand)
            logger.info(f"Ejecutando consulta: '{query}'")
            try:
                search_response = youtube.search().list(
                    q=query,
                    part='id',
                    maxResults=50, # Subido de 5 a 50 (máximo por petición)
                    type='video'
                ).execute()

                for item in search_response.get('items', []):
                    if 'videoId' in item['id']:
                        video_ids.add(item['id']['videoId'])
            except HttpError as e:
                if e.resp.status in [403, 429]:
                    logger.warning("Cuota o Rate limit de YouTube API excedida en la búsqueda.")
                    break # Detener búsqueda de videos si se acaba la cuota
                else:
                    logger.error(f"Error HTTP buscando {query}: {e}")
            except Exception as e:
                logger.error(f"Error inesperado buscando {query}: {e}")

        logger.info(f"Total videos únicos encontrados para {brand}: {len(video_ids)}")

        # 2. Extraer comentarios de TODOS los videos encontrados
        for video_id in tqdm(video_ids, desc=f"Procesando videos de {brand}", unit="video", leave=False):
            try:
                next_page_token = None
                pages_fetched = 0
                max_pages_per_video = 5 # Extraer hasta 500 comentarios (5 páginas x 100) por video
                
                while pages_fetched < max_pages_per_video:
                    comments_response = youtube.commentThreads().list(
                        part='snippet',
                        videoId=video_id,
                        maxResults=100, # Subido de 20 a 100 (máximo por petición)
                        textFormat='plainText',
                        pageToken=next_page_token
                    ).execute()

                    for item in comments_response.get('items', []):
                        comment = item['snippet']['topLevelComment']['snippet']['textDisplay']
                        if len(comment.strip()) > 15: # Capturar opiniones un poco más cortas también
                            results.append({
                                "fuente": "YouTube",
                                "objetivo": brand,
                                "texto_opinion": comment
                            })
                    
                    next_page_token = comments_response.get('nextPageToken')
                    pages_fetched += 1
                    
                    if not next_page_token:
                        break # No hay más páginas de comentarios

            except HttpError as e:
                error_str = str(e).lower()
                if e.resp.status == 403 and "disabled" in error_str:
                    # Comentarios desactivados en este video, ignorar silenciosamente
                    pass
                elif e.resp.status in [403, 429]:
                    logger.warning("Cuota de YouTube API excedida extrayendo comentarios. Abortando extracción para conservar los obtenidos.")
                    return results # Retornamos lo que llevamos si la cuota global se acaba
                else:
                    # Otros errores HTTP, como video borrado o no disponible
                    pass
            except Exception as e:
                pass # Ignorar errores inesperados aislados y continuar

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
