"""Etapa evidencia; contexto por turno."""

from __future__ import annotations

import re
import time
from importlib import import_module as _importar

from src.core.conversacion.control_aclaraciones import (
    dato_desconocido,
    debe_avanzar,
    desconocidos_consecutivos,
    hay_evidencia_diagnostica,
)
from src.core.conversacion.extractor_hechos import ExtractorHechos
from src.core.conversacion.generador_preguntas import GeneradorPreguntas
from src.core.conversacion.models import FactState, FactType
from src.core.conversacion.suficiencia_informacion import EvaluadorSuficiencia


async def evidencia(self, turno):
    turno.es_solicitud_detalle = ExtractorHechos.es_solicitud_detalle(turno.texto_limpio)
    turno.clasificar_intencion_consulta = _importar(
        "src.core.intent_classifier"
    ).clasificar_intencion_consulta
    turno.es_consulta_tecnica = turno.clasificar_intencion_consulta(turno.texto_limpio) == "consulta_tecnica"
    turno.solicita_alternativas = bool(
        turno.interp_semantica
        and turno.interp_semantica.solicita_causas_alternativas
        or re.search(
            r"\b(?:otra[s]?\s+causa[s]?|posibles?\s+causa[s]?|hip[oó]tesis\s+alternativa[s]?|qu[eé]\s+(?:otras?|m[aá]s)\s+puede\s+ser|qu[eé]\s+otra\s+cosa|diferenciar(?:las)?|distinguir(?:las)?)\b",
            turno.texto_limpio,
            re.IGNORECASE,
        )
    )
    turno.tiene_evidencia_mixta = bool(
        turno.hechos_extraidos
        and any(
            (
                isinstance(h, dict)
                and h.get("categoria")
                in ("sintoma", "medicion", "condicion", "comprobacion", "componente_reemplazado")
                for h in turno.hechos_extraidos
            )
        )
    )
    turno.tiene_caso_activo = bool(
        turno.estado.top3_actual
        or getattr(turno.estado, "falla_principal", None)
        or turno.estado.active_symptoms
    )
    turno.es_consulta_tecnica_pura = (
        turno.es_consulta_tecnica
        and (not turno.solicita_alternativas)
        and (not turno.tiene_evidencia_mixta)
        and (not turno.tiene_caso_activo)
    )
    if turno.es_solicitud_detalle or turno.es_consulta_tecnica_pura:
        turno.dto_tecnico = turno.gestor_diagnostico._procesar_consulta_tecnica(
            pregunta=turno.texto_limpio,
            inicio_total=turno.t0,
            remitente=turno.remitente,
            proveedor=turno.proveedor,
            taller_id=turno.taller_id,
            usuario_id=turno.usuario_id,
            conversacion_id=turno.conversacion_id or turno.session_id,
            slot_gemini_preconcedido=None,
            diferir_encolado_persistente=turno.diferir_encolado_persistente,
        )
        turno.resp_texto = getattr(turno.dto_tecnico, "respuesta_texto", "")
        if (turno.es_solicitud_detalle or turno.es_consulta_tecnica_pura) and (
            not turno.resp_texto
            or "No encontré una fuente documental" in turno.resp_texto
            or "no dispongo de información" in turno.resp_texto.lower()
            or "aviso de control metrológico" in turno.resp_texto.lower()
            or "sin respaldo documental" in turno.resp_texto.lower()
        ):
            from src.core.conversacion.formato_salidas.orientacion_segura import orientar_sin_manual

            turno.resp_texto = orientar_sin_manual(turno.texto_limpio)
        turno.resp_texto = turno.PoliticaSeguridad.enriquecer_respuesta_seguridad(
            turno.resp_texto or "Información técnica.",
            turno.texto_limpio,
            diagnostico_ml=getattr(turno.dto_tecnico, "diagnostico_ml", "Consulta técnica"),
            estado=turno.estado,
        )
        await self.repositorio.save_session(turno.session_id, turno.estado)
        return {
            "status": "consulta_tecnica" if not turno.es_solicitud_detalle else "solicitud_detalle",
            "respuesta_texto": turno.resp_texto,
            "diagnostico_ml": getattr(turno.dto_tecnico, "diagnostico_ml", "Consulta técnica"),
            "confianza_ml": getattr(turno.dto_tecnico, "confianza_ml", 1.0),
            "fase": turno.estado.fase.value,
            "es_pregunta": False,
            "decision": "DETALLE",
            "tiempo_ms": round((time.perf_counter() - turno.t0) * 1000, 2),
            "estado": turno.estado,
            "dto": turno.dto_tecnico,
        }
    if turno.estado.preguntas_realizadas:
        turno.interp_str = (
            turno.interpretacion_corta.get("valor") if turno.interpretacion_corta else None
        ) or "respuesta_usuario"
        turno.estado.registrar_respuesta(turno.texto_limpio, turno.interp_str)
    if turno.placa and turno.placa not in ("REST-API", "WAPP-01", "DESCONOCIDO"):
        turno.estado.placa = turno.placa
    if turno.marca_modelo and turno.marca_modelo not in (
        "Vehiculo Generico",
        "Generico Generico",
        "Generico",
        "",
    ):
        turno.partes_mm = turno.marca_modelo.split()
        if len(turno.partes_mm) >= 1 and (not turno.estado.marca):
            turno.estado.marca = turno.partes_mm[0]
            turno.estado.registrar_hecho(
                "marca",
                turno.partes_mm[0],
                categoria="vehiculo",
                texto_crudo=turno.marca_modelo,
                tipo=FactType.CONDICION,
            )
        if len(turno.partes_mm) >= 2 and (not turno.estado.modelo):
            turno.estado.modelo = " ".join(turno.partes_mm[1:])
            turno.estado.registrar_hecho(
                "modelo",
                " ".join(turno.partes_mm[1:]),
                categoria="vehiculo",
                texto_crudo=turno.marca_modelo,
                tipo=FactType.CONDICION,
            )
    turno.score, turno.categorias_vistas, turno.es_suficiente, turno.motivo_suficiencia = (
        EvaluadorSuficiencia.evaluar(turno.estado)
    )
    if turno.interp_semantica and turno.interp_semantica.solicita_causas_alternativas:
        turno.es_suficiente = True
        turno.motivo_suficiencia = "Mecánico solicita hipótesis diferenciales y causas alternativas"
    turno.medicion_area_pendiente = GeneradorPreguntas.falta_medicion_discriminante_por_area(turno.estado)
    if (
        turno.medicion_area_pendiente
        and turno.estado.active_system == "combustible_admision"
        and turno.estado.ya_preguntado_texto("STFT/LTFT")
        and re.search(
            r"\b(?:al acelerar|cuando acelera|en caliente|en frío|en frio|en marcha|pierde fuerza|pierde potencia|se apaga|ratea|tiembla)\b",
            turno.texto_limpio,
            re.IGNORECASE,
        )
    ):
        turno.medicion_area_pendiente = False
        turno.es_suficiente = True
        turno.motivo_suficiencia = "Se solicitó DTC/STFT una vez y se recibió contexto operativo; continuar con diagnóstico orientativo sin confirmar una causa"
    if (
        turno.estado.obtener_hecho("revision_concreta_mezcla")
        and (not turno.estado.obtener_hecho("caudal_inyectores_reportado"))
        and (
            not any(
                (
                    hecho.categoria == "dtc"
                    or re.search(r"\b(?:STFT|LTFT)\b.*\d", f"{hecho.campo} {hecho.valor}", re.IGNORECASE)
                    for hecho in turno.estado.hechos.values()
                )
            )
        )
    ):
        turno.es_suficiente = False
        turno.motivo_suficiencia = (
            "Revisión concreta registrada: avanzar a otra comprobación del mismo sistema"
        )
    turno.texto_historial_normalizado = " ".join(turno.estado.historial_mensajes_usuario).lower()
    if turno.estado.active_system == "electrico_ecu" and re.search(
        r"(?:cambie|cambio|cambiar|cambiaron|reemplazaron|reemplazo).{0,45}(?:ecu|computadora)",
        turno.texto_historial_normalizado,
    ):
        turno.es_suficiente = False
        turno.motivo_suficiencia = (
            "Antecedente de reemplazo ECU y error de codificación requiere comprobación específica"
        )
    if "sensor_maf_lectura_anomala_reportada" in turno.estado.hechos:
        turno.es_suficiente = False
        turno.motivo_suficiencia = "Hallazgo MAF explícito requiere seguimiento específico del sensor"
    if (
        turno.estado.active_system == "ambiguo"
        and re.search(r"\b500\s*rpm\b", turno.texto_historial_normalizado)
        and (
            not re.search(
                r"\b(?:tiembla|vibra|misfire|ratea|cabecea)\b",
                " ".join(turno.estado.historial_mensajes_usuario).lower(),
            )
        )
    ):
        turno.es_suficiente = False
        turno.motivo_suficiencia = (
            "RPM baja sin síntomas discriminantes: solicitar contexto antes de clasificar"
        )
    if turno.medicion_area_pendiente:
        turno.es_suficiente = False
        turno.motivo_suficiencia = (
            "Falta la lectura técnica mínima para confirmar la ruta explícita de mezcla o MAP"
        )
    turno.forzar_avance = debe_avanzar(turno.estado, turno.texto_limpio)
    turno.sin_evidencia = not hay_evidencia_diagnostica(turno.estado)
    if turno.sin_evidencia and dato_desconocido(turno.texto_limpio):
        turno.forzar_avance = desconocidos_consecutivos(turno.estado) >= max(
            1, turno.estado.max_repreguntas - 1
        )
    if turno.forzar_avance and dato_desconocido(turno.texto_limpio):
        turno.estado.registrar_hecho(
            "dato_solicitado_desconocido",
            "DESCONOCIDO",
            categoria="flujo",
            estado=FactState.NO_REVISADO,
            texto_crudo=turno.texto_limpio,
            tipo=FactType.CONDICION,
        )
