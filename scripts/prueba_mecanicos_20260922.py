"""Sondeo sintético del pipeline real; no registra casos oficiales ni envía WhatsApp."""
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from src.config_bootstrap import cargar_variables_entorno

cargar_variables_entorno()
from src.config import settings

settings.database.enabled = False
settings.database.required = False
from src.core.gestor_diagnostico import GestorDiagnostico

# Expectativas definidas antes de ejecutar. Coincidencia por familia, no pieza confirmada.
CASOS = [
    ("Frenos", "discos", "Soy mecánico. El volante vibra solamente al frenar desde 80 km/h. Sin frenar no vibra. Medí alabeo lateral en los discos delanteros fuera de tolerancia. Pastillas parejas.", ["disco", "alabe"]),
    ("Encendido", "bujías/bobinas", "En el taller tengo un motor a gasolina que tironea y pierde fuerza al subir. Sale P0302. Intercambié la bobina del cilindro 2 al 3 y el fallo cambió a P0303.", ["bobina", "bujia", "bujía"]),
    ("Carga", "alternador", "El cliente dice que se prende la luz de batería andando. Medí 12.1 V con motor encendido y baja al prender luces. La correa está puesta y los bornes están firmes.", ["alternador", "carga"]),
    ("Arranque", "batería/bornes", "Al dar arranque hace varios clics rápidos y las luces se apagan. La batería marca 12 V en reposo y cae a 7 V al intentar arrancar. Con batería de apoyo arranca.", ["bateria", "batería", "borne"]),
    ("Embrague", "embrague", "Caja manual: en cuarta al acelerar las revoluciones suben mucho pero la velocidad no aumenta. En subida empeora y huele a forro quemado. El motor no tironea.", ["embrague"]),
    ("Refrigeración", "electroventilador", "Sube la temperatura parado en tráfico, pero en carretera vuelve a normal. Hay refrigerante y no veo fugas. El electroventilador no gira cuando calienta.", ["ventilador", "refrigeracion", "refrigeración"]),
    ("Suspensión", "bujes/rótulas", "Suena cloc cloc adelante al pasar baches. En pista lisa no suena. En elevador encontré juego en la rótula inferior y goma del buje rota. Al frenar no vibra.", ["rotula", "rótula", "buje", "suspension", "suspensión"]),
    ("Dirección", "homocinética", "Cuando giro todo el volante y avanzo despacio acelerando suena tac tac tac cerca de la rueda. En línea recta no suena. El guardapolvo de la junta exterior está roto y salió grasa.", ["homocinetica", "homocinética", "junta"]),
    ("Climatización", "refrigerante/fuga AC", "El aire acondicionado sopla fuerte pero no enfría. El compresor acopla. Detectamos fuga de refrigerante en una unión y presión baja. La temperatura del motor es normal.", ["refrigerante", "fuga", "aire acondicionado"]),
    ("Transmisión", "transmisión automática", "Carro automático: en D entra normal. En R demora varios segundos, debo acelerar un poco y entra con golpe. Hacia adelante cambia normal. Sin luces en tablero. No he revisado nada.", ["transmision", "transmisión", "caja", "atf", "solenoide"]),
]


def main():
    gestor = GestorDiagnostico()
    # Solo se desactiva la escritura del tracker; ML/RAG/LLM conservan su implementación.
    gestor._registrar_en_tracker = lambda **kwargs: None
    resultados = []
    nombre = "prueba_mecanicos_20260922_mejorado.json" if "--mejorado" in sys.argv else "prueba_mecanicos_20260922.json"
    if "--final" in sys.argv:
        nombre = "prueba_mecanicos_20260923_final.json"
    salida = ROOT / "docs/operacion" / nombre
    if salida.exists():
        raise RuntimeError("La evidencia ya existe; no se sobrescribe una ejecución anterior.")
    for i, (sistema, esperado, texto, terminos) in enumerate(CASOS, 1):
        if "--final" in sys.argv and i not in (7, 10):
            continue
        inicio = time.perf_counter()
        fila = dict(id=i, sistema=sistema, esperado=esperado, texto=texto, criterios=terminos)
        try:
            res = gestor.procesar_consulta_texto(
                texto, session_id=f"PILOTO-SINTETICO-20260922-{i}",
                marca_modelo="Vehiculo Generico", diferir_encolado_persistente=True,
            )
            fila["resultado"] = res.model_dump(mode="json")
            top = [p.falla.lower() for p in res.predicciones_ml[:3]]
            fila["familia_top1"] = any(t in res.diagnostico_ml.lower() for t in terminos)
            fila["familia_top3"] = any(t in p for p in top for t in terminos)
            fila["segundos"] = round(time.perf_counter() - inicio, 2)
            print(i, sistema, res.diagnostico_ml, res.modo_diagnostico, res.llm_usado, flush=True)
        except Exception as exc:
            fila["error"] = type(exc).__name__
            print(i, sistema, fila["error"], flush=True)
        resultados.append(fila)
        salida.write_text(json.dumps(resultados, ensure_ascii=False, indent=2), encoding="utf-8")
        time.sleep(6)


if __name__ == "__main__":
    main()
