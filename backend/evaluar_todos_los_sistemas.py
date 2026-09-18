"""
Script integral de evaluación para CarBot cubriendo TODOS los sistemas automotrices (14 subsistemas).
Valida: Pipeline End-to-End (Clasificador de Intención -> NLP -> Linear SVM TF-IDF -> FAISS RAG -> LLM).
"""

import sys
import time

sys.path.insert(0, ".")
from src.core.gestor_diagnostico import GestorDiagnostico

gestor = GestorDiagnostico()

# Batería completa de pruebas representando todas las familias/subsistemas vehiculares de la taxonomía
CASOS_TODOS_LOS_SISTEMAS = [
    # 1. FRENO CONVENCIONAL
    {
        "id": 1,
        "subsistema": "Frenos Hidráulicos / Pastillas",
        "consulta": "al pisar el pedal de freno suena un chirrido agudo a fierro con fierro en las ruedas delanteras y huele a quemado",
        "falla_esperada": "Desgaste de pastillas y zapatas de freno",
    },
    {
        "id": 2,
        "subsistema": "Frenos Hidráulicos / Fuga y Líquido",
        "consulta": "el pedal de freno se va hasta el fondo y para que agarre tengo que bombearlo tres veces seguidas, siento que no frena casi nada",
        "falla_esperada": "Fuga hidraulica o aire en el sistema de frenos",
    },
    {
        "id": 3,
        "subsistema": "Frenos Hidráulicos / Discos Alabeados",
        "consulta": "cada vez que freno a alta velocidad el pedal de freno zapatea y el timon vibra al pisar el freno pero en marcha normal anda suave",
        "falla_esperada": "Discos de freno alabeados o desgastados",
    },
    # 2. FRENOS NEUMÁTICOS (CAMIONES)
    {
        "id": 4,
        "subsistema": "Frenos Neumáticos (Camiones)",
        "consulta": "en el camion se escucha un escape de aire continuo por los pulmones de freno traseros y la presion de aire en los tanques no sube de 4 bares",
        "falla_esperada": "Fugas de aire o fallos en el sistema de frenos neumático (Camiones)",
    },
    # 3. MOTOR Y ENCENDIDO
    {
        "id": 5,
        "subsistema": "Motor / Encendido (Misfire)",
        "consulta": "cuando acelero fuerte para adelantar o subir una cuesta el carro empieza a temblar, jalonea feo y parpadea la luz del motor en el tablero",
        "falla_esperada": "Falla en bujias o bobinas de encendido (misfire)",
    },
    {
        "id": 6,
        "subsistema": "Motor / Empaque de Culata",
        "consulta": "el motor calienta rapido, bota bastante humo blanco con olor dulce por el tubo de escape y al revisar la tapa del aceite parece cafe con leche",
        "falla_esperada": "Empaque de culata soplado o danado",
    },
    {
        "id": 7,
        "subsistema": "Motor / Distribución",
        "consulta": "se escucho un golpe seco en la tapa de distribucion y el motor se apago al instante, al dar arranque gira liviano y rapido pero no arranca porque parece que salto el punto",
        "falla_esperada": "Faja o cadena de distribucion destensada o con salto de punto",
    },
    # 4. INYECCIÓN Y COMBUSTIBLE
    {
        "id": 8,
        "subsistema": "Inyección Gasolina / Ralentí IAC",
        "consulta": "cada vez que llego a un semaforo piso el freno y pongo neutro el motor empieza a temblar y las revoluciones suben y bajan solas como locas hasta que de la nada se apaga, y si prendo el aire se apaga mas rapido",
        "falla_esperada": "Cuerpo de aceleracion o valvula IAC sucia",
    },
    {
        "id": 9,
        "subsistema": "Inyección Gasolina / Bomba de Combustible",
        "consulta": "abro el contacto del carro y ya no suena el zumbido de la bomba de gasolina en el tanque, doy arranque gira el motor pero no llega nada de combustible al riel",
        "falla_esperada": "Bomba de gasolina quemada o con baja presion",
    },
    {
        "id": 10,
        "subsistema": "Inyección Diésel / Common Rail",
        "consulta": "la camioneta diesel tarda mucho en arrancar por las mananas, arroja codigo de baja presion de riel common rail y la valvula reguladora de presion no mantiene el flujo",
        "falla_esperada": "Fuga o baja presion en sistema Common Rail Diesel (Camiones/Pickups)",
    },
    # 5. TRANSMISIÓN Y EMBRAGUE
    {
        "id": 11,
        "subsistema": "Embrague / Disco Patinando",
        "consulta": "piso el acelerador y el motor se revoluciona a mas de 4000 rpm pero el carro no avanza y no tiene fuerza para subir pendientes",
        "falla_esperada": "Disco de embrague desgastado o patinando",
    },
    {
        "id": 12,
        "subsistema": "Embrague / Bombín Hidráulico",
        "consulta": "el pedal de embrague se quedo pegado en el piso del carro y no entran los cambios primera ni retroceso y hay charco de liquido de embrague abajo",
        "falla_esperada": "Falla en bombin o bomba hidraulica de embrague",
    },
    {
        "id": 13,
        "subsistema": "Transmisión Automática / CVT",
        "consulta": "la caja automatica cvt empieza a patinar cuando calienta en carretera y sale mensaje de sobrecalentamiento de transmision con los cambios trabados",
        "falla_esperada": "Sobrecalentamiento o solenoides en caja automatica CVT / DSG",
    },
    # 6. REFRIGERACIÓN
    {
        "id": 14,
        "subsistema": "Refrigeración / Termostato y Electroventilador",
        "consulta": "la aguja de temperatura llega a la zona roja cuando estoy detenido en el trafico porque el electroventilador no activa ni gira y la manguera inferior del radiador esta fria",
        "falla_esperada": "Falla en termostato o motoventilador de radiador",
    },
    # 7. SISTEMA ELÉCTRICO Y CARGA
    {
        "id": 15,
        "subsistema": "Eléctrico / Alternador",
        "consulta": "en pleno viaje se encendio la luz de la bateria en el tablero, las luces delanteras bajaron de intensidad y al medir con multimetro el alternador solo bota 11.5 voltios",
        "falla_esperada": "Alternador defectuoso o placa de diodos quemada",
    },
    {
        "id": 16,
        "subsistema": "Eléctrico / Batería o Arranque",
        "consulta": "al girar la llave para encender el carro solo hace un tac tac tac en el arrancador solenoide y las luces del tablero se apagan por completo",
        "falla_esperada": "Bateria descargada o bornes sulfatados",
    },
    # 8. SUSPENSIÓN Y DIRECCIÓN
    {
        "id": 17,
        "subsistema": "Suspensión / Amortiguadores",
        "consulta": "al pasar por baches o romperresortes el carro rebota como un barco varias veces y el amortiguador delantero derecho esta todo chorreado de aceite",
        "falla_esperada": "Amortiguadores reventados o bujes de suspension gastados",
    },
    {
        "id": 18,
        "subsistema": "Suspensión / Juntas Homocinéticas",
        "consulta": "al doblar toda la direccion a la izquierda para entrar en una curva o estacionar suena un trac trac trac constante en la rueda delantera",
        "falla_esperada": "Juntas homocineticas o palieres danados",
    },
    {
        "id": 19,
        "subsistema": "Dirección / Desbalanceo",
        "consulta": "al pasar los 80 kilometros por hora en la pista el timon empieza a vibrar feo y se siente un temblor en las manos pero cuando bajo la velocidad se quita",
        "falla_esperada": "Llantas desbalanceadas o desalineadas",
    },
    # 9. CLIMATIZACIÓN
    {
        "id": 20,
        "subsistema": "Climatización / Aire Acondicionado",
        "consulta": "prendo el aire acondicionado del carro en frio pero solo bota aire tibio normal, no enfria nada y no se escucha acoplar el compresor ni tiene gas r134a",
        "falla_esperada": "Falla en compresor de aire acondicionado o fuga de gas R134a",
    },
    # 10. SOBREALIMENTACIÓN Y TURBO
    {
        "id": 21,
        "subsistema": "Sobrealimentación / Intercooler y Turbo",
        "consulta": "cuando acelero a fondo se escucha un silbido fuerte o soplido como de aire a presion en el motor y la manguera del intercooler tiene una raja perdiendo presion de turbo",
        "falla_esperada": "Fuga en mangueras de intercooler o turbocompresor danado",
    },
    # 11. ESCAPE Y EMISIONES (DIÉSEL DPF)
    {
        "id": 22,
        "subsistema": "Emisiones / Filtro de Partículas DPF",
        "consulta": "en el tablero de la camioneta diesel se prendio la luz del filtro de particulas dpf y mensaje de revisar sistema adblue, el motor entro en modo emergencia sin fuerza",
        "falla_esperada": "Falla en filtro de particulas DPF / FAP y sistema AdBlue DEF (Diesel Euro 5/6)",
    },
    # 12. CARROCERÍA Y CONFORT
    {
        "id": 23,
        "subsistema": "Carrocería / Alzacristales",
        "consulta": "presiono el boton de la puerta para subir la ventana del copiloto y solo suena un traqueteo en el alzacristales y el vidrio se quedo trabado abajo",
        "falla_esperada": "Elevalunas electrico o guaya de alzacristales rota o trabada",
    },
    # 13. VEHÍCULOS HÍBRIDOS Y ELÉCTRICOS (EV / HEV)
    {
        "id": 24,
        "subsistema": "Vehículos Híbridos / Batería HV",
        "consulta": "en el auto hibrido toyota prius salio alerta en la pantalla de revisar sistema hibrido con codigo p0a80 por degradacion en las celdas de la bateria de alto voltaje",
        "falla_esperada": "Degradacion o falla en paquete de bateria de alto voltaje (EV / Hibridos)",
    },
]

print("=" * 85)
print("BENCHMARK GLOBAL DE DIAGNÓSTICO VEHICULAR - TODOS LOS TIPOS DE CASOS (ML + RAG + LLM)")
print("Total de Casos Evaluados:", len(CASOS_TODOS_LOS_SISTEMAS))
print("=" * 85 + "\n")

aciertos = 0
tiempos_ml = []
tiempos_totales = []
resultados_por_subsistema = {}

for c in CASOS_TODOS_LOS_SISTEMAS:
    t0 = time.perf_counter()
    res = gestor.procesar_consulta_texto(
        texto_usuario=c["consulta"],
        placa="EVAL-FULL",
        proveedor="meta",
    )
    t_tot = (time.perf_counter() - t0) * 1000

    pred = res.diagnostico_ml or ""
    conf = float(res.confianza_ml or 0.0)

    # Normalización para cotejo
    pred_clean = pred.strip().lower()
    esp_clean = c["falla_esperada"].strip().lower()
    es_acierto = pred_clean == esp_clean

    if es_acierto:
        aciertos += 1
        status = "ACIERTO"
    else:
        status = "DESVIADO"

    tiempos_ml.append(res.tiempo_ml_ms)
    tiempos_totales.append(t_tot)

    sub = c["subsistema"]
    if sub not in resultados_por_subsistema:
        resultados_por_subsistema[sub] = {"total": 0, "aciertos": 0}
    resultados_por_subsistema[sub]["total"] += 1
    if es_acierto:
        resultados_por_subsistema[sub]["aciertos"] += 1

    print(f"[{c['id']:02d}] {sub}")
    print(f"     Consulta: '{c['consulta'][:80]}...'")
    print(f"     Esperado:   {c['falla_esperada']}")
    print(f"     Predicho:   {pred} ({int(conf * 100)}%) -> [{status}]")
    print(f"     Manual RAG: {res.titulo_manual or 'Sin manual OEM'}")
    print(f"     Latencia:   ML={res.tiempo_ml_ms}ms | Total={int(t_tot)}ms | Modo={res.modo_diagnostico}")
    print("-" * 85)

print("\n" + "=" * 85)
print("RESUMEN DE RESULTADOS POR COBERTURA DE SUBSISTEMAS")
print("=" * 85)
for sub, stats in resultados_por_subsistema.items():
    pct = (stats["aciertos"] / stats["total"]) * 100
    print(f"- {sub:<45}: {stats['aciertos']}/{stats['total']} ({pct:.0f}%)")

print("\n" + "=" * 85)
print("MÉTRICAS TOTALES DE RENDIMIENTO")
print("=" * 85)
acc = (aciertos / len(CASOS_TODOS_LOS_SISTEMAS)) * 100
avg_ml = sum(tiempos_ml) / len(tiempos_ml)
avg_tot = sum(tiempos_totales) / len(tiempos_totales)
print(f"Exactitud Global (PPCF):          {aciertos}/{len(CASOS_TODOS_LOS_SISTEMAS)} ({acc:.1f}%)")
print(f"Tiempo Promedio Inferencia ML:    {avg_ml:.2f} ms")
print(f"Tiempo Promedio Pipeline Completo:{avg_tot:.2f} ms")
print("=" * 85)
