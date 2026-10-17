"""Registro de evidencia empírica de acciones de taller, desacoplado de inferencias de salud."""

from __future__ import annotations

import re
from typing import Any

from src.core.conversacion.models import ConversationState, FactState, FactType


def normalizar(texto: str) -> str:
    cadena = texto.lower()
    for o, d in (("á", "a"), ("é", "e"), ("í", "i"), ("ó", "o"), ("ú", "u")):
        cadena = cadena.replace(o, d)
    return cadena


def accion_afirmada(clausula: str, accion: str, patron: str) -> bool:
    for m in re.finditer(patron, clausula):
        pieza = m.group(0)
        if not pieza:
            continue
        for match in re.finditer(accion, clausula):
            anterior = clausula[max(0, match.start() - 48):match.start()]
            if not re.search(r"\b(?:no|nunca|sin|pendiente|falta)\b(?:\s+\w+){0,6}\s*$", anterior):
                return True
    return False


def descarte_afirmado(texto: str, componente: str) -> bool:
    return accion_afirmada(texto, r"\b(?:descarte|descartado|descartada)\b", componente)


def registrar_acciones_taller(estado: ConversationState, texto_usuario: str) -> list[dict[str, Any]]:
    """Persistencia de la acción declarada, separada de su resultado diagnóstico."""
    hechos_extraidos: list[dict[str, Any]] = []
    texto_norm = normalizar(texto_usuario)
    # Registrar acciones, sin deducir que una pieza nueva o inspeccionada funciona bien.
    piezas = ("bujias", "bobinas?", "bomba", "filtro", "termostato", "pastillas", "aceite",
              "intercooler", "fusible", "presion", "compresion", "bateria", "alternador", "arrancador")
    for pieza in piezas:
        patron = rf"\b{pieza}\b"
        canon = "bujías" if "buj" in pieza else ("bobinas" if "bobin" in pieza else pieza)
        acciones = (
            ("reemplazado", r"\b(?:cambie|cambiamos|cambiados?|cambiadas?|nuevos?|nuevas?)\b", "antecedente"),
            ("probado", r"\b(?:revise|probe|intercambie|inspeccione|medi)\b", "prueba_realizada"),
        )
        for clausula in re.split(r"[.;!?]|\bpero\b", texto_norm):
            observacion = r"\b(?:tenia|tiene|presenta|observe|vi)\b"
            if (re.search(r"\b(?:aceite|humedad|residuos?|corrosion|oxido)\b", clausula)
                    and not re.search(r"\b(?:quizas|podria|supongo|creo)\b", clausula)
                    and accion_afirmada(clausula, observacion, patron)):
                hecho = estado.registrar_hecho(
                    f"observacion_{canon}", clausula.strip(),
                    categoria="observacion", texto_crudo=texto_usuario, tipo=FactType.CONDICION,
                )
                hechos_extraidos.append(hecho.to_dict())
            if re.search(patron, clausula) and re.search(
                r"\b(?:no|nunca|sin)\b(?:\s+\w+){0,4}\s+"
                r"(?:probe|revise|medi|comprobe|inspeccione|revisar|medir|comprobar|inspeccionar)\b", clausula,
            ):
                hecho = estado.registrar_hecho(
                    f"no_comprobado_{canon}", f"{canon}: comprobación pendiente",
                    categoria="inspeccion_pendiente", estado=FactState.NO_REVISADO,
                    texto_crudo=texto_usuario, tipo=FactType.CONDICION,
                )
                hechos_extraidos.append(hecho.to_dict())
        for nombre, accion, categoria in acciones:
            if accion_afirmada(texto_norm, accion, patron):
                valor_hecho = (
                    f"{canon} probado/descartado"
                    if nombre == "probado" and "bobin" in pieza
                    else f"{canon} {nombre}(a)"
                )
                hecho = estado.registrar_hecho(
                    f"{nombre}_{canon}", valor_hecho,
                    categoria=categoria, texto_crudo=texto_usuario, tipo=FactType.CONDICION,
                )
                hechos_extraidos.append(hecho.to_dict())
        if descarte_afirmado(texto_norm, patron):
            hecho = estado.registrar_hecho(
                f"descartado_{canon}", f"{canon} descartado explícitamente por el mecánico",
                categoria="componente_descartado", estado=FactState.DESCARTADO,
                texto_crudo=texto_usuario, tipo=FactType.CONDICION,
            )
            hechos_extraidos.append(hecho.to_dict())

    return hechos_extraidos
