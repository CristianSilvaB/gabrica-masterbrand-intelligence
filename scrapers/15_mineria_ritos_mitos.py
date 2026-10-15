import logging
import re
from pathlib import Path
from typing import Dict, List, Optional

import polars as pl

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(levelname)s] - %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("MineriaRitosMitos")

INPUT_08 = Path("data/processed/08_reviews_cuantitativo.csv")
INPUT_12 = Path("data/processed/12_reviews_gemini.csv")
OUTPUT_FILE = Path("data/processed/15_mitos_ritos_oportunidades.csv")

# Diccionario de Ritos, Mitos y Oportunidades de Campaña para Gabrica
RITOS_MITOS_TAXONOMIA = [
    {
        "tipo_semiocultural": "Rito / Rutina",
        "dimension": "Rito de Salud Mensual y Fármacos",
        "regex": r'(?is)\b(cada mes|mensual|darle la pastilla|tomar la pastilla|esconder la pastilla|desparasitar|desparasitaci[oó]n|veterinario|vacuna|vacunaci[oó]n)\b',
        "habito_detectado": "Rutina periódica de prevención de parásitos o administración forzada de medicamentos.",
        "producto_gabrica_objetivo": "Simparica Trio / Apoquel",
        "oportunidad_campaña": "Campaña de palatabilidad y triple protección (pulgas, garrapatas y nematodos) para que darle la pastilla deje de ser una batalla."
    },
    {
        "tipo_semiocultural": "Rito / Rutina",
        "dimension": "Rito del Paseo y Exteriores",
        "regex": r'(?is)\b(paseo|pasear|sacar a pasear|parque|correa|collar|arn[eé]s|andar|caminar|calle)\b',
        "habito_detectado": "Salida diaria para socialización, ejercicio y desahogo de energía.",
        "producto_gabrica_objetivo": "Simparica Trio / Yoos (articulaciones) / Hydra Toallas",
        "oportunidad_campaña": "Posicionar la tranquilidad ante garrapatas del césped y protección articular/almohadillas antes y después del parque."
    },
    {
        "tipo_semiocultural": "Rito / Rutina",
        "dimension": "Rito del Baño y Cuidado Estético",
        "regex": r'(?is)\b(ba[ñn]o|ba[ñn]ar|shampoo|champ[uú]|peluquer[ií]a|cepillar|cepillado|u[ñn]as|dientes|limpiar las patas|limpieza)\b',
        "habito_detectado": "Rutina de higiene periódica, desenredo de pelo o desinfección.",
        "producto_gabrica_objetivo": "Hydra (Pet Society) / Fresh Step",
        "oportunidad_campaña": "Ritual de spa en casa y aromaterapia profesional que convierte el estrés del baño en un momento de afecto."
    },
    {
        "tipo_semiocultural": "Rito / Rutina",
        "dimension": "Rito de la Comida y Premiación",
        "regex": r'(?is)\b(premio|premiar|snack|galleta|llegar a casa|hora de comer|ansiedad por comer|mezclar|comida h[uú]meda|plato)\b',
        "habito_detectado": "Recompensa emocional al llegar a casa o estímulo con toppings húmedos.",
        "producto_gabrica_objetivo": "Plaisir (Paté/Salsa) / Hill's Science Diet Treats",
        "oportunidad_campaña": "Promover la 'nutrición mixta' (croquetas + paté Plaisir) como el premio saludable que no desbalancea la dieta."
    },
    {
        "tipo_semiocultural": "Rito / Rutina",
        "dimension": "Rito de Soledad, Viajes y Mudanzas",
        "regex": r'(?is)\b(dejarlo sol[oa]|dejarlos sol[oa]s|soledad|viaje|viajar|carro|auto|avi[oó]n|guacal|trasteo|mudanza|ansiedad por separaci[oó]n)\b',
        "habito_detectado": "Situaciones de alta tensión, ruidos, viajes en carro o soledad durante la jornada laboral.",
        "producto_gabrica_objetivo": "Feliway (Gatos) / Adaptil (Perros)",
        "oportunidad_campaña": "Campaña de bienestar emocional y feromonas para hogares sin estrés ('Viaja y trabaja tranquilo con Adaptil y Feliway')."
    },
    {
        "tipo_semiocultural": "Mito / Creencia",
        "dimension": "Mito Dieta BARF vs. Concentrado Seco",
        "regex": r'(?is)\b(barf|dieta natural|comida casera|cruda|carne cruda|huesos|hueso carnoso|sin granos|grain free|veneno el concentrado)\b',
        "habito_detectado": "Creencia de que los concentrados comerciales son dañinos o que la carne cruda es intrínsecamente superior.",
        "producto_gabrica_objetivo": "Guabi Natural / Hill's Science Diet",
        "oportunidad_campaña": "Educar sobre los riesgos bacterianos de la carne cruda y posicionar Guabi Natural como la alternativa holística segura y balanceada."
    },
    {
        "tipo_semiocultural": "Mito / Creencia",
        "dimension": "Mito de Vulnerabilidad por Raza",
        "regex": r'(?is)\b(los bulldog|los pug|los gatos blancos|braquic[eé]falos|pastor alem[aá]n|raza propensa|gen[eé]tica de la raza|los caniches)\b',
        "habito_detectado": "Convicción de que ciertas razas están destinadas a sufrir de la piel, digestión o articulaciones.",
        "producto_gabrica_objetivo": "Hill's Prescription Diet / Apoquel / Holliday Artrin",
        "oportunidad_campaña": "Derribar la resignación: nutrición y moléculas terapéuticas personalizadas que devuelven la calidad de vida sin importar la raza."
    }
]


def clasificar_semiocultura(texto: str) -> Optional[Dict[str, str]]:
    """Evalúa un texto y detecta si describe ritos, mitos o hábitos de cuidado animal."""
    if not texto or len(texto.strip()) < 35:
        return None

    for item in RITOS_MITOS_TAXONOMIA:
        if re.search(item["regex"], texto):
            return {
                "tipo_semiocultural": item["tipo_semiocultural"],
                "dimension_cultural": item["dimension"],
                "habito_detectado": item["habito_detectado"],
                "producto_gabrica_objetivo": item["producto_gabrica_objetivo"],
                "oportunidad_campaña": item["oportunidad_campaña"]
            }
    return None


def main():
    logger.info("🚀 Iniciando Minería de Perfil Semiocultural (Ritos, Mitos y Hábitos)...")

    dfs = []
    if INPUT_08.exists():
        df_08 = pl.read_csv(INPUT_08)
        dfs.append(df_08.select(["fuente", "objetivo", "texto_opinion", "sentimiento"]))

    if INPUT_12.exists():
        df_12 = pl.read_csv(INPUT_12)
        dfs.append(df_12.select(["fuente", "objetivo", "texto_opinion", "sentimiento"]))

    if not dfs:
        logger.error("❌ No se encontraron datasets locales.")
        sys.exit(1)

    df_total = pl.concat(dfs).unique(subset=["fuente", "objetivo", "texto_opinion"])
    logger.info(f"Total opiniones únicas a auditar: {df_total.height:,}")

    filas_resultados = []
    for fila in df_total.iter_rows(named=True):
        analisis = clasificar_semiocultura(fila["texto_opinion"])
        if analisis:
            # Detectar si es oportunidad cruzada de conquista
            es_marca_rival = fila["objetivo"] in ["Bravecto", "Nexgard", "Purina", "Laika", "Agrocampo"]
            es_oportunidad_conquista = "SÍ: Usuario en ecosistema rival conquistable" if es_marca_rival else "Fidelización / Cross-selling Gabrica"

            filas_resultados.append({
                "fuente": fila["fuente"],
                "marca_mencionada": fila["objetivo"],
                "texto_opinion": fila["texto_opinion"],
                "sentimiento": fila["sentimiento"],
                "tipo_semiocultural": analisis["tipo_semiocultural"],
                "dimension_cultural": analisis["dimension_cultural"],
                "habito_detectado": analisis["habito_detectado"],
                "producto_gabrica_recomendado": analisis["producto_gabrica_objetivo"],
                "oportunidad_campaña": analisis["oportunidad_campaña"],
                "estrategia_comercial": es_oportunidad_conquista
            })

    df_resultado = pl.DataFrame(filas_resultados).unique(subset=["fuente", "marca_mencionada", "texto_opinion"])

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    df_resultado.write_csv(OUTPUT_FILE)
    logger.info(f"✅ ¡Minería semiocultural finalizada! {df_resultado.height:,} hábitos y mitos en: {OUTPUT_FILE}")

    # Resumen analítico en consola
    print("\n" + "=" * 70)
    print("🏺 RESUMEN DE PERFIL SEMIOCULTURAL: RITOS, MITOS Y OPORTUNIDADES")
    print("=" * 70)
    print("\nPor Dimensión Cultural / Rito:")
    print(df_resultado.group_by("dimension_cultural").len().sort("len", descending=True))

    print("\nPor Estrategia Comercial:")
    print(df_resultado.group_by("estrategia_comercial").len().sort("len", descending=True))

    print("\nPor Marca donde se detectó el rito:")
    print(df_resultado.group_by("marca_mencionada").len().sort("len", descending=True))
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
