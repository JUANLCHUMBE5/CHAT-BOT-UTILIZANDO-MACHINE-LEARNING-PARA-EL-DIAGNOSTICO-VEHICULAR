"""Purificación semántica de síntomas e interpretación de conectores y descartes."""

from __future__ import annotations

import re


def purificar_sintoma_para_vectorizador_ml(texto: str) -> str:
    """
    Interpreta negaciones y contrastes físicos para evitar que términos descartados
    por el conductor (ej: 'la batería tiene fuerza pero no da marcha y suena clac')
    induzcan sesgo espurio en el vectorizador TF-IDF del SVM o en la búsqueda RAG.
    """
    limpio = texto.lower()
    texto_filtrado = texto

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
        texto_filtrado += " falla motor de arranque solenoide carbones terminal 50 no da marcha clac seco arrancador pegado"

    # 1.1 Desambiguación contextual de 'dar arranque' como ACCIÓN DEL CONDUCTOR (no avería de arrancador)
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
        if any(w in limpio for w in ("gira", "bombeando", "tosa", "no enciende", "no prende", "no arranca")):
            texto_filtrado += " motor gira con normalidad falta suministro de combustible bomba de gasolina o chispa no enciende"

    # 2. Descarte de freno en vibraciones de velocidad (Balanceo / Alineación de ruedas)
    # Detección exhaustiva de negaciones en frenado
    niega_freno = bool(re.search(
        r"\b(?:al\s+(?:pisar\s+(?:el\s+)?)?fren(?:o|ar)|frenando)\s+no\s+(?:vibra|tiembla|se\s+siente|hace\s+nada|pasa\s+nada|en\s+absoluto)\b|"
        r"\bno\s+(?:vibra|tiembla|se\s+siente)\s+al\s+(?:pisar\s+(?:el\s+)?)?fren(?:o|ar)\b|"
        r"\b(?:sin\s+pisar\s+(?:el\s+)?freno\s+vibra|vibra\s+sin\s+frenar|tiembla\s+sin\s+frenar|frenos\s+descartados|frenos\s+no\s+son)\b",
        limpio
    ))

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
        texto_filtrado += " llantas desbalanceadas desalineadas vibracion velocidad direccion plomos balanceo alineacion"
    elif afirma_freno and any(f in limpio for f in ("freno", "frenar", "pedal")):
        texto_filtrado += " discos de freno alabeados desgastados deformados alabeo variacion espesor dtv reloj comparador vibracion pedal volante al frenar"

    # 3. Descarte de encendido (bujías) cuando el síntoma es de suministro/presión de combustible
    # Solo si no se afirma que la bobina o la chispa es la que está fallando
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
    sintoma_combustible = any(
        p in limpio for p in (
            "asientos de atras", "asientos de atrás", "asiento trasero", "debajo del asiento",
            "zumbido", "tanque", "ahoga", "bomba", "filtro de gasolina", "pata a fondo",
            "subida", "acelerar a fondo", "falta fuerza", "pierde toda la fuerza"
        )
    )
    if descarte_bujias and sintoma_combustible:
        texto_filtrado = re.sub(r"\bbuj[ií]as?\b", " ", texto_filtrado, flags=re.IGNORECASE)
        texto_filtrado += " bomba de gasolina quemada baja presion caudal obstruccion tanque combustible zumbido"

    # 4. Negación de sobrecalentamiento y fugas de refrigerante
    if any(p in limpio for p in ("no se calienta", "no calienta", "temperatura normal", "aguja en el medio")):
        texto_filtrado = re.sub(r"\bcalienta\b", " ", texto_filtrado, flags=re.IGNORECASE)
    if any(p in limpio for p in ("no pierde refrigerante", "no pierde agua", "no consume agua")):
        texto_filtrado = re.sub(r"\brefrigerante\b", " ", texto_filtrado, flags=re.IGNORECASE)

    return texto_filtrado
