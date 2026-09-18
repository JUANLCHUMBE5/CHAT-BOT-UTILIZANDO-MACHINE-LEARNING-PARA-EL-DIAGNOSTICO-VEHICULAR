"""
Verificación de DEV 60 con el Gestor Oficial de CarBot (Candidata 8.3 Calibrada).
"""

import sys
from pathlib import Path
import numpy as np

BASE_DIR = Path(__file__).resolve().parents[3]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))
BACKEND_DIR = BASE_DIR / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from src.core.gestor_diagnostico import GestorDiagnostico
from machine_learning.data.benchmark_dev_60_casos import CASOS_DEV_60
from machine_learning.training.fase8.experimentar_calibracion_dev import calcular_metricas_calibracion

def main():
    g = GestorDiagnostico()
    confs = []
    aciertos = []
    top3_aciertos = 0

    for c in CASOS_DEV_60:
        q = c["sintoma"]
        gt = c["falla_esperada"]
        top_f = g.modelo_ml.predecir_top_fallas(q, limite=3)
        p1 = top_f[0]["falla"]
        c1 = top_f[0]["probabilidad"]
        confs.append(c1)
        ac = 1 if p1 == gt else 0
        aciertos.append(ac)
        if gt in [t["falla"] for t in top_f]:
            top3_aciertos += 1

    confs = np.array(confs)
    aciertos = np.array(aciertos)
    calib = calcular_metricas_calibracion(confs, aciertos)

    print("=" * 80)
    print("=== DEV 60 CON GESTOR OFICIAL (CALIBRADO 8.3) ===")
    print("=" * 80)
    print(f"Top-1 ML:        {np.mean(aciertos)*100:.2f}% ({np.sum(aciertos)}/60)")
    print(f"Top-3 ML:        {top3_aciertos/len(CASOS_DEV_60)*100:.2f}% ({top3_aciertos}/60)")
    print(f"Brier Score:     {calib['brier']:.4f}")
    print(f"ECE:             {calib['ece']:.4f}")
    print(f"Acc >= 80%:      {calib['acc_gte_80']*100:.2f}%")
    print(f"Cov >= 80%:      {calib['cov_gte_80']*100:.1f}%")
    print(f"Conf Aciertos:   {calib['conf_aciertos']:.4f}")
    print(f"Conf Errores:    {calib['conf_errores']:.4f}")
    print("\nBins de Fiabilidad (Reliability Curve):")
    for b in calib["bins"]:
        print(f"  Bin {b['bin']}: n={b['count']}, Acc={b['acc']*100:.1f}%, Conf={b['conf']*100:.1f}%, Gap={b['gap']:.4f}")
    print("=" * 80)

if __name__ == "__main__":
    main()
