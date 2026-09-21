import sys
from pathlib import Path
backend_dir = Path(__file__).resolve().parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from src.infrastructure.container import ServiceContainer

ml = ServiceContainer.get_modelo_ml()

queries = [
    "aire acondicionado no enfria sale aire caliente",
    "aire acondicionado no enfria casi nada detenido en semaforo sale caliente en movimiento enfria un poco",
    "presenta aire acondicionado no enfria. en semaforo sale aire a temperatura ambiente",
    "presenta perdida de potencia. cuando esta al acelerar bajo carga. con A/C encendido.",
    "el carro pierde fuerza cuando prendo el aire acondicionado en subida",
]

for q in queries:
    top = ml.predecir_top_fallas(q, limite=3)
    macro = ml.predecir_sistema(q)
    print(f"Query: {q}")
    print(f"  Macro: {macro}")
    print(f"  Top1: {top[0]['falla']} ({top[0]['probabilidad']:.4f})")
    print()
