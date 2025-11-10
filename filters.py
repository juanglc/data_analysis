import polars as pl


def apply_filters(
        df,
        selected_departments=["Todos"],
        selected_years=["Todos"],
        selected_fact=["Todos"],
        selected_ciclo_vital=["Todos"],
        selected_etnia=["Todos"]
):
    """Aplica filtros múltiples al DataFrame"""

    # Filtro de departamentos
    if "Todos" not in selected_departments and "ESTADO_DEPTO" in df.columns:
        if selected_departments:  # Verificar que no esté vacío
            df = df.filter(pl.col("ESTADO_DEPTO").is_in(selected_departments))

    # Filtro de años
    if "Todos" not in selected_years and "Vigencia" in df.columns:
        if selected_years:  # Verificar que no esté vacío
            df = df.filter(pl.col("Vigencia").is_in(selected_years))

    # Filtro de hechos victimizantes
    if "Todos" not in selected_fact and "Tipo o Nombre de Hecho Victimizante" in df.columns:
        if selected_fact:  # Verificar que no esté vacío
            df = df.filter(pl.col("Tipo o Nombre de Hecho Victimizante").is_in(selected_fact))

    # Filtro de etnia
    if "Todos" not in selected_etnia and "Etnia" in df.columns:
        if selected_etnia:  # Verificar que no esté vacío
            df = df.filter(pl.col("Etnia").is_in(selected_etnia))

    # Filtro de ciclo vital
    if "Todos" not in selected_ciclo_vital and "Ciclo vital" in df.columns:
        if selected_ciclo_vital:  # Verificar que no esté vacío
            df = df.filter(pl.col("Ciclo vital").is_in(selected_ciclo_vital))

    return df
