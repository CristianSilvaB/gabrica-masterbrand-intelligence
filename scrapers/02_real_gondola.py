import asyncio
from playwright.async_api import async_playwright
import polars as pl
from pathlib import Path

out_dir = Path("data/processed")
out_dir.mkdir(parents=True, exist_ok=True)

async def scrape_laika():
    print("Iniciando navegador con camuflaje antibot para retail...")
    async with async_playwright() as p:
        # Añadimos user_agent para evitar que Cloudflare o Laika nos bloqueen
        browser = await p.chromium.launch(headless=True)
        context = await browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
        )
        page = await context.new_page()
        
        marcas_auditoria = ["Hills", "Simparica", "Equilibrio"]
        resultados = []

        for marca in marcas_auditoria:
            print(f"Buscando {marca} en Laika Colombia...")
            url = f"https://laika.com.co/search?q={marca}"
            
            try:
                # Esperar hasta que la red esté tranquila (la página cargó por completo)
                await page.goto(url, wait_until="networkidle", timeout=60000)
                await page.wait_for_timeout(4000) # Pausa para que el JavaScript renderice
                
                # Extraemos agresivamente cualquier bloque de texto que contenga un precio ($)
                productos_crudos = await page.evaluate('''() => {
                    let items = [];
                    // Buscamos cualquier enlace o contenedor div profundo
                    let cards = document.querySelectorAll('a, div');
                    cards.forEach(card => {
                        let text = card.innerText;
                        // Si tiene texto, contiene un signo $ y no es un texto gigante de toda la página
                        if (text && text.includes('$') && text.length < 200 && text.length > 15) {
                            items.push(text);
                        }
                    });
                    return items;
                }''')
                
                # Limpiar y procesar el texto extraído
                for prod_text in productos_crudos:
                    lineas = [linea.strip() for linea in prod_text.split('\n') if linea.strip()]
                    if len(lineas) >= 2:
                        precio = next((l for l in lineas if '$' in l), None)
                        nombre = next((l for l in lineas if len(l) > 4 and '$' not in l), None)
                        
                        if precio and nombre:
                            resultados.append({
                                "marca_buscada": marca,
                                "producto_retail": nombre,
                                "precio_publicado": precio
                            })
                            
                print(f" -> Bloques de producto analizados para {marca}")
            except Exception as e:
                print(f"Fallo en {marca}: {e}")
                
        await browser.close()
        
        if resultados:
            # Eliminar duplicados generados por la extracción agresiva
            df = pl.DataFrame(resultados).unique(subset=["producto_retail"])
            output_path = out_dir / "02_real_portafolio_precios.csv"
            df.write_csv(output_path)
            print(f"¡Éxito total! {len(df)} productos reales extraídos y guardados en {output_path}")
        else:
            print("No se extrajeron productos. La página está bloqueando el tráfico severamente.")

asyncio.run(scrape_laika())