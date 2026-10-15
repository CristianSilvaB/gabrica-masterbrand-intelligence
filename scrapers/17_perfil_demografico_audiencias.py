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
logger = logging.getLogger("PerfilDemograficoAudiencias")

INPUT_08 = Path("data/processed/08_reviews_cuantitativo.csv")
INPUT_12 = Path("data/processed/12_reviews_gemini.csv")
OUTPUT_FILE = Path("data/processed/17_perfil_demografico_audiencias.csv")

# Mapeo de Geografías en Colombia
CIUDADES_COLOMBIA = [
    ("Bogotá D.C. / Cundinamarca", r'(?i)\b(bogot[aá]|soacha|ch[ií]a|cajic[aá]|cundinamarca)\b'),
    ("Medellín / Antioquia", r'(?i)\b(medell[ií]n|envigado|bello|itag[uü][ií]|antioquia|paisa)\b'),
    ("Cali / Valle del Cauca", r'(?i)\b(cali|valle del cauca|palmira|yumbo|buenaventura)\b'),
    ("Barranquilla / Costa Caribe", r'(?i)\b(barranquilla|soledad|atl[aá]ntico|cartagena|santa marta|valledupar|monter[ií]a)\b'),
    ("Bucaramanga / Santanderes", r'(?i)\b(bucaramanga|floridablanca|gir[oó]n|santander|c[uú]cuta)\b'),
    ("Eje Cafetero", r'(?i)\b(pereira|manizales|armenia|caldas|risaralda|quind[ií]o)\b'),
    ("Otras Regiones Colombia", r'(?i)\b(ibagu[eé]|villavicencio|pasto|popay[aá]n|neiva|sincelejo|tunja|colombia)\b')
]

# Tipos de Mascota
REGEX_MULTI = re.compile(r'(?i)\b(perr[oas].*?gat[oas]|gat[oas].*?perr[oas])\b')
REGEX_CANINO = re.compile(r'(?i)\b(perr[oas]|cachorr[oas]|canin[oas]|pelud[oas]|canino)\b')
REGEX_FELINO = re.compile(r'(?i)\b(gat[oas]|felin[oas]|michi|minino|felino)\b')

# Rescate y Fundaciones
REGEX_RESCATE = re.compile(r'(?i)\b(fundaci[oó]n|rescatad[oa]|adopci[oó]n|adopt[eé]|adoptad[oa]|callejero|refugio|albergue|esterilizaci[oó]n|hogar de paso)\b')


def detectar_ciudad(texto: str) -> str:
    for region, regex in CIUDADES_COLOMBIA:
        if re.search(regex, texto):
            return region
    return "Colombia (Territorio Nacional / Sin Ciudad Explícita)"


def detectar_mascota(texto: str) -> str:
    if REGEX_MULTI.search(texto):
        return "Multimascota (Perro y Gato)"
    elif REGEX_CANINO.search(texto):
        return "Canino (Perro)"
    elif REGEX_FELINO.search(texto):
        return "Felino (Gato)"
    return "Mascota General"


def clasificar_perfil_usuario(marca: str, texto: str, sentimiento: str) -> Dict[str, str]:
    es_gabrica = marca in ["Gabrica", "Hills"]
    es_rescate = bool(REGEX_RESCATE.search(texto))
    longitud = len(texto.strip())

    # 1. Segmento: Comunidad Pet-Lover / Rescate y Fundaciones
    if es_rescate:
        return {
            "segmento_estrategico": "Comunidad Pet-Lover / Rescatistas y Fundaciones",
            "afinidad_declarada": "Bienestar animal, rescate, adopción y salud preventiva",
            "potencial_embajador": "Alto (Líder de Opinión en Comunidad)",
            "accion_recomendada_gabrica": "Programa de apadrinamiento con marcas masivas (Max, Guaumor) y donación de desparasitantes en jornadas de adopción."
        }

    # 2. Segmento: Embajador Potencial / Vocero de Marca
    if es_gabrica and sentimiento == "positivo" and longitud >= 90:
        return {
            "segmento_estrategico": "Embajador Potencial / Vocero Orgánico",
            "afinidad_declarada": "Alta satisfacción con nutrición clínica y respaldo Gabrica/Hill's",
            "potencial_embajador": "Muy Alto (Candidato a Micro-influencer)",
            "accion_recomendada_gabrica": "Contactar para testimoniales de caso de éxito y co-creación de contenido para redes sociales."
        }

    # 3. Segmento: Fuga de Categoría / Cross-Selling
    # Usuario que interactúa con Hill's pero tiene dolor o queja de antiparasitarios o aseo
    if es_gabrica and any(w in texto.lower() for w in ["pulga", "garrapata", "baño", "shampoo", "arena"]):
        return {
            "segmento_estrategico": "Fuga de Categoría / Cross-Selling Gabrica",
            "afinidad_declarada": "Consume marca Gabrica pero tiene necesidades descubiertas en Farma o Aseo",
            "potencial_embajador": "Medio (Cliente Activo Expandible)",
            "accion_recomendada_gabrica": "Impactar con campañas de producto cruzado (Simparica Trio para nutrición Hill's; Hydra para cuidado estético)."
        }

    # 4. Segmento: Prospecto Conquistable de la Competencia
    if not es_gabrica:
        sub_dolor = "con queja activa" if sentimiento == "negativo" else "consumidor habitual"
        return {
            "segmento_estrategico": f"Prospecto de la Competencia ({marca})",
            "afinidad_declarada": f"Usuario en ecosistema rival ({marca}) - {sub_dolor}",
            "potencial_embajador": "Objetivo de Conversión",
            "accion_recomendada_gabrica": f"Pauta segmentada resolviendo los dolores de {marca} (garantía de tolerancia digestiva y palatabilidad superior)."
        }

    # 5. Segmento General
    return {
        "segmento_estrategico": "Consumidor General del Mercado",
        "afinidad_declarada": "Interés en cuidado de mascotas y nutrición",
        "potencial_embajador": "Estándar",
        "accion_recomendada_gabrica": "Campañas de awareness y educación sobre nutrición y salud veterinaria preventiva."
    }


def main():
    logger.info("🚀 Iniciando Perfilamiento Demográfico y Mapeo de Audiencias (Costo $0 USD)...")

    dfs = []
    if INPUT_08.exists():
        df_08 = pl.read_csv(INPUT_08)
        dfs.append(df_08.select(["fuente", "objetivo", "texto_opinion", "sentimiento"]))

    if INPUT_12.exists():
        df_12 = pl.read_csv(INPUT_12)
        dfs.append(df_12.select(["fuente", "objetivo", "texto_opinion", "sentimiento"]))

    df_total = pl.concat(dfs).unique(subset=["fuente", "objetivo", "texto_opinion"]).filter(
        pl.col("texto_opinion").str.strip_chars().str.len_chars() >= 35
    )

    logger.info(f"Total opiniones sustantivas para perfilamiento demográfico: {df_total.height:,}")

    filas_demograficas = []
    for fila in df_total.iter_rows(named=True):
        texto = fila["texto_opinion"]
        ciudad = detectar_ciudad(texto)
        mascota = detectar_mascota(texto)
        perfil = clasificar_perfil_usuario(fila["objetivo"], texto, fila["sentimiento"])

        filas_demograficas.append({
            "fuente": fila["fuente"],
            "marca_interaccion": fila["objetivo"],
            "sentimiento": fila["sentimiento"],
            "tipo_mascota": mascota,
            "ubicacion_geografica": ciudad,
            "segmento_estrategico": perfil["segmento_estrategico"],
            "afinidad_declarada": perfil["afinidad_declarada"],
            "potencial_embajador": perfil["potencial_embajador"],
            "accion_recomendada_gabrica": perfil["accion_recomendada_gabrica"],
            "texto_opinion": texto
        })

    df_resultado = pl.DataFrame(filas_demograficas).unique(subset=["fuente", "marca_interaccion", "texto_opinion"])

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    df_resultado.write_csv(OUTPUT_FILE)
    logger.info(f"✅ ¡Perfilamiento demográfico finalizado! {df_resultado.height:,} audiencias mapeadas en: {OUTPUT_FILE}")

    # Resumen en consola
    print("\n" + "=" * 70)
    print("👥 RESUMEN DE PERFIL DEMOGRÁFICO Y SEGMENTACIÓN DE AUDIENCIAS")
    print("=" * 70)
    print("\nPor Segmento Estratégico:")
    print(df_resultado.group_by("segmento_estrategico").len().sort("len", descending=True))

    print("\nPor Tipo de Mascota:")
    print(df_resultado.group_by("tipo_mascota").len().sort("len", descending=True))

    print("\nPor Ubicación Geográfica Detectada:")
    print(df_resultado.filter(pl.col("ubicacion_geografica") != "Colombia (Territorio Nacional / Sin Ciudad Explícita)").group_by("ubicacion_geografica").len().sort("len", descending=True))

    print("\nPor Potencial de Embajador / Vocero:")
    print(df_resultado.group_by("potencial_embajador").len().sort("len", descending=True))
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
