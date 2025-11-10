import streamlit as st
import math
from datetime import datetime
from data_loader import load_and_prepare_csv
from filters import apply_filters
from visualizations import (
    create_kpi_metrics,
    create_temporal_analysis,
    create_geographic_analysis,
    create_demographic_analysis,
    create_comparative_analysis,
    create_detailed_tables,
    create_critical_analysis,
    create_children_analysis,
    create_minorities_analysis
)

# ============================================
# CONFIGURACIÓN DE PÁGINA
# ============================================
st.set_page_config(
    page_title="Análisis de Desplazamiento Forzado en Colombia",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================
# ESTILOS PERSONALIZADOS (RESPONSIVOS)
# ============================================
st.markdown("""
    <style>
    /* Estilos responsivos al tema */
    .section-header {
        padding: 0.8rem;
        border-radius: 5px;
        margin: 1.5rem 0 1rem 0;
        font-weight: 600;
        background: linear-gradient(90deg, #1f77b4 0%, #ff7f0e 100%);
        color: white;
    }
    .filter-badge {
        background-color: #ff7f0e;
        color: white;
        padding: 0.3rem 0.6rem;
        border-radius: 12px;
        font-size: 0.85rem;
        font-weight: 600;
        display: inline-block;
        margin: 0.2rem;
    }
    </style>
""", unsafe_allow_html=True)

# ============================================
# ENCABEZADO PRINCIPAL
# ============================================
st.title("📊 Análisis de Víctimas de Desplazamiento Forzado en Colombia")

st.info("""
**Contexto:** Este dashboard presenta un análisis integral de los datos de desplazamiento forzado 
por violencia en Colombia, permitiendo identificar patrones, tendencias y áreas críticas para la toma de decisiones 
y políticas públicas.
""")


# ============================================
# CARGA DE DATOS
# ============================================
@st.cache_data
def load_data():
    df_subjects = load_and_prepare_csv("datasets/hecho_victimizante.csv")
    df_arrivals = load_and_prepare_csv("datasets/llegadas.csv")
    return df_subjects, df_arrivals


with st.spinner('Cargando datos...'):
    df_subjects, df_arrivals = load_data()

# ============================================
# SIDEBAR - FILTROS Y CONTROLES
# ============================================
with st.sidebar:
    st.markdown("### 🎛️ Panel de Control")
    st.markdown("---")


    # Función auxiliar para opciones
    def make_options(df, col):
        if col not in df.columns:
            return ["Todos"]
        unique_vals = sorted([str(v) for v in df[col].unique().to_list() if v is not None])
        return ["Todos"] + unique_vals


    def normalize_selection(sel):
        if not sel or "Todos" in sel:
            return ["Todos"]
        return sel


    # FILTROS PRINCIPALES
    st.markdown("#### 📋 Filtros Principales")

    selected_fact = normalize_selection(
        st.multiselect(
            "Hecho Victimizante:",
            make_options(df_subjects, "Tipo o Nombre de Hecho Victimizante"),
            default=["Todos"],
            help="Selecciona uno o más hechos victimizantes"
        )
    )

    selected_etnia = normalize_selection(
        st.multiselect(
            "Etnia:",
            make_options(df_subjects, "Etnia"),
            default=["Todos"],
            help="Filtra por grupo étnico"
        )
    )

    selected_ciclo_vital = normalize_selection(
        st.multiselect(
            "Ciclo Vital:",
            make_options(df_subjects, "Ciclo vital"),
            default=["Todos"],
            help="Filtra por rango de edad"
        )
    )

    st.markdown("---")
    st.markdown("#### 🗺️ Filtros Geográficos y Temporales")

    selected_departments = normalize_selection(
        st.multiselect(
            "Departamentos:",
            make_options(df_arrivals, "ESTADO_DEPTO"),
            default=["Todos"],
            help="Departamentos de llegada"
        )
    )

    selected_years = normalize_selection(
        st.multiselect(
            "Años:",
            make_options(df_arrivals, "Vigencia"),
            default=["Todos"],
            help="Período temporal"
        )
    )

    st.markdown("---")
    st.markdown("#### ⚙️ Opciones de Visualización")

    show_raw_data = st.checkbox("Mostrar tablas detalladas", value=False)
    chart_theme = st.selectbox("Tema de gráficos:", ["plotly", "plotly_white", "plotly_dark", "ggplot2"])

    # Botón para limpiar filtros
    if st.button("🔄 Limpiar todos los filtros", width="stretch"):
        st.rerun()

# ============================================
# INDICADOR DE FILTROS ACTIVOS
# ============================================
active_filters = []
if selected_fact != ["Todos"]:
    active_filters.append(f"Hecho: {len(selected_fact)}")
if selected_etnia != ["Todos"]:
    active_filters.append(f"Etnia: {len(selected_etnia)}")
if selected_ciclo_vital != ["Todos"]:
    active_filters.append(f"Ciclo Vital: {len(selected_ciclo_vital)}")
if selected_departments != ["Todos"]:
    active_filters.append(f"Deptos: {len(selected_departments)}")
if selected_years != ["Todos"]:
    active_filters.append(f"Años: {len(selected_years)}")

if active_filters:
    filter_html = " ".join([f'<span class="filter-badge">{f}</span>' for f in active_filters])
    st.markdown(f'🔍 **Filtros activos:** {filter_html}', unsafe_allow_html=True)

# ============================================
# APLICAR FILTROS
# ============================================
filtered_subjects = apply_filters(
    df_subjects,
    selected_departments,
    selected_years,
    selected_fact,
    selected_ciclo_vital,
    selected_etnia
)

filtered_arrivals = apply_filters(
    df_arrivals,
    selected_departments,
    selected_years,
    selected_fact,
    selected_ciclo_vital,
    selected_etnia
)

# ============================================
# SECCIÓN 1: KPIs PRINCIPALES
# ============================================
st.markdown('<div class="section-header">📈 Indicadores Clave de Impacto</div>', unsafe_allow_html=True)
create_kpi_metrics(filtered_subjects, filtered_arrivals)

# ============================================
# SECCIÓN 2: ANÁLISIS TEMPORAL
# ============================================
st.markdown('<div class="section-header">⏱️ Análisis Temporal</div>', unsafe_allow_html=True)
create_temporal_analysis(filtered_subjects, filtered_arrivals, chart_theme)

# ============================================
# SECCIÓN 3: ANÁLISIS GEOGRÁFICO
# ============================================
st.markdown('<div class="section-header">🗺️ Distribución Geográfica</div>', unsafe_allow_html=True)
create_geographic_analysis(filtered_subjects, filtered_arrivals, chart_theme)

# ============================================
# SECCIÓN 4: ANÁLISIS DEMOGRÁFICO
# ============================================
st.markdown('<div class="section-header">👥 Perfil Demográfico de las Víctimas</div>', unsafe_allow_html=True)
create_demographic_analysis(filtered_subjects, filtered_arrivals, chart_theme)

# ============================================
# SECCIÓN 5: ANÁLISIS COMPARATIVO
# ============================================
st.markdown('<div class="section-header">🔄 Análisis Comparativo</div>', unsafe_allow_html=True)
create_comparative_analysis(filtered_subjects, filtered_arrivals, chart_theme)

# ============================================
# SECCIÓN 6: ANÁLISIS DE MINORÍAS ÉTNICAS
# ============================================
st.markdown('<div class="section-header">🌍 Análisis de Minorías Étnicas y Poblaciones Vulnerables</div>',
            unsafe_allow_html=True)
create_minorities_analysis(filtered_subjects, filtered_arrivals, chart_theme)

# ============================================
# SECCIÓN 7: ANÁLISIS DE MENORES DE EDAD
# ============================================
st.markdown('<div class="section-header">👶 Análisis de Menores de Edad y Protección Infantil</div>',
            unsafe_allow_html=True)
create_children_analysis(filtered_subjects, filtered_arrivals, chart_theme)

# ============================================
# SECCIÓN 8: ANÁLISIS CRÍTICO Y CONCLUSIONES
# ============================================
st.markdown('<div class="section-header">📝 Análisis Crítico de los Datos</div>', unsafe_allow_html=True)
create_critical_analysis(filtered_subjects, filtered_arrivals)

# ============================================
# SECCIÓN 9: TABLAS DETALLADAS (OPCIONAL)
# ============================================
if show_raw_data:
    st.markdown('<div class="section-header">📊 Datos Detallados</div>', unsafe_allow_html=True)
    create_detailed_tables(filtered_subjects, filtered_arrivals)

# ============================================
# PIE DE PÁGINA
# ============================================
st.markdown("---")
st.caption("""
**Fuente de datos:** Registro Único de Víctimas (RUV) - Colombia \n
**Fecha de corte de los datos:** 1985 - Septiembre 30 de 2025 \n
**Desarrollado por:** Ivonne Patricia Cruz Caballero, Juan Guillermo López Cortés\n
**Dashboard desarrollado con Streamlit**\n
**Fecha de última actualización:** {} \n
""".format(datetime.now().strftime("%Y-%m-%d")))
st.markdown("""
**Nota:** Los datos presentados en este dashboard son para fines informativos y de análisis.
Este análisis es un recurso para la toma de decisiones en políticas públicas y atención humanitaria.
""")
