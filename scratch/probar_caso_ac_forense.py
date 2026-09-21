import sys
import joblib
import pandas as pd
import numpy as np
from pathlib import Path

base_dir = Path('.').resolve()
if str(base_dir) not in sys.path:
    sys.path.insert(0, str(base_dir))
if str(base_dir / "backend") not in sys.path:
    sys.path.insert(0, str(base_dir / "backend"))

from backend.src.core.diagnostico.taxonomia_sistemas import FALLA_A_SISTEMA
from backend.src.core.diagnostico.semantic_purifier import purificar_sintoma_para_vectorizador_ml
from backend.src.core.sanitizer import sanitizar_prompt_usuario
from backend.src.core.diagnostico.text_processor import normalizar_jerga_peruana

vec_f83 = joblib.load(base_dir / "machine_learning/models/vectorizador_tfidf.pkl")
cal_f_f83 = joblib.load(base_dir / "machine_learning/models/modelo_diagnostico.pkl")
cal_s_f83 = joblib.load(base_dir / "machine_learning/models/modelo_sistema.pkl")

dir_c1 = base_dir / "machine_learning/training/fase10/candidates/C1"
vec_c1 = joblib.load(dir_c1 / "vectorizador_c1.pkl")
cal_f_c1 = joblib.load(dir_c1 / "modelo_diagnostico_c1.pkl")
cal_s_c1 = joblib.load(dir_c1 / "modelo_sistema_c1.pkl")

def predecir(texto, vec, cal_f, cal_s):
    X = vec.transform([texto])
    pf = cal_f.predict_proba(X)[0]
    ps = cal_s.predict_proba(X)[0]
    clases_f = list(cal_f.classes_)
    clases_s = list(cal_s.classes_)
    sist_map = {clases_s[j]: ps[j] for j in range(len(clases_s))}
    
    p_comb = np.zeros_like(pf)
    for j, f in enumerate(clases_f):
        m = FALLA_A_SISTEMA.get(f, "GENERAL")
        p_comb[j] = pf[j] * (sist_map.get(m, 0.05) ** 0.65)
    p_comb /= p_comb.sum()
    
    top3_idx = np.argsort(p_comb)[-3:][::-1]
    top3 = [(clases_f[idx], round(float(p_comb[idx]), 4)) for idx in top3_idx]
    return top3

consultas = [
    # 1. Caso aislado limpio cotidiano
    ("Texto Crudo Cotidiano", "Prendo el boton A/C del aire acondicionado sale aire tibio ambiente y no enfria nada parece ventilador comun y corriente."),
    # 2. Caso técnico Corolla
    ("Texto Crudo Tecnico Corolla", "Toyota Corolla 2017 aire acondicionado no enfria en cabina, compresor acopla pero presion de baja y alta estan igualadas en 70 PSI."),
    # 3. Caso Sail multi-turno (Piloto Fase 9.2 CASO 02 Turno 4)
    ("Multi-turno CASO 02 Sail", "Chevrolet Sail año 2018. presenta pérdida de potencia. cuando está al acelerar bajo carga. con A/C encendido."),
    # 4. Caso Kia Rio multi-turno (Piloto Fase 9.2 CASO 20 Turno 2)
    ("Multi-turno CASO 20 Kia Rio", "Kia Rio año 2017. presenta vibración, apagado de motor. con A/C encendido, luces tenues o encendidas."),
    # 5. Caso contaminado con motor previo (vibración + pérdida de potencia + A/C tibio sin segmentar)
    ("Contaminado Cross-Turno Sin Segmentar", "Kia con humo negro y consumo alto. Scanner marca mezcla rica. Prendo el aire acondicionado y no enfria sale aire tibio."),
    # 6. Caso donde el síntoma menciona compresor pero también tironeo/mezcla
    ("Sintoma Mixto Carga A/C", "El auto tironea y pierde fuerza al prender el aire acondicionado en subida.")
]

print("="*100)
print("TRAZABILIDAD FORENSE DE CASOS DE CLIMATIZACIÓN (A/C) EN PIPELINE ML:")
print("="*100)

for etiqueta, txt in consultas:
    print(f"\n>>> [{etiqueta}]")
    print(f"Texto de entrada: '{txt}'")
    san = sanitizar_prompt_usuario(txt)
    norm = normalizar_jerga_peruana(san)
    purif = purificar_sintoma_para_vectorizador_ml(norm)
    print(f"Purificado ML:    '{purif}'")
    
    top3_f83 = predecir(purif, vec_f83, cal_f_f83, cal_s_f83)
    top3_c1  = predecir(purif, vec_c1, cal_f_c1, cal_s_c1)
    
    print("  F8.3 Top-3:")
    for f, p in top3_f83:
        print(f"    - {f} ({p*100:.1f}%) [Macro: {FALLA_A_SISTEMA.get(f)}]")
    print("  C1 Top-3:")
    for f, p in top3_c1:
        print(f"    - {f} ({p*100:.1f}%) [Macro: {FALLA_A_SISTEMA.get(f)}]")
