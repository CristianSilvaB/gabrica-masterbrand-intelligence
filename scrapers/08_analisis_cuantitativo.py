import logging
from pathlib import Path
from typing import List

import polars as pl
from pysentimiento import create_analyzer

# Configurar logging profesional
logging.basicConfig(level=logging.INFO, format='%(asctime)s - [%(levelname)s] - %(name)s: %(message)s')
logger = logging.getLogger("AnalisisCuantitativoNLP")

def main():
    archivo_yt = Path("data/processed/05_reviews_oficiales.csv")
    archivo_multicanal = Path("data/processed/11_reviews_multicanal.csv")
    archivo_salida = Path("data/processed/08_reviews_cuantitativo.csv")
    
    dfs_a_consolidar: List[pl.DataFrame] = []
    
    # 1. Cargar YouTube si existe
    if archivo_yt.exists():
        logger.info(f"Cargando dataset oficial de YouTube: {archivo_yt}...")
        df_yt = pl.read_csv(archivo_yt)
        logger.info(f"-> {df_yt.height} reseñas cargadas de YouTube.")
        dfs_a_consolidar.append(df_yt)
    else:
        logger.warning(f"No se encontró el archivo de YouTube ({archivo_yt}).")

    # 2. Cargar Multicanal si existe
    if archivo_multicanal.exists():
        logger.info(f"Cargando dataset multicanal (Apify): {archivo_multicanal}...")
        df_multi = pl.read_csv(archivo_multicanal)
        logger.info(f"-> {df_multi.height} opiniones cargadas de multicanal.")
        dfs_a_consolidar.append(df_multi)
    else:
        logger.warning(f"No se encontró el archivo multicanal ({archivo_multicanal}).")

    if not dfs_a_consolidar:
        logger.error("❌ No hay datasets de entrada disponibles (ni 05 ni 11).")
        return

    # Consolidar y deduplicar opiniones de entrada
    df_unificado = pl.concat(dfs_a_consolidar).unique(
        subset=["fuente", "objetivo", "texto_opinion"]
    ).filter(
        (pl.col("texto_opinion").is_not_null()) &
        (pl.col("texto_opinion").str.strip_chars().str.len_chars() >= 10)
    )
    logger.info(f"Total opiniones únicas consolidadas a evaluar: {df_unificado.height}")

    # 3. Manejo Incremental Inteligente: Reutilizar clasificaciones ya calculadas
    df_existente = None
    if archivo_salida.exists():
        try:
            df_existente = pl.read_csv(archivo_salida)
            logger.info(f"Base cuantitativa previa detectada con {df_existente.height} opiniones ya clasificadas.")
        except Exception as e:
            logger.warning(f"No se pudo leer el archivo existente ({e}), se re-evaluará completo.")
            df_existente = None

    cols_esperadas = ["fuente", "objetivo", "texto_opinion", "sentimiento", "prob_positivo", "prob_negativo", "prob_neutral"]
    if df_existente is not None and all(c in df_existente.columns for c in cols_esperadas):
        # Reutilizar lo que ya tiene sentimiento y probabilidad
        df_ya_clasificado = df_unificado.join(
            df_existente.select(cols_esperadas),
            on=["fuente", "objetivo", "texto_opinion"],
            how="inner"
        )
        df_pendientes = df_unificado.join(
            df_existente.select(["fuente", "objetivo", "texto_opinion"]),
            on=["fuente", "objetivo", "texto_opinion"],
            how="anti"
        )
        logger.info(f"Reutilizando {df_ya_clasificado.height} clasificaciones existentes del archivo previo.")
        logger.info(f"Opiniones nuevas pendientes de inferencia NLP: {df_pendientes.height}")
    else:
        df_ya_clasificado = pl.DataFrame(schema={
            "fuente": pl.String, "objetivo": pl.String, "texto_opinion": pl.String,
            "sentimiento": pl.String, "prob_positivo": pl.Float64, "prob_negativo": pl.Float64, "prob_neutral": pl.Float64
        })
        df_pendientes = df_unificado

    # 4. Inferencia en Lote solo para las filas pendientes
    if df_pendientes.height > 0:
        textos_pendientes = df_pendientes["texto_opinion"].to_list()
        textos_limpios = [str(t) if t is not None else "" for t in textos_pendientes]
        
        logger.info("Cargando modelo NLP en español (RoBERTa - pysentimiento)...")
        analyzer = create_analyzer(task="sentiment", lang="es")
        
        logger.info(f"Inferenciando sentimiento para {len(textos_limpios)} reseñas nuevas...")
        resultados = analyzer.predict(textos_limpios)
        
        mapa_sentimientos = {"POS": "positivo", "NEG": "negativo", "NEU": "neutral"}
        etiquetas = [mapa_sentimientos.get(res.output, res.output) for res in resultados]
        prob_pos = [round(float(res.probas.get("POS", 0.0)), 3) for res in resultados]
        prob_neg = [round(float(res.probas.get("NEG", 0.0)), 3) for res in resultados]
        prob_neu = [round(float(res.probas.get("NEU", 0.0)), 3) for res in resultados]
        
        df_recien_clasificado = df_pendientes.with_columns([
            pl.Series("sentimiento", etiquetas),
            pl.Series("prob_positivo", prob_pos),
            pl.Series("prob_negativo", prob_neg),
            pl.Series("prob_neutral", prob_neu),
        ]).select(cols_esperadas)
    else:
        logger.info("Todas las opiniones ya estaban clasificadas. No se requiere nueva inferencia.")
        df_recien_clasificado = pl.DataFrame(schema={c: df_ya_clasificado.schema[c] for c in cols_esperadas})

    # 5. Consolidar el resultado final
    df_final = pl.concat([df_ya_clasificado.select(cols_esperadas), df_recien_clasificado.select(cols_esperadas)]).unique(
        subset=["fuente", "objetivo", "texto_opinion"]
    )
    
    archivo_salida.parent.mkdir(parents=True, exist_ok=True)
    df_final.write_csv(archivo_salida)
    logger.info(f"✅ ¡Éxito! Dataset cuantitativo consolidado guardado con {df_final.height} filas en {archivo_salida}")

    # --- Resúmenes Analíticos ---
    print("\n" + "="*65)
    print("📊 RESUMEN DE SENTIMIENTO POR MARCA (CONSOLIDADO MULTICANAL)")
    print("="*65)
    try:
        resumen_marca = df_final.group_by(["objetivo", "sentimiento"]).len().sort(["objetivo", "sentimiento"])
        print(resumen_marca)
    except Exception as e:
        logger.error(f"Error generando resumen por marca: {e}")

    print("\n" + "="*65)
    print("🌐 DISTRIBUCIÓN DE SENTIMIENTOS POR FUENTE DE DATOS")
    print("="*65)
    try:
        resumen_fuente = df_final.group_by(["fuente", "sentimiento"]).len().sort(["fuente", "sentimiento"])
        print(resumen_fuente)
    except Exception as e:
        logger.error(f"Error generando resumen por fuente: {e}")
    print("="*65 + "\n")

if __name__ == "__main__":
    main()