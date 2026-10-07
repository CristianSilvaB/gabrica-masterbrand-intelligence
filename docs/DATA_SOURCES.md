# Matriz de Datos Reales — Gabrica Masterbrand

Este repositorio contiene extracciones automatizadas de datos públicos y de mercado para establecer la línea base real del ecosistema Gabrica en Colombia. No se utilizan datos sintéticos.

## Fuentes de Datos Activas

| ID Fuente | Origen Exacto | Método de Extracción | Indicador Estratégico | Frecuencia de Captura |
| :--- | :--- | :--- | :--- | :--- |
| **SRC-01** | **Google Trends (Colombia)** | API Oficial (`pytrends`) | Proxy de Notoriedad / Share of Voice (Gabrica vs Competencia) | Últimos 12 meses |
| **SRC-02** | **Laika Colombia (E-commerce)** | Web Scraping Headless (`Playwright`) | Catálogo real, precios de góndola y presencia de marcas de Gabrica | Tiempo Real (Scraping) |

## Metodología
* **Notoriedad:** Se mide el Índice de Interés de Búsqueda (0 a 100) en el territorio colombiano para comparar la tracción orgánica de las marcas hijas (ej. Simparica, Hill's) frente al sello corporativo (Gabrica) y sus competidores directos.
* **Góndola Digital:** Se extrae el HTML público del motor de búsqueda de retail especializado para auditar cómo se presentan los productos al consumidor final en Colombia.
