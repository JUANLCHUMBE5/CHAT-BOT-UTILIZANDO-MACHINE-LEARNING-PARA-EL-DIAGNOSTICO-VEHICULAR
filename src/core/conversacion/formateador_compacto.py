"""Formateador de respuestas conversacionales compactas para WhatsApp (Fase 9.3).

Genera salidas directas, limpias y orientadas a la acción en taller:
- Máximo 3 hipótesis con confianza ML calibrada.
- Acción o prueba física prioritaria ("🛠️ Primero revisa").
- Pregunta contextual para continuar el diagnóstico.
- Soporte bajo demanda para "más detalles" / procedimiento técnico paso a paso.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional, Tuple

from src.core.conversacion.models import QuestionIntent
from src.core.taxonomy.catalogo_pruebas_taller import (
    obtener_directriz_taller,
)


def _simplificar_nombre_falla(falla: str) -> str:
    """Elimina identificadores internos o códigos crudos de la falla."""
    if not falla:
        return "Falla mecánica bajo revisión"
    texto = str(falla).strip()
    # Reemplazar guiones bajos o sintaxis de variable interna
    if "_" in texto and " " not in texto:
        texto = texto.replace("_", " ").title()
    # Limpiar prefijos de variables internas como 'sintoma_' o 'falla_'
    texto = re.sub(r"^(sintoma|falla|error)_+", "", texto, flags=re.IGNORECASE)
    return texto[0].upper() + texto[1:] if texto else "Revisión técnica general"


def _extraer_accion_prioritaria(falla: str, contexto_rag: str = "", estado: Optional[Any] = None) -> str:
    """Extrae una prueba física o acción concreta y breve (<140 caracteres)."""
    # 0. Consultar Plan B si hay herramientas bloqueadas (Fase 9.11)
    if estado:
        from src.core.conversacion.gestor_plan_b import GestorPlanB
        plan_b = GestorPlanB.obtener_plan_b_para_falla(falla, estado)
        if plan_b:
            return plan_b[0]

    directriz = obtener_directriz_taller(falla)
    falla_l = falla.lower().replace("í", "i").replace("á", "a").replace("é", "e").replace("ó", "o").replace("ú", "u")

    # 1. Reglas específicas de taller para máxima concisión en WhatsApp
    if "bateria" in falla_l or "borne" in falla_l:
        return "voltaje en reposo (referencial ≥12.6 V), caída en arranque (mínimo 9.6 V) y ajuste de bornes."
    if "alternador" in falla_l or ("carga" in falla_l and "descarga" not in falla_l):
        return "voltaje de carga en ralentí con motor encendido (debe situarse entre 13.8 V y 14.4 V)."
    if "arranque" in falla_l or "arrancador" in falla_l or "solenoide" in falla_l:
        return "caída de tensión en el terminal 50 del solenoide y verificar si el motor gira al dar contacto."
    if "bomba" in falla_l and "combustible" in falla_l:
        return "presión de combustible en el riel con manómetro y comparar con la especificación del fabricante."
    if "inyector" in falla_l or "filtro" in falla_l:
        return "presión en el riel de inyección y prueba de entrega/goteo en banco o probador."
    if "bujia" in falla_l or "bobina" in falla_l:
        return "salto de chispa en las bobinas y estado/calibración del electrodo de las bujías."
    if "desbalanceo" in falla_l or "llanta" in falla_l:
        return "balanceo dinámico de las ruedas en banco e inspección de deformación en neumáticos."
    if "alabeo" in falla_l or "disco" in falla_l:
        return "alabeo en los discos de freno con reloj comparador (máximo 0.05 mm admisible)."
    if "pastilla" in falla_l or "freno" in falla_l:
        return "espesor de las pastillas de freno (reemplazar si es menor a 3 mm) y estado de los discos."
    if "embrague" in falla_l or "clutch" in falla_l:
        return "prueba de patinamiento en 3ra marcha con freno de mano accionado e inspección de recorrido del pedal."
    if "termostato" in falla_l or "ventilador" in falla_l or "recalienta" in falla_l:
        return "temperatura en ambas mangueras del radiador y activación oportuna del electroventilador."

    # 2. Utilizar prueba de la directriz taxonómica
    if directriz and directriz.prueba_sugerida:
        oraciones = directriz.prueba_sugerida.split(". ")
        primera = oraciones[0].strip()
        if not primera.endswith("."):
            primera += "."
        # Si es concisa (< 160 caracteres), retornarla directamente
        if len(primera) <= 160:
            return primera[0].lower() + primera[1:]

    # 3. Extraer del contexto RAG si hay instrucciones
    if contexto_rag and "1." in contexto_rag:
        match = re.search(r"1\.\s*([^\n\r.]+)", contexto_rag)
        if match:
            candidata = match.group(1).strip()
            if len(candidata) <= 140:
                return candidata[0].lower() + candidata[1:] + "."

    return "inspección física directa del componente y sus conexiones principales en taller."


def _generar_pregunta_contextual(
    falla: str,
    texto_usuario: str = "",
    estado: Optional[Any] = None,
) -> Tuple[str, QuestionIntent]:
    falla_l = falla.lower().replace("í", "i").replace("á", "a").replace("é", "e").replace("ó", "o").replace("ú", "u")

    # 0. Consultar Plan B si hay herramientas bloqueadas (Fase 9.11)
    if estado:
        from src.core.conversacion.gestor_plan_b import GestorPlanB
        plan_b = GestorPlanB.obtener_plan_b_para_falla(falla, estado)
        if plan_b:
            return plan_b[1], plan_b[2]

    # Inspección de hechos en estado conversacional si existe
    multimetro_disp = None
    manometro_disp = None
    luces_atenuan = None
    if estado and getattr(estado, "hechos", None):
        h_m = estado.obtener_hecho("multimetro_disponible") or estado.obtener_hecho("herramienta_disponible")
        if h_m:
            multimetro_disp = getattr(h_m, "valor", "").upper()
        h_man = estado.obtener_hecho("manometro_disponible")
        if h_man:
            manometro_disp = getattr(h_man, "valor", "").upper()
        h_luces = estado.obtener_hecho("luces_se_atenuan")
        if h_luces:
            luces_atenuan = getattr(h_luces, "valor", "").upper()

    if "bateria" in falla_l or "borne" in falla_l or "arranque" in falla_l or "alternador" in falla_l:
        # Plan B sin multímetro
        if multimetro_disp == "NO":
            if luces_atenuan is None:
                return (
                    "Entiendo, no tienes multímetro. Cuando intentas arrancar, ¿las luces del tablero bajan bastante de intensidad o permanecen casi igual?",
                    QuestionIntent.COMPORTAMIENTO_ARRANQUE,
                )
            return (
                "Al mantener la llave en arranque, ¿se escucha un clic seco en el arrancador o se percibe silencio total?",
                QuestionIntent.COMPORTAMIENTO_ARRANQUE,
            )
        elif multimetro_disp == "SI":
            return (
                "Con el multímetro conectado en escala de 20 V DC: ¿cuánto marca en reposo y a cuánto baja al dar arranque?",
                QuestionIntent.MEDICION_VOLTAJE,
            )
        return "¿Tienes multímetro para comprobar el voltaje?", QuestionIntent.DISPONIBILIDAD_HERRAMIENTA

    if "combustible" in falla_l or "inyector" in falla_l or "bomba" in falla_l:
        # Plan B sin manómetro
        if manometro_disp == "NO":
            return (
                "Entiendo, sin manómetro. Al poner contacto en ON sin dar arranque, ¿se escucha el zumbido de la bomba en el tanque durante 2 a 3 segundos?",
                QuestionIntent.COMPONENTE_REVISADO,
            )
        elif manometro_disp == "SI":
            return (
                "Con el manómetro conectado al riel: ¿cuántos PSI marca con la llave en ON y al dar marcha?",
                QuestionIntent.MEDICION_PRESION,
            )
        return "¿Cuentas con manómetro para medir la presión de combustible?", QuestionIntent.DISPONIBILIDAD_HERRAMIENTA

    if "freno" in falla_l or "disco" in falla_l or "pastilla" in falla_l:
        return "¿Sientes que el pedal esponjoso se va al fondo o vibra el volante al frenar?", QuestionIntent.CONDICION_OPERACION

    if "desbalanceo" in falla_l or "suspension" in falla_l or "rotula" in falla_l:
        return "¿El síntoma o vibración aumenta a partir de cierta velocidad (ej. más de 60-80 km/h)?", QuestionIntent.CONDICION_OPERACION

    if "recalienta" in falla_l or "termostato" in falla_l or "refrigerante" in falla_l:
        return "¿Has revisado si el nivel de refrigerante en el depósito disminuye?", QuestionIntent.COMPONENTE_REVISADO

    return "¿Has podido verificar este punto o deseas que te detalle el procedimiento de prueba?", QuestionIntent.GENERAL


class FormateadorCompacto:
    """Formateador oficial de salidas compactas para WhatsApp."""

    @classmethod
    def calcular_scores_presentacion(
        cls, top_hipotesis: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """
        Calcula scores de presentación para WhatsApp sin alterar las probabilidades RAW.
        Garantiza que tres hipótesis mutuamente excluyentes nunca sumen más de 100%.
        """
        if not top_hipotesis:
            return []

        items = list(top_hipotesis[:3])
        probs = [float(item.get("probabilidad", 0.0)) for item in items]
        pcts = [int(round(p * 100)) if p <= 1.0 else int(round(p)) for p in probs]
        suma_pcts = sum(pcts)

        # Si representan una distribución conjunta o diferencial (sum <= 1.05), no pueden sumar > 100%
        es_conjunta = sum(probs) <= 1.05
        if es_conjunta and suma_pcts > 100:
            exceso = suma_pcts - 100
            for i in reversed(range(len(pcts))):
                ajuste = min(exceso, pcts[i])
                pcts[i] -= ajuste
                exceso -= ajuste
                if exceso <= 0:
                    break

        resultado = []
        for item, pct in zip(items, pcts):
            resultado.append({
                "falla": item.get("falla", ""),
                "probabilidad_raw": item.get("probabilidad", 0.0),
                "porcentaje_presentacion": pct,
                "es_distribucion_conjunta": es_conjunta,
            })
        return resultado

    @classmethod
    def formatear_respuesta_diagnostico(
        cls,
        top_hipotesis: List[Dict[str, Any]],
        sintoma_original: str = "",
        contexto_rag: str = "",
        prueba_personalizada: Optional[str] = None,
        pregunta_personalizada: Optional[str] = None,
        estado: Optional[Any] = None,
    ) -> str:
        """
        Produce el formato canónico compacto para WhatsApp:
        🔧 Posibles causas
        1. [Hipótesis Top 1] — [confianza]%
        2. [Hipótesis Top 2] — [confianza]%
        3. [Hipótesis Top 3] — [confianza]%

        🛠️ Primero revisa: [prueba/acción concreta y breve].

        [Pregunta contextual]
        """
        if not top_hipotesis:
            return (
                "🔧 *Posibles causas*\n\n"
                "1. Falla mecánica en evaluación — 50%\n\n"
                "🛠️ Primero revisa: inspección física en elevador para identificar holguras o fugas.\n\n"
                "¿Puedes describir más detalles del comportamiento del vehículo?"
            )

        # 1. Determinación del tipo de combustible si está disponible
        combustible_str = ""
        if estado:
            combustible_str = getattr(estado, "combustible", "") or ""
            if not combustible_str and getattr(estado, "hechos", None):
                h_comb = estado.hechos.get("combustible")
                if h_comb:
                    combustible_str = getattr(h_comb, "valor", "") or ""
        combustible_str = str(combustible_str).lower()

        # 2. Bloque de hipótesis con scores de presentación controlados (Fase 9.10)
        scores_pres = cls.calcular_scores_presentacion(top_hipotesis)
        es_conjunta = scores_pres[0].get("es_distribucion_conjunta", True) if scores_pres else True

        lineas_hipotesis = []
        num_mostrado = 1
        for item in scores_pres:
            falla_nom = _simplificar_nombre_falla(item.get("falla", ""))
            conf_pct = item.get("porcentaje_presentacion", 0)
            falla_l = falla_nom.lower()

            es_diesel_exclusivo = any(k in falla_l for k in ("diesel", "dpf", "fap", "adblue", "def "))
            if es_diesel_exclusivo:
                if combustible_str in ("gasolina", "glp", "gnv", "nafta"):
                    continue
                elif not combustible_str:
                    lineas_hipotesis.append(f"{num_mostrado}. {falla_nom} — {conf_pct}% *(solo si es Diésel)*")
                    num_mostrado += 1
                    if num_mostrado > 3:
                        break
                    continue

            lineas_hipotesis.append(f"{num_mostrado}. {falla_nom} — {conf_pct}%")
            num_mostrado += 1
            if num_mostrado > 3:
                break

        bloque_causas = "\n".join(lineas_hipotesis)
        titulo_causas = "🔧 *Posibles causas*" if es_conjunta else "🔧 *Posibles causas (confianza individual)*"

        # 2. Acción o prueba prioritaria
        top1_falla = top_hipotesis[0].get("falla", "")
        accion = prueba_personalizada or _extraer_accion_prioritaria(top1_falla, contexto_rag, estado)
        if not accion.endswith("."):
            accion += "."

        # 3. Pregunta contextual
        if pregunta_personalizada:
            pregunta = pregunta_personalizada
        else:
            pregunta, _ = cls.obtener_pregunta_contextual(top1_falla, sintoma_original, estado)

        return (
            f"{titulo_causas}\n\n"
            f"{bloque_causas}\n\n"
            f"🛠️ *Primero revisa:* {accion}\n\n"
            f"{pregunta}"
        )

    @classmethod
    def obtener_pregunta_contextual(
        cls,
        top1_falla_o_hipotesis: Any,
        sintoma_original: str = "",
        estado: Optional[Any] = None,
    ) -> Tuple[str, QuestionIntent]:
        """Retorna la pregunta contextual y su QuestionIntent correspondiente."""
        if isinstance(top1_falla_o_hipotesis, list) and top1_falla_o_hipotesis:
            primera = top1_falla_o_hipotesis[0]
            falla = primera.get("falla", "") if isinstance(primera, dict) else str(primera)
        elif isinstance(top1_falla_o_hipotesis, dict):
            falla = top1_falla_o_hipotesis.get("falla", "")
        else:
            falla = str(top1_falla_o_hipotesis or "")
        return _generar_pregunta_contextual(falla, sintoma_original, estado)

    @classmethod
    def formatear_detalle_tecnico(
        cls,
        falla: str,
        procedimiento_rag: str = "",
        titulo_manual: str = "",
        tolerancias_clave: str = "",
        estado: Optional[Any] = None,
    ) -> str:
        """Formatea la explicación técnica paso a paso bajo demanda ('más detalles')."""
        from src.core.conversacion.models import FactState

        falla_nom = _simplificar_nombre_falla(falla)
        lineas = [f"📋 *Procedimiento de comprobación: {falla_nom}*\n"]

        if isinstance(procedimiento_rag, tuple):
            procedimiento_rag = procedimiento_rag[0] or ""
        procedimiento_rag = str(procedimiento_rag or "").strip()
        procedimiento_rag = re.sub(
            r"tolerancias\s+y\s+especificaciones\s+metrológicas\s+oem:?",
            "Valores del procedimiento técnico recuperado:",
            procedimiento_rag,
            flags=re.IGNORECASE,
        )
        procedimiento_rag = re.sub(
            r"especificaciones\s+metrológicas\s+oem:?",
            "valores del procedimiento técnico recuperado:",
            procedimiento_rag,
            flags=re.IGNORECASE,
        )

        # 1. Manejo estricto de DTC Observado vs DTC Relacionado (Fase 9.3)
        dtcs_en_texto = list(dict.fromkeys(re.findall(r"\b[PCBU]\d{4}\b", procedimiento_rag, re.IGNORECASE)))

        directriz = obtener_directriz_taller(falla)
        if directriz and directriz.dtc_frecuente and directriz.dtc_frecuente != "N/A":
            for d in directriz.dtc_frecuente.split("/"):
                d_c = d.strip()
                if re.match(r"^[PCBU]\d{4}$", d_c, re.IGNORECASE) and d_c not in dtcs_en_texto:
                    dtcs_en_texto.append(d_c)

        tiene_dtc_observado = False
        codigos_observados = []
        if estado:
            for h in getattr(estado, "hechos", {}).values():
                if getattr(h, "categoria", "") == "dtc" and getattr(h, "estado", None) == FactState.CONFIRMADO:
                    tiene_dtc_observado = True
                    codigos_observados.append(h.valor)

        if tiene_dtc_observado and codigos_observados:
            lineas.append(f"📡 *Código reportado por el escáner:* {', '.join(codigos_observados)}\n")
        elif dtcs_en_texto and not (directriz and directriz.es_mecanica_pura and not dtcs_en_texto):
            codigos_rel = ", ".join(dtcs_en_texto[:3])
            lineas.append(f"📡 *Si realizas un escaneo, algunos códigos relacionados que podrían aparecer son:* {codigos_rel}\n")

        # 2. Pasos de comprobación limpios
        if procedimiento_rag:
            pasos = []
            for p in procedimiento_rag.split("\n"):
                p_s = p.strip()
                if not p_s or p_s.startswith("#") or p_s.startswith("METADATOS:"):
                    continue
                if re.match(r"^(código[^\n:]*|codigo[^\n:]*|dtc[^\n:]*|gravedad[^\n:]*|modelos compatibles[^\n:]*|síntomas[^\n:]*|sintomas[^\n:]*):", p_s, re.IGNORECASE):
                    continue
                if "instrucciones paso a paso:" in p_s.lower():
                    continue
                pasos.append(p_s)

            if pasos:
                lineas.append("\n".join(pasos[:8]))
            else:
                lineas.append(procedimiento_rag[:500])
        elif directriz:
            lineas.append(f"1. {directriz.prueba_sugerida}")
        else:
            lineas.append("1. Inspección metrológica de tolerancias según manual de servicio del fabricante.")

        if tolerancias_clave:
            lineas.append(f"\n🔬 *Tolerancias y valores nominales:* {tolerancias_clave}")

        lineas.append("\n¿Deseas registrar el resultado de alguna de estas pruebas?")
        return "\n".join(lineas)
