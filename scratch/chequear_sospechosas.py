import pandas as pd
from pathlib import Path

base_dir = Path('.').resolve()
df_f10 = pd.read_csv(base_dir / "machine_learning/data/fase10/auditoria_etapa31/taxonomia_fase10.csv")
classes = list(df_f10['clase'])

suspicious = [
    "Cremallera de direccion asistida electrica (EPS) o sensor de torque",
    "Fallo en modulo de control electronico (PCM / ECM / BCM)",
    "Falla en sensor de angulo de direccion (SAS) o calibracion ESP",
    "Falla en modulo de freno de mano electrico (EPB) o motor de pinza",
    "Valvula moduladora ABS o sensor de presion de frenos de aire (Camiones)",
    "Falla en suspension neumatica (compresor, balonas o valvulas)",
    "Desgaste de zapatas o tambores de freno trasero"
]

print("Check suspicious labels in 61 classes:")
for s in suspicious:
    in_classes = s in classes
    print(f"'{s}' in classes? {in_classes}")
    if not in_classes:
        # find partial match
        partials = [c for c in classes if any(word.lower() in c.lower() for word in s.split() if len(word) > 4)]
        print(f"  Closest matches: {partials[:3]}")
