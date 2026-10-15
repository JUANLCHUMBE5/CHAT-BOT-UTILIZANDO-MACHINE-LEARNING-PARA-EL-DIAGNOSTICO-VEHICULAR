import os

import numpy as np
import pandas as pd

# Simularemos los 60 registros de diagnóstico (30 Pre-test sin chatbot y 30 Post-test con chatbot)
# Esto le muestra al usuario cómo debe estructurar su archivo Excel real para la tesis.

np.random.seed(42)

registros = []

# --- 1. Generar 30 registros de PRE-TEST (Proceso manual tradicional) ---
for i in range(1, 31):
    registros.append({
        "item": i,
        "fase": "Pre-test",  # Proceso tradicional manual
        "fecha": f"2026-05-{i:02d}",
        "placa": f"ABC-{np.random.randint(100, 999)}",
        "marca_modelo": "Toyota Yaris",
        "sintoma": "Pedal de freno esponjoso",
        "falla_real": "Fuga de liquido de frenos",
        
        # Ficha 1: En Pre-test no hay chatbot, la predicción del mecánico depende del ojo/experiencia.
        # Asumimos que el mecánico acierta un 75% de las veces en su primer diagnóstico visual.
        "chatbot_prediccion": "Fuga de liquido de frenos" if np.random.rand() < 0.75 else "Bujias desgastadas",
        
        # Ficha 2: Control de información. En cuadernos físicos a veces se olvidan campos.
        # Asumimos que solo el 60% de los registros manuales tienen los 8 campos completos en la hoja.
        "campos_completos": 1 if np.random.rand() < 0.60 else 0,
        
        # Ficha 3: Eficiencia (tiempo en minutos). El proceso tradicional (llamar por teléfono,
        # escribir en cuaderno, inspección manual) toma en promedio 35 minutos.
        "tiempo_diagnostico_minutos": int(np.random.normal(35, 5))
    })

# --- 2. Generar 30 registros de POST-TEST (Proceso con tu Chatbot ML) ---
for i in range(31, 61):
    registros.append({
        "item": i,
        "fase": "Post-test",  # Proceso con Chatbot
        "fecha": f"2026-06-{i-30:02d}",
        "placa": f"XYZ-{np.random.randint(100, 999)}",
        "marca_modelo": "Hyundai Accent",
        "sintoma": "Timon tiembla a alta velocidad",
        "falla_real": "Llantas desalineadas",
        
        # Ficha 1: El Chatbot de ML tiene mayor precisión (ej. 90%)
        "chatbot_prediccion": "Llantas desalineadas" if np.random.rand() < 0.90 else "Amortiguadores reventados",
        
        # Ficha 2: El chatbot obliga a llenar los campos antes de dar el diagnóstico.
        # Por lo tanto, el 100% de los registros digitales están completos.
        "campos_completos": 1,
        
        # Ficha 3: Eficiencia. Con el chatbot, el registro y predicción toma promedio 10 minutos.
        "tiempo_diagnostico_minutos": int(np.random.normal(10, 2))
    })

df = pd.DataFrame(registros)

# Crear columna indicando si la predicción fue correcta (Ficha 1)
df['prediccion_correcta'] = (df['falla_real'] == df['chatbot_prediccion']).astype(int)

# Guardar a archivo CSV para abrir en Excel
os.makedirs("data", exist_ok=True)
df.to_csv("data/tracker_diagnosticos.csv", index=False, encoding="utf-8")

print("=" * 70)
print("¡Archivo 'data/tracker_diagnosticos.csv' generado exitosamente!")
print("Contiene la simulación de tus 60 casos (30 Pre-test y 30 Post-test).")
print("Puedes abrir este archivo en Excel para ver cómo estructurar tus datos reales.")
print("=" * 70)
