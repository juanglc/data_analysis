import io
import tempfile
from datetime import datetime
from reportlab.lib.pagesizes import A4, letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, Image, Table, TableStyle, KeepTogether
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from reportlab.lib import colors
import plotly.express as px
import plotly.graph_objects as go
import polars as pl


def generate_plotly_image(fig, width=600, height=400):
    """
    Convierte una figura de Plotly a bytes de imagen PNG
    """
    try:
        img_bytes = fig.to_image(format="png", width=width, height=height, engine="kaleido")
        return io.BytesIO(img_bytes)
    except Exception as e:
        print(f"Error generando imagen: {e}")
        return None


def create_complete_pdf_report(df_subjects: pl.DataFrame, df_arrivals: pl.DataFrame, filters_applied: dict,
                               theme: str = "plotly"):
    """
    Genera un PDF completo con TODAS las visualizaciones del dashboard
    """

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=A4,
        rightMargin=40,
        leftMargin=40,
        topMargin=50,
        bottomMargin=30
    )

    story = []
    styles = getSampleStyleSheet()

    # Estilos personalizados
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=20,
        textColor=colors.HexColor('#1f77b4'),
        spaceAfter=20,
        alignment=TA_CENTER,
        fontName='Helvetica-Bold'
    )

    section_style = ParagraphStyle(
        'SectionHeader',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#ff7f0e'),
        spaceAfter=10,
        spaceBefore=15,
        fontName='Helvetica-Bold'
    )

    subsection_style = ParagraphStyle(
        'SubsectionHeader',
        parent=styles['Heading3'],
        fontSize=12,
        textColor=colors.HexColor('#2ca02c'),
        spaceAfter=8,
        fontName='Helvetica-Bold'
    )

    normal_style = ParagraphStyle(
        'CustomNormal',
        parent=styles['Normal'],
        fontSize=10,
        alignment=TA_JUSTIFY,
        spaceAfter=8
    )

    # ============================================
    # PORTADA
    # ============================================
    story.append(Spacer(1, 1.5 * inch))
    story.append(Paragraph("📊 Análisis de Víctimas de Desplazamiento Forzado en Colombia", title_style))
    story.append(Spacer(1, 0.3 * inch))

    fecha_reporte = datetime.now().strftime("%d de %B de %Y - %H:%M")
    story.append(Paragraph(f"<b>Fecha del Reporte:</b> {fecha_reporte}", normal_style))
    story.append(Spacer(1, 0.2 * inch))

    # Filtros aplicados
    if any(v != ["Todos"] for v in filters_applied.values()):
        story.append(Paragraph("<b>Filtros Aplicados:</b>", subsection_style))
        for filter_name, filter_value in filters_applied.items():
            if filter_value != ["Todos"]:
                filter_text = f"• <b>{filter_name}:</b> {', '.join(map(str, filter_value[:3]))}"
                if len(filter_value) > 3:
                    filter_text += f" (y {len(filter_value) - 3} más)"
                story.append(Paragraph(filter_text, normal_style))
        story.append(Spacer(1, 0.2 * inch))

    story.append(Paragraph(
        "<b>Contexto:</b> Este reporte presenta un análisis integral de los datos de desplazamiento forzado "
        "por violencia en Colombia, con todas las visualizaciones y análisis del dashboard.",
        normal_style
    ))
    story.append(PageBreak())

    # ============================================
    # SECCIÓN 1: KPIs
    # ============================================
    story.append(Paragraph("📈 Indicadores Clave de Impacto", section_style))

    total_victims = int(
        df_subjects["Personas por ocurrencia"].sum()) if "Personas por ocurrencia" in df_subjects.columns else 0
    total_displaced = int(
        df_arrivals["Personas que llegaron"].sum()) if "Personas que llegaron" in df_arrivals.columns else 0
    total_events = int(df_arrivals["Eventos"].sum()) if "Eventos" in df_arrivals.columns else 0
    unique_depts = df_arrivals["ESTADO_DEPTO"].n_unique() if "ESTADO_DEPTO" in df_arrivals.columns else 0

    kpi_data = [
        ['Indicador', 'Valor'],
        ['👥 Total Personas Afectadas', f'{total_victims:,}'],
        ['🚶 Personas Desplazadas', f'{total_displaced:,}'],
        ['⚠️ Eventos Registrados', f'{total_events:,}'],
        ['🗺️ Departamentos Afectados', f'{unique_depts}']
    ]

    kpi_table = Table(kpi_data, colWidths=[3.5 * inch, 2 * inch])
    kpi_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#1f77b4')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 11),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 10),
        ('BACKGROUND', (0, 1), (-1, -1), colors.lightgrey),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 10),
    ]))

    story.append(kpi_table)
    story.append(PageBreak())

    # ============================================
    # SECCIÓN 2: ANÁLISIS TEMPORAL
    # ============================================
    story.append(Paragraph("⏱️ Análisis Temporal", section_style))

    if "Vigencia" in df_arrivals.columns and "Personas que llegaron" in df_arrivals.columns:
        yearly_data = df_arrivals.group_by("Vigencia").agg([
            pl.col("Personas que llegaron").sum().alias("Personas Desplazadas"),
            pl.col("Eventos").sum().alias("Eventos")
        ]).sort("Vigencia")

        # Gráfico de línea temporal
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
            height=350
        )

        img_buffer = generate_plotly_image(fig, width=700, height=350)
        if img_buffer:
            story.append(Image(img_buffer, width=6.5 * inch, height=3.2 * inch))
            story.append(Spacer(1, 0.2 * inch))

        # Gráfico de barras de eventos
        yearly_events = df_arrivals.group_by("Vigencia").agg([
            pl.col("Eventos").sum().alias("Total Eventos")
        ]).sort("Vigencia")

        fig2 = px.bar(
            yearly_events.to_pandas(),
            x="Vigencia",
            y="Total Eventos",
            title="Eventos de Desplazamiento por Año",
            labels={"Total Eventos": "Número de Eventos", "Vigencia": "Año"},
            color="Total Eventos",
            color_continuous_scale="Reds",
            template=theme
        )
        fig2.update_layout(height=350)

        img_buffer2 = generate_plotly_image(fig2, width=700, height=350)
        if img_buffer2:
            story.append(Image(img_buffer2, width=6.5 * inch, height=3.2 * inch))

    story.append(PageBreak())

    # ============================================
    # SECCIÓN 3: DISTRIBUCIÓN GEOGRÁFICA
    # ============================================
    story.append(Paragraph("🗺️ Distribución Geográfica", section_style))

    if "ESTADO_DEPTO" in df_arrivals.columns:
        dept_summary = df_arrivals.group_by("ESTADO_DEPTO").agg([
            pl.col("Personas que llegaron").sum().alias("Personas Desplazadas"),
            pl.col("Eventos").sum().alias("Eventos")
        ]).sort("Personas Desplazadas", descending=True).head(10)

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
        fig.update_layout(height=450)

        img_buffer = generate_plotly_image(fig, width=700, height=450)
        if img_buffer:
            story.append(Image(img_buffer, width=6.5 * inch, height=4 * inch))
            story.append(Spacer(1, 0.2 * inch))

        # Tabla de departamentos
        dept_data = [['Departamento', 'Personas', 'Eventos']]
        for row in dept_summary.head(10).iter_rows():
            dept_data.append([row[0], f'{int(row[1]):,}', f'{int(row[2]):,}'])

        dept_table = Table(dept_data, colWidths=[2.5 * inch, 2 * inch, 1.5 * inch])
        dept_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2ca02c')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BACKGROUND', (0, 1), (-1, -1), colors.lightblue),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
        ]))
        story.append(dept_table)

    story.append(PageBreak())

    # ============================================
    # SECCIÓN 4: ANÁLISIS DEMOGRÁFICO
    # ============================================
    story.append(Paragraph("👥 Perfil Demográfico de las Víctimas", section_style))

    # Etnia
    if "Etnia" in df_subjects.columns:
        story.append(Paragraph("Distribución por Etnia", subsection_style))
        etnia_summary = df_subjects.group_by("Etnia").agg(
            pl.col("Personas por ocurrencia").sum().alias("Total")
        ).sort("Total", descending=True).head(8)

        fig = px.pie(
            etnia_summary.to_pandas(),
            values="Total",
            names="Etnia",
            title="Distribución por Etnia",
            hole=0.4,
            template=theme
        )
        fig.update_layout(height=350)

        img_buffer = generate_plotly_image(fig, width=600, height=350)
        if img_buffer:
            story.append(Image(img_buffer, width=5.5 * inch, height=3.2 * inch))
            story.append(Spacer(1, 0.2 * inch))

    # Ciclo Vital
    if "Ciclo vital" in df_subjects.columns:
        story.append(Paragraph("Distribución por Ciclo Vital", subsection_style))
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
        fig.update_xaxes(tickangle=-45)
        fig.update_layout(height=350)

        img_buffer = generate_plotly_image(fig, width=700, height=350)
        if img_buffer:
            story.append(Image(img_buffer, width=6.5 * inch, height=3.2 * inch))

    story.append(PageBreak())

    # ============================================
    # SECCIÓN 5: ANÁLISIS COMPARATIVO
    # ============================================
    story.append(Paragraph("🔄 Análisis Comparativo", section_style))

    if "Tipo o Nombre de Hecho Victimizante" in df_subjects.columns:
        hecho_summary = df_subjects.group_by("Tipo o Nombre de Hecho Victimizante").agg(
            pl.col("Personas por ocurrencia").sum().alias("Total Víctimas")
        ).sort("Total Víctimas", descending=True).head(8)

        fig = px.treemap(
            hecho_summary.to_pandas(),
            path=["Tipo o Nombre de Hecho Victimizante"],
            values="Total Víctimas",
            title="Distribución de Hechos Victimizantes",
            color="Total Víctimas",
            color_continuous_scale="RdYlGn_r",
            template=theme
        )
        fig.update_layout(height=400)

        img_buffer = generate_plotly_image(fig, width=700, height=400)
        if img_buffer:
            story.append(Image(img_buffer, width=6.5 * inch, height=3.7 * inch))

    story.append(PageBreak())

    # ============================================
    # SECCIÓN 6: ANÁLISIS DE MINORÍAS ÉTNICAS
    # ============================================
    story.append(Paragraph("🌍 Análisis de Minorías Étnicas", section_style))

    minorities_only = df_subjects.filter(
        ~pl.col("Etnia").str.to_lowercase().is_in(["ninguna", "no informa", "sin información", "no especificado", "nd"])
    )

    if minorities_only.shape[0] > 0:
        etnia_detailed = minorities_only.group_by("Etnia").agg([
            pl.col("Personas por ocurrencia").sum().alias("Total Víctimas")
        ]).sort("Total Víctimas", descending=True).head(10)

        fig = px.bar(
            etnia_detailed.to_pandas(),
            x="Etnia",
            y="Total Víctimas",
            title="Impacto en Minorías Étnicas (Excluye 'Ninguna')",
            color="Total Víctimas",
            color_continuous_scale="Reds",
            template=theme
        )
        fig.update_xaxes(tickangle=-45)
        fig.update_layout(height=400)

        img_buffer = generate_plotly_image(fig, width=700, height=400)
        if img_buffer:
            story.append(Image(img_buffer, width=6.5 * inch, height=3.7 * inch))

    story.append(PageBreak())

    # ============================================
    # SECCIÓN 7: ANÁLISIS DE MENORES
    # ============================================
    story.append(Paragraph("👶 Análisis de Menores de Edad", section_style))

    child_categories = ['entre 0 y 5', 'entre 6 y 11', 'entre 12 y 17']
    children_df = df_subjects.filter(pl.col("Ciclo vital").is_in(child_categories))

    if children_df.shape[0] > 0:
        age_labels = {
            'entre 0 y 5': 'Primera Infancia (0-5)',
            'entre 6 y 11': 'Infancia (6-11)',
            'entre 12 y 17': 'Adolescencia (12-17)'
        }

        age_distribution = children_df.group_by("Ciclo vital").agg(
            pl.col("Personas por ocurrencia").sum().alias("Total Víctimas")
        ).sort("Ciclo vital")

        age_dist_df = age_distribution.to_pandas()
        age_dist_df['Etiqueta'] = age_dist_df['Ciclo vital'].map(age_labels)

        fig = px.pie(
            age_dist_df,
            values="Total Víctimas",
            names="Etiqueta",
            title="Distribución de Menores Víctimas por Grupo de Edad",
            hole=0.4,
            template=theme
        )
        fig.update_layout(height=350)

        img_buffer = generate_plotly_image(fig, width=600, height=350)
        if img_buffer:
            story.append(Image(img_buffer, width=5.5 * inch, height=3.2 * inch))
            story.append(Spacer(1, 0.2 * inch))

        # Hechos victimizantes contra menores
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
                color="Total Víctimas",
                color_continuous_scale="Reds",
                template=theme
            )
            fig.update_layout(height=450)

            img_buffer = generate_plotly_image(fig, width=700, height=450)
            if img_buffer:
                story.append(Image(img_buffer, width=6.5 * inch, height=4 * inch))

    story.append(PageBreak())

    # ============================================
    # CONCLUSIONES
    # ============================================
    story.append(Paragraph("💡 Conclusiones Principales", section_style))

    conclusiones = """
    <b>1. Magnitud del Desplazamiento:</b><br/>
    Millones de personas afectadas evidencian una crisis humanitaria de décadas. 
    El desplazamiento es la principal consecuencia del conflicto armado.<br/><br/>

    <b>2. Poblaciones Más Vulnerables:</b><br/>
    • Minorías étnicas: Desproporcionadamente afectadas<br/>
    • Menores de edad: Proporción alarmante de víctimas<br/>
    • Mujeres y niñas: Riesgo específico de violencia sexual<br/><br/>

    <b>3. Explotación Infantil:</b><br/>
    El desplazamiento expone a menores a explotación sexual comercial, trabajo forzado y reclutamiento.<br/><br/>

    <b>4. Concentración Geográfica:</b><br/>
    Algunos departamentos concentran la mayoría de llegadas, generando presión sobre infraestructura.
    """
    story.append(Paragraph(conclusiones, normal_style))
    story.append(Spacer(1, 0.3 * inch))

    # Recomendaciones
    story.append(Paragraph("📋 Recomendaciones", section_style))

    recomendaciones = """
    <b>Protección:</b> Protocolos especiales para menores, atención diferencial étnica, rutas de protección inmediata.<br/><br/>
    <b>Datos:</b> Mejorar registro de perpetradores, georreferenciación precisa, seguimiento longitudinal.<br/><br/>
    <b>Justicia:</b> Persecución de explotadores, reparación integral, garantías de no repetición.
    """
    story.append(Paragraph(recomendaciones, normal_style))

    # Footer
    story.append(Spacer(1, 0.5 * inch))
    footer = f"""
    <b>Fuente:</b> Registro Único de Víctimas (RUV) - Colombia<br/>
    <b>Generado:</b> {fecha_reporte}<br/>
    <b>Sistema:</b> Dashboard de Análisis de Desplazamiento Forzado
    """
    story.append(Paragraph(footer, normal_style))

    # Construir PDF
    doc.build(story)
    buffer.seek(0)

    return buffer
