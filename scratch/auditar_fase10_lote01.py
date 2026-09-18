"""
Auditoría exhaustiva de Fase 10 Lote 01.
Evalúa aspectos estructurales, semánticos, contrastivos, DTC, duplicados,
near-duplicates y contaminación/leakage contra TRAIN y todos los benchmarks.
"""

import csv
import hashlib
import importlib.util
import re
import sys
import unicodedata
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

# Asegurar backend en sys.path
sys.path.insert(0, str(Path("backend").resolve()))
from src.core.diagnostico.taxonomia_sistemas import FALLA_A_SISTEMA, TAXONOMIA_MACRO_SISTEMAS

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
    csv_path = Path("dataset_fase10_lote_01.csv")
    print(f"Cargando {csv_path}...")
    
    # 1. Validación de UTF-8 y lectura
    try:
        raw_bytes = csv_path.read_bytes()
        raw_text = raw_bytes.decode("utf-8")
        print("[OK] Archivo codificado correctamente en UTF-8.")
    except Exception as e:
        print(f"[ERROR] Error de decodificación UTF-8: {e}")
        return

    df = pd.read_csv(csv_path)
    total_reg = len(df)
    print(f"Total registros cargados: {total_reg}")

    # Columnas esperadas
    cols_esperadas = [
        "id", "id_grupo", "clase_objetivo", "macro_sistema", "nivel_informacion",
        "texto_usuario", "tipo_lenguaje", "condicion_operacion", "sintomas_presentes",
        "sintomas_negados", "dtc", "requiere_pregunta", "es_contrastivo",
        "clase_contrastiva", "fuente", "observaciones"
    ]
    cols_actuales = df.columns.tolist()
    diff_cols = set(cols_esperadas) ^ set(cols_actuales)
    if not diff_cols:
        print("[OK] Columnas estructurales conformes (16/16).")
    else:
        print(f"[ALERTA] Discrepancia en columnas: {diff_cols}")

    # Cargar fuentes de referencia para leakage
    print("Cargando fuentes de referencia para detección de leakage...")
    df_train = pd.read_csv("machine_learning/data/dataset_sintomas_limpio.csv")
    dev_60 = cargar_py_benchmark("machine_learning/data/benchmark_dev_60_casos.py", "CASOS_DEV_60")
    test_100 = cargar_py_benchmark("machine_learning/data/benchmark_test_ciego_100.py", "BENCHMARK_TEST_CIEGO_100")
    g1 = cargar_py_benchmark("scripts/benchmark_v4_g1_casos.py", "BENCHMARK_V4_G1_CASOS")
    g2 = cargar_py_benchmark("scripts/benchmark_v4_g2_casos.py", "BENCHMARK_V4_G2_CASOS")
    df_field60 = pd.read_csv("machine_learning/data/casos_reales_mecanicos_evaluacion.csv")

    corpus_ref = {}
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

    print(f"Total referencias históricas para cotejo: {len(corpus_ref)}")

    # Vectorización TF-IDF combinada para similitud coseno
    textos_lote = [str(t) for t in df["texto_usuario"].tolist()]
    textos_lote_norm = [normalizar_texto(t) for t in textos_lote]
    
    ref_keys = list(corpus_ref.keys())
    ref_origins = [corpus_ref[k][0] for k in ref_keys]
    textos_ref = [corpus_ref[k][1] for k in ref_keys]
    textos_ref_norm = [normalizar_texto(t) for t in textos_ref]

    vectorizer = TfidfVectorizer(ngram_range=(1, 2), min_df=1, sublinear_tf=True)
    todos_textos = textos_lote_norm + textos_ref_norm
    vectorizer.fit(todos_textos)

    mat_lote = vectorizer.transform(textos_lote_norm)
    mat_ref = vectorizer.transform(textos_ref_norm)

    # Similitud intra-lote
    sim_intra = cosine_similarity(mat_lote, mat_lote)
    np.fill_diagonal(sim_intra, 0.0)

    # Similitud contra referencias históricas
    sim_inter = cosine_similarity(mat_lote, mat_ref)

    # Catálogo de 61 clases
    clases_validas = set(FALLA_A_SISTEMA.keys())

    # Patrones de plantillas sintéticas
    patrones_plantilla = [
        r"comenzó a motor tiembla",
        r"comenzo a motor tiembla",
        r"comenzó a ralenti",
        r"comenzo a ralenti",
        r"comenzó a se queda sin",
        r"comenzo a se queda sin",
        r"comenzó a sale humo",
        r"comenzo a sale humo",
        r"comenzó a rpm suben",
        r"comenzo a rpm suben",
        r"se siente que el carro comenzó a",
        r"cuando voy al acelerar fuerte",
        r"cuando está al acelerar fuerte",
        r"cuando voy en semaforo",
        r"al manejar despues de manejar un rato",
        r"al manejar despues de varias horas",
        r"al manejar despues de calentar",
    ]

    # Evaluación registro por registro
    auditoria_rows = []
    
    conteo_estados = {"APROBADO": 0, "REVISAR": 0, "RECHAZADO": 0}

    for i, row in df.iterrows():
        reg_id = str(row["id"])
        clase = str(row["clase_objetivo"])
        macro = str(row["macro_sistema"])
        nivel = str(row["nivel_informacion"])
        texto = str(row["texto_usuario"])
        texto_norm = textos_lote_norm[i]
        es_cont = str(row["es_contrastivo"]).strip().upper()
        clase_cont = str(row["clase_contrastiva"]) if pd.notna(row["clase_contrastiva"]) else ""
        dtc_val = str(row["dtc"]).strip() if pd.notna(row["dtc"]) else ""
        req_preg = str(row["requiere_pregunta"]).strip().upper()
        sint_neg = str(row["sintomas_negados"]).strip() if pd.notna(row["sintomas_negados"]) else ""
        sint_pres = str(row["sintomas_presentes"]).strip() if pd.notna(row["sintomas_presentes"]) else ""

        motivos = []
        recomendaciones = []
        estado = "APROBADO"

        # 1. Clase objetivo válida
        if clase not in clases_validas:
            motivos.append(f"Clase objetivo '{clase}' no pertenece a la taxonomía canónica de 61 clases.")
            estado = "RECHAZADO"

        # 2. Macro-sistema coherente
        macro_esperado = FALLA_A_SISTEMA.get(clase, "")
        if macro != macro_esperado:
            motivos.append(f"Macro-sistema '{macro}' no coincide con el esperado '{macro_esperado}'.")
            if estado != "RECHAZADO":
                estado = "REVISAR"

        # 3. Nivel de información
        if nivel not in ("L1", "L2", "L3"):
            motivos.append(f"Nivel '{nivel}' desconocido.")
            estado = "RECHAZADO"

        # 4. Requiere pregunta coherencia con nivel
        if nivel == "L1" and req_preg != "SI":
            motivos.append("Registro L1 con requiere_pregunta != 'SI'. En L1 siempre se debe interrogar.")
            if estado != "RECHAZADO":
                estado = "REVISAR"
        elif nivel in ("L2", "L3") and req_preg == "SI" and not dtc_val and not es_cont == "SI":
            pass

        # 5. Contrastivo coherencia
        if es_cont == "SI":
            if not clase_cont:
                motivos.append("Marcado como contrastivo (SI) pero clase_contrastiva está vacía.")
                if estado != "RECHAZADO":
                    estado = "REVISAR"
            elif clase_cont not in clases_validas:
                motivos.append(f"Clase contrastiva '{clase_cont}' no pertenece a las 61 clases.")
                estado = "RECHAZADO"
            elif clase_cont == clase:
                motivos.append("Clase contrastiva es idéntica a la clase objetivo.")
                if estado != "RECHAZADO":
                    estado = "REVISAR"
        elif es_cont == "NO":
            if clase_cont:
                motivos.append(f"Marcado no contrastivo (NO) pero contiene clase_contrastiva '{clase_cont}'.")
                if estado != "RECHAZADO":
                    estado = "REVISAR"

        # 6. DTC coherencia
        if dtc_val:
            if not re.match(r"^[PBCU]\d{4}$", dtc_val):
                motivos.append(f"Formato DTC inválido: '{dtc_val}'.")
                if estado != "RECHAZADO":
                    estado = "REVISAR"
            if nivel == "L1":
                motivos.append(f"Registro L1 incluye DTC '{dtc_val}'. Un síntoma inicial L1 no debería traer DTC.")
                if estado != "RECHAZADO":
                    estado = "REVISAR"

        # 7. Duplicados exactos dentro del lote
        indices_dup = [j for j, tn in enumerate(textos_lote_norm) if j != i and tn == texto_norm]
        if indices_dup:
            motivos.append(f"Duplicado exacto/normalizado de fila {df.iloc[indices_dup[0]]['id']}.")
            estado = "RECHAZADO"

        # 8. Similitud máxima intra-lote
        max_intra_sim = np.max(sim_intra[i])
        max_intra_idx = np.argmax(sim_intra[i])
        
        # 9. Similitud máxima inter-referencias (leakage)
        max_inter_sim = np.max(sim_inter[i])
        max_inter_idx = np.argmax(sim_inter[i])
        ref_key = ref_keys[max_inter_idx]
        ref_origin, ref_text = corpus_ref[ref_key]

        # Determinar máxima similitud global
        if max_inter_sim >= max_intra_sim:
            sim_maxima = round(float(max_inter_sim), 4)
            origen_sim = f"{ref_origin} ({ref_key})"
            if max_inter_sim > 0.88:
                motivos.append(f"Posible leakage con {ref_origin} (similitud {sim_maxima:.2f}): '{ref_text[:60]}...'")
                if max_inter_sim > 0.95:
                    estado = "RECHAZADO"
                elif estado != "RECHAZADO":
                    estado = "REVISAR"
        else:
            sim_maxima = round(float(max_intra_sim), 4)
            origen_sim = f"LOTE_01 ({df.iloc[max_intra_idx]['id']})"
            if max_intra_sim > 0.90:
                motivos.append(f"Paráfrasis casi idéntica a {df.iloc[max_intra_idx]['id']} (similitud {sim_maxima:.2f}).")
                if estado != "RECHAZADO":
                    estado = "REVISAR"

        # 10. Detección de artefactos de plantilla sintética
        for pat in patrones_plantilla:
            if re.search(pat, texto, re.IGNORECASE):
                motivos.append(f"Artefacto de plantilla sintética detectado ('{pat}'). Redacción forzada o agramatical.")
                if estado != "RECHAZADO":
                    estado = "REVISAR"
                break

        # 11. Coherencia de negaciones en texto
        if sint_neg:
            partes_neg = [p.strip().lower() for p in sint_neg.split("|")]
            for pn in partes_neg:
                if pn in ("no se calienta", "sin sobrecalentamiento"):
                    if "calienta" in texto.lower() and "no" not in texto.lower():
                        motivos.append("Contradicción en negación de temperatura.")
                        if estado != "RECHAZADO":
                            estado = "REVISAR"

        # Recomendaciones de resolución
        if estado == "RECHAZADO":
            recomendacion = "Excluir del dataset maestro o reescribir integralmente."
        elif estado == "REVISAR":
            recomendacion = "Corregir redacción / plantilla sintética / desambiguar antes de incorporar."
        else:
            recomendacion = "Aprobado para preselección en corpus maestro Fase 10."

        conteo_estados[estado] += 1

        auditoria_rows.append({
            "id": reg_id,
            "estado": estado,
            "motivos": " | ".join(motivos) if motivos else "Sin observaciones técnicas.",
            "similitud_maxima": sim_maxima,
            "origen_similitud": origen_sim,
            "recomendacion": recomendacion
        })

    # Guardar fase10_auditoria_lote01.csv
    out_csv = Path("fase10_auditoria_lote01.csv")
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "id", "estado", "motivos", "similitud_maxima", "origen_similitud", "recomendacion"
        ])
        writer.writeheader()
        writer.writerows(auditoria_rows)

    print(f"\n[OK] Auditoría completada y guardada en {out_csv}.")
    print(f"Resumen de evaluación ({total_reg} casos):")
    print(f"  - APROBADO:  {conteo_estados['APROBADO']} ({conteo_estados['APROBADO']/total_reg*100:.1f}%)")
    print(f"  - REVISAR:   {conteo_estados['REVISAR']} ({conteo_estados['REVISAR']/total_reg*100:.1f}%)")
    print(f"  - RECHAZADO: {conteo_estados['RECHAZADO']} ({conteo_estados['RECHAZADO']/total_reg*100:.1f}%)")

if __name__ == "__main__":
    main()
