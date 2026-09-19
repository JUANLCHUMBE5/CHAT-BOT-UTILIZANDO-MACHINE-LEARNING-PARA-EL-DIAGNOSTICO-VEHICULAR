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
    sintoma_arrancador = any(
        p in limpio for p in (
            "no da marcha", "no gira", "clac seco", "se queda mudo", "solo un clac",
            "hace clac", "engancha y prende", "toques al arrancador", "golpecitos al arrancador",
            "en caliente no prende", "caliente no arranca"
        )
    )
    if descarte_bateria and sintoma_arrancador:
        texto_filtrado = re.sub(r"\bbater[ií]a\b", " ", texto_filtrado, flags=re.IGNORECASE)
        texto_filtrado = re.sub(r"\bluces\b", " ", texto_filtrado, flags=re.IGNORECASE)
        texto_filtrado += " falla motor de arranque solenoide carbones terminal 50 no da marcha clac seco arrancador pegado"

    # 2. Descarte de freno en vibraciones de velocidad (Balanceo / Alineación de ruedas)
    # Solo aplica cuando la vibración ocurre sin frenar ('vibra sin frenar') o se niega el freno ('no vibra al frenar').
    # NUNCA debe aplicar si el usuario afirma que vibra al frenar o que 'sin frenar no vibra'.
    afirma_freno = any(
        p in limpio for p in (
            "vibra al frenar", "tiembla al frenar", "al frenar vibra", "cuando frena vibra",
            "cuando freno vibra", "al pisar el pedal de freno", "al pisar el freno", "cuando frena",
            "al frenar"
        )
    ) and not any(p in limpio for p in ("no vibra al frenar", "al frenar no vibra", "al frenar no tiembla"))

    sin_frenar_no_vibra = bool(re.search(r"\bsin\s+frenar\s+(?:no\s+vibra|no\s+siente|no\s+pasa)\b", limpio))

    descarte_freno = False
    if not afirma_freno and not sin_frenar_no_vibra:
        descarte_freno = any(
            p in limpio for p in (
                "no vibra al frenar", "al frenar no tiembla", "no tiembla al frenar",
                "frenos no son", "frenos descartados", "vibra sin frenar", "tiembla sin frenar",
                "sin pisar el freno vibra"
            )
        )
    if descarte_freno:
        texto_filtrado = re.sub(r"\bfren(?:o|os|ar|ada)\b", " ", texto_filtrado, flags=re.IGNORECASE)
        texto_filtrado = re.sub(r"\bdisco(?:s)?\b", " ", texto_filtrado, flags=re.IGNORECASE)
        texto_filtrado = re.sub(r"\bpastilla(?:s)?\b", " ", texto_filtrado, flags=re.IGNORECASE)
        texto_filtrado += " llantas desbalanceadas desalineadas vibracion velocidad direccion"

    # 3. Descarte de encendido (bujías) cuando el síntoma es de suministro/presión de combustible
    descarte_bujias = any(
        p in limpio for p in (
            "cambie bujias", "cambié bujías", "cambie bujia", "cambié bujía",
            "bujias nuevas", "bujías nuevas", "cambie cables y bujias", "bujias descartadas",
            "bujias no son", "cambie filtro de aire pero sigue"
        )
    )
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

    # 4. Especialización: Vibración exclusiva al frenar (Alabeo / Deformación de discos de freno)
    vibracion_frenado = any(
        p in limpio for p in (
            "apenas piso el freno", "al pisar el freno", "piso el freno para", "vibra al frenar",
            "tiembla al frenar", "sacude al frenar", "zapatea al frenar", "pedal tiembla",
            "pedal del freno tiembla", "patea el pie", "pedal me patea", "sacudirse de lado a lado",
            "al frenar", "cuando frena", "cuando freno", "al pisar el pedal de freno"
        )
    ) and not any(p in limpio for p in ("no vibra al frenar", "al frenar no vibra", "al frenar no tiembla"))
    if (vibracion_frenado or sin_frenar_no_vibra) and any(f in limpio for f in ("freno", "frenar", "pedal")):
        texto_filtrado += " discos de freno alabeados desgastados deformados alabeo variacion espesor dtv reloj comparador vibracion pedal volante al frenar"

    return texto_filtrado
