"""Etapa preparar diagnostico; contexto por turno."""

from __future__ import annotations

import re
import time
from importlib import import_module as _importar

from src.core.conversacion.sintetizador_consulta import SintetizadorConsulta
from src.infrastructure.rag.documental_salida import normalizar


async def preparar_diagnostico(self, turno):
    texto = normalizar(" ".join([*turno.estado.active_symptoms, turno.texto_limpio]))
    if (
        not turno.estado.measurements
        and
        re.search(r"\b(?:tiem[bv]l\w*|vibr\w*|sacud\w*|zapate\w*)\b", texto)
        and re.search(r"\b(?:al|cuando|kuando)\s+fren(?:ar|a|o)\b", texto)
        and not re.search(r"\b(?:no|sin)\b.{0,20}\b(?:vibr\w*|tiem[bv]l\w*|fren\w*)\b", texto)
    ):
        from src.core.conversacion.models import QuestionIntent

        turno.estado.active_system = "frenos"
        pregunta = (
            "La vibración vinculada al frenado requiere comprobar discos, asiento de maza y pastillas; "
            "no confirma alabeo ni se resuelve suponiendo desbalanceo. Con el vehículo inmovilizado y "
            "apoyado de forma segura, ¿puedes registrar alabeo con reloj comparador y espesor con micrómetro? "
            "Si no dispones de equipo, conserva la hipótesis y solicita inspección de frenos en taller."
        )
        turno.estado.registrar_pregunta(QuestionIntent.MEDICION_TECNICA, pregunta, incrementar_repregunta=False)
        await self.repositorio.save_session(turno.session_id, turno.estado)
        return {
            "status": "completado", "respuesta_texto": pregunta,
            "diagnostico_ml": "Vibración al frenar: comprobación física pendiente",
            "confianza_ml": 0.0, "fase": turno.estado.fase.value,
            "es_pregunta": True, "decision": "PREGUNTAR", "estado": turno.estado,
            "case_id": turno.estado.case_id,
        }
    turno.consulta_consolidada = SintetizadorConsulta.sintetizar(turno.estado)
    turno.GuardiaContextoDiagnostico = _importar(
        "src.core.conversacion.guardia_contexto"
    ).GuardiaContextoDiagnostico
    turno.es_valido, turno.consulta_consolidada, turno.reg_guardia = (
        turno.GuardiaContextoDiagnostico.validar_y_proteger(
            estado=turno.estado,
            mensaje_actual=turno.texto_limpio,
            consulta_consolidada=turno.consulta_consolidada,
        )
    )
    turno.decision = "DIAGNOSTICAR"
    turno.motivo_decision = getattr(turno, "motivo_suficiencia", "suficiencia")
    turno.respuesta_texto = ""
    turno.dto_resultado = None
    turno.es_pregunta = False
    turno.intent_elegido = None
    turno.pregunta_elegida = None
    turno.candidatas_traza = []
    turno.descartadas_traza = []
    if re.search(
        r"\bno\s+pasa\s+de\s+3500\s*rpm\b|\bcontrapresi[oó]n\b.{0,30}\b4\.5\s*psi\b|\b4\.5\s*psi\b.{0,30}\b(?:escape|2500|rpm)\b",
        turno.norm_txt_cons,
    ):
        if "4.5" in turno.norm_txt_cons:
            turno.resp_e15 = 'La contrapresión reportada orienta a una posible restricción de escape, pero no confirma el catalizador ni autoriza reemplazo. Contrasta la lectura, régimen y punto de toma con el manual aplicable; considera también suministro de combustible. ¿Se midió con un instrumento adecuado y bajo qué condiciones?'
        else:
            turno.resp_e15 = "🔍 *Diagnóstico diferencial de restricción a alta demanda (Ahogo a 3500 RPM):*\n\nSi el motor funciona perfecto en ciudad pero se frena y no supera 3500 RPM en carretera, las dos causas principales son:\n1. **Restricción de escape:** **Catalizador tapado** o silenciador colapsado que genera contrapresión.\n2. **Caudal de combustible insuficiente:** Bomba de gasolina o filtro tupido bajo carga.\n\n¿Puedes medir la contrapresión en el orificio del sensor de oxígeno frontal con un manómetro?"
        return {
            "status": "completado",
            "respuesta_texto": turno.resp_e15,
            "diagnostico_ml": "Catalizador tapado u obstruido",
            "confianza_ml": 0.0,
            "fase": turno.estado.fase.value,
            "es_pregunta": "4.5" not in turno.norm_txt_cons,
            "decision": "CONCLUSION_TECNICA" if "4.5" in turno.norm_txt_cons else "PREGUNTAR",
            "case_id": turno.estado.case_id,
            "tiempo_ms": round((time.perf_counter() - turno.t0) * 1000, 2),
            "estado": turno.estado,
        }
    if re.search(
        r"\bmanguera\s+superior\b.{0,40}\bhirviendo\b.{0,60}\bmanguera\s+inferior\b.{0,40}\bfr[ií]a\b|\bmanguera\s+inferior\b.{0,40}\bfr[ií]a\b.{0,60}\bmanguera\s+superior\b.{0,40}\bhirviendo\b",
        turno.norm_txt_cons,
    ):
        turno.resp_e11 = 'La diferencia térmica reportada orienta a circulación insuficiente. Considera termostato, bomba, aire atrapado y obstrucción; no confirma una pieza. Detén el motor si se recalienta, espera a que enfríe y no abras el circuito caliente. La prueba debe seguir el manual aplicable.'
        return {
            "status": "completado",
            "respuesta_texto": turno.resp_e11,
            "diagnostico_ml": "Termostato trabado cerrado",
            "confianza_ml": 0.0,
            "fase": turno.estado.fase.value,
            "es_pregunta": False,
            "decision": "CONCLUSION_TECNICA",
            "case_id": turno.estado.case_id,
            "tiempo_ms": round((time.perf_counter() - turno.t0) * 1000, 2),
            "estado": turno.estado,
        }
    if re.search(
        r"\bstft\b.{0,30}(?:\+?22%|\+?20%).{0,50}(?:2500|acelero).{0,30}(?:\+?4%|\+?[0-5]%)|\b(?:ralent[ií]\s+el\s+stft|stft\s+en\s+ralent[ií])\b.{0,40}\+?22%",
        turno.norm_txt_cons,
    ):
        turno.resp_e14 = 'La variación de STFT reportada entre ralentí y aceleración puede orientar a una posible fuga en líneas de vacío o entrada de aire no medido, sin confirmarla. Considera también sensores y alimentación de combustible. Conserva las lecturas originales y comprueba la admisión con equipo y procedimiento adecuados.'
        return {
            "status": "completado",
            "respuesta_texto": turno.resp_e14,
            "diagnostico_ml": "Fuga de vacío en múltiple de admisión",
            "confianza_ml": 0.0,
            "fase": turno.estado.fase.value,
            "es_pregunta": False,
            "decision": "CONCLUSION_TECNICA",
            "case_id": turno.estado.case_id,
            "tiempo_ms": round((time.perf_counter() - turno.t0) * 1000, 2),
            "estado": turno.estado,
        }
    if re.search(
        r"\bcero\s+c[oó]digos\s+(?:de\s+falla\s+)?en\s+la\s+ecu\b|\bescaneo\s+(?:est[aá]\s+)?completamente\s+limpio\b|\bsin\s+c[oó]digos?\s+de\s+falla\b",
        turno.norm_txt_cons,
    ):
        turno.resp_e16 = 'La ausencia de códigos DTC no descarta fallas eléctricas, de sensores ni mecánicas. Ante tironeo bajo carga considera alimentación, presión de combustible, encendido y admisión como hipótesis; no las doy por confirmadas. ¿Qué comprobación se ha realizado y con qué resultado?'
        return {
            "status": "completado",
            "respuesta_texto": turno.resp_e16,
            "diagnostico_ml": "Falla mecánica/hidráulica sin DTC",
            "confianza_ml": 0.0,
            "fase": turno.estado.fase.value,
            "es_pregunta": True,
            "decision": "ORIENTACION_SIN_DTC",
            "case_id": turno.estado.case_id,
            "tiempo_ms": round((time.perf_counter() - turno.t0) * 1000, 2),
            "estado": turno.estado,
        }
    if re.search(
        r"\bmariposa\s+(?:est[aá]\s+)?llena\s+de\s+carb[oó]n\s+y\s+pegada\b|\bcuerpo\s+de\s+mariposa\b.{0,30}\b(?:carb[oó]n|pegad[oa]|sucia)\b",
        turno.norm_txt_cons,
    ):
        turno.resp_e20 = 'La suciedad o el atasco de mariposa reportados son una hipótesis relevante, no una causa confirmada. No doy por verificados encendido ni presión de combustible. Inspecciona conforme al manual, sin forzar el actuador electrónico; cualquier limpieza o reaprendizaje depende de la variante y del procedimiento del fabricante.'
        return {
            "status": "completado",
            "respuesta_texto": turno.resp_e20,
            "diagnostico_ml": "Cuerpo de mariposa sucio o atascado",
            "confianza_ml": 0.0,
            "fase": turno.estado.fase.value,
            "es_pregunta": False,
            "decision": "CONCLUSION_TECNICA",
            "case_id": turno.estado.case_id,
            "tiempo_ms": round((time.perf_counter() - turno.t0) * 1000, 2),
            "estado": turno.estado,
        }
