"""Purificación semántica de síntomas e interpretación de conectores y descartes."""

from __future__ import annotations

import re


def purificar_sintoma_para_vectorizador_ml(texto: str) -> str:
    """
    Interpreta negaciones y contrastes físicos para evitar que términos descartados
    por el conductor (ej: 'la batería tiene fuerza pero no da marcha y suena clac')
    induzcan sesgo espurio en el vectorizador TF-IDF del SVM o en la búsqueda RAG.
    Normaliza legítimamente síntomas sin inyectar etiquetas de fallas ni cadenas
    diagnósticas sintéticas generadas por el sistema.
    """
    # La síntesis clínica ya contiene hechos vigentes y pruebas realizadas.
    # El anexo textual es trazabilidad para el LLM/auditoría, no nueva evidencia
    # independiente: repetirlo en TF-IDF amplifica síntomas antiguos/corregidos.
    texto_filtrado = re.split(
        r"últimos aportes textuales del mecánico\s*\(", texto, maxsplit=1,
        flags=re.IGNORECASE,
    )[0].strip()
    limpio = texto_filtrado.lower()

    # 1. Descarte de batería con síntomas de motor de arranque / solenoide / carbones
    descarte_bateria = any(
        p in limpio for p in (
            "bateria tiene fuerza", "batería tiene fuerza", "bateria esta buena", "batería está buena",
            "bateria nueva", "batería nueva", "luces no bajan", "no se bajan de brillo", "no bajan de brillo",
            "luces no se atenúan", "luces no se atenuan", "faros alumbran parejo", "bateria descartada"
        )
    )
    sintoma_arrancador_electrico = any(
        p in limpio for p in (
            "no da marcha", "no gira", "clac seco", "se queda mudo", "solo un clac",
            "hace clac", "engancha y prende", "toques al arrancador", "golpecitos al arrancador",
            "arrancador pegado", "motor de arranque no gira", "carbones gastados",
            "en caliente no prende", "caliente no arranca"
        )
    )
    if descarte_bateria and sintoma_arrancador_electrico:
        texto_filtrado = re.sub(r"\bbater[ií]a\b", " ", texto_filtrado, flags=re.IGNORECASE)
        texto_filtrado = re.sub(r"\bluces\b", " ", texto_filtrado, flags=re.IGNORECASE)
        texto_filtrado += " no da marcha clac seco arrancador no gira"

    # 1.1 Desambiguación contextual de 'dar arranque' como ACCIÓN DEL CONDUCTOR
    accion_dar_arranque = bool(re.search(
        r"\b(?:le\s+doy\s+arranque|darle\s+arranque|dar\s+arranque|al\s+dar\s+arranque|"
        r"darle\s+a\s+la\s+llave|intento\s+prenderlo|insisto\s+con\s+la\s+llave)\b",
        limpio
    ))
    if accion_dar_arranque and not sintoma_arrancador_electrico:
        texto_filtrado = re.sub(
            r"\b(?:le\s+doy\s+arranque|darle\s+arranque|dar\s+arranque|al\s+dar\s+arranque)\b",
            "intentar encender el motor",
            texto_filtrado,
            flags=re.IGNORECASE
        )

    # 2. Descarte de freno en vibraciones de velocidad (Balanceo / Alineación de ruedas)
    # Detección exhaustiva de negaciones en frenado
    niega_freno = bool(re.search(
        r"\b(?:al\s+(?:pisar\s+(?:el\s+)?)?fren(?:o|ar)|frenando)\s+no\s+(?:vibra|tiembla|se\s+siente|hace\s+nada|pasa\s+nada|en\s+absoluto)\b|"
        r"\bno\s+(?:vibra|tiembla|se\s+siente)\s+al\s+(?:pisar\s+(?:el\s+)?)?fren(?:o|ar)\b|"
        r"\b(?:sin\s+pisar\s+(?:el\s+)?freno\s+vibra|vibra\s+sin\s+frenar|tiembla\s+sin\s+frenar|frenos\s+descartados|frenos\s+no\s+son)\b",
        limpio
    ))
    niega_freno = niega_freno or bool(
        re.search(
            r"\bsin\s+(?:tocar|pisar|apretar)\s+(?:(?:el|los)\s+)?(?:pedal\s+de\s+)?freno\b",
            limpio,
        )
        and re.search(r"\b(?:vibra|tiembla|vibraci[oó]n)\b", limpio)
    )

    afirma_freno = not niega_freno and any(
        p in limpio for p in (
            "vibra al frenar", "tiembla al frenar", "al frenar vibra", "cuando frena vibra",
            "cuando freno vibra", "al pisar el pedal de freno", "al pisar el freno", "cuando frena",
            "al frenar", "apenas piso el freno", "pedal tiembla", "patea el pie", "pedal me patea"
        )
    )

    if niega_freno:
        texto_filtrado = re.sub(r"\bfren(?:o|os|ar|ada)\b", " ", texto_filtrado, flags=re.IGNORECASE)
        texto_filtrado = re.sub(r"\bdisco(?:s)?\b", " ", texto_filtrado, flags=re.IGNORECASE)
        texto_filtrado = re.sub(r"\bpastilla(?:s)?\b", " ", texto_filtrado, flags=re.IGNORECASE)
        texto_filtrado += " vibracion en marcha a velocidad constante"
    elif afirma_freno and any(f in limpio for f in ("freno", "frenar", "pedal")):
        texto_filtrado = re.sub(r"\bresto\s+del\s+veh[ií]culo\s+no\s+vibra\b", " ", texto_filtrado, flags=re.IGNORECASE)
        texto_filtrado += " vibracion al frenar pedal de freno volante al frenar alabeo de disco"

    # 3. Descarte de encendido (bujías)
    mencion_bobina_falla = any(
        p in limpio for p in (
            "bobina falla", "cambiar la bobina", "falla de chispa", "sin chispa",
            "no genera chispa", "bobina individual", "bobina no manda", "bobina mala"
        )
    )
    descarte_bujias = any(
        p in limpio for p in (
            "cambie bujias", "cambié bujías", "cambie bujia", "cambié bujía",
            "bujias nuevas", "bujías nuevas", "cambie cables y bujias", "bujias descartadas",
            "bujias no son", "cambie filtro de aire pero sigue"
        )
    ) and not mencion_bobina_falla

    if descarte_bujias:
        texto_filtrado = re.sub(r"\bbuj[ií]as?\b", " ", texto_filtrado, flags=re.IGNORECASE)

    # 4. Negación de sobrecalentamiento y fugas de refrigerante
    if any(p in limpio for p in ("no se calienta", "no calienta", "temperatura normal", "aguja en el medio")):
        texto_filtrado = re.sub(r"\bcalienta\b", " ", texto_filtrado, flags=re.IGNORECASE)
    if any(p in limpio for p in ("no pierde refrigerante", "no pierde agua", "no consume agua")):
        texto_filtrado = re.sub(r"\brefrigerante\b", " ", texto_filtrado, flags=re.IGNORECASE)

    # 5. Embrague: zapateo / trepidación al arrancar en primera o soltar el pedal, o patinado bajo carga
    limpio_full = texto.lower()
    sintoma_trepidacion_embrague = bool(re.search(
        r"\b(?:zapatea|zapateo|trepidaci[oó]n)\b.{0,40}\b(?:al\s+arrancar|en\s+primera|al\s+salir|al\s+soltar)\b|"
        r"\b(?:al\s+arrancar|en\s+primera|al\s+salir)\b.{0,40}\b(?:zapatea|zapateo|trepidaci[oó]n)\b|"
        r"\b(?:pedal\s+vibra|vibra\s+(?:el\s+)?pedal)\b.{0,30}\b(?:al\s+soltar|cuando\s+lo\s+suelto)\b",
        limpio_full,
    ))
    sintoma_patinado_embrague = bool(re.search(
        r"\b(?:revoluciones\s+suben|rpm\s+suben)\b.{0,45}\b(?:no\s+avanza|no\s+camina|huele\s+a\s+quemado)\b|"
        r"\b(?:embrague|clutch|disco)\s+patina\b",
        limpio_full,
    ))
    if sintoma_trepidacion_embrague:
        texto_filtrado += " trepidacion y vibracion al salir en primera"
    elif sintoma_patinado_embrague:
        texto_filtrado += " patinado suben revoluciones sin avanzar"

    return texto_filtrado
