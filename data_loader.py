import polars as pl


def load_and_prepare_csv(path: str):
    """Carga y prepara los datos CSV con manejo de errores"""
    try:
        df = pl.read_csv(path, truncate_ragged_lines=True, ignore_errors=True)
        df = df.rename({c: c.strip().upper() for c in df.columns})

        # Columnas a eliminar
        drop_list = ["FECHA_CORTE", "COD_ESTADO_DEPTO", "PARAM_HECHO"]

        for col in drop_list:
            if col in df.columns:
                df = df.drop(col)

        # Mapeo de nombres a español descriptivo
        column_rename_map = {
            "HECHO": "Tipo o Nombre de Hecho Victimizante",
            "SEXO": "Sexo",
            "ETNIA": "Etnia",
            "DISCAPACIDAD": "Discapacidad",
            "CICLO_VITAL": "Ciclo vital",
            "PER_OCU": "Personas por ocurrencia",
            "PER_SA": "Personas sujetas a atención",
            "EVENTOS": "Eventos",
            "VIGENCIA": "Vigencia",
            "PER_LLEGADA": "Personas que llegaron"
        }

        df = df.rename({k: v for k, v in column_rename_map.items() if k in df.columns})

        # Limpieza de datos: reemplazar valores nulos
        for col in df.columns:
            if df[col].dtype == pl.Utf8:
                df = df.with_columns(
                    pl.col(col).fill_null("No especificado")
                )

        return df

    except Exception as e:
        raise Exception(f"Error al cargar el archivo {path}: {str(e)}")
