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
logger = logging.getLogger("MineriaTensionesBarreras")

INPUT_08 = Path("data/processed/08_reviews_cuantitativo.csv")
INPUT_12 = Path("data/processed/12_reviews_gemini.csv")
OUTPUT_FILE = Path("data/processed/14_motivaciones_tensiones_barreras.csv")

# Diccionario de Patrones Sintácticos y de Negocio (Requerimientos de Pato)
PATRONES_TENSION = [
    {
        "tipo_insight": "Tensión",
        "patron": "Deseo vs Costo",
        "regex": r'(?is)\b(lo mejor|excelente|calidad|bueno|buena|encanta|recomiendo)\b.*?\b(pero|l[aá]stima que|aunque)\b.*?\b(car[oa]|costos[oa]|precio|plata|dinero|mantener|alcance)\b',
        "categoria": "Precio/Costo",
        "oportunidad": "Presentar alternativas con alto costo-beneficio de Gabrica (Max, Grand Vita, presentaciones de mayor rendimiento)."
    },
    {
        "tipo_insight": "Tensión",
        "patron": "Efectividad vs Efecto Secundario",
        "regex": r'(?is)\b(funciona|sirve|efectiv[oa]|mata|limpia|buen producto)\b.*?\b(pero|problema es que|l[aá]stima|aunque|sin embargo)\b.*?\b(v[oó]mit|diarre|alerg|rasca|enferm|dañ|t[oó]xic|malestar|rechaz)\b',
        "categoria": "Efecto Adverso",
        "oportunidad": "Posicionar la seguridad gástrica y palatabilidad de Simparica Trio o dietas Hill's i/d Digestive Care."
    },
    {
        "tipo_insight": "Tensión",
        "patron": "Lealtad en Riesgo",
        "regex": r'(?is)\b(toda la vida|siempre|hace a[ñn]os|a[ñn]os usando|compraba|llevo a[ñn]os)\b.*?\b(pero [uú]ltimamente|ya no|dej[oó] de funcionar|no le hace efecto|cambi[oó] la f[oó]rmula|esta vez)\b',
        "categoria": "Efectividad/Fórmula",
        "oportunidad": "Captar clientes frustrados con campañas de renovación antiparasitaria o migración nutricional a Hill's Science Diet."
    },
    {
        "tipo_insight": "Tensión",
        "patron": "Disonancia con Veterinario/Recomendación",
        "regex": r'(?is)\b(le[ií]|dicen|amig[oa]|internet|video|redes)\b.*?\b(pero el veterinario|mi veterinario|veterinaria dice|recomienda|me dijo que)\b',
        "categoria": "Conflicto de Criterio",
        "oportunidad": "Reforzar la educación científica de Gabrica y respaldo veterinario oficial para dar certidumbre al tutor."
    },
    {
        "tipo_insight": "Tensión",
        "patron": "Quiero pero Limitante",
        "regex": r'(?is)\b(quiero|quisiera|me encantar[ií]a|deseo|busco|gustar[ií]a)\b.*?\b(pero|l[aá]stima|el problema es|no puedo|dif[ií]cil|miedo|duda)\b',
        "categoria": "Fricción de Compra",
        "oportunidad": "Eliminar barreras de entrada con muestras médicas, promociones en canal veterinario y asesoría personalizada."
    },
    {
        "tipo_insight": "Barrera",
        "patron": "Barrera de Precio Extremo",
        "regex": r'(?is)\b(muy car[oa]|demasiado car[oa]|precio excesivo|por las nubes|inaccesible|imposible pagar|subi[oó] mucho)\b',
        "categoria": "Precio/Inaccesibilidad",
        "oportunidad": "Ofrecer presentaciones accesibles, esquemas de fidelización o marcas escalables como Max o Guaumor."
    },
    {
        "tipo_insight": "Barrera",
        "patron": "Barrera de Disponibilidad/Canal",
        "regex": r'(?is)\b(no se consigue|no hay|agotado|descontinuado|dif[ií]cil de encontrar|en ninguna veterinaria|no lo encuentro)\b',
        "categoria": "Disponibilidad/Distribución",
        "oportunidad": "Optimizar la red de distribución de Gabrica en clínicas aliadas y geolocalizar puntos de venta oficiales."
    },
    {
        "tipo_insight": "Motivación",
        "patron": "Motivación de Salud y Bienestar",
        "regex": r'(?is)\b(para que no sufra|por su salud|calidad de vida|mejor para mi (perr|gat)|vale la pena la salud|su bienestar|hacerlo feliz|lo amo|la amo)\b',
        "categoria": "Vínculo Emocional / Salud",
        "oportunidad": "Campañas de humanización y bienestar integral ('Cuidamos juntos, crecemos juntos') apalancando nutrición clínica."
    }
]

# Patrón genérico de Fricción / Adversativo con Dolor
REGEX_ADVERSATIVO = re.compile(r'(?i)\b(pero|aunque|sin embargo|l[aá]stima que|el problema es)\b')
REGEX_DOLOR = re.compile(r'(?i)\b(v[oó]mit|diarre|alerg|reacci[oó]n|rasca|car[oa]|costos[oa]|precio|vencid|enferm|intoxic|rechaz|duro|sabor|engorda|pepa|olor)\b')


def clasificar_opinion(texto: str) -> Optional[Dict[str, str]]:
    """Evalúa un texto y retorna la clasificación de tensión, barrera o motivación si aplica."""
    if not texto or len(texto.strip()) < 35:
        return None

    # 1. Probar patrones específicos de alta precisión
    for p in PATRONES_TENSION:
        if re.search(p["regex"], texto):
            return {
                "tipo_insight": p["tipo_insight"],
                "patron_detectado": p["patron"],
                "categoria_problema": p["categoria"],
                "oportunidad_gabrica": p["oportunidad"]
            }

    # 2. Probar combinación adversativo + dolor si no coincidió con los anteriores
    if REGEX_ADVERSATIVO.search(texto) and REGEX_DOLOR.search(texto):
        # Determinar categoría básica
        t_low = texto.lower()
        if any(w in t_low for w in ["caro", "costoso", "precio", "plata"]):
            cat = "Precio/Costo"
            op = "Fomentar líneas con alta relación beneficio-costo o presentaciones grandes."
        elif any(w in t_low for w in ["vomit", "diarre", "alerg", "intoxic", "enferm"]):
            cat = "Efecto Adverso"
            op = "Promover formulaciones hipoalergénicas o digestivas de Gabrica (Hill's d/d, i/d, z/d)."
        elif any(w in t_low for w in ["rechaz", "sabor", "duro", "no come", "no le gustó"]):
            cat = "Palatabilidad/Aceptación"
            op = "Destacar palatabilidad garantizada y mezclas con alimento húmedo Plaisir."
        elif any(w in t_low for w in ["vencid", "roto", "caja", "olor"]):
            cat = "Calidad/Empaque"
            op = "Garantía de originalidad y frescura a través de la cadena de distribución médica de Gabrica."
        else:
            cat = "Fricción General"
            op = "Identificar y abordar objeciones específicas en el punto de venta veterinario."

        return {
            "tipo_insight": "Tensión",
            "patron_detectado": "Adversativo con Dolor Específico",
            "categoria_problema": cat,
            "oportunidad_gabrica": op
        }

    return None


def main():
    logger.info("🚀 Iniciando Minería de Motivaciones, Tensiones y Barreras (Costo $0 USD)...")

    # Cargar datasets locales
    dfs = []
    if INPUT_08.exists():
        logger.info(f"Cargando dataset cuantitativo: {INPUT_08}...")
        df_08 = pl.read_csv(INPUT_08)
        dfs.append(df_08.select(["fuente", "objetivo", "texto_opinion", "sentimiento"]))

    if INPUT_12.exists():
        logger.info(f"Cargando dataset cualitativo de Gemini: {INPUT_12}...")
        df_12 = pl.read_csv(INPUT_12)
        dfs.append(df_12.select(["fuente", "objetivo", "texto_opinion", "sentimiento"]))

    if not dfs:
        logger.error("❌ No se encontraron datasets locales para procesar.")
        sys.exit(1)

    df_total = pl.concat(dfs).unique(subset=["fuente", "objetivo", "texto_opinion"])
    logger.info(f"Total opiniones únicas a auditar: {df_total.height:,}")

    # Procesar fila por fila en memoria
    resultados = []
    for fila in df_total.iter_rows(named=True):
        analisis = clasificar_opinion(fila["texto_opinion"])
        if analisis:
            resultados.append({
                "fuente": fila["fuente"],
                "marca_evaluada": fila["objetivo"],
                "texto_opinion": fila["texto_opinion"],
                "sentimiento_base": fila["sentimiento"],
                "tipo_insight": analisis["tipo_insight"],
                "patron_detectado": analisis["patron_detectado"],
                "categoria_problema": analisis["categoria_problema"],
                "oportunidad_gabrica": analisis["oportunidad_gabrica"]
            })

    df_resultado = pl.DataFrame(resultados).unique(subset=["fuente", "marca_evaluada", "texto_opinion"])

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    df_resultado.write_csv(OUTPUT_FILE)
    logger.info(f"✅ ¡Minería finalizada! {df_resultado.height:,} tensiones y barreras extraídas en: {OUTPUT_FILE}")

    # Resumen en consola
    print("\n" + "=" * 70)
    print("🧠 RESUMEN DE TENSIONES, BARRERAS Y MOTIVACIONES DETECTADAS")
    print("=" * 70)
    print("\nPor Tipo de Insight:")
    print(df_resultado.group_by("tipo_insight").len().sort("len", descending=True))

    print("\nPor Patrón Específico:")
    print(df_resultado.group_by("patron_detectado").len().sort("len", descending=True))

    print("\nPor Categoría del Problema:")
    print(df_resultado.group_by("categoria_problema").len().sort("len", descending=True))

    print("\nPor Marca Evaluada:")
    print(df_resultado.group_by("marca_evaluada").len().sort("len", descending=True))
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
