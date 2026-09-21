import sys
from pathlib import Path

import faiss
import numpy as np

BASE_DIR = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "backend"))

from machine_learning.data.benchmark_dev_60_casos import CASOS_DEV_60

from src.core.gestor_diagnostico import GestorDiagnostico

gestor = GestorDiagnostico()
motor_rag = gestor.motor_rag

test_ids = ["DEV_08", "DEV_13", "DEV_14", "DEV_30", "DEV_33", "DEV_38", "DEV_46"]
casos_dict = {c["id"]: c for c in CASOS_DEV_60}

for cid in test_ids:
    c = casos_dict[cid]
    sintoma = c["sintoma"]
    esperada = c["falla_esperada"]
    dtc = c.get("codigo_dtc")
    dtcs = [dtc] if dtc else []
    
    pred_top = gestor.modelo_ml.predecir_top_fallas(sintoma, limite=3)
    pred_sis = gestor.modelo_ml.predecir_sistema(sintoma)
    
    from src.infrastructure.rag.query_builder import construir_consulta_hibrida
    c_hib = construir_consulta_hibrida(sintoma, pred_sis, pred_top, dtcs)
    c_exp = motor_rag._expandir_consulta(c_hib)
    vec = motor_rag.vectorizador.transform([c_exp]).toarray().astype(np.float32)
    faiss.normalize_L2(vec)
    sims, inds = motor_rag.faiss_index.search(vec, k=30)
    
    cands_fallas = [motor_rag.metadatos_procedimientos[int(i)].get("falla") for i in inds[0] if int(i) < len(motor_rag.metadatos_procedimientos)]
    
    en_top30 = esperada in cands_fallas
    pos_faiss = cands_fallas.index(esperada) if en_top30 else -1
    print(f"{cid} ({esperada}): En top30 FAISS? {en_top30} (Pos: {pos_faiss}) | ML Top1: {pred_top[0]['falla']} ({pred_top[0]['probabilidad']:.2f})")
