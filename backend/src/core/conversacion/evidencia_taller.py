"""Conservación de observaciones de taller y preguntas específicas de mezcla."""

import re

from src.core.conversacion.models import FactType, QuestionIntent
from src.core.conversacion.ruteador_sistema import _normalizar, detectar_ruta_sistema


def registrar_evidencia(estado, mensaje):
    """Retiene el mensaje técnico literal; nunca interpreta una medición como una causa."""
    texto = _normalizar(mensaje)
    extraidos = []

    def guardar(campo, valor, categoria="sintoma"):
        hecho = estado.registrar_hecho(
            campo, valor, categoria=categoria, texto_crudo=mensaje, tipo=FactType.CONDICION
        )
        extraidos.append(hecho.to_dict())

    if re.search(r"\b(escaner|scanner|scaner)\b.*\b(arroja|indica|conect|codigo|mezcla)", texto):
        guardar("escaner_disponible", "SI", "herramienta")
    if "caliente" in texto and "no esta caliente" not in texto:
        guardar("temperatura", "caliente", "temperatura")
    if any(p in texto for p in ("mezcla pobre", "inyector", "injector", "sensor de oxigeno", "sensor o2")):
        guardar(f"evidencia_taller_{estado.turno_actual}", mensaje)
    if re.search(r"\b(?:se queda|marca|mide)\s+(?:en\s+)?\d+[.,]\d+", texto):
        guardar(f"medicion_taller_{estado.turno_actual}", mensaje, "medicion")
    # Un pronombre solo se vincula si hay exactamente una hipótesis en la última
    # pregunta; con varias piezas posibles no inferimos qué componente se descartó.
    if re.fullmatch(r"ya (?:lo )?revise y eso esta bien[.! ]*", texto):
        ultima = estado.ultima_pregunta() or {}
        candidatas = ultima.get("hipotesis", [])
        if len(candidatas) == 1 and candidatas[0] not in estado.hipotesis_descartadas:
            estado.hipotesis_descartadas.append(candidatas[0])
    return extraidos


def pregunta_mezcla(estado):
    """Pregunta una vez por dato; no reinicia el cuestionario de condiciones generales."""
    if detectar_ruta_sistema(estado).sistema != "INYECCION_MEZCLA":
        return None
    preguntas = []
    dtc_conocido = any(h.categoria == "dtc" for h in estado.hechos.values())
    if not dtc_conocido:
        preguntas.append((
            "¿Cuál es el código DTC exacto reportado, o el escáner no registra códigos?",
            QuestionIntent.CODIGO_DTC,
        ))
    texto = _normalizar(" ".join(estado.historial_mensajes_usuario))
    if re.search(r"\b(?:se queda|marca|mide)\s+(?:en\s+)?\d+[.,]\d+", texto):
        preguntas.append((
            "Para interpretar esa lectura, ¿qué sensor o parámetro mediste, "
            "en qué unidad y con qué instrumento?",
            QuestionIntent.MEDICION_TECNICA,
        ))
    if "oxigeno" in texto or "sensor o2" in texto or "lambda" in texto:
        preguntas.append((
            "¿La lectura corresponde al sensor O2 anterior o posterior al catalizador, "
            "y se obtuvo con escáner o multímetro?",
            QuestionIntent.MEDICION_TECNICA,
        ))
    if "inyect" in texto or "inject" in texto:
        preguntas.append((
            "¿Con qué prueba comprobaste el caudal de los inyectores y qué resultado obtuviste?",
            QuestionIntent.COMPONENTE_REVISADO,
        ))
    preguntas.append((
        "¿Tienes una medición de presión de combustible comparada con la especificación "
        "del motor? Indica el valor y la unidad, o si aún no se ha medido.",
        QuestionIntent.MEDICION_PRESION,
    ))
    preguntas.append((
        "¿Se realizó una prueba de fugas de admisión y cuál fue el resultado?",
        QuestionIntent.COMPONENTE_REVISADO,
    ))
    for pregunta, intent in preguntas:
        if not estado.ya_preguntado_texto(pregunta):
            return pregunta, intent
    return "", None


def respuesta_evidencia_insuficiente(estado):
    """Separa los hallazgos reportados de una conclusión no sustentada por ML."""
    ruta = detectar_ruta_sistema(estado).sistema
    if ruta == "CLIMATIZACION":
        return (
            "El acople del compresor ya quedó registrado. Sin confirmar una causa todavía, "
            "el siguiente paso es verificar el electroventilador y medir las presiones del "
            "refrigerante con el equipo adecuado; también inspecciona fugas en las tuberías."
        )
    if getattr(getattr(estado, "estado_operativo", None), "name", "") == "ARRANQUE":
        return (
            "Para continuar con el problema de arranque, confirma si el motor gira lento, "
            "se escucha un clic o no gira. Luego mide el voltaje de batería y la caída de "
            "tensión al dar arranque antes de sustituir componentes."
        )
    if ruta != "INYECCION_MEZCLA":
        return (
            "No hay una hipótesis con respaldo suficiente para este caso. "
            "Conservo los datos y los descartes registrados; hace falta una comprobación "
            "de taller antes de confirmar una causa."
        )
    observaciones = [h.valor for h in estado.hechos.values()
                     if h.campo.startswith(("evidencia_taller_", "medicion_taller_"))]
    resumen = "\n".join(f"• {texto}" for texto in observaciones[-3:])
    texto = _normalizar(" ".join(estado.historial_mensajes_usuario))
    pasos = []
    if re.search(r"\b0[.,]1\b", texto):
        pasos.append(("identificar_lectura", "La lectura 0.1 no identifica por sí sola una avería. "
                      "Anota el parámetro o sensor, unidad, instrumento y condición de medición; "
                      "si cambiaste el sensor y la lectura sigue igual, registra también ese antecedente."))
    if "inyect" in texto or "inject" in texto:
        pasos.append(("caudal_reportado", "Tomemos como pista el caudal insuficiente que reportaste. "
                      "Documenta cómo se comprobó y si afecta a uno o a todos los inyectores. "
                      "Eso permite distinguir una falla individual de un problema común de alimentación."))
    pasos.extend([
        ("presion", "El siguiente dato útil es la presión de combustible bajo la condición de falla, "
         "comparada con el manual del motor. Si no cuentas con equipo, registra esa limitación; "
         "no abras el circuito de combustible para improvisar la prueba."),
        ("admision", "Para distinguir falta de combustible de entrada de aire no medida, "
         "registra el resultado de la comprobación de fugas de admisión realizada en taller."),
    ])
    vistos = set((estado.obtener_valor_confirmado("orientaciones_mezcla") or "").split("|"))
    for clave, paso in pasos:
        if clave not in vistos:
            vistos.add(clave)
            estado.registrar_hecho("orientaciones_mezcla", "|".join(sorted(vistos)),
                                   categoria="control_flujo", tipo=FactType.CONDICION)
            return (
                "Seguimos con inyección y control de mezcla.\n\n" + paso + "\n\n"
                "Es una ruta de comprobación, no una falla confirmada ni una probabilidad ML."
            )
    return (
        "Resumen del caso para continuar con una comprobación en taller:\n" + resumen + "\n\n"
        "Ya recorrimos las comprobaciones orientativas disponibles. No hay evidencia suficiente "
        "para elegir una causa; aporta el resultado de una de esas pruebas cuando esté disponible. "
        "El caso conserva sus datos y no necesita comenzar de nuevo."
    )
