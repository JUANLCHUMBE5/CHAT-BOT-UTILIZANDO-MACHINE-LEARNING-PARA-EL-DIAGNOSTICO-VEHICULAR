"""
Muestreo semántico estratificado de 33 casos del Lote 08 (SUSPENSION_CHASIS) para CarBot:
- 25 casos base: 5 por cada una de las 5 clases (1 L1, 2 L2, 2 L3)
- 3 casos extra de Clase 43 (Juntas homocineticas o palieres danados)
- 3 casos extra de Clase 46 (Rodamiento de maza o rodaje de rueda picado)
- 2 casos extra de contraste entre Clase 44 (Llantas) y Clase 28 (Discos de freno alabeados)
Total = 33 casos.
"""

import pandas as pd
from pathlib import Path


def main():
    df = pd.read_csv("dataset_fase10_lote_08.csv")

    clases = [
        "Amortiguadores reventados o bujes de suspension gastados",
        "Juntas homocineticas o palieres danados",
        "Llantas desbalanceadas o desalineadas",
        "Cremallera de direccion asistida con holgura o fuga",
        "Rodamiento de maza o rodaje de rueda picado (zumbido de rodadura)"
    ]

    seleccionados_ids = []

    # 1. 25 casos base (1 L1, 2 L2, 2 L3 por clase)
    for c in clases:
        sub_c = df[df["clase_objetivo"] == c]
        l1 = sub_c[sub_c["nivel_informacion"] == "L1"].head(1)["id"].tolist()
        # Preferir L2 contrastivos
        l2_cand = sub_c[sub_c["nivel_informacion"] == "L2"]
        l2_cont = l2_cand[l2_cand["es_contrastivo"] == "SI"]
        if len(l2_cont) >= 2:
            l2 = l2_cont.head(2)["id"].tolist()
        else:
            l2 = l2_cand.head(2)["id"].tolist()
        # Preferir L3 con mediciones/DTC
        l3_cand = sub_c[sub_c["nivel_informacion"] == "L3"]
        l3_dtc = l3_cand[l3_cand["dtc"].notna() & (l3_cand["dtc"] != "")]
        if len(l3_dtc) >= 1:
            l3 = l3_dtc.head(1)["id"].tolist() + l3_cand[~l3_cand["id"].isin(l3_dtc["id"])].head(1)["id"].tolist()
        else:
            l3 = l3_cand.head(2)["id"].tolist()
        
        seleccionados_ids.extend(l1 + l2 + l3)

    # 2. 3 casos extra de Clase 43 (Homocinéticas)
    c43_cand = df[(df["clase_objetivo"] == "Juntas homocineticas o palieres danados") & (~df["id"].isin(seleccionados_ids))]
    extra_c43 = c43_cand.head(3)["id"].tolist()
    seleccionados_ids.extend(extra_c43)

    # 3. 3 casos extra de Clase 46 (Rodamientos)
    c46_cand = df[(df["clase_objetivo"] == "Rodamiento de maza o rodaje de rueda picado (zumbido de rodadura)") & (~df["id"].isin(seleccionados_ids))]
    extra_c46 = c46_cand.head(3)["id"].tolist()
    seleccionados_ids.extend(extra_c46)

    # 4. 2 casos de contraste Clase 44 vs 28 (Llantas vs Discos de freno alabeados)
    c44_vs_28 = df[(df["clase_objetivo"] == "Llantas desbalanceadas o desalineadas") & 
                   (df["clase_contrastiva"] == "Discos de freno alabeados o desgastados") & 
                   (~df["id"].isin(seleccionados_ids))]
    extra_c44_28 = c44_vs_28.head(2)["id"].tolist()
    seleccionados_ids.extend(extra_c44_28)

    df_muestra = df[df["id"].isin(seleccionados_ids)].copy()
    print(f"Total muestra semántica seleccionada: {len(df_muestra)} casos")

    out_path = Path("scratch/muestra_semantica_33_lote08.csv")
    df_muestra.to_csv(out_path, index=False, encoding="utf-8")
    print(f"Muestra guardada en {out_path}")

    print("\nDistribución por clase y nivel:")
    print(df_muestra.groupby(["clase_objetivo", "nivel_informacion"]).size())


if __name__ == "__main__":
    main()
