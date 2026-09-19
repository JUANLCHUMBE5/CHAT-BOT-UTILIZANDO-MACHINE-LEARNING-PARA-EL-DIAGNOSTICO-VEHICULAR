"""Máquina de estados finitos para el ciclo de vida del diálogo diagnóstico vehicular."""

from __future__ import annotations

from typing import Tuple

from src.core.conversacion.models import ConversationPhase, ConversationState
from src.core.conversacion.suficiencia_informacion import EvaluadorSuficiencia


class MaquinaEstadosConversacion:
    """Controla las transiciones formales entre fases del diálogo conversacional."""

    @classmethod
    def transicionar(
        cls,
        estado: ConversationState,
        es_reinicio: bool = False,
        nueva_evidencia: bool = False,
    ) -> Tuple[ConversationPhase, str]:
        """
        Calcula la siguiente fase válida en la máquina de estados.
        Retorna:
          (nueva_fase, motivo_transicion)
        """
        fase_anterior = estado.fase

        # 1. Reinicio explícito de sesión
        if es_reinicio:
            estado.reiniciar()
            estado.fase = ConversationPhase.INICIO
            return ConversationPhase.INICIO, "Reinicio solicitado: sesión limpia creada"

        # 2. Transición desde INICIO
        if fase_anterior == ConversationPhase.INICIO:
            estado.fase = ConversationPhase.RECOLECTANDO
            return ConversationPhase.RECOLECTANDO, "Primer mensaje recibido: iniciando recolección de hechos"

        # 3. Transición desde RESULTADO con nueva evidencia
        if fase_anterior == ConversationPhase.RESULTADO:
            if nueva_evidencia:
                # Regresar a aclarando / diagnosticando
                score, _, suficiente, motivo = EvaluadorSuficiencia.evaluar(estado)
                if suficiente:
                    estado.fase = ConversationPhase.DIAGNOSTICANDO
                    return ConversationPhase.DIAGNOSTICANDO, f"Nueva evidencia aportada tras resultado: {motivo}"
                else:
                    estado.fase = ConversationPhase.ACLARANDO
                    return ConversationPhase.ACLARANDO, "Nueva evidencia parcial aportada: pasando a aclarar"
            return ConversationPhase.RESULTADO, "Estado de resultado mantenido"

        # 4. Transición desde RECOLECTANDO o ACLARANDO
        score, _, suficiente, motivo = EvaluadorSuficiencia.evaluar(estado)

        # Si se superó el límite de repreguntas, ir directo a RESULTADO
        if estado.turnos_repregunta >= estado.max_repreguntas:
            estado.fase = ConversationPhase.RESULTADO
            return ConversationPhase.RESULTADO, "Límite máximo de 3 repreguntas alcanzado: emitiendo conclusión diferencial"

        if suficiente:
            estado.fase = ConversationPhase.DIAGNOSTICANDO
            return ConversationPhase.DIAGNOSTICANDO, motivo

        estado.fase = ConversationPhase.ACLARANDO
        return ConversationPhase.ACLARANDO, motivo
