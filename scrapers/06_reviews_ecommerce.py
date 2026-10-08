import asyncio
import random
import logging
import os
import json
from typing import List, Dict

import polars as pl
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

# Configuración de Logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

BRANDS = ['Hills', 'Purina Pro Plan', 'Bravecto', 'Nexgard']
OUTPUT_FILE = "data/processed/07_reviews_ecommerce.csv"

# Pausas aleatorias respetuosas
async def random_sleep(min_s=2, max_s=5):
    await asyncio.sleep(random.uniform(min_s, max_s))

async def check_for_captcha(page) -> bool:
    """Verifica si la página actual es un desafío CAPTCHA."""
    title = await page.title()
    if "robot check" in title.lower() or "captcha" in page.url.lower():
        return True
    return False

async def scrape_mercadolibre(page, brand: str) -> List[Dict[str, str]]:
    logger.info(f"[Mercado Libre] Buscando productos para: {brand}")
    results = []
    try:
        query = brand.replace(' ', '-')
        await page.goto(f"https://listado.mercadolibre.com.co/{query}", timeout=30000)
        await random_sleep(2, 4)
        
        if await check_for_captcha(page):
            raise Exception("CAPTCHA detectado en los resultados de búsqueda.")

        # Obtener los 3 primeros enlaces de productos usando un selector más genérico
        try:
            links_loc = page.locator("a.ui-search-link, a[href*='articulo.mercadolibre.com.co'], a.ui-search-item__group__element").first
            await links_loc.wait_for(timeout=10000)
            links = await page.locator("a.ui-search-link, a[href*='articulo.mercadolibre.com.co'], a.ui-search-item__group__element").evaluate_all(
                "elements => elements.map(e => e.href).slice(0, 3)"
            )
        except PlaywrightTimeoutError:
            logger.warning(f"[Mercado Libre] No se encontraron enlaces. Tomando captura de pantalla de depuración...")
            await page.screenshot(path=f"debug_ML_{brand.replace(' ', '_')}.png")
            raise Exception("Timeout esperando selectores de productos.")

        for link in links:
            try:
                await random_sleep(2, 5)
                await page.goto(link, timeout=30000)
                
                if await check_for_captcha(page):
                    logger.warning(f"[Mercado Libre] CAPTCHA al abrir producto de {brand}. Ignorando.")
                    continue
                
                # Desplazarse un poco para cargar opiniones perezosas (lazy loading)
                await page.evaluate("window.scrollBy(0, 1500)")
                await random_sleep(1, 3)

                # Intentar localizar el bloque de reseñas
                reviews = await page.locator("article.ui-pdp-reviews__comments__box").all()
                for review in reviews:
                    try:
                        text = await review.locator("p.ui-pdp-reviews__comments__content").inner_text()
                        
                        # MercadoLibre maneja estrellas visualmente (ej. width: 80% = 4 estrellas), extraemos el aria-label o asumimos base
                        # Simplificación: intentar extraer calificación del texto o dejar 'N/A'
                        calificacion = "N/A"
                        
                        if len(text.strip()) > 10:
                            results.append({
                                "fuente": "Mercado Libre",
                                "marca": brand,
                                "calificacion": calificacion,
                                "texto_opinion": text
                            })
                    except Exception:
                        continue # Ignorar si falla un comentario individual

            except Exception as e:
                logger.warning(f"[Mercado Libre] Error procesando un producto de {brand}: {e}")
                continue # Continuar con el siguiente producto

    except Exception as e:
        logger.error(f"[Mercado Libre] Error global/Bloqueo al buscar {brand}: {e}. Continuando con siguiente fuente.")
    
    return results

async def scrape_amazon(page, brand: str) -> List[Dict[str, str]]:
    logger.info(f"[Amazon] Buscando productos para: {brand}")
    results = []
    try:
        query = brand.replace(' ', '+')
        await page.goto(f"https://www.amazon.com/s?k={query}", timeout=30000)
        await random_sleep(3, 6)

        if await check_for_captcha(page):
            raise Exception("CAPTCHA detectado en la página principal.")

        try:
            links = await page.locator("a.a-link-normal.s-no-outline, a.a-link-normal.s-line-clamp-2").evaluate_all(
                "elements => elements.map(e => e.href).slice(0, 3)"
            )
            if not links:
                raise PlaywrightTimeoutError("No links found")
        except Exception:
            logger.warning(f"[Amazon] No se encontraron enlaces. Tomando captura de pantalla de depuración...")
            await page.screenshot(path=f"debug_AMZ_{brand.replace(' ', '_')}.png")
            raise Exception("Timeout esperando selectores de productos en Amazon.")

        for link in links:
            try:
                await random_sleep(3, 7)
                # Asegurar ruta absoluta si el href vino relativo
                full_url = link if link.startswith('http') else f"https://www.amazon.com{link}"
                await page.goto(full_url, timeout=30000)
                
                if await check_for_captcha(page):
                    logger.warning(f"[Amazon] CAPTCHA al abrir producto de {brand}. Ignorando.")
                    continue

                await page.evaluate("window.scrollBy(0, 2000)")
                await random_sleep(2, 4)

                reviews = await page.locator("div[data-hook='review']").all()
                for review in reviews:
                    try:
                        text = await review.locator("span[data-hook='review-body']").inner_text()
                        rating_elem = await review.locator("i[data-hook='review-star-rating']").inner_text()
                        
                        if len(text.strip()) > 10:
                            results.append({
                                "fuente": "Amazon",
                                "marca": brand,
                                "calificacion": rating_elem.split(" ")[0] if rating_elem else "N/A",
                                "texto_opinion": text
                            })
                    except Exception:
                        continue
                        
            except Exception as e:
                logger.warning(f"[Amazon] Error procesando producto de {brand}: {e}")
                continue

    except Exception as e:
        logger.error(f"[Amazon] Error global/Bloqueo al buscar {brand}: {e}. Continuando con siguiente fuente.")
        
    return results

async def scrape_laika(page, brand: str) -> List[Dict[str, str]]:
    logger.info(f"[Laika] Buscando productos para: {brand}")
    results = []
    try:
        query = brand.replace(' ', '%20')
        await page.goto(f"https://laika.com.co/search?q={query}", timeout=30000)
        await random_sleep(3, 5)

        if await check_for_captcha(page):
            raise Exception("CAPTCHA detectado en Laika.")
            
        # Selectores genéricos, dependientes de la UI de Laika
        try:
            links = await page.locator("a[href*='/product/'], a[href*='/producto/']").evaluate_all(
                "elements => elements.map(e => e.href).slice(0, 3)"
            )
            if not links:
                raise PlaywrightTimeoutError("No links found")
        except Exception:
            logger.warning(f"[Laika] No se encontraron enlaces. Tomando captura de pantalla de depuración...")
            await page.screenshot(path=f"debug_LAIKA_{brand.replace(' ', '_')}.png")
            raise Exception("Timeout esperando selectores de productos en Laika.")

        for link in links:
            try:
                await random_sleep(2, 5)
                full_url = link if link.startswith('http') else f"https://laika.com.co{link}"
                await page.goto(full_url, timeout=30000)
                
                await page.evaluate("window.scrollBy(0, 1000)")
                await random_sleep(2, 4)
                
                # Asumiendo existencia de bloque de reviews (Laika es dinámica y cambia frecuentemente)
                reviews = await page.locator(".review-item, .comment-box, [class*='review']").all()
                for review in reviews[:5]:
                    try:
                        text = await review.inner_text()
                        if len(text.strip()) > 10:
                            results.append({
                                "fuente": "Laika",
                                "marca": brand,
                                "calificacion": "N/A", # Placeholder si no hay estrellas en DOM claro
                                "texto_opinion": text
                            })
                    except Exception:
                        continue

            except Exception as e:
                logger.warning(f"[Laika] Error procesando producto de {brand}: {e}")
                continue

    except Exception as e:
        logger.error(f"[Laika] Error global/Bloqueo al buscar {brand}: {e}. Continuando con siguiente fuente.")
        
    return results

async def main_scraper():
    logger.info("Iniciando Pipeline de Extracción E-commerce con Playwright...")
    all_results = []
    
    async with async_playwright() as p:
        # Lanzar el navegador
        browser = await p.chromium.launch(headless=True)
        
        # Configurar un User-Agent estándar y cargar cookies si existen
        context_args = {
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/117.0.0.0 Safari/537.36",
            "viewport": {"width": 1920, "height": 1080},
            "locale": "es-CO",
            "timezone_id": "America/Bogota"
        }
        
        if os.path.exists("ml_state.json"):
            logger.info("Inyectando sesión autenticada (cookies de ml_state.json)...")
            try:
                with open("ml_state.json", "r", encoding="utf-8") as f:
                    state_data = json.load(f)
                # Si las cookies vienen de una extensión como lista, las adaptamos para Playwright
                if isinstance(state_data, list):
                    for c in state_data:
                        if "sameSite" in c:
                            val = c["sameSite"].lower()
                            if val in ["no_restriction", "none"]:
                                c["sameSite"] = "None"
                            elif val == "lax":
                                c["sameSite"] = "Lax"
                            elif val == "strict":
                                c["sameSite"] = "Strict"
                            else:
                                del c["sameSite"]
                    context_args["storage_state"] = {"cookies": state_data}
                else:
                    context_args["storage_state"] = state_data
            except Exception as e:
                logger.error(f"Error leyendo ml_state.json: {e}")
            
        context = await browser.new_context(**context_args)
        
        page = await context.new_page()

        for brand in BRANDS:
            all_results.extend(await scrape_mercadolibre(page, brand))
            all_results.extend(await scrape_amazon(page, brand))
            all_results.extend(await scrape_laika(page, brand))

        await browser.close()
        
    return all_results

def process_and_export(data: List[Dict[str, str]]):
    if not data:
        logger.error("No se recolectó ningún dato de los e-commerce.")
        return
        
    logger.info("Consolidando y limpiando datos con Polars...")
    
    # Crear DataFrame
    df = pl.DataFrame(data, schema={
        "fuente": pl.String,
        "marca": pl.String,
        "calificacion": pl.String,
        "texto_opinion": pl.String
    })
    
    # Limpieza de textos
    df_cleaned = df.with_columns(
        pl.col("texto_opinion")
        .str.replace_all(r"[\n\r\t]+", " ")
        .str.replace_all(r"\s{2,}", " ")
        .str.strip_chars()
    )
    
    # Remover filas vacías
    df_cleaned = df_cleaned.filter(pl.col("texto_opinion").str.len_chars() > 0)
    
    # Exportación
    os.makedirs(os.path.dirname(OUTPUT_FILE), exist_ok=True)
    df_cleaned.write_csv(OUTPUT_FILE)
    logger.info(f"Proceso finalizado. {df_cleaned.height} reseñas exportadas a {OUTPUT_FILE}.")

if __name__ == "__main__":
    # Ejecutar pipeline asíncrono y luego procesar datos
    extracted_data = asyncio.run(main_scraper())
    process_and_export(extracted_data)
