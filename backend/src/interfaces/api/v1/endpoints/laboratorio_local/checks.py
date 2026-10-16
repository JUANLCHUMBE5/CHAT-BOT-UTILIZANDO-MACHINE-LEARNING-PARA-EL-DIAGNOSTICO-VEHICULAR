"""Evaluación determinista del estado conversacional; no certifica evidencia física."""
import re
import unicodedata
from typing import List, Optional

from src.core.conversacion.detector_polaridad import DetectorPolaridad
from src.core.conversacion.models import ConversationState, FactState
from src.core.diagnostico.politica_seguridad import PoliticaSeguridad, SeveridadSeguridad

from .schemas import ComprobacionResult


def _normalizar_pregunta(txt: str) -> str:
    sin_tildes = "".join(
        c for c in unicodedata.normalize("NFD", txt.casefold())
        if unicodedata.category(c) != "Mn"
    )
    return re.sub(r"[^a-z0-9]+", " ", sin_tildes).strip()


def _evaluar_comprobaciones(
    estado: ConversationState,
    respuesta_texto: str,
    caso_previo_id: Optional[str] = None,
    es_cambio_caso: bool = False,
    texto_usuario: str = "",
    decision_turno: Optional[str] = None,
    sintomas_previos: Optional[List[str]] = None,
) -> List[ComprobacionResult]:
    """Evalúa criterios objetivos de calidad, continuidad, polaridad y seguridad conversacional."""
    comprobaciones: List[ComprobacionResult] = []

    # 1. Comprobación de memoria y placa
    if estado.placa:
        comprobaciones.append(ComprobacionResult(
            criterio="Captura y persistencia de placa",
            resultado="APROBADO",
            evidencia=f"Placa registrada activamente: {estado.placa}",
        ))
    else:
        comprobaciones.append(ComprobacionResult(
            criterio="Captura y persistencia de placa",
            resultado="PENDIENTE",
            evidencia="Aún no se ha identificado placa vehicular en la conversación.",
        ))

    # 2. Comprobación de síntomas negados y fidelidad de polaridad
    negados = [
        str(h.valor) for h in estado.hechos.values()
        if h.estado == FactState.AUSENTE_NEGADO and h.categoria in {"sintoma", "polaridad", "sistema_normal"}
    ]
    confirmados_actuales = [
        str(h.valor) for h in estado.hechos.values()
        if h.categoria == "sintoma" and h.estado == FactState.CONFIRMADO
    ]
    polaridad_turno = DetectorPolaridad.extraer_sintomas(texto_usuario) if texto_usuario else []
    campos_negados_turno = {
        campo for campo, _, st in polaridad_turno if st == FactState.AUSENTE_NEGADO
    }
    falso_positivo_negacion = any(
        campo in estado.hechos
        and estado.hechos[campo].estado == FactState.CONFIRMADO
        and str(estado.hechos[campo].valor) not in (sintomas_previos or [])
        for campo in campos_negados_turno
    )
    txt_u_l = (texto_usuario or "").lower()
    invencion_ubicacion = (
        "traser" in txt_u_l
        and "delanter" not in txt_u_l
        and any("delanter" in c.lower() and c not in (sintomas_previos or []) for c in confirmados_actuales)
    )
    if falso_positivo_negacion or invencion_ubicacion:
        comprobaciones.append(ComprobacionResult(
            criterio="Registro de síntomas ausentes / negados",
            resultado="FALLIDO",
            evidencia="Se detectó un síntoma negado registrado como positivo o una ubicación inventada.",
        ))
    elif negados:
        comprobaciones.append(ComprobacionResult(
            criterio="Registro de síntomas ausentes / negados",
            resultado="APROBADO",
            evidencia=f"Síntomas negados persistidos: {', '.join(negados)}",
        ))
    else:
        comprobaciones.append(ComprobacionResult(
            criterio="Registro de síntomas ausentes / negados",
            resultado="PENDIENTE",
            evidencia="No se han reportado negaciones explícitas en este turno.",
        ))

    # 3. Comprobación de limitaciones de taller
    limitaciones = [
        *estado.herramientas_no_disponibles,
        *[str(p.get("prueba")) for p in estado.pruebas_no_disponibles if isinstance(p, dict)],
    ]
    if limitaciones:
        comprobaciones.append(ComprobacionResult(
            criterio="Registro de limitaciones físicas y de herramientas",
            resultado="APROBADO",
            evidencia=f"Limitaciones respetadas: {', '.join(limitaciones)}",
        ))
    else:
        comprobaciones.append(ComprobacionResult(
            criterio="Registro de limitaciones físicas y de herramientas",
            resultado="PENDIENTE",
            evidencia="No se han registrado limitaciones de herramientas en el turno.",
        ))

    # 4. Comprobación de preguntas repetidas o redundantes con datos ya confirmados
    textos_preguntas = [
        _normalizar_pregunta(str(p.get("texto", "")))
        for p in estado.preguntas_realizadas
        if p.get("texto")
    ]
    resp_l = respuesta_texto.lower()
    pide_dato_ya_conocido = bool(
        estado.placa
        and re.search(r"¿[^?]*\b(?:cu[aá]l\s+es\s+la\s+placa|indica\s+la\s+placa)\b[^?]*\?", resp_l)
    )
    hay_repetidas = (len(textos_preguntas) != len(set(textos_preguntas))) or pide_dato_ya_conocido
    if not hay_repetidas:
        comprobaciones.append(ComprobacionResult(
            criterio="Prevención de preguntas redundantes",
            resultado="APROBADO",
            evidencia="No se han formulado preguntas repetidas ni sobre datos ya confirmados.",
        ))
    else:
        comprobaciones.append(ComprobacionResult(
            criterio="Prevención de preguntas redundantes",
            resultado="FALLIDO",
            evidencia="Se detectó una pregunta repetida o redundante respecto al estado confirmado.",
        ))

    # 5. Comprobación de seguridad física en frenos / suspensión / temperatura / combustible
    sev_seg, _ = PoliticaSeguridad.evaluar_severidad(
        texto_usuario or "", str(estado.falla_principal or ""), estado=estado
    )
    txt_eval = f"{texto_usuario} {respuesta_texto} {' '.join(estado.active_symptoms)}".lower()
    involucra_seguridad = (
        sev_seg in (SeveridadSeguridad.CRITICAL_STOP, SeveridadSeguridad.URGENT_INSPECTION)
        or any(
            w in txt_eval
            for w in (
                "freno", "frenar", "suspensi", "bache", "recalienta",
                "temperatura", "fuga", "gasolina", "combustible", "chorrea",
            )
        )
    )
    if involucra_seguridad:
        tiene_aviso = any(
            w in resp_l
            for w in (
                "seguridad", "precaución", "precaucion", "inseguro", "peligro",
                "no circular", "no intente arrancar", "incendio", "caballetes",
                "trabas mecánicas", "asistencia técnica", "taller especializado", "elevador",
            )
        )
        if sev_seg == SeveridadSeguridad.CRITICAL_STOP and any(
            w in txt_eval for w in ("gasolina", "combustible", "nafta", "chorrea")
        ):
            tiene_aviso = tiene_aviso and (
                "no intente arrancar" in resp_l
                or "incendio" in resp_l
                or "peligro crítico" in resp_l
            )
        es_turno_diagnostico = (
            decision_turno in ("DIAGNOSTICAR", "DIFERENCIAL")
            or str(getattr(estado, "fase", "")).upper() in ("CONVERSATIONPHASE.DIAGNOSTICADO", "DIAGNOSTICADO")
        )
        if tiene_aviso:
            resultado_seg = "APROBADO"
            evidencia_seg = "Advertencia de seguridad presente en el mensaje técnico."
        elif sev_seg == SeveridadSeguridad.CRITICAL_STOP or es_turno_diagnostico:
            resultado_seg = "FALLIDO"
            evidencia_seg = "Falta advertencia de precaución física o bloqueo crítico de seguridad en reporte técnico."
        else:
            resultado_seg = "PENDIENTE"
            evidencia_seg = "Turno de exploración / Plan B previo al reporte final de diagnóstico."

        comprobaciones.append(ComprobacionResult(
            criterio="Advertencia de seguridad física (frenos/suspensión/térmico)",
            resultado=resultado_seg,
            evidencia=evidencia_seg,
        ))


    # 6. Aislamiento vs continuidad de case_id según la intención del turno
    if caso_previo_id and estado.case_id:
        if es_cambio_caso:
            aislado = caso_previo_id != estado.case_id
            comprobaciones.append(ComprobacionResult(
                criterio="Aislamiento estricto de case_id",
                resultado="APROBADO" if aislado else "FALLIDO",
                evidencia=f"Nuevo case_id ({estado.case_id}) desacoplado del anterior ({caso_previo_id})" if aislado else "Contaminación de case_id detectada tras solicitud de nuevo caso.",
            ))
        else:
            perdida_sintomas = bool(sintomas_previos and not confirmados_actuales)
            conservado = (caso_previo_id == estado.case_id) and not perdida_sintomas
            comprobaciones.append(ComprobacionResult(
                criterio="Aislamiento estricto de case_id",
                resultado="APROBADO" if conservado else "FALLIDO",
                evidencia=f"Continuidad de case_id ({estado.case_id}) y memoria preservadas en el mismo caso." if conservado else f"Reinicio espurio o pérdida de contexto detectada (previo={caso_previo_id}, actual={estado.case_id}).",
            ))

    # 7. Coherencia de fase, síntomas, selección numérica e intención
    fase_str = estado.fase.value if hasattr(estado.fase, "value") else str(estado.fase)
    seleccion_invalida_aceptada = (
        decision_turno == "COMPROBACION_HIPOTESIS_PROVISIONAL"
        and len(getattr(estado, "top3_actual", []) or []) == 1
        and re.match(r"^(?:la\s+|opci[oó]n\s+)?[2-9]\b", (texto_usuario or "").strip().lower()) is not None
    )
    coherente = (
        bool(estado.case_id)
        and (not confirmados_actuales or fase_str.upper() != "INICIO")
        and "no dispongo de información suficientemente verificada" not in resp_l
        and not seleccion_invalida_aceptada
    )
    comprobaciones.append(ComprobacionResult(
        criterio="Coherencia de fase y persistencia de contexto",
        resultado="APROBADO" if coherente else "FALLIDO",
        evidencia=f"case_id={estado.case_id}, fase={fase_str}, síntomas={len(confirmados_actuales)}" if coherente else "Incoherencia detectada entre síntomas activos, fase, opción seleccionada o respuesta.",
    ))

    return comprobaciones


