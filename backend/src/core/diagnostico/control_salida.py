"""Barrera compartida para las fachadas REST y consultas técnicas sin conversación."""

from functools import wraps

from src.infrastructure.rag.contrato_documental import proteger_salida_conversacional
from src.infrastructure.rag.documental_salida import es_solicitud_especificacion, limpiar_advertencia


def con_gobernanza_documental(func):
    @wraps(func)
    def control(gestor, *args, **kwargs):
        texto = args[0] if args else kwargs.get("texto_usuario", kwargs.get("pregunta", ""))
        from src.core.diagnostico.models import ResultadoDiagnostico
        from src.core.diagnostico.politica_seguridad import PoliticaSeguridad, SeveridadSeguridad

        sesion_id = kwargs.get("session_id") or kwargs.get("conversacion_id")
        sesion = gestor.session_manager.obtener_sesion(sesion_id) if sesion_id else None
        estado = getattr(sesion, "conversation_state", None)
        if not kwargs.get("orquestado", False):
            severidad, banner = PoliticaSeguridad.evaluar_severidad(texto, "", estado=estado)
            if severidad == SeveridadSeguridad.CRITICAL_STOP and banner:
                return ResultadoDiagnostico(
                    respuesta_texto=limpiar_advertencia(banner),
                    diagnostico_ml="Advertencia de seguridad física",
                    confianza_ml=0.0,
                    contexto_manual="",
                    titulo_manual="",
                    requiere_revision_humana=True,
                    modo_diagnostico="seguridad_critica",
                    tipo_consulta="seguridad_critica",
                )
        dto = func(gestor, *args, **kwargs)
        if not isinstance(dto, ResultadoDiagnostico):
            return dto
        respuesta, _, changed = proteger_salida_conversacional(
            dto.respuesta_texto,
            kwargs.get("marca_modelo") or "",
            texto,
            corpus_validado=False,
            mediciones_reportadas=getattr(estado, "historial_mensajes_usuario", []) if estado else [],
        )
        if changed:
            cambios = {"respuesta_texto": respuesta}
            if es_solicitud_especificacion(texto):
                cambios.update(confianza_ml=0.0, requiere_revision_humana=True)
            dto = dto.model_copy(update=cambios)
        return dto

    return control
