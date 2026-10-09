# Fuentes de Datos Oficiales y Metodología — Gabrica Masterbrand Intelligence

Este documento establece la procedencia exacta y los métodos tecnológicos utilizados para extraer, procesar y enriquecer los datos de mercado en el ecosistema de Gabrica Colombia. **Cero datos sintéticos; todos los volúmenes son extraídos de fuentes públicas reales y procesados con rigor.**

## 📊 Matriz de Extracción Activa

| ID | Origen Exacto | Método de Extracción / Librería | Indicador Estratégico | Salida (Dataset) |
| :--- | :--- | :--- | :--- | :--- |
| **01** | **Google Trends (CO)** | API Oficial (`pytrends`) | **Notoriedad (Share of Search):** Comparativa de interés de búsqueda entre marcas corporativas (Gabrica, Agrocampo) y antiparasitarios. | `01_real_notoriedad_completa.csv` |
| **02** | **Retail E-commerce** | Scraping HTTP (`cloudscraper` + `bs4`) | **Auditoría de Góndola Digital:** Mapeo de portafolio y captura de precios de productos publicados (Hills, Bravecto, etc.). | `02_real_portafolio_masivo.csv` |
| **03** | **Procesamiento Interno**| Limpieza Vectorizada (`polars`) | **Estandarización Financiera:** Sanitización de precios (conversión de string a integrales) lista para visualización. | `03_flourish_ready_precios.csv` |
| **04** | **Google Trends (CO)** | API Oficial (`pytrends`) | **Macro-Tendencias (5 años):** Evolución histórica del interés en categorías clave ("dieta barf", "pet shop", "veterinaria"). | `04_tendencias_categoria_5años.csv` |
| **05** | **YouTube Data API v3**| API Oficial (Búsqueda Profunda) | **Social Listening (Cualitativo):** Recolección masiva y paginada de miles de opiniones reales de usuarios sobre 7 marcas. | `05_reviews_oficiales.csv` |
| **08** | **Modelo NLP (RoBERTa)**| Inferencia IA Acelerada (GPU/CUDA) | **Análisis de Sentimiento (Cuantitativo):** Asignación estadística ultra-rápida (en lotes) de polaridad a más de 93k reseñas. | `08_reviews_cuantitativo.csv` |
| **09** | **Supersociedades (SIIS)** | Portal Oficial SIIS (https://siis.ia.supersociedades.gov.co/) | **Inteligencia Financiera Corporativa:** Estados de resultados (Ingresos, Costos, Ganancias) reportados legalmente por las empresas dueñas de las marcas. | `09_siis_financiero_veterinarias.csv` |

## 🛠️ Notas Metodológicas y de Seguridad Técnica

1. **Veracidad Geográfica:** Todos los scripts de Google Trends están anclados al territorio colombiano (`hl='es-CO'`, `tz=300`), lo que significa que el ruido de búsquedas de otros países de habla hispana está estrictamente filtrado.
2. **Defensas Anti-Bot y Scraping Ético:** 
   - El script **02** suplanta huellas de cliente con `cloudscraper` para evadir escudos básicos en las tiendas.
3. **Privacidad de Datos y Soporte GPU (NLP Local):** El análisis de sentimientos que califica las opiniones de los usuarios (script **08**) se ejecuta **100% de manera local**, utilizando aceleración por hardware de tu tarjeta gráfica (**GPU/CUDA**) para procesar masivamente grandes volúmenes de datos. No envía datos a servicios LLM externos de pago, garantizando absoluta privacidad y un entendimiento altísimo de la jerga y modismos latinos sin comprometer la propiedad del dataset.
4. **Compilación Financiera (Dataset 09):** La información financiera corporativa fue extraída de forma directa desde el Sistema de Información Integrada Societaria (SIIS) de la Superintendencia de Sociedades de Colombia. Estos datos duros fueron consolidados y transcritos a partir de reportes visuales compartidos internamente (capturas de pantalla/imágenes) y posteriormente estandarizados a nivel programático para permitir sumatorias y visualización vectorial.
