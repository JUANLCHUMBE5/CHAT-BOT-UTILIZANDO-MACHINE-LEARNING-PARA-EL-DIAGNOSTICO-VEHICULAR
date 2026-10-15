"""Proyección paginada del tracker CSV conservando los valores pendientes."""

from collections.abc import Callable

import pandas as pd

from src.interfaces.api.v1.dtos.validacion import CasoValidacionDTO


def presentar_casos_csv(
    df: pd.DataFrame,
    taller_id_auth: str,
    _pseudonimizar_placa: Callable[[str], tuple[str, str]],
    *,
    fase: str | None,
    tipo_registro: str | None,
    estado_registro: str | None,
    marca: str | None,
    acierto: int | None,
    busqueda: str | None,
    skip: int,
    limit: int,
) -> dict:
    if df.empty:
        return {"total": 0, "skip": skip, "limit": limit, "casos": []}

    # Aplicar filtros
    if fase:
        df = df[df["fase"].astype(str).str.lower() == fase.strip().lower()]
    if tipo_registro:
        df = df[df["tipo_registro"] == tipo_registro] if "tipo_registro" in df.columns else df.iloc[0:0]
    if estado_registro:
        df = df[df["estado_registro"] == estado_registro] if "estado_registro" in df.columns else df.iloc[0:0]
    if marca:
        df = df[df["marca_modelo"].astype(str).str.contains(marca.strip(), case=False, na=False)]
    if acierto is not None:
        df = df[df["prediccion_correcta"] == acierto]
    if busqueda:
        term = busqueda.strip()
        mask = (
            df["sintoma"].astype(str).str.contains(term, case=False, na=False)
            | df["falla_real"].astype(str).str.contains(term, case=False, na=False)
            | df["chatbot_prediccion"].astype(str).str.contains(term, case=False, na=False)
            | df["placa"].astype(str).str.contains(term, case=False, na=False)
            | df["marca_modelo"].astype(str).str.contains(term, case=False, na=False)
        )
        df = df[mask]

    total_filtrado = len(df)
    df_pagina = df.sort_values(["fecha", "item"], ascending=False, kind="stable").iloc[skip : skip + limit]

    casos_lista = []
    for r in df_pagina.to_dict(orient="records"):
        placa_raw = str(r.get("placa", ""))

        # Recuperar placa_hash persistido si ya existe en el registro
        p_hash_existente = str(r.get("placa_hash", "")).strip() if pd.notna(r.get("placa_hash")) else ""
        if p_hash_existente:
            p_hash = p_hash_existente
            enmascarada = (
                placa_raw if ("-" in placa_raw and "***" in placa_raw) else _pseudonimizar_placa(placa_raw)[0]
            )
        else:
            enmascarada, p_hash = _pseudonimizar_placa(placa_raw)

        fase_registro = str(r.get("fase", ""))
        diagnostico_registrado = (
            str(r.get("chatbot_prediccion")) if pd.notna(r.get("chatbot_prediccion")) else ""
        )
        es_pretest = fase_registro.strip().casefold() in {"pre-test", "pretest"}
        casos_lista.append(
            CasoValidacionDTO(
                item=int(r.get("item", 0)),
                fase=fase_registro,
                fecha=str(r.get("fecha", "")),
                placa_enmascarada=enmascarada,
                placa_hash=p_hash,
                marca_modelo=str(r.get("marca_modelo", "")),
                sintoma=str(r.get("sintoma", "")),
                descripcion_sintoma=str(r.get("descripcion_sintoma", ""))
                if pd.notna(r.get("descripcion_sintoma"))
                else None,
                vehiculo_anio=int(r.get("vehiculo_anio")) if pd.notna(r.get("vehiculo_anio")) else None,
                vehiculo_kilometraje=int(r.get("vehiculo_kilometraje"))
                if pd.notna(r.get("vehiculo_kilometraje"))
                else None,
                vehiculo_combustible=str(r.get("vehiculo_combustible", ""))
                if pd.notna(r.get("vehiculo_combustible"))
                else None,
                vehiculo_transmision=str(r.get("vehiculo_transmision", ""))
                if pd.notna(r.get("vehiculo_transmision"))
                else None,
                falla_real=str(r.get("falla_real")) if pd.notna(r.get("falla_real")) else None,
                chatbot_prediccion=diagnostico_registrado,
                diagnostico_preliminar_sin_chatbot=diagnostico_registrado if es_pretest else None,
                falla_sugerida_chatbot=None if es_pretest else diagnostico_registrado,
                campos_completos=(
                    int(r.get("campos_completos"))
                    if pd.notna(r.get("campos_completos")) and int(r.get("campos_completos")) in (0, 1)
                    else 0
                ),
                cantidad_campos_completos=(
                    int(r.get("cantidad_campos_completos"))
                    if pd.notna(r.get("cantidad_campos_completos"))
                    else 0
                ),
                detalles_campos=r.get("detalles_campos")
                if isinstance(r.get("detalles_campos"), dict)
                else None,
                tiempo_diagnostico_minutos=(
                    int(r.get("tiempo_diagnostico_minutos"))
                    if pd.notna(r.get("tiempo_diagnostico_minutos"))
                    else None
                ),
                prediccion_correcta=(
                    int(r.get("prediccion_correcta"))
                    if pd.notna(r.get("prediccion_correcta")) and int(r.get("prediccion_correcta")) in (0, 1)
                    else None
                ),
                taller_id=str(r.get("taller_id", taller_id_auth)),
                mecanico_id=str(r.get("mecanico_id")) if pd.notna(r.get("mecanico_id")) else None,
                metodo_confirmacion=str(r.get("metodo_confirmacion"))
                if pd.notna(r.get("metodo_confirmacion"))
                else None,
                evidencia_ref=str(r.get("evidencia_ref", "")) if pd.notna(r.get("evidencia_ref")) else None,
                estado_registro=str(r.get("estado_registro"))
                if pd.notna(r.get("estado_registro"))
                else "borrador",
                tipo_registro=str(r.get("tipo_registro"))
                if pd.notna(r.get("tipo_registro"))
                else "DEVELOPMENT",
                conversacion_id=str(r.get("conversacion_id", ""))
                if pd.notna(r.get("conversacion_id"))
                else None,
                diagnostico_id=str(r.get("diagnostico_id", ""))
                if pd.notna(r.get("diagnostico_id"))
                else None,
                validado_por_id=str(r.get("validado_por_id")) if pd.notna(r.get("validado_por_id")) else None,
                fecha_validacion=str(r.get("fecha_validacion"))
                if pd.notna(r.get("fecha_validacion"))
                else None,
            )
        )

    return {
        "total": total_filtrado,
        "skip": skip,
        "limit": limit,
        "casos": [c.model_dump() for c in casos_lista],
    }
