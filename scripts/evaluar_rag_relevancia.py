"""
Evaluación Comparativa de Relevancia del Motor RAG Multimarca (Hit@K y MRR).
Compara:
1. Búsqueda Semántica Léxica Base (V1): TF-IDF puro sobre consulta del usuario.
2. Búsqueda Híbrida Multiseñal (V2): Consulta + ML Top-3 + DTC + Macro-Sistema.
Mide:
- Hit@1: Porcentaje de casos donde el procedimiento Top 1 es técnicamente relevante.
- Hit@3: Porcentaje de casos con procedimiento relevante en Top 3.
- Hit@5: Porcentaje de casos con procedimiento relevante en Top 5.
- Mean Reciprocal Rank (MRR): Posicionamiento medio del procedimiento relevante.
"""

import sys
import json
import re
import numpy as np
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "backend"))
sys.path.insert(0, str(BASE_DIR / "scripts"))

from src.infrastructure.container import ServiceContainer
from src.core.diagnostico.taxonomia_sistemas import obtener_macro_sistema
from fase5_benchmark_v2_ground_truth import GROUND_TRUTH_G1, GROUND_TRUTH_G2

KEYWORDS_RELEVANCIA = {
    "misfire": ["misfire", "bujia", "bobina", "p0300", "p0301", "p0302", "p0303", "combustion"],
    "bujia": ["misfire", "bujia", "bobina", "p0300", "p0301", "p0302", "p0303", "combustion"],
    "bomba de gasolina": ["bomba", "combustible", "presion", "tanque", "caudal", "p0087", "aforador"],
    "inyectores": ["inyector", "inyectores", "riel", "combustible", "limpieza", "filtro", "scv"],
    "sensor de oxigeno": ["sensor", "oxigeno", "mezcla", "lambda", "p0171", "p0172", "p0420", "catalizador", "maf", "map"],
    "catalizador": ["catalizador", "p0420", "contraprestion", "escape", "emisiones", "eficiencia"],
    "valvula iac": ["iac", "cuerpo de aceleracion", "ralenti", "marcha minima", "p0505", "p0506", "mariposa", "etcs"],
    "cuerpo de aceleracion": ["iac", "cuerpo de aceleracion", "ralenti", "marcha minima", "p0505", "p0506", "mariposa", "etcs"],
    "culata": ["culata", "empaque", "sobrecalentamiento", "co2", "refrigerante", "burbujas"],
    "termostato": ["termostato", "motoventilador", "ventilador", "refrigeracion", "p0128", "temperatura", "purga", "radiador"],
    "aceite": ["aceite", "presion de aceite", "bomba de aceite", "taque", "punterias", "anillos", "retenes", "humo azul", "pcv"],
    "embrague": ["embrague", "clutch", "disco", "prensa", "bombin", "esclavo", "patina", "calado"],
    "freno": ["freno", "pastilla", "disco", "alabeo", "dtv", "liquido", "purga", "booster", "servofreno", "caliper"],
    "pastilla": ["freno", "pastilla", "disco", "alabeo", "dtv", "liquido", "purga", "booster", "servofreno", "caliper"],
    "caliper": ["caliper", "freno", "embolo", "traba", "pastilla", "mordaza"],
    "bateria": ["bateria", "arranque", "arrancador", "solenoide", "terminal 50", "clac", "alternador", "carga", "p0562"],
    "arranque": ["arranque", "arrancador", "solenoide", "terminal 50", "clac", "bateria"],
    "alternador": ["alternador", "carga", "diodos", "regulador", "lin", "p0562", "bateria", "voltaje"],
    "caja": ["caja", "transmision", "cvt", "dsg", "dualogic", "atf", "solenoide", "p0841", "p0700", "valvolina", "robotizada"],
    "transmision": ["caja", "transmision", "cvt", "dsg", "dualogic", "atf", "solenoide", "p0841", "p0700", "valvolina", "robotizada"],
    "robotizada": ["dualogic", "i-motion", "robotizada", "acumulador", "electrohidraulico", "p0841", "transmision"],
    "dualogic": ["dualogic", "i-motion", "robotizada", "acumulador", "electrohidraulico", "p0841", "transmision"],
    "suspension": ["amortiguador", "buje", "suspension", "llanta", "balanceo", "alineacion", "rebote", "trapecio"],
    "amortiguador": ["amortiguador", "buje", "suspension", "llanta", "balanceo", "alineacion", "rebote", "trapecio"],
    "llantas": ["balanceo", "alineacion", "llanta", "convergencia", "camber", "neumatico", "vibracion", "desbalance"],
    "desbalanceadas": ["balanceo", "alineacion", "llanta", "convergencia", "camber", "neumatico", "vibracion", "desbalance"],
    "direccion": ["cremallera", "direccion", "timon", "terminal", "rotula", "palier", "homocinetica", "triceta", "alineacion"],
    "rotula": ["rotula", "terminal", "direccion", "suspension", "juego"],
    "palier": ["palier", "homocinetica", "semieje", "fuelle", "rodamiento", "apoyo", "clac"],
    "homocinetica": ["homocinetica", "palier", "semieje", "fuelle", "rodamiento", "apoyo", "clac"],
    "distribucion": ["distribucion", "cadena", "faja", "correa", "sincronizacion", "desfase", "p0016", "p0017", "vvt", "ckp", "cmp"],
    "cadena": ["distribucion", "cadena", "faja", "correa", "sincronizacion", "desfase", "p0016", "p0017", "vvt", "ckp", "cmp"],
    "aire acondicionado": ["aire acondicionado", "compresor", "climatizacion", "r134a", "refrigerante", "fuga", "hvac"],
    "compresor": ["compresor", "aire acondicionado", "climatizacion", "r134a", "refrigerante", "fuga", "hvac"],
    "cierre centralizado": ["cierre centralizado", "chapa", "pestillo", "puerta", "actuador", "cerradura"],
    "elevalunas": ["elevalunas", "alzacristales", "vidrio", "motor ventana"],
    "camion": ["camion", "neumatico", "frenos de aire", "secador", "aps", "compresor de aire", "valvula"]
}

def es_procedimiento_relevante(titulo_procedimiento: str, contenido: str, falla_esperada: str, dtc_esperado: str = None) -> bool:
    tit_low = titulo_procedimiento.lower()
    cont_low = contenido[:1000].lower()
    falla_low = falla_esperada.lower()

    if dtc_esperado and dtc_esperado.lower() in tit_low:
        return True

    for grupo, palabras in KEYWORDS_RELEVANCIA.items():
        if grupo in falla_low:
            coincidencias = sum(1 for p in palabras if p in tit_low or p in cont_low)
            if coincidencias >= 1:
                return True

    return False

def evaluar_rag_benchmark():
    rag = ServiceContainer.get_motor_rag()
    modelo_ml = ServiceContainer.get_modelo_ml()

    json_path = BASE_DIR / "docs" / "graficas" / "reporte_evaluacion_nuevos_100_casos.json"
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    res_todos = data["grupo_1"]["resultados"] + data["grupo_2"]["resultados"]
    gt_todos = GROUND_TRUTH_G1 + GROUND_TRUTH_G2

    total = len(res_todos)

    # 1. Evaluación Semántica Básica
    h1_base, h3_base, h5_base, rr_base = 0, 0, 0, 0.0
    # 2. Evaluación Híbrida Multiseñal
    h1_hib, h3_hib, h5_hib, rr_hib = 0, 0, 0, 0.0

    detalles_hibridos = []

    for i, (r, gt) in enumerate(zip(res_todos, gt_todos)):
        caso_texto = r["caso"]
        falla_esp = gt["esperado"]
        dtc_esp = gt.get("dtc")

        # Inferencia ML para enriquecimiento híbrido
        pred_ml_top = modelo_ml.predecir_top_fallas(caso_texto, limite=3)
        top1_falla = pred_ml_top[0]["falla"] if pred_ml_top else ""
        macro_sis = obtener_macro_sistema(top1_falla)
        dtcs_cas = [dtc_esp] if dtc_esp else [d.upper() for d in re.findall(r"\b[pbcu]\d{4}\b", caso_texto, re.IGNORECASE)]

        # --- A. Búsqueda Léxica Base ---
        c_exp = rag._expandir_consulta(caso_texto)
        v_base = rag.vectorizador.transform([c_exp]).toarray().astype(np.float32)
        import faiss
        faiss.normalize_L2(v_base)
        s_b, idx_b = rag.faiss_index.search(v_base, k=5)
        rank_base = 0
        for k_idx in range(5):
            d_idx = int(idx_b[0][k_idx])
            if 0 <= d_idx < len(rag.documentos):
                if es_procedimiento_relevante(rag.titulos[d_idx], rag.documentos[d_idx], falla_esp, dtc_esp):
                    rank_base = k_idx + 1
                    break
        if rank_base == 1:
            h1_base += 1; h3_base += 1; h5_base += 1; rr_base += 1.0
        elif 1 < rank_base <= 3:
            h3_base += 1; h5_base += 1; rr_base += (1.0 / rank_base)
        elif 3 < rank_base <= 5:
            h5_base += 1; rr_base += (1.0 / rank_base)

        # --- B. Búsqueda Híbrida Multiseñal ---
        from src.infrastructure.rag.query_builder import construir_consulta_hibrida
        from src.infrastructure.rag.relevance_filter import reordenar_candidatos_rag

        c_hib = construir_consulta_hibrida(
            consulta_usuario=caso_texto,
            macro_sistema=macro_sis,
            top_fallas=pred_ml_top,
            codigos_dtc=dtcs_cas,
        )
        c_hib_exp = rag._expandir_consulta(c_hib)
        v_hib = rag.vectorizador.transform([c_hib_exp]).toarray().astype(np.float32)
        faiss.normalize_L2(v_hib)
        s_h, idx_h = rag.faiss_index.search(v_hib, k=15)

        cands = []
        for k_idx in range(min(15, len(rag.documentos))):
            d_idx = int(idx_h[0][k_idx])
            if 0 <= d_idx < len(rag.documentos):
                cands.append({
                    "indice": d_idx,
                    "titulo": rag.titulos[d_idx],
                    "documento": rag.documentos[d_idx],
                    "similitud": float(s_h[0][k_idx]),
                    "metadatos": rag.metadatos_procedimientos[d_idx] if d_idx < len(rag.metadatos_procedimientos) else {}
                })

        cands_reord = reordenar_candidatos_rag(
            cands,
            macro_sistema=macro_sis,
            top_fallas=pred_ml_top,
            codigos_dtc=dtcs_cas,
        )

        rank_hib = 0
        top5_hib_det = []
        for k_idx, c_item in enumerate(cands_reord[:5]):
            tit = c_item["titulo"]
            doc = c_item["documento"]
            es_rel = es_procedimiento_relevante(tit, doc, falla_esp, dtc_esp)
            top5_hib_det.append({
                "rank": k_idx + 1,
                "titulo": tit,
                "similitud": round(c_item["similitud"], 4),
                "relevante": es_rel
            })
            if es_rel and rank_hib == 0:
                rank_hib = k_idx + 1

        if rank_hib == 1:
            h1_hib += 1; h3_hib += 1; h5_hib += 1; rr_hib += 1.0
        elif 1 < rank_hib <= 3:
            h3_hib += 1; h5_hib += 1; rr_hib += (1.0 / rank_hib)
        elif 3 < rank_hib <= 5:
            h5_hib += 1; rr_hib += (1.0 / rank_hib)

        detalles_hibridos.append({
            "idx": i + 1,
            "caso": caso_texto[:70],
            "falla_esperada": falla_esp,
            "rank_base": rank_base,
            "rank_hibrido": rank_hib,
            "top1_recuperado": top5_hib_det[0]["titulo"] if top5_hib_det else "",
            "candidatos_top5": top5_hib_det
        })

    # Métricas
    hit1_b_pct = (h1_base / total) * 100
    hit3_b_pct = (h3_base / total) * 100
    hit5_b_pct = (h5_base / total) * 100
    mrr_b = rr_base / total

    hit1_h_pct = (h1_hib / total) * 100
    hit3_h_pct = (h3_hib / total) * 100
    hit5_h_pct = (h5_hib / total) * 100
    mrr_h = rr_hib / total

    print("\n" + "="*85)
    print("EVALUACIÓN COMPARATIVA DE RELEVANCIA TÉCNICA RAG (100 CASOS BENCHMARK V2)")
    print("="*85)
    print(f"{'Métrica':<35} | {'Semántica Base':<20} | {'Híbrida Multiseñal':<20}")
    print("-" * 85)
    print(f"{'Hit@1 (Primer procedimiento OK)':<35} | {hit1_b_pct:6.2f}% ({h1_base:02d}/{total})     | {hit1_h_pct:6.2f}% ({h1_hib:02d}/{total})")
    print(f"{'Hit@3 (En los 3 primeros)':<35} | {hit3_b_pct:6.2f}% ({h3_base:02d}/{total})     | {hit3_h_pct:6.2f}% ({h3_hib:02d}/{total})")
    print(f"{'Hit@5 (En los 5 primeros)':<35} | {hit5_b_pct:6.2f}% ({h5_base:02d}/{total})     | {hit5_h_pct:6.2f}% ({h5_hib:02d}/{total})")
    print(f"{'Mean Reciprocal Rank (MRR)':<35} | {mrr_b:6.4f}               | {mrr_h:6.4f}")
    print("="*85 + "\n")

    # Guardar reporte comparativo
    out_file = BASE_DIR / "docs" / "graficas" / "evaluacion_relevancia_rag.json"
    with open(out_file, "w", encoding="utf-8") as f:
        json.dump({
            "total_casos": total,
            "linea_base": {
                "hit_at_1": round(hit1_b_pct, 2),
                "hit_at_3": round(hit3_b_pct, 2),
                "hit_at_5": round(hit5_b_pct, 2),
                "mrr": round(mrr_b, 4)
            },
            "hibrida_multisenal": {
                "hit_at_1": round(hit1_h_pct, 2),
                "hit_at_3": round(hit3_h_pct, 2),
                "hit_at_5": round(hit5_h_pct, 2),
                "mrr": round(mrr_h, 4)
            },
            "detalles": detalles_hibridos
        }, f, indent=2, ensure_ascii=False)
    print(f"Reporte RAG guardado en: {out_file}")

if __name__ == "__main__":
    evaluar_rag_benchmark()
