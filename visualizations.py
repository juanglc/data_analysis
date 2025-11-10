import streamlit as st
import polars as pl
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots


def create_kpi_metrics(df_subjects: pl.DataFrame, df_arrivals: pl.DataFrame):
    """Crea métricas KPI principales en la parte superior del dashboard"""

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        if "Personas por ocurrencia" in df_subjects.columns:
            total_victims = int(df_subjects["Personas por ocurrencia"].sum())
            st.metric(
                label="👥 Total Personas Afectadas",
                value=f"{total_victims:,}",
                delta=None,
                help="Total de personas afectadas por hechos victimizantes"
            )
        else:
            st.metric("👥 Total Personas Afectadas", "N/A")

    with col2:
        if "Personas que llegaron" in df_arrivals.columns:
            total_displaced = int(df_arrivals["Personas que llegaron"].sum())
            st.metric(
                label="🚶 Personas Desplazadas",
                value=f"{total_displaced:,}",
                delta=None,
                help="Total de personas que tuvieron que desplazarse"
            )
        else:
            st.metric("🚶 Personas Desplazadas", "N/A")

    with col3:
        if "Eventos" in df_arrivals.columns:
            total_events = int(df_arrivals["Eventos"].sum())
            st.metric(
                label="⚠️ Eventos Registrados",
                value=f"{total_events:,}",
                delta=None,
                help="Número total de eventos de desplazamiento"
            )
        else:
            st.metric("⚠️ Eventos Registrados", "N/A")

    with col4:
        if "ESTADO_DEPTO" in df_arrivals.columns:
            unique_depts = df_arrivals["ESTADO_DEPTO"].n_unique()
            st.metric(
                label="🗺️ Departamentos Afectados",
                value=f"{unique_depts}",
                delta=None,
                help="Número de departamentos con llegadas registradas"
            )
        else:
            st.metric("🗺️ Departamentos Afectados", "N/A")


def create_temporal_analysis(df_subjects: pl.DataFrame, df_arrivals: pl.DataFrame, theme: str):
    """Análisis de tendencias temporales"""

    col1, col2 = st.columns(2)

    with col1:
        if "Vigencia" in df_arrivals.columns and "Personas que llegaron" in df_arrivals.columns:
            yearly_data = df_arrivals.group_by("Vigencia").agg([
                pl.col("Personas que llegaron").sum().alias("Personas Desplazadas"),
                pl.col("Eventos").sum().alias("Eventos")
            ]).sort("Vigencia")

            fig = go.Figure()

            fig.add_trace(go.Scatter(
                x=yearly_data["Vigencia"].to_list(),
                y=yearly_data["Personas Desplazadas"].to_list(),
                mode='lines+markers',
                name='Personas Desplazadas',
                line=dict(color='#e74c3c', width=3),
                marker=dict(size=8)
            ))

            fig.update_layout(
                title="Evolución Temporal del Desplazamiento Forzado",
                xaxis_title="Año",
                yaxis_title="Número de Personas",
                template=theme,
                height=400,
                hovermode='x unified'
            )

            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No hay datos temporales disponibles")

    with col2:
        if "Vigencia" in df_arrivals.columns and "Eventos" in df_arrivals.columns:
            yearly_events = df_arrivals.group_by("Vigencia").agg([
                pl.col("Eventos").sum().alias("Total Eventos")
            ]).sort("Vigencia")

            fig = px.bar(
                yearly_events.to_pandas(),
                x="Vigencia",
                y="Total Eventos",
                title="Eventos de Desplazamiento por Año",
                labels={"Total Eventos": "Número de Eventos", "Vigencia": "Año"},
                color="Total Eventos",
                color_continuous_scale="Reds",
                template=theme
            )

            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No hay datos de eventos disponibles")


def create_geographic_analysis(df_subjects: pl.DataFrame, df_arrivals: pl.DataFrame, theme: str):
    """Análisis de distribución geográfica"""

    if "ESTADO_DEPTO" in df_arrivals.columns:
        dept_summary = df_arrivals.group_by("ESTADO_DEPTO").agg([
            pl.col("Personas que llegaron").sum().alias("Personas Desplazadas"),
            pl.col("Eventos").sum().alias("Eventos"),
            pl.col("Personas por ocurrencia").sum().alias("Personas Afectadas")
        ]).sort("Personas Desplazadas", descending=True).head(10)

        col1, col2 = st.columns([2, 1])

        with col1:
            fig = px.bar(
                dept_summary.to_pandas(),
                y="ESTADO_DEPTO",
                x="Personas Desplazadas",
                orientation='h',
                title="Top 10 Departamentos con Mayor Recepción de Desplazados",
                labels={"ESTADO_DEPTO": "Departamento", "Personas Desplazadas": "Número de Personas"},
                color="Personas Desplazadas",
                color_continuous_scale="RdYlBu_r",
                template=theme
            )

            fig.update_layout(height=500, showlegend=False)
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.markdown("##### Resumen por Departamento")
            st.dataframe(
                dept_summary.to_pandas().style.format({
                    "Personas Desplazadas": "{:,.0f}",
                    "Eventos": "{:,.0f}",
                    "Personas Afectadas": "{:,.0f}"
                }),
                height=500,
                use_container_width=True
            )
    else:
        st.warning("No hay datos geográficos disponibles")


def create_demographic_analysis(df_subjects: pl.DataFrame, df_arrivals: pl.DataFrame, theme: str):
    """Análisis demográfico de las víctimas"""

    col1, col2, col3 = st.columns(3)

    with col1:
        if "Etnia" in df_subjects.columns and "Personas por ocurrencia" in df_subjects.columns:
            etnia_summary = df_subjects.group_by("Etnia").agg(
                pl.col("Personas por ocurrencia").sum().alias("Total")
            ).sort("Total", descending=True)

            fig = px.pie(
                etnia_summary.to_pandas(),
                values="Total",
                names="Etnia",
                title="Distribución por Etnia (Todas las Categorías)",
                hole=0.4,
                template=theme,
                color_discrete_sequence=px.colors.qualitative.Set3
            )

            fig.update_traces(textposition='inside', textinfo='percent+label')
            fig.update_layout(height=400)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No hay datos de etnia")

    with col2:
        if "Ciclo vital" in df_subjects.columns and "Personas por ocurrencia" in df_subjects.columns:
            ciclo_summary = df_subjects.group_by("Ciclo vital").agg(
                pl.col("Personas por ocurrencia").sum().alias("Total")
            ).sort("Total", descending=True)

            fig = px.bar(
                ciclo_summary.to_pandas(),
                x="Ciclo vital",
                y="Total",
                title="Distribución por Ciclo Vital",
                labels={"Total": "Número de Personas", "Ciclo vital": "Grupo de Edad"},
                color="Total",
                color_continuous_scale="Blues",
                template=theme
            )

            fig.update_layout(height=400, showlegend=False)
            fig.update_xaxes(tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No hay datos de ciclo vital")

    with col3:
        if "Sexo" in df_subjects.columns and "Personas por ocurrencia" in df_subjects.columns:
            sexo_summary = df_subjects.group_by("Sexo").agg(
                pl.col("Personas por ocurrencia").sum().alias("Total")
            )

            fig = go.Figure(data=[go.Pie(
                labels=sexo_summary["Sexo"].to_list(),
                values=sexo_summary["Total"].to_list(),
                hole=0.5,
                marker_colors=['#3498db', '#e74c3c', '#95a5a6']
            )])

            fig.update_layout(
                title="Distribución por Sexo",
                template=theme,
                height=400
            )

            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No hay datos de sexo")


def create_comparative_analysis(df_subjects: pl.DataFrame, df_arrivals: pl.DataFrame, theme: str):
    """Análisis comparativo entre diferentes categorías"""

    col1, col2 = st.columns(2)

    with col1:
        if "Tipo o Nombre de Hecho Victimizante" in df_subjects.columns:
            hecho_summary = df_subjects.group_by("Tipo o Nombre de Hecho Victimizante").agg(
                pl.col("Personas por ocurrencia").sum().alias("Total Víctimas")
            ).sort("Total Víctimas", descending=True).head(8)

            fig = px.treemap(
                hecho_summary.to_pandas(),
                path=["Tipo o Nombre de Hecho Victimizante"],
                values="Total Víctimas",
                title="Distribución de Hechos Victimizantes (Treemap)",
                color="Total Víctimas",
                color_continuous_scale="RdYlGn_r",
                template=theme
            )

            fig.update_layout(height=500)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No hay datos de hechos victimizantes")

    with col2:
        if "Discapacidad" in df_subjects.columns and "Personas por ocurrencia" in df_subjects.columns:
            discap_summary = df_subjects.group_by("Discapacidad").agg(
                pl.col("Personas por ocurrencia").sum().alias("Total")
            )

            fig = px.bar(
                discap_summary.to_pandas(),
                x="Discapacidad",
                y="Total",
                title="Víctimas con y sin Discapacidad",
                labels={"Total": "Número de Personas", "Discapacidad": "Estado"},
                color="Discapacidad",
                template=theme,
                color_discrete_map={"NO": "#2ecc71", "SI": "#e67e22"}
            )

            fig.update_layout(height=500, showlegend=True)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No hay datos de discapacidad")


def create_minorities_analysis(df_subjects: pl.DataFrame, df_arrivals: pl.DataFrame, theme: str):
    """Análisis específico de minorías étnicas y grupos vulnerables - EXCLUYE 'Ninguna'"""

    # REEMPLAZAR HTML CON COMPONENTE NATIVO
    st.warning("""
**⚠️ Contexto Importante:** Las minorías étnicas han sido históricamente las más afectadas por 
el desplazamiento forzado en Colombia. Este análisis **EXCLUYE la categoría "Ninguna"** (población sin 
pertenencia étnica específica) para visibilizar el impacto desproporcionado en comunidades étnicas.
    """)

    if "Etnia" not in df_subjects.columns or "Personas por ocurrencia" not in df_subjects.columns:
        st.warning("No hay datos de etnia disponibles para este análisis")
        return

    minorities_only = df_subjects.filter(
        ~pl.col("Etnia").str.to_lowercase().is_in(["ninguna", "no informa", "sin información", "no especificado", "nd"])
    )

    if minorities_only.shape[0] == 0:
        st.warning("No se encontraron registros de minorías étnicas en el dataset")
        return

    etnia_detailed = minorities_only.group_by("Etnia").agg([
        pl.col("Personas por ocurrencia").sum().alias("Total Víctimas"),
        pl.col("Personas sujetas a atención").sum().alias("Personas Requieren Atención"),
        pl.count().alias("Número de Eventos")
    ]).sort("Total Víctimas", descending=True)

    total_minorities = etnia_detailed["Total Víctimas"].sum()
    total_all_victims = int(df_subjects["Personas por ocurrencia"].sum())

    col1, col2 = st.columns([2, 1])

    with col1:
        fig = px.bar(
            etnia_detailed.to_pandas(),
            x="Etnia",
            y="Total Víctimas",
            title="Impacto del Desplazamiento en Minorías Étnicas (Excluye 'Ninguna')",
            labels={"Total Víctimas": "Número de Víctimas", "Etnia": "Grupo Étnico"},
            color="Total Víctimas",
            color_continuous_scale="Reds",
            template=theme,
            text="Total Víctimas"
        )

        fig.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
        fig.update_layout(height=500, showlegend=False)
        fig.update_xaxes(tickangle=-45)
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("##### 📊 Distribución Proporcional de Minorías Étnicas")
        etnia_with_pct = etnia_detailed.to_pandas()
        etnia_with_pct['% del Total de Minorías'] = (etnia_with_pct['Total Víctimas'] / total_minorities * 100).round(2)
        etnia_with_pct['% del Total General'] = (etnia_with_pct['Total Víctimas'] / total_all_victims * 100).round(2)

        st.dataframe(
            etnia_with_pct.style.format({
                "Total Víctimas": "{:,.0f}",
                "Personas Requieren Atención": "{:,.0f}",
                "Número de Eventos": "{:,.0f}",
                "% del Total de Minorías": "{:.2f}%",
                "% del Total General": "{:.2f}%"
            }),
            use_container_width=True,
            height=300
        )

    with col2:
        st.markdown("#### Indicadores Clave")

        pct_minorities = (total_minorities / total_all_victims * 100)

        st.metric(
            "🌍 Total Víctimas de Minorías Étnicas",
            f"{int(total_minorities):,}",
            delta=f"{pct_minorities:.1f}% del total",
            help="Total excluyendo 'Ninguna'"
        )

        most_affected = etnia_detailed.head(1)
        if most_affected.shape[0] > 0:
            group_name = most_affected["Etnia"][0]
            group_count = int(most_affected["Total Víctimas"][0])
            group_pct = (group_count / total_minorities * 100)

            st.metric(
                "Grupo Étnico Más Afectado",
                group_name,
                delta=f"{group_count:,} víctimas ({group_pct:.1f}%)"
            )

        st.metric(
            "Grupos Étnicos Registrados",
            etnia_detailed.shape[0],
            help="Número de minorías étnicas diferentes afectadas"
        )

        ninguna_count = df_subjects.filter(
            pl.col("Etnia").str.to_lowercase() == "ninguna"
        )["Personas por ocurrencia"].sum()

        st.markdown("---")
        st.markdown("##### 📈 Contexto Comparativo")
        st.info(f"""
**Población sin etnia específica ('Ninguna'):**  
{int(ninguna_count):,} víctimas ({(ninguna_count / total_all_victims * 100):.1f}% del total)

**Minorías étnicas:**  
{int(total_minorities):,} víctimas ({pct_minorities:.1f}% del total)
        """)

    st.markdown("---")
    st.markdown("#### 🔍 Hechos Victimizantes en Comunidades Étnicas")

    if "Tipo o Nombre de Hecho Victimizante" in minorities_only.columns:
        hecho_minorities = minorities_only.group_by("Tipo o Nombre de Hecho Victimizante").agg(
            pl.col("Personas por ocurrencia").sum().alias("Total Víctimas")
        ).sort("Total Víctimas", descending=True).head(10)

        fig = px.bar(
            hecho_minorities.to_pandas(),
            y="Tipo o Nombre de Hecho Victimizante",
            x="Total Víctimas",
            orientation='h',
            title="Top 10 Hechos Victimizantes en Minorías Étnicas (Excluye 'Ninguna')",
            labels={"Total Víctimas": "Número de Víctimas"},
            color="Total Víctimas",
            color_continuous_scale="YlOrRd",
            template=theme
        )

        fig.update_layout(height=400, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)


def create_children_analysis(df_subjects: pl.DataFrame, df_arrivals: pl.DataFrame, theme: str):
    """Análisis específico de menores de edad"""

    # REEMPLAZAR HTML CON COMPONENTE NATIVO
    st.error("""
**🚨 Alerta Crítica:** Los menores de edad representan una población extremadamente vulnerable. 
El desplazamiento infantil tiene consecuencias devastadoras en desarrollo, educación y salud mental. 
**La explotación sexual y laboral de menores es una consecuencia directa del conflicto armado.**
    """)

    if "Ciclo vital" not in df_subjects.columns:
        st.warning("No hay datos de ciclo vital disponibles")
        return

    child_categories = ['entre 0 y 5', 'entre 6 y 11', 'entre 12 y 17']

    children_df = df_subjects.filter(
        pl.col("Ciclo vital").is_in(child_categories)
    )

    if children_df.shape[0] == 0:
        st.error(f"⚠️ No se encontraron registros de menores usando las categorías: {child_categories}")
        return

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        total_children = int(children_df["Personas por ocurrencia"].sum())
        total_victims = int(df_subjects["Personas por ocurrencia"].sum())
        pct_children = (total_children / total_victims * 100)

        st.metric(
            "👶 Total Menores Afectados",
            f"{total_children:,}",
            delta=f"{pct_children:.1f}% del total",
            help="Menores de 0 a 17 años afectados por desplazamiento forzado"
        )

    with col2:
        children_events = int(children_df.shape[0])
        st.metric(
            "📋 Eventos con Menores",
            f"{children_events:,}",
            help="Número de registros que involucran menores de edad"
        )

    with col3:
        if "Sexo" in children_df.columns:
            girls = children_df.filter(pl.col("Sexo") == "MUJER")["Personas por ocurrencia"].sum()
            st.metric(
                "👧 Niñas Afectadas",
                f"{int(girls):,}",
                help="Niñas y adolescentes mujeres en especial riesgo de violencia sexual"
            )

    with col4:
        if "Sexo" in children_df.columns:
            boys = children_df.filter(pl.col("Sexo") == "HOMBRE")["Personas por ocurrencia"].sum()
            st.metric(
                "👦 Niños Afectados",
                f"{int(boys):,}",
                help="Niños y adolescentes varones en riesgo de reclutamiento forzado"
            )

    st.markdown("---")
    st.markdown("#### 📊 Distribución por Rangos de Edad")

    col1, col2 = st.columns(2)

    with col1:
        age_distribution = children_df.group_by("Ciclo vital").agg(
            pl.col("Personas por ocurrencia").sum().alias("Total Víctimas")
        ).sort("Ciclo vital")

        age_labels = {
            'entre 0 y 5': 'Primera Infancia (0-5 años)',
            'entre 6 y 11': 'Infancia (6-11 años)',
            'entre 12 y 17': 'Adolescencia (12-17 años)'
        }

        age_dist_df = age_distribution.to_pandas()
        age_dist_df['Etiqueta'] = age_dist_df['Ciclo vital'].map(age_labels)

        fig = px.pie(
            age_dist_df,
            values="Total Víctimas",
            names="Etiqueta",
            title="Distribución de Menores Víctimas por Grupo de Edad",
            hole=0.4,
            template=theme,
            color_discrete_sequence=px.colors.sequential.Reds_r
        )

        fig.update_traces(textposition='inside', textinfo='percent+label')
        fig.update_layout(height=400)
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        age_detailed = age_dist_df.copy()
        age_detailed['Porcentaje'] = (age_detailed['Total Víctimas'] / total_children * 100).round(2)
        age_detailed = age_detailed[['Etiqueta', 'Total Víctimas', 'Porcentaje']]

        st.markdown("##### Detalle Numérico")
        st.dataframe(
            age_detailed.style.format({
                "Total Víctimas": "{:,.0f}",
                "Porcentaje": "{:.2f}%"
            }),
            use_container_width=True,
            height=300
        )

        st.markdown("##### 🔍 Observaciones")
        max_group = age_detailed.loc[age_detailed['Total Víctimas'].idxmax()]
        st.info(
            f"**Grupo más afectado:** {max_group['Etiqueta']} con {int(max_group['Total Víctimas']):,} víctimas ({max_group['Porcentaje']:.1f}%)")

    st.markdown("---")
    st.markdown("#### 🚨 Hechos Victimizantes contra Menores de Edad")

    if "Tipo o Nombre de Hecho Victimizante" in children_df.columns:
        hecho_children = children_df.group_by("Tipo o Nombre de Hecho Victimizante").agg(
            pl.col("Personas por ocurrencia").sum().alias("Total Víctimas")
        ).sort("Total Víctimas", descending=True).head(10)

        fig = px.bar(
            hecho_children.to_pandas(),
            y="Tipo o Nombre de Hecho Victimizante",
            x="Total Víctimas",
            orientation='h',
            title="Top 10 Crímenes contra Menores de Edad",
            labels={"Total Víctimas": "Número de Menores Afectados"},
            color="Total Víctimas",
            color_continuous_scale="Reds",
            template=theme,
            text="Total Víctimas"
        )

        fig.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
        fig.update_layout(height=500, showlegend=False)
        st.plotly_chart(fig, use_container_width=True)

        st.markdown("##### 📋 Detalle Completo de Hechos Victimizantes")
        hecho_children_full = children_df.group_by("Tipo o Nombre de Hecho Victimizante").agg(
            pl.col("Personas por ocurrencia").sum().alias("Total Menores Víctimas")
        ).sort("Total Menores Víctimas", descending=True)

        hecho_full_df = hecho_children_full.to_pandas()
        hecho_full_df['Porcentaje del Total'] = (hecho_full_df['Total Menores Víctimas'] / total_children * 100).round(
            2)

        st.dataframe(
            hecho_full_df.style.format({
                "Total Menores Víctimas": "{:,.0f}",
                "Porcentaje del Total": "{:.2f}%"
            }),
            use_container_width=True,
            height=300
        )

    # REEMPLAZAR HTML CON COMPONENTE NATIVO
    st.markdown("---")
    st.warning("""
**⚠️ Explotación Sexual y Laboral de Menores**

**El desplazamiento forzado expone a los menores a:**

- **Explotación sexual comercial:** Niñas y adolescentes son víctimas de redes de trata con fines de explotación sexual, especialmente en zonas de conflicto y rutas de desplazamiento.
- **Trabajo infantil forzado:** Los menores desplazados son obligados a trabajar en condiciones de explotación para sobrevivir.
- **Reclutamiento forzado:** Grupos armados reclutan menores para actividades del conflicto.
- **Matrimonio infantil forzado:** Como estrategia de "protección" familiar en contextos de desplazamiento.
- **Pérdida de educación:** El desarraigo interrumpe procesos educativos, perpetuando ciclos de pobreza.

📞 **Es imperativo fortalecer los mecanismos de protección infantil y atención psicosocial especializada.**
    """)

    if "Sexo" in children_df.columns:
        st.markdown("---")
        st.markdown("#### ⚖️ Análisis de Género en Población Menor")

        col1, col2 = st.columns(2)

        with col1:
            gender_children = children_df.group_by("Sexo").agg(
                pl.col("Personas por ocurrencia").sum().alias("Total")
            )

            fig = px.pie(
                gender_children.to_pandas(),
                values="Total",
                names="Sexo",
                title="Distribución por Sexo en Menores Víctimas",
                hole=0.5,
                template=theme,
                color_discrete_map={"MUJER": "#e74c3c", "HOMBRE": "#3498db", "NO INFORMA": "#95a5a6"}
            )

            fig.update_layout(height=350)
            st.plotly_chart(fig, use_container_width=True)

        with col2:
            # REEMPLAZAR HTML CON MARKDOWN SIMPLE
            st.markdown("""
##### 🚨 Vulnerabilidades Diferenciadas

**Niñas y adolescentes:**
- Mayor riesgo de violencia sexual
- Explotación sexual comercial
- Embarazo adolescente forzado
- Matrimonio infantil

**Niños y adolescentes varones:**
- Reclutamiento forzado
- Trabajo infantil explotación
- Uso en actividades ilícitas
            """)

    if "Etnia" in children_df.columns:
        st.markdown("---")
        st.markdown("#### 🌍 Menores de Minorías Étnicas Afectados")

        children_minorities = children_df.filter(
            ~pl.col("Etnia").str.to_lowercase().is_in(
                ["ninguna", "no informa", "sin información", "no especificado", "nd"])
        )

        if children_minorities.shape[0] > 0:
            etnia_children = children_minorities.group_by("Etnia").agg(
                pl.col("Personas por ocurrencia").sum().alias("Total Menores")
            ).sort("Total Menores", descending=True).head(8)

            fig = px.bar(
                etnia_children.to_pandas(),
                x="Etnia",
                y="Total Menores",
                title="Menores de Minorías Étnicas Víctimas (Top 8, Excluye 'Ninguna')",
                labels={"Total Menores": "Número de Menores", "Etnia": "Grupo Étnico"},
                color="Total Menores",
                color_continuous_scale="OrRd",
                template=theme,
                text="Total Menores"
            )

            fig.update_traces(texttemplate='%{text:,.0f}', textposition='outside')
            fig.update_layout(height=400, showlegend=False)
            fig.update_xaxes(tickangle=-45)
            st.plotly_chart(fig, use_container_width=True)

            total_minority_children = int(children_minorities["Personas por ocurrencia"].sum())
            pct_minority_children = (total_minority_children / total_children * 100)

            st.warning(f"""
💡 **Doble Vulnerabilidad:**  
{total_minority_children:,} menores de minorías étnicas ({pct_minority_children:.1f}% de los menores afectados) 
enfrentan doble vulnerabilidad por su edad y su pertenencia a comunidades históricamente excluidas.
            """)
        else:
            st.info("No se encontraron datos de menores en minorías étnicas")

    if "Vigencia" in children_df.columns:
        st.markdown("---")
        st.markdown("#### 📅 Evolución Temporal de Menores Afectados")

        temporal_children = children_df.group_by("Vigencia").agg(
            pl.col("Personas por ocurrencia").sum().alias("Menores Afectados")
        ).sort("Vigencia")

        if temporal_children.shape[0] > 0:
            fig = go.Figure()

            fig.add_trace(go.Scatter(
                x=temporal_children["Vigencia"].to_list(),
                y=temporal_children["Menores Afectados"].to_list(),
                mode='lines+markers',
                name='Menores Afectados',
                line=dict(color='#e74c3c', width=3),
                marker=dict(size=8),
                fill='tozeroy',
                fillcolor='rgba(231, 76, 60, 0.1)'
            ))

            fig.update_layout(
                title="Tendencia de Menores Afectados por Año",
                xaxis_title="Año",
                yaxis_title="Número de Menores",
                template=theme,
                height=400,
                hovermode='x unified'
            )

            st.plotly_chart(fig, use_container_width=True)


def create_critical_analysis(df_subjects: pl.DataFrame, df_arrivals: pl.DataFrame):
    """Análisis crítico y conclusiones sobre la calidad de los datos y hallazgos"""

    # REEMPLAZAR HTML CON COMPONENTE NATIVO
    st.info("""
**📊 Análisis Crítico de los Datos**

Este análisis identifica limitaciones en los datos que afectan la comprensión completa del fenómeno 
y propone conclusiones basadas en los patrones identificados.
    """)

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 🔍 Problemas de Calidad de Datos")

        if "ESTADO_DEPTO" in df_arrivals.columns:
            undefined_dept = df_arrivals.filter(
                pl.col("ESTADO_DEPTO").str.to_lowercase().is_in(
                    ["sin definir", "no informa", "sin información", "no especificado"])
            )
            total_arrivals = df_arrivals.shape[0]
            undefined_count = undefined_dept.shape[0]
            undefined_pct = (undefined_count / total_arrivals * 100) if total_arrivals > 0 else 0

            if "Personas que llegaron" in undefined_dept.columns:
                undefined_people = int(undefined_dept["Personas que llegaron"].sum())
                total_people = int(df_arrivals["Personas que llegaron"].sum())
                undefined_people_pct = (undefined_people / total_people * 100) if total_people > 0 else 0

                st.warning(f"""
**⚠️ Lugares Sin Definir**

- **{undefined_count:,}** eventos ({undefined_pct:.1f}%) sin departamento definido
- **{undefined_people:,}** personas ({undefined_people_pct:.1f}%) afectadas sin ubicación clara

**Implicación:** Dificulta la focalización de recursos y atención humanitaria.
                """)

        st.error("""
**🕵️ Perpetradores No Identificados**

Una gran proporción de casos **no identifica al grupo armado responsable**:

- Dificulta la rendición de cuentas
- Impide patrones de actuación criminal
- Obstaculiza justicia transicional
- Genera impunidad estructural

**Conclusión:** Se requiere mejorar los protocolos de recolección de información sobre perpetradores.
        """)

        if "Vigencia" in df_arrivals.columns:
            years_available = sorted(df_arrivals["Vigencia"].unique().to_list())
            min_year = min(years_available) if years_available else "N/A"
            max_year = max(years_available) if years_available else "N/A"

            st.info(f"""
**📅 Cobertura Temporal**

**Período:** {min_year} - {max_year}

Los datos históricos muestran la persistencia del conflicto a lo largo de décadas.
            """)

    with col2:
        st.markdown("### 💡 Conclusiones Principales")

        st.success("""
**🎯 Hallazgos Clave**

**1. Magnitud del Desplazamiento**
- Millones de personas afectadas evidencian una **crisis humanitaria de décadas**
- El desplazamiento es la principal consecuencia del conflicto armado

**2. Poblaciones Más Vulnerables**
- **Minorías étnicas:** Desproporcionadamente afectadas
- **Menores de edad:** Representan una proporción alarmante de víctimas
- **Mujeres y niñas:** En riesgo específico de violencia sexual

**3. Concentración Geográfica**
- Algunos departamentos concentran la mayoría de llegadas
- Zonas rurales y fronterizas más afectadas
- Presión sobre infraestructura de ciudades receptoras
        """)

        st.error("""
**🚨 Explotación Infantil: Consecuencia Invisible**

**El desplazamiento forzado es un factor de riesgo directo para:**

**1. Explotación Sexual Comercial de Menores (ESCNNA)**
- Niñas desplazadas son víctimas de redes de trata
- Rutas de desplazamiento coinciden con rutas de trata
- Vulnerabilidad económica facilita explotación

**2. Trabajo Infantil Forzado**
- Menores trabajan en condiciones de explotación
- Agricultura, minería ilegal, servicios domésticos
- Interrupción de educación perpetúa pobreza

**3. Reclutamiento por Grupos Armados**
- Menores desplazados son objetivo de reclutamiento
- Uso en actividades delictivas y conflicto
- Traumas psicológicos profundos

---

📞 **Urgencia:** Se requiere fortalecer protección infantil, atención psicosocial, y persecución penal de explotadores.
        """)

    st.markdown("---")
    st.markdown("### 📋 Recomendaciones de Política Pública")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.info("""
**🛡️ Protección**
- Protocolos especiales para menores
- Atención diferencial étnica
- Rutas de protección inmediata
- Prevención de re-victimización
        """)

    with col2:
        st.warning("""
**📊 Datos**
- Mejorar registro de perpetradores
- Georreferenciación precisa
- Seguimiento longitudinal
- Datos desagregados por vulnerabilidad
        """)

    with col3:
        st.success("""
**⚖️ Justicia**
- Persecución de explotadores
- Reparación integral a víctimas
- Garantías de no repetición
- Verdad y memoria histórica
        """)

    st.markdown("---")
    st.info("""
**📖 Nota Metodológica**

Este análisis se basa en datos del Registro Único de Víctimas (RUV). Los vacíos de información 
identificados no disminuyen la magnitud de la crisis, sino que evidencian la necesidad de 
**mejorar sistemas de registro, protección y atención**. Cada número representa 
una persona con historia, dignidad y derechos que deben ser garantizados.
    """)


def create_detailed_tables(df_subjects: pl.DataFrame, df_arrivals: pl.DataFrame):
    """Muestra tablas detalladas con paginación"""

    tab1, tab2 = st.tabs(["📋 Hechos Victimizantes", "📍 Llegadas"])

    with tab1:
        st.markdown("##### Tabla Detallada: Víctimas por Hecho Victimizante")

        rows_per_page = 50
        total_rows = df_subjects.shape[0]
        total_pages = max((total_rows + rows_per_page - 1) // rows_per_page, 1)

        page = st.number_input(
            "Página:",
            min_value=1,
            max_value=total_pages,
            value=1,
            step=1,
            key="page_subjects"
        )

        start = (page - 1) * rows_per_page
        end = start + rows_per_page

        page_df = df_subjects[start:end].to_pandas()

        st.dataframe(
            page_df.style.format({
                col: "{:,.0f}" for col in page_df.select_dtypes(include=['float64', 'int64']).columns
            }),
            use_container_width=True,
            height=400
        )

        st.caption(f"Mostrando filas {start + 1} a {min(end, total_rows)} de {total_rows:,}")

        csv = df_subjects.to_pandas().to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Descargar datos completos (CSV)",
            data=csv,
            file_name='victimas_hechos.csv',
            mime='text/csv',
        )

    with tab2:
        st.markdown("##### Tabla Detallada: Llegadas por Departamento")

        rows_per_page = 50
        total_rows = df_arrivals.shape[0]
        total_pages = max((total_rows + rows_per_page - 1) // rows_per_page, 1)

        page = st.number_input(
            "Página:",
            min_value=1,
            max_value=total_pages,
            value=1,
            step=1,
            key="page_arrivals"
        )

        start = (page - 1) * rows_per_page
        end = start + rows_per_page

        page_df = df_arrivals[start:end].to_pandas()

        st.dataframe(
            page_df.style.format({
                col: "{:,.0f}" for col in page_df.select_dtypes(include=['float64', 'int64']).columns
            }),
            use_container_width=True,
            height=400
        )

        st.caption(f"Mostrando filas {start + 1} a {min(end, total_rows)} de {total_rows:,}")

        csv = df_arrivals.to_pandas().to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Descargar datos completos (CSV)",
            data=csv,
            file_name='llegadas_departamentos.csv',
            mime='text/csv',
        )
