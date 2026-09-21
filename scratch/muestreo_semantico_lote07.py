"""
Muestreo semántico estratificado de 46 casos del Lote 07 (TRANSMISION) para CarBot:
- 40 casos base: 5 por cada una de las 8 clases (1 L1, 2 L2, 2 L3)
- 2 casos extra de Clase 38 (CVT / DSG)
- 2 casos extra de Clase 39 (Robotizada Dualogic / I-Motion / Easytronic)
- 2 casos extra de contraste entre Clase 37 (Diferencial) y Clase 41 (Eje primario)
Total = 46 casos.
"""

import pandas as pd
from pathlib import Path


def main():
    df = pd.read_csv("dataset_fase10_lote_07.csv")

    clases = [
        "Disco de embrague desgastado o patinando",
        "Falla en bombin o bomba hidraulica de embrague",
        "Falta o degradacion de aceite de caja de cambios",
        "Rodajes de caja mecanica o diferencial gastados",
        "Sobrecalentamiento o solenoides en caja automatica CVT / DSG",
        "Falla en caja robotizada Dualogic / I-Motion / Easytronic (Fiat / VW)",
        "Desgaste en collarin de empuje o crapodina de embrague",
        "Rodajes de transmision manual o eje primario gastados"
    ]

    seleccionados_ids = []

    # 1. 40 casos base (1 L1, 2 L2, 2 L3 por clase)
    for c in clases:
        sub_c = df[df["clase_objetivo"] == c]
        l1 = sub_c[sub_c["nivel_informacion"] == "L1"].head(1)["id"].tolist()
        # Preferir L2 con contrastivo o mediciones/dtc
        l2_cand = sub_c[sub_c["nivel_informacion"] == "L2"]
        l2_cont = l2_cand[l2_cand["es_contrastivo"] == "SI"]
        if len(l2_cont) >= 2:
            l2 = l2_cont.head(2)["id"].tolist()
        else:
            l2 = l2_cand.head(2)["id"].tolist()
        # Preferir L3 con mediciones/dtc
        l3_cand = sub_c[sub_c["nivel_informacion"] == "L3"]
        l3_dtc = l3_cand[l3_cand["dtc"].notna() & (l3_cand["dtc"] != "")]
        if len(l3_dtc) >= 1:
            l3 = l3_dtc.head(1)["id"].tolist() + l3_cand[~l3_cand["id"].isin(l3_dtc["id"])].head(1)["id"].tolist()
        else:
            l3 = l3_cand.head(2)["id"].tolist()
        
        seleccionados_ids.extend(l1 + l2 + l3)

    # 2. 2 casos extra de Clase 38 (uno CVT y uno DSG)
    c38_cand = df[(df["clase_objetivo"] == "Sobrecalentamiento o solenoides en caja automatica CVT / DSG") & (~df["id"].isin(seleccionados_ids))]
    extra_c38 = c38_cand.head(2)["id"].tolist()
    seleccionados_ids.extend(extra_c38)

    # 3. 2 casos extra de Clase 39 (Robotizadas con actuador / presión / modo N)
    c39_cand = df[(df["clase_objetivo"] == "Falla en caja robotizada Dualogic / I-Motion / Easytronic (Fiat / VW)") & (~df["id"].isin(seleccionados_ids))]
    extra_c39 = c39_cand.head(2)["id"].tolist()
    seleccionados_ids.extend(extra_c39)

    # 4. 2 casos extra de contraste entre 37 y 41
    c37_vs_41 = df[(df["clase_objetivo"] == "Rodajes de caja mecanica o diferencial gastados") & 
                   (df["clase_contrastiva"] == "Rodajes de transmision manual o eje primario gastados") & 
                   (~df["id"].isin(seleccionados_ids))]
    c41_vs_37 = df[(df["clase_objetivo"] == "Rodajes de transmision manual o eje primario gastados") & 
                   (df["clase_contrastiva"] == "Rodajes de caja mecanica o diferencial gastados") & 
                   (~df["id"].isin(seleccionados_ids))]
    
    extra_contrastes = []
    if len(c37_vs_41) > 0:
        extra_contrastes.append(c37_vs_41.iloc[0]["id"])
    if len(c41_vs_37) > 0:
        extra_contrastes.append(c41_vs_37.iloc[0]["id"])
    while len(extra_contrastes) < 2:
        rem = df[(df["es_contrastivo"] == "SI") & (~df["id"].isin(seleccionados_ids + extra_contrastes))]
        extra_contrastes.append(rem.iloc[0]["id"])
    seleccionados_ids.extend(extra_contrastes)

    df_muestra = df[df["id"].isin(seleccionados_ids)].copy()
    print(f"Total muestra semántica seleccionada: {len(df_muestra)} casos")

    # Guardar en archivo para revisión
    out_path = Path("scratch/muestra_semantica_46_lote07.csv")
    df_muestra.to_csv(out_path, index=False, encoding="utf-8")
    print(f"Muestra guardada en {out_path}")

    # Imprimir un resumen por clase y nivel
    print(df_muestra.groupby(["clase_objetivo", "nivel_informacion"]).size())


if __name__ == "__main__":
    main()
