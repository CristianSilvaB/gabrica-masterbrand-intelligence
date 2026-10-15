import logging
import os
from pathlib import Path
from typing import Dict, List, Optional
import polars as pl
import requests
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(levelname)s] - %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("AnalisisInfluencersMetricas")

OUTPUT_FILE = Path("data/processed/19_embajadores_influencers_metricas.csv")
API_KEY = os.getenv("YOUTUBE_API_KEY")

# ==============================================================================
# CANALES CANDIDATOS EN COLOMBIA (DIVERSIFICADOS POR CATEGORÍA Y ENTORNO)
# ==============================================================================

CANALES_SEEDS = [
    # 1. LIFESTYLE CON MASCOTAS (DOMÉSTICO / HOGAR URBANO)
    {
        "nombre_creador": "Angie Pangie (@pangieoficial)",
        "query_search": "angie pangie pangieoficial",
        "categoria_perfil": "Lifestyle / Vlogs con Mascota",
        "entorno_mascota": "Doméstico / Hogar Urbano",
        "especies_visibles": "Caninos (Perros en vida familiar)",
        "afinidad_base_gabrica": 8.0,
        "marca_gabrica_afín": "Hill's Science Diet / Hydra Pet Spa / Plaisir",
        "enfoque_campaña": "Vlogs de vida cotidiana: 'Cómo viajo y cuido la salud y pelaje de mi perro en mis aventuras diarias'."
    },
    {
        "nombre_creador": "Planeta Juana",
        "query_search": "Planeta Juana colombia vlogs",
        "categoria_perfil": "Lifestyle / Vlogs con Mascota",
        "entorno_mascota": "Doméstico / Hogar Urbano",
        "especies_visibles": "Caninos y Felinos en familia",
        "afinidad_base_gabrica": 7.5,
        "marca_gabrica_afín": "Simparica Trio / Plaisir Snacks",
        "enfoque_campaña": "Storytelling familiar: 'Protegiendo a nuestros peludos en casa con pastillas que se comen como premios'."
    },

    # 2. FINCA / RURAL / EQUINOS (CAMPO, CABALLOS Y PERROS DE FINCA)
    {
        "nombre_creador": "Los Escachaítos",
        "query_search": "LOS ESCACHAITOS QUE VIVA EL CAMPO",
        "categoria_perfil": "Finca / Campo / Rural",
        "entorno_mascota": "Finca / Rural / Equinos",
        "especies_visibles": "Perros de campo, Caballos, Animales de granja",
        "afinidad_base_gabrica": 9.0,
        "marca_gabrica_afín": "Simparica (choque garrapata en campo) / Max / Agrocampo",
        "enfoque_campaña": "Vida rural auténtica: 'En el campo las garrapatas no perdonan: así protegemos a los perros bravos de finca'."
    },
    {
        "nombre_creador": "La Granja del Borrego",
        "query_search": "La Granja del Borrego campo colombia",
        "categoria_perfil": "Finca / Campo / Rural",
        "entorno_mascota": "Finca / Rural / Equinos",
        "especies_visibles": "Perros de granja, Caballos, Granja integral",
        "afinidad_base_gabrica": 8.5,
        "marca_gabrica_afín": "Simparica Trio / Bioseguridad y Salud Animal",
        "enfoque_campaña": "Educación campestre masiva: 'El cuidado diario de los animales de la granja y la desparasitación correcta'."
    },
    {
        "nombre_creador": "Criadero Doble Diamante (Paso Fino)",
        "query_search": "Criadero doble diamante caballos paso fino",
        "categoria_perfil": "Mundo Equino / Criadero de Finca",
        "entorno_mascota": "Finca / Rural / Equinos",
        "especies_visibles": "Equinos (Caballos de Paso) y Perros de Criadero",
        "afinidad_base_gabrica": 9.5,
        "marca_gabrica_afín": "Suplementos Articulares Zoetis / Salud Equina Agrocampo",
        "enfoque_campaña": "Excelencia equina: 'Cuidado de cascos, pelaje brillante y prevención antiparasitaria para ejemplares de exhibición'."
    },
    {
        "nombre_creador": "Criadero El Astro (Caballos)",
        "query_search": "Criadero el Astro caballos colombia",
        "categoria_perfil": "Mundo Equino / Criadero de Finca",
        "entorno_mascota": "Finca / Rural / Equinos",
        "especies_visibles": "Equinos de alta competencia y faena",
        "afinidad_base_gabrica": 9.0,
        "marca_gabrica_afín": "Líneas de Farmacia Equina Zoetis / Agrocampo",
        "enfoque_campaña": "Rendimiento y medicina veterinaria de grandes animales en pesebreras y potreros."
    },

    # 3. ESPECIALISTAS EN MASCOTAS / ADIESTRAMIENTO / ETOLOGÍA (DOMÉSTICO)
    {
        "nombre_creador": "Escuela Canina Colombiana",
        "query_search": "Escuela Canina Colombiana adiestramiento",
        "categoria_perfil": "Especialista Pet / Adiestramiento",
        "entorno_mascota": "Doméstico / Hogar Urbano",
        "especies_visibles": "Caninos de todas las razas",
        "afinidad_base_gabrica": 8.5,
        "marca_gabrica_afín": "Plaisir (refuerzo positivo) / Hill's Science Diet",
        "enfoque_campaña": "Educación y premios: 'Cómo educar a tu perro usando premios saludables que no engordan'."
    },
    {
        "nombre_creador": "Adiestramiento Canino Colombia",
        "query_search": "Adiestramiento canino Colombia perros",
        "categoria_perfil": "Especialista Pet / Comportamiento",
        "entorno_mascota": "Doméstico / Hogar Urbano",
        "especies_visibles": "Caninos urbanos en apartamentos",
        "afinidad_base_gabrica": 8.0,
        "marca_gabrica_afín": "Ferplast (correas/arneses) / Hill's Science Diet Treats",
        "enfoque_campaña": "Rito del Paseo Seguro: 'Paseos sin tirones y sin pulgas en los parques de la ciudad'."
    },
    {
        "nombre_creador": "Mark Lee (Educador Canino)",
        "query_search": "Mark Lee educador canino colombia",
        "categoria_perfil": "Especialista Pet / Comportamiento",
        "entorno_mascota": "Doméstico / Hogar Urbano",
        "especies_visibles": "Caninos urbanos y familias",
        "afinidad_base_gabrica": 8.5,
        "marca_gabrica_afín": "Hill's Science Diet / Hydra Spa",
        "enfoque_campaña": "Vínculo emocional: 'Solucionando problemas de conducta y asegurando nutrición científica en casa'."
    },

    # 4. MÉDICOS VETERINARIOS COLOMBIANOS (AUTORIDAD MÉDICA Y CLÍNICA)
    {
        "nombre_creador": "Dra. Karla Carpio (Tata . Veterinaria)",
        "query_search": "Tata . Veterinaria Karla Carpio colombia",
        "categoria_perfil": "Médico Veterinario / Divulgación",
        "entorno_mascota": "Doméstico / Hogar Urbano",
        "especies_visibles": "Caninos y Felinos en consulta clínica",
        "afinidad_base_gabrica": 10.0,
        "marca_gabrica_afín": "Hill's Prescription Diet / Simparica Trio / Apoquel",
        "enfoque_campaña": "Autoridad médica: 'Por qué no debes automedicar a tu mascota y cómo una dieta clínica previene enfermedades crónicas'."
    },
    {
        "nombre_creador": "Dr. Sala de Emergencias Veterinaria",
        "query_search": "Sala de Emergencias cardiologia veterinaria colombia",
        "categoria_perfil": "Médico Veterinario / Urgencias",
        "entorno_mascota": "Doméstico / Hogar Urbano",
        "especies_visibles": "Caninos y Felinos en hospitalización",
        "afinidad_base_gabrica": 10.0,
        "marca_gabrica_afín": "Hill's Prescription Diet k/d, c/d / Cytopoint",
        "enfoque_campaña": "Medicina intensiva y longevidad: 'Casos reales de pacientes salvados gracias a nutrición clínica y diagnóstico a tiempo'."
    },
    {
        "nombre_creador": "Veterinaria Práctica Colombia",
        "query_search": "veterinaria practica colombia perros gatos",
        "categoria_perfil": "Médico Veterinario / Consultorio",
        "entorno_mascota": "Doméstico / Hogar Urbano",
        "especies_visibles": "Caninos y Felinos en consulta preventiva",
        "afinidad_base_gabrica": 9.5,
        "marca_gabrica_afín": "Simparica Trio / Revolution Plus / Vacunas Zoetis",
        "enfoque_campaña": "Desparasitación sin riesgos: 'La diferencia entre un antiparasitario de farmacia veterinaria legal y uno genérico'."
    }
]


def buscar_canal_youtube(query: str, api_key: str) -> Optional[Dict]:
    """Busca el channelId oficial en YouTube."""
    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "part": "snippet",
        "q": query,
        "type": "channel",
        "maxResults": 1,
        "key": api_key
    }
    try:
        res = requests.get(url, params=params, timeout=10)
        data = res.json()
        items = data.get("items", [])
        if items:
            return {
                "channel_id": items[0]["id"]["channelId"],
                "titulo_oficial": items[0]["snippet"]["title"],
                "descripcion": items[0]["snippet"]["description"]
            }
    except Exception as e:
        logger.error(f"Error al buscar canal para '{query}': {e}")
    return None


def obtener_metricas_canal(channel_id: str, api_key: str) -> Optional[Dict]:
    """Obtiene suscriptores, playlist de uploads y métricas de videos recientes."""
    url = "https://www.googleapis.com/youtube/v3/channels"
    params = {
        "part": "contentDetails,statistics,snippet",
        "id": channel_id,
        "key": api_key
    }
    try:
        res = requests.get(url, params=params, timeout=10)
        data = res.json()
        items = data.get("items", [])
        if not items:
            return None

        channel = items[0]
        stats = channel.get("statistics", {})
        content_details = channel.get("contentDetails", {})
        uploads_playlist = content_details.get("relatedPlaylists", {}).get("uploads")

        subs = int(stats.get("subscriberCount", 0))
        total_views = int(stats.get("viewCount", 0))
        total_videos = int(stats.get("videoCount", 0))

        # Obtener métricas de los últimos 6 a 10 videos
        avg_views = 0
        avg_likes = 0
        avg_comments = 0

        if uploads_playlist:
            url_playlist = "https://www.googleapis.com/youtube/v3/playlistItems"
            params_pl = {
                "part": "contentDetails",
                "playlistId": uploads_playlist,
                "maxResults": 8,
                "key": api_key
            }
            res_pl = requests.get(url_playlist, params=params_pl, timeout=10).json()
            vid_ids = [it["contentDetails"]["videoId"] for it in res_pl.get("items", [])]

            if vid_ids:
                url_vids = "https://www.googleapis.com/youtube/v3/videos"
                params_vids = {
                    "part": "statistics",
                    "id": ",".join(vid_ids),
                    "key": api_key
                }
                res_vids = requests.get(url_vids, params=params_vids, timeout=10).json()

                views_list = []
                likes_list = []
                comments_list = []

                for v in res_vids.get("items", []):
                    st = v.get("statistics", {})
                    views_list.append(int(st.get("viewCount", 0)))
                    likes_list.append(int(st.get("likeCount", 0)))
                    comments_list.append(int(st.get("commentCount", 0)))

                if views_list:
                    avg_views = round(sum(views_list) / len(views_list))
                    avg_likes = round(sum(likes_list) / len(likes_list))
                    avg_comments = round(sum(comments_list) / len(comments_list))

        return {
            "suscriptores": subs,
            "total_vistas_canal": total_views,
            "total_videos": total_videos,
            "vistas_promedio": avg_views,
            "likes_promedio": avg_likes,
            "comentarios_promedio": avg_comments
        }
    except Exception as e:
        logger.error(f"Error al obtener métricas del canal '{channel_id}': {e}")
    return None


def clasificar_escala_influencer(subs: int) -> str:
    """Clasifica al creador en Macro, Mid, Micro o Nano según suscriptores."""
    if subs >= 250000:
        return "Macro-influencer (>250k)"
    elif subs >= 100000:
        return "Mid-tier (100k - 250k)"
    elif subs >= 10000:
        return "Micro-influencer (10k - 100k)"
    else:
        return "Nano-influencer (<10k)"


def calcular_costo_patrocinio_cop(escala: str, categoria: str, vistas_prom: int) -> int:
    """Estima el costo de una integración/mención en COP según benchmark publicitario en Colombia."""
    # CPM base en Colombia según categoría
    if "Veterinario" in categoria:
        cpm = 45000  # Mayor valor por autoridad médica
        piso = 1000000
    elif "Equino" in categoria or "Finca" in categoria:
        cpm = 28000
        piso = 800000
    elif "Especialista" in categoria:
        cpm = 35000
        piso = 900000
    else:  # Lifestyle
        cpm = 22000
        piso = 1200000 if "Macro" in escala else 600000

    costo_vistas = (vistas_prom / 1000) * cpm
    return max(piso, round(costo_vistas, -3))


def calcular_score_exito(er_pct: float, afinidad: float, vistas_prom: int) -> float:
    """Calcula el Score de Éxito de Comunicación (0 a 100)."""
    # 1. Componente ER (máximo 5% ER = 100 pts)
    norm_er = min(100.0, (er_pct / 4.0) * 100.0)
    # 2. Componente Afinidad (10 pts = 100 pts)
    norm_afinidad = (afinidad / 10.0) * 100.0
    # 3. Componente Alcance (vistas promedio)
    norm_alcance = min(100.0, (vistas_prom / 15000.0) * 100.0)

    score = (norm_afinidad * 0.40) + (norm_er * 0.35) + (norm_alcance * 0.25)
    return round(score, 1)


def dictaminar_veredicto(score: float, escala: str) -> str:
    if score >= 80.0:
        return "Altamente Rentable: Prioridad #1 de Patrocinio"
    elif score >= 65.0:
        return "Recomendado para Campaña Específica de Nicho"
    else:
        return "Evaluar solo para Campañas de Awareness Masivo"


def main():
    logger.info("🚀 Iniciando Auditoría y Evaluación de Embajadores/Influencers con YouTube API...")

    if not API_KEY:
        logger.error("❌ No se encontró YOUTUBE_API_KEY en el entorno. Revisa el archivo .env.")
        return

    resultados = []

    for seed in CANALES_SEEDS:
        nombre = seed["nombre_creador"]
        logger.info(f"🔍 Buscando canal: {nombre}...")

        canal_info = buscar_canal_youtube(seed["query_search"], API_KEY)
        if not canal_info:
            logger.warning(f"No se encontró canal para: {nombre}")
            continue

        ch_id = canal_info["channel_id"]
        metricas = obtener_metricas_canal(ch_id, API_KEY)
        if not metricas:
            logger.warning(f"No se pudieron obtener métricas para: {nombre}")
            continue

        subs = metricas["suscriptores"]
        vistas_prom = metricas["vistas_promedio"]
        likes_prom = metricas["likes_promedio"]
        comentarios_prom = metricas["comentarios_promedio"]

        # Engagement Rate
        er_pct = round(((likes_prom + comentarios_prom) / vistas_prom * 100), 2) if vistas_prom > 0 else 0.0

        escala = clasificar_escala_influencer(subs)
        costo_cop = calcular_costo_patrocinio_cop(escala, seed["categoria_perfil"], vistas_prom)
        score_roi = calcular_score_exito(er_pct, seed["afinidad_base_gabrica"], vistas_prom)
        veredicto = dictaminar_veredicto(score_roi, escala)

        fila = {
            "channel_id": ch_id,
            "nombre_creador": nombre,
            "titulo_canal_youtube": canal_info["titulo_oficial"],
            "escala_influencer": escala,
            "entorno_mascota": seed["entorno_mascota"],
            "categoria_perfil": seed["categoria_perfil"],
            "especies_visibles": seed["especies_visibles"],
            "suscriptores": subs,
            "vistas_totales_canal": metricas["total_vistas_canal"],
            "videos_totales": metricas["total_videos"],
            "vistas_promedio_recientes": vistas_prom,
            "likes_promedio": likes_prom,
            "comentarios_promedio": comentarios_prom,
            "engagement_rate_pct": er_pct,
            "costo_estimado_patrocinio_cop": costo_cop,
            "score_afinidad_gabrica": seed["afinidad_base_gabrica"],
            "score_exito_comunicacion": score_roi,
            "veredicto_patrocinio": veredicto,
            "marca_gabrica_recomendada": seed["marca_gabrica_afín"],
            "enfoque_campaña_recomendado": seed["enfoque_campaña"]
        }
        resultados.append(fila)

    df_salida = pl.DataFrame(resultados).sort("score_exito_comunicacion", descending=True)

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    df_salida.write_csv(OUTPUT_FILE)
    logger.info(f"✅ ¡Auditoría de Influencers finalizada! {df_salida.height} creadores evaluados en: {OUTPUT_FILE}")

    # Resumen en consola
    print("\n" + "=" * 90)
    print("🌟 RANKING DE INFLUENCERS & EMBAJADORES EVALUADOS (YOUTUBE DATA API V3)")
    print("=" * 90)
    print(df_salida.select([
        "nombre_creador", "escala_influencer", "entorno_mascota", "suscriptores",
        "vistas_promedio_recientes", "engagement_rate_pct", "costo_estimado_patrocinio_cop", "score_exito_comunicacion"
    ]))
    print("=" * 90 + "\n")


if __name__ == "__main__":
    main()
