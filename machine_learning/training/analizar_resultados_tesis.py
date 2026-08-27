import os
from pathlib import Path

import pandas as pd
from scipy import stats

RAIZ_ML = Path(__file__).resolve().parents[1]
tracker_path = RAIZ_ML / "data" / "tracker_diagnosticos.csv"
if not tracker_path.exists():
    tracker_path = Path("data/tracker_diagnosticos.csv")

if not tracker_path.exists():
    print(f"Error: No se encontro '{tracker_path}'. Ejecuta primero 'generar_tracker_excel.py'")
    exit(1)

# Cargar los datos
df = pd.read_csv(tracker_path)

# Separar los datos en Pre-test (sin chatbot) y Post-test (con chatbot)
pre_test = df[df['fase'] == 'Pre-test']
post_test = df[df['fase'] == 'Post-test']

print("=" * 80)
print("PROCESAMIENTO AUTOMATICO DE FICHAS DE TESIS (RESULTADOS CAPITULO IV)")
print("=" * 80)

# --- 1. FICHA 1: PREDICCION DE FALLAS VEHICULARES ---
correctos_pre = pre_test['prediccion_correcta'].sum()
total_pre = len(pre_test)
porcentaje_pre = (correctos_pre / total_pre) * 100

correctos_post = post_test['prediccion_correcta'].sum()
total_post = len(post_test)
porcentaje_post = (correctos_post / total_post) * 100

print("\nFICHA 1: PREDICCION DE FALLAS VEHICULARES (PRECISION)")
print("-" * 65)
print(f"Fase Pre-test:  {correctos_pre}/{total_pre} predicciones correctas ({porcentaje_pre:.2f}%)")
print(f"Fase Post-test: {correctos_post}/{total_post} predicciones correctas ({porcentaje_post:.2f}%)")
print(f"--> Mejora en la precision: +{porcentaje_post - porcentaje_pre:.2f}% de aciertos.")

# --- 2. FICHA 2: CONTROL DE INFORMACION DIAGNOSTICA ---
completos_pre = pre_test['campos_completos'].sum()
completos_post = post_test['campos_completos'].sum()
pct_completo_pre = (completos_pre / total_pre) * 100
pct_completo_post = (completos_post / total_post) * 100

print("\nFICHA 2: CONTROL DE INFORMACION DIAGNOSTICA (COMPLETITUD)")
print("-" * 65)
print(f"Fase Pre-test:  {completos_pre}/{total_pre} registros completos ({pct_completo_pre:.2f}%)")
print(f"Fase Post-test: {completos_post}/{total_post} registros completos ({pct_completo_post:.2f}%)")
print(f"--> Mejora en completitud: +{pct_completo_post - pct_completo_pre:.2f}% de registros completos.")

# --- 3. FICHA 3: EFICIENCIA DEL DIAGNOSTICO VEHICULAR (TIEMPO) ---
tiempo_total_pre = pre_test['tiempo_diagnostico_minutos'].sum()
tiempo_prom_pre = pre_test['tiempo_diagnostico_minutos'].mean()

tiempo_total_post = post_test['tiempo_diagnostico_minutos'].sum()
tiempo_prom_post = post_test['tiempo_diagnostico_minutos'].mean()

print("\nFICHA 3: EFICIENCIA DEL DIAGNOSTICO (TIEMPOS EN MINUTOS)")
print("-" * 65)
print(f"Fase Pre-test:  Tiempo Total = {tiempo_total_pre} min | Promedio = {tiempo_prom_pre:.2f} min por auto")
print(f"Fase Post-test: Tiempo Total = {tiempo_total_post} min | Promedio = {tiempo_prom_post:.2f} min por auto")
print(f"--> Reduccion de tiempo de atencion: -{tiempo_prom_pre - tiempo_prom_post:.2f} minutos por vehiculo.")

# --- 4. CONTRASTACION DE HIPOTESIS ESTADISTICA (PRUEBA T-STUDENT RELACIONADA) ---
n_muestras = min(len(pre_test), len(post_test))
t_stat, p_value = stats.ttest_rel(
    pre_test['tiempo_diagnostico_minutos'].iloc[:n_muestras], 
    post_test['tiempo_diagnostico_minutos'].iloc[:n_muestras]
)

print("\nCONTRASTACION DE HIPOTESIS ESTADISTICA (T-STUDENT MUESTRAS RELACIONADAS)")
print("-" * 65)
print(f"Valor estadistico T: {t_stat:.4f}")
print(f"Valor P (P-Value):   {p_value:.8f}")

if p_value < 0.05:
    print("\nCONCLUSION CIENTIFICA:")
    print("Dado que el P-Valor es menor que 0.05, se RECHAZA la hipotesis nula y se ACEPTA la hipotesis general:")
    print("'El chatbot utilizando Machine Learning influye y mejora significativamente el diagnostico vehicular en los talleres mecanicos de Carabayllo, 2026.'")
else:
    print("\nCONCLUSION CIENTIFICA:")
    print("No hay diferencia estadisticamente significativa.")

print("=" * 80)
