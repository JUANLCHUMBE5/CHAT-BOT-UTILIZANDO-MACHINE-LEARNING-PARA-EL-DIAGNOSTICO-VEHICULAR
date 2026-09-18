import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "backend"))

from machine_learning.data.benchmark_dev_60_casos import CASOS_DEV_60
from src.core.gestor_diagnostico import GestorDiagnostico
from src.core.diagnostico.auto_interrogador import evaluar_auto_pregunta_descarte

gestor = GestorDiagnostico()
test_ids = ["DEV_13", "DEV_17", "DEV_18", "DEV_38", "DEV_52"]
casos_dict = {c["id"]: c for c in CASOS_DEV_60}

for cid in test_ids:
    c = casos_dict[cid]
    sintoma = c["sintoma"]
    pred_top = gestor.modelo_ml.predecir_top_fallas(sintoma, limite=3)
    top1_f = pred_top[0]["falla"]
    conf = pred_top[0]["probabilidad"]
    
    auto_preg = evaluar_auto_pregunta_descarte(
        texto=sintoma,
        diagnostico_top1=top1_f,
        confianza_top1=conf,
        predicciones_top=pred_top,
    )
    print(f"\n{cid}: {c['falla_esperada']}")
    print(f"  Texto: {sintoma}")
    print(f"  Top 1 ML: {top1_f} ({conf:.3f})")
    print(f"  AutoPregunta: {auto_preg.es_necesaria if auto_preg else False}")
    if auto_preg:
        print(f"  Pregunta: {auto_preg.pregunta[:80]}")
