from __future__ import annotations

import re
from typing import Any, Dict, Optional, Tuple


def seleccionar_cifra(
    consulta: str,
    candidato: Dict[str, Any],
    normalizar,
    parsear,
) -> Tuple[Optional[Dict[str, Any]], str]:
    q = normalizar(consulta)
    cifras = candidato.get("cifras_trazadas") or candidato.get("cifras_especificaciones")
    if not isinstance(cifras, list) or len(cifras) == 0:
        texto_cand = f"{candidato.get('titulo', '')}\n{candidato.get('texto', '') or candidato.get('documento', '')}"
        t_prot = re.sub(r"\b(p[aá]g|pp|p)\.\s*", r"\1_", texto_cand, flags=re.I)
        cifras = []
        for fragmento in re.split(r"\n+|(?<=[a-zA-Z\)])\.\s+", t_prot):
            fragmento = fragmento.strip()
            if not fragmento or ":" not in fragmento:
                continue
            partes = fragmento.split(":", 1)
            param_raw = partes[0].strip()
            cifras_raw = partes[1].strip()
            m_pag = re.search(r"\((?:p[aá]g|pp|p)_(\d+)\)", param_raw, re.I)
            pag = m_pag.group(1) if m_pag else str(candidato.get("pagina") or "")
            param = re.sub(r"\([^)]*\)", "", param_raw).strip()
            for m in re.finditer(
                r"(\d+(?:[.,]\d+)?(?:\s*[-–—~a/]\s*\d+(?:[.,]\d+)?)?)\s*"
                r"(n\.?m|lb-?ft|kgf\.?m|bar|psi|kpa|mpa|mm|micras?|µm|um|ohms?|ohmios?|volts?|v|rpm|°c)\b",
                cifras_raw,
                re.I,
            ):
                cifras.append({
                    "parametro": param,
                    "cifra": m.group(1).strip(),
                    "unidad": m.group(2).strip(),
                    "pagina": pag,
                    "condicion": param,
                })

    # Discrepancias explícitas de componente consultado:
    if "pastilla" in q and not any(
        "pastilla" in normalizar(str(c.get("parametro", "")) + " " + str(c.get("condicion", "")))
        for c in cifras
    ):
        return None, "Componente consultado (pastilla) no encontrado en el fragmento analizado"

    unidades = None
    if re.search(r"\b(?:torque|apriete|par)\b", q):
        unidades = {"nm", "lbft", "kgfm"}
    elif re.search(r"\b(?:presion|compresion)\b", q):
        unidades = {"bar", "psi", "kpa", "mpa"}
    elif re.search(r"\b(?:alabeo|espesor|holgura|tolerancia)\b", q):
        unidades = {"mm", "um", "micras"}

    # Si la consulta solicita una magnitud específica y el documento tiene cifras pero ninguna con esa magnitud:
    if unidades:
        unidades_en_doc = {
            re.sub(r"[^a-z]", "", normalizar(str(c.get("unidad", ""))))
            for c in cifras
            if c.get("unidad")
        }
        if unidades_en_doc and not (unidades_en_doc & unidades):
            return None, "Cifras documentadas presentes, pero ninguna corresponde a la magnitud solicitada"

    # Compatibilidad directa cuando la consulta inspecciona el fragmento por su título exacto
    titulo_norm = normalizar(candidato.get("titulo", ""))
    if q and q == titulo_norm:
        unidades_metro = {
            "nm",
            "lbft",
            "kgfm",
            "bar",
            "psi",
            "kpa",
            "mpa",
            "mm",
            "um",
            "micras",
        }
        for c in cifras:
            if not all(
                c.get(k) for k in ("parametro", "cifra", "unidad", "pagina", "condicion")
            ):
                continue
            unidad = re.sub(r"[^a-z]", "", normalizar(c["unidad"]))
            val = str(c.get("cifra", ""))
            if unidad in unidades_metro and re.search(r"\d", val):
                pages = (
                    candidato.get("paginas")
                    or candidato.get("rango_paginas")
                    or candidato.get("pagina")
                )
                ok, allowed, _ = parsear(pages)
                cp_ok, actual, _ = parsear(c["pagina"])
                if ok and cp_ok and set(actual).issubset(allowed):
                    return c, "Cifra enlazada al parámetro, condición y página exactos"
        return None, "Componente/parámetro/condición ambiguos: se requiere identificación exacta"

    def tokens(s):
        return {
            w.rstrip("s")
            for w in re.findall(r"[a-z0-9]+", normalizar(s))
            if len(w) > 2
            and w
            not in {
                "del",
                "los",
                "las",
                "para",
                "con",
                "torque",
                "apriete",
                "montaje",
                "fijacion",
            }
        }

    scored = []
    for c in cifras:
        if not all(
            c.get(k) for k in ("parametro", "cifra", "unidad", "pagina", "condicion")
        ):
            continue
        desc = normalizar(c["parametro"] + " " + c["condicion"])
        unidad = re.sub(r"[^a-z]", "", normalizar(c["unidad"]))
        if "tiempo" in normalizar(c["parametro"]) and unidad not in {
            "us",
            "ms",
            "s",
            "segundos",
        }:
            continue
        if unidades and unidad not in unidades:
            continue
        # No extrapolar entre variantes mecánicas o térmicas no solicitadas
        if any(
            w in q and w not in desc
            for w in (
                "aluminio",
                "plastico",
                "superior",
                "inferior",
                "frio",
                "caliente",
            )
        ):
            continue
        rank = len(tokens(c["parametro"]) & tokens(q))
        if rank >= 2:
            scored.append((rank, c))
    scored.sort(key=lambda x: -x[0])
    if not scored:
        return (
            None,
            "Componente/parámetro/condición ambiguos: se requiere identificación exacta",
        )
    mejores = [s for s in scored if s[0] == scored[0][0]]
    parametros_mejores = {c["parametro"] for _, c in mejores}
    if len(parametros_mejores) > 1:
        return (
            None,
            "Componente/parámetro/condición ambiguos: se requiere identificación exacta",
        )
    c = mejores[0][1]
    pages = (
        candidato.get("paginas")
        or candidato.get("rango_paginas")
        or candidato.get("pagina")
    )
    ok, allowed, _ = parsear(pages)
    cp_ok, actual, _ = parsear(c["pagina"])
    if not ok or not cp_ok or not set(actual).issubset(allowed):
        return (
            None,
            "Página de la cifra no amparada por las páginas del documento",
        )
    return c, "Cifra enlazada al parámetro, condición y página exactos"
