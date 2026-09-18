import sys
import json
from pathlib import Path

base_dir = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(base_dir / "backend"))

from src.infrastructure.container import ServiceContainer
from src.core.diagnostico.taxonomia_sistemas import obtener_macro_sistema, TAXONOMIA_MACRO_SISTEMAS

ServiceContainer.reset()
modelo_ml = ServiceContainer.get_modelo_ml()

consultas_smoke = [
    ("siento que al frenar de golpe el pedal vibra y se escucha un chillido metálico en las ruedas delanteras", "FRENOS"),
    ("la aguja de temperatura sube al rojo en tráfico y el ventilador no arranca", "MOTOR"),
    ("al pasar los cambios de primera a segunda raspa la caja y cuesta que entre", "TRANSMISION"),
    ("en los baches suena un golpe seco clac clac en la llanta derecha delantera", "SUSPENSION_CHASIS"),
    ("por las mañanas el auto no gira motor, solo suena un tic y las luces del tablero se apagan", "ELECTRICO"),
    ("prendo el aire acondicionado pero solo bota aire caliente por las rejillas del tablero", "CLIMATIZACION"),
    ("la ventana del lado del copiloto no sube ni baja cuando presiono el botón de la puerta", "CARROCERIA_NEUMATICA"),
    ("el motor tose y tironea en baja revoluciones con la luz check engine parpadeando", "MOTOR"),
]

clases_validas_falla = set(modelo_ml.modelo.classes_)
clases_validas_macro = set(modelo_ml.modelo_sistema.classes_)

resultados_smoke = []
todo_ok = True

print(f"{'#':<3} {'Macro Esperado':<22} {'Macro Predicho':<22} {'Conf Macro':<10} {'Falla Top-1':<50} {'Conf Falla':<10}")
print("-" * 125)

for idx, (txt, macro_exp) in enumerate(consultas_smoke, 1):
    top3 = modelo_ml.predecir_top_fallas(txt, limite=3)
    macro_pred = modelo_ml.predecir_sistema(txt)
    
    assert len(top3) == 3, f"Expected Top-3, got {len(top3)}"
    for item in top3:
        assert item["falla"] in clases_validas_falla, f"Class {item['falla']} not in 61 taxonomy classes!"
        assert 0.0 <= item["probabilidad"] <= 1.0, f"Invalid prob {item['probabilidad']}"
    
    assert macro_pred in clases_validas_macro, f"Macro {macro_pred} not in 7 macro classes!"
    
    top1 = top3[0]
    macro_top1 = obtener_macro_sistema(top1["falla"])
    
    print(f"{idx:<3} {macro_exp:<22} {macro_pred:<22} {'N/A':<10} {top1['falla'][:48]:<50} {top1['probabilidad']:<10.4f}")
    resultados_smoke.append({
        "id": idx,
        "texto": txt,
        "macro_esperado": macro_exp,
        "macro_predicho": macro_pred,
        "falla_top1": top1["falla"],
        "confianza_top1": top1["probabilidad"],
        "top3": top3,
        "clases_en_taxonomia": True
    })

print("\nSmoke test completado: 8/8 consultas ejecutadas con éxito.")
print("0 excepciones, 0 clases fuera de taxonomía, 0 macros inválidos.")
