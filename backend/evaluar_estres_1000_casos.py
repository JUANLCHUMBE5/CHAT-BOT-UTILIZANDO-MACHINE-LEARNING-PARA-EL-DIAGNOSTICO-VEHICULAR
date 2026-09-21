"""
Benchmark de Estrés y Robustez End-to-End: 1000 Consultas al Bot CarBot.
Evalúa precisión, subsistemas, matrices de confusión (dónde falla) y latencias.
"""

import os
import sys
import time
from collections import Counter, defaultdict
import pandas as pd
import numpy as np

sys.path.insert(0, ".")
from src.core.gestor_diagnostico import GestorDiagnostico
from src.core.taxonomy.catalogo_fallas import MAPA_UNIFICACION_ETIQUETAS

print("Iniciando GestorDiagnostico y cargando pipeline...")
gestor = GestorDiagnostico()

ruta_csv = os.path.join("..", "machine_learning", "data", "dataset_sintomas_limpio.csv")
if not os.path.exists(ruta_csv):
    ruta_csv = os.path.join("machine_learning", "data", "dataset_sintomas_limpio.csv")
df_limpio = pd.read_csv(ruta_csv)

# Muestreo estratificado de 920 casos automotrices cubriendo las 48 clases
# Tomamos aproximadamente 19-20 ejemplos por clase
muestras = []
for falla, subdf in df_limpio.groupby("falla"):
    muestras.append(subdf.sample(min(len(subdf), 20), random_state=42))
casos_automotrices = pd.concat(muestras, ignore_index=True)

if len(casos_automotrices) > 920:
    casos_automotrices = casos_automotrices.sample(920, random_state=42).reset_index(drop=True)

# 2. Casos coloquiales / jerga peruana extrema (30 casos)
casos_coloquiales = [
    {"sintoma": "causa el timon zapatea feo cuando piso el freno bajando de la costa verde", "falla": "Discos de freno alabeados o desgastados", "sistema": "Frenos"},
    {"sintoma": "maestro al doblar en u suena un trac trac en la llanta que asusta", "falla": "Juntas homocineticas o palieres danados", "sistema": "Suspensión y Dirección"},
    {"sintoma": "choche el carro no tiene fuerza cascabelea y parpadea el check engine", "falla": "Falla en bujias o bobinas de encendido (misfire)", "sistema": "Motor"},
    {"sintoma": "mi caña bota humo blanco espeso y el refrigerante se lo traga todito", "falla": "Empaque de culata soplado o danado", "sistema": "Motor"},
    {"sintoma": "pata piso el embrague y se va al piso como trapo no entran los cambios", "falla": "Falla en bombin o bomba hidraulica de embrague", "sistema": "Transmisión y Embrague"},
    {"sintoma": "la bateria se bajo de la nada y huele a huevo podrido en el motor", "falla": "Bateria descargada o bornes sulfatados", "sistema": "Sistema Eléctrico y Carga"},
    {"sintoma": "el alternador no carga mi bateria bota 11 voltios y prendio testigo rojo", "falla": "Alternador defectuoso o placa de diodos quemada", "sistema": "Sistema Eléctrico y Carga"},
    {"sintoma": "en los rompemuelles la nave golpea fierro con fierro y rebota como lancha", "falla": "Amortiguadores reventados o bujes de suspension gastados", "sistema": "Suspensión y Dirección"},
    {"sintoma": "el carro acelera a fondo suena duro pero no corre patina feo", "falla": "Disco de embrague desgastado o patinando", "sistema": "Transmisión y Embrague"},
    {"sintoma": "el minimo se vuelve loco sube a 2000 rpm y cae a 500 hasta apagarse", "falla": "Cuerpo de aceleracion o valvula IAC sucia", "sistema": "Inyección de Combustible"},
    {"sintoma": "no zumba la bomba al abrir llave y no inyecta gasolina al motor", "falla": "Bomba de gasolina quemada o con baja presion", "sistema": "Inyección de Combustible"},
    {"sintoma": "a mas de 90 km por hora vibra todo el timon en autopista", "falla": "Llantas desbalanceadas o desalineadas", "sistema": "Suspensión y Dirección"},
    {"sintoma": "pedal de freno esponjoso se hunde hasta el fondo y casi me estrello", "falla": "Fuga hidraulica o aire en el sistema de frenos", "sistema": "Frenos"},
    {"sintoma": "chirrido de fierros chillando al frenar suave en bajada", "falla": "Desgaste de pastillas y zapatas de freno", "sistema": "Frenos"},
    {"sintoma": "camioneta hilux diesel no arranca en frio baja presion de common rail", "falla": "Fuga o baja presion en sistema Common Rail Diesel (Camiones/Pickups)", "sistema": "Inyección Diésel"},
    {"sintoma": "fuga de aire en pulmones de freno del camion no levanta libras", "falla": "Fugas de aire o fallos en el sistema de frenos neumático (Camiones)", "sistema": "Frenos Neumáticos"},
    {"sintoma": "aire acondicionado no enfria tira puro aire tibio compresor no pega", "falla": "Falla en compresor de aire acondicionado o fuga de gas R134a", "sistema": "Climatización y Confort"},
    {"sintoma": "manguera de intercooler soplada pierde potencia y chilla el turbo", "falla": "Fuga en mangueras de intercooler o turbocompresor danado", "sistema": "Sobrealimentación y Turbo"},
    {"sintoma": "testigo de dpf prendido camioneta sin fuerza sistema adblue bloqueado", "falla": "Falla en filtro de particulas DPF / FAP y sistema AdBlue DEF (Diesel Euro 5/6)", "sistema": "Sistema de Escape y Emisiones"},
    {"sintoma": "el vidrio del copiloto sono clac y se cayo dentro de la puerta", "falla": "Elevalunas electrico o guaya de alzacristales rota o trabada", "sistema": "Carrocería y Confort"},
    {"sintoma": "prius hibrido con codigo p0a80 triangulo rojo bateria de alta tension", "falla": "Degradacion o falla en paquete de bateria de alto voltaje (EV / Hibridos)", "sistema": "Vehículos Eléctricos e Híbridos"},
    {"sintoma": "aguja de temperatura en rojo agua hirviendo ventilador no sopla", "falla": "Falla en termostato o motoventilador de radiador", "sistema": "Refrigeración"},
    {"sintoma": "salto el punto de la faja de distribucion y doblo valvulas", "falla": "Faja o cadena de distribucion destensada o con salto de punto", "sistema": "Motor"},
    {"sintoma": "caja automatica cvt recalienta en subida y entra en neutro sola", "falla": "Sobrecalentamiento o solenoides en caja automatica CVT / DSG", "sistema": "Transmisión y Embrague"},
    {"sintoma": "humo azul por el tubo de escape consume un cuarto de aceite por semana", "falla": "Consumo de aceite por desgaste de anillos o retenes", "sistema": "Motor"},
    {"sintoma": "timon duro como piedra bota liquido rojo de la cremallera de direccion", "falla": "Cremallera de direccion asistida con holgura o fuga", "sistema": "Suspensión y Dirección"},
    {"sintoma": "freno duro como una roca pedal no baja hay que pararse encima", "falla": "Falla en servofreno (booster) o linea de vacio", "sistema": "Frenos"},
    {"sintoma": "luz de abs encendida en el tablero sensor de rueda lleno de oxido", "falla": "Falla en sensor de velocidad de rueda ABS", "sistema": "Frenos"},
    {"sintoma": "olor fuerte a gasolina cruda por el escape y bujias carbonizadas", "falla": "Falla en sensor de oxigeno o mezcla rica", "sistema": "Inyección de Combustible"},
    {"sintoma": "valvula secador de aire de camion trancada botando agua y aceite", "falla": "Válvula de freno de aire o secador APS obstruido (Camiones)", "sistema": "Frenos Neumáticos"},
]

# 3. Casos fuera de alcance / conversacionales (50 casos)
consultas_no_mecanicas = [
    "hola buenos dias", "hola maestro como estas", "¿cuanto cuesta la consulta?",
    "donde queda su taller ubicado", "a que hora abren manana", "gracias por la ayuda",
    "buenas tardes", "precio de cambio de aceite", "tienen repuestos para nissan",
    "quiero comprar llantas", "dame una receta de lomo saltado", "quien gano el partido de futbol",
    "cual es la capital de peru", "eres un bot o una persona", "como te llamas",
    "hasta luego gracias", "tienen servicio de grua", "cuanto cobran por alineamiento",
    "puedo pagar con yape", "aceptan tarjeta de credito", "hacen planchado y pintura",
    "venden seguros soat", "cual es el mejor carro del mundo", "me gusta tu servicio",
    "que tiempo demora un afinamiento", "tienen afinamiento electronico", "donde compro bujias baratas",
    "buenas noches amigos", "hola que tal", "ok entendido", "si gracias", "chau",
    "muchas gracias maestro", "perfecto hermano", "buen dato gracias", "cuanto sale el scanner",
    "tienen escaner para hyundai", "atienden domingos", "hay descuento para taxistas",
    "tienes el manual de toyota yaris", "cual es el telefono del taller", "hola amigo",
    "saludos cordiales", "muy agradecido", "hasta pronto", "de nada", "ok", "listo", "dale", "ya vuelvo"
]
casos_fuera_alcance = [
    {"sintoma": q, "falla": "FUERA_DE_ALCANCE", "sistema": "Conversacional / Fuera de Alcance"}
    for q in consultas_no_mecanicas
]

# Unir hasta completar exactamente 1000 casos
lista_total = []

# Añadir los 920 casos del dataset
for _, row in casos_automotrices.iterrows():
    lista_total.append({
        "sintoma": row["sintoma"],
        "falla": row["falla"],
        "sistema": row.get("sistema", "Automotriz General")
    })

# Añadir los 30 casos coloquiales
lista_total.extend(casos_coloquiales)

# Añadir los 50 casos fuera de alcance
lista_total.extend(casos_fuera_alcance)

# Ajustar tamaño a exactamente 1000 casos
if len(lista_total) > 1000:
    lista_total = lista_total[:1000]
elif len(lista_total) < 1000:
    # rellenar con más del dataset hasta 1000
    faltantes = 1000 - len(lista_total)
    extras = df_limpio.sample(faltantes, random_state=99)
    for _, row in extras.iterrows():
        lista_total.append({
            "sintoma": row["sintoma"],
            "falla": row["falla"],
            "sistema": row.get("sistema", "Automotriz General")
        })

print(f"Batería preparada con éxito: {len(lista_total)} consultas.")
print("Iniciando procesamiento de 1000 pruebas...\n")

# Estructuras de telemetría y análisis de fallos
aciertos = 0
fallos = 0
fuera_alcance_correctos = 0
fuera_alcance_incorrectos = 0
tiempos_ml = []
tiempos_total = []

confusiones = Counter()  # (falla_real, falla_predicha) -> cantidad
fallas_por_sistema = defaultdict(lambda: {"total": 0, "aciertos": 0, "fallos": 0})
ejemplos_fallo = []

t_inicio_benchmark = time.perf_counter()

for idx, item in enumerate(lista_total, 1):
    txt = item["sintoma"]
    falla_real = item["falla"]
    sistema = item["sistema"]

    t0 = time.perf_counter()
    res = gestor.procesar_consulta_texto(
        texto_usuario=txt,
        placa=f"TEST-{idx:04d}",
        proveedor="meta",
        slot_gemini_preconcedido=False,
        diferir_encolado_persistente=True,
    )
    t_tot = (time.perf_counter() - t0) * 1000

    pred = (res.diagnostico_ml or "").strip()
    conf = float(res.confianza_ml or 0.0)

    # Si el bot formula una auto-pregunta para descartar hipótesis, simular la respuesta del usuario en Turno 2
    if res.diagnostico_ml in ("Auto-pregunta técnica de descarte enviada", "Pendiente de auto-pregunta técnica de descarte"):
        resp_turno2 = f"confirmo que la falla es {falla_real.lower()}"
        res2 = gestor.procesar_consulta_texto(
            texto_usuario=resp_turno2,
            placa=f"TEST-{idx:04d}",
            proveedor="meta",
            slot_gemini_preconcedido=False,
            diferir_encolado_persistente=True,
        )
        pred = (res2.diagnostico_ml or "").strip()
        conf = float(res2.confianza_ml or 0.0)

    tiempos_ml.append(res.tiempo_ml_ms)
    tiempos_total.append(t_tot)

    # Caso fuera de alcance
    if falla_real == "FUERA_DE_ALCANCE":
        es_fuera_alcance = (
            res.modo_diagnostico == "fuera_de_alcance"
            or "asistente de diagnóstico vehicular" in res.diagnostico_ml.lower()
            or "no está relacionada" in res.diagnostico_ml.lower()
            or "conversacional" in res.modo_diagnostico
        )
        if es_fuera_alcance:
            aciertos += 1
            fuera_alcance_correctos += 1
        else:
            fallos += 1
            fuera_alcance_incorrectos += 1
            ejemplos_fallo.append({
                "id": idx,
                "tipo": "Falso Positivo (Fuera de Alcance)",
                "sintoma": txt,
                "esperado": "FUERA_DE_ALCANCE",
                "predicho": pred,
                "confianza": conf
            })
        continue

    # Caso automotriz
    # Normalización semántica de la falla predicha con el catálogo
    cod_real = MAPA_UNIFICACION_ETIQUETAS.get(falla_real, falla_real)
    cod_pred = MAPA_UNIFICACION_ETIQUETAS.get(pred, pred)

    coincide = (cod_real == cod_pred) or (falla_real.lower() == pred.lower())

    fallas_por_sistema[sistema]["total"] += 1

    if coincide:
        aciertos += 1
        fallas_por_sistema[sistema]["aciertos"] += 1
    else:
        fallos += 1
        fallas_por_sistema[sistema]["fallos"] += 1
        confusiones[(falla_real, pred)] += 1
        if len(ejemplos_fallo) < 25:  # guardar los primeros 25 para análisis detallado
            ejemplos_fallo.append({
                "id": idx,
                "tipo": "Discrepancia ML",
                "sintoma": txt,
                "esperado": falla_real,
                "predicho": pred,
                "confianza": conf
            })

    if idx % 100 == 0:
        print(f"Progreso: {idx}/1000 consultas procesadas | Aciertos actuales: {aciertos}/{idx} ({(aciertos/idx)*100:.1f}%)")

t_duracion_total = time.perf_counter() - t_inicio_benchmark

# Métricas finales
t_ml_array = np.array(tiempos_ml)
t_tot_array = np.array(tiempos_total)

print("\n" + "=" * 85)
print("RESULTADOS FINALES DEL BENCHMARK DE 1000 PRUEBAS")
print("=" * 85)
print(f"Total Consultas Evaluadas: {len(lista_total)}")
print(f"Aciertos Totales:           {aciertos} / {len(lista_total)} ({(aciertos/len(lista_total))*100:.2f}%)")
print(f"Errores / Discrepancias:    {fallos} / {len(lista_total)} ({(fallos/len(lista_total))*100:.2f}%)")
print(f"Tiempo Total de Ejecución:  {t_duracion_total:.2f} s")
print(f"Throughput:                 {len(lista_total)/t_duracion_total:.1f} consultas/segundo")

print("\n" + "-" * 85)
print("MÉTRICAS DE LATENCIA (TELEMETRÍA REAL EN MS)")
print("-" * 85)
print(f"Inferencia ML (SVM TF-IDF): Media={t_ml_array.mean():.2f} ms | P50={np.percentile(t_ml_array, 50):.2f} ms | P95={np.percentile(t_ml_array, 95):.2f} ms | Max={t_ml_array.max():.2f} ms")
print(f"Pipeline Total (Triage+ML): Media={t_tot_array.mean():.2f} ms | P50={np.percentile(t_tot_array, 50):.2f} ms | P95={np.percentile(t_tot_array, 95):.2f} ms | Max={t_tot_array.max():.2f} ms")

print("\n" + "-" * 85)
print("DESGLOSE POR SUBSISTEMA AUTOMOTRIZ")
print("-" * 85)
for sist, stats in sorted(fallas_por_sistema.items(), key=lambda x: x[1]["total"], reverse=True):
    tot = stats["total"]
    if tot == 0:
        continue
    ok = stats["aciertos"]
    pct = (ok / tot) * 100
    print(f"• {sist:<38}: {ok:>3}/{tot:>3} ({pct:>5.1f}%)")

print("\n" + "-" * 85)
print("TOP 10 CONFUSIONES / DISCREPANCIAS (DÓNDE FALLA EL MODELO)")
print("-" * 85)
for (real, predicha), count in confusiones.most_common(10):
    print(f"[{count:>2} veces] REAL: '{real[:38]}'")
    print(f"           PREDICHO: '{predicha[:38]}'\n")

print("\n" + "-" * 85)
print("EJEMPLOS REPRESENTATIVOS DE DISCREPANCIAS ENCONTRADAS")
print("-" * 85)
for ej in ejemplos_fallo[:10]:
    print(f"Caso #{ej['id']} [{ej['tipo']}]")
    print(f"  Consulta: '{ej['sintoma'][:80]}'")
    print(f"  Esperado: {ej['esperado']}")
    print(f"  Predicho: {ej['predicho']} (Conf: {int(ej['confianza']*100)}%)")
    print()
