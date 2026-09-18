import json
import sys
import os
from pathlib import Path

# Add paths
root_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(root_dir))
sys.path.insert(0, str(root_dir / "backend"))

from scratch.audit_l1_l2_l3_train import clasificar_ejemplo
from machine_learning.data.benchmark_dev_60_casos import CASOS_DEV_60
from machine_learning.data.benchmark_test_ciego_100 import BENCHMARK_TEST_CIEGO_100

from src.infrastructure.modelo_ml import ModeloML
from src.core.diagnostico.auto_interrogador import evaluar_auto_pregunta_descarte
from src.core.diagnostico.taxonomia_sistemas import obtener_macro_sistema

def normalizar_label(label: str) -> str:
    return label.strip().lower()

def coincidencia_falla(prediccion: str, esperada: str) -> bool:
    p = normalizar_label(prediccion)
    e = normalizar_label(esperada)
    if p == e:
        return True
    # Substring match if highly specific
    if e in p or p in e:
        return True
    return False

def evaluar_dataset(nombre, dataset):
    modelo = ModeloML(
        modelo_path="machine_learning/models/modelo_diagnostico.pkl",
        vectorizador_path="machine_learning/models/vectorizador_tfidf.pkl",
        modelo_sistema_path="machine_learning/models/modelo_sistema.pkl"
    )
    
    resultados_por_nivel = {
        "L1": [],
        "L2": [],
        "L3": []
    }
    
    for item in dataset:
        sintoma = item["sintoma"]
        falla_esp = item.get("falla_esperada", "")
        sist_esp = item.get("macro_sistema", "")
        es_ambiguo = item.get("es_ambiguo_intencional", False)
        
        # Clasificar nivel de información
        info_nivel = clasificar_ejemplo(sintoma)
        nivel = info_nivel["nivel"]
        
        # Inferencia ML
        top_fallas = modelo.predecir_top_fallas(sintoma, limite=3)
        macro_pred = modelo.predecir_sistema(sintoma)
        
        top1_falla = top_fallas[0]["falla"] if top_fallas else ""
        top1_prob = float(top_fallas[0]["probabilidad"]) if top_fallas else 0.0
        top3_fallas = [f["falla"] for f in top_fallas]
        
        # Aciertos
        macro_ok = (macro_pred.upper() == sist_esp.upper())
        top1_ok = any(coincidencia_falla(top1_falla, exp) for exp in [falla_esp] + item.get("claves_estrictas", []))
        top3_ok = any(
            any(coincidencia_falla(pred, exp) for exp in [falla_esp] + item.get("claves_estrictas", []) + item.get("claves_diferenciales", []))
            for pred in top3_fallas
        )
        
        # Auto-interrogador
        auto_preg = evaluar_auto_pregunta_descarte(
            texto=sintoma,
            diagnostico_top1=top1_falla,
            confianza_top1=top1_prob,
            predicciones_top=top_fallas
        )
        
        preg_necesaria = auto_preg.es_necesaria if auto_preg else False
        pregunta_texto = auto_preg.pregunta if auto_preg else ""
        opciones = auto_preg.opciones if auto_preg else []
        
        resultados_por_nivel[nivel].append({
            "id": item.get("id", ""),
            "sintoma": sintoma,
            "falla_esperada": falla_esp,
            "macro_sistema_esperado": sist_esp,
            "macro_sistema_predicho": macro_pred,
            "macro_ok": macro_ok,
            "top1_falla": top1_falla,
            "top1_prob": top1_prob,
            "top1_ok": top1_ok,
            "top3_fallas": top3_fallas,
            "top3_ok": top3_ok,
            "es_ambiguo_intencional": es_ambiguo,
            "auto_pregunta_necesaria": preg_necesaria,
            "pregunta_texto": pregunta_texto,
            "num_opciones": len(opciones)
        })
        
    resumen = {}
    for nivel, casos in resultados_por_nivel.items():
        total = len(casos)
        if total == 0:
            resumen[nivel] = {"total": 0}
            continue
        
        macro_acc = sum(1 for c in casos if c["macro_ok"]) / total * 100
        top1_acc = sum(1 for c in casos if c["top1_ok"]) / total * 100
        top3_acc = sum(1 for c in casos if c["top3_ok"]) / total * 100
        conf_media = sum(c["top1_prob"] for c in casos) / total
        preg_activada = sum(1 for c in casos if c["auto_pregunta_necesaria"]) / total * 100
        ambiguos_total = sum(1 for c in casos if c["es_ambiguo_intencional"])
        
        resumen[nivel] = {
            "total_casos": total,
            "macro_acc": round(macro_acc, 2),
            "top1_acc": round(top1_acc, 2),
            "top3_acc": round(top3_acc, 2),
            "confianza_media": round(conf_media, 4),
            "tasa_autopregunta": round(preg_activada, 2),
            "ambiguos_intencionales": ambiguos_total,
            "casos": casos
        }
        
    return resumen

if __name__ == "__main__":
    print("Evaluando BENCHMARK_TEST_CIEGO_100...")
    res_ciego = evaluar_dataset("TEST_CIEGO_100", BENCHMARK_TEST_CIEGO_100)
    
    print("\nEvaluando CASOS_DEV_60...")
    res_dev = evaluar_dataset("DEV_60", CASOS_DEV_60)
    
    output = {
        "test_ciego_100": {k: {kk: vv for kk, vv in v.items() if kk != "casos"} for k, v in res_ciego.items()},
        "dev_60": {k: {kk: vv for kk, vv in v.items() if kk != "casos"} for k, v in res_dev.items()},
        "detalles_test_ciego_100": res_ciego,
        "detalles_dev_60": res_dev
    }
    
    with open("scratch/evaluacion_niveles_independientes.json", "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
        
    print("\n================ RESUMEN TEST CIEGO 100 ================")
    for nivel in ["L1", "L2", "L3"]:
        d = output["test_ciego_100"].get(nivel, {})
        print(f"Nivel {nivel}: {d.get('total_casos', 0)} casos | Macro: {d.get('macro_acc', 0)}% | Top-1: {d.get('top1_acc', 0)}% | Top-3: {d.get('top3_acc', 0)}% | Conf: {d.get('confianza_media', 0):.3f} | AutoPreg: {d.get('tasa_autopregunta', 0)}%")
        
    print("\n================ RESUMEN DEV 60 ================")
    for nivel in ["L1", "L2", "L3"]:
        d = output["dev_60"].get(nivel, {})
        print(f"Nivel {nivel}: {d.get('total_casos', 0)} casos | Macro: {d.get('macro_acc', 0)}% | Top-1: {d.get('top1_acc', 0)}% | Top-3: {d.get('top3_acc', 0)}% | Conf: {d.get('confianza_media', 0):.3f} | AutoPreg: {d.get('tasa_autopregunta', 0)}%")
