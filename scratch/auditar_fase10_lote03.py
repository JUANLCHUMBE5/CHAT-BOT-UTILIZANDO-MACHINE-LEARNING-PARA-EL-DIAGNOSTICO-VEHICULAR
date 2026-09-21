"""
Auditoría exhaustiva de Fase 10 Lote 03 para CarBot.
Verifica 200 registros de Clases 11 a 15 contra todas las restricciones:
estructura, coherencia técnica, DTC, niveles L1/L2/L3, duplicados intra e inter-lotes,
near-duplicates, contaminación contra TRAIN/DEV/TEST/G1/G2/FIELD60, y contrastivos.
"""

import csv
import importlib.util
import re
import sys
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Backend taxonomia
sys.path.insert(0, str(Path("backend").resolve()))
from src.core.diagnostico.taxonomia_sistemas import FALLA_A_SISTEMA

def normalizar_texto(t: str) -> str:
    if not isinstance(t, str):
        return ""
    t = unicodedata.normalize("NFKD", t)
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = t.lower()
    t = re.sub(r"[^\w\s]", " ", t)
    return re.sub(r"\s+", " ", t).strip()

def cargar_py_benchmark(path_str: str, var_name: str):
    spec = importlib.util.spec_from_file_location("mod", path_str)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return getattr(mod, var_name)

def main():
    lote03_path = Path("dataset_fase10_lote_03.csv")
    print(f"=== INICIANDO AUDITORIA LOTE 03: {lote03_path} ===")
    
    # 1. UTF-8 check
    try:
        raw_bytes = lote03_path.read_bytes()
        raw_text = raw_bytes.decode("utf-8")
        print("[OK] Codificación UTF-8 válida.")
    except Exception as e:
        print(f"[ERROR] Decodificación UTF-8 falló: {e}")
        return

    df_l3 = pd.read_csv(lote03_path)
    total_reg = len(df_l3)
    print(f"Total registros Lote 03: {total_reg}")
    assert total_reg == 200, f"Error: esperados 200, encontrados {total_reg}"

    # 2. Estructura de columnas
    cols_esperadas = [
        "id", "id_grupo", "clase_objetivo", "macro_sistema", "nivel_informacion",
        "texto_usuario", "tipo_lenguaje", "condicion_operacion", "sintomas_presentes",
        "sintomas_negados", "dtc", "requiere_pregunta", "es_contrastivo",
        "clase_contrastiva", "fuente", "observaciones"
    ]
    assert list(df_l3.columns) == cols_esperadas, f"Columnas no coinciden: {df_l3.columns}"
    print("[OK] Estructura de 16 columnas canónicas verificada.")

    # 3. Clases canónicas
    clases_validas = set(FALLA_A_SISTEMA.keys())
    assert len(clases_validas) == 61, f"Taxonomía debe tener 61 clases, tiene {len(clases_validas)}"

    # Clases esperadas del lote 03
    clases_l03_esperadas = [
        "Faja o cadena de distribucion destensada o con salto de punto",
        "Falla en sistema de sincronizacion variable de valvulas (VVT / VVT-i / Valvetronic)",
        "Falla de descarbonizacion e inyeccion directa GDI (acumulacion de carbon en valvulas)",
        "Falla en actuador de turbocompresor o VGT en motores alemanes TSI / TFSI",
        "Fuga en mangueras de intercooler o turbocompresor danado"
    ]
    for c in clases_l03_esperadas:
        assert c in clases_validas, f"Clase no canónica: {c}"
    print("[OK] Las 5 clases objetivo pertenecen exactamente a las 61 canónicas.")

    # 4. Distribución de clases y niveles
    conteo_clases = df_l3["clase_objetivo"].value_counts().to_dict()
    for c in clases_l03_esperadas:
        cant = conteo_clases.get(c, 0)
        assert cant == 40, f"Clase {c} tiene {cant} != 40 registros."
    print("[OK] Exactamente 40 registros por clase (5 x 40 = 200).")

    conteo_niveles = df_l3["nivel_informacion"].value_counts().to_dict()
    assert conteo_niveles.get("L1") == 50, f"L1 tiene {conteo_niveles.get('L1')} != 50"
    assert conteo_niveles.get("L2") == 75, f"L2 tiene {conteo_niveles.get('L2')} != 75"
    assert conteo_niveles.get("L3") == 75, f"L3 tiene {conteo_niveles.get('L3')} != 75"
    print("[OK] Distribución obligatoria de niveles: L1=50, L2=75, L3=75.")

    # 5. Cargar referencias para duplicados y leakage
    print("\nCargando fuentes de referencia para auditoría de duplicados y leakage...")
    df_l1 = pd.read_csv("dataset_fase10_lote_01.csv")
    df_l2 = pd.read_csv("dataset_fase10_lote_02.csv")
    df_train = pd.read_csv("machine_learning/data/dataset_sintomas_limpio.csv")
    dev_60 = cargar_py_benchmark("machine_learning/data/benchmark_dev_60_casos.py", "CASOS_DEV_60")
    test_100 = cargar_py_benchmark("machine_learning/data/benchmark_test_ciego_100.py", "BENCHMARK_TEST_CIEGO_100")
    g1 = cargar_py_benchmark("scripts/benchmark_v4_g1_casos.py", "BENCHMARK_V4_G1_CASOS")
    g2 = cargar_py_benchmark("scripts/benchmark_v4_g2_casos.py", "BENCHMARK_V4_G2_CASOS")
    df_field60 = pd.read_csv("machine_learning/data/casos_reales_mecanicos_evaluacion.csv")

    corpus_ref = {}
    for idx, row in df_l1.iterrows():
        corpus_ref[f"LOTE01_{row['id']}"] = ("LOTE_01", str(row["texto_usuario"]))
    for idx, row in df_l2.iterrows():
        corpus_ref[f"LOTE02_{row['id']}"] = ("LOTE_02", str(row["texto_usuario"]))
    for idx, row in df_train.iterrows():
        corpus_ref[f"TRAIN_{idx}"] = ("TRAIN", str(row["sintoma"]))
    for item in dev_60:
        corpus_ref[f"DEV60_{item['id']}"] = ("DEV_60", str(item["sintoma"]))
    for item in test_100:
        corpus_ref[f"TEST100_{item['id']}"] = ("TEST_100", str(item["sintoma"]))
    for item in g1:
        corpus_ref[f"G1_{item['id']}"] = ("G1", str(item["sintoma"]))
    for item in g2:
        corpus_ref[f"G2_{item['id']}"] = ("G2", str(item["sintoma"]))
    for idx, row in df_field60.iterrows():
        txt = str(row.get("sintoma", row.get("descripcion", "")))
        corpus_ref[f"FIELD60_{idx}"] = ("FIELD_60", txt)

    print(f"Total referencias cotejadas: {len(corpus_ref)}")

    textos_l3 = [str(t) for t in df_l3["texto_usuario"].tolist()]
    textos_l3_norm = [normalizar_texto(t) for t in textos_l3]

    ref_keys = list(corpus_ref.keys())
    ref_origins = [corpus_ref[k][0] for k in ref_keys]
    textos_ref = [corpus_ref[k][1] for k in ref_keys]
    textos_ref_norm = [normalizar_texto(t) for t in textos_ref]

    # TF-IDF para similitud
    vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=1, sublinear_tf=True)
    vectorizer.fit(textos_l3_norm + textos_ref_norm)
    mat_l3 = vectorizer.transform(textos_l3_norm)
    mat_ref = vectorizer.transform(textos_ref_norm)

    sim_intra = cosine_similarity(mat_l3, mat_l3)
    np.fill_diagonal(sim_intra, 0.0)

    sim_inter = cosine_similarity(mat_l3, mat_ref)

    # 6. Evaluación individual detallada
    auditoria_rows = []
    aprobados = 0
    revisar = 0
    rechazados = 0
    total_con_dtc = 0
    total_contrastivos = 0

    for i, row in df_l3.iterrows():
        reg_id = str(row["id"])
        clase = str(row["clase_objetivo"])
        macro = str(row["macro_sistema"])
        nivel = str(row["nivel_informacion"])
        texto = str(row["texto_usuario"])
        texto_norm = textos_l3_norm[i]
        es_cont = str(row["es_contrastivo"]).strip().upper()
        clase_cont = str(row["clase_contrastiva"]).strip() if pd.notna(row["clase_contrastiva"]) else ""
        dtc_val = str(row["dtc"]).strip() if pd.notna(row["dtc"]) else ""
        req_preg = str(row["requiere_pregunta"]).strip().upper()

        motivos = []
        estado = "APROBADO"

        # Coherencia macro
        if macro != "MOTOR":
            motivos.append(f"Macro {macro} != MOTOR")
            estado = "REVISAR"

        # L1 sin DTC y con requiere_pregunta = SI
        if nivel == "L1":
            if dtc_val:
                motivos.append(f"L1 contiene DTC '{dtc_val}' (prohibido en L1)")
                estado = "REVISAR"
            if req_preg != "SI":
                motivos.append("L1 con requiere_pregunta != SI")
                estado = "REVISAR"

        # Conteo DTC
        if dtc_val:
            total_con_dtc += 1
            if not re.match(r"^[PBCU]\d{4}$", dtc_val):
                motivos.append(f"Formato DTC inválido: '{dtc_val}'")
                estado = "REVISAR"

        # Contrastivo
        if es_cont == "SI":
            total_contrastivos += 1
            if not clase_cont:
                motivos.append("es_contrastivo=SI pero clase_contrastiva vacía")
                estado = "REVISAR"
            elif clase_cont not in clases_validas:
                motivos.append(f"clase_contrastiva '{clase_cont}' no está en las 61 canónicas")
                estado = "RECHAZADO"
            elif clase_cont == clase:
                motivos.append("clase_contrastiva igual a clase_objetivo")
                estado = "REVISAR"
        elif es_cont == "NO":
            if clase_cont:
                motivos.append(f"es_contrastivo=NO pero tiene clase_contrastiva '{clase_cont}'")
                estado = "REVISAR"

        # Duplicado exacto intra-lote
        dups_intra = [j for j, tn in enumerate(textos_l3_norm) if j != i and tn == texto_norm]
        if dups_intra:
            motivos.append(f"Duplicado exacto intra-lote con {df_l3.iloc[dups_intra[0]]['id']}")
            estado = "RECHAZADO"

        # Duplicado exacto inter-lotes / train / dev / benchmarks / field
        dups_inter = [j for j, trn in enumerate(textos_ref_norm) if trn == texto_norm]
        if dups_inter:
            origen_dup = ref_origins[dups_inter[0]]
            key_dup = ref_keys[dups_inter[0]]
            motivos.append(f"Duplicado exacto con {origen_dup} ({key_dup})")
            estado = "RECHAZADO"

        # Similitud intra-lote máxima
        max_intra = float(np.max(sim_intra[i]))
        max_intra_idx = int(np.argmax(sim_intra[i]))
        if max_intra > 0.90:
            motivos.append(f"Near-duplicate intra-lote con {df_l3.iloc[max_intra_idx]['id']} (sim={max_intra:.3f})")
            if max_intra > 0.96:
                estado = "RECHAZADO"
            elif estado != "RECHAZADO":
                estado = "REVISAR"

        # Similitud inter-referencias máxima (leakage)
        max_inter = float(np.max(sim_inter[i]))
        max_inter_idx = int(np.argmax(sim_inter[i]))
        ref_orig = ref_origins[max_inter_idx]
        ref_k = ref_keys[max_inter_idx]
        if max_inter > 0.88:
            motivos.append(f"Posible leakage con {ref_orig} ({ref_k}) (sim={max_inter:.3f})")
            if max_inter > 0.95:
                estado = "RECHAZADO"
            elif estado != "RECHAZADO":
                estado = "REVISAR"

        if estado == "APROBADO":
            aprobados += 1
        elif estado == "REVISAR":
            revisar += 1
        else:
            rechazados += 1

        auditoria_rows.append({
            "id": reg_id,
            "clase_objetivo": clase,
            "nivel_informacion": nivel,
            "estado_auditoria": estado,
            "motivos": " | ".join(motivos) if motivos else "CONFORME",
            "sim_intra_max": round(max_intra, 4),
            "sim_inter_max": round(max_inter, 4),
            "inter_ref_origen": ref_orig,
            "dtc": dtc_val,
            "es_contrastivo": es_cont,
            "clase_contrastiva": clase_cont
        })

    # Guardar reporte de auditoría CSV
    df_aud = pd.DataFrame(auditoria_rows)
    audit_csv = Path("fase10_auditoria_lote03.csv")
    df_aud.to_csv(audit_csv, index=False, encoding="utf-8")
    print(f"\n[OK] Auditoría guardada en {audit_csv}")

    # Resumen
    print("\n" + "="*50)
    print("RESUMEN DE AUDITORIA LOTE 03")
    print("="*50)
    print(f"Total registros: {total_reg}")
    print(f"APROBADO: {aprobados}")
    print(f"REVISAR:  {revisar}")
    print(f"RECHAZADO: {rechazados}")
    print(f"Conteo L1 / L2 / L3: {conteo_niveles.get('L1')} / {conteo_niveles.get('L2')} / {conteo_niveles.get('L3')}")
    print(f"Cantidad con DTC: {total_con_dtc}")
    print(f"Cantidad contrastivos: {total_contrastivos}")
    
    # Máximas similitudes
    max_sim_global_inter = df_aud["sim_inter_max"].max()
    max_sim_global_intra = df_aud["sim_intra_max"].max()
    print(f"Máxima similitud intra-lote: {max_sim_global_intra:.4f}")
    print(f"Máxima similitud inter-referencias (leakage): {max_sim_global_inter:.4f}")

    if revisar > 0 or rechazados > 0:
        print("\n[ALERTA] Registros no conformes:")
        for r in auditoria_rows:
            if r["estado_auditoria"] != "APROBADO":
                print(f"  {r['id']} [{r['estado_auditoria']}]: {r['motivos']}")

if __name__ == "__main__":
    main()
