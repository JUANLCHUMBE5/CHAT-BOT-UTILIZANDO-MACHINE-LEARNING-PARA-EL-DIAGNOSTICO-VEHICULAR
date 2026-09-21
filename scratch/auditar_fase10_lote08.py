"""
Auditoría exhaustiva de Fase 10 Lote 08 (SUSPENSION_CHASIS) para CarBot.
Verifica 200 registros de Clases 42 a 46 contra todas las restricciones:
estructura, coherencia técnica, DTC, niveles L1/L2/L3, duplicados intra e inter-lotes,
near-duplicates, contaminación contra Lotes 1-7/TRAIN/DEV/TEST/G1/G2/FIELD60, contrastivos,
validación de condición operacional en L2/L3, y validación de arquitectura en dirección (Secciones 27 y 28).
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


def verificar_arquitectura_direccion(texto: str, clase: str):
    """
    Validación de arquitectura de dirección (Sección 28):
    - No atribuir fugas de líquido hidráulico a cremalleras EPS puramente eléctricas.
    - Hidráulica pura: usa bomba mecánica, fluido ATF/Dexron/CHF, retenes y fuelles con aceite.
    - EPS eléctrica pura: motor eléctrico acoplado a columna o cremallera, sin líquido hidráulico.
    """
    tn = normalizar_texto(texto)
    errores = []

    if clase == "Cremallera de direccion asistida con holgura o fuga":
        es_eps_electrico = any(w in tn for w in [
            "eps", "electroasistida", "electrico", "motorreductor", "sensor de torque", "c1511", "c1512", "c1532"
        ])
        es_hidraulico = any(w in tn for w in [
            "hidraulica", "atf", "dexron", "chf", "fuga de aceite", "fuga de liquido", "gotea aceite", "charco de liquido"
        ])
        if es_eps_electrico and any(w in tn for w in ["fuga de aceite", "fuga de liquido", "atf", "dexron"]):
            # A menos que sea explícitamente electrohidráulica (EHPS)
            if "ehps" not in tn and "electrohidraulica" not in tn:
                errores.append("Error de arquitectura: Fuga de fluido hidráulico atribuida a dirección electroasistida EPS pura")

    return errores


def verificar_condicion_operacional(texto: str, nivel: str, clase: str):
    """
    Validación de condición operacional (Sección 27):
    En L2 y L3 no se admiten síntomas 'desnudos' sin contexto operativo
    (debe existir velocidad, curva, aceleración, bache, frenado o inspección física).
    """
    tn = normalizar_texto(texto)
    errores = []

    if nivel in ["L2", "L3"]:
        tiene_contexto = any(w in tn for w in [
            "km h", "kmh", "velocidad", "curva", "recta", "aceler", "fren", "bache",
            "rompemuelle", "empedrado", "adoquin", "neutro", "embrague", "parado",
            "ralenti", "inspeccion", "desarme", "elevador", "fosa", "banco", "medicion",
            "micrometro", "reloj", "holgura", "mm", "dba", "temperatura", "pirómetro",
            "alineacion", "balanceo", "volante", "timon", "fuelle", "guardapolvo",
            "carretera", "autopista", "hueco", "zanja", "vereda", "loma", "calle", "pista",
            "trafico", "giro", "girar", "girando", "viraje", "doblar", "torque", "nm",
            "grado", "grados", "convergencia", "divergencia", "angulo", "resorte", "banda",
            "tacos", "feathering", "scanner", "escaner", "dtc", "taller", "semieje",
            "palier", "tulipan", "vastago", "traccion", "columna", "cabina", "asfalto",
            "polvo", "grasa", "aceite", "reten", "desgaste", "resistencia"
        ])
        if not tiene_contexto:
            errores.append(f"Falta condición operacional o evidencia técnica en {nivel}")

    return errores


def main():
    lote08_path = Path("dataset_fase10_lote_08.csv")
    print(f"=== INICIANDO AUDITORIA LOTE 08: {lote08_path} ===")

    # 1. UTF-8 check
    try:
        raw_bytes = lote08_path.read_bytes()
        raw_text = raw_bytes.decode("utf-8")
        print("[OK] Codificación UTF-8 válida.")
    except Exception as e:
        print(f"[ERROR] Decodificación UTF-8 falló: {e}")
        return

    df_l8 = pd.read_csv(lote08_path)
    total_reg = len(df_l8)
    print(f"Total registros Lote 08: {total_reg}")
    assert total_reg == 200, f"Error: esperados 200, encontrados {total_reg}"

    # 2. Estructura de columnas
    cols_esperadas = [
        "id", "id_grupo", "clase_objetivo", "macro_sistema", "nivel_informacion",
        "texto_usuario", "tipo_lenguaje", "condicion_operacion", "sintomas_presentes",
        "sintomas_negados", "dtc", "requiere_pregunta", "es_contrastivo",
        "clase_contrastiva", "fuente", "observaciones"
    ]
    assert list(df_l8.columns) == cols_esperadas, f"Columnas no coinciden: {df_l8.columns}"
    print("[OK] Estructura de 16 columnas canónicas verificada.")

    # 3. Clases canónicas
    clases_validas = set(FALLA_A_SISTEMA.keys())
    assert len(clases_validas) == 61, f"Taxonomía debe tener 61 clases, tiene {len(clases_validas)}"

    clases_l08_esperadas = [
        "Amortiguadores reventados o bujes de suspension gastados",
        "Juntas homocineticas o palieres danados",
        "Llantas desbalanceadas o desalineadas",
        "Cremallera de direccion asistida con holgura o fuga",
        "Rodamiento de maza o rodaje de rueda picado (zumbido de rodadura)"
    ]

    for c in clases_l08_esperadas:
        assert c in clases_validas, f"Clase no canónica: {c}"
        assert FALLA_A_SISTEMA[c] == "SUSPENSION_CHASIS", f"Macro no es SUSPENSION_CHASIS para {c}"
    print("[OK] Las 5 clases objetivo pertenecen exactamente a las 61 canónicas (Macro: SUSPENSION_CHASIS).")

    # 4. Distribución de clases y niveles
    conteo_clases = df_l8["clase_objetivo"].value_counts().to_dict()
    for c in clases_l08_esperadas:
        cant = conteo_clases.get(c, 0)
        assert cant == 40, f"Clase {c} tiene {cant} != 40 registros"
    print("[OK] Cada una de las 5 clases tiene exactamente 40 registros.")

    niveles_conteo = df_l8["nivel_informacion"].value_counts().to_dict()
    assert niveles_conteo.get("L1") == 50, f"L1 total {niveles_conteo.get('L1')} != 50"
    assert niveles_conteo.get("L2") == 75, f"L2 total {niveles_conteo.get('L2')} != 75"
    assert niveles_conteo.get("L3") == 75, f"L3 total {niveles_conteo.get('L3')} != 75"
    print(f"[OK] Distribución de niveles: L1={niveles_conteo['L1']}, L2={niveles_conteo['L2']}, L3={niveles_conteo['L3']}.")

    # Distribución de niveles por clase
    for c in clases_l08_esperadas:
        sub_c = df_l8[df_l8["clase_objetivo"] == c]
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

    textos_l8 = [str(t) for t in df_l8["texto_usuario"].tolist()]
    textos_l8_norm = [normalizar_texto(t) for t in textos_l8]

    ref_keys = list(corpus_ref.keys())
    ref_origins = [corpus_ref[k][0] for k in ref_keys]
    textos_ref = [corpus_ref[k][1] for k in ref_keys]
    textos_ref_norm = [normalizar_texto(t) for t in textos_ref]

    # TF-IDF para similitud
    vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=1, sublinear_tf=True)
    vectorizer.fit(textos_l8_norm + textos_ref_norm)
    mat_l8 = vectorizer.transform(textos_l8_norm)
    mat_ref = vectorizer.transform(textos_ref_norm)

    sim_intra = cosine_similarity(mat_l8, mat_l8)
    np.fill_diagonal(sim_intra, 0.0)

    sim_inter = cosine_similarity(mat_l8, mat_ref)

    # 6. Evaluación individual detallada
    auditoria_rows = []
    aprobados = 0
    revisar = 0
    rechazados = 0
    total_con_dtc = 0
    total_contrastivos = 0

    dtc_por_clase = {c: 0 for c in clases_l08_esperadas}
    dtc_por_nivel = {"L1": 0, "L2": 0, "L3": 0}

    for i, row in df_l8.iterrows():
        reg_id = str(row["id"])
        clase = str(row["clase_objetivo"])
        macro = str(row["macro_sistema"])
        nivel = str(row["nivel_informacion"])
        texto = str(row["texto_usuario"])
        texto_norm = textos_l8_norm[i]
        es_cont = str(row["es_contrastivo"]).strip().upper()
        clase_cont = str(row["clase_contrastiva"]).strip() if pd.notna(row["clase_contrastiva"]) else ""
        dtc_val = str(row["dtc"]).strip() if pd.notna(row["dtc"]) else ""
        req_preg = str(row["requiere_pregunta"]).strip().upper()

        motivos = []
        estado = "APROBADO"

        # Coherencia macro
        if macro != "SUSPENSION_CHASIS":
            motivos.append(f"Macro {macro} != SUSPENSION_CHASIS")
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

        # Validación especial de Condición Operacional (Sección 27)
        err_cond = verificar_condicion_operacional(texto, nivel, clase)
        if err_cond:
            for err in err_cond:
                motivos.append(f"Condición: {err}")
            estado = "REVISAR"

        # Validación específica de Arquitectura de Dirección (Sección 28)
        err_arq = verificar_arquitectura_direccion(texto, clase)
        if err_arq:
            for err in err_arq:
                motivos.append(f"Arquitectura: {err}")
            estado = "RECHAZADO"

        # Duplicado exacto intra-lote
        dups_intra = [j for j, tn in enumerate(textos_l8_norm) if j != i and tn == texto_norm]
        if dups_intra:
            motivos.append(f"Duplicado exacto intra-lote con {df_l8.iloc[dups_intra[0]]['id']}")
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
            motivos.append(f"Near-duplicate intra-lote con {df_l8.iloc[max_intra_idx]['id']} (sim={max_intra:.3f})")
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
    audit_csv = Path("fase10_auditoria_lote08.csv")
    df_aud.to_csv(audit_csv, index=False, encoding="utf-8")
    print(f"\n[OK] Auditoría guardada en {audit_csv}")

    # Resumen
    print("\n" + "="*50)
    print("RESUMEN DE AUDITORÍA AUTOMÁTICA LOTE 08")
    print("="*50)
    print(f"Total registros: {total_reg}")
    print(f"APROBADO: {aprobados}")
    print(f"REVISAR:  {revisar}")
    print(f"RECHAZADO: {rechazados}")
    print(f"\nCasos con DTC total: {total_con_dtc}")
    print(f"DTC L1: {dtc_por_nivel['L1']}")
    print(f"DTC L2: {dtc_por_nivel['L2']}")
    print(f"DTC L3: {dtc_por_nivel['L3']}")
    print(f"L2/L3 sin DTC: {(75 + 75) - total_con_dtc}")

    print("\nDTC por clase:")
    for c, cnt in dtc_por_clase.items():
        print(f"  - {c}: {cnt}")

    print(f"\nCasos contrastivos: {total_contrastivos}")
    max_sim_intra_global = float(np.max(sim_intra))
    max_sim_inter_global = float(np.max(sim_inter))
    print(f"Similitud máxima intra-lote: {max_sim_intra_global:.4f}")
    print(f"Similitud máxima inter-referencias: {max_sim_inter_global:.4f}")

    if revisar == 0 and rechazados == 0:
        print("\n>>> RESULTADO FINAL: LOTE 08 100% APROBADO <<<")
    else:
        print(f"\n>>> ATENCION: Hay {revisar} en REVISAR y {rechazados} RECHAZADOS <<<")


if __name__ == "__main__":
    main()
