"""Módulo para el manejo de mensajes con datos de vehículo y estados de espera de vehículo."""

from __future__ import annotations

from typing import Any, Optional, Tuple

from src.core.diagnostico.models import ResultadoDiagnostico
from src.core.intent_classifier import clasificar_intencion_consulta
from src.core.vehicle_profile import (
    extraer_datos_vehiculo,
    extraer_datos_vehiculo_contextual,
)


def manejar_mensaje_solo_datos_vehiculo(
    gestor: Any,
    texto_normalizado: str,
    sesion_pendiente: Optional[Any],
    clave_sesion: Optional[str],
    marca_modelo: Optional[str],
) -> Tuple[Optional[ResultadoDiagnostico], str, Optional[str], Optional[Any]]:
    """
    Procesa entradas que contienen exclusivamente información del vehículo.
    Retorna: (resultado_diagnostico, texto_normalizado, marca_modelo, sesion_actualizada)
    Si resultado_diagnostico no es None, la función llamadora debe retornar ese resultado.
    """
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
        return (
            ResultadoDiagnostico(
                respuesta_texto=respuesta_vehiculo,
                diagnostico_ml="Dato de vehículo registrado; se conserva el paso pendiente",
                confianza_ml=0.0,
                contexto_manual="",
                titulo_manual="",
                modo_diagnostico="esperando_contexto",
                estado_sesion=sesion_vehiculo.estado,
                tipo_consulta="aclaracion",
                sintoma_evaluado=sintoma_existente,
            ),
            texto_normalizado,
            marca_modelo,
            sesion_vehiculo,
        )

    if not sintoma_existente:
        return (
            ResultadoDiagnostico(
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
            ),
            texto_normalizado,
            marca_modelo,
            sesion_vehiculo,
        )

    texto_con_vehiculo = f"{sintoma_existente}\nDATOS CONFIRMADOS DEL VEHÍCULO: {perfil_texto}".strip()
    sesion_vehiculo.sintomas = [texto_con_vehiculo]
    sesion_vehiculo.estado = "en_proceso"
    return None, texto_con_vehiculo, marca_modelo, sesion_vehiculo


def manejar_esperando_datos_vehiculo(
    gestor: Any,
    sesion_pendiente: Any,
    texto_normalizado: str,
    marca_modelo: Optional[str],
    inicio_total: float,
    remitente: Optional[str],
    proveedor: str,
    taller_id: Optional[str],
    usuario_id: Optional[str],
    conversacion_id: Optional[str],
    slot_gemini_preconcedido: Optional[bool],
    diferir_encolado_persistente: bool,
) -> Optional[ResultadoDiagnostico]:
    """Procesa el estado 'esperando_datos_vehiculo' de la sesión."""
    sesion_pendiente.campos_requeridos = []
    es_nueva_consulta = clasificar_intencion_consulta(texto_normalizado) == "consulta_tecnica"
    if es_nueva_consulta:
        sesion_pendiente.reiniciar()
        return None

    datos_recibidos = extraer_datos_vehiculo_contextual(
        texto_normalizado,
        sesion_pendiente.campos_faltantes(),
        sesion_pendiente.perfil_vehiculo,
    )
    if marca_modelo and marca_modelo not in ("Vehiculo Generico", "Generico", ""):
        datos_recibidos.update(extraer_datos_vehiculo(marca_modelo))
    sesion_pendiente.actualizar_perfil(datos_recibidos)
    if sesion_pendiente.kilometraje_por_aclarar:
        return gestor._resultado_solicitud_datos_vehiculo(sesion_pendiente)

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
    )
