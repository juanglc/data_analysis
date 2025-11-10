import streamlit as st
import polars as pl
import plotly.express as px


def show_summary_arrivals(df: pl.DataFrame):
    if "ESTADO_DEPTO" in df.columns:
        summary = df.group_by("ESTADO_DEPTO").agg([
            pl.col("Personas por ocurrencia").sum().alias("Personas Afectadas"),
            pl.col("Eventos").sum().alias("Eventos Totales"),
            pl.col("Personas que llegaron").sum().alias("Llegadas Totales"),
        ])
        st.subheader("📍 Resumen por Departamento (Llegadas)")
        st.dataframe(summary.to_pandas())
        # Pie chart for affected people
        fig = px.pie(summary.to_pandas(), values="Personas Afectadas", names="ESTADO_DEPTO",
                     title="Distribución de Personas Afectadas por Departamento")
        st.plotly_chart(fig)


def show_summary_subjects(df: pl.DataFrame):
    if "ESTADO_DEPTO" in df.columns:
        summary = df.group_by("ESTADO_DEPTO").agg([
            pl.col("Personas sujetas a atención").sum().alias("Personas Afectadas"),
            pl.count().alias("Total_Rows")
        ])
        st.subheader("📍 Resumen por Departamento (Víctimas)")
        st.dataframe(summary.to_pandas())
        # Pie chart for affected people
        fig = px.pie(summary.to_pandas(), values="Personas Afectadas", names="ESTADO_DEPTO",
                     title="Distribución de Personas Afectadas por Departamento")
        st.plotly_chart(fig)


def show_graphics_section(df_subjects: pl.DataFrame, df_arrivals: pl.DataFrame):
    st.header("📊 Sección de Gráficas (Circulares Dinámicas)")

    # Pie charts for subjects
    if "Etnia" in df_subjects.columns:
        summary_etnia = df_subjects.group_by("Etnia").agg(
            pl.col("Personas por ocurrencia").sum().alias("Personas Afectadas"))
        fig_etnia = px.pie(summary_etnia.to_pandas(), values="Personas Afectadas", names="Etnia",
                           title="Distribución por Etnia (Víctimas)")
        st.plotly_chart(fig_etnia)

    if "Ciclo vital" in df_subjects.columns:
        summary_ciclo = df_subjects.group_by("Ciclo vital").agg(
            pl.col("Personas por ocurrencia").sum().alias("Personas Afectadas"))
        fig_ciclo = px.pie(summary_ciclo.to_pandas(), values="Personas Afectadas", names="Ciclo vital",
                           title="Distribución por Ciclo Vital (Víctimas)")
        st.plotly_chart(fig_ciclo)

    if "Tipo o Nombre de Hecho Victimizante" in df_subjects.columns:
        summary_hecho = df_subjects.group_by("Tipo o Nombre de Hecho Victimizante").agg(
            pl.col("Personas por ocurrencia").sum().alias("Personas Afectadas"))
        fig_hecho = px.pie(summary_hecho.to_pandas(), values="Personas Afectadas",
                           names="Tipo o Nombre de Hecho Victimizante", title="Distribución por Hecho Victimizante")
        st.plotly_chart(fig_hecho)

    # Pie charts for arrivals
    if "ESTADO_DEPTO" in df_arrivals.columns:
        summary_depto_arr = df_arrivals.group_by("ESTADO_DEPTO").agg(
            pl.col("Personas que llegaron").sum().alias("Llegadas"))
        fig_depto_arr = px.pie(summary_depto_arr.to_pandas(), values="Llegadas", names="ESTADO_DEPTO",
                               title="Distribución de Llegadas por Departamento")
        st.plotly_chart(fig_depto_arr)

    if "Vigencia" in df_arrivals.columns:
        summary_year = df_arrivals.group_by("Vigencia").agg(pl.col("Personas que llegaron").sum().alias("Llegadas"))
        fig_year = px.pie(summary_year.to_pandas(), values="Llegadas", names="Vigencia",
                          title="Distribución de Llegadas por Año")
        st.plotly_chart(fig_year)

    if "Etnia" in df_arrivals.columns:
        summary_etnia_arr = df_arrivals.group_by("Etnia").agg(pl.col("Personas que llegaron").sum().alias("Llegadas"))
        fig_etnia_arr = px.pie(summary_etnia_arr.to_pandas(), values="Llegadas", names="Etnia",
                               title="Distribución de Llegadas por Etnia")
        st.plotly_chart(fig_etnia_arr)
