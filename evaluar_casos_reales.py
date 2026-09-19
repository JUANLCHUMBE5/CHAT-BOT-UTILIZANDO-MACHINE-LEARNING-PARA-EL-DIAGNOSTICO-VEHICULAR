"""
Script de evaluación y simulación de casos reales de taller para CarBot (ML + RAG + LLM).
"""

import sys
import time

sys.path.insert(0, ".")
from src.core.gestor_diagnostico import GestorDiagnostico

gestor = GestorDiagnostico()

casos_reales_taller = [
    {
        "id": 1,
        "nombre": "Falla de Misfire (Encendido / Bujías o Bobina)",
        "consulta": "cuando acelero fuerte para adelantar o subir una cuesta el carro empieza a temblar, jalonea feo y parpadea la luz del motor en el tablero",
        "falla_real": "Falla en bujias o bobinas de encendido (misfire)",
        "sistema": "Encendido / Motor",
    },
    {
        "id": 2,
        "nombre": "Inestabilidad en Ralentí (Cuerpo de Aceleración / Válvula IAC)",
        "consulta": "cada vez que llego a un semaforo piso el freno y pongo neutro el motor empieza a temblar y las revoluciones suben y bajan solas como locas hasta que de la nada se apaga, y si prendo el aire se apaga mas rapido",
        "falla_real": "Cuerpo de aceleracion o valvula IAC sucia",
        "sistema": "Admisión / Ralentí",
    },
    {
        "id": 3,
        "nombre": "Fuga Hidráulica en Frenos",
        "consulta": "el pedal de freno se va hasta el fondo y para que agarre tengo que bombearlo tres veces seguidas, siento que no frena casi nada",
        "falla_real": "Fuga hidraulica o aire en el sistema de frenos",
        "sistema": "Frenos",
    },
    {
        "id": 4,
        "nombre": "Juntas Homocinéticas / Palieres",
        "consulta": "al doblar toda la direccion a la izquierda para entrar en una curva o estacionar suena un trac trac trac constante en la rueda delantera",
        "falla_real": "Juntas homocineticas o palieres danados",
        "sistema": "Transmisión / Tracción",
    },
    {
        "id": 5,
        "nombre": "Desbalanceo de Ruedas",
        "consulta": "al pasar los 80 kilometros por hora en la pista el timon empieza a vibrar feo y se siente un temblor en las manos pero cuando bajo la velocidad se quita",
        "falla_real": "Llantas desbalanceadas o desalineadas",
        "sistema": "Dirección / Ruedas",
    },
    {
        "id": 6,
        "nombre": "Discos de Freno Alabeados",
        "consulta": "cada vez que freno a alta velocidad el pedal de freno zapatea y el timon vibra al pisar el freno pero en marcha normal anda suave",
        "falla_real": "Discos de freno alabeados o desgastados",
        "sistema": "Frenos",
    },
    {
        "id": 7,
        "nombre": "Desgaste de Pastillas de Freno",
        "consulta": "al pisar el pedal de freno suena un chirrido agudo a fierro con fierro en las ruedas delanteras y huele a quemado",
        "falla_real": "Desgaste de pastillas y zapatas de freno",
        "sistema": "Frenos",
    },
    {
        "id": 8,
        "nombre": "Embrague Patinando",
        "consulta": "piso el acelerador y el motor se revoluciona a mas de 4000 rpm pero el carro no avanza y no tiene fuerza para subir pendientes",
        "falla_real": "Disco de embrague desgastado o patinando",
        "sistema": "Transmisión / Embrague",
    },
]

print("=" * 80)
print("EVALUACIÓN EXPERIMENTAL END-TO-END DE CASOS REALES DE TALLER (ML + RAG + LLM)")
print("=" * 80 + "\n")

correctas = 0
tiempos_ml = []
tiempos_total = []

for c in casos_reales_taller:
    t0 = time.perf_counter()
    res = gestor.procesar_consulta_texto(
        texto_usuario=c["consulta"],
        placa="TEST-01",
        proveedor="meta",
    )
    t_tot = (time.perf_counter() - t0) * 1000

    pred = res.diagnostico_ml
    conf = float(res.confianza_ml or 0.0)
    coincide = pred.strip().lower() == c["falla_real"].strip().lower()
    if coincide:
        correctas += 1

    tiempos_ml.append(res.tiempo_ml_ms)
    tiempos_total.append(t_tot)

    eval_str = "[ACIERTO EXACTO]" if coincide else "[DIFERENCIAL / REVISAR]"

    print(f"CASO {c['id']}: {c['nombre']}")
    print(f"  Consulta: '{c['consulta'][:75]}...'")
    print(f"  Falla Real: {c['falla_real']}")
    print(f"  Prediccion ML: {pred} (Confianza: {int(conf * 100)}%)")
    print(f"  RAG Recuperado: {res.titulo_manual or 'Sin manual especifico'}")
    print(
        f"  Modo: {res.modo_diagnostico} | Tiempo ML: {res.tiempo_ml_ms}ms | Tiempo Total: {int(t_tot)}ms"
    )
    print(f"  Evaluacion: {eval_str}\n")

print("=" * 80)
print("RESUMEN DE METRICAS DE LA SIMULACIÓN")
print("=" * 80)
print(
    f"Exactitud en Casos Reales (PPCF): {correctas}/{len(casos_reales_taller)} ({(correctas / len(casos_reales_taller)) * 100:.1f}%)"
)
print(f"Tiempo Promedio Inferencia ML:    {sum(tiempos_ml) / len(tiempos_ml):.2f} ms")
print(f"Tiempo Promedio Pipeline Total:   {sum(tiempos_total) / len(tiempos_total):.2f} ms")
