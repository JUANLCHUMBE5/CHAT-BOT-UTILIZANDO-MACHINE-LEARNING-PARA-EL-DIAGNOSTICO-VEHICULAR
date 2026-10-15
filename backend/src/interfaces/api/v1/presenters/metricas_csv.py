"""Indicadores CSV trazables: sin imputaciones ni inclusión de cohortes de prueba."""

import pandas as pd

from src.interfaces.api.v1.dtos.validacion import (
    MetricasValidacionResponseDTO,
    MetricasVariableIndependienteDTO,
)


def _filtrar_df_oficial_verificado(df: pd.DataFrame) -> pd.DataFrame:
    """Falla cerrada: solo muestra filas oficiales con estado y auditoría humana explícitos."""
    requeridas = {
        "tipo_registro",
        "estado_registro",
        "fase",
        "falla_real",
        "metodo_confirmacion",
        "evidencia_ref",
        "validado_por_id",
        "fecha_validacion",
    }
    if df.empty or not requeridas.issubset(df.columns):
        return df.iloc[0:0].copy()

    tipo = df["tipo_registro"].fillna("").astype(str).str.strip()
    fase = df["fase"].fillna("").astype(str).str.strip().str.casefold()
    estado = df["estado_registro"].fillna("").astype(str).str.strip().str.casefold()
    tipo_fase_valido = ((tipo == "THESIS_PRETEST") & fase.isin({"pre-test", "pretest"})) | (
        (tipo == "THESIS_POSTTEST") & fase.isin({"post-test", "posttest"})
    )
    mask = (
        tipo_fase_valido
        & estado.eq("verificado")
        & df["falla_real"].fillna("").astype(str).str.strip().ne("")
        & df["metodo_confirmacion"].fillna("").astype(str).str.strip().ne("")
        & df["evidencia_ref"].fillna("").astype(str).str.strip().ne("")
        & df["validado_por_id"].fillna("").astype(str).str.strip().ne("")
        & pd.to_datetime(df["fecha_validacion"], errors="coerce").notna()
    )
    return df.loc[mask].copy()


def _serie_binaria(df: pd.DataFrame, columna: str) -> pd.Series:
    if columna not in df.columns:
        return pd.Series(index=df.index, dtype="float64")
    valores = pd.to_numeric(df[columna], errors="coerce")
    return valores.where(valores.isin((0, 1)))


def _serie_predicciones_evaluables(df: pd.DataFrame) -> pd.Series:
    """Solo cuenta resultado cuando existen predicción y falla real en una fila verificada."""
    valores = _serie_binaria(df, "prediccion_correcta")
    if "chatbot_prediccion" not in df.columns:
        return valores.where(False)
    tiene_prediccion = df["chatbot_prediccion"].fillna("").astype(str).str.strip().ne("")
    tiene_falla_real = df.get("falla_real", pd.Series(index=df.index, dtype="string"))
    tiene_falla_real = tiene_falla_real.fillna("").astype(str).str.strip().ne("")
    return valores.where(tiene_prediccion & tiene_falla_real)


def presentar_metricas_csv(df_taller: pd.DataFrame) -> MetricasValidacionResponseDTO:
    df = _filtrar_df_oficial_verificado(df_taller)
    fases = (
        df["fase"].astype(str).str.casefold()
        if "fase" in df.columns
        else pd.Series(index=df.index, dtype="string")
    )
    df_pre = df[fases.isin({"pre-test", "pretest"})]
    df_post = df[fases.isin({"post-test", "posttest"})]

    def binaria(filas: pd.DataFrame, columna: str) -> pd.Series:
        return _serie_binaria(filas, columna)

    def porcentaje(valores: pd.Series) -> float | None:
        observados = valores.dropna()
        return round(float(observados.mean()) * 100, 2) if not observados.empty else None

    def tiempo_medido(filas: pd.DataFrame) -> tuple[float | None, int]:
        if "tiempo_diagnostico_minutos" not in filas.columns:
            return None, 0
        valores = pd.to_numeric(filas["tiempo_diagnostico_minutos"], errors="coerce")
        validos = valores[(valores > 0) & (valores < float("inf"))]
        cantidad = int(validos.count())
        promedio = round(float(validos.mean()), 1) if cantidad and cantidad == len(filas) else None
        return promedio, cantidad

    aciertos_pre = _serie_predicciones_evaluables(df_pre)
    aciertos_post = _serie_predicciones_evaluables(df_post)
    todos_aciertos = pd.concat([aciertos_pre, aciertos_post])
    evaluados_pre = int(aciertos_pre.count())
    evaluados_post = int(aciertos_post.count())
    aciertos = int(todos_aciertos.fillna(0).sum())
    predicciones_evaluadas = evaluados_pre + evaluados_post
    tiempo_pre, tiempos_pre = tiempo_medido(df_pre)
    tiempo_post, tiempos_post = tiempo_medido(df_post)
    reduccion_tiempo = (
        round((tiempo_pre - tiempo_post) / tiempo_pre * 100, 2)
        if tiempo_pre is not None and tiempo_post is not None and tiempo_pre > 0
        else None
    )

    def porcentaje_completitud(filas: pd.DataFrame) -> float | None:
        if filas.empty:
            return None
        valores = binaria(filas, "campos_completos")
        return porcentaje(valores) if valores.count() == len(filas) else None

    campos_pre_evaluados = int(binaria(df_pre, "campos_completos").count())
    campos_post_evaluados = int(binaria(df_post, "campos_completos").count())

    # Los indicadores de CarBot se reportan solo en POST-TEST; el PRE-TEST es línea base manual.
    sintomas = binaria(df_post, "sintoma_registrado_correctamente")
    if "procesamiento_validado" in df_post.columns:
        procesamiento = binaria(df_post, "procesamiento_validado")
    elif {"normalizacion_correcta", "extraccion_correcta", "clasificacion_procesada"}.issubset(
        df_post.columns
    ):
        normalizacion = binaria(df_post, "normalizacion_correcta")
        extraccion = binaria(df_post, "extraccion_correcta")
        clasificacion = binaria(df_post, "clasificacion_procesada")
        validos = normalizacion.notna() & extraccion.notna() & clasificacion.notna()
        procesamiento = pd.Series(index=df_post.index, dtype="float64")
        procesamiento.loc[validos] = (
            (normalizacion.loc[validos] == 1)
            & (extraccion.loc[validos] == 1)
            & (clasificacion.loc[validos] == 1)
        ).astype(int)
    else:
        procesamiento = pd.Series(index=df_post.index, dtype="float64")
    predicciones_post = aciertos_post
    vi_metricas = MetricasVariableIndependienteDTO(
        indicador1_sintomas_correctos_pct=porcentaje(sintomas),
        indicador2_procesamiento_correcto_pct=porcentaje(procesamiento),
        indicador3_exactitud_ml_pct=porcentaje(predicciones_post),
        casos_verificados_evaluados=len(df_post),
        casos_sintomas_evaluados=int(sintomas.count()),
        casos_procesamiento_evaluados=int(procesamiento.count()),
        casos_modelo_evaluados=evaluados_post,
        nota_metodologica=(
            "Indicadores de CarBot calculados solo sobre casos POST-TEST oficiales con "
            "revisión humana trazable; no incluyen el diagnóstico manual PRE-TEST."
            if not df_post.empty
            else "Pendiente de registros POST-TEST oficiales con revisión humana trazable."
        ),
    )

    candidatos_oficiales = df_taller
    if "tipo_registro" in candidatos_oficiales.columns and "estado_registro" in candidatos_oficiales.columns:
        candidatos_oficiales = candidatos_oficiales[
            candidatos_oficiales["tipo_registro"].isin(("THESIS_PRETEST", "THESIS_POSTTEST"))
        ]
        borradores = int(
            candidatos_oficiales["estado_registro"].fillna("").astype(str).str.casefold().eq("borrador").sum()
        )
    else:
        borradores = 0
    casos_piloto = (
        int(df_taller["tipo_registro"].eq("PILOT").sum()) if "tipo_registro" in df_taller.columns else 0
    )
    dist_marcas = (
        [{"marca": str(k), "conteo": int(v)} for k, v in df["marca_modelo"].value_counts().head(8).items()]
        if "marca_modelo" in df.columns
        else []
    )
    top_fallas = (
        [{"falla": str(k), "conteo": int(v)} for k, v in df["falla_real"].value_counts().head(8).items()]
        if "falla_real" in df.columns
        else []
    )
    return MetricasValidacionResponseDTO(
        total_casos=len(df),
        total_aciertos=aciertos,
        total_desaciertos=predicciones_evaluadas - aciertos,
        tasa_acierto_global_porcentaje=porcentaje(todos_aciertos),
        casos_pretest=len(df_pre),
        predicciones_evaluadas_pretest=evaluados_pre,
        tasa_acierto_pretest_porcentaje=porcentaje(aciertos_pre),
        tiempos_evaluados_pretest=tiempos_pre,
        tiempo_promedio_pretest_min=tiempo_pre,
        registros_completos_pretest_porcentaje=porcentaje_completitud(df_pre),
        registros_prdc_evaluados_pretest=campos_pre_evaluados,
        casos_posttest=len(df_post),
        predicciones_evaluadas_posttest=evaluados_post,
        tasa_acierto_posttest_porcentaje=porcentaje(aciertos_post),
        tiempos_evaluados_posttest=tiempos_post,
        tiempo_promedio_posttest_min=tiempo_post,
        registros_completos_posttest_porcentaje=porcentaje_completitud(df_post),
        registros_prdc_evaluados_posttest=campos_post_evaluados,
        reduccion_tiempo_porcentaje=reduccion_tiempo,
        casos_piloto=casos_piloto,
        casos_verificados=len(df_post),
        total_casos_verificados=len(df),
        total_casos_borrador=borradores,
        porcentaje_sintomas_correctos=vi_metricas.indicador1_sintomas_correctos_pct,
        porcentaje_datos_procesados_correctos=vi_metricas.indicador2_procesamiento_correcto_pct,
        exactitud_modelo_validada=vi_metricas.indicador3_exactitud_ml_pct,
        variable_independiente=vi_metricas,
        distribucion_marcas=dist_marcas,
        top_fallas_reales=top_fallas,
        nota_metodologica=(
            "Se incluyen solo registros THESIS_PRETEST/THESIS_POSTTEST verificados con autor, fecha, "
            "método y referencia de evidencia explícitos. La referencia no acredita por sí sola una "
            "prueba física; la revisión corresponde a la persona autorizada."
        ),
    )
