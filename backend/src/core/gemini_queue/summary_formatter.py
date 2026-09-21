"""Generación y formateo de resúmenes operativos de diagnóstico para WhatsApp."""

from __future__ import annotations

import re

from src.application.services.confirmacion_diagnostico import instrucciones_confirmacion_whatsapp
from src.config import settings
from src.core.gemini_queue.models import SolicitudGeminiEncolada
from src.core.taxonomy.catalogo_pruebas_taller import obtener_directriz_taller
from src.core.traductor_jerga import normalizar_jerga_peruana
from src.core.vehicle_profile import extraer_datos_vehiculo
from src.core.whatsapp_response import formatear_consulta_tecnica_whatsapp


def crear_resumen_whatsapp(
    solicitud: SolicitudGeminiEncolada, texto_respuesta: str
) -> str:
    """Crea una salida breve y operativa; el detalle completo queda en PostgreSQL."""
    if solicitud.tipo_consulta == "consulta_tecnica":
        datos_vehiculo = extraer_datos_vehiculo(solicitud.sintoma)
        modelo_informado = bool(
            datos_vehiculo.get("modelo")
            or (
                solicitud.marca_modelo
                and solicitud.marca_modelo.lower()
                not in {"generico", "vehiculo generico"}
            )
        )
        return formatear_consulta_tecnica_whatsapp(
            texto_respuesta,
            modelo_informado=modelo_informado,
        )

    confianza = max(0, min(100, int(solicitud.confianza_ml * 100)))
    sintoma = normalizar_jerga_peruana(solicitud.sintoma)
    tiene_dtc = bool(re.search(r"\b[pbcu]\d{4}\b", sintoma, re.IGNORECASE))
    tiene_dtc_encendido = bool(re.search(r"\bp03\d{2}\b", sintoma, re.IGNORECASE))
    tiene_componente_especifico = any(
        c in sintoma.lower()
        for c in (
            "bobina", "bujia", "bujía", "inyector", "sensor", "valvula", "válvula",
            "compresion", "compresión", "bomba de gasolina", "bomba de combustible",
            "cables de bujia", "distribuidor", "catalizador", "egr", "maf", "map", "cilindro",
        )
    )
    es_gas = "gnv" in sintoma or "gas natural" in sintoma or "glp" in sintoma
    solo_gas = es_gas and any(
        frase in sintoma
        for frase in (
            "solo en gnv", "solo a gnv", "solo con gnv", "solo usando gnv",
            "solo en glp", "solo a glp", "solo con glp", "solo usando glp",
            "solo a gas", "solo con gas", "solo usando gas",
        )
    )
    hipotesis = solicitud.diagnostico_ml
    describe_patinamiento = (
        ("rpm" in sintoma or "revoluciones" in sintoma)
        and ("no avanza" in sintoma or "sin aumentar velocidad" in sintoma)
    )
    if es_gas and not describe_patinamiento and any(
        termino in hipotesis.lower() for termino in ("embrague", "clutch", "disco")
    ):
        hipotesis = "Pérdida de potencia bajo carga: diferenciar sistema GNV/GLP y motor"

    es_desbalanceo_o_alineacion = any(
        t in hipotesis.lower()
        for t in ("desbalance", "alinea", "llanta", "aro")
    ) or (
        any(w in sintoma for w in ("timon", "timón", "volante", "direccion", "dirección", "llanta", "aro"))
        and any(w in sintoma for w in ("vibra", "tiembla", "cabecea", "jala", "desvia", "desvía", "tira"))
        and not any(w in sintoma for w in ("al frenar", "piso el freno", "pisar el freno", "al pisar"))
    )

    es_alabeo_discos = any(
        t in hipotesis.lower() for t in ("alabeado", "disco de freno", "alabeo")
    ) or (
        any(w in sintoma for w in ("freno", "frenar", "disco"))
        and any(w in sintoma for w in ("zapatea", "pulsa", "vibra al frenar", "tiembla al frenar"))
    )

    es_pastillas_freno = any(
        t in hipotesis.lower() for t in ("pastilla", "zapata")
    ) or (
        any(w in sintoma for w in ("freno", "frenar", "pastilla"))
        and any(w in sintoma for w in ("chilla", "chillido", "chirrido", "fierro con fierro", "raspa"))
    )

    es_suspension_rotulas = any(
        t in hipotesis.lower() for t in ("suspension", "suspensión", "amortiguador", "bujes", "rotula", "rótula", "bieleta")
    ) or (
        any(w in sintoma for w in ("rompemuelle", "bache", "trocha", "desnivel"))
        and any(w in sintoma for w in ("golpe", "cloc", "traqueteo"))
    )

    directriz_ml = obtener_directriz_taller(solicitud.diagnostico_ml)
    es_mecanica_ml = directriz_ml.es_mecanica_pura if directriz_ml else False

    if solo_gas and not tiene_dtc and not tiene_componente_especifico and (
        confianza < int(settings.diagnostic.confidence_threshold * 100)
        or any(t in hipotesis.lower() for t in ("embrague", "clutch", "disco", "resultado no concluyente"))
    ):
        hipotesis = (
            "Sistema GNV/GLP bajo carga: posible descalibración o alimentación "
            "de gas (por confirmar)"
        )
    elif confianza < int(settings.diagnostic.confidence_threshold * 100) and not tiene_dtc:
        if es_gas:
            hipotesis = "Pérdida de potencia bajo carga: diferenciar sistema GNV/GLP y motor"
        elif es_desbalanceo_o_alineacion and confianza >= 40:
            hipotesis = "Llantas desbalanceadas o desalineadas"
        elif (es_alabeo_discos or es_pastillas_freno or es_suspension_rotulas) and confianza >= 40:
            hipotesis = solicitud.diagnostico_ml
        elif es_mecanica_ml and confianza >= 35:
            hipotesis = directriz_ml.falla if directriz_ml else solicitud.diagnostico_ml
        elif confianza >= 40:
            # Mantener la hipótesis principal predicha por ML para evaluación del mecánico
            hipotesis = solicitud.diagnostico_ml
        else:
            hipotesis = "Resultado no concluyente: faltan datos y pruebas de confirmación"

    descartar_embrague_por_gas = es_gas and not describe_patinamiento and any(
        t in solicitud.diagnostico_ml.lower() for t in ("embrague", "clutch", "disco")
    )
    if descartar_embrague_por_gas:
        directriz_actual = obtener_directriz_taller(hipotesis)
    else:
        directriz_actual = obtener_directriz_taller(hipotesis) or directriz_ml

    tipo_comprobacion = ""
    if directriz_actual:
        if directriz_actual.es_mecanica_pura:
            tipo_comprobacion = "Inspección física / metrológica (Sin escáner)"
        else:
            tipo_comprobacion = f"Diagnóstico con escáner OBD-II ({directriz_actual.dtc_frecuente})"

    es_hipotesis_encendido = any(
        termino in hipotesis.lower()
        for termino in ("bobina", "bujia", "bujía", "chispa", "encendido", "misfire")
    )
    if tiene_dtc_encendido or es_hipotesis_encendido:
        if es_gas:
            primera_prueba = (
                "Revisar primero la bobina y bujía del cilindro afectado. "
                "(El GLP/GNV requiere mayor tensión de encendido, por lo que una bobina con fuga falla antes a gas que a gasolina)."
            )
        else:
            primera_prueba = (
                "Comprobar chispa y resistencia de bobina/bujía del cilindro afectado; intercambiar con otro cilindro para contrastar DTC."
            )
    elif es_alabeo_discos:
        primera_prueba = (
            "Medir alabeo (runout) y espesor de discos de freno con reloj comparador y micrómetro "
            "antes de rectificar o cambiar piezas."
        )
    elif es_desbalanceo_o_alineacion:
        primera_prueba = (
            "Calibrar presión de inflado en frío en las 4 ruedas, realizar balanceo dinámico "
            "computarizado de ruedas delanteras e inspección de cotas de alineación en elevador."
        )
    elif es_pastillas_freno:
        primera_prueba = (
            "Inspección visual del espesor de pastillas, estado de zapatas y guías de cáliper en rueda."
        )
    elif es_suspension_rotulas:
        primera_prueba = (
            "Inspección y palanqueo en elevador de rótulas, terminales de dirección, terminales de "
            "barra estabilizadora y amortiguadores."
        )
    elif solo_gas:
        primera_prueba = (
            "Revisar primero la calibración/mapa de inyección de gas y la presión bajo carga; "
            "después verificar filtros e inyectores de gas."
        )
    elif es_gas and not (directriz_actual and directriz_actual.es_mecanica_pura):
        primera_prueba = (
            "Comparar el comportamiento en gasolina y GNV/GLP bajo carga. "
            "Si solo falla a gas, revisar presión, filtros, inyectores y calibración."
        )
    elif directriz_actual and directriz_actual.prueba_sugerida:
        primera_prueba = directriz_actual.prueba_sugerida
    elif describe_patinamiento:
        primera_prueba = (
            "Prueba de calado en 3ra marcha y verificación de altura y recorrido de corte del pedal de embrague."
        )
    else:
        primera_prueba = "Realizar inspección funcional y metrológica antes de desmontar o cambiar piezas."

    # Extraer prueba específica recomendada por Gemini LLM si existe en su síntesis
    prueba_llm = None
    m_elevador = re.search(
        r"\*\*\s*(?:Prueba en elevador|Prueba f[ií]sica|Inspecci[oó]n sugerida|Prueba de ruta):\*\*\s*([^\n]+)",
        texto_respuesta,
        re.IGNORECASE,
    )
    if m_elevador:
        prueba_llm = m_elevador.group(1).strip()
    else:
        m_sec2 = re.search(
            r"📖\s*\*\*2\.\s*Procedimiento[^\n]*\*\*\s*\n(.*?)(?=\n⏱️|\Z)",
            texto_respuesta,
            re.DOTALL,
        )
        if m_sec2:
            for b_tit, b_desc in re.findall(r"\*\s*\*\*([^:]+):\*\*\s*([^\n]+)", m_sec2.group(1)):
                if (
                    any(w in b_tit.lower() for w in ("prueba", "elevador", "verificaci", "inspecci"))
                    and "manual" not in b_desc.lower()
                    and len(b_desc) > 20
                ):
                    prueba_llm = f"{b_tit.strip()}: {b_desc.strip()}"
                    break

    if prueba_llm and 15 < len(prueba_llm) < 260:
        primera_prueba = prueba_llm

    # Diagnóstico Diferencial (Top 2 y Top 3 del modelo ML)
    lineas_diferencial = []
    if solicitud.predicciones_ml and len(solicitud.predicciones_ml) > 1:
        for alt in solicitud.predicciones_ml[1:3]:
            falla_alt = alt.get("falla")
            prob_alt = int(alt.get("probabilidad", 0) * 100)
            if not falla_alt or prob_alt < 5:
                continue
            if falla_alt.strip().lower() == hipotesis.strip().lower():
                continue
            if descartar_embrague_por_gas and any(t in falla_alt.lower() for t in ("embrague", "clutch", "disco")):
                continue
            lineas_diferencial.append(f"  • {falla_alt} ({prob_alt}%)")

    bloque_diferencial = ""
    if lineas_diferencial:
        bloque_diferencial = "\n🔍 *Otras posibilidades (ML):*\n" + "\n".join(lineas_diferencial) + "\n"

    bloque_rag = ""
    if (
        solicitud.titulo_manual
        and "coincidencia baja" not in solicitud.titulo_manual.lower()
        and not solicitud.titulo_manual.lower().startswith("sin ")
    ):
        bloque_rag = f"📖 Manual OEM (RAG): *{solicitud.titulo_manual.strip()}*\n"

    texto_limpio = texto_respuesta.lower().replace("*", "")
    if "gravedad: alta" in texto_limpio:
        gravedad = "Alta"
    elif "gravedad: media" in texto_limpio:
        gravedad = "Media"
    elif "gravedad: baja" in texto_limpio:
        gravedad = "Baja"
    else:
        gravedad = "Por confirmar"

    revision = " Se requiere validación física." if solicitud.requiere_revision_humana else ""
    linea_comprobacion = f"Tipo de comprobación: *{tipo_comprobacion}*\n" if tipo_comprobacion else ""
    return (
        "🔧 *Resumen de diagnóstico (ML + RAG + LLM)*\n"
        f"Hipótesis ML: *{hipotesis}*\n"
        f"Confianza ML: *{confianza}%*.{revision}\n"
        f"{linea_comprobacion}"
        f"{bloque_diferencial}"
        f"{bloque_rag}"
        f"Primera prueba: {primera_prueba}\n"
        f"Gravedad: *{gravedad}*.\n"
        "📋 Análisis completo disponible en el panel del taller."
        f"{instrucciones_confirmacion_whatsapp()}"
    )
