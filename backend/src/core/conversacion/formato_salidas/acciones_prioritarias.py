"""Extracción de acciones y pruebas prioritarias de taller (Fase 9.3)."""

from __future__ import annotations

import re
from typing import Any, Optional, Tuple

from src.core.conversacion.models import QuestionIntent
from src.core.taxonomy.catalogo_pruebas_taller import (
    obtener_directriz_taller,
)


def simplificar_nombre_falla(falla: str) -> str:
    """Elimina identificadores internos o códigos crudos de la falla."""
    if not falla:
        return "Falla mecánica bajo revisión"
    texto = str(falla).strip()
    if "_" in texto and " " not in texto:
        texto = texto.replace("_", " ").title()
    texto = re.sub(r"^(sintoma|falla|error)_+", "", texto, flags=re.IGNORECASE)
    return texto[0].upper() + texto[1:] if texto else "Revisión técnica general"


_PATRONES_PASO_PREPARATORIO = re.compile(
    r"(?:"
    r"desconect(?:ar|e)\s+.*(?:borne|bater[ií]a|cable\s+negativo|alimentaci[oó]n|corriente)"
    r"|borne\s+negativo"
    r"|cable\s+negativo"
    r"|retirar\s+.*(?:alimentaci[oó]n|bater[ií]a|borne)"
    r"|aislar\s+.*(?:borne|cable|bater[ií]a)"
    r"|por\s+seguridad"
    r"|como\s+precauci[oó]n"
    r"|precauci[oó]n\s+de\s+seguridad"
    r"|(?:elevar|levantar)\s+el\s+veh[ií]culo"
    r"|estacionar\s+en\s+superficie\s+plana"
    r"|apagar\s+el\s+motor\s+y\s+esperar"
    r")",
    re.IGNORECASE,
)


def es_paso_preparatorio(texto: str) -> bool:
    """Detecta si un paso del manual RAG es preparatorio/seguridad y no una prueba diagnóstica."""
    return bool(_PATRONES_PASO_PREPARATORIO.search(texto))


def extraer_accion_prioritaria(falla: str, contexto_rag: str = "", estado: Optional[Any] = None) -> str:
    """Extrae una prueba física o acción concreta y breve (<140 caracteres)."""
    if estado:
        from src.core.conversacion.gestor_plan_b import GestorPlanB
        plan_b = GestorPlanB.obtener_plan_b_para_falla(falla, estado)
        if plan_b:
            return plan_b[0]

    directriz = obtener_directriz_taller(falla)
    falla_l = falla.lower().replace("í", "i").replace("á", "a").replace("é", "e").replace("ó", "o").replace("ú", "u")

    caida_excesiva = estado.obtener_hecho("caida_tension_excesiva") if estado else None
    voltaje_arranque_normal = estado.obtener_hecho("voltaje_arranque_normal") if estado else None
    bateria_normal = bool(
        (caida_excesiva and caida_excesiva.valor == "NO")
        or (voltaje_arranque_normal and voltaje_arranque_normal.valor == "SI")
    )
    if ("bateria" in falla_l or "borne" in falla_l) and not bateria_normal:
        return "voltaje en reposo (referencial ≥12.6 V), caída en arranque (mínimo 9.6 V) y ajuste de bornes."
    if "alternador" in falla_l or ("carga" in falla_l and "descarga" not in falla_l):
        return "voltaje de carga en ralentí con motor encendido (debe situarse entre 13.8 V y 14.4 V)."
    if "arranque" in falla_l or "arrancador" in falla_l or "solenoide" in falla_l:
        return "caída de tensión en el terminal 50 del solenoide y verificar si el motor gira al dar contacto."
    if "bomba" in falla_l and "combustible" in falla_l:
        return "presión de combustible en el riel con manómetro y comparar con la especificación del fabricante."
    if "inyector" in falla_l or "filtro" in falla_l:
        return "presión en el riel de inyección y prueba de entrega/goteo en banco o probador."
    if any(k in falla_l for k in ("precalentamiento", "incandesc", "glow", "calentador")):
        return "resistencia de las bujías incandescentes con multímetro (típico 0.5 a 1.5 Ω) y alimentación de 12 V del relé de precalentamiento."
    if "bujia" in falla_l or "bobina" in falla_l:
        prueba_chispa_completada = bool(
            estado
            and getattr(estado, "completed_tests", {}).get("prueba_chispa") is not None
        )
        if prueba_chispa_completada:
            return "estado físico y calibración del electrodo de las bujías."
        return "salto de chispa en las bobinas y estado/calibración del electrodo de las bujías."
    if "desbalanceo" in falla_l or "llanta" in falla_l:
        return "balanceo dinámico de las ruedas en banco e inspección de deformación en neumáticos."
    if "embrague" in falla_l or "clutch" in falla_l:
        return "recorrido libre del pedal, retorno del mando y fugas hidráulicas visibles con motor apagado; comparar con especificación OEM."
    if "alabeo" in falla_l or "disco" in falla_l:
        return "alabeo de los discos con reloj comparador y comparación con la especificación del fabricante para ese vehículo."
    if "pastilla" in falla_l or "freno" in falla_l:
        return "espesor de las pastillas y estado de discos, comparados con el límite de servicio del fabricante para ese vehículo."

    if "termostato" in falla_l or "ventilador" in falla_l or "recalienta" in falla_l:
        return "temperatura en ambas mangueras del radiador y activación oportuna del electroventilador."

    if directriz and directriz.prueba_sugerida:
        oraciones = directriz.prueba_sugerida.split(". ")
        primera = oraciones[0].strip()
        if not primera.endswith("."):
            primera += "."
        if len(primera) <= 250:
            return primera[0].lower() + primera[1:]
        corte = primera[:240].rsplit(",", 1)[0].strip()
        if not corte.endswith("."):
            corte += "."
        return corte[0].lower() + corte[1:]

    if contexto_rag:
        candidatos_rag = re.findall(r"(?:^|\n)\s*\d+\.\s*([^\n\r.]+)", contexto_rag)
        for paso in candidatos_rag:
            paso_limpio = paso.strip()
            if not paso_limpio or es_paso_preparatorio(paso_limpio):
                continue
            if len(paso_limpio) <= 180:
                return paso_limpio[0].lower() + paso_limpio[1:] + "."

    return "inspección física directa del componente y sus conexiones principales en taller."


def generar_pregunta_contextual(
    falla: str,
    texto_usuario: str = "",
    estado: Optional[Any] = None,
) -> Tuple[str, QuestionIntent]:
    """Genera la pregunta contextual según la hipótesis prioritaria."""
    falla_l = falla.lower().replace("í", "i").replace("á", "a").replace("é", "e").replace("ó", "o").replace("ú", "u")

    if estado:
        from src.core.conversacion.gestor_plan_b import GestorPlanB
        plan_b = GestorPlanB.obtener_plan_b_para_falla(falla, estado)
        if plan_b:
            return plan_b[1], plan_b[2]

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

    if "embrague" in falla_l or "clutch" in falla_l:
        return "¿El patinamiento ocurre con el pedal completamente liberado y bajo carga?", QuestionIntent.CONDICION_OPERACION

    if "freno" in falla_l or "disco" in falla_l or "pastilla" in falla_l:
        return "¿Sientes que el pedal esponjoso se va al fondo o vibra el volante al frenar?", QuestionIntent.CONDICION_OPERACION

    if "desbalanceo" in falla_l or "suspension" in falla_l or "rotula" in falla_l:
        return "¿El síntoma o vibración aumenta a partir de cierta velocidad (ej. más de 60-80 km/h)?", QuestionIntent.CONDICION_OPERACION

    if "recalienta" in falla_l or "termostato" in falla_l or "refrigerante" in falla_l:
        return "¿Has revisado si el nivel de refrigerante en el depósito disminuye?", QuestionIntent.COMPONENTE_REVISADO

    return "¿Has podido verificar este punto o deseas que te detalle el procedimiento de prueba?", QuestionIntent.CONFIRMACION_ALTERNATIVA
