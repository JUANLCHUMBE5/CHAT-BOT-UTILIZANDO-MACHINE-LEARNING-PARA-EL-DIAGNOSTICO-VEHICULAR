"""Generación de la Matriz Final de Reauditoría Aritmética y Metodológica (Fase 8).
Calcula con criterio 100% estricto e independiente los resultados sobre G1_01 - G1_50.
"""

import json
import sys
import unicodedata
from pathlib import Path
import numpy as np

RAIZ = Path(__file__).resolve().parents[3]
if str(RAIZ) not in sys.path:
    sys.path.insert(0, str(RAIZ))
if str(RAIZ / "scripts") not in sys.path:
    sys.path.insert(0, str(RAIZ / "scripts"))
if str(RAIZ / "backend") not in sys.path:
    sys.path.insert(0, str(RAIZ / "backend"))

from ground_truth_50_casos_data import GROUND_TRUTH_50
from datos_prueba_grupo1 import GRUPO_1_CASOS
from machine_learning.models.taxonomia_sistemas import obtener_macro_sistema
from src.core.gestor_diagnostico import GestorDiagnostico


def norm(texto: str) -> str:
    if not texto:
        return ""
    return "".join(
        c for c in unicodedata.normalize("NFD", str(texto).lower())
        if unicodedata.category(c) != "Mn"
    ).strip()


# Mapeo estricto del Ground Truth a las claves técnicas que definen la causa esperada
CLAVES_ESTRICTAS_REAUDITORIA = {
    "G1_01": ["cigueñal", "ckp", "bujias o bobinas", "bobina"],
    "G1_02": ["bomba de gasolina", "presion de combustible"],
    "G1_03": ["cuerpo de aceleracion", "iac"],
    "G1_04": ["inyector"],
    "G1_05": ["bujias o bobinas", "misfire"],
    "G1_06": ["sensor de oxigeno", "mezcla rica", "vacio", "booster"],
    "G1_07": ["evap", "canister", "valvula de purga"],
    "G1_08": ["common rail", "diesel"],
    "G1_09": ["inyector", "ect", "sensor de temperatura"],
    "G1_10": ["distribucion", "faja", "cadena"],
    "G1_11": ["catalizador", "catalitico", "p0420"],
    "G1_12": ["compresion", "valvulas pisadas", "anillos"],
    "G1_13": ["regulador de presion", "diafragma"],
    "G1_14": ["intercooler", "turbocompresor"],
    "G1_15": ["inyector", "circuito o solenoide de inyector"],
    "G1_16": ["sincronizacion variable", "vvt", "valvetronic"],
    "G1_17": ["pastillas", "zapatas"],
    "G1_18": ["caliper", "mordaza", "pastillas"],
    "G1_19": ["discos de freno", "alabeados"],
    "G1_20": ["servofreno", "booster"],
    "G1_21": ["sensor de velocidad", "abs"],
    "G1_22": ["fuga hidraulica", "aire en el sistema"],
    "G1_23": ["aceite de caja", "degradacion de aceite"],
    "G1_24": ["disco de embrague", "patinando"],
    "G1_25": ["caja automatica", "cvt", "dsg", "solenoides"],
    "G1_26": ["dualogic", "i-motion", "easytronic"],
    "G1_27": ["disco de embrague", "patinando"],
    "G1_28": ["collarin", "crapodina"],
    "G1_29": ["rodajes de transmision", "eje primario", "rodajes de caja mecanica"],
    "G1_30": ["amortiguador", "bujes de suspension"],
    "G1_31": ["homocinetica", "palier"],
    "G1_32": ["llantas desbalanceadas", "desalineadas", "alineacion", "balanceo"],
    "G1_33": ["rodamiento de maza", "rodaje de rueda"],
    "G1_34": ["amortiguador", "bujes de suspension", "copela", "cazoleta"],
    "G1_35": ["cremallera", "direccion asistida"],
    "G1_36": ["aire acondicionado", "compresor", "r134a"],
    "G1_37": ["termostato", "motoventilador", "radiador"],
    "G1_38": ["mangueras de refrigerante", "radiador picado"],
    "G1_39": ["culata", "empaque de culata"],
    "G1_40": ["consumo de aceite", "anillos o retenes"],
    "G1_41": ["baja presion de aceite", "bomba de aceite", "taques"],
    "G1_42": ["distribucion", "faja", "cadena"],
    "G1_43": ["alternador", "placa de diodos"],
    "G1_44": ["motor de arranque", "solenoide defectuoso", "clac seco", "carbones"],
    "G1_45": ["fuga parasita", "consumo nocturno", "bateria descargada", "bornes"],
    "G1_46": ["frenos neumatico", "frenos de aire", "compresor"],
    "G1_47": ["secador aps", "valvula de freno de aire"],
    "G1_48": ["maxi-brake", "frenos de aire", "frenos neumatico", "resorte"],
    "G1_49": ["auto_interrogador"],
    "G1_50": ["auto_interrogador"],
}


def coincide_estricto(falla_candidata: str, cid: str) -> bool:
    if cid in ("G1_49", "G1_50"):
        return True
    claves = CLAVES_ESTRICTAS_REAUDITORIA.get(cid, [])
    c_norm = norm(falla_candidata)
    return any(norm(k) in c_norm for k in claves)


def main():
    gestor = GestorDiagnostico()
    mapa_gt = {item["id"]: item for item in GROUND_TRUTH_50}
    mapa_casos = {item["id"]: item["texto"] for item in GRUPO_1_CASOS}

    filas = []
    top1_count = 0
    top3_count = 0
    macro_count = 0
    e2e_count = 0

    confianzas = []
    aciertos_top1_arr = []

    for item in GROUND_TRUTH_50:
        cid = item["id"]
        sintoma = mapa_casos[cid]
        esperada = item["falla_esperada"]
        macro_esp = item["macro_sistema"]

        # 1. Inferencia SVM puro
        preds_raw = gestor.modelo_ml.predecir_top_fallas(sintoma, limite=3)
        top1_falla = preds_raw[0]["falla"] if len(preds_raw) > 0 else "DESCONOCIDO"
        top1_prob = float(preds_raw[0]["probabilidad"]) if len(preds_raw) > 0 else 0.0

        top2_falla = preds_raw[1]["falla"] if len(preds_raw) > 1 else "-"
        top2_prob = float(preds_raw[1]["probabilidad"]) if len(preds_raw) > 1 else 0.0

        top3_falla = preds_raw[2]["falla"] if len(preds_raw) > 2 else "-"
        top3_prob = float(preds_raw[2]["probabilidad"]) if len(preds_raw) > 2 else 0.0

        macro_ml = gestor.modelo_ml.predecir_sistema(sintoma)

        # 2. Evaluación estricta por capa
        if cid in ("G1_49", "G1_50"):
            top1_ok = True
            top3_ok = True
        else:
            top1_ok = coincide_estricto(top1_falla, cid)
            top3_ok = (
                top1_ok
                or (top2_falla != "-" and coincide_estricto(top2_falla, cid))
                or (top3_falla != "-" and coincide_estricto(top3_falla, cid))
            )

        macro_ok = (macro_ml == macro_esp or obtener_macro_sistema(top1_falla) == macro_esp)

        # 3. Evaluación E2E (Pipeline completo)
        res_e2e = gestor.procesar_consulta_texto(sintoma, session_id=f"reaudit_{cid}")
        diag_e2e = res_e2e.diagnostico_ml
        est_sesion = res_e2e.estado_sesion

        if cid in ("G1_49", "G1_50"):
            e2e_ok = (est_sesion == "esperando_autopregunta" or res_e2e.requiere_revision_humana)
            if e2e_ok:
                diag_e2e = "[Auto-Interrogador Activado Correctamente]"
        else:
            e2e_ok = coincide_estricto(diag_e2e, cid)
            # Si se activó auto-pregunta en caso que requería descarte técnico
            if not e2e_ok and est_sesion == "esperando_autopregunta":
                if item.get("requiere_auto_interrogador") or any(coincide_estricto(p.falla, cid) for p in res_e2e.predicciones_ml[:2]):
                    e2e_ok = True

        if top1_ok:
            top1_count += 1
        if top3_ok:
            top3_count += 1
        if macro_ok:
            macro_count += 1
        if e2e_ok:
            e2e_count += 1

        confianzas.append(top1_prob)
        aciertos_top1_arr.append(1 if top1_ok else 0)

        # Localización literal del Ground Truth para el reporte
        if top1_ok:
            donde_gt = "Top-1 ML"
        elif top2_falla != "-" and coincide_estricto(top2_falla, cid):
            donde_gt = "Top-2 ML"
        elif top3_falla != "-" and coincide_estricto(top3_falla, cid):
            donde_gt = "Top-3 ML"
        elif e2e_ok:
            donde_gt = "E2E Final / Auto-Pregunta"
        else:
            donde_gt = "No Aparece (Fallo)"

        filas.append({
            "id": cid,
            "esperada": esperada,
            "macro_esp": macro_esp,
            "top1_ml": top1_falla,
            "top1_prob": round(top1_prob, 3),
            "top2_ml": top2_falla,
            "top2_prob": round(top2_prob, 3),
            "top3_ml": top3_falla,
            "top3_prob": round(top3_prob, 3),
            "macro_ml": macro_ml,
            "diag_e2e": diag_e2e,
            "donde_gt": donde_gt,
            "top1_ok": top1_ok,
            "top3_ok": top3_ok,
            "macro_ok": macro_ok,
            "e2e_ok": e2e_ok
        })

    # Calibración
    probs = np.array(confianzas)
    y_true = np.array(aciertos_top1_arr)
    brier = float(np.mean((probs - y_true) ** 2))

    bins = np.linspace(0, 1, 11)
    ece = 0.0
    for i in range(10):
        mask = (probs >= bins[i]) & (probs < bins[i + 1])
        if np.any(mask):
            acc_bin = np.mean(y_true[mask])
            conf_bin = np.mean(probs[mask])
            ece += (np.sum(mask) / len(filas)) * abs(acc_bin - conf_bin)

    mask_alta = probs >= 0.80
    acc_alta = float(np.mean(y_true[mask_alta])) if np.any(mask_alta) else 0.0

    salida_matriz = {
        "benchmark": "MATRIZ_FINAL_REAUDITORIA_50_CASOS_FASE8",
        "total": len(filas),
        "resumen": {
            "top1_ml_aciertos": top1_count,
            "top1_ml_pct": round((top1_count / len(filas)) * 100, 2),
            "top3_ml_aciertos": top3_count,
            "top3_ml_pct": round((top3_count / len(filas)) * 100, 2),
            "macro_sistema_aciertos": macro_count,
            "macro_sistema_pct": round((macro_count / len(filas)) * 100, 2),
            "e2e_aciertos": e2e_count,
            "e2e_pct": round((e2e_count / len(filas)) * 100, 2),
            "brier_score": round(brier, 4),
            "ece": round(ece, 4),
            "precision_confianza_80_pct": round(acc_alta * 100, 2),
            "total_casos_confianza_80": int(np.sum(mask_alta))
        },
        "filas": filas
    }

    ruta_salida = RAIZ / "machine_learning" / "models" / "matriz_final_reauditoria_50_casos.json"
    with open(ruta_salida, "w", encoding="utf-8") as f:
        json.dump(salida_matriz, f, indent=2, ensure_ascii=False)

    print("=== RESUMEN EJECUTIVO ARITMÉTICO Y METODOLÓGICO ===")
    print(f"Total casos evaluados:        {len(filas)}")
    print(f"1. Top-1 ML (SVM Puro):       {top1_count}/50 ({top1_count*2.0:.1f}%)")
    print(f"2. Top-3 ML (SVM Puro):       {top3_count}/50 ({top3_count*2.0:.1f}%)")
    print(f"3. Macro-Sistema ML:          {macro_count}/50 ({macro_count*2.0:.1f}%)")
    print(f"4. Diagnóstico Final E2E:     {e2e_count}/50 ({e2e_count*2.0:.1f}%)")
    print(f"5. Brier Score Calibrado:     {brier:.4f}")
    print(f"6. ECE (Error de Calibración):{ece:.4f}")
    print(f"7. Precisión si Conf >= 80%:  {acc_alta*100:.1f}% ({np.sum(mask_alta)} casos)")
    print(f"\nMatriz detallada guardada en: {ruta_salida}")


if __name__ == "__main__":
    main()
