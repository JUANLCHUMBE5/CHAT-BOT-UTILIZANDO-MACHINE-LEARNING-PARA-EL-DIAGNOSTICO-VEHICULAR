"""Reintenta solo casos SIMULACION_POST que terminaron en cola de Gemini.

Respeta lotes de hasta diez solicitudes por ejecución; no modifica modelos,
datasets, RAG ni registros oficiales.
"""

from __future__ import annotations

import argparse
import csv
import importlib.util
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from src.core.gestor_diagnostico import GestorDiagnostico

SALIDA = ROOT / "docs" / "simulaciones_tecnicas" / "simulacion_post_202609"
DETALLE = SALIDA / "SIMULACION_POST_30_CASOS_DETALLE.csv"


def cargar_modulo_principal():
    ruta = Path(__file__).with_name("ejecutar_simulacion_post_local.py")
    spec = importlib.util.spec_from_file_location("sim_post", ruta)
    modulo = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(modulo)
    return modulo


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--limite", type=int, default=10)
    args = parser.parse_args()
    with DETALLE.open(encoding="utf-8-sig", newline="") as archivo:
        filas = list(csv.DictReader(archivo))
        campos = list(filas[0])
    pendientes = [fila for fila in filas if fila.get("modo_diagnostico") == "en_cola_gemini"][: args.limite]
    if not pendientes:
        print("No hay casos en cola para reintentar.")
        return
    gestor = GestorDiagnostico()
    gestor._registrar_en_tracker = lambda **_: None
    for fila in pendientes:
        inicio = time.perf_counter()
        resultado = gestor.procesar_consulta_texto(
            fila["sintoma_ingresado"], placa=f"RETRY-{fila['id_caso'][-3:]}",
            marca_modelo="Vehículo de simulación", session_id=f"retry-{fila['id_caso']}",
            proveedor="simulacion_local",
        )
        fila.update({
            "diagnostico_principal_carbot": resultado.diagnostico_ml,
            "alternativas_diagnosticas_carbot": json.dumps(
                [item.model_dump() for item in resultado.predicciones_ml], ensure_ascii=False
            ),
            "informacion_generada_carbot": resultado.respuesta_texto,
            "contexto_rag": resultado.contexto_manual,
            "titulo_manual": resultado.titulo_manual,
            "confianza_ml": resultado.confianza_ml,
            "tiempo_real_ms": round((time.perf_counter() - inicio) * 1000, 2),
            "tiempo_ml_ms": resultado.tiempo_ml_ms,
            "tiempo_rag_ms": resultado.tiempo_rag_ms,
            "tiempo_llm_ms": resultado.tiempo_llm_ms,
            "tiempo_total_reportado_ms": resultado.tiempo_total_ms,
            "modo_diagnostico": resultado.modo_diagnostico,
            "estado_ejecucion": "EJECUTADO" if resultado.modo_diagnostico != "en_cola_gemini" else "EN_COLA_GEMINI",
            "error": "",
        })
        print(f"{fila['id_caso']}: {fila['modo_diagnostico']}")
    modulo = cargar_modulo_principal()
    for fila in filas:
        if fila.get("estado_ejecucion") == "EJECUTADO":
            fila["coincide_principal_con_referencia"] = (
                modulo.normalizar(fila.get("diagnostico_principal_carbot", ""))
                == modulo.normalizar(fila["diagnostico_referencia_esperado_simulado"])
            )
    prediccion, completitud, eficiencia = modulo.resumen_por_grupo(filas)
    modulo.escribir_csv(DETALLE.name, filas, campos)
    modulo.escribir_csv("FICHA_1_PREDICCION_PPCF.csv", prediccion, list(prediccion[0]))
    modulo.escribir_csv("FICHA_2_CONTROL_INFORMACION_PRDC_PENDIENTE.csv", completitud, list(completitud[0]))
    modulo.escribir_csv("FICHA_3_EFICIENCIA_TPRD.csv", eficiencia, list(eficiencia[0]))
    modulo.escribir_reporte(filas, prediccion, eficiencia)


if __name__ == "__main__":
    main()
