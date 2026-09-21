import sys
import pandas as pd
import numpy as np
import joblib
from pathlib import Path
from sklearn.metrics import f1_score

base_dir = Path('.').resolve()
if str(base_dir) not in sys.path:
    sys.path.insert(0, str(base_dir))
if str(base_dir / "backend") not in sys.path:
    sys.path.insert(0, str(base_dir / "backend"))

from backend.src.core.diagnostico.taxonomia_sistemas import FALLA_A_SISTEMA

# Load DEV10
df_dev10 = pd.read_csv(base_dir / "machine_learning/data/fase10/dev10_v1.csv")
dev_textos = df_dev10["texto_usuario"].astype(str).tolist()
y_real = df_dev10["clase_objetivo"].tolist()

# Load models
vec_f83 = joblib.load(base_dir / "machine_learning/models/vectorizador_tfidf.pkl")
cal_f_f83 = joblib.load(base_dir / "machine_learning/models/modelo_diagnostico.pkl")
cal_s_f83 = joblib.load(base_dir / "machine_learning/models/modelo_sistema.pkl")

dir_c1 = base_dir / "machine_learning/training/fase10/candidates/C1"
vec_c1 = joblib.load(dir_c1 / "vectorizador_c1.pkl")
cal_f_c1 = joblib.load(dir_c1 / "modelo_diagnostico_c1.pkl")
cal_s_c1 = joblib.load(dir_c1 / "modelo_sistema_c1.pkl")

def inferir(cal_falla, cal_sist, vec, textos, temp=0.80, exp_sist=0.65):
    X_vec = vec.transform(textos)
    p_f = cal_falla.predict_proba(X_vec)
    p_s = cal_sist.predict_proba(X_vec)

    clases_f = list(cal_falla.classes_)
    clases_s = list(cal_sist.classes_)
    sist_map = [{clases_s[j]: p_s[i, j] for j in range(len(clases_s))} for i in range(len(textos))]

    p_comb = np.zeros_like(p_f)
    for i in range(len(textos)):
        for j, f in enumerate(clases_f):
            m = FALLA_A_SISTEMA.get(f, "GENERAL")
            p_comb[i, j] = p_f[i, j] * (sist_map[i].get(m, 0.05) ** exp_sist)
        suma_i = np.sum(p_comb[i])
        if suma_i > 0:
            p_comb[i] /= suma_i

    if temp > 0 and temp != 1.0:
        for i in range(len(textos)):
            p_comb[i] = p_comb[i] ** (1.0 / temp)
            suma_t = np.sum(p_comb[i])
            if suma_t > 0:
                p_comb[i] /= suma_t

    pred_top1_idx = np.argmax(p_comb, axis=1)
    pred_top1 = [clases_f[idx] for idx in pred_top1_idx]
    
    top3_idx = np.argsort(p_comb, axis=1)[:, -3:][:, ::-1]
    pred_top3 = [[clases_f[idx] for idx in row] for row in top3_idx]

    return pred_top1, pred_top3

print("Inferencia F8.3...")
p1_f83, p3_f83 = inferir(cal_f_f83, cal_s_f83, vec_f83, dev_textos)
print("Inferencia C1...")
p1_c1, p3_c1 = inferir(cal_f_c1, cal_s_c1, vec_c1, dev_textos)

correct1_f83 = [int(p1_f83[i] == y_real[i]) for i in range(len(y_real))]
correct1_c1  = [int(p1_c1[i] == y_real[i]) for i in range(len(y_real))]
correct3_f83 = [int(y_real[i] in p3_f83[i]) for i in range(len(y_real))]
correct3_c1  = [int(y_real[i] in p3_c1[i]) for i in range(len(y_real))]

df_eval = pd.DataFrame({
    "id": df_dev10["id"],
    "real": y_real,
    "pred_f83": p1_f83,
    "pred_c1": p1_c1,
    "correct1_f83": correct1_f83,
    "correct1_c1": correct1_c1,
    "correct3_f83": correct3_f83,
    "correct3_c1": correct3_c1,
    "source": df_dev10["synthetic_or_original"],
    "nivel": df_dev10["nivel_informacion"],
    "macro": df_dev10["macro_sistema"]
})

# Load leakage IDs
df_leak = pd.read_csv(base_dir / "machine_learning/data/fase10/fase10_leakage_train_dev.csv")
leak_ids = set(df_leak['dev_id'])

subsets = {
    "DEV10 GLOBAL": df_eval,
    "ORIGINAL VISTO POR F8.3 (TOTAL ORIGINAL)": df_eval[df_eval['source'] == 'ORIGINAL'],
    "ORIGINAL REALMENTE NO VISTO POR F8.3": df_eval[(df_eval['source'] == 'ORIGINAL') & False],
    "ORIGINAL CON NEAR-DUPLICATE EN TRAIN10": df_eval[df_eval['id'].isin(leak_ids)],
    "ORIGINAL SIN NEAR-DUPLICATE EN TRAIN10 (STRICT CLEAN ORIGINAL)": df_eval[(df_eval['source'] == 'ORIGINAL') & (~df_eval['id'].isin(leak_ids))],
    "SINTETICO FASE 10 (NO VISTO POR F8.3 NI C1 TRAIN)": df_eval[df_eval['source'] == 'SINTETICO'],
    "SINTETICO L1": df_eval[(df_eval['source'] == 'SINTETICO') & (df_eval['nivel'] == 'L1')],
    "SINTETICO L2": df_eval[(df_eval['source'] == 'SINTETICO') & (df_eval['nivel'] == 'L2')],
    "SINTETICO L3": df_eval[(df_eval['source'] == 'SINTETICO') & (df_eval['nivel'] == 'L3')],
}

rows = []
for name, sub in subsets.items():
    n = len(sub)
    if n == 0:
        rows.append({
            "subset": name,
            "n": 0,
            "top1_f83": "N/A", "top1_c1": "N/A", "delta_top1": "N/A",
            "top3_f83": "N/A", "top3_c1": "N/A", "delta_top3": "N/A",
            "mf1_f83": "N/A", "mf1_c1": "N/A", "delta_mf1": "N/A"
        })
        continue
    
    t1_f83 = sub['correct1_f83'].mean()
    t1_c1  = sub['correct1_c1'].mean()
    t3_f83 = sub['correct3_f83'].mean()
    t3_c1  = sub['correct3_c1'].mean()
    
    present_cl = sorted(sub['real'].unique())
    mf1_f83 = f1_score(sub['real'], sub['pred_f83'], labels=present_cl, average='macro', zero_division=0)
    mf1_c1  = f1_score(sub['real'], sub['pred_c1'], labels=present_cl, average='macro', zero_division=0)
    
    rows.append({
        "subset": name,
        "n": n,
        "top1_f83": f"{t1_f83*100:.2f}%",
        "top1_c1": f"{t1_c1*100:.2f}%",
        "delta_top1": f"{(t1_c1 - t1_f83)*100:+.2f}%",
        "top3_f83": f"{t3_f83*100:.2f}%",
        "top3_c1": f"{t3_c1*100:.2f}%",
        "delta_top3": f"{(t3_c1 - t3_f83)*100:+.2f}%",
        "mf1_f83": f"{mf1_f83*100:.2f}%",
        "mf1_c1": f"{mf1_c1*100:.2f}%",
        "delta_mf1": f"{(mf1_c1 - mf1_f83)*100:+.2f}%"
    })

df_report = pd.DataFrame(rows)
print("\n" + "="*100)
print("REPORTE COMPLETO REINTERPRETADO (TOP 1, TOP 3, MACRO F1):")
print("="*100)
print(df_report.to_string(index=False))
