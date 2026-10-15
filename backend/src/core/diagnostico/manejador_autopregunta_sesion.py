"""Módulo para resolver respuestas a autopreguntas y aclaraciones técnicas pendientes en la sesión."""

from __future__ import annotations

import time
from typing import Any, Optional, Tuple

from src.core.diagnostico.auto_interrogador import (
    es_rechazo_de_opciones,
    generar_pregunta_descarte_secundario,
    resolver_respuesta_autopregunta,
)
from src.core.diagnostico.models import ResultadoDiagnostico


def manejar_respuesta_autopregunta(
    sesion_pendiente: Any,
    texto_normalizado: str,
    diagnostico_forzado: Optional[str],
    inicio_total: float,
) -> Tuple[Optional[ResultadoDiagnostico], str, Optional[str]]:
    """
    Procesa respuestas cuando la sesión está esperando autopregunta o aclaración.
    Retorna: (resultado_diagnostico, texto_normalizado, diagnostico_forzado)
    """
    idx_opt, txt_opt, diag_canonica = resolver_respuesta_autopregunta(
        texto_normalizado,
        sesion_pendiente.autopregunta_opciones,
        sesion_pendiente.autopregunta_hipotesis,
    )
    if idx_opt is not None:
        sintoma_base = sesion_pendiente.autopregunta_sintoma_base or sesion_pendiente.obtener_sintoma_completo()
        texto_evaluar = f"{sintoma_base}. Confirmación técnica: {txt_opt}".strip()
        sesion_pendiente.sintomas = [texto_evaluar]
        sesion_pendiente.estado = "en_proceso"
        otras_hipotesis = [
            h for i, h in enumerate(sesion_pendiente.autopregunta_hipotesis) if i != idx_opt
        ]
        sesion_pendiente.ultimas_hipotesis_diferenciales = otras_hipotesis
        sesion_pendiente.autopregunta_sintoma_base = None
        sesion_pendiente.autopregunta_opciones = []
        sesion_pendiente.autopregunta_hipotesis = []
        return None, texto_evaluar, diag_canonica

    if es_rechazo_de_opciones(texto_normalizado):
        sintoma_base = sesion_pendiente.autopregunta_sintoma_base or sesion_pendiente.obtener_sintoma_completo()
        hipotesis_descartadas = list(sesion_pendiente.autopregunta_hipotesis)
        sesion_pendiente.ultimas_hipotesis_diferenciales = hipotesis_descartadas
        sesion_pendiente.autopregunta_opciones = []
        sesion_pendiente.autopregunta_hipotesis = []
        sesion_pendiente.estado = "esperando_aclaracion_sintoma"

        mensaje_descarte = generar_pregunta_descarte_secundario(sintoma_base, hipotesis_descartadas)
        res = ResultadoDiagnostico(
            respuesta_texto=mensaje_descarte,
            diagnostico_ml="Descarte de opciones previas / Solicitud de aclaración técnica",
            confianza_ml=0.0,
            contexto_manual="",
            titulo_manual="",
            requiere_revision_humana=True,
            estado_sesion="esperando_aclaracion_sintoma",
            modo_diagnostico="esperando_clarificacion",
            sintoma_evaluado=sintoma_base,
            tipo_consulta="aclaracion",
            tiempo_ml_ms=0,
            tiempo_total_ms=max(0, int((time.perf_counter() - inicio_total) * 1000)),
        )
        return res, texto_normalizado, diagnostico_forzado

    es_cambio = any(
        f in texto_normalizado.lower()
        for f in (
            "otro problema", "otra falla", "nuevo problema", "hola", "buenas", "reiniciar",
            "el cliente dejó", "el cliente dejo", "el cliente trajo", "el cliente dice",
            "el cliente indica", "otro vehículo", "otro vehiculo", "otro carro", "este es otro",
            "nuevo caso", "tengo otro", "ahora presenta", "ahora el problema", "ahora revisemos",
            "ya revisaré", "ya revisare", "olvida lo anterior", "eso ya lo revisé", "eso ya lo revise"
        )
    )
    sintoma_base = sesion_pendiente.autopregunta_sintoma_base or sesion_pendiente.obtener_sintoma_completo()
    if sintoma_base and not es_cambio:
        descarte_previo = ""
        if sesion_pendiente.ultimas_hipotesis_diferenciales:
            descarte_previo = f" Descarte previo: no es {', '.join(sesion_pendiente.ultimas_hipotesis_diferenciales[:2])}."
        texto_evaluar = f"{sintoma_base}.{descarte_previo} Aclaración técnica del mecánico: {texto_normalizado}".strip()
        sesion_pendiente.sintomas = [texto_evaluar]
        sesion_pendiente.estado = "en_proceso"
        sesion_pendiente.autopregunta_sintoma_base = None
        sesion_pendiente.autopregunta_opciones = []
        sesion_pendiente.autopregunta_hipotesis = []
        return None, texto_evaluar, diagnostico_forzado
    elif es_cambio:
        sesion_pendiente.reiniciar()

    return None, texto_normalizado, diagnostico_forzado
