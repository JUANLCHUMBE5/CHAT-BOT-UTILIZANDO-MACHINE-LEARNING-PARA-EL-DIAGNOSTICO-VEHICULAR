import sys
sys.stdout.reconfigure(encoding='utf-8')
from src.application.services import GestorDiagnostico

gestor = GestorDiagnostico()
texto = (
    "Anoche venía manejando y noté que los faros y las luces del tablero bajaban de intensidad y titilaban. "
    "Por ratos la radio se reiniciaba sola y las agujas del velocímetro caían a cero por un segundo. "
    "Hoy por la mañana quise prender el carro y no hizo nada, ni las luces del tablero encendieron"
)

tops = gestor.modelo_ml.predecir_top_fallas(texto, limite=5)
print("PREDICCIONES DEL MODELO ML:")
for t in tops:
    print(f" - {t['falla']}: {t['probabilidad']*100:.2f}%")
