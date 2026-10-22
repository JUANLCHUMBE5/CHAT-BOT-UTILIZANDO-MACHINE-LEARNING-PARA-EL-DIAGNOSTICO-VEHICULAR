"""Manejo de estados interactivos de sesión, autopreguntas, combustible y cortesía."""

from __future__ import annotations

import re
import time
from typing import Any, Optional, Tuple

from src.core.diagnostico.models import ResultadoDiagnostico
from src.core.intent_classifier import clasificar_intencion_consulta
from src.core.vehicle_profile import (
    es_mensaje_solo_datos_vehiculo,
    extraer_datos_vehiculo,
    extraer_datos_vehiculo_contextual,
)


def manejar_interaccion_previa(
    gestor: Any,
    texto_normalizado: str,
    clave_sesion: Optional[str],
    sesion_pendiente: Any,
    marca_modelo: Optional[str],
    inicio_total: float,
    remitente: Optional[str],
    proveedor: str,
    taller_id: Optional[str],
    usuario_id: Optional[str],
    conversacion_id: Optional[str],
    slot_gemini_preconcedido: Optional[bool],
    diferir_encolado_persistente: bool,
) -> Tuple[Optional[ResultadoDiagnostico], str, Optional[str]]:
    """Procesa mensajes que interactúan con estados conversacionales previos de la sesión.

    Retorna: (resultado_inmediato, texto_actualizado, diagnostico_forzado)
    """
    diagnostico_forzado = None

    # El reinicio explícito precede a combustible y autopreguntas pendientes.
    from src.core.conversacion.extractor_hechos import ExtractorHechos

    solicitud = ExtractorHechos.clasificar_solicitud_caso(texto_normalizado)
    if solicitud and solicitud.get("accion") in {"nuevo_caso", "cancelar"}:
        if clave_sesion:
            gestor.session_manager.reiniciar_sesion(clave_sesion)
        if re.fullmatch(
            r"\s*(?:nuevo\s+(?:caso|diagn[oó]stico)|otro\s+(?:caso|problema|veh[ií]culo|carro|auto)|"
            r"reiniciar|cancelar(?:\s+(?:el\s+)?caso)?)\s*[.!]*\s*",
            texto_normalizado, re.I,
        ):
            return ResultadoDiagnostico(
                respuesta_texto="Caso anterior cerrado. Indica el vehículo y el síntoma del nuevo caso.",
                diagnostico_ml="Reinicio de sesión", confianza_ml=0.0,
                contexto_manual="", titulo_manual="", tipo_consulta="conversacional",
                modo_diagnostico="reinicio", estado_sesion="reinicio",
            ), texto_normalizado, diagnostico_forzado
        # Un comando y un síntoma en el mismo mensaje deben procesarse juntos.
        sesion_pendiente = None

    # 1. Mensaje con solo datos de vehículo
    if (
        es_mensaje_solo_datos_vehiculo(texto_normalizado)
        and not (sesion_pendiente and sesion_pendiente.estado == "esperando_datos_vehiculo")
    ):
        datos_vehiculo = extraer_datos_vehiculo(texto_normalizado)
        if marca_modelo and marca_modelo not in ("Vehiculo Generico", "Generico", ""):
            datos_vehiculo.update(extraer_datos_vehiculo(marca_modelo))
        sesion_vehiculo = sesion_pendiente
        if clave_sesion:
            sesion_vehiculo = sesion_vehiculo or gestor.session_manager.obtener_o_crear_sesion(clave_sesion)
            sesion_vehiculo.actualizar_perfil(datos_vehiculo)
            perfil_texto = gestor._formatear_perfil_vehiculo(sesion_vehiculo.perfil_vehiculo)
            marca_modelo = sesion_vehiculo.marca_modelo or marca_modelo
        else:
            perfil_texto = gestor._formatear_perfil_vehiculo(datos_vehiculo)

        sintoma_existente = sesion_vehiculo.obtener_sintoma_completo() if sesion_vehiculo else ""
        if sesion_vehiculo and sesion_vehiculo.estado in (
            "esperando_autopregunta",
            "esperando_aclaracion_sintoma",
            "esperando_combustible",
        ):
            respuesta_vehiculo = (
                f"Anoté {perfil_texto or 'los datos del vehículo'} como contexto. "
                "Conservo la pregunta técnica pendiente; responde esa indicación para continuar."
            )
            return ResultadoDiagnostico(
                respuesta_texto=respuesta_vehiculo,
                diagnostico_ml="Dato de vehículo registrado; se conserva el paso pendiente",
                confianza_ml=0.0,
                contexto_manual="",
                titulo_manual="",
                modo_diagnostico="esperando_contexto",
                estado_sesion=sesion_vehiculo.estado,
                tipo_consulta="aclaracion",
                sintoma_evaluado=sintoma_existente,
            ), texto_normalizado, diagnostico_forzado

        if not sintoma_existente:
            return ResultadoDiagnostico(
                respuesta_texto=(
                    f"Anoté {perfil_texto or 'los datos del vehículo'}. "
                    "Ahora cuéntame qué síntoma o falla presenta para iniciar el diagnóstico."
                ),
                diagnostico_ml="Datos de vehículo; falta describir la falla",
                confianza_ml=0.0,
                contexto_manual="",
                titulo_manual="",
                modo_diagnostico="esperando_sintoma",
                estado_sesion="esperando_sintoma",
                tipo_consulta="aclaracion",
            ), texto_normalizado, diagnostico_forzado

        texto_con_vehiculo = f"{sintoma_existente}\nDATOS CONFIRMADOS DEL VEHÍCULO: {perfil_texto}".strip()
        sesion_vehiculo.sintomas = [texto_con_vehiculo]
        sesion_vehiculo.estado = "en_proceso"
        texto_normalizado = texto_con_vehiculo

    # 2. Respuestas a autopregunta o aclaración técnica previa
    if sesion_pendiente and sesion_pendiente.estado in ("esperando_autopregunta", "esperando_aclaracion_sintoma"):
        from src.core.diagnostico.auto_interrogador import (
            es_rechazo_de_opciones,
            generar_pregunta_descarte_secundario,
            resolver_respuesta_autopregunta,
        )

        idx_opt, txt_opt, diag_canonica = resolver_respuesta_autopregunta(
            texto_normalizado,
            sesion_pendiente.autopregunta_opciones,
            sesion_pendiente.autopregunta_hipotesis,
        )
        if idx_opt is not None:
            sintoma_base = sesion_pendiente.autopregunta_sintoma_base or sesion_pendiente.obtener_sintoma_completo()
            texto_evaluar = f"{sintoma_base}. Confirmación técnica: {txt_opt}".strip()
            texto_normalizado = texto_evaluar
            sesion_pendiente.sintomas = [texto_evaluar]
            sesion_pendiente.estado = "en_proceso"
            otras_hipotesis = [
                h for i, h in enumerate(sesion_pendiente.autopregunta_hipotesis) if i != idx_opt
            ]
            sesion_pendiente.ultimas_hipotesis_diferenciales = otras_hipotesis
            sesion_pendiente.autopregunta_sintoma_base = None
            sesion_pendiente.autopregunta_opciones = []
            sesion_pendiente.autopregunta_hipotesis = []
            diagnostico_forzado = diag_canonica
        elif es_rechazo_de_opciones(texto_normalizado):
            sintoma_base = sesion_pendiente.autopregunta_sintoma_base or sesion_pendiente.obtener_sintoma_completo()
            hipotesis_descartadas = list(sesion_pendiente.autopregunta_hipotesis)
            sesion_pendiente.ultimas_hipotesis_diferenciales = hipotesis_descartadas
            sesion_pendiente.autopregunta_opciones = []
            sesion_pendiente.autopregunta_hipotesis = []
            sesion_pendiente.estado = "esperando_aclaracion_sintoma"

            mensaje_descarte = generar_pregunta_descarte_secundario(sintoma_base, hipotesis_descartadas)
            return ResultadoDiagnostico(
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
            ), texto_normalizado, diagnostico_forzado
        else:
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
                texto_normalizado = texto_evaluar
                sesion_pendiente.sintomas = [texto_evaluar]
                sesion_pendiente.estado = "en_proceso"
                sesion_pendiente.autopregunta_sintoma_base = None
                sesion_pendiente.autopregunta_opciones = []
                sesion_pendiente.autopregunta_hipotesis = []
            elif es_cambio:
                sesion_pendiente.reiniciar()

    # 3. Esperando combustible
    if sesion_pendiente and sesion_pendiente.estado == "esperando_combustible":
        combustible_anterior = sesion_pendiente.perfil_vehiculo.get("combustible")
        combustible, modo_falla = gestor._extraer_contexto_combustible(
            texto_normalizado, combustible_anterior
        )
        es_respuesta_combustible = bool(
            combustible
            or modo_falla
            or any(t in texto_normalizado.lower() for t in ("gnv", "glp", "gasolina", "gas", "ambos", "dos"))
        )
        es_cambio_de_tema = any(
            term in texto_normalizado.lower()
            for term in (
                "freno", "pedal", "pastilla", "zapata", "disco", "liquido", "timon", "timón",
                "cremallera", "rotula", "rótula", "amortiguador", "palier", "homocinetica",
                "homocinética", "rodaje", "rodamiento", "embrague", "clutch", "bateria",
                "otro problema", "otra falla", "nuevo problema", "tengo un susto", "mire maestro",
            )
        )
        if not es_respuesta_combustible or es_cambio_de_tema:
            sesion_pendiente.reiniciar()
        else:
            if combustible in {"GNV", "GLP"} or (combustible and not combustible_anterior):
                sesion_pendiente.actualizar_perfil({"combustible": combustible})
            sesion_pendiente.establecer_modo_falla_combustible(modo_falla)
            combustible_confirmado = sesion_pendiente.perfil_vehiculo.get("combustible")
            if not combustible_confirmado or not sesion_pendiente.modo_falla_combustible:
                return gestor._resultado_solicitud_combustible(
                    sesion_pendiente, combustible_confirmado
                ), texto_normalizado, diagnostico_forzado

            pregunta_original = sesion_pendiente.consulta_combustible_pendiente or ""
            contexto_combustible = gestor._texto_modo_combustible(
                combustible_confirmado, sesion_pendiente.modo_falla_combustible
            )
            texto_normalizado = f"{pregunta_original} {contexto_combustible}".strip()
            sesion_pendiente.reiniciar()
            sesion_pendiente.estado = "en_proceso"
            sesion_pendiente.actualizar_perfil({"combustible": combustible_confirmado})
            sesion_pendiente.establecer_modo_falla_combustible(modo_falla)
            sesion_pendiente.agregar_sintoma(texto_normalizado)

    # 4. Esperando datos de vehículo
    if sesion_pendiente and sesion_pendiente.estado == "esperando_datos_vehiculo":
        sesion_pendiente.campos_requeridos = []
        es_nueva_consulta = clasificar_intencion_consulta(texto_normalizado) == "consulta_tecnica"
        if es_nueva_consulta:
            sesion_pendiente.reiniciar()
        else:
            datos_recibidos = extraer_datos_vehiculo_contextual(
                texto_normalizado,
                sesion_pendiente.campos_faltantes(),
                sesion_pendiente.perfil_vehiculo,
            )
            if marca_modelo and marca_modelo not in ("Vehiculo Generico", "Generico", ""):
                datos_recibidos.update(extraer_datos_vehiculo(marca_modelo))
            sesion_pendiente.actualizar_perfil(datos_recibidos)
            if sesion_pendiente.kilometraje_por_aclarar:
                return gestor._resultado_solicitud_datos_vehiculo(sesion_pendiente), texto_normalizado, diagnostico_forzado

            pregunta_original = sesion_pendiente.consulta_tecnica_pendiente or texto_normalizado
            perfil_texto = gestor._formatear_perfil_vehiculo(sesion_pendiente.perfil_vehiculo)
            pregunta_contextual = pregunta_original
            if perfil_texto:
                pregunta_contextual += f"\n\nDATOS CONFIRMADOS DEL VEHÍCULO:\n{perfil_texto}"
            sesion_pendiente.reiniciar()
            return gestor._procesar_consulta_tecnica(
                pregunta_contextual,
                inicio_total=inicio_total,
                remitente=remitente,
                proveedor=proveedor,
                taller_id=taller_id,
                usuario_id=usuario_id,
                conversacion_id=conversacion_id,
                slot_gemini_preconcedido=slot_gemini_preconcedido,
                diferir_encolado_persistente=diferir_encolado_persistente,
            ), texto_normalizado, diagnostico_forzado

    # 5. Saludos o cortesía
    es_saludo, mensaje_saludo = gestor._es_saludo_o_contacto_inicial(texto_normalizado)
    if es_saludo:
        if clave_sesion:
            gestor.session_manager.reiniciar_sesion(clave_sesion)
        return ResultadoDiagnostico(
            respuesta_texto=mensaje_saludo,
            diagnostico_ml="Consulta General / Saludo",
            confianza_ml=1.0,
            contexto_manual="",
            titulo_manual="",
            modo_diagnostico="saludo",
            tipo_consulta="conversacional",
        ), texto_normalizado, diagnostico_forzado

    if gestor._es_respuesta_cordial(texto_normalizado):
        if clave_sesion:
            gestor.session_manager.reiniciar_sesion(clave_sesion)
        return ResultadoDiagnostico(
            respuesta_texto="👍 Entendido.",
            diagnostico_ml="Confirmación conversacional",
            confianza_ml=0.0,
            contexto_manual="",
            titulo_manual="",
            modo_diagnostico="conversacional",
            sintoma_evaluado=texto_normalizado,
            tipo_consulta="conversacional",
        ), texto_normalizado, diagnostico_forzado

    return None, texto_normalizado, diagnostico_forzado
