"""Módulo de protección y auditoría contra contexto obsoleto en el diagnóstico (Fase 9.5).

Garantiza que el clasificador de Machine Learning nunca reciba una consulta consolidada
compuesta únicamente por hechos antiguos cuando el mensaje actual aporta síntomas nuevos.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from src.core.conversacion.extractor_hechos import ExtractorHechos
from src.core.conversacion.models import ConversationState, FactType
from src.core.conversacion.sintetizador_consulta import SintetizadorConsulta
from src.core.logger import logger


@dataclass
class RegistroGuardiaContexto:
    """Auditoría obligatoria antes de invocar la inferencia diagnóstica."""
    case_id: str
    mensaje_actual: str
    hechos_activos: List[Dict[str, Any]]
    consulta_consolidada: str
    inconsistencia_detectada: bool = False
    motivo_inconsistencia: Optional[str] = None


class GuardiaContextoDiagnostico:
    """Valida la congruencia clínica entre el mensaje actual y los hechos antes de invocar ML."""

    @classmethod
    def validar_y_proteger(
        cls,
        estado: ConversationState,
        mensaje_actual: str,
        consulta_consolidada: str,
    ) -> Tuple[bool, str, RegistroGuardiaContexto]:
        """
        Verifica que la consulta consolidada contenga la evidencia del mensaje actual
        y no esté contaminada por hechos obsoletos de un caso anterior.

        Retorna:
            (es_valido, consulta_final_segura, registro_auditoria)
        """
        if not estado.case_id:
            import uuid
            estado.case_id = str(uuid.uuid4())

        hechos_activos = [h.to_dict() for h in estado.hechos.values()]
        registro = RegistroGuardiaContexto(
            case_id=str(estado.case_id),
            mensaje_actual=mensaje_actual,
            hechos_activos=hechos_activos,
            consulta_consolidada=consulta_consolidada,
        )

        # Extraer síntomas potenciales del mensaje actual de forma independiente
        temp_state = ConversationState(session_id="temp_validation")
        ExtractorHechos.extraer_y_actualizar(temp_state, mensaje_actual)
        sintomas_mensaje = [
            f.valor for f in temp_state.hechos.values()
            if f.categoria == "sintoma" or f.tipo == FactType.SINTOMA
        ]

        if not sintomas_mensaje:
            # El mensaje no aporta síntomas primarios nuevos; se conserva el contexto
            return True, consulta_consolidada, registro

        # Verificar si la consulta consolidada contiene alguno de los síntomas del mensaje actual
        consulta_norm = consulta_consolidada.lower()
        contiene_sintoma_nuevo = any(
            s.lower() in consulta_norm or any(w in consulta_norm for w in s.lower().split() if len(w) > 4)
            for s in sintomas_mensaje
        )

        # Si el mensaje actual aporta síntomas pero la consulta consolidada NO contiene ninguno
        # y solo tiene hechos antiguos de turnos previos:
        if not contiene_sintoma_nuevo and len(estado.hechos) > 0:
            registro.inconsistencia_detectada = True
            registro.motivo_inconsistencia = (
                f"Contaminación detectada: mensaje actual aporta {sintomas_mensaje} pero "
                f"la consulta consolidada ('{consulta_consolidada}') contiene únicamente hechos anteriores."
            )
            logger.warning(f"[GuardiaContexto] {registro.motivo_inconsistencia}")

            # RECONSTRUCCIÓN OBLIGATORIA DEL CONTEXTO
            estado.iniciar_nuevo_caso()
            ExtractorHechos.extraer_y_actualizar(estado, mensaje_actual)
            nueva_consulta = SintetizadorConsulta.sintetizar(estado)
            registro.consulta_consolidada = nueva_consulta
            registro.hechos_activos = [h.to_dict() for h in estado.hechos.values()]
            return False, nueva_consulta, registro

        return True, consulta_consolidada, registro
