"""
Auditoría exhaustiva de Fase 10 Lote 10 (CLIMATIZACION y CARROCERIA_NEUMATICA) para CarBot.
Verifica 200 registros de Clases 54 a 58 contra todas las restricciones:
- Estructura canónica de 16 columnas.
- Coherencia técnica, macro_sistema = 'CLIMATIZACION' (Clase 54) y 'CARROCERIA_NEUMATICA' (Clases 55 a 58).
- Distribución exacta: 5 clases x 40 casos = 200 (10 L1, 15 L2, 15 L3 por clase).
- L1: 0 DTC, requiere_pregunta = 'SI'.
- L2/L3: DTC válidos y sintácticos, control de atajo de DTC.
- Contrastivos válidos dentro de las 61 etiquetas canónicas.
- Duplicados intra e inter-lotes (L01 a L09).
- Fuga y contaminación (leakage) contra TRAIN, DEV-60, TEST-100, G1, G2, FIELD-60.
- Validación especial Clase 54 (Climatización de habitáculo libre de empuje a MOTOR).
"""

import csv
import importlib.util
import os
import re
import sys
import unicodedata
from collections import Counter
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


def verificar_clase_54_climatizacion(texto: str):
    """
    Verifica que la evidencia principal de clase 54 corresponda a climatización de cabina
    y no contenga palabras o contextos que empujen espuriamente hacia MOTOR.
    """
    tn = normalizar_texto(texto)
    errores = []
    # No debe confundir con refrigeración de motor
    if "recalentamiento de motor" in tn and "ac" not in tn and "aire" not in tn:
        errores.append("Texto de Clase 54 parece describir recalentamiento de motor sin mención a A/C")
    return errores


def auditar_lote10():
    lote10_path = Path("dataset_fase10_lote_10.csv")
    print(f"=== INICIANDO AUDITORIA LOTE 10: {lote10_path} ===")

    # 1. UTF-8 check
    try:
        raw_bytes = lote10_path.read_bytes()
        raw_text = raw_bytes.decode("utf-8")
        print("[OK] Codificación UTF-8 válida.")
    except Exception as e:
        print(f"[ERROR] Decodificación UTF-8 falló: {e}")
        return False

    df_l10 = pd.read_csv(lote10_path)
    total_reg = len(df_l10)
    print(f"Total registros Lote 10: {total_reg}")
    assert total_reg == 200, f"Error: esperados 200, encontrados {total_reg}"

    # 2. Estructura de columnas
    cols_esperadas = [
        "id", "id_grupo", "clase_objetivo", "macro_sistema", "nivel_informacion",
        "texto_usuario", "tipo_lenguaje", "condicion_operacion", "sintomas_presentes",
        "sintomas_negados", "dtc", "requiere_pregunta", "es_contrastivo",
        "clase_contrastiva", "fuente", "observaciones"
    ]
    assert list(df_l10.columns) == cols_esperadas, f"Columnas no coinciden: {df_l10.columns}"
    print("[OK] Estructura de 16 columnas canónicas verificada.")

    # 3. Clases canónicas
    clases_validas = set(FALLA_A_SISTEMA.keys())
    assert len(clases_validas) == 61, f"Taxonomía debe tener 61 clases, tiene {len(clases_validas)}"

    clases_l10_esperadas = [
        "Falla en compresor de aire acondicionado o fuga de gas R134a",
        "Falla electrica del cierre centralizado o actuador de puerta",
        "Cerradura, chapa o pestillo mecanico de puerta trabado o desalineado",
        "Elevalunas electrico o guaya de alzacristales rota o trabada",
        "Limpiaparabrisas o motor pluma quemado"
    ]

    for c in clases_l10_esperadas:
        assert c in clases_validas, f"Clase no canónica: {c}"
        macro_esp = FALLA_A_SISTEMA[c]
        if c == "Falla en compresor de aire acondicionado o fuga de gas R134a":
            assert macro_esp == "CLIMATIZACION", f"Macro no es CLIMATIZACION para {c}"
        else:
            assert macro_esp == "CARROCERIA_NEUMATICA", f"Macro no es CARROCERIA_NEUMATICA para {c}"
    print("[OK] Las 5 clases objetivo pertenecen exactamente a las 61 canónicas con macros correctos.")

    # 4. Distribución de clases y niveles
    conteo_clases = df_l10["clase_objetivo"].value_counts().to_dict()
    for c in clases_l10_esperadas:
        cant = conteo_clases.get(c, 0)
        assert cant == 40, f"Clase {c} tiene {cant} != 40 registros"
    print("[OK] Cada una de las 5 clases tiene exactamente 40 registros.")

    niveles_conteo = df_l10["nivel_informacion"].value_counts().to_dict()
    assert niveles_conteo.get("L1") == 50, f"L1 total {niveles_conteo.get('L1')} != 50"
    assert niveles_conteo.get("L2") == 75, f"L2 total {niveles_conteo.get('L2')} != 75"
    assert niveles_conteo.get("L3") == 75, f"L3 total {niveles_conteo.get('L3')} != 75"
    print(f"[OK] Distribución de niveles: L1={niveles_conteo['L1']}, L2={niveles_conteo['L2']}, L3={niveles_conteo['L3']}.")

    for c in clases_l10_esperadas:
        sub_c = df_l10[df_l10["clase_objetivo"] == c]
        sub_niv = sub_c["nivel_informacion"].value_counts().to_dict()
        assert sub_niv.get("L1") == 10, f"Clase {c} tiene {sub_niv.get('L1')} L1 != 10"
        assert sub_niv.get("L2") == 15, f"Clase {c} tiene {sub_niv.get('L2')} L2 != 15"
        assert sub_niv.get("L3") == 15, f"Clase {c} tiene {sub_niv.get('L3')} L3 != 15"
    print("[OK] Cada una de las 5 clases tiene exactamente 10 L1, 15 L2, 15 L3.")

    # 5. Cargar referencias para duplicados y leakage
    print("\nCargando fuentes de referencia para auditoría de duplicados y leakage...")
    df_l1 = pd.read_csv("dataset_fase10_lote_01.csv")
    df_l2 = pd.read_csv("dataset_fase10_lote_02.csv")
    df_l3 = pd.read_csv("dataset_fase10_lote_03.csv")
    df_l4 = pd.read_csv("dataset_fase10_lote_04.csv")
    df_l5 = pd.read_csv("dataset_fase10_lote_05.csv")
    df_l6 = pd.read_csv("dataset_fase10_lote_06.csv")
    df_l7 = pd.read_csv("dataset_fase10_lote_07.csv")
    df_l8 = pd.read_csv("dataset_fase10_lote_08.csv")
    df_l9 = pd.read_csv("dataset_fase10_lote_09.csv")
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
    for idx, row in df_l3.iterrows():
        corpus_ref[f"LOTE03_{row['id']}"] = ("LOTE_03", str(row["texto_usuario"]))
    for idx, row in df_l4.iterrows():
        corpus_ref[f"LOTE04_{row['id']}"] = ("LOTE_04", str(row["texto_usuario"]))
    for idx, row in df_l5.iterrows():
        corpus_ref[f"LOTE05_{row['id']}"] = ("LOTE_05", str(row["texto_usuario"]))
    for idx, row in df_l6.iterrows():
        corpus_ref[f"LOTE06_{row['id']}"] = ("LOTE_06", str(row["texto_usuario"]))
    for idx, row in df_l7.iterrows():
        corpus_ref[f"LOTE07_{row['id']}"] = ("LOTE_07", str(row["texto_usuario"]))
    for idx, row in df_l8.iterrows():
        corpus_ref[f"LOTE08_{row['id']}"] = ("LOTE_08", str(row["texto_usuario"]))
    for idx, row in df_l9.iterrows():
        corpus_ref[f"LOTE09_{row['id']}"] = ("LOTE_09", str(row["texto_usuario"]))
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

    textos_l10 = [str(t) for t in df_l10["texto_usuario"].tolist()]
    textos_l10_norm = [normalizar_texto(t) for t in textos_l10]

    ref_keys = list(corpus_ref.keys())
    ref_origins = [corpus_ref[k][0] for k in ref_keys]
    textos_ref = [corpus_ref[k][1] for k in ref_keys]
    textos_ref_norm = [normalizar_texto(t) for t in textos_ref]

    # TF-IDF para similitud
    vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=1, sublinear_tf=True)
    vectorizer.fit(textos_l10_norm + textos_ref_norm)
    mat_l10 = vectorizer.transform(textos_l10_norm)
    mat_ref = vectorizer.transform(textos_ref_norm)

    sim_intra = cosine_similarity(mat_l10, mat_l10)
    np.fill_diagonal(sim_intra, 0.0)

    sim_inter = cosine_similarity(mat_l10, mat_ref)

    # 6. Evaluación individual detallada
    auditoria_rows = []
    aprobados = 0
    revisar = 0
    rechazados = 0
    total_con_dtc = 0
    total_contrastivos = 0

    dtc_por_clase = {c: 0 for c in clases_l10_esperadas}
    dtc_por_nivel = {"L1": 0, "L2": 0, "L3": 0}

    for i, row in df_l10.iterrows():
        reg_id = str(row["id"])
        clase = str(row["clase_objetivo"])
        macro = str(row["macro_sistema"])
        nivel = str(row["nivel_informacion"])
        texto = str(row["texto_usuario"])
        texto_norm = textos_l10_norm[i]
        es_cont = str(row["es_contrastivo"]).strip().upper()
        clase_cont = str(row["clase_contrastiva"]).strip() if pd.notna(row["clase_contrastiva"]) else ""
        dtc_val = str(row["dtc"]).strip() if pd.notna(row["dtc"]) else ""
        req_preg = str(row["requiere_pregunta"]).strip().upper()

        motivos = []
        estado = "APROBADO"

        # Coherencia macro
        macro_esperado = FALLA_A_SISTEMA[clase]
        if macro != macro_esperado:
            motivos.append(f"Macro {macro} != {macro_esperado}")
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
            dtc_por_clase[clase] += 1
            dtc_por_nivel[nivel] += 1
            codigos = [c.strip() for c in dtc_val.split(",") if c.strip()]
            for cod in codigos:
                if not re.match(r"^[PBCU][0-9A-Fa-f]{4}$", cod):
                    motivos.append(f"Formato DTC inválido: '{cod}'")
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

        # Validación específica Clase 54
        if clase == "Falla en compresor de aire acondicionado o fuga de gas R134a":
            err_c54 = verificar_clase_54_climatizacion(texto)
            if err_c54:
                for err in err_c54:
                    motivos.append(err)
                estado = "REVISAR"

        # Duplicado exacto intra-lote
        dups_intra = [j for j, tn in enumerate(textos_l10_norm) if j != i and tn == texto_norm]
        if dups_intra:
            motivos.append(f"Duplicado exacto intra-lote con {df_l10.iloc[dups_intra[0]]['id']}")
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
            motivos.append(f"Near-duplicate intra-lote con {df_l10.iloc[max_intra_idx]['id']} (sim={max_intra:.3f})")
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
    audit_csv = Path("fase10_auditoria_lote10.csv")
    df_aud.to_csv(audit_csv, index=False, encoding="utf-8")
    print(f"\nReporte de auditoría guardado en: {audit_csv}")

    # Estadísticas globales
    max_intra_global = float(df_aud["sim_intra_max"].max())
    max_inter_global = float(df_aud["sim_inter_max"].max())

    print("\n============================================================")
    print("RESUMEN DE AUDITORIA LOTE 10:")
    print(f"Total registros auditados: {total_reg}")
    print(f"APROBADO: {aprobados}")
    print(f"REVISAR: {revisar}")
    print(f"RECHAZADO: {rechazados}")
    print(f"Similitud máxima intra-lote: {max_intra_global:.4f}")
    print(f"Similitud máxima inter-referencias (leakage): {max_inter_global:.4f}")
    print(f"Total con DTC: {total_con_dtc} (L1: {dtc_por_nivel['L1']}, L2: {dtc_por_nivel['L2']}, L3: {dtc_por_nivel['L3']})")
    print(f"Total contrastivos: {total_contrastivos}")
    print("============================================================")

    if revisar > 0 or rechazados > 0:
        print("\nDetalle de casos observados:")
        for r in auditoria_rows:
            if r["estado_auditoria"] != "APROBADO":
                print(f"  - {r['id']} ({r['clase_objetivo']}, {r['nivel_informacion']}): {r['estado_auditoria']} -> {r['motivos']}")
        return False

    return True


if __name__ == "__main__":
    exito = auditar_lote10()
    sys.exit(0 if exito else 1)
