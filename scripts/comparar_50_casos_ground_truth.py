"""
Comparación Científica de los 50 Casos de Taller contra el Ground Truth Establecido.
Auditoría estricta sin modificación ni reentrenamiento de CarBot (Fase 7).
"""

import json
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))

from scripts.ground_truth_50_casos_data import GROUND_TRUTH_50


def auditar_50_casos():
    reporte_path = BASE_DIR / "docs" / "graficas" / "reporte_prueba_general_100_casos.json"
    if not reporte_path.exists():
        print(f"Error: no existe el archivo {reporte_path}")
        sys.exit(1)

    with open(reporte_path, "r", encoding="utf-8") as f:
        data_rep = json.load(f)

    casos_rep = {c["id"]: c for c in data_rep["casos_completos"] if c["grupo"] == "GRUPO_1_TECNICO"}

    resultados_auditoria = []

    conteo_top1_ml_estricto = 0
    conteo_top3_ml_acierto = 0

    conteo_e2e_estricto = 0
    conteo_e2e_diferencial = 0
    conteo_e2e_incorrecto = 0

    conteo_macro_correcto = 0
    conteo_auto_interrogador_efectivo = 0
    total_auto_interrogador_requerido = 0
    conteo_interrogador_sobreactivado = 0

    conteo_respaldo_doc_si = 0
    conteo_respaldo_doc_parcial = 0
    conteo_respaldo_doc_no = 0

    for gt in GROUND_TRUTH_50:
        cid = gt["id"]
        c_rep = casos_rep[cid]

        diag_ml_top1 = c_rep["diagnostico_ml"]
        conf_ml_top1 = c_rep["confianza_ml"]
        preds = c_rep.get("predicciones_ml", [])

        top1_falla = preds[0]["falla"] if len(preds) > 0 else diag_ml_top1
        top2_falla = preds[1]["falla"] if len(preds) > 1 else "Ninguno"
        top3_falla = preds[2]["falla"] if len(preds) > 2 else "Ninguno"

        # Diagnóstico final E2E (si fue interactivo, el resultado de turno 2)
        if c_rep["es_interactivo"] and "interaccion_turno2" in c_rep:
            diag_final = c_rep["interaccion_turno2"]["diagnostico_final"]
        else:
            diag_final = diag_ml_top1

        reporte_texto = c_rep.get("reporte_tecnico_completo", "") or c_rep.get("respuesta_inmediata_bot", "")

        # 1. Macro-Sistema
        macro_esperado = gt["macro_sistema"]
        macro_predicho = c_rep["macro_sistema"]
        macro_ok = (macro_esperado == macro_predicho)
        if macro_ok:
            conteo_macro_correcto += 1

        # 2. Evaluación ML pura (Top-1 y Top-3)
        diag_top1_low = top1_falla.lower()
        top1_ml_match = any(k.lower() in diag_top1_low for k in gt["claves_estrictas"])
        if top1_ml_match:
            conteo_top1_ml_estricto += 1

        top3_ml_match = any(
            any(k.lower() in p["falla"].lower() for k in gt["claves_estrictas"] + gt["claves_diferenciales"])
            for p in preds[:3]
        )
        if top3_ml_match:
            conteo_top3_ml_acierto += 1

        # 3. Diagnóstico Final E2E: Distinción estricta vs diferencial
        diag_final_low = diag_final.lower()
        reporte_low = reporte_texto.lower()

        # Estricto: El diagnóstico final primario apunta directamente a la falla esperada
        es_estricto_final = any(k.lower() in diag_final_low for k in gt["claves_estrictas"])

        # Diferencial: Si no es estricto en el diagnóstico primario, pero está presente en Top-3 ML
        # o en el desglose diferencial del reporte
        es_diferencial_reporte = any(
            k.lower() in reporte_low for k in gt["claves_estrictas"] + gt["claves_diferenciales"]
        )
        es_diferencial_valido = top3_ml_match or es_diferencial_reporte

        if es_estricto_final:
            clasificacion_e2e = "CORRECTO ESTRICTO"
            conteo_e2e_estricto += 1
        elif es_diferencial_valido and "fuera del alcance" not in diag_final_low:
            clasificacion_e2e = "DIFERENCIAL ACEPTABLE"
            conteo_e2e_diferencial += 1
        else:
            clasificacion_e2e = "INCORRECTO"
            conteo_e2e_incorrecto += 1

        # 4. Auto-interrogador
        req_inter = gt["requiere_auto_interrogador"]
        activo_inter = c_rep["es_interactivo"]

        if req_inter:
            total_auto_interrogador_requerido += 1
            if activo_inter:
                inter_status = "SÍ (ACTIVACIÓN APROPIADA)"
                conteo_auto_interrogador_efectivo += 1
            else:
                inter_status = "NO (NO ACTIVADO CUANDO DEBÍA)"
        else:
            if activo_inter:
                inter_status = "ACTIVACIÓN PREVENTIVA (NO REQUERIDA)"
                conteo_interrogador_sobreactivado += 1
            else:
                inter_status = "NO APLICABA (FLUJO DIRECTO CORRECTO)"

        # 5. Evidencia RAG y respaldo documental
        titulo_rag = c_rep.get("titulo_rag", "")
        similitud_rag = c_rep.get("similitud_rag", 0.0)

        valores_esperados = gt["valores_tolerancias_esperadas"]
        if not valores_esperados:
            respaldo_doc = "SÍ (PROCEDIMIENTO CUALITATIVO VALIDADO)"
            conteo_respaldo_doc_si += 1
        else:
            respaldos_encontrados = [v for v in valores_esperados if v.lower() in reporte_low]
            if len(respaldos_encontrados) >= max(1, len(valores_esperados) // 2):
                respaldo_doc = "SÍ (VALORES TÉCNICOS RESPALDADOS)"
                conteo_respaldo_doc_si += 1
            elif len(respaldos_encontrados) > 0:
                respaldo_doc = "PARCIAL (ALGUNOS VALORES CITADOS)"
                conteo_respaldo_doc_parcial += 1
            else:
                respaldo_doc = "NO RESPALDADO"
                conteo_respaldo_doc_no += 1

        registro_auditoria = {
            "id": cid,
            "sintoma": c_rep["texto_usuario"],
            "diagnostico_esperado": gt["falla_esperada"],
            "top1_ml": f"{top1_falla} ({conf_ml_top1*100:.1f}%)",
            "top2_ml": top2_falla,
            "top3_ml": top3_falla,
            "top1_ml_acierto": "SÍ" if top1_ml_match else "NO",
            "top3_ml_acierto": "SÍ" if top3_ml_match else "NO",
            "diagnostico_final_e2e": diag_final,
            "clasificacion_final_e2e": clasificacion_e2e,
            "macro_sistema_esperado": macro_esperado,
            "macro_sistema_predicho": macro_predicho,
            "macro_sistema_correcto": "SÍ" if macro_ok else "NO",
            "auto_interrogador_status": inter_status,
            "documento_rag_utilizado": f"{titulo_rag} (Similitud: {similitud_rag:.2f})",
            "respaldo_documental_valores": respaldo_doc,
        }
        resultados_auditoria.append(registro_auditoria)

    total = len(GROUND_TRUTH_50)
    top1_ml_acc = (conteo_top1_ml_estricto / total) * 100.0
    top3_ml_acc = (conteo_top3_ml_acierto / total) * 100.0

    e2e_estricto_acc = (conteo_e2e_estricto / total) * 100.0
    e2e_global_acc = ((conteo_e2e_estricto + conteo_e2e_diferencial) / total) * 100.0

    macro_acc = (conteo_macro_correcto / total) * 100.0

    # Efectividad auto-interrogador: de los casos donde era requerido, cuántos se activaron
    efectividad_auto_inter = (
        (conteo_auto_interrogador_efectivo / total_auto_interrogador_requerido) * 100.0
        if total_auto_interrogador_requerido > 0
        else 100.0
    )

    respaldo_doc_si_pct = (conteo_respaldo_doc_si / total) * 100.0
    respaldo_doc_parcial_pct = (conteo_respaldo_doc_parcial / total) * 100.0

    resumen = {
        "metricas_globales": {
            "total_casos_evaluados": total,
            "top1_ml_accuracy_pct": round(top1_ml_acc, 2),
            "top1_ml_conteo": conteo_top1_ml_estricto,
            "top3_ml_accuracy_pct": round(top3_ml_acc, 2),
            "top3_ml_conteo": conteo_top3_ml_acierto,
            "e2e_diagnostico_final_estricto_pct": round(e2e_estricto_acc, 2),
            "e2e_diagnostico_final_estricto_conteo": conteo_e2e_estricto,
            "e2e_diagnostico_final_diferencial_conteo": conteo_e2e_diferencial,
            "e2e_diagnostico_final_incorrecto_conteo": conteo_e2e_incorrecto,
            "e2e_diagnostico_final_global_pct": round(e2e_global_acc, 2),
            "macro_sistema_accuracy_pct": round(macro_acc, 2),
            "macro_sistema_conteo": conteo_macro_correcto,
            "auto_interrogador_efectividad_pct": round(efectividad_auto_inter, 2),
            "auto_interrogador_requerido_activado": conteo_auto_interrogador_efectivo,
            "auto_interrogador_total_requerido": total_auto_interrogador_requerido,
            "auto_interrogador_sobreactivaciones": conteo_interrogador_sobreactivado,
            "respaldo_documental_si_pct": round(respaldo_doc_si_pct, 2),
            "respaldo_documental_parcial_pct": round(respaldo_doc_parcial_pct, 2),
        },
        "detalle_por_caso": resultados_auditoria,
    }

    out_file = BASE_DIR / "docs" / "graficas" / "reporte_auditoria_50_casos_ground_truth.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump(resumen, f, indent=2, ensure_ascii=False)

    print("\n" + "=" * 80)
    print("AUDITORÍA CIENTÍFICA: 50 CASOS VS GROUND TRUTH ESTABLECIDO (FASE 7)")
    print("=" * 80)
    print(f"Total casos auditados: {total}")
    print(f"1. Top-1 ML Accuracy: {top1_ml_acc:.2f}% ({conteo_top1_ml_estricto}/{total})")
    print(f"2. Top-3 ML Accuracy: {top3_ml_acc:.2f}% ({conteo_top3_ml_acierto}/{total})")
    print(f"3. Diagnóstico Final E2E (Estricto): {e2e_estricto_acc:.2f}% ({conteo_e2e_estricto}/{total})")
    print(f"   Diagnóstico Final E2E (Diferencial Aceptable): {conteo_e2e_diferencial}/{total}")
    print(f"   Diagnóstico Final E2E (Incorrecto): {conteo_e2e_incorrecto}/{total}")
    print(f"   Diagnóstico Final E2E (Global Estricto + Diferencial): {e2e_global_acc:.2f}%")
    print(f"4. Macro-Sistema Accuracy: {macro_acc:.2f}% ({conteo_macro_correcto}/{total})")
    print(f"5. Efectividad Auto-interrogador: {efectividad_auto_inter:.2f}% ({conteo_auto_interrogador_efectivo}/{total_auto_interrogador_requerido})")
    print(f"6. Respaldo Documental de Tolerancias/OEM: {respaldo_doc_si_pct:.2f}% SÍ, {respaldo_doc_parcial_pct:.2f}% PARCIAL")
    print(f"\nReporte guardado en: {out_file}")
    print("=" * 80)


if __name__ == "__main__":
    auditar_50_casos()
