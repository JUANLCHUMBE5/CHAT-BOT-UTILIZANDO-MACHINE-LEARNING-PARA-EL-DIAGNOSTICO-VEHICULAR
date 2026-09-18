"""
Prototipo y validación del split TRAIN10 / DEV10.
Garantiza:
1. GroupSplit estricto (cero grupos compartidos).
2. 61 clases presentes tanto en TRAIN10 como en DEV10.
3. Proporción ~80% TRAIN10 y ~20% DEV10.
4. Distribución controlada L1, L2, L3 para sintéticos.
5. Cero leakage y cero intersección.
"""

import pandas as pd
import numpy as np
import unicodedata
import re
from sklearn.model_selection import StratifiedGroupKFold

PREFIJOS = re.compile(
    r"\b(amigo una consulta|tengo un problema con mi auto|tengo un problema|"
    r"resulta que en mi carro|resulta que|sabes que|mi carro presenta|"
    r"amigo mi auto presenta|maestro una consulta|buenas tardes mecanico|"
    r"en mi vehiculo noto que|hace dos dias noto que)\b"
)
SUFIJOS = re.compile(
    r"\b(ultimamente|desde ayer|en carabayllo|en la pista|en las mananas|"
    r"cuando voy manejando|cuando salgo a trabajar|al pasar un rompemuelles|"
    r"de la nada|al acelerar|al andar a \d+ km(?:/h| por hora)?)\b"
)


def norm_g(t: str) -> str:
    t = unicodedata.normalize("NFKD", str(t).lower())
    t = "".join(c for c in t if not unicodedata.combining(c))
    t = PREFIJOS.sub(" ", t)
    t = SUFIJOS.sub(" ", t)
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9 ]", " ", t)).strip()


def probar_split():
    df_orig = pd.read_csv("machine_learning/data/dataset_sintomas_limpio.csv")
    df_f10 = pd.read_csv("machine_learning/data/fase10/dataset_fase10_master_v1_1_2440.csv")

    # 1. Preparar original con metadatos
    df_orig_prep = pd.DataFrame()
    df_orig_prep["id"] = [f"ORIG-{i:04d}" for i in range(1, len(df_orig) + 1)]
    # Asignar grupos canónicos por raíz de síntoma + clase
    grupos_raw = df_orig.apply(lambda r: r["falla"] + "###" + norm_g(r["sintoma"]), axis=1)
    # Mapear a códigos de grupo G-ORIG-XXXX
    grp_map = {g: f"G-ORIG-{idx:04d}" for idx, g in enumerate(grupos_raw.unique(), 1)}
    df_orig_prep["id_grupo"] = grupos_raw.map(grp_map)
    df_orig_prep["clase_objetivo"] = df_orig["falla"]
    df_orig_prep["macro_sistema"] = df_orig["sistema"]
    df_orig_prep["nivel_informacion"] = "ORIGINAL_NO_ESTRATIFICADO"
    df_orig_prep["texto_usuario"] = df_orig["sintoma"]
    df_orig_prep["tipo_lenguaje"] = "COTIDIANO"
    df_orig_prep["condicion_operacion"] = "NO_REPORTA"
    df_orig_prep["sintomas_presentes"] = df_orig["sintoma"]
    df_orig_prep["sintomas_negados"] = "NO_REPORTA"
    df_orig_prep["dtc"] = df_orig["codigo_falla"].fillna("")
    df_orig_prep["requiere_pregunta"] = "NO"
    df_orig_prep["es_contrastivo"] = "NO"
    df_orig_prep["clase_contrastiva"] = ""
    df_orig_prep["fuente"] = "ORIGINAL"
    df_orig_prep["observaciones"] = "TRAIN_CANONICO_ORIGINAL"
    df_orig_prep["source_dataset"] = "dataset_sintomas_limpio.csv"
    df_orig_prep["source_row_id"] = [str(i) for i in range(len(df_orig))]
    df_orig_prep["source_type"] = "ORIGINAL"
    df_orig_prep["specificity_level"] = "ORIGINAL_NO_ESTRATIFICADO"
    df_orig_prep["synthetic_or_original"] = "ORIGINAL"

    # 2. Split Original usando StratifiedGroupKFold
    sgkf_orig = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=42)
    train_idx_orig, dev_idx_orig = next(sgkf_orig.split(df_orig_prep, df_orig_prep["clase_objetivo"], df_orig_prep["id_grupo"]))

    df_orig_train = df_orig_prep.iloc[train_idx_orig].copy()
    df_orig_dev = df_orig_prep.iloc[dev_idx_orig].copy()

    print("Split Original:")
    print(f"  TRAIN: {len(df_orig_train)} ({len(df_orig_train)/len(df_orig_prep)*100:.1f}%) | Clases: {df_orig_train['clase_objetivo'].nunique()}")
    print(f"  DEV:   {len(df_orig_dev)} ({len(df_orig_dev)/len(df_orig_prep)*100:.1f}%) | Clases: {df_orig_dev['clase_objetivo'].nunique()}")
    # Verificar grupos originales
    grps_orig_train = set(df_orig_train["id_grupo"])
    grps_orig_dev = set(df_orig_dev["id_grupo"])
    assert len(grps_orig_train.intersection(grps_orig_dev)) == 0, "Colisión de grupos en original!"

    # 3. Split Fase 10 estratificado por clase y nivel manteniendo id_grupo intacto
    # Para cada clase (40 casos: 10 L1, 15 L2, 15 L3), 80% a train (8 L1, 12 L2, 12 L3 = 32 casos), 20% a dev (2 L1, 3 L2, 3 L3 = 8 casos)
    np.random.seed(42)
    f10_train_ids = []
    f10_dev_ids = []

    for c in df_f10["clase_objetivo"].unique():
        sub_c = df_f10[df_f10["clase_objetivo"] == c]
        for niv, n_dev in [("L1", 2), ("L2", 3), ("L3", 3)]:
            sub_niv = sub_c[sub_c["nivel_informacion"] == niv]
            # Muestreo determinista con random_state
            dev_sub = sub_niv.sample(n=n_dev, random_state=42)
            train_sub = sub_niv.drop(dev_sub.index)

            f10_dev_ids.extend(dev_sub["id"].tolist())
            f10_train_ids.extend(train_sub["id"].tolist())

    df_f10_train = df_f10[df_f10["id"].isin(f10_train_ids)].copy()
    df_f10_dev = df_f10[df_f10["id"].isin(f10_dev_ids)].copy()

    print("\nSplit Fase 10:")
    print(f"  TRAIN: {len(df_f10_train)} ({len(df_f10_train)/len(df_f10)*100:.1f}%) | Clases: {df_f10_train['clase_objetivo'].nunique()}")
    print(f"    Niveles: {df_f10_train['nivel_informacion'].value_counts().to_dict()}")
    print(f"  DEV:   {len(df_f10_dev)} ({len(df_f10_dev)/len(df_f10)*100:.1f}%) | Clases: {df_f10_dev['clase_objetivo'].nunique()}")
    print(f"    Niveles: {df_f10_dev['nivel_informacion'].value_counts().to_dict()}")

    # Verificar grupos Fase 10
    grps_f10_train = set(df_f10_train["id_grupo"])
    grps_f10_dev = set(df_f10_dev["id_grupo"])
    assert len(grps_f10_train.intersection(grps_f10_dev)) == 0, "Colisión de grupos en Fase 10!"

    # 4. Combinar TRAIN10 y DEV10
    cols_comunes = list(df_f10.columns)
    df_train10 = pd.concat([df_orig_train[cols_comunes], df_f10_train[cols_comunes]], ignore_index=True)
    df_dev10 = pd.concat([df_orig_dev[cols_comunes], df_f10_dev[cols_comunes]], ignore_index=True)

    print("\nPOOL TOTAL COMBINADO:")
    print(f"  TRAIN10 Total: {len(df_train10)} filas | Clases: {df_train10['clase_objetivo'].nunique()}")
    print(f"    Originales: {len(df_orig_train)}, Sintéticos: {len(df_f10_train)}")
    print(f"  DEV10 Total:   {len(df_dev10)} filas | Clases: {df_dev10['clase_objetivo'].nunique()}")
    print(f"    Originales: {len(df_orig_dev)}, Sintéticos: {len(df_f10_dev)}")
    print(f"  Suma: {len(df_train10) + len(df_dev10)} (esperado: {len(df_orig) + len(df_f10)})")

    assert len(df_train10) + len(df_dev10) == len(df_orig) + len(df_f10)
    assert set(df_train10["id"]).intersection(set(df_dev10["id"])) == set()
    assert set(df_train10["id_grupo"]).intersection(set(df_dev10["id_grupo"])) == set()

    print("\n[OK] Split completamente validado: cero colisiones de IDs y cero colisiones de id_grupo.")


if __name__ == "__main__":
    probar_split()
