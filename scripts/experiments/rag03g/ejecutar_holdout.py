"""Captura ciega para un auditor posterior; no crea ni puntúa el holdout.

El custodio proporciona manifiesto, 180 escenarios y oráculos congelados. Los
oráculos se verifican por hash pero este proceso no los interpreta ni ajusta.
"""

import argparse
import asyncio
import hashlib
import json
from pathlib import Path

from ejecutar import entorno


def cargar(manifest_path):
    m = json.loads(manifest_path.read_text(encoding="utf-8"))
    if (
        m.get("schema") != "carbot.holdout/1"
        or m.get("count") != 180
        or not m.get("custodian")
        or not m.get("frozen_at")
    ):
        raise ValueError("Manifiesto de custodia/congelación incompleto")
    for role in ("scenarios", "oracles"):
        p = (manifest_path.parent / m[role]["path"]).resolve()
        if not p.is_relative_to(manifest_path.parent.resolve()):
            raise ValueError("Ruta de holdout fuera de paquete")
        if hashlib.sha256(p.read_bytes()).hexdigest() != m[role]["sha256"]:
            raise ValueError("Hash de " + role + " no coincide")
    scenarios = json.loads(
        (manifest_path.parent / m["scenarios"]["path"]).read_text(encoding="utf-8")
    )
    if len(scenarios) != 180 or len({s["id"] for s in scenarios}) != 180:
        raise ValueError("Se requieren 180 escenarios únicos")
    return m, scenarios


async def ejecutar(scenarios, out):
    from src.core.conversacion.orquestador_conversacion import OrquestadorConversacion
    from src.core.conversacion.repositorio import InMemoryConversationRepository
    from src.core.gestor_diagnostico import GestorDiagnostico

    g = GestorDiagnostico()
    results = []
    for scenario in scenarios:
        repo = InMemoryConversationRepository()
        o = OrquestadorConversacion(repo)
        for n, text in enumerate(scenario["turns"], 1):
            r = await o.procesar_turno(scenario["id"], text, g)
            state = await repo.get_session(scenario["id"])
            results.append(
                dict(
                    id=scenario["id"],
                    turn=n,
                    input=text,
                    decision=r.get("decision"),
                    response=r.get("respuesta_texto"),
                    state=state.exportar_dict() if state else None,
                )
            )
    (out / "raw_outputs.json").write_text(
        json.dumps(results, ensure_ascii=False, indent=2, default=str), encoding="utf-8"
    )


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--manifest", type=Path, required=True)
    p.add_argument("--out", type=Path, required=True)
    args = p.parse_args()
    m, cases = cargar(args.manifest.resolve())
    out = args.out.resolve()
    out.mkdir(parents=True, exist_ok=False)
    entorno(out)
    asyncio.run(ejecutar(cases, out))
    (out / "custodia.json").write_text(json.dumps(m, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
