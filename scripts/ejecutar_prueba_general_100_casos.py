"""
Ejecución de Prueba General de CarBot con 100 Casos Reales (Fase 7).
Pipeline completo: ML Jerárquico + RAG Multiseñal + LLM Gemini / Fallback Degradado + Auto-interrogador.
Evalúa Grupo 1 (50 casos técnicos) y Grupo 2 (50 casos coloquiales).
"""

import json
import sys
import time
from pathlib import Path
from typing import Any, Dict, List

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "backend"))
sys.path.insert(0, str(BASE_DIR / "scripts"))

from datos_prueba_grupo1 import GRUPO_1_CASOS
from datos_prueba_grupo2 import GRUPO_2_CASOS
from machine_learning.models.taxonomia_sistemas import obtener_macro_sistema
from src.core.diagnostic_cache import diagnostico_cache
from src.core.gestor_diagnostico import GestorDiagnostico


def ejecutar_caso(
    gestor: GestorDiagnostico,
    gestor_degradado: GestorDiagnostico,
    caso: Dict[str, Any],
    grupo_nombre: str,
) -> Dict[str, Any]:
    caso_id = caso["id"]
    texto = caso["texto"]
    session_id = f"SESSION_{grupo_nombre}_{caso_id}_{int(time.time()*1000)}"

    t0 = time.perf_counter()
    resultado = gestor.procesar_consulta_texto(
        texto_usuario=texto,
        session_id=session_id,
        marca_modelo="Universal",
    )
    t_pipeline_ms = round((time.perf_counter() - t0) * 1000.0, 2)

    es_interactivo = bool(
        resultado.estado_sesion in ("esperando_autopregunta", "esperando_aclaracion_sintoma")
        or resultado.modo_diagnostico == "esperando_clarificacion"
        or resultado.tipo_consulta == "aclaracion"
    )

    predicciones = []
    if resultado.predicciones_ml:
        for p in resultado.predicciones_ml:
            predicciones.append({
                "falla": p.falla,
                "probabilidad": round(float(p.probabilidad), 4)
            })

    macro_sistema = obtener_macro_sistema(resultado.diagnostico_ml) if resultado.diagnostico_ml else "MOTOR"

    # Si se generó mensaje preliminar de cola de WhatsApp, resolver el reporte técnico completo con ML+RAG
    if resultado.respuesta_texto.startswith("⏳"):
        diagnostico_cache.limpiar()
        res_full = gestor_degradado.procesar_consulta_texto(
            texto_usuario=texto,
            session_id=f"FULL_{session_id}",
            marca_modelo="Universal",
        )
        reporte_completo = res_full.respuesta_texto
    else:
        reporte_completo = resultado.respuesta_texto

    registro = {
        "id": caso_id,
        "grupo": grupo_nombre,
        "subgrupo": caso.get("subgrupo", "tecnico"),
        "texto_usuario": texto,
        "macro_sistema": macro_sistema,
        "diagnostico_ml": resultado.diagnostico_ml,
        "confianza_ml": round(float(resultado.confianza_ml or 0.0), 4),
        "predicciones_ml": predicciones,
        "titulo_rag": resultado.titulo_manual or "Procedimiento Estándar OEM",
        "similitud_rag": round(float(resultado.similitud_rag or 0.0), 4),
        "modo_diagnostico": resultado.modo_diagnostico,
        "es_interactivo": es_interactivo,
        "estado_sesion": resultado.estado_sesion,
        "respuesta_inmediata_bot": resultado.respuesta_texto,
        "reporte_tecnico_completo": reporte_completo,
        "tiempo_total_ms": t_pipeline_ms,
    }

    # Si fue interactivo (auto-interrogador), procesar el segundo turno de respuesta
    if es_interactivo:
        t_turn2_0 = time.perf_counter()
        resp_aclaracion = gestor.procesar_consulta_texto(
            texto_usuario="1",  # Selecciona la opción 1 técnica sugerida
            session_id=session_id,
            marca_modelo="Universal",
        )
        if resp_aclaracion.respuesta_texto.startswith("⏳") or resp_aclaracion.estado_sesion in ("esperando_autopregunta", "esperando_aclaracion_sintoma"):
            diagnostico_cache.limpiar()
            resp_full2 = gestor_degradado.procesar_consulta_texto(
                texto_usuario=f"{texto}. Confirmación técnica: opción 1",
                session_id=f"FULL2_{session_id}",
                marca_modelo="Universal",
            )
            resp_final_texto = resp_full2.respuesta_texto
        else:
            resp_final_texto = resp_aclaracion.respuesta_texto

        t_turn2_ms = round((time.perf_counter() - t_turn2_0) * 1000.0, 2)
        registro["interaccion_turno2"] = {
            "entrada_usuario": "1",
            "diagnostico_final": resp_aclaracion.diagnostico_ml,
            "confianza_final": round(float(resp_aclaracion.confianza_ml or 0.0), 4),
            "modo_final": resp_aclaracion.modo_diagnostico,
            "respuesta_bot_final": resp_final_texto,
            "tiempo_turno2_ms": t_turn2_ms
        }

    return registro


def main():
    print("=" * 85)
    print("CARBOT — PRUEBA GENERAL INTEGRAL DEL SISTEMA COMPLETO (100 CASOS)")
    print("Flujo: Entrada Usuario -> Jerga/DTC -> ML Jerárquico -> RAG Multiseñal -> Gemini/Degradado")
    print("=" * 85)

    gestor = GestorDiagnostico()
    gestor_degradado = GestorDiagnostico()
    gestor_degradado.api_key = ""  # Desactiva cola para resolución inmediata del informe 3 secciones

    todos_los_resultados: List[Dict[str, Any]] = []

    # --- EJECUTAR GRUPO 1 (50 casos técnicos) ---
    print("\n>>> PROCESANDO 1ER GRUPO: 50 CASOS TÉCNICOS DE TALLER...")
    for idx, c in enumerate(GRUPO_1_CASOS, 1):
        reg = ejecutar_caso(gestor, gestor_degradado, c, "GRUPO_1_TECNICO")
        todos_los_resultados.append(reg)
        tipo_tag = "[PREGUNTA ACLARATORIA]" if reg["es_interactivo"] else "[DIAGNÓSTICO 3 SECC]"
        print(f"[{idx:02d}/50 G1] {reg['id']}: {reg['macro_sistema']:<18} | "
              f"ML: {reg['confianza_ml']*100:4.1f}% ({reg['diagnostico_ml'][:28]}...) | "
              f"RAG: {reg['similitud_rag']:4.2f} | {tipo_tag} | {reg['tiempo_total_ms']:5.1f}ms")

    # --- EJECUTAR GRUPO 2 (50 casos coloquiales) ---
    print("\n>>> PROCESANDO 2DO GRUPO: 50 CASOS COLOQUIALES DE TALLER...")
    for idx, c in enumerate(GRUPO_2_CASOS, 1):
        reg = ejecutar_caso(gestor, gestor_degradado, c, "GRUPO_2_COLOQUIAL")
        todos_los_resultados.append(reg)
        tipo_tag = "[PREGUNTA ACLARATORIA]" if reg["es_interactivo"] else "[DIAGNÓSTICO 3 SECC]"
        print(f"[{idx:02d}/50 G2] {reg['id']}: {reg['macro_sistema']:<18} | "
              f"ML: {reg['confianza_ml']*100:4.1f}% ({reg['diagnostico_ml'][:28]}...) | "
              f"RAG: {reg['similitud_rag']:4.2f} | {tipo_tag} | {reg['tiempo_total_ms']:5.1f}ms")

    # --- ESTADÍSTICAS GLOBALES ---
    total = len(todos_los_resultados)
    g1 = [r for r in todos_los_resultados if r["grupo"] == "GRUPO_1_TECNICO"]
    g2 = [r for r in todos_los_resultados if r["grupo"] == "GRUPO_2_COLOQUIAL"]

    interactivos_g1 = sum(1 for r in g1 if r["es_interactivo"])
    interactivos_g2 = sum(1 for r in g2 if r["es_interactivo"])
    directos_g1 = len(g1) - interactivos_g1
    directos_g2 = len(g2) - interactivos_g2

    tiempos = [r["tiempo_total_ms"] for r in todos_los_resultados]
    tiempo_promedio = sum(tiempos) / total

    sistemas_conteo = {}
    for r in todos_los_resultados:
        sistemas_conteo[r["macro_sistema"]] = sistemas_conteo.get(r["macro_sistema"], 0) + 1

    resumen = {
        "total_casos_evaluados": total,
        "distribucion_grupos": {
            "grupo_1_tecnico": {
                "total": len(g1),
                "diagnosticos_directos": directos_g1,
                "preguntas_aclaratorias": interactivos_g1,
                "confianza_ml_promedio": round(sum(r["confianza_ml"] for r in g1) / len(g1), 4),
            },
            "grupo_2_coloquial": {
                "total": len(g2),
                "diagnosticos_directos": directos_g2,
                "preguntas_aclaratorias": interactivos_g2,
                "confianza_ml_promedio": round(sum(r["confianza_ml"] for r in g2) / len(g2), 4),
            }
        },
        "distribucion_macro_sistemas": sistemas_conteo,
        "latencia_promedio_pipeline_ms": round(tiempo_promedio, 2),
        "casos_completos": todos_los_resultados
    }

    out_dir = BASE_DIR / "docs" / "graficas"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "reporte_prueba_general_100_casos.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(resumen, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 85)
    print("RESUMEN DE LA PRUEBA GENERAL DE 100 CASOS:")
    print(f"• Total Casos Evaluados: {total}")
    print(f"• Grupo 1 (Técnicos): {len(g1)} casos | Directos: {directos_g1} | Aclaratorios: {interactivos_g1} | Confianza ML: {resumen['distribucion_grupos']['grupo_1_tecnico']['confianza_ml_promedio']*100:.1f}%")
    print(f"• Grupo 2 (Coloquiales): {len(g2)} casos | Directos: {directos_g2} | Aclaratorios: {interactivos_g2} | Confianza ML: {resumen['distribucion_grupos']['grupo_2_coloquial']['confianza_ml_promedio']*100:.1f}%")
    print(f"• Latencia Promedio del Pipeline: {tiempo_promedio:.2f} ms")
    print("• Distribución por Macro-Sistemas:")
    for sist, cnt in sorted(sistemas_conteo.items(), key=lambda x: x[1], reverse=True):
        print(f"   - {sist:<22}: {cnt:2d} casos ({cnt/total*100:4.1f}%)")
    print(f"\nArchivo guardado: {out_file}")
    print("=" * 85)


if __name__ == "__main__":
    main()
