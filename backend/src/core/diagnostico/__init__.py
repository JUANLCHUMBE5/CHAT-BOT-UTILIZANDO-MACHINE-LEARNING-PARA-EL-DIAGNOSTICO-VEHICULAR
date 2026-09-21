"""Módulo core/diagnostico: orquestación, lógica de negocio y DTOs del diagnóstico automotriz."""

from src.core.diagnostico.ambiguity_checker import (
    es_consulta_ambigua,
    es_continuacion_contextual,
    es_respuesta_cordial,
    es_respuesta_opcion_o_combustible,
    es_saludo_o_contacto_inicial,
)
from src.core.diagnostico.constants import (
    PALABRAS_MECANICAS,
    VERBOS_FALLA,
    VOCABULARIO_COMPONENTES,
)
from src.core.diagnostico.degraded_fallback import generar_respuesta_degradada
from src.core.diagnostico.diagnostico_tracker import registrar_en_tracker
from src.core.diagnostico.fuel_context import (
    es_perdida_potencia_bajo_carga,
    extraer_contexto_combustible,
    resultado_solicitud_combustible,
    texto_modo_combustible,
)
from src.core.diagnostico.models import PrediccionML, ResultadoDiagnostico
from src.core.diagnostico.prompt_builder import (
    construir_prompt_consulta_tecnica,
    construir_prompt_diagnostico,
)
from src.core.diagnostico.semantic_purifier import purificar_sintoma_para_vectorizador_ml
from src.core.diagnostico.vehicle_context import (
    campos_requeridos_consulta_tecnica,
    formatear_perfil_vehiculo,
    resultado_solicitud_datos_vehiculo,
)

__all__ = [
    "PrediccionML",
    "ResultadoDiagnostico",
    "VOCABULARIO_COMPONENTES",
    "VERBOS_FALLA",
    "PALABRAS_MECANICAS",
    "purificar_sintoma_para_vectorizador_ml",
    "es_saludo_o_contacto_inicial",
    "es_respuesta_cordial",
    "es_continuacion_contextual",
    "es_consulta_ambigua",
    "es_respuesta_opcion_o_combustible",
    "es_perdida_potencia_bajo_carga",
    "extraer_contexto_combustible",
    "texto_modo_combustible",
    "resultado_solicitud_combustible",
    "formatear_perfil_vehiculo",
    "resultado_solicitud_datos_vehiculo",
    "campos_requeridos_consulta_tecnica",
    "registrar_en_tracker",
    "construir_prompt_diagnostico",
    "construir_prompt_consulta_tecnica",
    "generar_respuesta_degradada",
]
