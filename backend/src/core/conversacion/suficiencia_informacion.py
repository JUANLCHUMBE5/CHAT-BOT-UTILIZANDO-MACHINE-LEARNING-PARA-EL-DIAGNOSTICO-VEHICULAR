"""Módulo de evaluación de suficiencia informativa (InformationSufficiencyScore) y nivel de evidencia."""

from __future__ import annotations

from typing import List, Tuple

from src.core.conversacion.models import ConversationState, EvidenceLevel, FactState

CATEGORIAS_INDEPENDIENTES = (
    "sintoma",
    "sistema",
    "condicion",
    "comportamiento",
    "cambio_accion",
    "temperatura",
    "dtc",
    "medicion",
    "componente_descartado",
    "antecedente",
    "modificador",
    "vehiculo",
    "inspeccion",
)


class EvaluadorSuficiencia:
    """Calcula el InformationSufficiencyScore y clasifica el conversation_evidence_level (Adenda 9.1)."""

    @classmethod
    def tiene_evidencia_fuerte(cls, estado: ConversationState) -> Tuple[bool, str]:
        """Detecta si existe evidencia técnica concluyente que exime de pedir más información."""
        hechos_confirmados = [
            h for h in estado.hechos.values() if h.estado == FactState.CONFIRMADO
        ]

        # 1. DTC específico confirmado
        tiene_dtc = any(h.categoria == "dtc" for h in hechos_confirmados)
        if tiene_dtc:
            codigos = [h.valor for h in hechos_confirmados if h.categoria == "dtc"]
            return True, f"Evidencia fuerte: DTC OBD-II confirmado ({', '.join(codigos)})"

        # 2. Medición técnica cuantitativa (compresión, presión de combustible, voltaje)
        tiene_medicion = any(h.categoria == "medicion" for h in hechos_confirmados)
        if tiene_medicion:
            meds = [h.valor for h in hechos_confirmados if h.categoria == "medicion"]
            return True, f"Evidencia fuerte: Medición técnica confirmada ({', '.join(meds)})"

        # 3. Componente ya probado o intercambiado con prueba de banco/taller
        tiene_descarte = any(
            h.categoria in ("componente_descartado", "antecedente", "inspeccion") for h in hechos_confirmados
        )
        tiene_sintoma = any(h.categoria == "sintoma" for h in hechos_confirmados)
        if tiene_descarte and tiene_sintoma:
            return True, "Evidencia fuerte: Síntoma clínico con componente descartado/probado en taller"

        # 4. Síntomas altamente discriminantes combinados
        valores_sintomas = " ".join([h.valor.lower() for h in hechos_confirmados])
        if "humo blanco" in valores_sintomas and "sobrecalentamiento" in valores_sintomas:
            return True, "Evidencia fuerte: Humo blanco con ebullición / sobrecalentamiento"
        if "sobrecalentamiento" in valores_sintomas and "fuga de refrigerante" in valores_sintomas:
            return True, "Evidencia fuerte: sobrecalentamiento con perdida de refrigerante reportada"
        tiene_chasquido = "chasquido" in valores_sintomas or any(h.campo == "sintoma_chasquido_de_arranque_clac" for h in hechos_confirmados)
        tiene_luces_bat = any(c in valores_sintomas for c in ("bateria", "luces")) or any(h.campo in ("luces_se_atenuan", "modificador_luces") for h in hechos_confirmados)
        if tiene_chasquido and tiene_luces_bat:
            return True, "Evidencia fuerte: Chasquido de solenoide con batería/luces encendidas o atenuadas"

        mensajes_completos = " ".join(estado.historial_mensajes_usuario).lower()
        if any(w in valores_sintomas or w in mensajes_completos for w in ("esponjoso", "se va al fondo", "se hunde")) and any(
            w in valores_sintomas or w in mensajes_completos for w in ("freno", "frenar", "frenado", "pedal")
        ):
            return True, "Evidencia fuerte: Anomalía hidráulica en pedal de freno (esponjoso / se hunde)"

        tiene_cascabeleo = any(
            w in valores_sintomas or w in mensajes_completos
            for w in ("cascabelea", "cascabeleo", "pistonea", "pistoneo", "detonacion", "detonación")
        )
        tiene_potencia = any(
            w in valores_sintomas or w in mensajes_completos
            for w in ("pierde potencia", "falta de fuerza", "sin fuerza", "se chupa", "no jala", "pérdida de potencia", "perdida de potencia")
        )
        tiene_carga = any(
            w in valores_sintomas or w in mensajes_completos
            for w in ("subida", "pendiente", "subir pendientes", "bajo carga")
        )
        if tiene_cascabeleo and (tiene_potencia or tiene_carga):
            return True, "Evidencia fuerte: Cascabeleo / detonación en aceleración o pendientes"

        return False, ""

    @classmethod
    def evaluar(cls, estado: ConversationState) -> Tuple[int, List[str], bool, str]:
        """
        Calcula el InformationSufficiencyScore y actualiza conversation_evidence_level.
        Retorna:
          (score, categorias_detectadas, es_suficiente, motivo)
        """
        # Comprobar primero salida anticipada por evidencia fuerte
        es_fuerte, motivo_fuerte = cls.tiene_evidencia_fuerte(estado)
        if es_fuerte:
            estado.conversation_evidence_level = EvidenceLevel.ALTA
            return 3, ["evidencia_fuerte"], True, motivo_fuerte

        # Identificar categorías confirmadas independientes
        categorias_vistas = set()
        for h in estado.hechos.values():
            if h.estado == FactState.CONFIRMADO:
                cat = h.categoria
                if cat in CATEGORIAS_INDEPENDIENTES:
                    categorias_vistas.add(cat)

        lista_cat = sorted(list(categorias_vistas))
        score = len(lista_cat)

        if score >= 3:
            estado.conversation_evidence_level = EvidenceLevel.MEDIA
            return (
                score,
                lista_cat,
                True,
                f"Información suficiente: {score} categorías diagnósticas independientes ({', '.join(lista_cat)})",
            )

        estado.conversation_evidence_level = EvidenceLevel.BAJA
        return (
            score,
            lista_cat,
            False,
            f"Información insuficiente: solo {score}/3 categorías ({', '.join(lista_cat) or 'ninguna'}). Se requiere aclarar.",
        )
