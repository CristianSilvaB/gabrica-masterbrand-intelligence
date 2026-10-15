# Gabrica Masterbrand Intelligence 📊🐾

Este repositorio centraliza los scripts de extracción, limpieza y análisis de datos (Inteligencia de Mercado) orientados al sector de mascotas en Colombia (analizando marcas como Gabrica, Hills, Purina, Bravecto, Nexgard, etc.).

---

## 📁 Estructura de Scripts (`/scrapers`)

Esta carpeta contiene todos los motores de recolección y procesamiento.

1. **`01_real_trends.py`**: Se conecta a la API de Google Trends (`pytrends`) para extraer la notoriedad histórica y volumen de búsqueda de marcas corporativas y antiparasitarios en Colombia.
2. **`02_real_gondola.py`**: Un web scraper configurado con `cloudscraper` y `BeautifulSoup` que audita el portafolio en e-commerce de las marcas objetivo, extrayendo productos y precios publicados.
3. **`03_clean_flourish.py`**: Un script de limpieza con `Polars` que toma los datos crudos del scraper de góndola (02) y formatea los precios convirtiéndolos de cadenas de texto (ej. `"$45.228"`) a números enteros puros, dejándolos listos para importar a herramientas de visualización como Flourish.
4. **`04_tendencias_categoria.py`**: Similar al script 01, pero enfocado en las *macro-tendencias* del mercado en los últimos 5 años (analiza términos clave como "comida para perros", "dieta barf", "pet shop").
5. **`05_reviews_oficiales.py`**: Conecta con la **YouTube Data API v3** oficial para ejecutar una **extracción profunda y masiva**. Utiliza múltiples consultas y paginación para descargar decenas de miles de opiniones reales sobre 7 marcas objetivo (incluyendo Laika, Gabrica y Agrocampo).
6. **`08_analisis_cuantitativo.py`**: El motor de Inteligencia Artificial (NLP). Consolida automáticamente las opiniones masivas de **YouTube** (05) y las extracciones multicanal de **Apify** (11), ejecutando un motor de inferencia incremental con RoBERTa (`pysentimiento`) acelerado por GPU para clasificar polaridades (positivo, negativo, neutral) sin recomputar innecesariamente opiniones previas.
7. **`10_formato_flourish_financiero.py`**: Script de procesamiento con `Polars` que transforma los estados de resultados del dataset 09 (SIIS), pivoteando las ventas por año y precalculando participaciones de mercado y crecimiento anual para Flourish.
8. **`11_reviews_multicanal.py`**: Conecta con la API de **Apify** para ejecutar extracciones en la nube evadiendo bloqueos WAF/Cloudflare en 6 plataformas: **Mercado Libre, Amazon, TikTok, Facebook, Instagram y Reddit**, consolidando opiniones bajo el mismo formato analítico de YouTube.
9. **`12_analisis_sentimiento_gemini.py`**: Motor de Inteligencia Artificial cualitativa utilizando **Google Gemini** (`gemini-3.8-flash`). Incluye un **filtro semántico inteligente para YouTube** que descarta ruido, spam y contenido fuera de contexto (reduciendo de 93k comentarios a una muestra representativa y depurada en español sobre mascotas y veterinaria). Clasifica en lotes estructurados el sentimiento (`positivo`, `negativo`, `neutral`), extrae el tema central (`sabor/palatabilidad`, `salud digestiva`, `precio/costo`, etc.) y sintetiza un micro-resumen por reseña con soporte incremental de caché.

---

## 💾 Archivos de Datos (`/data/processed`)

Aquí residen los resultados listos para ser consumidos por tableros de BI, analistas o presentaciones.

- 📈 **`01_real_notoriedad_completa.csv`**: Base de datos de series de tiempo con el interés de búsqueda relativo de cada marca a lo largo del tiempo.
- 🛒 **`02_real_portafolio_masivo.csv`**: La base de datos cruda de productos encontrados en el e-commerce (nombres de producto, marca, precio en texto).
- ✨ **`03_flourish_ready_precios.csv`**: La versión ultra-limpia del archivo 02. Ideal para hacer gráficas de dispersión de precios o promedios en Flourish, PowerBI o Tableau.
- 📉 **`04_tendencias_categoria_5años.csv`**: Base de datos histórica con el comportamiento de términos genéricos de la industria de mascotas en Colombia.
- 🗣️ **`05_reviews_oficiales.csv`**: Un dataset puramente textual masivo (más de 93,000 filas). Contiene las columnas `fuente`, `objetivo` (marca) y `texto_opinion` extraídas tras la búsqueda profunda en YouTube.
- 🧠 **`08_reviews_cuantitativo.csv`**: El dataset definitivo de percepción consolidado (YouTube + Mercado Libre + Reddit + Instagram + TikTok + Facebook), enriquecido con 4 columnas calculadas por la IA: `sentimiento` (etiquetas claras: positivo, negativo, neutral), `prob_positivo`, `prob_negativo` y `prob_neutral`.
- 🏢 **`09_siis_financiero_veterinarias.csv`**: Estado de resultados y métricas financieras clave de los laboratorios y marcas. Datos oficiales consolidados a partir del portal SIIS de la Superintendencia de Sociedades.
- 📊 **`10_flourish_financiero.csv`**: Transformación del dataset 09 optimizada para Flourish. Incluye ventas pivoteadas por año (2022-2025) y métricas precalculadas de participación de mercado y crecimiento interanual.
- 🌐 **`11_reviews_multicanal.csv`**: Dataset complementario multicanal (Mercado Libre, Amazon, TikTok, Facebook, Instagram, Reddit) estructurado con el mismo esquema (`fuente`, `objetivo`, `texto_opinion`) listo para el modelo NLP.
- 🤖 **`12_reviews_gemini.csv`**: Dataset enriquecido con análisis cualitativo mediante Google Gemini. Incluye las columnas `fuente`, `objetivo`, `texto_opinion`, `sentimiento`, `tema` y `resumen`.

---

## 🔬 Benchmark de Inteligencia Artificial: RoBERTa Local vs. Google Gemini Flash (08 vs. 12)

El ecosistema cuenta con dos arquitecturas complementarias de análisis de percepción del consumidor para optimizar costos y profundidad analítica:

| Dimensión | RoBERTa Local (`08_analisis_cuantitativo.py`) | Google Gemini Cloud (`12_analisis_sentimiento_gemini.py`) |
| :--- | :--- | :--- |
| **Infraestructura** | 100% Local (Aceleración GPU/CUDA privada) | Cloud API Oficial (`gemini-3.5-flash-lite`) |
| **Coste / Cuota** | **$0.00 USD** (Ilimitado y sin conexión externa) | Ultra-económico (~$0.005 USD por base completa) |
| **Rendimiento** | **Ultra-rápido** (~100 opiniones/segundo) | Inferencia por lotes estructurados (~4 seg/lote) |
| **Salida Analítica** | Probabilidades estadísticas (`prob_pos`, `prob_neg`, `prob_neu`) | Polaridad + Categoría Temática (`tema`) + Resumen contextual |
| **Filtrado YouTube** | Ingesta masiva cruda completa (más de 93,000 opiniones) | Filtro semántico de alta relevancia en español (~5,200 candidatas) |

### 📊 Resultados de la Comparativa Cruzada (1,350 Opiniones Consolidadas):
* **Tasa de Concordancia Global:** **67.8%** (915 de 1,350 opiniones coincidieron unívocamente).
* **Captura de Matices Coloquiales:** Gemini reclasificó como **positivas** a 119 opiniones que RoBERTa catalogó como "neutral" (ej. *"Le encantó encima de la comida húmeda"*, *"A Peppa le encantó"*).
* **Detección Fina de Quejas:** Gemini detectó como **negativas** a 126 opiniones que RoBERTa catalogó como "neutral" (ej. *"Mi perro todavía se rasca y tiene pulgas"*, *"Efectivamente son sobres de 85g y no de 100g"*).
* **Identificación del "Por Qué" (Temas accionables):** Los temas negativos más frecuentes identificados por Gemini fueron *efectos secundarios* (49), *logística/entrega* (32), *pérdida de eficacia* (49) y *fecha de vencimiento* (23).
* **Supresión de Ruido y Falsos Positivos:** Gemini detectó y neutralizó menciones ajenas al sector mascotas (ej. críticas a películas o videojuegos homónimos del estudio *"Laika"*).

---

## 🔒 Seguridad (Git Ignore)

Todos los entornos virtuales (`.venv`), cachés (`__pycache__`), llaves de API (`.env`), pantallazos de depuración (`*.png`) y archivos de cookies (`ml_state.json`) están ignorados intencionalmente en este repositorio para evitar fugas de credenciales de seguridad.

