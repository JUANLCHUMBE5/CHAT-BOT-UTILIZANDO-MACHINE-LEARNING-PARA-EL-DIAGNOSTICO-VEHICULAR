"""
Evaluación del Auto-Interrogador en DEV:
Conjunto Positivo (20 casos ambiguos de desarrollo)
Conjunto Negativo (60 casos claros de desarrollo DEV_01-DEV_60)
"""

import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[3]
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))
BACKEND_DIR = BASE_DIR / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from src.core.gestor_diagnostico import GestorDiagnostico
from src.core.diagnostico.auto_interrogador import evaluar_auto_pregunta_descarte
from machine_learning.data.benchmark_dev_60_casos import CASOS_DEV_60

CASOS_DEV_AMBIGUOS_20 = [
    "Mi carro vibra al andar",
    "Tironea cuando acelero en pista",
    "No arranca en la mañana",
    "Se me apaga en marcha",
    "Tiene un ruido seco en el tren delantero al pasar baches",
    "El pedal de freno está raro",
    "Se recalienta el carro en el tráfico",
    "Pierde fuerza en subida y prende el check",
    "Huele a quemado cuando manejo",
    "Zumba fuerte cuando rueda",
    "Le cuesta entrar los cambios",
    "Tiembla todo el carro",
    "Consume demasiado combustible",
    "Hace un ruido en el motor",
    "Bota humo por el escape",
    "El timón tiene juego y vibra",
    "Las luces del tablero parpadean",
    "El aire acondicionado no enfría",
    "Tiene un ruido al doblar",
    "Se queda acelerado solo",
]

def main():
    gestor = GestorDiagnostico()

    print("=" * 80)
    print("EVALUACIÓN DE CASOS AMBIGUOS DE DESARROLLO (20 casos)")
    print("=" * 80)
    tp = 0
    fn = 0
    for idx, q in enumerate(CASOS_DEV_AMBIGUOS_20, 1):
        p_top = gestor.modelo_ml.predecir_top_fallas(q, limite=4)
        t1_f = p_top[0]["falla"] if p_top else ""
        t1_p = p_top[0]["probabilidad"] if p_top else 0.5
        ap = evaluar_auto_pregunta_descarte(q, t1_f, t1_p, p_top)
        det = bool(ap and ap.es_necesaria)
        if det:
            tp += 1
            print(f"[{idx:02d}] [OK - DETECTADO] {q:<50} | Top-1: {t1_f[:28]} ({t1_p:.2f})")
        else:
            fn += 1
            print(f"[{idx:02d}] [NO DETECTADO]  {q:<50} | Top-1: {t1_f[:28]} ({t1_p:.2f})")

    print("\n" + "=" * 80)
    print("EVALUACIÓN DE CASOS CLAROS DE DESARROLLO (60 casos DEV)")
    print("=" * 80)
    tn = 0
    fp = 0
    for idx, caso in enumerate(CASOS_DEV_60, 1):
        q = caso["sintoma"]
        p_top = gestor.modelo_ml.predecir_top_fallas(q, limite=4)
        t1_f = p_top[0]["falla"] if p_top else ""
        t1_p = p_top[0]["probabilidad"] if p_top else 0.5
        ap = evaluar_auto_pregunta_descarte(q, t1_f, t1_p, p_top)
        det = bool(ap and ap.es_necesaria)
        if not det:
            tn += 1
        else:
            fp += 1
            print(f"[{idx:02d}] [FALSO POSITIVO] {q[:60]}... | Top-1: {t1_f} ({t1_p:.2f})")

    print("\n" + "=" * 80)
    sensibilidad = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    especificidad = tn / (tn + fp) if (tn + fp) > 0 else 0.0
    precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    f1 = 2 * (precision * sensibilidad) / (precision + sensibilidad) if (precision + sensibilidad) > 0 else 0.0

    print(f"TP (Ambiguos detectados):        {tp} / {len(CASOS_DEV_AMBIGUOS_20)}")
    print(f"FN (Ambiguos no detectados):     {fn} / {len(CASOS_DEV_AMBIGUOS_20)}")
    print(f"TN (Claros no interrumpidos):    {tn} / {len(CASOS_DEV_60)}")
    print(f"FP (Claros interrumpidos err.):  {fp} / {len(CASOS_DEV_60)}")
    print(f"Sensibilidad:                    {sensibilidad*100:.2f}%")
    print(f"Especificidad:                   {especificidad*100:.2f}%")
    print(f"Precisión:                       {precision*100:.2f}%")
    print(f"F1-Score:                        {f1*100:.2f}%")
    print("=" * 80)

if __name__ == "__main__":
    main()
