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
7. **`08_analisis_cuantitativo.py`**: El motor de Inteligencia Artificial (NLP). Descarga un modelo pre-entrenado (RoBERTa vía `pysentimiento`) e infiere en bloque usando **aceleración por tarjeta gráfica (GPU)** para procesar y clasificar masivamente casi 100,000 comentarios como positivo, negativo o neutral en cuestión de minutos.

---

## 💾 Archivos de Datos (`/data/processed`)

Aquí residen los resultados listos para ser consumidos por tableros de BI, analistas o presentaciones.

- 📈 **`01_real_notoriedad_completa.csv`**: Base de datos de series de tiempo con el interés de búsqueda relativo de cada marca a lo largo del tiempo.
- 🛒 **`02_real_portafolio_masivo.csv`**: La base de datos cruda de productos encontrados en el e-commerce (nombres de producto, marca, precio en texto).
- ✨ **`03_flourish_ready_precios.csv`**: La versión ultra-limpia del archivo 02. Ideal para hacer gráficas de dispersión de precios o promedios en Flourish, PowerBI o Tableau.
- 📉 **`04_tendencias_categoria_5años.csv`**: Base de datos histórica con el comportamiento de términos genéricos de la industria de mascotas en Colombia.
- 🗣️ **`05_reviews_oficiales.csv`**: Un dataset puramente textual masivo (más de 93,000 filas). Contiene las columnas `fuente`, `objetivo` (marca) y `texto_opinion` extraídas tras la búsqueda profunda en YouTube.
- 🧠 **`08_reviews_cuantitativo.csv`**: El dataset definitivo de percepción. Es el mismo archivo masivo 05, pero enriquecido con 4 nuevas columnas calculadas por la IA: `sentimiento` (etiquetas claras: positivo, negativo, neutral), `prob_positivo`, `prob_negativo` y `prob_neutral`.
- 🏢 **`09_siis_financiero_veterinarias.csv`**: Estado de resultados y métricas financieras clave de los laboratorios y marcas. Datos oficiales consolidados a partir del portal SIIS de la Superintendencia de Sociedades.

---

## 🔒 Seguridad (Git Ignore)

Todos los entornos virtuales (`.venv`), cachés (`__pycache__`), llaves de API (`.env`), pantallazos de depuración (`*.png`) y archivos de cookies (`ml_state.json`) están ignorados intencionalmente en este repositorio para evitar fugas de credenciales de seguridad.
- 📊 **`10_flourish_financiero.csv`**: Transformación del dataset 09 optimizada para Flourish. Incluye ventas pivoteadas por año (2022-2025) y métricas precalculadas de participación de mercado y crecimiento interanual.
