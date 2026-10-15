import argparse
import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional

import html
from dotenv import load_dotenv
import polars as pl

# Cargar variables de entorno
load_dotenv()

# Configuración de Logging profesional
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(levelname)s] - %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("ApifyMultiChannelScraper")

# Configuración y Constantes
DEFAULT_TARGET_BRANDS = ["Hills", "Purina", "Bravecto", "Nexgard", "Gabrica", "Agrocampo", "Laika"]
OUTPUT_FILE = Path("data/processed/11_reviews_multicanal.csv")

# Mapeo de Actores recomendados y verificados en Apify
ACTORS = {
    "mercadolibre": "sourabhbgp/mercadolibre-scraper",
    "amazon": "junglee/amazon-reviews-scraper",
    "tiktok": "clockworks/tiktok-comments-scraper",
    "facebook": "apify/facebook-posts-scraper",
    "instagram": "apify/instagram-scraper",
    "reddit": "trudax/reddit-scraper-lite",
}

def get_dataset_id(run) -> Optional[str]:
    """Extrae el ID del dataset de manera segura según el objeto o diccionario de retorno de Apify."""
    if run is None:
        return None
    if isinstance(run, dict):
        return run.get("defaultDatasetId")
    return getattr(run, "default_dataset_id", None) or getattr(run, "defaultDatasetId", None)

def get_apify_client():
    """Valida y retorna la instancia del cliente Apify."""
    api_token = os.getenv("APIFY_API_TOKEN")
    if not api_token or api_token.strip() == "" or "tu_token" in api_token:
        logger.error(
            "❌ Token de Apify no configurado.\n"
            "Asegúrate de agregar APIFY_API_TOKEN=\"tu_token\" en tu archivo .env local."
        )
        sys.exit(1)
        
    try:
        from apify_client import ApifyClient
        client = ApifyClient(api_token)
        return client
    except ImportError:
        logger.error("❌ 'apify-client' no está instalado. Ejecuta: pip install apify-client")
        sys.exit(1)


# =====================================================================
# HANDLERS POR PLATAFORMA
# =====================================================================

def scrape_mercadolibre(client, brands: List[str], max_items: int, direct_urls: Optional[List[str]] = None, dry_run: bool = False) -> List[Dict[str, str]]:
    """Extrae opiniones y reseñas reales de compradores en Mercado Libre Colombia."""
    actor_id = ACTORS["mercadolibre"]
    logger.info(f"🛒 Iniciando extracción en Mercado Libre Colombia (Actor: {actor_id})...")
    results = []

    for brand in brands:
        if direct_urls:
            product_urls = direct_urls
        else:
            num_products = min(25, max(5, max_items // 10))
            search_input = {
                "mode": "search",
                "country": "CO",
                "searchQuery": f"{brand} perros gatos mascotas",
                "maxItems": num_products
            }
            if dry_run:
                logger.info(f"[DRY-RUN] Mercado Libre -> Búsqueda para '{brand}' ({num_products} productos) | Input: {json.dumps(search_input)}")
                continue

            try:
                logger.info(f"Buscando top {num_products} productos de '{brand}' en Mercado Libre Colombia...")
                search_run = client.actor(actor_id).call(run_input=search_input)
                s_dataset_id = get_dataset_id(search_run)
                product_urls = []
                if s_dataset_id:
                    for item in client.dataset(s_dataset_id).iterate_items():
                        u = item.get("listingUrl") or item.get("url")
                        if u:
                            product_urls.append(u)
            except Exception as e:
                logger.error(f"Error buscando productos de Mercado Libre para '{brand}': {e}")
                product_urls = []

        if dry_run:
            continue

        if not product_urls:
            logger.warning(f"No se obtuvieron URLs de productos para '{brand}' en Mercado Libre.")
            continue

        reviews_input = {
            "mode": "reviews",
            "startUrls": [{"url": u} for u in product_urls],
            "maxItems": max_items
        }

        try:
            logger.info(f"Extrayendo reseñas de compradores para '{brand}' ({len(product_urls)} productos objetivo)...")
            reviews_run = client.actor(actor_id).call(run_input=reviews_input)
            r_dataset_id = get_dataset_id(reviews_run)
            count = 0
            if r_dataset_id:
                for item in client.dataset(r_dataset_id).iterate_items():
                    texto = item.get("reviewText") or item.get("reviewTitle") or item.get("comment") or ""
                    if texto and len(str(texto).strip()) >= 15:
                        results.append({
                            "fuente": "MercadoLibre",
                            "objetivo": brand,
                            "texto_opinion": str(texto).strip()
                        })
                        count += 1
            logger.info(f"Mercado Libre: {count} reseñas reales capturadas para '{brand}'.")
        except Exception as e:
            logger.error(f"Error extrayendo reseñas en Mercado Libre para '{brand}': {e}")

    return results


def scrape_amazon(client, brands: List[str], max_items: int, direct_urls: Optional[List[str]] = None, dry_run: bool = False) -> List[Dict[str, str]]:
    """Extrae reseñas de Amazon de productos líderes."""
    actor_id = ACTORS["amazon"]
    logger.info(f"📦 Iniciando extracción en Amazon (Actor: {actor_id})...")
    results = []

    amazon_asins = {
        "Hills": "https://www.amazon.com/dp/B003M5Z852",
        "Purina": "https://www.amazon.com/dp/B002FY268U",
        "Bravecto": "https://www.amazon.com/dp/B0002AQN9Q",
        "Nexgard": "https://www.amazon.com/dp/B0002AQN9Q",
    }

    for brand in brands:
        target_url = amazon_asins.get(brand, "https://www.amazon.com/dp/B003M5Z852")
        urls_to_crawl = direct_urls if direct_urls else [{"url": target_url}]
        
        run_input = {
            "productUrls": urls_to_crawl,
            "maxReviews": max_items,
            "sort": "recent"
        }
        
        if dry_run:
            logger.info(f"[DRY-RUN] Amazon -> Marca '{brand}' | Input: {json.dumps(run_input)}")
            continue

        try:
            logger.info(f"Ejecutando Actor de Amazon para: '{brand}'...")
            run = client.actor(actor_id).call(run_input=run_input)
            dataset_id = get_dataset_id(run)
            
            count = 0
            if dataset_id:
                for item in client.dataset(dataset_id).iterate_items():
                    review_text = item.get("reviewText") or item.get("reviewDescription") or item.get("text") or ""
                    review_title = item.get("reviewTitle") or ""
                    combined = f"{review_title}. {review_text}".strip(" .")
                    cleaned_review = html.unescape(combined).strip()
                    
                    if cleaned_review and len(cleaned_review) >= 15:
                        results.append({
                            "fuente": "Amazon",
                            "objetivo": brand,
                            "texto_opinion": cleaned_review
                        })
                        count += 1

            logger.info(f"Amazon: {count} reseñas capturadas para '{brand}'.")
        except Exception as e:
            logger.error(f"Error extrayendo de Amazon para '{brand}': {e}")

    return results


def scrape_tiktok(client, brands: List[str], max_items: int, direct_urls: Optional[List[str]] = None, dry_run: bool = False) -> List[Dict[str, str]]:
    """Extrae comentarios de TikTok sobre marcas o videos relevantes."""
    actor_id = ACTORS["tiktok"]
    logger.info(f"🎵 Iniciando extracción en TikTok (Actor: {actor_id})...")
    results = []

    for brand in brands:
        if direct_urls:
            run_input = {
                "postURLs": direct_urls,
                "commentsPerPost": max_items,
                "maxRepliesPerComment": 1
            }
        else:
            run_input = {
                "profiles": ["agrocampocolombia", "laika_mascotas"],
                "commentsPerPost": max_items,
                "maxRepliesPerComment": 1,
                "resultsPerPage": 2
            }
        
        if dry_run:
            logger.info(f"[DRY-RUN] TikTok -> Marca '{brand}' | Input: {json.dumps(run_input)}")
            continue

        try:
            logger.info(f"Ejecutando Actor de TikTok para '{brand}'...")
            run = client.actor(actor_id).call(run_input=run_input)
            dataset_id = get_dataset_id(run)
            
            count = 0
            if dataset_id:
                for item in client.dataset(dataset_id).iterate_items():
                    comment = item.get("text") or item.get("comment") or ""
                    cleaned_comment = html.unescape(str(comment)).strip()
                    if cleaned_comment and len(cleaned_comment) >= 15:
                        results.append({
                            "fuente": "TikTok",
                            "objetivo": brand,
                            "texto_opinion": cleaned_comment
                        })
                        count += 1

            logger.info(f"TikTok: {count} comentarios capturados para '{brand}'.")
        except Exception as e:
            logger.error(f"Error extrayendo de TikTok para '{brand}': {e}")

    return results


def scrape_facebook(client, brands: List[str], max_items: int, direct_urls: Optional[List[str]] = None, dry_run: bool = False) -> List[Dict[str, str]]:
    """Extrae opiniones y publicaciones públicas en Facebook."""
    actor_id = ACTORS["facebook"]
    logger.info(f"👥 Iniciando extracción en Facebook (Actor: {actor_id})...")
    results = []

    for brand in brands:
        start_urls = [{"url": u} for u in direct_urls] if direct_urls else [
            {"url": "https://www.facebook.com/AgrocampoColombia/"}
        ]
        
        run_input = {
            "startUrls": start_urls,
            "resultsLimit": max_items
        }

        if dry_run:
            logger.info(f"[DRY-RUN] Facebook -> Marca '{brand}' | Input: {json.dumps(run_input)}")
            continue

        try:
            logger.info(f"Ejecutando Actor de Facebook para '{brand}'...")
            run = client.actor(actor_id).call(run_input=run_input)
            dataset_id = get_dataset_id(run)
            
            count = 0
            if dataset_id:
                for item in client.dataset(dataset_id).iterate_items():
                    comment = item.get("text") or item.get("postText") or item.get("caption") or ""
                    cleaned_comment = html.unescape(str(comment)).strip()
                    if cleaned_comment and len(cleaned_comment) >= 15:
                        results.append({
                            "fuente": "Facebook",
                            "objetivo": brand,
                            "texto_opinion": cleaned_comment
                        })
                        count += 1

            logger.info(f"Facebook: {count} opiniones capturadas para '{brand}'.")
        except Exception as e:
            logger.error(f"Error extrayendo de Facebook para '{brand}': {e}")

    return results


def scrape_instagram(client, brands: List[str], max_items: int, direct_urls: Optional[List[str]] = None, dry_run: bool = False) -> List[Dict[str, str]]:
    """Extrae comentarios y publicaciones en Instagram."""
    actor_id = ACTORS["instagram"]
    logger.info(f"📷 Iniciando extracción en Instagram (Actor: {actor_id})...")
    results = []

    for brand in brands:
        direct_urls_list = direct_urls if direct_urls else [
            "https://www.instagram.com/agrocampoco/",
            "https://www.instagram.com/laikacolombia/"
        ]
        
        run_input = {
            "resultsType": "posts",
            "directUrls": direct_urls_list,
            "resultsLimit": max_items
        }

        if dry_run:
            logger.info(f"[DRY-RUN] Instagram -> Marca '{brand}' | Input: {json.dumps(run_input)}")
            continue

        try:
            logger.info(f"Ejecutando Actor de Instagram para '{brand}'...")
            run = client.actor(actor_id).call(run_input=run_input)
            dataset_id = get_dataset_id(run)
            
            count = 0
            if dataset_id:
                for item in client.dataset(dataset_id).iterate_items():
                    comment = item.get("caption") or item.get("text") or ""
                    cleaned_comment = html.unescape(str(comment)).strip()
                    if cleaned_comment and len(cleaned_comment) >= 15:
                        results.append({
                            "fuente": "Instagram",
                            "objetivo": brand,
                            "texto_opinion": cleaned_comment
                        })
                        count += 1

            logger.info(f"Instagram: {count} publicaciones/comentarios capturados para '{brand}'.")
        except Exception as e:
            logger.error(f"Error extrayendo de Instagram para '{brand}': {e}")

    return results


def scrape_reddit(client, brands: List[str], max_items: int, direct_urls: Optional[List[str]] = None, dry_run: bool = False) -> List[Dict[str, str]]:
    """Extrae discusiones y comentarios de Reddit sobre las marcas."""
    actor_id = ACTORS["reddit"]
    logger.info(f"🤖 Iniciando extracción en Reddit (Actor: {actor_id})...")
    results = []

    for brand in brands:
        searches = [
            f"{brand} perro gato opiniones",
            f"{brand} alimento veterinaria"
        ]
        
        run_input = {
            "searches": searches,
            "sort": "relevance",
            "maxItems": max_items,
            "maxPostCount": max_items,
            "maxComments": max_items
        }

        if dry_run:
            logger.info(f"[DRY-RUN] Reddit -> Marca '{brand}' | Input: {json.dumps(run_input)}")
            continue

        try:
            logger.info(f"Ejecutando Actor de Reddit para '{brand}'...")
            run = client.actor(actor_id).call(run_input=run_input)
            dataset_id = get_dataset_id(run)
            
            count = 0
            if dataset_id:
                for item in client.dataset(dataset_id).iterate_items():
                    body = item.get("body") or item.get("selftext") or item.get("title") or ""
                    cleaned_body = html.unescape(str(body)).strip()
                    if cleaned_body and len(cleaned_body) >= 15:
                        results.append({
                            "fuente": "Reddit",
                            "objetivo": brand,
                            "texto_opinion": cleaned_body
                        })
                        count += 1

            logger.info(f"Reddit: {count} opiniones/comentarios capturados para '{brand}'.")
        except Exception as e:
            logger.error(f"Error extrayendo de Reddit para '{brand}': {e}")

    return results


# =====================================================================
# PIPELINE DE CONSOLIDACIÓN Y LIMPIEZA CON POLARS
# =====================================================================

def process_and_save_reviews(raw_data: List[Dict[str, str]]) -> pl.DataFrame:
    """Limpia y consolida las opiniones en el esquema exacto de YouTube."""
    if not raw_data:
        logger.warning("No se recolectaron nuevas opiniones en esta ejecución.")
        if OUTPUT_FILE.exists():
            return pl.read_csv(OUTPUT_FILE)
        return pl.DataFrame(schema={"fuente": pl.String, "objetivo": pl.String, "texto_opinion": pl.String})

    logger.info(f"Procesando y normalizando {len(raw_data)} opiniones con Polars...")
    df_new = pl.DataFrame(raw_data)

    # Limpieza idéntica a 05_reviews_oficiales.py
    df_cleaned = df_new.with_columns(
        pl.col("texto_opinion")
        .cast(pl.String)
        .str.replace_all(r"[\n\r\t]+", " ")   # Eliminar saltos de línea y tabuladores
        .str.replace_all(r"\s{2,}", " ")      # Eliminar dobles espacios
        .str.strip_chars()                    # Quitar espacios en los bordes
    ).filter(
        (pl.col("texto_opinion").str.len_chars() >= 15) &
        (pl.col("texto_opinion").is_not_null())
    ).select(["fuente", "objetivo", "texto_opinion"])

    # Idempotencia: si ya existe el CSV, anexar y deduplicar
    if OUTPUT_FILE.exists():
        logger.info(f"Anexando datos al archivo existente: {OUTPUT_FILE}")
        df_existing = pl.read_csv(OUTPUT_FILE)
        df_consolidated = pl.concat([df_existing, df_cleaned]).unique(
            subset=["fuente", "objetivo", "texto_opinion"]
        )
    else:
        df_consolidated = df_cleaned.unique(
            subset=["fuente", "objetivo", "texto_opinion"]
        )

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    df_consolidated.write_csv(OUTPUT_FILE)
    logger.info(f"✅ ¡Éxito! Archivo guardado con {df_consolidated.height} opiniones únicas en: {OUTPUT_FILE}")

    # Resumen analítico por plataforma y marca
    print("\n" + "=" * 60)
    print("📊 RESUMEN DE OPINIONES MULTICANAL POR FUENTE Y OBJETIVO")
    print("=" * 60)
    resumen = df_consolidated.group_by(["fuente", "objetivo"]).len().sort(["fuente", "objetivo"])
    print(resumen)
    print("=" * 60 + "\n")

    return df_consolidated


# =====================================================================
# CLI RUNNER PRINCIPAL
# =====================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Scraper Multicanal de Reseñas y Opiniones con Apify para Gabrica Intelligence."
    )
    parser.add_argument(
        "--plataformas",
        type=str,
        default="mercadolibre,reddit",
        help="Plataformas separadas por coma ('mercadolibre', 'amazon', 'tiktok', 'facebook', 'instagram', 'reddit') o 'all'."
    )
    parser.add_argument(
        "--marcas",
        type=str,
        default=",".join(DEFAULT_TARGET_BRANDS),
        help="Marcas objetivo separadas por comas."
    )
    parser.add_argument(
        "--max-items",
        type=int,
        default=25,
        help="Límite máximo de elementos o comentarios a extraer por marca/consulta (control de créditos)."
    )
    parser.add_argument(
        "--urls-file",
        type=str,
        default=None,
        help="Ruta opcional a un archivo JSON con URLs directas a auditar."
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Simula la ejecución mostrando los payloads a enviar a Apify sin gastar créditos."
    )

    args = parser.parse_args()

    # Procesar plataformas solicitadas
    available_handlers = {
        "mercadolibre": scrape_mercadolibre,
        "amazon": scrape_amazon,
        "tiktok": scrape_tiktok,
        "facebook": scrape_facebook,
        "instagram": scrape_instagram,
        "reddit": scrape_reddit,
    }

    if args.plataformas.strip().lower() == "all":
        selected_platforms = list(available_handlers.keys())
    else:
        selected_platforms = [p.strip().lower() for p in args.plataformas.split(",") if p.strip().lower() in available_handlers]

    if not selected_platforms:
        logger.error(f"Ninguna plataforma válida seleccionada. Opciones disponibles: {list(available_handlers.keys())}")
        sys.exit(1)

    brands = [b.strip() for b in args.marcas.split(",") if b.strip()]
    logger.info(f"Marcas objetivo ({len(brands)}): {brands}")
    logger.info(f"Plataformas activas ({len(selected_platforms)}): {selected_platforms}")
    logger.info(f"Límite por consulta: {args.max_items} | Modo Dry-Run: {args.dry_run}")

    # Cargar URLs directas si existen
    direct_urls = None
    if args.urls_file:
        urls_path = Path(args.urls_file)
        if urls_path.exists():
            with open(urls_path, "r", encoding="utf-8") as f:
                direct_urls = json.load(f)
            logger.info(f"Cargadas URLs directas desde {urls_path}")

    # Obtener cliente de Apify
    client = get_apify_client()

    # Ejecutar scrapers
    all_extracted_data: List[Dict[str, str]] = []
    for platform in selected_platforms:
        handler = available_handlers[platform]
        try:
            data = handler(client, brands, args.max_items, direct_urls, dry_run=args.dry_run)
            all_extracted_data.extend(data)
        except Exception as e:
            logger.error(f"Error procesando plataforma {platform}: {e}")

    # Consolidar y exportar con Polars
    if not args.dry_run:
        process_and_save_reviews(all_extracted_data)
    else:
        logger.info("[DRY-RUN COMPLETADO] No se guardaron archivos en disco ni se consumieron créditos.")


if __name__ == "__main__":
    main()
