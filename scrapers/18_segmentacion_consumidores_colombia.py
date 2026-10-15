import logging
from pathlib import Path
import polars as pl

# Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [%(levelname)s] - %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger("SegmentacionConsumidoresColombia")

OUTPUT_FILE = Path("data/processed/18_segmentacion_consumidores_colombia.csv")

# ==============================================================================
# DATOS DE SEGMENTACIÓN ESTRUCTURADA: DANE, FENALCO, MINSALUD & MERCADO GABRICA
# ==============================================================================

SEGMENTOS = [
    {
        "id_segmento": "SEG-01",
        "nombre_segmento": "Tutores DINK / 'Hijos de 4 Patas'",
        "entorno_vida": "Doméstico / Hogar Urbano",
        "especies_a_cargo": "Caninos pequeños/medianos (French Poodle, Bulldog, Pomerania) y Felinos Indoor",
        "perfil_sociodemografico": "Parejas jóvenes profesionales sin hijos (25 a 42 años) y solteros de ingresos medios-altos",
        "estrato_predominante": "Estratos 4, 5 y 6",
        "ciudades_foco": "Bogotá (Usaquén, Chapinero), Medellín (El Poblado, Laureles), Cali (Oeste, Ciudad Jardín), Barranquilla (Norte)",
        "penetracion_estimada_pct": 24.5,
        "gasto_mensual_min_cop": 300000,
        "gasto_mensual_max_cop": 950000,
        "gasto_mensual_promedio_cop": 550000,
        "drivers_de_compra": "Humanización extrema, prevención médica proactiva, bienestar holístico, estética y moda pet",
        "barreras_frecuentes": "Falta de tiempo entre semana, desinformación sobre dietas comerciales vs BARF, ansiedad por separación",
        "marcas_clave_gabrica": "Hill's Science Diet / Prescription Diet, Hydra Pet Spa, Plaisir (patés gourmet), Simparica Trio",
        "estrategia_comunicacion_masterbrand": "Posicionar a Gabrica como el 'Garante de Longevidad': 'Dale a tu hijo de 4 patas la mejor nutrición celular y medicina preventiva para que viva 15+ años contigo'.",
        "canal_compra_habitual": "Clínicas veterinarias premium de barrio, pet shops boutique y delivery programado"
    },
    {
        "id_segmento": "SEG-02",
        "nombre_segmento": "Familia Multiespecie Tradicional",
        "entorno_vida": "Doméstico / Hogar Urbano",
        "especies_a_cargo": "Caninos medianos/grandes (Criollos adoptados, Golden, Labradores) y ocasionalmente 1 felino",
        "perfil_sociodemografico": "Hogares biparentales con 1 a 3 hijos en edad escolar o adolescentes",
        "estrato_predominante": "Estratos 2, 3 y 4",
        "ciudades_foco": "Bogotá (Suba, Kennedy, Engativá), Medellín (Bello, Envigado), Cali (Sur, Oriente), Bucaramanga, Pereira, Ibagué",
        "penetracion_estimada_pct": 36.0,
        "gasto_mensual_min_cop": 120000,
        "gasto_mensual_max_cop": 320000,
        "gasto_mensual_promedio_cop": 210000,
        "drivers_de_compra": "Rendimiento del concentrado (bultos grandes 15-22kg), palatabilidad que le guste a la mascota, protección básica de salud",
        "barreras_frecuentes": "Sensibilidad al precio y alzas inflacionarias, compra en tiendas de barrio o almacenes de cadena",
        "marcas_clave_gabrica": "Grand Vita Equilíbrio, Max Cat/Dog, Guaumor, Simparica (tableta mensual)",
        "estrategia_comunicacion_masterbrand": "Costo-beneficio y rendimiento: 'Protección y nutrición avalada por veterinarios al precio que tu hogar necesita para cuidar a toda la familia'.",
        "canal_compra_habitual": "Agrocampo, pet shops de barrio, tiendas de retail y supermercados"
    },
    {
        "id_segmento": "SEG-03",
        "nombre_segmento": "Tutor Felino Exclusivo ('Cat Lover')",
        "entorno_vida": "Doméstico / Hogar Urbano",
        "especies_a_cargo": "Felinos exclusivamente (1 a 4 gatos criollos adoptados, Persas, Siameses)",
        "perfil_sociodemografico": "Jóvenes independientes, teletrabajadores, creativos y estudiantes (20 a 38 años)",
        "estrato_predominante": "Estratos 3, 4, 5 y 6",
        "ciudades_foco": "Bogotá, Medellín, Manizales, Bucaramanga (zonas de alta densidad de apartamentos)",
        "penetracion_estimada_pct": 16.5,
        "gasto_mensual_min_cop": 140000,
        "gasto_mensual_max_cop": 450000,
        "gasto_mensual_promedio_cop": 280000,
        "drivers_de_compra": "Salud urinaria y renal preventiva, control de olores en areneros, enriquecimiento ambiental y palatabilidad húmeda",
        "barreras_frecuentes": "Dificultad extrema para suministrar medicamentos orales, fobia felina a transportines y veterinarias presenciales",
        "marcas_clave_gabrica": "Hill's Feline c/d Multicare y k/d, Revolution Plus (pipeta sin estrés), Plaisir Cat Paté, Arenas sanitarias Catit",
        "estrategia_comunicacion_masterbrand": "Especialización felina médica: 'Medicina y bienestar sin batallas ni estrés: protección tópica y nutrición renal especializada para gatos'.",
        "canal_compra_habitual": "Pet shops especializados en gatos, e-commerce veterinario y clínicas cat-friendly"
    },
    {
        "id_segmento": "SEG-04",
        "nombre_segmento": "Adulto Mayor / Compañero de Vida Senior",
        "entorno_vida": "Doméstico / Hogar Urbano",
        "especies_a_cargo": "Perros o gatos de edad avanzada (senior de 7+ años, razas pequeñas o medianas)",
        "perfil_sociodemografico": "Pensionados o adultos mayores de 60 años en etapa de 'nido vacío' (viven solos o en pareja)",
        "estrato_predominante": "Estratos 2, 3, 4 y 5",
        "ciudades_foco": "Bogotá, Medellín, Armenia, Pereira, Manizales, Bucaramanga, Tunja",
        "penetracion_estimada_pct": 9.0,
        "gasto_mensual_min_cop": 150000,
        "gasto_mensual_max_cop": 500000,
        "gasto_mensual_promedio_cop": 310000,
        "drivers_de_compra": "Fidelidad absoluta a la receta del médico veterinario de confianza, alivio de dolores articulares y soporte de órganos vitales",
        "barreras_frecuentes": "Dificultad de movilidad para cargar bultos pesados, ingresos fijos de pensión, apego emocional muy alto",
        "marcas_clave_gabrica": "Hill's Prescription Diet j/d (movilidad), k/d (renal), Apoquel (dermatología senil), condroprotectores Zoetis",
        "estrategia_comunicacion_masterbrand": "Dignidad y longevidad en la vejez: 'Calidad de vida y menos dolor para tu compañero más fiel en sus años dorados'.",
        "canal_compra_habitual": "Clínica veterinaria tradicional de cabecera con servicio a domicilio telefónico"
    },
    {
        "id_segmento": "SEG-05",
        "nombre_segmento": "Propietario de Finca & Criador Equino",
        "entorno_vida": "Finca / Rural / Equinos",
        "especies_a_cargo": "Equinos (caballos de paso, deporte o recreo), caninos de guarda/pastoreo en libertad y gatos de establo",
        "perfil_sociodemografico": "Propietarios de fincas de recreo, hacendados, empresarios del agro y aficionados a ferias equinas",
        "estrato_predominante": "Estratos 4, 5 y 6 / Productores agropecuarios",
        "ciudades_foco": "Sabana de Bogotá, Rionegro/Llanogrande (Antioquia), Tuluá/Buga (Valle), Villavicencio/Meta, Montería/Córdoba",
        "penetracion_estimada_pct": 6.5,
        "gasto_mensual_min_cop": 600000,
        "gasto_mensual_max_cop": 3500000,
        "gasto_mensual_promedio_cop": 1600000,
        "drivers_de_compra": "Salud y rendimiento de equinos (articulaciones, pelaje, cascos), control masivo de garrapatas de potrero y choque antiparasitario",
        "barreras_frecuentes": "Aislamiento geográfico, necesidad de compras al por mayor, riesgo de productos vencidos en ferreterías rurales",
        "marcas_clave_gabrica": "Simparica (choque antiparasitario perros de finca), Suplementos Zoetis equinos, antibióticos y biológicos oficiales",
        "estrategia_comunicacion_masterbrand": "Bioseguridad y potencia de campo: 'Trazabilidad y potencia farmacéutica para proteger el patrimonio y la salud de tus ejemplares en finca'.",
        "canal_compra_habitual": "Agrocampo, almacenes agropecuarios regionales, cooperativas ganaderas y médicos veterinarios de campo"
    },
    {
        "id_segmento": "SEG-06",
        "nombre_segmento": "Administrador / Mayordomo de Finca Rural",
        "entorno_vida": "Finca / Rural / Equinos",
        "especies_a_cargo": "Perros criollos de trabajo/guarda rural, equinos de faena y ganado de pastoreo",
        "perfil_sociodemografico": "Trabajadores y familias campesinas residentes fijas en predios rurales y fincas",
        "estrato_predominante": "Estrato 1 y 2 Rural",
        "ciudades_foco": "Regiones rurales de Cundinamarca, Antioquia, Santander, Tolima, Huila, Costa Caribe y Llanos",
        "penetracion_estimada_pct": 4.5,
        "gasto_mensual_min_cop": 70000,
        "gasto_mensual_max_cop": 220000,
        "gasto_mensual_promedio_cop": 130000,
        "drivers_de_compra": "Eficacia dura inmediata contra pulgas y garrapatas (evitar hemoparásitos), bultos económicos rendidores de alimento",
        "barreras_frecuentes": "Bajo presupuesto disponible, escasa oferta de marcas médicas en veredas, uso tradicional de remedios caseros (vinagre, aceites)",
        "marcas_clave_gabrica": "Max, Guaumor, soluciones antiparasitarias de choque accesibles",
        "estrategia_comunicacion_masterbrand": "Resistencia y prevención: 'Evita la muerte por garrapatas en tu finca con soluciones que rinden y protegen a tus perros de trabajo'.",
        "canal_compra_habitual": "Almacenes agropecuarios municipales, tiendas de vereda y veterinarias de cabecera municipal"
    },
    {
        "id_segmento": "SEG-07",
        "nombre_segmento": "Rescatistas, Albergues y Hogares de Paso",
        "entorno_vida": "Comunidad Solidaria / Mixto",
        "especies_a_cargo": "Poblaciones masivas rescatadas (15 a 80+ perros y gatos en recuperación o adopción)",
        "perfil_sociodemografico": "Líderes de fundaciones, activistas independientes y colectivos de protección animal",
        "estrato_predominante": "Estratos 1, 2 y 3 (financiados por donaciones de estratos 4-6)",
        "ciudades_foco": "Periferias de Bogotá (Soacha, Mosquera), Medellín (Caldas, Girardota), Cali (Yumbo), Barranquilla, Bucaramanga",
        "penetracion_estimada_pct": 3.0,
        "gasto_mensual_min_cop": 800000,
        "gasto_mensual_max_cop": 5000000,
        "gasto_mensual_promedio_cop": 2200000,
        "drivers_de_compra": "Compra por toneladas/bultos al por mayor, nutrición de recuperación rápida de desnutrición, vacunas y desparasitantes en bulto",
        "barreras_frecuentes": "Déficit crónico de presupuesto, dependencia de donaciones, emergencias clínicas constantes",
        "marcas_clave_gabrica": "Max, Guaumor, programas de donación y apadrinamiento Gabrica de desparasitantes y vacunas",
        "estrategia_comunicacion_masterbrand": "Responsabilidad social corporativa: 'Gabrica al lado de los que rescatan vidas: nutrición y salud accesible para segundas oportunidades'.",
        "canal_compra_habitual": "Distribuidores mayoristas directos, convenios institucionales y donaciones empresariales"
    }
]


def main():
    logger.info("🚀 Generando Matriz de Segmentación de Consumidores en Colombia...")

    df_segmentos = pl.DataFrame(SEGMENTOS)

    # Validaciones y Cálculos
    assert df_segmentos.height == 7, "Debe haber 7 segmentos modelados"
    
    total_penetracion = df_segmentos["penetracion_estimada_pct"].sum()
    logger.info(f"Suma de penetración de mercado estimada: {total_penetracion:.1f}%")

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    df_segmentos.write_csv(OUTPUT_FILE)
    logger.info(f"✅ ¡Dataset de Consumidores guardado exitosamente en: {OUTPUT_FILE}!")

    print("\n" + "=" * 80)
    print("📊 MATRIZ DE SEGMENTACIÓN DE CONSUMIDORES: DUEÑOS DE MASCOTAS Y FINCAS (COLOMBIA)")
    print("=" * 80)
    for row in df_segmentos.iter_rows(named=True):
        print(f"\n[{row['id_segmento']}] {row['nombre_segmento']} ({row['entorno_vida']})")
        print(f"  • Estratos: {row['estrato_predominante']} | Penetración: {row['penetracion_estimada_pct']}%")
        print(f"  • Gasto Mensual Promedio: ${row['gasto_mensual_promedio_cop']:,} COP (Rango: ${row['gasto_mensual_min_cop']:,} - ${row['gasto_mensual_max_cop']:,})")
        print(f"  • Marcas Gabrica Afines: {row['marcas_clave_gabrica']}")
        print(f"  • Mensaje Masterbrand: {row['estrategia_comunicacion_masterbrand']}")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
