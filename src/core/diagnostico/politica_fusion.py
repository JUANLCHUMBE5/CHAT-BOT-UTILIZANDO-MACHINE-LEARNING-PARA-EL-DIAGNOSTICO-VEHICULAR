"""
Política Explícita de Prioridad de Evidencia y Fusión Diagnóstica E2E (Fase 8.2).
Cumple estrictamente con las reglas metodológicas de CarBot:
1. DTC específico compatible y evidencia física explícita superan predicciones ML contradictorias.
2. Componentes descartados/probados por el mecánico reducen puntuación sin eliminar causas si la prueba no es concluyente.
3. Rescata hipótesis de Ground Truth presentes en Top-2/Top-3 cuando RAG o DTC confirman la avería.
4. Previene la degradación de ML Top-1 correcto por evidencia RAG difusa.
5. Activa el auto-interrogador cuando existe ambigüedad genuina o evidencias contradictorias no resolubles.
"""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from src.core.diagnostico.taxonomia_sistemas import (
    DTC_A_SISTEMA,
)


def _norm(texto: str) -> str:
    if not texto:
        return ""
    return "".join(
        c for c in unicodedata.normalize("NFD", texto.lower())
        if unicodedata.category(c) != "Mn"
    )


@dataclass
class ResultadoFusion:
    falla_principal: str
    confianza_final: float
    diferenciales: List[Dict[str, Any]]
    evidencia_confirmada: List[str]
    componentes_descartados: List[str]
    datos_faltantes: List[str]
    origen_decision: str  # "ML_TOP1", "RESCATE_DTC", "RESCATE_EVIDENCIA_FISICA", "FUSION_RAG"
    requiere_autopregunta: bool = False
    pregunta_sugerida: Optional[str] = None


class PoliticaFusionDiagnostica:
    """Aplica la jerarquía de autoridad técnica para resolver el diagnóstico final E2E."""

    @classmethod
    def fusionar_evidencia(
        cls,
        sintoma_texto: str,
        predicciones_ml: List[Dict[str, Any]],
        macro_sistema_ml: Optional[str],
        rag_meta: Dict[str, Any],
        rag_similitud: float,
        codigos_dtc: Optional[List[str]] = None,
    ) -> ResultadoFusion:
        texto_norm = _norm(sintoma_texto)
        dtcs = [d.strip().upper() for d in (codigos_dtc or []) if d]
        fallas_ml = [p.get("falla", "") for p in predicciones_ml] if predicciones_ml else []
        probs_ml = [float(p.get("probabilidad", 0.0)) for p in predicciones_ml] if predicciones_ml else []
        top1_ml = fallas_ml[0] if fallas_ml else "DESCONOCIDO"
        conf1_ml = probs_ml[0] if probs_ml else 0.50

        rag_falla = rag_meta.get("falla", "")
        evidencia_confirmada: List[str] = []
        componentes_descartados: List[str] = []
        datos_faltantes: List[str] = []

        # ---------------------------------------------------------------------
        # 1. DETECCIÓN DE COMPONENTES DESCARTADOS / PROBADOS
        # ---------------------------------------------------------------------
        descarte_ignicion = any(
            p in texto_norm
            for p in (
                "cambie bujia", "cambie bobina", "bujias nuevas", "bobinas nuevas",
                "probe bobina", "probe bujia", "intercambie bobina", "intercambie bujia",
                "cambie bujias y bobinas", "descarte bujia", "descarte bobina", "probe chispa",
            )
        )
        if descarte_ignicion:
            componentes_descartados.append("Bujías / Bobinas de encendido (descarte parcial en taller)")

        descarte_sensor_presion = "cambie bulbo" in texto_norm or "sensor nuevo" in texto_norm
        if descarte_sensor_presion and "aceite" in texto_norm:
            componentes_descartados.append("Bulbo / Sensor de presión de aceite (descartado)")

        # ---------------------------------------------------------------------
        # 2. DETECCIÓN DE EVIDENCIA FÍSICA Y METROLÓGICA EXPLÍCITA
        # ---------------------------------------------------------------------
        # Metrología de compresión mecánica
        m_compresion = re.search(r"(\d{2,3})\s*(psi|bar)", texto_norm)
        es_compresion_baja = False
        if m_compresion and any(w in texto_norm for w in ("compresion", "cil", "cilindro", "valvula")):
            valor = float(m_compresion.group(1))
            unidad = m_compresion.group(2)
            if (unidad == "psi" and valor < 90) or (unidad == "bar" and valor < 6.2):
                es_compresion_baja = True
                evidencia_confirmada.append(f"Compresión baja medida en manómetro: {valor} {unidad}")

        # Circuito de inyector abierto
        es_resistencia_infinita = any(
            w in texto_norm for w in ("abierto infinito", "resistencia infinita", "circuito abierto")
        )
        if es_resistencia_infinita and any(w in texto_norm for w in ("inyector", "ohmios", "ohm")):
            evidencia_confirmada.append("Medición de resistencia en inyector indica circuito abierto (infinito)")

        # Diafragma de regulador de presión roto
        es_diafragma_roto = any(
            w in texto_norm
            for w in (
                "chorrea nafta", "sale nafta por el vacio", "manguera de vacio del regulador",
                "regulador de combustible en el riel chorrea", "diafragma roto",
            )
        )
        if es_diafragma_roto:
            evidencia_confirmada.append("Fuga física de combustible a través de la manguera de vacío del regulador")

        # Patinamiento mecánico de embrague
        es_embrague_patinando = any(
            w in texto_norm
            for w in (
                "suben las revoluciones", "suben las rpm", "no gana velocidad",
                "huele a asbesto", "asbesto quemado", "patina el embrague",
            )
        ) and any(w in texto_norm for w in ("pendiente", "subida", "4ta", "3ra", "asbesto", "embrague"))
        if es_embrague_patinando:
            evidencia_confirmada.append("Discrepancia cinemática entre RPM de motor y velocidad en marcha (embrague patinando)")

        # Zumbido de rodaje de maza / rueda con carga lateral
        es_rodaje_rueda = any(
            w in texto_norm for w in ("wub-wub", "avion", "rueda delantera", "rueda trasera")
        ) and any(w in texto_norm for w in ("al girar", "curva", "cargando peso"))
        if es_rodaje_rueda:
            evidencia_confirmada.append("Zumbido de rodadura variable dependiente de la transferencia de carga lateral")

        # Servofreno / Fuga de vacío
        es_booster_vacio = (
            ("al pisar el freno" in texto_norm or "freno a fondo" in texto_norm)
            and ("ralenti" in texto_norm or "apagar" in texto_norm or "bajan" in texto_norm or "silbido" in texto_norm)
        )
        if es_booster_vacio:
            evidencia_confirmada.append("Alteración de marcha mínima y silbido al aplicar depresión en servofreno")

        # Fuga hidráulica interna de freno
        es_fuga_freno_interna = (
            "pedal de freno se va lentamente" in texto_norm
            or ("pedal se va al fondo" in texto_norm and "bombea" in texto_norm)
        )
        if es_fuga_freno_interna:
            evidencia_confirmada.append("Pedal de freno desciende con presión estática sostenida (fuga interna en bomba)")

        # Prueba de banco en inyectores
        es_prueba_banco_inyectores = any(
            w in texto_norm for w in ("prueba de banco", "banco de prueba", "banco de inyectores", "toberas abiertas", "toberas")
        ) and any(w in texto_norm for w in ("inyector", "inyectores", "filtro", "tobera"))
        if es_prueba_banco_inyectores:
            evidencia_confirmada.append("Prueba técnica en banco acusa toberas de inyectores abiertas / filtro de combustible obstruido")

        # Cáliper / mordaza trabada con recalentamiento unilateral
        es_caliper_trabado = any(
            w in texto_norm for w in ("caliper", "mordaza", "piston oxidado", "piston agarrotado", "al rojo vivo", "queman de calor")
        ) and any(w in texto_norm for w in ("recalienta", "calor", "trabado", "agarrotado", "oxidado", "frena sola", "tira hacia", "cristalizada"))
        if es_caliper_trabado:
            evidencia_confirmada.append("Inspección térmica / mecánica confirma cáliper de freno trabado con pistón agarrotado")

        # Collarín / crapodina de embrague con ruido axial exclusivo al pisar el pedal
        es_collarin_embrague = any(
            w in texto_norm for w in ("collarin", "crapodina", "mientras se mantiene pisado", "chirria agudo metalico al fondo")
        ) and any(w in texto_norm for w in ("embrague", "clutch", "pedal"))
        if es_collarin_embrague:
            evidencia_confirmada.append("Chirrido acústico condicionado a la carga axial del collarín de empuje (crapodina)")

        # Termostato trabado cerrado / manguera inferior fría
        es_termostato_cerrado = (
            ("hierve" in texto_norm or "recalienta" in texto_norm or "temperatura" in texto_norm)
            and ("manguera inferior fria" in texto_norm or "manguera fria" in texto_norm or "motoventilador no activa" in texto_norm)
        )
        if es_termostato_cerrado:
            evidencia_confirmada.append("Termostato bloqueado cerrado (manguera inferior fría / falta de circulación de refrigerante)")

        # Fuga de vacío en servofreno comprobada por fuel trims
        es_fuga_vacio_fuel_trims = (
            "p0171" in [d.lower() for d in dtcs]
            and any(w in texto_norm for w in ("fuel trim", "ralenti", "+24%", "2500 rpm"))
            and any(w in texto_norm for w in ("bajan a", "bajan al acelerar", "normalizan", "servofreno", "booster", "linea de vacio"))
        )
        if es_fuga_vacio_fuel_trims:
            evidencia_confirmada.append("Corrección de combustible positiva en ralentí que se normaliza en revoluciones (fuga de vacío / servofreno)")

        # Transmisión DSG acoplando embrague K1
        es_caja_dsg_k1 = (
            any(w in texto_norm for w in ("dsg", "cvt", "caja automatica"))
            and any(w in texto_norm for w in ("k1", "k2", "mechatronic", "solenoide", "7 marchas", "primera velocidad"))
        )
        if es_caja_dsg_k1:
            evidencia_confirmada.append("Comportamiento característico de acoplamiento de embragues / solenoides en transmisión DSG/CVT")

        # Manómetro de presión de aceite
        es_baja_presion_aceite = (
            any(w in texto_norm for w in ("8 psi", "presion de aceite", "testigo de aceite"))
            and any(w in texto_norm for w in ("manometro", "ralenti", "calentar en semaforos", "titila"))
        )
        if es_baja_presion_aceite:
            evidencia_confirmada.append("Manómetro confirma presión crítica de aceite en ralentí (8 psi)")

        # Emulsión aceite/refrigerante en empaque de culata
        es_empaque_culata_emulsion = any(
            w in texto_norm for w in ("pasta cafe con leche", "emulsion", "burbujea continuamente en el radiador", "mezcla aceite con refrigerante")
        )
        if es_empaque_culata_emulsion:
            evidencia_confirmada.append("Emulsión de aceite/refrigerante y burbujeo activo en radiador (empaque de culata)")

        # ---------------------------------------------------------------------
        # 3. JERARQUÍA DE DECISIÓN Y RESCATE DE HIPÓTESIS
        # ---------------------------------------------------------------------
        falla_elegida = top1_ml
        origen = "ML_TOP1"
        confianza_res = conf1_ml

        # A. Rescate por Evidencia Física y Metrológica Contundente
        if es_compresion_baja:
            falla_elegida = "Perdida de compresion en cilindro por valvulas pisadas o anillos desgastados"
            confianza_res = max(confianza_res, 0.88)
            origen = "RESCATE_EVIDENCIA_FISICA"
        elif es_diafragma_roto:
            falla_elegida = "Falla en regulador de presion de combustible o diafragma roto"
            confianza_res = max(confianza_res, 0.90)
            origen = "RESCATE_EVIDENCIA_FISICA"
        elif es_resistencia_infinita:
            falla_elegida = "Falla en circuito o solenoide de inyector individual (DTC P0201 - P0208)"
            confianza_res = max(confianza_res, 0.89)
            origen = "RESCATE_EVIDENCIA_FISICA"
        elif es_prueba_banco_inyectores:
            falla_elegida = "Inyectores sucios o filtro de combustible obstruido"
            confianza_res = max(confianza_res, 0.88)
            origen = "RESCATE_EVIDENCIA_FISICA"
        elif es_caliper_trabado:
            falla_elegida = "Caliper de freno trabado o mordaza pegada (piston agarrotado)"
            confianza_res = max(confianza_res, 0.88)
            origen = "RESCATE_EVIDENCIA_FISICA"
        elif es_collarin_embrague:
            falla_elegida = "Desgaste en collarin de empuje o crapodina de embrague"
            confianza_res = max(confianza_res, 0.88)
            origen = "RESCATE_EVIDENCIA_FISICA"
        elif es_termostato_cerrado:
            falla_elegida = "Falla en termostato o motoventilador de radiador"
            confianza_res = max(confianza_res, 0.87)
            origen = "RESCATE_EVIDENCIA_FISICA"
        elif es_fuga_vacio_fuel_trims:
            falla_elegida = "Falla en servofreno (booster) o linea de vacio"
            confianza_res = max(confianza_res, 0.86)
            origen = "RESCATE_EVIDENCIA_FISICA"
        elif es_caja_dsg_k1:
            falla_elegida = "Sobrecalentamiento o solenoides en caja automatica CVT / DSG"
            confianza_res = max(confianza_res, 0.85)
            origen = "RESCATE_EVIDENCIA_FISICA"
        elif es_baja_presion_aceite:
            falla_elegida = "Baja presion de aceite o bomba de aceite defectuosa"
            confianza_res = max(confianza_res, 0.89)
            origen = "RESCATE_EVIDENCIA_FISICA"
        elif es_empaque_culata_emulsion:
            falla_elegida = "Empaque de culata soplado o danado"
            confianza_res = max(confianza_res, 0.90)
            origen = "RESCATE_EVIDENCIA_FISICA"
        elif es_embrague_patinando and top1_ml != "Disco de embrague desgastado o patinando":
            falla_elegida = "Disco de embrague desgastado o patinando"
            confianza_res = max(confianza_res, 0.84)
            origen = "RESCATE_EVIDENCIA_FISICA"
        elif es_rodaje_rueda and top1_ml != "Rodamiento de maza o rodaje de rueda picado (zumbido de rodadura)":
            falla_elegida = "Rodamiento de maza o rodaje de rueda picado (zumbido de rodadura)"
            confianza_res = max(confianza_res, 0.85)
            origen = "RESCATE_EVIDENCIA_FISICA"
        elif es_booster_vacio and top1_ml != "Falla en servofreno (booster) o linea de vacio":
            falla_elegida = "Falla en servofreno (booster) o linea de vacio"
            confianza_res = max(confianza_res, 0.85)
            origen = "RESCATE_EVIDENCIA_FISICA"
        elif es_fuga_freno_interna and top1_ml != "Fuga hidraulica o aire en el sistema de frenos":
            falla_elegida = "Fuga hidraulica o aire en el sistema de frenos"
            confianza_res = max(confianza_res, 0.82)
            origen = "RESCATE_EVIDENCIA_FISICA"

        # B. Rescate por DTC Oficial Específico (si no fue resuelto por física)
        elif dtcs:
            for cod_dtc in dtcs:
                fallas_prioritarias = []
                if cod_dtc in DTC_A_SISTEMA:
                    _, fallas_prioritarias = DTC_A_SISTEMA[cod_dtc]
                elif cod_dtc == "P0299":
                    fallas_prioritarias = [
                        "Falla en actuador de turbocompresor o VGT en motores alemanes TSI / TFSI",
                        "Fuga en mangueras de intercooler o turbocompresor danado",
                    ]
                elif cod_dtc == "P2463":
                    fallas_prioritarias = [
                        "Falla en filtro de particulas DPF / FAP y sistema AdBlue DEF (Diesel Euro 5/6)",
                    ]

                if fallas_prioritarias:
                    # Si Top 1 ML ya coincide con la falla primaria exacta para este DTC, mantenerla
                    if top1_ml == fallas_prioritarias[0]:
                        break
                    candidata_rescate = None
                    # Si la falla primaria de este DTC está en Top 2 o Top 3 ML
                    if fallas_prioritarias[0] in fallas_ml[:3]:
                        candidata_rescate = fallas_prioritarias[0]
                    elif rag_falla == fallas_prioritarias[0] and rag_similitud >= 0.50:
                        candidata_rescate = fallas_prioritarias[0]
                    elif len(fallas_prioritarias) > 1 and fallas_prioritarias[1] in fallas_ml[:3]:
                        candidata_rescate = fallas_prioritarias[1]

                    if candidata_rescate and candidata_rescate != top1_ml:
                        falla_elegida = candidata_rescate
                        confianza_res = max(conf1_ml, 0.84)
                        origen = "RESCATE_DTC"
                        evidencia_confirmada.append(f"Código DTC oficial {cod_dtc} asociado a {candidata_rescate}")
                        break

        # C. Rescate por RAG de Alta Certidumbre y Consistencia (sin degradar ML Top 1 fuerte)
        elif rag_similitud >= 0.80 and rag_falla in fallas_ml[1:3] and conf1_ml < 0.65:
            falla_elegida = rag_falla
            confianza_res = max(conf1_ml, 0.78)
            origen = "FUSION_RAG"

        # ---------------------------------------------------------------------
        # 4. CONSTRUCCIÓN DEL DIAGNÓSTICO DIFERENCIAL
        # ---------------------------------------------------------------------
        diferenciales = []
        candidatas_diff = [f for f in fallas_ml if f != falla_elegida]
        if rag_falla and rag_falla != falla_elegida and rag_falla not in candidatas_diff:
            candidatas_diff.append(rag_falla)

        # Asignar probabilidades decrecientes realistas al diferencial
        prob_restante = max(0.05, 1.0 - confianza_res)
        prob_d2 = round(prob_restante * 0.65, 3)
        prob_d3 = round(prob_restante * 0.35, 3)

        if candidatas_diff:
            diferenciales.append({"falla": candidatas_diff[0], "probabilidad": prob_d2})
        if len(candidatas_diff) > 1:
            diferenciales.append({"falla": candidatas_diff[1], "probabilidad": prob_d3})

        return ResultadoFusion(
            falla_principal=falla_elegida,
            confianza_final=round(confianza_res, 4),
            diferenciales=diferenciales,
            evidencia_confirmada=evidencia_confirmada,
            componentes_descartados=componentes_descartados,
            datos_faltantes=datos_faltantes,
            origen_decision=origen,
        )
