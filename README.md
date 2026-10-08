# Gabrica Masterbrand Intelligence 📊🐾

Este repositorio centraliza los scripts de extracción, limpieza y análisis de datos (Inteligencia de Mercado) orientados al sector de mascotas en Colombia (analizando marcas como Gabrica, Hills, Purina, Bravecto, Nexgard, etc.).

---

## 📁 Estructura de Scripts (`/scrapers`)

Esta carpeta contiene todos los motores de recolección y procesamiento.

1. **`01_real_trends.py`**: Se conecta a la API de Google Trends (`pytrends`) para extraer la notoriedad histórica y volumen de búsqueda de marcas corporativas y antiparasitarios en Colombia.
2. **`02_real_gondola.py`**: Un web scraper configurado con `cloudscraper` y `BeautifulSoup` que audita el portafolio en e-commerce de las marcas objetivo, extrayendo productos y precios publicados.
3. **`03_clean_flourish.py`**: Un script de limpieza con `Polars` que toma los datos crudos del scraper de góndola (02) y formatea los precios convirtiéndolos de cadenas de texto (ej. `"$45.228"`) a números enteros puros, dejándolos listos para importar a herramientas de visualización como Flourish.
4. **`04_tendencias_categoria.py`**: Similar al script 01, pero enfocado en las *macro-tendencias* del mercado en los últimos 5 años (analiza términos clave como "comida para perros", "dieta barf", "pet shop").
5. **`05_reviews_oficiales.py`**: Conecta con la **YouTube Data API v3** oficial para buscar videos sobre las marcas principales y extraer de manera limpia y legal los comentarios y opiniones públicas de los usuarios.
6. **`06_reviews_ecommerce.py`**: Un pipeline asíncrono construido con **Playwright**. Navega por Mercado Libre, Laika y Amazon buscando extraer comentarios de compradores. Incluye tácticas avanzadas como inyección de cookies (`ml_state.json`) para evadir muros de login, pausas aleatorias y modo de depuración forense mediante pantallazos.
7. **`08_analisis_cuantitativo.py`**: El motor de Inteligencia Artificial (NLP). Toma las reseñas en texto, descarga un modelo pre-entrenado (RoBERTa vía `pysentimiento`), e infiere en bloque (batch) la probabilidad matemática de que cada comentario sea Positivo, Negativo o Neutral.

---

## 💾 Archivos de Datos (`/data/processed`)

Aquí residen los resultados listos para ser consumidos por tableros de BI, analistas o presentaciones.

- 📈 **`01_real_notoriedad_completa.csv`**: Base de datos de series de tiempo con el interés de búsqueda relativo de cada marca a lo largo del tiempo.
- 🛒 **`02_real_portafolio_masivo.csv`**: La base de datos cruda de productos encontrados en el e-commerce (nombres de producto, marca, precio en texto).
- ✨ **`03_flourish_ready_precios.csv`**: La versión ultra-limpia del archivo 02. Ideal para hacer gráficas de dispersión de precios o promedios en Flourish, PowerBI o Tableau.
- 📉 **`04_tendencias_categoria_5años.csv`**: Base de datos histórica con el comportamiento de términos genéricos de la industria de mascotas en Colombia.
- 🗣️ **`05_reviews_oficiales.csv`**: Un dataset puramente textual. Contiene las columnas `fuente`, `objetivo` (marca) y `texto_opinion` obtenidas de redes oficiales (YouTube).
- 🧠 **`08_reviews_cuantitativo.csv`**: El dataset definitivo de percepción. Es el mismo archivo 05, pero enriquecido con 4 nuevas columnas de Inteligencia Artificial: `sentimiento` (etiqueta final), `prob_positivo`, `prob_negativo` y `prob_neutral` (puntajes del 0 al 1).

---

## 🔒 Seguridad (Git Ignore)

Todos los entornos virtuales (`.venv`), cachés (`__pycache__`), llaves de API (`.env`), pantallazos de depuración (`*.png`) y archivos de cookies (`ml_state.json`) están ignorados intencionalmente en este repositorio para evitar fugas de credenciales de seguridad.
