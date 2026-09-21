import sys
sys.stdout.reconfigure(encoding='utf-8')
from src.application.services import GestorDiagnostico

gestor = GestorDiagnostico()

consultas_nuevas = [
    # Mangueras / radiador
    "Encontré un charco de líquido verde fosforescente debajo del motor en la mañana y el tanque de expansión está seco",
    # FSCM / PEM
    "El auto se apaga de golpe en carretera como si le cortaran la corriente de combustible, luego de enfriar 15 minutos vuelve a encender normal",
    # DPF / FAP
    "Luz de advertencia del filtro de partículas DPF encendida fija en el tablero con pérdida notoria de fuerza y humo picante",
    # VVT-i
    "El motor cascabelea feo al subir cuestas a 2500 RPM y el escáner arroja código DTC P0011 de fase avanzada del árbol de levas",
    # Faja bañada en aceite
    "Testigo rojo de presión de aceite titila en el tablero al calentar el motor 1.0 Dragon de faja bañada en aceite",
    # Dualogic robotizada
    "Mensaje en el tablero 'Hacer controlar el cambio' y la transmisión se salta a Neutro sola en pleno tráfico",
    # Flex
    "El auto flex no quiere arrancar en las mañanas frías, gira el arranque pesado y ahoga las bujías de olor a alcohol",
    # Alternador
    "Anoche venía manejando y noté que los faros y las luces del tablero bajaban de intensidad y titilaban, la radio se reiniciaba sola"
]

print("=" * 80)
print("TEST DE INFERENCIA SOBRE CASOS ENRIQUECIDOS:")
print("=" * 80)
for c in consultas_nuevas:
    tops = gestor.modelo_ml.predecir_top_fallas(c, limite=1)
    p = tops[0]
    print(f"\nConsulta: \"{c[:70]}...\"")
    print(f" -> Predicción: {p['falla']} ({p['probabilidad']*100:.1f}%)")
