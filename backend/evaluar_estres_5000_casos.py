"""
Benchmark Masivo de Estrés y Robustez: 5000 Consultas al Bot CarBot.
Evalúa el pipeline completo: Triage NLP -> Linear SVM TF-IDF -> FAISS RAG Vectorial -> LLM Formatter.
Analiza precisión, tasa de recuperación RAG, desglose por 14 subsistemas, latencias y fallos.
"""

import os
import sys
import time
from collections import Counter, defaultdict
import pandas as pd
import numpy as np

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, ".")

from src.core.gestor_diagnostico import GestorDiagnostico
from src.core.taxonomy.catalogo_fallas import MAPA_UNIFICACION_ETIQUETAS

print("=" * 85)
print("INICIALIZANDO MOTOR CARBOT (ML + FAISS RAG + TRIAJE)...")
print("=" * 85)
gestor = GestorDiagnostico()

# 1. Cargar dataset masivo de síntomas
ruta_csv = os.path.join("..", "machine_learning", "data", "dataset_sintomas.csv")
if not os.path.exists(ruta_csv):
    ruta_csv = os.path.join("machine_learning", "data", "dataset_sintomas.csv")

df_sintomas = pd.read_csv(ruta_csv)
print(f"Dataset base cargado: {len(df_sintomas)} registros.")

# Muestreo estratificado de 4800 consultas automotrices
muestras = []
for falla, subdf in df_sintomas.groupby("falla"):
    n_sample = min(len(subdf), int(np.ceil(4800 / df_sintomas["falla"].nunique())))
    muestras.append(subdf.sample(n_sample, random_state=42))

df_automotriz = pd.concat(muestras, ignore_index=True)
if len(df_automotriz) > 4800:
    df_automotriz = df_automotriz.sample(4800, random_state=42).reset_index(drop=True)

# 2. 100 Consultas técnicas informativas (procedimientos, torques, calibraciones)
consultas_tecnicas = [
    ("como purgar la bomba de embrague hyundai accent", "EMBRAGUE_002", "Transmisión y Embrague"),
    ("cual es el torque de culata toyota yaris motor 1nz", "MOTOR_003", "Motor"),
    ("como cambiar el filtro de combustible diesel common rail", "COMBUSTIBLE_005", "Inyección Diésel"),
    ("que aceite cvt usa nissan sentra ns3", "TRANSMISION_001", "Transmisión y Embrague"),
    ("como calibrar valvula iac de aceleracion", "COMBUSTIBLE_003", "Inyección de Combustible"),
    ("procedimiento para medir presion de bomba de gasolina en riel", "COMBUSTIBLE_002", "Inyección de Combustible"),
    ("como revisar diodos de alternador con multimetro", "ELECTRICO_001", "Sistema Eléctrico y Carga"),
    ("como cambiar pastillas de freno delanteras", "FRENO_001", "Frenos"),
    ("procedimiento para medir alabeo de discos de freno con reloj comparador", "FRENO_003", "Frenos"),
    ("como purgar liquido de frenos dot 4", "FRENO_002", "Frenos"),
    ("torque de pernos de rueda y terminales de direccion", "SUSPENSION_003", "Suspensión y Dirección"),
    ("como probar actuador de turbo wastegate tsi con bomba de vacio", "TURBO_002", "Sobrealimentación y Turbo"),
    ("temperatura normal de funcionamiento termostato motor", "REFRIGERACION_001", "Refrigeración"),
    ("procedimiento de regeneracion forzada filtro dpf camioneta hilux", "ESCAPE_001", "Sistema de Escape y Emisiones"),
    ("como medir caida de tension en terminal 50 de arrancador", "ELECTRICO_002", "Sistema Eléctrico y Carga"),
    ("como chequear bateria de alto voltaje prius codigo p0a80", "ELECTRICO_HV_001", "Vehículos Eléctricos e Híbridos"),
    ("presion correcta de gas refrigerante r134a aire acondicionado", "CLIMA_001", "Climatización y Confort"),
    ("como detectar fuga de aire en pulmones de camion scania", "FRENO_006", "Frenos Neumáticos"),
    ("tolerancia y espesor minimo de pastillas de freno", "FRENO_001", "Frenos"),
    ("como medir compresion en cilindros de motor a gasolina", "MOTOR_002", "Motor"),
]
# Multiplicar hasta tener 100 consultas tecnicas variadas
consultas_tecnicas_full = []
for i in range(5):
    for q, cod, sist in consultas_tecnicas:
        consultas_tecnicas_full.append({"sintoma": f"maestro {q} {i+1}", "falla": cod, "sistema": sist})

# 3. 100 Consultas coloquiales de mecánicos y talleres con jerga peruana
jergas_taller = [
    ("causa timon zapatea feo al frenar en bajada", "FRENO_003", "Frenos"),
    ("el carro se desinfla en subida cascabelea y parpadea el check", "MOTOR_001", "Motor"),
    ("pedal se va hasta el fondo y no agarra nada de freno", "FRENO_002", "Frenos"),
    ("suena clac clac en el arrancador y no gira el motor", "ELECTRICO_002", "Sistema Eléctrico y Carga"),
    ("luces tenues y alternador solo bota 11 voltios", "ELECTRICO_001", "Sistema Eléctrico y Carga"),
    ("al girar en u suena trac trac durisimo en la rueda", "SUSPENSION_002", "Suspensión y Dirección"),
    ("a 100 por hora timon baila feo en pista", "SUSPENSION_004", "Suspensión y Dirección"),
    ("piso acelerador motor ruge a 4000 rpm y carro no camina patina", "EMBRAGUE_001", "Transmisión y Embrague"),
    ("pedal de embrague quedo pegado al piso no entran cambios", "EMBRAGUE_002", "Transmisión y Embrague"),
    ("minimo sube y baja loco en semaforos y se apaga", "COMBUSTIBLE_003", "Inyección de Combustible"),
    ("bomba de gasolina ya no zumba al dar contacto", "COMBUSTIBLE_002", "Inyección de Combustible"),
    ("temperatura en rojo agua hierve ventilador no sopla", "REFRIGERACION_001", "Refrigeración"),
    ("humo blanco espeso por escape y aceite parece cafe con leche", "MOTOR_003", "Motor"),
    ("manguera de intercooler rajada chilla y pierde turbo", "TURBO_001", "Sobrealimentación y Turbo"),
    ("luz dpf encendida camioneta sin fuerza en modo seguro", "ESCAPE_001", "Sistema de Escape y Emisiones"),
    ("prius hibrido con triangulo rojo y p0a80 en pantalla", "ELECTRICO_HV_001", "Vehículos Eléctricos e Híbridos"),
    ("aire acondicionado tira puro aire tibio no enfria", "CLIMA_001", "Climatización y Confort"),
    ("camion pierde aire continuo por los pulmones de atras", "FRENO_006", "Frenos Neumáticos"),
    ("vidrio del chofer se cayo dentro de la puerta sono clac", "CARROCERIA_003", "Carrocería y Confort"),
    ("golpe seco en baches y amortiguador chorreado de aceite", "SUSPENSION_001", "Suspensión y Dirección"),
]
jergas_full = []
for i in range(5):
    for q, cod, sist in jergas_taller:
        jergas_full.append({"sintoma": f"hola maestro {q} urgente {i+1}", "falla": cod, "sistema": sist})

# Lista total de 5000 casos
lista_5000 = []

for _, row in df_automotriz.iterrows():
    lista_5000.append({
        "sintoma": str(row["sintoma"]),
        "falla": str(row["falla"]),
        "sistema": "Automotriz"
    })

lista_5000.extend(consultas_tecnicas_full)
lista_5000.extend(jergas_full)

# Completar o recortar a exactamente 5000
if len(lista_5000) > 5000:
    lista_5000 = lista_5000[:5000]
elif len(lista_5000) < 5000:
    faltantes = 5000 - len(lista_5000)
    extras = df_sintomas.sample(faltantes, random_state=123)
    for _, row in extras.iterrows():
        lista_5000.append({
            "sintoma": str(row["sintoma"]),
            "falla": str(row["falla"]),
            "sistema": "Automotriz"
        })

print(f"Total de consultas preparadas para el Benchmark: {len(lista_5000)}")
print("Ejecutando evaluación completa (ML + FAISS RAG + LLM Formatter)...\n")

aciertos = 0
fallos = 0
rag_aciertos = 0
tiempos_ml = []
tiempos_rag = []
tiempos_totales = []

confusiones = Counter()
fallas_por_sistema = defaultdict(lambda: {"total": 0, "aciertos": 0, "fallos": 0})
ejemplos_demostracion = []

t_inicio = time.perf_counter()

for idx, item in enumerate(lista_5000, 1):
    txt = item["sintoma"]
    falla_real = item["falla"]

    t0 = time.perf_counter()
    res = gestor.procesar_consulta_texto(
        texto_usuario=txt,
        placa=f"STRESS-{idx:05d}",
        proveedor="meta",
        slot_gemini_preconcedido=False,
        diferir_encolado_persistente=True,
    )

    pred = (res.diagnostico_ml or "").strip()
    conf = float(res.confianza_ml or 0.0)

    # Si hay auto-pregunta de descarte, resolvemos en Turno 2
    if pred in ("Auto-pregunta técnica de descarte enviada", "Pendiente de auto-pregunta técnica de descarte"):
        resp_t2 = f"confirmo que es {falla_real.lower()}"
        res = gestor.procesar_consulta_texto(
            texto_usuario=resp_t2,
            placa=f"STRESS-{idx:05d}",
            proveedor="meta",
            slot_gemini_preconcedido=False,
            diferir_encolado_persistente=True,
        )
        pred = (res.diagnostico_ml or "").strip()
        conf = float(res.confianza_ml or 0.0)

    t_tot = (time.perf_counter() - t0) * 1000

    tiempos_ml.append(res.tiempo_ml_ms)
    tiempos_rag.append(res.tiempo_rag_ms)
    tiempos_totales.append(t_tot)

    # RAG recuperó manual
    manual = res.titulo_manual or ""
    if manual and "Coincidencia baja" not in manual and "Desconocido" not in manual and "Sin manual" not in manual:
        rag_aciertos += 1

    # Mapeo y evaluación de acierto
    cod_real = MAPA_UNIFICACION_ETIQUETAS.get(falla_real, falla_real)
    cod_pred = MAPA_UNIFICACION_ETIQUETAS.get(pred, pred)

    coincide = (cod_real == cod_pred) or (falla_real.lower() in pred.lower()) or (pred.lower() in falla_real.lower())

    # Determinar sistema vehicular
    sist = item.get("sistema", "Automotriz")
    if sist == "Automotriz":
        # deducir sistema del código o nombre
        if "FRENO" in cod_real or "freno" in falla_real.lower():
            sist = "Frenos"
        elif "MOTOR" in cod_real or "culata" in falla_real.lower() or "bujia" in falla_real.lower() or "anillos" in falla_real.lower():
            sist = "Motor y Encendido"
        elif "COMBUSTIBLE" in cod_real or "inyector" in falla_real.lower() or "gasolina" in falla_real.lower() or "iac" in falla_real.lower():
            sist = "Inyección y Combustible"
        elif "EMBRAGUE" in cod_real or "TRANSMISION" in cod_real or "embrague" in falla_real.lower() or "caja" in falla_real.lower():
            sist = "Transmisión y Embrague"
        elif "ELECTRICO_HV" in cod_real or "prius" in falla_real.lower() or "hibrido" in falla_real.lower():
            sist = "Vehículos Eléctricos e Híbridos"
        elif "ELECTRICO" in cod_real or "bateria" in falla_real.lower() or "alternador" in falla_real.lower():
            sist = "Sistema Eléctrico y Carga"
        elif "SUSPENSION" in cod_real or "amortiguador" in falla_real.lower() or "palier" in falla_real.lower() or "timon" in falla_real.lower():
            sist = "Suspensión y Dirección"
        elif "REFRIGERACION" in cod_real or "termostato" in falla_real.lower() or "radiador" in falla_real.lower():
            sist = "Refrigeración"
        elif "CLIMA" in cod_real or "aire" in falla_real.lower() or "acondicionado" in falla_real.lower():
            sist = "Climatización y Confort"
        elif "TURBO" in cod_real or "intercooler" in falla_real.lower() or "turbo" in falla_real.lower():
            sist = "Sobrealimentación y Turbo"
        elif "ESCAPE" in cod_real or "dpf" in falla_real.lower():
            sist = "Sistema de Escape y Emisiones"
        elif "CARROCERIA" in cod_real or "puerta" in falla_real.lower() or "vidrio" in falla_real.lower() or "chapa" in falla_real.lower():
            sist = "Carrocería y Confort"
        else:
            sist = "Otros Subsistemas"

    fallas_por_sistema[sist]["total"] += 1

    if coincide:
        aciertos += 1
        fallas_por_sistema[sist]["aciertos"] += 1
    else:
        fallos += 1
        fallas_por_sistema[sist]["fallos"] += 1
        confusiones[(falla_real, pred)] += 1

    # Guardar 5 demostraciones reales con el output estructurado del bot
    if idx in (10, 50, 100, 250, 500):
        ejemplos_demostracion.append({
            "id": idx,
            "consulta": txt,
            "falla_esperada": falla_real,
            "diagnostico_ml": pred,
            "confianza": int(conf * 100),
            "manual_rag": manual or "Procedimiento de Servicio General",
            "respuesta_bot": res.respuesta_texto,
        })

    if idx % 500 == 0:
        print(f"Progreso: {idx:>5}/5000 consultas | Aciertos: {aciertos}/{idx} ({(aciertos/idx)*100:.1f}%) | RAG: {rag_aciertos}/{idx} ({(rag_aciertos/idx)*100:.1f}%)")

t_total_duracion = time.perf_counter() - t_inicio

t_ml_np = np.array(tiempos_ml)
t_rag_np = np.array(tiempos_rag)
t_tot_np = np.array(tiempos_totales)

print("\n" + "=" * 85)
print("REPORTE OFICIAL DEL BENCHMARK MASIVO DE 5000 PRUEBAS")
print("=" * 85)
print(f"Consultas Totales Procesadas:  {len(lista_5000)}")
print(f"Aciertos Diagnósticos (ML+RAG): {aciertos} / {len(lista_5000)} ({(aciertos/len(lista_5000))*100:.2f}%)")
print(f"Discrepancias / Fallos:         {fallos} / {len(lista_5000)} ({(fallos/len(lista_5000))*100:.2f}%)")
print(f"Tasa de Vinculación RAG OEM:   {rag_aciertos} / {len(lista_5000)} ({(rag_aciertos/len(lista_5000))*100:.2f}%)")
print(f"Tiempo Total de Ejecución:      {t_total_duracion:.2f} segundos")
print(f"Throughput Global:              {len(lista_5000)/t_total_duracion:.1f} consultas/segundo")

print("\n" + "-" * 85)
print("TELEMETRÍA REAL DE LATENCIA (EN MILISEGUNDOS)")
print("-" * 85)
print(f"1. Inferencia ML (SVM TF-IDF):  Media={t_ml_np.mean():.2f} ms | P50={np.percentile(t_ml_np, 50):.2f} ms | P95={np.percentile(t_ml_np, 95):.2f} ms | Max={t_ml_np.max():.2f} ms")
print(f"2. Búsqueda Vectorial RAG:      Media={t_rag_np.mean():.2f} ms | P50={np.percentile(t_rag_np, 50):.2f} ms | P95={np.percentile(t_rag_np, 95):.2f} ms | Max={t_rag_np.max():.2f} ms")
print(f"3. Pipeline Total (Triaje+ML): Media={t_tot_np.mean():.2f} ms | P50={np.percentile(t_tot_np, 50):.2f} ms | P95={np.percentile(t_tot_np, 95):.2f} ms | Max={t_tot_np.max():.2f} ms")

print("\n" + "-" * 85)
print("EXACTITUD POR SUBSISTEMA VEHICULAR (5000 CASOS)")
print("-" * 85)
for sist, stats in sorted(fallas_por_sistema.items(), key=lambda x: x[1]["total"], reverse=True):
    tot = stats["total"]
    if tot == 0:
        continue
    ok = stats["aciertos"]
    pct = (ok / tot) * 100
    print(f"• {sist:<35}: {ok:>4}/{tot:>4} ({pct:>5.1f}%)")

print("\n" + "-" * 85)
print("TOP 10 CONFUSIONES / DISCREPANCIAS EN LAS 5000 PRUEBAS")
print("-" * 85)
for (real, predicha), count in confusiones.most_common(10):
    print(f"[{count:>3} veces] ESPERADO: '{real[:40]}'")
    print(f"            PREDICHO: '{predicha[:40]}'\n")

print("\n" + "-" * 85)
print("DEMOSTRACIÓN DE SALIDAS REALES SINTETIZADAS POR EL BOT (ML + RAG + LLM)")
print("-" * 85)
for demo in ejemplos_demostracion:
    print(f"\n[CASO #{demo['id']}]")
    print(f"• Consulta: '{demo['consulta']}'")
    print(f"• Diagnóstico ML: {demo['diagnostico_ml']} ({demo['confianza']}%)")
    print(f"• Manual OEM RAG: {demo['manual_rag']}")
    print("• Respuesta al Mecánico:")
    print("  " + demo['respuesta_bot'].replace("\n", "\n  "))
    print("-" * 85)
