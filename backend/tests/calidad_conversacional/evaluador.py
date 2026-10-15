"""Evaluador reproducible por capas para conversaciones técnicas largas."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import re
import statistics
import time
import unicodedata
from dataclasses import dataclass
from difflib import SequenceMatcher
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[2]
os.environ.setdefault("DATABASE_ENABLED", "false")
os.environ["GEMINI_API_KEY"] = ""
os.environ["GROQ_API_KEY"] = ""
os.environ["GROQ_CHAT_ENABLED"] = "false"
ARTEFACTOS_ML = ROOT.parent / "machine_learning"
os.environ["ML_ROOT"] = str(ARTEFACTOS_ML)

from src.core.conversacion.orquestador_conversacion import OrquestadorConversacion  # noqa: E402
from src.core.conversacion.repositorio import InMemoryConversationRepository  # noqa: E402
from src.core.conversacion.sintetizador_consulta import SintetizadorConsulta  # noqa: E402
from tests.calidad_conversacional.casos_congelados import (  # noqa: E402
    CASOS_CONGELADOS,
    validar_casos_congelados,
)


def normalizar(texto: Any) -> str:
    base = unicodedata.normalize("NFKD", str(texto).casefold())
    sin_tildes = "".join(c for c in base if not unicodedata.combining(c))
    return re.sub(r"\s+", " ", sin_tildes).strip()


def _tokens(texto: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", normalizar(texto)))


def equivalencia_semantica(a: str, b: str) -> float:
    ta, tb = _tokens(a), _tokens(b)
    if not ta or not tb:
        return 0.0
    jaccard = len(ta & tb) / len(ta | tb)
    secuencia = SequenceMatcher(None, normalizar(a), normalizar(b)).ratio()
    return max(jaccard, secuencia)


def extraer_preguntas(texto: str) -> list[str]:
    return [p.strip() for p in re.findall(r"¿([^?]+)\?", texto or "") if p.strip()]


def blob_estructurado(estado: Any) -> str:
    """Serializa memoria estructurada sin historial crudo ni trazas."""
    data = estado.exportar_dict(incluir_trazabilidad=False)
    for campo in ("historial_mensajes_usuario", "respuestas_obtenidas", "preguntas_realizadas"):
        data.pop(campo, None)
    return normalizar(json.dumps(data, ensure_ascii=False, sort_keys=True))


def medir_mediciones(estado: Any, esperadas: list[tuple[float, str]]) -> tuple[int, list[dict[str, Any]]]:
    unicas: dict[tuple[float, str], dict[str, Any]] = {}
    for med in estado.measurements.values():
        if not isinstance(med, dict):
            continue
        clave = (float(med.get("valor", float("nan"))), normalizar(med.get("unidad", "")))
        unicas[clave] = med
    detalles = []
    aciertos = 0
    for valor, unidad in esperadas:
        encontrada = any(abs(v - valor) < 1e-9 and u == normalizar(unidad) for v, u in unicas)
        aciertos += int(encontrada)
        detalles.append({"valor": valor, "unidad": unidad, "retenida": encontrada})
    return aciertos, detalles


@dataclass
class Contadores:
    hechos_ok: int = 0
    hechos_total: int = 0
    mediciones_ok: int = 0
    mediciones_total: int = 0
    vehiculo_ok: int = 0
    vehiculo_total: int = 0
    contexto_ok: int = 0
    contexto_total: int = 0
    confirmaciones_indebidas: int = 0
    preguntas: int = 0
    preguntas_repetidas: int = 0
    respuestas_comparables: int = 0
    respuestas_redundantes: int = 0
    bucles: int = 0


async def evaluar_casos() -> dict[str, Any]:
    # La carga del SVM/FAISS es deliberadamente tardía para que las pruebas de la
    # metodología no dependan de artefactos binarios ni paguen su coste de inicio.
    from src.config import settings
    from src.core.gestor_diagnostico import GestorDiagnostico

    # `.env` se carga durante la importación de configuración. Sobrescribimos el
    # objeto ya construido para garantizar que este runner nunca llame proveedores.
    settings.gemini_api_key = ""
    settings.groq_api_key = ""
    settings.groq_chat_enabled = False

    validar_casos_congelados()
    gestor = GestorDiagnostico()
    acumulado = Contadores()
    latencias: list[float] = []
    tamanios_contexto: list[int] = []
    resultados = []

    for caso in CASOS_CONGELADOS:
        repo = InMemoryConversationRepository()
        orquestador = OrquestadorConversacion(repositorio=repo)
        respuestas: list[str] = []
        preguntas_previas: list[str] = []
        transiciones: list[dict[str, Any]] = []
        decisiones_turno: list[dict[str, Any]] = []
        repeticiones = 0
        bucles = 0
        preguntas_repetidas_detalle: list[str] = []

        for numero_turno, mensaje in enumerate(caso["turnos"], start=1):
            inicio = time.perf_counter()
            resultado = await orquestador.procesar_turno(caso["id"], mensaje, gestor)
            latencias.append((time.perf_counter() - inicio) * 1000)
            respuesta = str(resultado.get("respuesta_texto") or "")
            transiciones.append(
                {
                    "turno": numero_turno,
                    "decision": resultado.get("decision_transicion"),
                    "motivo": resultado.get("motivo_transicion"),
                }
            )
            decisiones_turno.append(
                {
                    "turno": numero_turno,
                    "decision": resultado.get("decision"),
                    "motivo": resultado.get("motivo_decision"),
                    "nueva_evidencia": bool(resultado.get("nueva_evidencia")),
                }
            )
            respuestas.append(respuesta)
            preguntas_turno = extraer_preguntas(respuesta)
            repetidas_turno = 0
            for pregunta in preguntas_turno:
                if any(equivalencia_semantica(pregunta, previa) >= 0.84 for previa in preguntas_previas):
                    repeticiones += 1
                    repetidas_turno += 1
                    preguntas_repetidas_detalle.append({"turno": numero_turno, "pregunta": pregunta})
                preguntas_previas.append(pregunta)
            if repetidas_turno and len(preguntas_turno) == repetidas_turno:
                bucles += 1

        estado = await repo.get_session(caso["id"])
        assert estado is not None
        estructurado = blob_estructurado(estado)
        contexto = SintetizadorConsulta.sintetizar(estado)
        contexto_norm = normalizar(contexto)
        tamanios_contexto.append(len(contexto))

        vehiculo_detalle = {}
        for campo, esperado in caso["vehiculo"].items():
            actual = getattr(estado, campo)
            ok = normalizar(esperado) in normalizar(actual)
            vehiculo_detalle[campo] = {"esperado": esperado, "actual": actual, "retenido": ok}
            acumulado.vehiculo_ok += int(ok)
            acumulado.vehiculo_total += 1

        hechos_detalle = {}
        for esperado in caso["hechos"]:
            ok = normalizar(esperado) in estructurado
            hechos_detalle[esperado] = ok
            acumulado.hechos_ok += int(ok)
            acumulado.hechos_total += 1

        mediciones_ok, mediciones_detalle = medir_mediciones(estado, caso["mediciones"])
        acumulado.mediciones_ok += mediciones_ok
        acumulado.mediciones_total += len(caso["mediciones"])

        contexto_detalle = {}
        for esperado in caso["contexto"]:
            ok = normalizar(esperado) in contexto_norm
            contexto_detalle[esperado] = ok
            acumulado.contexto_ok += int(ok)
            acumulado.contexto_total += 1

        prohibidos = caso.get("prohibidos_contexto", []) + caso.get("no_confirmar", [])
        confirmaciones = [p for p in prohibidos if normalizar(p) in contexto_norm]
        acumulado.confirmaciones_indebidas += len(confirmaciones)

        redundantes_detalle = [
            {
                "turnos": [indice, indice + 1],
                "similitud": round(equivalencia_semantica(anterior, actual), 4),
                "respuesta": actual,
            }
            for indice, (anterior, actual) in enumerate(zip(respuestas, respuestas[1:]), start=1)
            if equivalencia_semantica(anterior, actual) >= 0.92
        ]
        redundantes = len(redundantes_detalle)
        comparables = max(0, len(respuestas) - 1)
        acumulado.preguntas += len(preguntas_previas)
        acumulado.preguntas_repetidas += repeticiones
        acumulado.respuestas_comparables += comparables
        acumulado.respuestas_redundantes += redundantes
        acumulado.bucles += bucles

        resultados.append(
            {
                "id": caso["id"],
                "turnos": len(caso["turnos"]),
                "vehiculo": vehiculo_detalle,
                "hechos": hechos_detalle,
                "mediciones": mediciones_detalle,
                "contexto_llm": contexto_detalle,
                "contexto_llm_caracteres": len(contexto),
                "preguntas_emitidas": len(preguntas_previas),
                "preguntas_repetidas": repeticiones,
                "preguntas_repetidas_detalle": preguntas_repetidas_detalle,
                "respuestas_redundantes": redundantes,
                "respuestas_redundantes_detalle": redundantes_detalle,
                "bucles": bucles,
                "confirmaciones_indebidas": confirmaciones,
                "transiciones": transiciones,
                "decisiones_turno": decisiones_turno,
                "consulta_consolidada": contexto,
            }
        )

    def tasa(ok: int, total: int) -> dict[str, Any]:
        return {"numerador": ok, "denominador": total, "porcentaje": round(100 * ok / total, 2) if total else 0.0}

    latencias_ord = sorted(latencias)
    indice_p95 = min(len(latencias_ord) - 1, int(0.95 * len(latencias_ord)))
    return {
        "naturaleza": "evaluacion_sintetica_de_regresion_no_oficial",
        "total_casos": len(resultados),
        "total_turnos": sum(c["turnos"] for c in resultados),
        "retencion_hechos_estructurados": tasa(acumulado.hechos_ok, acumulado.hechos_total),
        "retencion_mediciones_exactas": tasa(acumulado.mediciones_ok, acumulado.mediciones_total),
        "consistencia_vehiculo_combustible": tasa(acumulado.vehiculo_ok, acumulado.vehiculo_total),
        "cobertura_contexto_llm": tasa(acumulado.contexto_ok, acumulado.contexto_total),
        "preguntas_repetidas": tasa(acumulado.preguntas_repetidas, acumulado.preguntas),
        "respuestas_redundantes": tasa(acumulado.respuestas_redundantes, acumulado.respuestas_comparables),
        "bucles_detectados": acumulado.bucles,
        "confirmaciones_indebidas": acumulado.confirmaciones_indebidas,
        "latencia_ms": {
            "muestras": len(latencias),
            "promedio": round(statistics.fmean(latencias), 2),
            "p50": round(statistics.median(latencias), 2),
            "p95": round(latencias_ord[indice_p95], 2),
        },
        "contexto_llm_caracteres": {
            "muestras": len(tamanios_contexto),
            "promedio": round(statistics.fmean(tamanios_contexto), 2),
            "maximo": max(tamanios_contexto),
        },
        "casos": resultados,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--compacto", action="store_true")
    parser.add_argument("--resumen", action="store_true", help="Omite evidencia detallada por caso")
    args = parser.parse_args()
    resultado = asyncio.run(evaluar_casos())
    if args.resumen:
        resultado = {k: v for k, v in resultado.items() if k != "casos"}
    print(json.dumps(resultado, ensure_ascii=False, indent=None if args.compacto else 2))


if __name__ == "__main__":
    main()
