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
logger = logging.getLogger("VerbatimsDoloresCompetencia")

INPUT_08 = Path("data/processed/08_reviews_cuantitativo.csv")
INPUT_12 = Path("data/processed/12_reviews_gemini.csv")
OUTPUT_FILE = Path("data/processed/16_verbatims_dolores_competencia.csv")

# Marcas rivales a auditar para identificar oportunidades de conquista
MARCAS_RIVALES = ["Bravecto", "Nexgard", "Purina", "Laika", "Agrocampo"]

# Clasificador de dolores y fallas de producto rival
CATEGORIAS_DOLOR = [
    {
        "categoria_falla": "Falla de Eficacia / No Sirvió",
        "regex": r'(?i)\b(no sirvi[oó]|no funcion[oó]|sigue con pulgas|todav[ií]a tiene pulgas|no le quit[oó]|lleno de garrapatas|infestado|plaga|ineficaz|no hace nada|perrotodav[ií]a se rasca)\b',
        "reaccion_tutor": "Frustración por haber pagado un alto precio sin resolver el problema de salud.",
        "solucion_gabrica": "Simparica Trio / Revolution Plus",
        "argumento_campaña": "Eliminación rápida y sostenida por 35 días con efectividad garantizada comprobada clínicamente."
    },
    {
        "categoria_falla": "Efectos Secundarios / Intoxicación / Vómito",
        "regex": r'(?i)\b(vomit[oó]|v[oó]mito|diarrea|temblor|convulsi[oó]n|intoxic[oó]|intoxicaci[oó]n|enferm[oó]|le cay[oó] mal|veneno|alergia|baba|letargo|decaimiento)\b',
        "reaccion_tutor": "Angustia, culpa y miedo genuino por poner en riesgo la vida de su mascota.",
        "solucion_gabrica": "Simparica Trio / Hill's Prescription Diet i/d / Apoquel",
        "argumento_campaña": "Seguridad gastrointestinal validada sin sobrecargas tóxicas ni estrés estomacal."
    },
    {
        "categoria_falla": "Rechazo de Sabor / Palatabilidad Nula",
        "regex": r'(?i)\b(no se lo come|no le gust[oó]|rechaz[oó]|lo escupi[oó]|imposible que se lo tome|muy duro|pepa dura|olor feo|huele a qu[ií]mico|ni lo mira|toca obligar)\b',
        "reaccion_tutor": "Molestia y frustración por batallar a diario para que la mascota coma o tome el tratamiento.",
        "solucion_gabrica": "Plaisir (Alimento Húmedo Francés) / Simparica sabor hígado / Max",
        "argumento_campaña": "Palatabilidad irresistible que transforma la medicina y la comida en un momento de disfrute voluntario."
    },
    {
        "categoria_falla": "Producto Vencido / Empaque Roto / Dudas de Autenticidad",
        "regex": r'(?i)\b(vencid[oa]|fecha de vencimiento|venci[oó]|caja rota|sello roto|abierto|falso|pirata|imitaci[oó]n|adulterado|lleg[oó] roto|aplastado)\b',
        "reaccion_tutor": "Inseguridad, sospecha de fraude y temor a aplicar productos no originales.",
        "solucion_gabrica": "Red Oficial de Clínicas Veterinarias y Pet Shops Aliados Gabrica",
        "argumento_campaña": "Garantía de procedencia legal, cadena de frío y respaldo de laboratorio oficial."
    },
    {
        "categoria_falla": "Precios Abusivos / Alzas Injustificadas",
        "regex": r'(?i)\b(muy car[oa]|demasiado car[oa]|por las nubes|subi[oó] un mont[oó]n|imposible de mantener|atraco|robo|costos[ií]simo|abuso)\b',
        "reaccion_tutor": "Imposibilidad económica de sostener el tratamiento mensual o la alimentación.",
        "solucion_gabrica": "Grand Vita Equilibrio / Max / Guaumor / Planes preventivos",
        "argumento_campaña": "Nutrición y protección de nivel veterinario con rendimientos que protegen el bolsillo del hogar."
    },
    {
        "categoria_falla": "Fallas Logísticas / Demoras de Entrega",
        "regex": r'(?i)\b(demor[oó]|tard[oó]|nunca lleg[oó]|cancelaron|p[eé]simo servicio|no responden|atenci[oó]n p[eé]sima|mala entrega|retraso)\b',
        "reaccion_tutor": "Desesperación por dejar a la mascota sin alimento o sin medicación a tiempo.",
        "solucion_gabrica": "Disponibilidad Inmediata en Clínicas Veterinarias de Barrio y Tiendas Especializadas",
        "argumento_campaña": "Cero esperas: siempre disponible al lado de tu casa con asesoría veterinaria directa."
    }
]


def clasificar_dolor_rival(texto: str) -> Optional[Dict[str, str]]:
    """Identifica la causa raíz de insatisfacción del cliente con una marca rival."""
    if not texto or len(texto.strip()) < 25:
        return None

    for cat in CATEGORIAS_DOLOR:
        if re.search(cat["regex"], texto):
            return {
                "categoria_falla_rival": cat["categoria_falla"],
                "reaccion_tutor": cat["reaccion_tutor"],
                "solucion_recomendada_gabrica": cat["solucion_gabrica"],
                "argumento_campaña_para_robar_cliente": cat["argumento_campaña"]
            }

    # Si es negativo pero no encajó en las anteriores
    return {
        "categoria_falla_rival": "Insatisfacción General con la Marca",
        "reaccion_tutor": "Descontento con el rendimiento del producto rival.",
        "solucion_recomendada_gabrica": "Portafolio Integral Gabrica",
        "argumento_campaña_para_robar_cliente": "Atraer al usuario comunicando el respaldo técnico y científico de Gabrica."
    }


def main():
    logger.info("🚀 Iniciando Extracción de Verbatims y Dolores de la Competencia...")

    # Cargar datasets
    dfs = []
    if INPUT_08.exists():
        df_08 = pl.read_csv(INPUT_08)
        dfs.append(df_08.select(["fuente", "objetivo", "texto_opinion", "sentimiento"]))

    if INPUT_12.exists():
        df_12 = pl.read_csv(INPUT_12)
        dfs.append(df_12.select(["fuente", "objetivo", "texto_opinion", "sentimiento"]))

    df_total = pl.concat(dfs).unique(subset=["fuente", "objetivo", "texto_opinion"])

    # Filtrar solo reseñas negativas de marcas rivales
    df_rivales_negativos = df_total.filter(
        (pl.col("objetivo").is_in(MARCAS_RIVALES)) &
        (pl.col("sentimiento") == "negativo") &
        (pl.col("texto_opinion").str.strip_chars().str.len_chars() >= 25)
    )

    logger.info(f"Total opiniones negativas de marcas rivales identificadas: {df_rivales_negativos.height:,}")

    filas_verbatims = []
    for fila in df_rivales_negativos.iter_rows(named=True):
        dolor = clasificar_dolor_rival(fila["texto_opinion"])
        if dolor:
            filas_verbatims.append({
                "fuente": fila["fuente"],
                "marca_competencia": fila["objetivo"],
                "verbatim_literal": fila["texto_opinion"],
                "categoria_falla_rival": dolor["categoria_falla_rival"],
                "reaccion_psicologica_tutor": dolor["reaccion_tutor"],
                "solucion_gabrica_recomendada": dolor["solucion_recomendada_gabrica"],
                "argumento_campaña_para_conquistar_cliente": dolor["argumento_campaña_para_robar_cliente"]
            })

    df_salida = pl.DataFrame(filas_verbatims).unique(subset=["fuente", "marca_competencia", "verbatim_literal"])

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    df_salida.write_csv(OUTPUT_FILE)
    logger.info(f"✅ ¡Base de Verbatims de Conquista finalizada! {df_salida.height:,} filas guardadas en: {OUTPUT_FILE}")

    # Resumen en consola
    print("\n" + "=" * 70)
    print("⚔️ BANCO DE VERBATIMS DE LA COMPETENCIA (ARGUMENTOS DE CONQUISTA)")
    print("=" * 70)
    print("\nPor Categoría de Falla en el Rival:")
    print(df_salida.group_by("categoria_falla_rival").len().sort("len", descending=True))

    print("\nPor Marca Rival Auditada:")
    print(df_salida.group_by("marca_competencia").len().sort("len", descending=True))
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
