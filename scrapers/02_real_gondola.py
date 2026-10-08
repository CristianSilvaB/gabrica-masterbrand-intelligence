import cloudscraper
from bs4 import BeautifulSoup
import polars as pl
from pathlib import Path
import time
import re

out_dir = Path("data/processed")
out_dir.mkdir(parents=True, exist_ok=True)

# Marcas objetivo según requerimiento
marcas_auditoria = [
    "Hills", "Equilibrio", "Max", "Simparica",
    "Bravecto", "Nexgard", "Purina", "Royal Canin"
]

print("=" * 60)
print("INICIANDO EXTRACCIÓN CON TÁCTICAS DE EVASIÓN AVANZADAS (WAF/Cloudflare)")
print("=" * 60)

# Inicializar scraper avanzado anti-bot / Cloudflare
scraper = cloudscraper.create_scraper(
    browser={
        'browser': 'chrome',
        'platform': 'windows',
        'desktop': True
    }
)

headers = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8",
    "Accept-Language": "es-CO,es;q=0.9,en;q=0.8",
}

resultados = []

def extraer_mercadolibre(marca):
    """Intenta extraer productos de Mercado Libre con tácticas de evasión."""
    url = f"https://listado.mercadolibre.com.co/animales-mascotas/{marca}"
    try:
        response = scraper.get(url, headers=headers, timeout=15)
        if response.status_code == 200:
            # Comprobar si retornó pantalla de bloqueo / challenge
            if "suspicious-traffic" in response.text or "account-verification" in response.text:
                print(f" [Mercado Libre] Desafío anti-bot / WAF detectado para '{marca}'.")
                return []
            
            soup = BeautifulSoup(response.text, 'html.parser')
            titulos = soup.find_all('h2')
            if not titulos:
                return []
            
            items = []
            for h2 in titulos[:15]:
                nombre = h2.text.strip()
                contenedor = h2.find_parent('div')
                while contenedor and contenedor.name != 'body':
                    precio_tag = contenedor.find('span', class_=lambda c: c and 'andes-money-amount__fraction' in c)
                    if precio_tag:
                        items.append({
                            "marca_buscada": marca,
                            "producto_retail": nombre,
                            "precio_publicado": f"${precio_tag.text.strip()}"
                        })
                        break
                    contenedor = contenedor.find_parent('div')
            return items
        else:
            print(f" [Mercado Libre] HTTP {response.status_code} para '{marca}'.")
            return []
    except Exception as e:
        print(f" [Mercado Libre] Excepción en '{marca}': {e}")
        return []

def extraer_agrocampo(marca):
    """Pivote automático: extrae el catálogo de Agrocampo superando Cloudflare."""
    url = f"https://www.agrocampo.com.co/catalogsearch/result/?q={marca}"
    try:
        response = scraper.get(url, headers=headers, timeout=25)
        if response.status_code != 200:
            print(f" [Agrocampo] Error HTTP {response.status_code} para '{marca}'.")
            return []
        
        soup = BeautifulSoup(response.text, 'html.parser')
        productos_html = soup.select('.product-item')
        
        items = []
        for p in productos_html:
            nombre_tag = p.select_one('.product-item-link')
            if not nombre_tag:
                continue
            nombre = nombre_tag.text.strip()
            
            # Priorizar precio especial / promoción, luego precio final o regular
            special_price = p.select_one('.special-price .price')
            final_price = p.select_one('.price-wrapper .price') or p.select_one('.price')
            price_tag = special_price if special_price else final_price
            
            if not price_tag:
                continue
            
            raw_price = price_tag.text.strip()
            # Limpiar espacios y caracteres no imprimibles (\xa0)
            clean_price = re.sub(r'\s+', '', raw_price.replace('\xa0', ' '))
            if clean_price and not clean_price.startswith('$'):
                clean_price = f"${clean_price}"
            
            items.append({
                "marca_buscada": marca,
                "producto_retail": nombre,
                "precio_publicado": clean_price
            })
        
        return items
    except Exception as e:
        print(f" [Agrocampo] Excepción en '{marca}': {e}")
        return []

# Bucle principal de auditoría
for marca in marcas_auditoria:
    print(f"\n>>> Procesando marca objetivo: {marca}")
    
    # Tarea 1: Intentar en Mercado Libre con evasión avanzada
    print(f" -> Tarea 1: Evaluando extracción evasiva en Mercado Libre...")
    items_ml = extraer_mercadolibre(marca)
    
    if items_ml:
        print(f" -> Éxito en Mercado Libre: {len(items_ml)} productos encontrados.")
        resultados.extend(items_ml)
    else:
        # Tarea 2: Pivote automático a Agrocampo
        print(f" -> Tarea 2: Defensas impenetrables en retail primario. Pivotando automáticamente a Agrocampo (agrocampo.com.co)...")
        items_agro = extraer_agrocampo(marca)
        if items_agro:
            print(f" -> Éxito en Agrocampo: {len(items_agro)} productos extraídos evadiendo Cloudflare.")
            resultados.extend(items_agro)
        else:
            print(f" -> Advertencia: No se obtuvieron productos para '{marca}' en Agrocampo.")
    
    time.sleep(1) # Pausa cortés entre peticiones

output_path = out_dir / "02_real_portafolio_masivo.csv"

if resultados:
    # Procesar y deduplicar con Polars
    df = (
        pl.DataFrame(resultados)
        .unique(subset=["producto_retail"])
        .select(["marca_buscada", "producto_retail", "precio_publicado"])
    )
    
    df.write_csv(output_path)
    print("\n" + "=" * 60)
    print(f"¡EXTRACCIÓN EXITOSA Y GUARDADA EN POLARS!")
    print(f"Total productos únicos consolidados: {len(df)}")
    print(f"Archivo generado: {output_path}")
    print("=" * 60)
    print("\nMuestra de datos extraídos:")
    print(df.head(10))
    print("\nDistribución por marca:")
    print(df.group_by("marca_buscada").len())
else:
    print("\nError crítico: No se pudieron extraer datos de ninguna fuente.")