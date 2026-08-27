from pathlib import Path

import pandas as pd
from scipy import stats

RAIZ_ML = Path(__file__).resolve().parents[1]
RAIZ_PROYECTO = RAIZ_ML.parent
tracker_path = RAIZ_ML / "data" / "tracker_diagnosticos.csv"
if not tracker_path.exists():
    tracker_path = Path("data/tracker_diagnosticos.csv")

if not tracker_path.exists():
    print(f"Error: No se encontro '{tracker_path}'. Ejecuta primero 'generar_tracker_excel.py'")
    raise SystemExit(1)

df = pd.read_csv(tracker_path)
pre_test = df[df["fase"] == "Pre-test"]
post_test = df[df["fase"] == "Post-test"]

print("=" * 80)
print("PROCESAMIENTO AUTOMATICO DE FICHAS DE TESIS (RESULTADOS CAPITULO IV)")
print("=" * 80)

correctos_pre = pre_test["prediccion_correcta"].sum()
total_pre = len(pre_test)
porcentaje_pre = (correctos_pre / total_pre) * 100
correctos_post = post_test["prediccion_correcta"].sum()
total_post = len(post_test)
porcentaje_post = (correctos_post / total_post) * 100

print("\nFICHA 1: PREDICCION DE FALLAS VEHICULARES (PRECISION)")
print("-" * 65)
print(f"Fase Pre-test:  {correctos_pre}/{total_pre} predicciones correctas ({porcentaje_pre:.2f}%)")
print(f"Fase Post-test: {correctos_post}/{total_post} predicciones correctas ({porcentaje_post:.2f}%)")
print(f"--> Mejora en la precision: +{porcentaje_post - porcentaje_pre:.2f}% de aciertos.")

completos_pre = pre_test["campos_completos"].sum()
completos_post = post_test["campos_completos"].sum()
pct_completo_pre = (completos_pre / total_pre) * 100
pct_completo_post = (completos_post / total_post) * 100

print("\nFICHA 2: CONTROL DE INFORMACION DIAGNOSTICA (COMPLETITUD)")
print("-" * 65)
print(f"Fase Pre-test:  {completos_pre}/{total_pre} registros completos ({pct_completo_pre:.2f}%)")
print(f"Fase Post-test: {completos_post}/{total_post} registros completos ({pct_completo_post:.2f}%)")
print(f"--> Mejora en completitud: +{pct_completo_post - pct_completo_pre:.2f}% de registros completos.")

tiempo_total_pre = pre_test["tiempo_diagnostico_minutos"].sum()
tiempo_prom_pre = pre_test["tiempo_diagnostico_minutos"].mean()
tiempo_total_post = post_test["tiempo_diagnostico_minutos"].sum()
tiempo_prom_post = post_test["tiempo_diagnostico_minutos"].mean()

print("\nFICHA 3: EFICIENCIA DEL DIAGNOSTICO (TIEMPOS EN MINUTOS)")
print("-" * 65)
print(f"Fase Pre-test:  Tiempo Total = {tiempo_total_pre} min | Promedio = {tiempo_prom_pre:.2f} min por auto")
print(f"Fase Post-test: Tiempo Total = {tiempo_total_post} min | Promedio = {tiempo_prom_post:.2f} min por auto")
print(f"--> Reduccion de tiempo de atencion: -{tiempo_prom_pre - tiempo_prom_post:.2f} minutos por vehiculo.")

n_muestras = min(len(pre_test), len(post_test))
t_stat, p_value = stats.ttest_rel(
    pre_test["tiempo_diagnostico_minutos"].iloc[:n_muestras],
    post_test["tiempo_diagnostico_minutos"].iloc[:n_muestras],
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

try:
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import seaborn as sns

    directorio_graficas = RAIZ_PROYECTO / "docs" / "graficas"
    directorio_graficas.mkdir(parents=True, exist_ok=True)
    sns.set_theme(style="whitegrid")
    plt.rcParams.update({"font.size": 11})

    plt.figure(figsize=(7, 5))
    sns.boxplot(
        x="fase",
        y="tiempo_diagnostico_minutos",
        data=df,
        hue="fase",
        palette="Set2",
        width=0.5,
        legend=False,
    )
    plt.title("Eficiencia del Diagnóstico: Tiempos Pre-test vs Post-test", pad=15)
    plt.xlabel("Fase de Evaluación")
    plt.ylabel("Tiempo de Diagnóstico (Minutos)")
    plt.savefig(directorio_graficas / "comparacion_tiempos_diagnostico.png", dpi=300, bbox_inches="tight")
    plt.close()

    metricas = {
        "Fase": ["Pre-test", "Post-test", "Pre-test", "Post-test"],
        "Métrica": [
            "Precisión del Diagnóstico",
            "Precisión del Diagnóstico",
            "Completitud de Ficha",
            "Completitud de Ficha",
        ],
        "Porcentaje (%)": [porcentaje_pre, porcentaje_post, pct_completo_pre, pct_completo_post],
    }
    df_metricas = pd.DataFrame(metricas)

    plt.figure(figsize=(8, 5))
    ax = sns.barplot(
        x="Métrica",
        y="Porcentaje (%)",
        hue="Fase",
        data=df_metricas,
        palette="Set1",
    )
    plt.title("Impacto en la Calidad del Diagnóstico Vehicular", pad=15)
    plt.ylabel("Porcentaje (%)")
    plt.ylim(0, 115)

    for barra in ax.patches:
        altura = barra.get_height()
        if altura > 0:
            ax.annotate(
                f"{altura:.1f}%",
                (barra.get_x() + barra.get_width() / 2, altura),
                ha="center",
                va="center",
                xytext=(0, 8),
                textcoords="offset points",
                fontweight="bold",
            )

    plt.savefig(directorio_graficas / "comparacion_calidad_diagnostico.png", dpi=300, bbox_inches="tight")
    plt.close()
    print(f"\n[Graficador] Gráficas exportadas en: '{directorio_graficas}'")
except ImportError as exc:
    print(f"\n[Graficador] Dependencia opcional no instalada: {exc}")
except Exception as exc:
    print(f"\n[Graficador] No se pudieron generar las gráficas: {exc}")
