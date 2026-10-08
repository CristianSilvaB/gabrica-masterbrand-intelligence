import logging
from pathlib import Path

import polars as pl
from pysentimiento import create_analyzer

# Configurar logging para un output más profesional
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def main():
    archivo_entrada = Path("data/processed/05_reviews_oficiales.csv")
    archivo_salida = Path("data/processed/08_reviews_cuantitativo.csv")
    
    if not archivo_entrada.exists():
        logger.error(f"El archivo {archivo_entrada} no existe. Corre primero el script 05.")
        return

    # Cargar datos
    df = pl.read_csv(archivo_entrada)
    if df.height == 0:
        logger.error("El DataFrame está vacío. No hay reseñas para procesar.")
        return

    # Extraer textos como lista para procesamiento por lotes 
    # (El procesamiento Batch es muchísimo más rápido que iterar fila por fila)
    textos = df["texto_opinion"].to_list()

    logger.info("Cargando modelo NLP en español (RoBERTa - pysentimiento)...")
    # Este proceso descarga los pesos del modelo si es la primera vez que se ejecuta
    analyzer = create_analyzer(task="sentiment", lang="es")

    logger.info(f"Evaluando el sentimiento de {len(textos)} reseñas en lote. Esto será rápido...")
    
    # Predecir en bloque
    resultados = analyzer.predict(textos)
    
    # Extraer etiquetas y probabilidades detalladas
    etiquetas = [res.output for res in resultados]
    prob_pos = [res.probas.get("POS", 0.0) for res in resultados]
    prob_neg = [res.probas.get("NEG", 0.0) for res in resultados]
    prob_neu = [res.probas.get("NEU", 0.0) for res in resultados]

    # Añadir nuevas columnas al DataFrame de manera vectorizada y ultra-eficiente
    df_cuantitativo = df.with_columns([
        pl.Series("sentimiento", etiquetas),
        pl.Series("prob_positivo", prob_pos).round(3),
        pl.Series("prob_negativo", prob_neg).round(3),
        pl.Series("prob_neutral", prob_neu).round(3),
    ])

    # Exportar el resultado
    archivo_salida.parent.mkdir(parents=True, exist_ok=True)
    df_cuantitativo.write_csv(archivo_salida)
    logger.info(f"¡Proceso completado! Análisis guardado en {archivo_salida}")

    # --- Resumen Analítico Limpio ---
    print("\n" + "="*50)
    print("📊 RESUMEN DE SENTIMIENTO POR MARCA")
    print("="*50)
    
    # Crear una tabla pivote para visualizar la percepción global de cada marca
    # Nota: polars en versiones recientes usa pivot, comprobamos compatibilidad
    try:
        resumen = df_cuantitativo.pivot(
            values="texto_opinion",
            index="objetivo",
            columns="sentimiento",
            aggregate_function="len"
        ).fill_null(0)
        print(resumen)
    except Exception as e:
        # Alternativa robusta usando group_by
        resumen_alternativo = df_cuantitativo.group_by(["objetivo", "sentimiento"]).len().sort(["objetivo", "sentimiento"])
        print(resumen_alternativo)
        
    print("="*50)

if __name__ == "__main__":
    main()