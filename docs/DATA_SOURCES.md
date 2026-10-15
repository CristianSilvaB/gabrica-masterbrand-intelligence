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
| **10** | **Procesamiento Interno** | Estandarización (`polars`) | **Modelado Financiero:** Ventas anuales pivoteadas y métricas de cuota de mercado optimizadas para Flourish. | `10_flourish_financiero.csv` |
| **11** | **Apify Cloud Platform**| Apify SDK (`apify-client`) | **Social Listening Multicanal:** Recolección en Mercado Libre, Amazon, TikTok, Facebook, Instagram y Reddit con evasión de antibots. | `11_reviews_multicanal.csv` |
| **12** | **Google Gemini LLM** | API Oficial (`gemini-3.5-flash-lite`) | **Análisis Cualitativo y Temático:** Detección de sentimiento (positivo/negativo/neutral), extracción del tema central (palatabilidad, empaque, eficacia) y síntesis en micro-resumen por reseña. | `12_reviews_gemini.csv` |
| **13** | **Portal Oficial Gabrica**| Web Scraping (`httpx` + `bs4`) | **Taxonomía de Catálogo y Competidores:** Mapeo de 57 variantes de marcas oficiales de Gabrica, categorías, especies y contrapartes rivales. | `13_catalogo_marcas_gabrica.csv` |
| **14** | **Minería de Texto Local**| Análisis Sintáctico (`polars` + regex)| **Motivaciones, Tensiones y Barreras:** Detección de patrones adversativos (*"Quiero X pero Y"*), disonancia veterinaria y barreras de precio. | `14_motivaciones_tensiones_barreras.csv` |
| **15** | **Minería Semiocultural** | Clasificación de Ritos (`polars` + regex)| **Ritos, Hábitos y Mitos:** Mapeo de los 4 ritos de cuidado animal (Paseo, Baño, Comida, Salud), mitos de dietas BARF y oportunidades de conquista. | `15_mitos_ritos_oportunidades.csv` |
| **16** | **Minería de Competencia**| Filtrado de Reseñas Críticas (`polars`) | **Verbatims de Dolor de la Competencia:** Base de más de 15,000 quejas en marcas rivales (Bravecto, Nexgard, Purina) con contra-argumentos de marketing. | `16_verbatims_dolores_competencia.csv` |

## 🛠️ Notas Metodológicas y de Seguridad Técnica

1. **Veracidad Geográfica:** Todos los scripts de Google Trends están anclados al territorio colombiano (`hl='es-CO'`, `tz=300`), lo que significa que el ruido de búsquedas de otros países de habla hispana está estrictamente filtrado.
2. **Defensas Anti-Bot y Scraping Ético:** 
   - El script **02** suplanta huellas de cliente con `cloudscraper` para evadir escudos básicos en las tiendas.
3. **Privacidad de Datos y Soporte GPU (NLP Local):** El análisis de sentimientos que califica las opiniones de los usuarios (script **08**) se ejecuta **100% de manera local**, utilizando aceleración por hardware de tu tarjeta gráfica (**GPU/CUDA**) para procesar masivamente grandes volúmenes de datos. No envía datos a servicios LLM externos de pago, garantizando absoluta privacidad y un entendimiento altísimo de la jerga y modismos latinos sin comprometer la propiedad del dataset.
4. **Compilación Financiera (Dataset 09):** La información financiera corporativa fue extraída de forma directa desde el Sistema de Información Integrada Societaria (SIIS) de la Superintendencia de Sociedades de Colombia. Estos datos duros fueron consolidados y transcritos a partir de reportes visuales compartidos internamente (capturas de pantalla/imágenes) y posteriormente estandarizados a nivel programático para permitir sumatorias y visualización vectorial.
5. **Modelado Financiero y KPIs para Flourish (Script 10 / Dataset 10):** Transforma la estructura contable del dataset 09 filtrando las cuentas de `Ingresos de actividades ordinarias`. Con `polars`, pivotea dinámicamente los años (2022 a 2025) en columnas temporales y calcula automáticamente los KPIs directos requeridos por los componentes gráficos de Flourish:
   - *Ventas del último año vs. Ventas de la competencia*.
   - *Participación de Mercado (%)*: Porcentaje que representa cada marca sobre el total del mercado auditado.
   - *Crecimiento Interanual de la Marca (%)* y *Crecimiento de la Categoría (%)*.
   - *Diagnóstico del Mercado*: Clasificación de tendencia global (`Creciendo` / `Decreciendo`).
6. **Social Listening Multicanal en la Nube (Script 11 / Dataset 11):** Utiliza la infraestructura de Apify para esquivar bloqueos antibot avanzados (Cloudflare/Akamai WAF) en 6 plataformas (Mercado Libre, Amazon, TikTok, Facebook, Instagram y Reddit), homologando todas las opiniones al esquema exacto `["fuente", "objetivo", "texto_opinion"]` compatible con el motor de NLP local (script **08**).
7. **Inferencia Inteligente con LLM Económico (Script 12 / Dataset 12):** Utiliza el modelo de última generación de bajo coste de Google (`gemini-3.8-flash`) vía requests estructurados por lotes (`batch_size=25` con `responseMimeType: "application/json"`). Proporciona capacidades de comprensión contextual semántica superiores para resumir opiniones y categorizar temas cualitativos específicos (ej. "sabor y palatabilidad", "efectos secundarios adversos", "fecha de vencimiento"), con un mecanismo incremental que ahorra llamadas a la API deduplicando opiniones previamente analizadas.

---

## 🔬 Estudio Comparativo de Modelos: RoBERTa Local (08) vs. Google Gemini Flash (12)

Para garantizar la máxima precisión en la toma de decisiones estratégicas de Gabrica, se implementó un benchmark continuo de doble validación entre el modelo supervisado local y el modelo generativo en la nube:

### 1. Matriz de Confusión Cruzada (Muestra Común Auditada: 1,350 Opiniones)

```text
┌────────────────────┬─────────────────┬──────────────────┬──────────────────┐
│ Gemini \ RoBERTa   ┆ RoBERTa Neutral ┆ RoBERTa Negativo ┆ RoBERTa Positivo │
╞════════════════════╪═════════════════╪══════════════════╪══════════════════╡
│ Gemini Positivo    ┆ 119             ┆ 33               ┆ 398 (Coincidencia)│
│ Gemini Negativo    ┆ 126             ┆ 334 (Coincidencia)┆ 11               │
│ Gemini Neutral     ┆ 183 (Coincidencia)┆ 105            ┆ 41               │
└────────────────────┴─────────────────┴──────────────────┴──────────────────┘
```

* **Concordancia Exacta:** **67.8%** (915/1,350 opiniones coinciden unívocamente).
* **Distribución por Marcas Principales:**
  * **Bravecto (443 op):** 164 Positivas / 220 Negativas / 59 Neutrales (Gemini detecta problemas puntuales de fecha de vencimiento y efectos secundarios).
  * **Purina (379 op):** 246 Positivas / 64 Negativas / 69 Neutrales (fuerte dominio positivo centrado en sabor y palatabilidad).
  * **Hills (136 op):** 52 Positivas / 38 Negativas / 46 Neutrales (balanceada en prescripción veterinaria y precio).
  * **Nexgard (108 op):** 26 Positivas / 54 Negativas / 28 Neutrales.
  * **Agrocampo (99 op):** 28 Positivas / 39 Negativas / 32 Neutrales.
  * **Laika (98 op):** 12 Positivas / 30 Negativas / 56 Neutrales (Gemini neutralizó falsos positivos homónimos ajenos a mascotas).
  * **Gabrica (87 op):** 22 Positivas / 26 Negativas / 39 Neutrales.

### 2. Cuadro Comparativo de Capacidades

| Criterio | RoBERTa Local (`pysentimiento`) | Google Gemini (`gemini-3.5-flash-lite`) |
| :--- | :--- | :--- |
| **Rol Estratégico** | **Minería Cuantitativa Masiva** (Big Data). | **Auditoría Cualitativa Profunda** (Insights accionables). |
| **Capacidad de Volumen** | Ilimitado (procesa 93,000+ reseñas en minutos). | Muestreo representativo controlado (~500 - 2,000 reseñas). |
| **Costo por Corrida** | $0.00 USD (Inferencia en hardware propio). | Fraccionario ($0.005 a $0.02 USD por lote auditado). |
| **Extracción Temática** | No (solo score numérico de polaridad). | **Sí:** Identifica drivers de insatisfacción (*vencimiento*, *vómitos*, *dureza*). |
| **Resumen Ejecutivo** | No. | **Sí:** Sintetiza la opinión del cliente en una frase concisa. |
| **Detección de Jerga y Slang** | Limitado al vocabulario del corpus de entrenamiento. | Excelente comprensión contextual de modismos y nombres de mascotas. |
| **Filtrado de Homónimos** | Asigna polaridad a todo texto sin validar contexto. | Detecta y neutraliza ruido externo (ej. estudios de cine o videojuegos homónimos). |

