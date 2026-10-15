import argparse
import html
import json
import logging
import os
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Dict, List, Optional

from dotenv import load_dotenv
import polars as pl

# Cargar variables de entorno (.env)
load_dotenv()

# Configurar logging profesional
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(levelname)s] - %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("AnalisisSentimientoGemini")

# Rutas y Constantes
INPUT_YOUTUBE = Path("data/processed/05_reviews_oficiales.csv")
INPUT_MULTICANAL = Path("data/processed/11_reviews_multicanal.csv")
OUTPUT_FILE = Path("data/processed/12_reviews_gemini.csv")
DEFAULT_MODEL = "gemini-3.5-flash-lite"


def get_gemini_api_key() -> str:
    """Valida y retorna la clave de API de Gemini."""
    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key or api_key.strip() == "" or "tu_" in api_key:
        logger.error(
            "❌ Clave de API de Gemini no configurada.\n"
            "Asegúrate de agregar GEMINI_API_KEY=\"tu_clave\" en tu archivo .env local."
        )
        sys.exit(1)
    return api_key.strip()


def call_gemini_batch(api_key: str, model: str, batch: List[Dict[str, any]], max_retries: int = 3) -> List[Dict[str, any]]:
    """Envía un lote de opiniones a Gemini y retorna su análisis estructurado en JSON."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
    
    prompt = f"""Eres un analista experto de Inteligencia de Mercado y Percepción del Consumidor en la industria de mascotas para Gabrica.
Analiza con rigor el sentimiento de cada una de las siguientes opiniones sobre productos de mascotas y extrae el tema central.

Reglas estrictas:
1. Responde ÚNICAMENTE con un arreglo JSON válido (array de objetos).
2. Cada objeto debe tener exactamente estos campos:
   - "id": el número de identificación recibido en la entrada.
   - "sentimiento": exactamente uno de los valores: "positivo", "negativo" o "neutral".
   - "tema": una categoría breve de 2-4 palabras que describa el aspecto evaluado (ejemplos: "sabor/palatabilidad", "salud digestiva", "precio/costo", "efectos secundarios", "logística/entrega", "recomendación veterinaria", "alergias/piel").
   - "resumen": síntesis de la opinión en máximo 10 palabras.

Opiniones a clasificar:
{json.dumps(batch, ensure_ascii=False)}"""

    payload = {
        "contents": [{"parts": [{"text": prompt}]}],
        "generationConfig": {
            "responseMimeType": "application/json",
            "temperature": 0.1
        }
    }

    data_bytes = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=data_bytes,
        headers={
            "Content-Type": "application/json",
            "x-goog-api-key": api_key
        }
    )

    for attempt in range(1, max_retries + 1):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                result_text = data["candidates"][0]["content"]["parts"][0]["text"].strip()
                parsed = json.loads(result_text)
                if isinstance(parsed, list):
                    return parsed
                elif isinstance(parsed, dict) and "opiniones" in parsed:
                    return parsed["opiniones"]
                else:
                    logger.warning(f"Formato inesperado de Gemini: {parsed}")
                    return []
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="ignore")
            logger.warning(f"Intento {attempt}/{max_retries} falló con HTTP {e.code}: {err_body[:200]}")
            if e.code == 429:
                wait_time = 25 * attempt
                logger.info(f"⏳ Pausa de enfriamiento por cuota (HTTP 429): esperando {wait_time}s...")
                time.sleep(wait_time)
            else:
                time.sleep(3)
        except Exception as e:
            logger.warning(f"Intento {attempt}/{max_retries} falló con error: {e}")
            time.sleep(2)

    logger.error(f"No fue posible procesar el lote tras {max_retries} intentos.")
    return []


# Patrones de filtrado semántico para YouTube (inteligencia de mercado para mascotas)
SPANISH_MARKERS = r'(?i)\b(el|la|los|las|un|una|de|del|en|y|que|con|por|para|mi|mis|su|sus|este|esta|al|es|son|muy|buen|bueno|buena|gracias|le|les|se|me|te|nos)\b'
ANIMATION_STUDIO_NOISE = r'(?i)\b(film|movie|cast|trailer|director|animation|character|actor|actress|coraline|kubo|stop[\s-]motion|cinema|theatre)\b'
PET_PATTERN = r'(?i)\b(perr[oas]|gat[oas]|mascot[as]|cachorr[oas]|canin[oas]|felin[oas]|pelud[oas])\b'
HEALTH_PATTERN = r'(?i)\b(veterinar|pulga|garrapata|parasit|dosis|recet|pastill|enferm|v[oó]mit|diarre|alerg|reacci[oó]n|s[ií]ntom|infecc|intoxic)\b'
PRODUCT_PATTERN = r'(?i)\b(alimento|comida|croqueta|pienso|pat[eé]|pepa|sabor|palatab|gust|rechaz|calidad|precio|costo|car[oa]|barat[oa]|compr|tienda|sirve|funciona|marca|efecto|resultado)\b'
BRAND_PATTERN = r'(?i)\b(hills|bravecto|nexgard|simparica|purina|pro\s?plan|gabrica|agrocampo|laika|royal|acana|orijen|credelio|revolution)\b'


def filtrar_opiniones_youtube(
    df_yt: pl.DataFrame,
    max_por_marca: Optional[int] = 100,
    min_chars: int = 40
) -> pl.DataFrame:
    """Filtra y depura los comentarios de YouTube para retener únicamente opiniones
    en español con alto valor semántico sobre mascotas, productos y salud veterinaria,
    eliminando ruido, spam y optimizando el consumo de la API de Gemini."""
    total_original = df_yt.height
    logger.info(f"🔍 Aplicando filtro inteligente a comentarios de YouTube ({total_original} comentarios originales)...")

    condicion_relevancia = (
        (pl.col("texto_opinion").str.len_chars() >= min_chars) &
        (pl.col("texto_opinion").str.contains(SPANISH_MARKERS)) &
        (~pl.col("texto_opinion").str.contains(ANIMATION_STUDIO_NOISE)) &
        (
            pl.col("texto_opinion").str.contains(BRAND_PATTERN) |
            (
                pl.col("texto_opinion").str.contains(PET_PATTERN) &
                (
                    pl.col("texto_opinion").str.contains(HEALTH_PATTERN) |
                    pl.col("texto_opinion").str.contains(PRODUCT_PATTERN)
                )
            )
        )
    )

    df_filtrado = df_yt.filter(condicion_relevancia)
    logger.info(f"-> {df_filtrado.height} comentarios pasaron el filtro semántico y de idioma en español.")

    if max_por_marca and max_por_marca > 0:
        # Priorizar comentarios con mayor riqueza y detalle (longitud del texto)
        df_filtrado = (
            df_filtrado.with_columns(
                pl.col("texto_opinion").str.len_chars().alias("_longitud")
            )
            .sort(["objetivo", "_longitud"], descending=[False, True])
            .group_by("objetivo", maintain_order=True)
            .head(max_por_marca)
            .drop("_longitud")
        )
        logger.info(f"-> Muestreo balanceado: {df_filtrado.height} comentarios seleccionados (máx {max_por_marca} por marca).")

    return df_filtrado.select(["fuente", "objetivo", "texto_opinion"])


def main():
    parser = argparse.ArgumentParser(
        description="Analizador de Sentimiento y Detección de Temas con Google Gemini para Gabrica Intelligence."
    )
    parser.add_argument(
        "--model",
        type=str,
        default=DEFAULT_MODEL,
        help=f"Modelo de Gemini a utilizar (por defecto: '{DEFAULT_MODEL}')."
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=25,
        help="Cantidad de opiniones enviadas por cada llamada a Gemini (ahorro de requests)."
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Límite máximo de opiniones nuevas a procesar en esta ejecución (opcional)."
    )
    parser.add_argument(
        "--solo-multicanal",
        action="store_true",
        help="Si se activa, solo analiza las opiniones de Mercado Libre, Reddit e Instagram (omite YouTube)."
    )
    parser.add_argument(
        "--youtube-max-per-brand",
        type=int,
        default=100,
        help="Máximo de comentarios de YouTube a seleccionar por marca tras el filtro semántico (por defecto: 100). Evita saturar la cuota de la API."
    )
    parser.add_argument(
        "--youtube-min-chars",
        type=int,
        default=40,
        help="Longitud mínima de caracteres para comentarios de YouTube (por defecto: 40)."
    )
    parser.add_argument(
        "--sin-filtro-youtube",
        action="store_true",
        help="Desactiva el filtro semántico de YouTube (no recomendado: consume cuota masiva)."
    )
    args = parser.parse_args()

    api_key = get_gemini_api_key()
    logger.info(f"🚀 Iniciando Clasificador de Sentimiento con Gemini ({args.model})...")

    # 1. Cargar fuentes de datos
    dfs_a_unir = []
    if not args.solo_multicanal and INPUT_YOUTUBE.exists():
        logger.info(f"Cargando dataset de YouTube: {INPUT_YOUTUBE}...")
        df_yt = pl.read_csv(INPUT_YOUTUBE)
        if not args.sin_filtro_youtube:
            df_yt = filtrar_opiniones_youtube(
                df_yt,
                max_por_marca=args.youtube_max_per_brand,
                min_chars=args.youtube_min_chars
            )
        else:
            logger.warning("⚠️ Filtro de YouTube desactivado por argumento CLI.")
        logger.info(f"-> {df_yt.height} reseñas preparadas de YouTube.")
        dfs_a_unir.append(df_yt)

    if INPUT_MULTICANAL.exists():
        logger.info(f"Cargando dataset Multicanal: {INPUT_MULTICANAL}...")
        df_multi = pl.read_csv(INPUT_MULTICANAL)
        logger.info(f"-> {df_multi.height} opiniones cargadas de Multicanal.")
        dfs_a_unir.append(df_multi)
    else:
        logger.warning(f"No se encontró el archivo multicanal en {INPUT_MULTICANAL}.")

    if not dfs_a_unir:
        logger.error("❌ No se encontraron datasets de opiniones para procesar.")
        sys.exit(1)

    # 2. Consolidar y deduplicar
    dfs_estandarizados = [df.select(["fuente", "objetivo", "texto_opinion"]) for df in dfs_a_unir]
    df_unificado = pl.concat(dfs_estandarizados).unique(
        subset=["fuente", "objetivo", "texto_opinion"]
    ).filter(
        (pl.col("texto_opinion").is_not_null()) &
        (pl.col("texto_opinion").str.strip_chars().str.len_chars() >= 12)
    )
    logger.info(f"Total opiniones únicas consolidadas: {df_unificado.height}")

    # 3. Manejo Incremental: Cache de análisis previos de Gemini
    cols_esperadas = ["fuente", "objetivo", "texto_opinion", "sentimiento", "tema", "resumen"]
    df_existente = None
    if OUTPUT_FILE.exists():
        try:
            df_existente = pl.read_csv(OUTPUT_FILE)
            logger.info(f"Dataset Gemini previo detectado con {df_existente.height} opiniones ya clasificadas.")
        except Exception as e:
            logger.warning(f"No se pudo leer archivo previo: {e}")

    if df_existente is not None and all(c in df_existente.columns for c in cols_esperadas):
        df_ya_analizado = df_unificado.join(
            df_existente.select(cols_esperadas),
            on=["fuente", "objetivo", "texto_opinion"],
            how="inner"
        )
        df_pendientes = df_unificado.join(
            df_existente.select(["fuente", "objetivo", "texto_opinion"]),
            on=["fuente", "objetivo", "texto_opinion"],
            how="anti"
        )
        logger.info(f"Reutilizando {df_ya_analizado.height} clasificaciones existentes de Gemini.")
        logger.info(f"Opiniones nuevas pendientes para Gemini: {df_pendientes.height}")
    else:
        df_ya_analizado = pl.DataFrame(schema={
            "fuente": pl.String, "objetivo": pl.String, "texto_opinion": pl.String,
            "sentimiento": pl.String, "tema": pl.String, "resumen": pl.String
        })
        df_pendientes = df_unificado

    if df_pendientes.height == 0:
        logger.info("✅ Todas las opiniones ya fueron analizadas previamente por Gemini.")
        sys.exit(0)

    # Aplicar límite si fue solicitado
    if args.limit and args.limit > 0:
        logger.info(f"Limitando la ejecución a las primeras {args.limit} opiniones pendientes.")
        df_pendientes = df_pendientes.head(args.limit)

    # 4. Procesamiento por Lotes con Gemini
    logger.info(f"Iniciando inferencia con Gemini en lotes de {args.batch_size} opiniones...")
    filas_pendientes = df_pendientes.to_dicts()
    nuevos_analisis: List[Dict[str, any]] = []

    total_lotes = (len(filas_pendientes) + args.batch_size - 1) // args.batch_size

    for i in range(0, len(filas_pendientes), args.batch_size):
        lote_filas = filas_pendientes[i : i + args.batch_size]
        lote_num = (i // args.batch_size) + 1
        
        # Preparar payload para Gemini
        lote_input = [
            {"id": idx, "texto": html.unescape(fila["texto_opinion"])[:300]}
            for idx, fila in enumerate(lote_filas)
        ]

        logger.info(f"Procesando lote {lote_num}/{total_lotes} ({len(lote_input)} opiniones)...")
        respuestas = call_gemini_batch(api_key, args.model, lote_input)
        
        if not respuestas:
            logger.warning(f"⚠️ Lote {lote_num} omitido temporalmente por límite o error de Gemini. Las opiniones permanecen pendientes para la próxima corrida.")
            time.sleep(10)
            continue

        # Mapear respuestas por ID
        resp_map = {r.get("id"): r for r in respuestas if "id" in r}

        for idx, fila in enumerate(lote_filas):
            res = resp_map.get(idx)
            if not res or not res.get("resumen"):
                continue  # Solo guardar si Gemini realmente analizó la opinión

            sent = str(res.get("sentimiento", "neutral")).lower()
            if sent not in ["positivo", "negativo", "neutral"]:
                sent = "neutral"

            nuevos_analisis.append({
                "fuente": fila["fuente"],
                "objetivo": fila["objetivo"],
                "texto_opinion": fila["texto_opinion"],
                "sentimiento": sent,
                "tema": str(res.get("tema", "general/otro")).strip(),
                "resumen": str(res.get("resumen", "")).strip()
            })

        # Guardar checkpoint periódico en disco cada 4 lotes (100 opiniones)
        if (lote_num % 4 == 0 or lote_num == total_lotes) and nuevos_analisis:
            try:
                df_parcial = pl.concat([
                    df_ya_analizado.select(cols_esperadas),
                    pl.DataFrame(nuevos_analisis).select(cols_esperadas)
                ]).unique(subset=["fuente", "objetivo", "texto_opinion"])
                OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
                df_parcial.write_csv(OUTPUT_FILE)
                logger.info(f"💾 Checkpoint guardado en disco ({df_parcial.height} opiniones acumuladas).")
            except Exception as e_ck:
                logger.warning(f"No se pudo guardar checkpoint: {e_ck}")

        # Pausa de cortesía para respetar rate limits de 15 RPM
        time.sleep(2.5)

    df_nuevos = pl.DataFrame(nuevos_analisis)

    # 5. Consolidar y Exportar
    df_consolidado = pl.concat([
        df_ya_analizado.select(cols_esperadas),
        df_nuevos.select(cols_esperadas)
    ]).unique(subset=["fuente", "objetivo", "texto_opinion"])

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    df_consolidado.write_csv(OUTPUT_FILE)
    logger.info(f"✅ ¡Éxito! Dataset enriquecido por Gemini guardado con {df_consolidado.height} filas en: {OUTPUT_FILE}")

    # --- Resumen Analítico en Consola ---
    print("\n" + "=" * 65)
    print("🤖 RESUMEN DE SENTIMIENTO GENERADO POR GEMINI")
    print("=" * 65)
    try:
        resumen_marca = df_consolidado.group_by(["objetivo", "sentimiento"]).len().sort(["objetivo", "sentimiento"])
        print(resumen_marca)
    except Exception as e:
        logger.error(f"Error generando resumen: {e}")

    print("\n" + "=" * 65)
    print("🏷️ TOP 10 TEMAS MÁS FRECUENTES DETECTADOS POR GEMINI")
    print("=" * 65)
    try:
        top_temas = df_consolidado.group_by("tema").len().sort("len", descending=True).head(10)
        print(top_temas)
    except Exception as e:
        logger.error(f"Error generando top temas: {e}")
    print("=" * 65 + "\n")


if __name__ == "__main__":
    main()
