"""
Auditoría exhaustiva de Fase 10 Lote 07 (TRANSMISION) para CarBot.
Verifica 320 registros de Clases 34 a 41 contra todas las restricciones:
estructura, coherencia técnica, DTC, niveles L1/L2/L3, duplicados intra e inter-lotes,
near-duplicates, contaminación contra Lotes 1-6/TRAIN/DEV/TEST/G1/G2/FIELD60, contrastivos,
y validación específica de aislamiento entre arquitecturas (CVT vs DSG vs Robotizada vs Manual).
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


def verificar_arquitectura(texto: str, clase: str):
    """
    Validación de arquitectura para detectar mezclas técnicas indebidas:
    - CVT: variador, poleas cónicas, pushbelt, faja metálica de empuje.
    - DSG: doble embrague concéntrico/paralelo, mecatrónica DQ200/250, embragues K1/K2.
    - Robotizada: robot actuador electrohidráulico sobre caja manual monopunto (Dualogic/I-Motion/Easytronic).
    - Manual pura: disco único, bombín/bomba, pedal de embrague, collarín mecánico, horquilla, caja de engranajes.
    """
    tn = normalizar_texto(texto)
    errores = []

    es_manual = clase in [
        "Disco de embrague desgastado o patinando",
        "Falla en bombin o bomba hidraulica de embrague",
        "Rodajes de caja mecanica o diferencial gastados",
        "Desgaste en collarin de empuje o crapodina de embrague",
        "Rodajes de transmision manual o eje primario gastados",
    ]

    # Regla 1: Cajas manuales puras no deben tener componentes exclusivos de CVT, DSG ni robotizadas
    if es_manual:
        if any(w in tn for w in ["variador", "pushbelt", "polea primaria", "polea secundaria", "ns 2", "ns 3"]):
            errores.append("Componente de CVT en caja manual pura")
        if any(w in tn for w in ["dq200", "dq250", "dq381", "embrague k1", "embrague k2", "mecatronica"]):
            errores.append("Componente de DSG en caja manual pura")
        if any(w in tn for w in ["dualogic", "i motion", "easytronic", "hacer controlar cambio", "tutela cs speed"]):
            errores.append("Componente de robotizada en caja manual pura")

    # Regla 2: En CVT o DSG el conductor no tiene pedal de embrague
    if clase == "Sobrecalentamiento o solenoides en caja automatica CVT / DSG":
        # No mezclar variador con DSG internamente dentro del mismo escenario
        menciona_cvt = any(w in tn for w in ["cvt", "variador", "polea", "pushbelt", "jatco", "ns 2", "ns 3"])
        menciona_dsg = any(w in tn for w in ["dsg", "dq200", "dq250", "k1", "k2", "mecatronica"])
        if menciona_cvt and menciona_dsg:
            errores.append("Mezcla híbrida inconsistente: componentes de CVT y DSG combinados en el mismo texto")
        if "pedal de embrague" in tn:
            errores.append("Pedal de embrague atribuido a caja automática CVT/DSG")

    # Regla 3: En Robotizada (monodisco con robot) no debe haber componentes de CVT ni doble embrague DSG
    if clase == "Falla en caja robotizada Dualogic / I-Motion / Easytronic (Fiat / VW)":
        if any(w in tn for w in ["variador", "pushbelt", "polea cónica", "cvt"]):
            errores.append("Componente de CVT en caja robotizada")
        if any(w in tn for w in ["dq200", "dq250", "k1 y k2", "doble embrague"]):
            errores.append("Componente de DSG doble embrague en caja robotizada monopunto")
        if "pedal de embrague" in tn:
            errores.append("Pedal de embrague atribuido a caja robotizada (no posee pedal físico)")

    return errores


def main():
    lote07_path = Path("dataset_fase10_lote_07.csv")
    print(f"=== INICIANDO AUDITORIA LOTE 07: {lote07_path} ===")

    # 1. UTF-8 check
    try:
        raw_bytes = lote07_path.read_bytes()
        raw_text = raw_bytes.decode("utf-8")
        print("[OK] Codificación UTF-8 válida.")
    except Exception as e:
        print(f"[ERROR] Decodificación UTF-8 falló: {e}")
        return

    df_l7 = pd.read_csv(lote07_path)
    total_reg = len(df_l7)
    print(f"Total registros Lote 07: {total_reg}")
    assert total_reg == 320, f"Error: esperados 320, encontrados {total_reg}"

    # 2. Estructura de columnas
    cols_esperadas = [
        "id", "id_grupo", "clase_objetivo", "macro_sistema", "nivel_informacion",
        "texto_usuario", "tipo_lenguaje", "condicion_operacion", "sintomas_presentes",
        "sintomas_negados", "dtc", "requiere_pregunta", "es_contrastivo",
        "clase_contrastiva", "fuente", "observaciones"
    ]
    assert list(df_l7.columns) == cols_esperadas, f"Columnas no coinciden: {df_l7.columns}"
    print("[OK] Estructura de 16 columnas canónicas verificada.")

    # 3. Clases canónicas
    clases_validas = set(FALLA_A_SISTEMA.keys())
    assert len(clases_validas) == 61, f"Taxonomía debe tener 61 clases, tiene {len(clases_validas)}"

    clases_l07_esperadas = [
        "Disco de embrague desgastado o patinando",
        "Falla en bombin o bomba hidraulica de embrague",
        "Falta o degradacion de aceite de caja de cambios",
        "Rodajes de caja mecanica o diferencial gastados",
        "Sobrecalentamiento o solenoides en caja automatica CVT / DSG",
        "Falla en caja robotizada Dualogic / I-Motion / Easytronic (Fiat / VW)",
        "Desgaste en collarin de empuje o crapodina de embrague",
        "Rodajes de transmision manual o eje primario gastados"
    ]

    for c in clases_l07_esperadas:
        assert c in clases_validas, f"Clase no canónica: {c}"
        assert FALLA_A_SISTEMA[c] == "TRANSMISION", f"Macro no es TRANSMISION para {c}"
    print("[OK] Las 8 clases objetivo pertenecen exactamente a las 61 canónicas (Macro: TRANSMISION).")

    # 4. Distribución de clases y niveles
    conteo_clases = df_l7["clase_objetivo"].value_counts().to_dict()
    for c in clases_l07_esperadas:
        cant = conteo_clases.get(c, 0)
        assert cant == 40, f"Clase {c} tiene {cant} != 40 registros"
    print("[OK] Cada una de las 8 clases tiene exactamente 40 registros.")

    niveles_conteo = df_l7["nivel_informacion"].value_counts().to_dict()
    assert niveles_conteo.get("L1") == 80, f"L1 total {niveles_conteo.get('L1')} != 80"
    assert niveles_conteo.get("L2") == 120, f"L2 total {niveles_conteo.get('L2')} != 120"
    assert niveles_conteo.get("L3") == 120, f"L3 total {niveles_conteo.get('L3')} != 120"
    print(f"[OK] Distribución de niveles: L1={niveles_conteo['L1']}, L2={niveles_conteo['L2']}, L3={niveles_conteo['L3']}.")

    # Distribución de niveles por clase
    for c in clases_l07_esperadas:
        sub_c = df_l7[df_l7["clase_objetivo"] == c]
        sub_niv = sub_c["nivel_informacion"].value_counts().to_dict()
        assert sub_niv.get("L1") == 10, f"Clase {c} tiene {sub_niv.get('L1')} L1 != 10"
        assert sub_niv.get("L2") == 15, f"Clase {c} tiene {sub_niv.get('L2')} L2 != 15"
        assert sub_niv.get("L3") == 15, f"Clase {c} tiene {sub_niv.get('L3')} L3 != 15"
    print("[OK] Cada una de las 8 clases tiene exactamente 10 L1, 15 L2, 15 L3.")

    # 5. Cargar referencias para duplicados y leakage
    print("\nCargando fuentes de referencia para auditoría de duplicados y leakage...")
    df_l1 = pd.read_csv("dataset_fase10_lote_01.csv")
    df_l2 = pd.read_csv("dataset_fase10_lote_02.csv")
    df_l3 = pd.read_csv("dataset_fase10_lote_03.csv")
    df_l4 = pd.read_csv("dataset_fase10_lote_04.csv")
    df_l5 = pd.read_csv("dataset_fase10_lote_05.csv")
    df_l6 = pd.read_csv("dataset_fase10_lote_06.csv")
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

    textos_l7 = [str(t) for t in df_l7["texto_usuario"].tolist()]
    textos_l7_norm = [normalizar_texto(t) for t in textos_l7]

    ref_keys = list(corpus_ref.keys())
    ref_origins = [corpus_ref[k][0] for k in ref_keys]
    textos_ref = [corpus_ref[k][1] for k in ref_keys]
    textos_ref_norm = [normalizar_texto(t) for t in textos_ref]

    # TF-IDF para similitud
    vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=1, sublinear_tf=True)
    vectorizer.fit(textos_l7_norm + textos_ref_norm)
    mat_l7 = vectorizer.transform(textos_l7_norm)
    mat_ref = vectorizer.transform(textos_ref_norm)

    sim_intra = cosine_similarity(mat_l7, mat_l7)
    np.fill_diagonal(sim_intra, 0.0)

    sim_inter = cosine_similarity(mat_l7, mat_ref)

    # 6. Evaluación individual detallada
    auditoria_rows = []
    aprobados = 0
    revisar = 0
    rechazados = 0
    total_con_dtc = 0
    total_contrastivos = 0

    dtc_por_clase = {c: 0 for c in clases_l07_esperadas}
    dtc_por_nivel = {"L1": 0, "L2": 0, "L3": 0}

    for i, row in df_l7.iterrows():
        reg_id = str(row["id"])
        clase = str(row["clase_objetivo"])
        macro = str(row["macro_sistema"])
        nivel = str(row["nivel_informacion"])
        texto = str(row["texto_usuario"])
        texto_norm = textos_l7_norm[i]
        es_cont = str(row["es_contrastivo"]).strip().upper()
        clase_cont = str(row["clase_contrastiva"]).strip() if pd.notna(row["clase_contrastiva"]) else ""
        dtc_val = str(row["dtc"]).strip() if pd.notna(row["dtc"]) else ""
        req_preg = str(row["requiere_pregunta"]).strip().upper()

        motivos = []
        estado = "APROBADO"

        # Coherencia macro
        if macro != "TRANSMISION":
            motivos.append(f"Macro {macro} != TRANSMISION")
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
            if not re.match(r"^[PBCU][0-9A-Fa-f]{4}$", dtc_val):
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

        # Validación específica de Arquitectura (Sección 27)
        err_arq = verificar_arquitectura(texto, clase)
        if err_arq:
            for err in err_arq:
                motivos.append(f"Arquitectura: {err}")
            estado = "RECHAZADO"

        # Duplicado exacto intra-lote
        dups_intra = [j for j, tn in enumerate(textos_l7_norm) if j != i and tn == texto_norm]
        if dups_intra:
            motivos.append(f"Duplicado exacto intra-lote con {df_l7.iloc[dups_intra[0]]['id']}")
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
            motivos.append(f"Near-duplicate intra-lote con {df_l7.iloc[max_intra_idx]['id']} (sim={max_intra:.3f})")
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
    audit_csv = Path("fase10_auditoria_lote07.csv")
    df_aud.to_csv(audit_csv, index=False, encoding="utf-8")
    print(f"\n[OK] Auditoría guardada en {audit_csv}")

    # Resumen
    print("\n" + "="*50)
    print("RESUMEN DE AUDITORÍA AUTOMÁTICA LOTE 07")
    print("="*50)
    print(f"Total registros: {total_reg}")
    print(f"APROBADO: {aprobados}")
    print(f"REVISAR:  {revisar}")
    print(f"RECHAZADO: {rechazados}")
    print(f"\nCasos con DTC total: {total_con_dtc}")
    print(f"DTC L1: {dtc_por_nivel['L1']}")
    print(f"DTC L2: {dtc_por_nivel['L2']}")
    print(f"DTC L3: {dtc_por_nivel['L3']}")
    print(f"L2/L3 sin DTC: {(120 + 120) - total_con_dtc}")

    print("\nDTC por clase:")
    for c, cnt in dtc_por_clase.items():
        print(f"  - {c}: {cnt}")

    print(f"\nCasos contrastivos: {total_contrastivos}")
    max_sim_intra_global = float(np.max(sim_intra))
    max_sim_inter_global = float(np.max(sim_inter))
    print(f"Similitud máxima intra-lote: {max_sim_intra_global:.4f}")
    print(f"Similitud máxima inter-referencias: {max_sim_inter_global:.4f}")

    if revisar == 0 and rechazados == 0:
        print("\n>>> RESULTADO FINAL: LOTE 07 100% APROBADO <<<")
    else:
        print(f"\n>>> ATENCION: Hay {revisar} en REVISAR y {rechazados} RECHAZADOS <<<")


if __name__ == "__main__":
    main()
