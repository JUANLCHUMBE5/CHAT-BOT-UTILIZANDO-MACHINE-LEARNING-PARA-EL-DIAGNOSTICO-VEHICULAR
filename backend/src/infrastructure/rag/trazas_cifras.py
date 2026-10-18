"""Selección inequívoca de parámetro y página; sin heurística de primera cifra."""

import re


def seleccionar_cifra(consulta, candidato, normalizar, parsear):
    cifras = candidato.get("cifras_trazadas")
    if not cifras:
        return None, "No hay cifras estructuradas con componente/condición"
    q = normalizar(consulta)

    def tokens(s):
        return {
            w.rstrip("s")
            for w in re.findall(r"[a-z0-9]+", normalizar(s))
            if len(w) > 2
            and w not in {"del", "los", "las", "para", "con", "torque", "apriete", "montaje", "fijacion"}
        }

    scored = []
    unidades = None
    if re.search(r"\b(?:torque|apriete|par)\b", q):
        unidades = {"nm", "lbft", "kgfm"}
    elif re.search(r"\b(?:presion|compresion)\b", q):
        unidades = {"bar", "psi", "kpa", "mpa"}
    elif re.search(r"\b(?:alabeo|espesor|holgura|tolerancia)\b", q):
        unidades = {"mm", "um", "micras"}
    for c in cifras:
        if not all(c.get(k) for k in ("parametro", "cifra", "unidad", "pagina", "condicion")):
            continue
        desc = normalizar(c["parametro"] + " " + c["condicion"])
        unidad = re.sub(r"[^a-z]", "", normalizar(c["unidad"]))
        if "tiempo" in normalizar(c["parametro"]) and unidad not in {"us", "ms", "s", "segundos"}:
            continue
        if unidades and unidad not in unidades:
            continue
        # No extrapolar entre variantes ni condiciones de medida explícitas.
        if any(
            w in q and w not in desc
            for w in ("aluminio", "plastico", "superior", "inferior", "sonata", "elantra", "frio", "caliente")
        ):
            continue
        rank = len(tokens(c["parametro"]) & tokens(q))
        if rank >= 2:
            scored.append((rank, c))
    scored.sort(key=lambda x: -x[0])
    if not scored or (len(scored) > 1 and scored[0][0] == scored[1][0]):
        return None, "Componente/parámetro/condición ambiguos: se requiere identificación exacta"
    c = scored[0][1]
    pages = candidato.get("paginas") or candidato.get("rango_paginas") or candidato.get("pagina")
    ok, allowed, _ = parsear(pages)
    cp_ok, actual, _ = parsear(c["pagina"])
    if not ok or not cp_ok or not set(actual).issubset(allowed):
        return None, "Página de la cifra no amparada por las páginas del documento"
    return c, "Cifra enlazada al parámetro, condición y página exactos"
