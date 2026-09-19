import sys
sys.stdout.reconfigure(encoding='utf-8')
from src.application.services import GestorDiagnostico

gestor = GestorDiagnostico()

casos_prueba = [
    # 1. El caso original del usuario
    "Anoche venía manejando y noté que los faros y las luces del tablero bajaban de intensidad y titilaban. Por ratos la radio se reiniciaba sola y las agujas del velocímetro caían a cero por un segundo. Hoy por la mañana quise prender el carro y no hizo nada, ni las luces del tablero encendieron",
    # 2. Variante con zumbido y luces parpadeantes en movimiento
    "El alternador empezó a zumbar y los faros alumbran amarillos y titilan cuando acelero de noche, la radio se apaga y el carro se apagó rodando",
    # 3. Testigo de batería y bajón de faros en carretera
    "Iba en la autopista y la luz roja de la batería parpadeaba tenue, los faros perdieron brillo de golpe y la radio se reinició, al apagarlo ya no dio arranque",
    # 4. Caso puro de batería descargada en cochera
    "Dejé el auto parado 5 días en la cochera y hoy que quise encenderlo no hace nada, la batería no tiene fuerza ni para mover el arranque",
    # 5. Bornes sulfatados
    "Los bornes de la batería están con bastante sarro blanco y polvo verde, hace falso contacto al mover los cables pero al pasar corriente prende normal"
]

print("=" * 80)
print("EVALUACIÓN DE CASOS DE PRUEBA TRAS LA EXPANSIÓN:")
print("=" * 80)
for i, texto in enumerate(casos_prueba, 1):
    tops = gestor.modelo_ml.predecir_top_fallas(texto, limite=2)
    p1, p2 = tops[0], tops[1] if len(tops) > 1 else {"falla": "N/A", "probabilidad": 0.0}
    print(f"\nCaso {i}: \"{texto[:75]}...\"")
    print(f" -> Top 1: {p1['falla']} ({p1['probabilidad']*100:.1f}%)")
    print(f" -> Top 2: {p2['falla']} ({p2['probabilidad']*100:.1f}%)")
