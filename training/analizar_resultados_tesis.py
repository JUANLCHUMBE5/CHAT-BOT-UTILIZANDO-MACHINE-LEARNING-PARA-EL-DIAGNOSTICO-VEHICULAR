import pandas as pd
from scipy import stats
import os

if not os.path.exists("data/tracker_diagnosticos.csv"):
    print("Error: No se encontro 'data/tracker_diagnosticos.csv'. Ejecuta primero 'generar_tracker_excel.py'")
    exit()

# Cargar los datos
df = pd.read_csv("data/tracker_diagnosticos.csv")

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
# Evaluamos si la reduccion del tiempo de diagnostico es significativa para muestras relacionadas (Pág. 27 del PDF)
n_muestras = min(len(pre_test), len(post_test))
t_stat, p_value = stats.ttest_rel(
    pre_test['tiempo_diagnostico_minutos'].iloc[:n_muestras], 
    post_test['tiempo_diagnostico_minutos'].iloc[:n_muestras]
)

print("\nCONTRASTACION DE HIPOTESIS ESTADISTICA (T-STUDENT MUESTRAS RELACIONADAS)")
print("-" * 65)
print(f"Valor estadistico T: {t_stat:.4f}")
print(f"Valor P (P-Value):   {p_value:.8f}")

# Nivel de significancia alfa = 0.05
if p_value < 0.05:
    print("\nCONCLUSION CIENTIFICA:")
    print("Dado que el P-Valor es menor que 0.05, se RECHAZA la hipotesis nula y se ACEPTA la hipotesis general:")
    print("'El chatbot utilizando Machine Learning influye y mejora significativamente el diagnostico vehicular en los talleres mecanicos de Carabayllo, 2026.'")
else:
    print("\nCONCLUSION CIENTIFICA:")
    print("No hay diferencia estadisticamente significativa.")

print("=" * 80)

# --- 5. GENERACION DE GRAFICAS ACADEMICAS PARA LA TESIS ---
try:
    import matplotlib.pyplot as plt
    import seaborn as sns
    
    # Crear carpeta para las gráficas si no existe
    os.makedirs("documentacion/graficas", exist_ok=True)
    
    # Configurar estilo
    sns.set_theme(style="whitegrid")
    plt.rcParams.update({'font.size': 11})
    
    # Gráfica 1: Comparación de Tiempos (Boxplot)
    plt.figure(figsize=(7, 5))
    sns.boxplot(x='fase', y='tiempo_diagnostico_minutos', data=df, palette='Set2', width=0.5)
    plt.title('Eficiencia del Diagnóstico: Tiempos Pre-test vs Post-test', pad=15)
    plt.xlabel('Fase de Evaluación')
    plt.ylabel('Tiempo de Diagnóstico (Minutos)')
    plt.savefig('documentacion/graficas/comparacion_tiempos_diagnostico.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    # Gráfica 2: Precisión y Completitud (Barras agrupadas)
    metricas = {
        'Fase': ['Pre-test', 'Post-test', 'Pre-test', 'Post-test'],
        'Métrica': ['Precisión del Diagnóstico', 'Precisión del Diagnóstico', 'Completitud de Ficha', 'Completitud de Ficha'],
        'Porcentaje (%)': [porcentaje_pre, porcentaje_post, pct_completo_pre, pct_completo_post]
    }
    df_metricas = pd.DataFrame(metricas)
    
    plt.figure(figsize=(8, 5))
    ax = sns.barplot(x='Métrica', y='Porcentaje (%)', hue='Fase', data=df_metricas, palette='Set1')
    plt.title('Impacto en la Calidad del Diagnóstico Vehicular', pad=15)
    plt.ylabel('Porcentaje (%)')
    plt.ylim(0, 115)
    
    # Agregar etiquetas sobre las barras
    for p in ax.patches:
        height = p.get_height()
        if height > 0:
            ax.annotate(f'{height:.1f}%',
                        (p.get_x() + p.get_width() / 2., height),
                        ha='center', va='center',
                        xytext=(0, 8),
                        textcoords='offset points',
                        fontweight='bold')
            
    plt.savefig('documentacion/graficas/comparacion_calidad_diagnostico.png', dpi=300, bbox_inches='tight')
    plt.close()
    
    print("\n[Graficador] Graficas de caja y barra exportadas con exito en: 'documentacion/graficas/'")
except Exception as e:
    print(f"\n[Error] Error al generar las graficas: {e}")

