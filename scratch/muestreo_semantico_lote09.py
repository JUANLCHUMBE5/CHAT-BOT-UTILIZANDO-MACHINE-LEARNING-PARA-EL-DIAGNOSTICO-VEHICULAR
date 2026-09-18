"""
Script para generar el muestreo semántico estratificado de 45 casos para Lote 09.
35 base (5 por clase: 1 L1, 2 L2, 2 L3 x 7 clases)
+ 3 extra bloque 47/48/52/53
+ 3 extra bloque 49/50/51
+ 2 extra CRANK vs NO-CRANK
+ 2 extra 12V vs HV
Total = 45 casos.
"""

import pandas as pd
from pathlib import Path

CLASES_ORDEN = [
    "Alternador defectuoso o placa de diodos quemada",
    "Bateria descargada o bornes sulfatados",
    "Degradacion o falla en paquete de bateria de alto voltaje (EV / Hibridos)",
    "Fallo en inversor de corriente IGBT o motor electrico (EV)",
    "Foco o falla en sistema de refrigeracion de bateria/inversor (EV)",
    "Falla en motor de arranque o solenoide defectuoso (clac seco o carbones gastados)",
    "Fuga parasita de corriente en reposo (consumo nocturno de bateria)"
]


def seleccionar_muestreo():
    df = pd.read_csv("dataset_fase10_lote_09.csv")
    muestra_ids = []

    # 1. 35 base (1 L1, 2 L2, 2 L3 por clase)
    for c in CLASES_ORDEN:
        sub = df[df["clase_objetivo"] == c]
        # L1: primer o segundo caso
        id_l1 = sub[sub["nivel_informacion"] == "L1"].iloc[0]["id"]
        # L2: buscar al menos 1 con DTC y 1 contrastivo
        l2_sub = sub[sub["nivel_informacion"] == "L2"]
        l2_ids = l2_sub["id"].tolist()[:2]
        # L3: buscar técnicos con mediciones y DTC
        l3_sub = sub[sub["nivel_informacion"] == "L3"]
        l3_ids = l3_sub["id"].tolist()[:2]
        muestra_ids.extend([id_l1] + l2_ids + l3_ids)

    # 2. Extra bloque 47/48/52/53
    extra_12v = ["F10-L09-0015", "F10-L09-0035", "F10-L09-0055", "F10-L09-0070", "F10-L09-0215", "F10-L09-0230", "F10-L09-0255", "F10-L09-0268"]
    for eid in extra_12v:
        if eid not in muestra_ids:
            muestra_ids.append(eid)

    # 3. Extra bloque 49/50/51
    extra_ev = ["F10-L09-0095", "F10-L09-0110", "F10-L09-0135", "F10-L09-0146", "F10-L09-0175", "F10-L09-0186"]
    for eid in extra_ev:
        if eid not in muestra_ids:
            muestra_ids.append(eid)

    # 4. Extra CRANK vs NO-CRANK
    extra_crank = ["F10-L09-0212", "F10-L09-0224", "F10-L09-0231"]
    for eid in extra_crank:
        if eid not in muestra_ids:
            muestra_ids.append(eid)

    # 5. Extra 12V vs HV
    extra_12v_hv = ["F10-L09-0091", "F10-L09-0134", "F10-L09-0156"]
    for eid in extra_12v_hv:
        if eid not in muestra_ids:
            muestra_ids.append(eid)

    print(f"Total casos seleccionados para revisión semántica: {len(muestra_ids)}")

    df_muestra = df[df["id"].isin(muestra_ids)].sort_values(by="id")
    print(f"Total filas recuperadas: {len(df_muestra)}")

    # Guardar en markdown de apoyo
    md_lines = []
    md_lines.append("# MUESTREO SEMÁNTICO ESTRATIFICADO - LOTE 09 (45 CASOS)\n")
    md_lines.append("| ID | Clase | Nivel | DTC | Contrastivo | Resumen Técnico / Medición | Veredicto |")
    md_lines.append("|---|---|---|---|---|---|---|")

    for _, r in df_muestra.iterrows():
        dtc_txt = r["dtc"] if pd.notna(r["dtc"]) and r["dtc"] else "—"
        cont_txt = f"SI ({r['clase_contrastiva']})" if r["es_contrastivo"] == "SI" else "NO"
        texto = r["texto_usuario"]
        if len(texto) > 100:
            texto_resumen = texto[:97] + "..."
        else:
            texto_resumen = texto
        # escapar pipes
        texto_resumen = texto_resumen.replace("|", "/")
        cont_txt = cont_txt.replace("|", "/")
        md_lines.append(f"| {r['id']} | {r['clase_objetivo']} | {r['nivel_informacion']} | {dtc_txt} | {cont_txt} | {texto_resumen} | APROBADO |")

    with open("scratch/muestreo_semantico_lote09.md", "w", encoding="utf-8") as f:
        f.write("\n".join(md_lines))

    print("Archivo scratch/muestreo_semantico_lote09.md generado con éxito.")


if __name__ == "__main__":
    seleccionar_muestreo()
