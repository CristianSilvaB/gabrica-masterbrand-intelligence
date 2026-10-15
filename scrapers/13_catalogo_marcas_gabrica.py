import html
import logging
import re
import sys
from pathlib import Path
from typing import Dict, List

import httpx
import polars as pl

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(levelname)s] - %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("CatalogoGabrica")

OUTPUT_FILE = Path("data/processed/13_catalogo_marcas_gabrica.csv")
CATALOG_URL = "https://gabrica.co/personas/es-CO/catalogo-productos"

# Matriz de Inteligencia Competitiva para el Mercado de Mascotas en Colombia
COMPETENCIA_TAXONOMIA: Dict[str, Dict[str, str]] = {
    "Hill's": {
        "categoria_estrategica": "Nutrición Super Premium / Veterinaria",
        "fabricante": "Hill's Pet Nutrition (Colgate-Palmolive)",
        "competidores_directos": "Royal Canin (Prescription/Size Health), Purina Pro Plan Veterinary Diets, Monello Select, Taste of the Wild",
        "ventaja_diferencial": "Alimentos con respaldo clínico y prescripción veterinaria para patologías específicas (urinario, renal, gastrointestinal, peso)."
    },
    "Grand Vita Equilibrio": {
        "categoria_estrategica": "Nutrición Super Premium / Especializada",
        "fabricante": "Total Alimentos / ADM",
        "competidores_directos": "Royal Canin, Purina Pro Plan, Diamond Naturals, Acana",
        "ventaja_diferencial": "Proteínas de alta digestibilidad, extracto de yucca para control de olores y libre de transgénicos."
    },
    "Grand Vita": {
        "categoria_estrategica": "Nutrición Premium",
        "fabricante": "ADM Animal Nutrition",
        "competidores_directos": "Chunky, Brit Premium, Nutra Nuggets",
        "ventaja_diferencial": "Nutrición integral accesible con balance óptimo de omega 3 y 6."
    },
    "Guabi Natural": {
        "categoria_estrategica": "Nutrición Holística / Natural",
        "fabricante": "BRF Pet",
        "competidores_directos": "Taste of the Wild, Orijen, Acana, Nutripet Natural",
        "ventaja_diferencial": "Conservación 100% natural sin colorantes ni aromas artificiales, con carnes seleccionadas."
    },
    "Max": {
        "categoria_estrategica": "Nutrición Premium Especial",
        "fabricante": "Total Alimentos",
        "competidores_directos": "Chunky, Dog Chow, Cat Chow, Ringo Premium",
        "ventaja_diferencial": "Excelente palatabilidad y rendimiento costo-beneficio para familias multimasctoa."
    },
    "Guaumor": {
        "categoria_estrategica": "Nutrición Estándar / Mainstream",
        "fabricante": "Gabrica Distribución",
        "competidores_directos": "Dog Chow, Ringo, Pedigree, Nutre Can",
        "ventaja_diferencial": "Alimento balanceado nacional con alta rotación en pet shops y agropecuarias."
    },
    "Manjar": {
        "categoria_estrategica": "Nutrición Económica / Masiva",
        "fabricante": "Gabrica Distribución",
        "competidores_directos": "Ringo, Mirringo, Campeón, Monello Tradicional",
        "ventaja_diferencial": "Fórmula accesible con pepas crocantes sabor a carne y pollo."
    },
    "Plaisir": {
        "categoria_estrategica": "Alimento Húmedo & Gourmet",
        "fabricante": "Normandise Pet Food (Francia)",
        "competidores_directos": "Purina Felix, Whiskas Paté, Sheba, Cesar, Hill's Cans",
        "ventaja_diferencial": "Troceados en salsa y patés importados franceses de altísima palatabilidad."
    },
    "Simparica": {
        "categoria_estrategica": "Antiparasitario Oral Mensual",
        "fabricante": "Zoetis",
        "competidores_directos": "Bravecto (MSD), NexGard (Boehringer Ingelheim), Credelio (Elanco)",
        "ventaja_diferencial": "Masticable sabor hígado de rápida acción (comienza a matar pulgas en 3 horas) y protección sostenida por 35 días."
    },
    "Zoetis": {
        "categoria_estrategica": "Salud & Biológicos Veterinarios",
        "fabricante": "Zoetis",
        "competidores_directos": "MSD Animal Health, Boehringer Ingelheim, Elanco, Virbac",
        "ventaja_diferencial": "Líder mundial en salud animal, vacunas y moléculas de prescripción veterinaria."
    },
    "Apoquel": {
        "categoria_estrategica": "Dermatología / Control Prurito Canino",
        "fabricante": "Zoetis",
        "competidores_directos": "Cytopoint (Zoetis), Corticoides sistémicos, Atopica (Elanco)",
        "ventaja_diferencial": "Inhibidor de JAK que detiene la picazón alérgica en 4 horas sin los efectos secundarios de los esteroides."
    },
    "Hydra": {
        "categoria_estrategica": "Aseo Profesional & Dermocosmética",
        "fabricante": "Pet Society (Brasil)",
        "competidores_directos": "Canamor, TropiClean, Bioline, Shampoos genéricos",
        "ventaja_diferencial": "Fórmulas ultraconcentradas de salón profesional y spa (extracto de avena, aceites esenciales, fragancias de larga duración)."
    },
    "Feliway": {
        "categoria_estrategica": "Comportamiento & Feromonas Felinas",
        "fabricante": "Ceva Santé Animale",
        "competidores_directos": "Catnip genérico, suplementos calmantes de valeriana/CBD",
        "ventaja_diferencial": "Análogo sintético de la feromona facial felina que reduce marcaje por orina, rascado y estrés en viajes/mudanzas."
    },
    "Adaptil": {
        "categoria_estrategica": "Comportamiento & Feromonas Caninas",
        "fabricante": "Ceva Santé Animale",
        "competidores_directos": "Calmantes de manzanilla, chalecos antiestrés Thundershirt",
        "ventaja_diferencial": "Copia de la feromona de apaciguamiento materno para miedo a pólvora, truenos y soledad."
    },
    "Fresh Step": {
        "categoria_estrategica": "Higiene / Arenas Sanitarias Aglomerantes",
        "fabricante": "The Clorox Company",
        "competidores_directos": "Sanicat, America Litter, Odor Eaters, Arenas de arcilla genéricas",
        "ventaja_diferencial": "Carbón activado con control superior de amoníaco y tecnología Febreze de bloqueo de olores."
    },
    "Feline Pine": {
        "categoria_estrategica": "Higiene / Arena Ecológica 100% Pino",
        "fabricante": "Church & Dwight Co.",
        "competidores_directos": "Cat's Best, Arena de tofu, aserrín prensado",
        "ventaja_diferencial": "Pellets naturales de pino reciclado que absorben humedad y neutralizan olores sin polvo ni químicos."
    },
    "Comfort Kat": {
        "categoria_estrategica": "Higiene / Arena Sanitaria Básica",
        "fabricante": "Gabrica Distribución",
        "competidores_directos": "Arenas blancas locales, bentonita a granel",
        "ventaja_diferencial": "Bentonita aglomerante de excelente absorción y costo competitivo."
    },
    "Holliday": {
        "categoria_estrategica": "Farmacéutica & Suplementación Especial",
        "fabricante": "Holliday-Scott (Argentina)",
        "competidores_directos": "Laboratorios Erma, Carval, Virbac, Brouwer",
        "ventaja_diferencial": "Condroprotectores articulares (Artrin), oftalmología y hepatoprotectores líderes en clínicas veterinarias."
    },
    "Vetnil": {
        "categoria_estrategica": "Nutracéuticos, Equinos y Mascotas",
        "fabricante": "Vetnil (Brasil)",
        "competidores_directos": "Nutri-Plus Gel, Glicopan pet competitors, suplementos vitamínicos",
        "ventaja_diferencial": "Referente en suplementos de aminoácidos y recuperación para mascotas y caballos de alto rendimiento."
    },
    "Ourofino": {
        "categoria_estrategica": "Salud Animal & Fármacos",
        "fabricante": "Ourofino Saúde Animal (Brasil)",
        "competidores_directos": "Bayer/Elanco, MSD, laboratorios nacionales",
        "ventaja_diferencial": "Antimicrobianos y antiparasitarios confiables para medicina veterinaria."
    }
}


def extraer_catalogo_gabrica() -> pl.DataFrame:
    """Extrae las marcas, especies y tipos de producto desde el portal oficial de Gabrica."""
    logger.info(f"🌐 Conectando a {CATALOG_URL}...")
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept-Language": "es-CO,es;q=0.9"
    }

    try:
        response = httpx.get(CATALOG_URL, headers=headers, timeout=25, follow_redirects=True)
        response.raise_for_status()
    except Exception as e:
        logger.error(f"❌ Error al consultar el catálogo de Gabrica: {e}")
        sys.exit(1)

    html_content = response.text
    logger.info(f"HTML recibido ({len(html_content)} bytes). Parseando taxonomía...")

    # Extraer entradas de marca estructuradas en el payload Next.js
    pattern = re.compile(
        r'\\"brand\\":\\"([^\\"]+)\\",\\"petType\\":\\"([^\\"]+)\\",.*?\\"productType\\":\\"([^\\"]+)\\"'
    )
    raw_matches = pattern.findall(html_content)

    if not raw_matches:
        logger.warning("No se encontraron entradas con el patrón principal. Usando selector secundario...")
        pattern_secundario = re.compile(r'brand\\\":\\\"([^\\\"]+)\\\"')
        marcas_sec = list(set(pattern_secundario.findall(html_content)))
        raw_matches = [(m, "Canino/Felino", "General") for m in marcas_sec]

    logger.info(f"-> Se detectaron {len(raw_matches)} registros brutos en el catálogo.")

    # Construir DataFrame normalizado
    filas = []
    for marca, pet_type, prod_type in raw_matches:
        marca_limpia = html.unescape(marca).strip()
        pet_limpio = html.unescape(pet_type).strip()
        prod_limpio = html.unescape(prod_type).strip()

        # Obtener metadata de inteligencia de mercado si está registrada
        meta = COMPETENCIA_TAXONOMIA.get(marca_limpia, {
            "categoria_estrategica": f"Especialidad ({prod_limpio})",
            "fabricante": "Gabrica Alianzas Internacionales",
            "competidores_directos": "Marcas del canal veterinario y retail",
            "ventaja_diferencial": "Distribución exclusiva por Gabrica Colombia."
        })

        filas.append({
            "marca_gabrica": marca_limpia,
            "tipo_mascota": pet_limpio,
            "categoria_producto": prod_limpio,
            "categoria_estrategica": meta["categoria_estrategica"],
            "fabricante_origen": meta["fabricante"],
            "es_portafolio_gabrica": True,
            "competidores_directos": meta["competidores_directos"],
            "ventaja_diferencial": meta["ventaja_diferencial"]
        })

    df = pl.DataFrame(filas).unique(
        subset=["marca_gabrica", "tipo_mascota", "categoria_producto"]
    ).sort(["categoria_producto", "marca_gabrica"])

    return df


def main():
    logger.info("🚀 Iniciando Extractor Oficial de Catálogo y Taxonomía de Marcas Gabrica...")
    df_catalogo = extraer_catalogo_gabrica()

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    df_catalogo.write_csv(OUTPUT_FILE)
    logger.info(f"✅ ¡Catálogo generado con éxito! {df_catalogo.height} líneas guardadas en: {OUTPUT_FILE}")

    # Mostrar resumen en consola
    print("\n" + "=" * 75)
    print("🐾 PORTAFOLIO OFICIAL DE MARCAS GABRICA COLOMBIA Y COMPETIDORES")
    print("=" * 75)
    resumen = df_catalogo.group_by(["categoria_producto"]).agg([
        pl.col("marca_gabrica").unique().alias("marcas_distribuidas"),
        pl.len().alias("variantes_registradas")
    ]).sort("variantes_registradas", descending=True)
    print(resumen)
    print("=" * 75 + "\n")


if __name__ == "__main__":
    main()
