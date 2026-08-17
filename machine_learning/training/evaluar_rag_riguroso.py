"""Evaluación rigurosa del subsistema RAG con umbral de producción 0.25 y consultas negativas."""

import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parents[2]
if str(RAIZ / "backend") not in sys.path:
    sys.path.insert(0, str(RAIZ / "backend"))

from src.infrastructure.motor_rag import MotorRAG
from src.config import settings

def evaluar_rag():
    print("=" * 80)
    print("EVALUACIÓN RIGUROSA DE RECUPERACIÓN RAG MULTIMARCA (UMBRAL 0.25)")
    print("=" * 80)

    motor = MotorRAG()
    umbral_prod = settings.diagnostic.rag_min_similarity
    print(f"Total procedimientos indexados en FAISS: {len(motor.documentos)}")
    print(f"Umbral de similitud configurado: {umbral_prod:.2f}")

    # 1. Casos Positivos Técnicos con Procedimiento Esperado Específico
    casos_positivos = [
        {
            "query": "Toyota Prius bateria de alto voltaje inversor error p0a80 celdas desbalanceadas",
            "marca_esperada": "Toyota",
            "termino_titulo_esperado": "BATERÍA DE ALTO VOLTAJE",
        },
        {
            "query": "Toyota Yaris pedal de embrague no desembraga bombin y plato de presion",
            "marca_esperada": "Toyota",
            "termino_titulo_esperado": "EMBRAGUE",
        },
        {
            "query": "Nissan Sentra transmision automatica CVT sobrecalentamiento solenoide p0700",
            "marca_esperada": "Nissan",
            "termino_titulo_esperado": "TRANSMISIÓN CONTINUAMENTE VARIABLE",
        },
        {
            "query": "Sistema de conversion a GNV GLP 5ta generacion calibracion rampa inyectores reductor",
            "marca_esperada": "Multimarca GNV/GLP",
            "termino_titulo_esperado": "SISTEMA GNV / GLP 5TA GENERACIÓN",
        },
        {
            "query": "Hyundai Accent cuerpo de aceleracion mariposa electronica tps ralenti inestable p2135",
            "marca_esperada": "Hyundai",
            "termino_titulo_esperado": "CUERPO DE ACELERACIÓN",
        },
        {
            "query": "Kia Rio valvula solenoide ocv sincronizacion variable vvt cascabeleo p0011",
            "marca_esperada": "Kia",
            "termino_titulo_esperado": "VÁLVULA SOLENOIDE DE SINCRONIZACIÓN VARIABLE",
        },
        {
            "query": "Frenos de aire neumaticos valvula secador camiones Scania Volvo perdida de presion",
            "marca_esperada": "Universal / Multimarca",
            "termino_titulo_esperado": "FRENOS DE AIRE",
        }
    ]

    # 2. Casos Negativos (Fuera de Dominio - Deben ser rechazados con similitud < umbral)
    casos_negativos = [
        "receta casera para preparar pastel de chocolate con fresas",
        "lavadora samsung digital no centrifuga ni bota el agua en el ciclo",
        "vuelos baratos y reservas de hotel en cusco machu picchu",
    ]

    print("\n--- EVALUANDO CASOS POSITIVOS DENTRO DE DOMINIO ---")
    aciertos_positivos = 0
    for i, caso in enumerate(casos_positivos, start=1):
        q = caso["query"]
        cuerpo, titulo, sim, meta = motor.recuperar_procedimiento_con_metadatos(q, umbral=umbral_prod)
        print(f"\n[Positivo {i}] Consulta: '{q[:60]}...'")
        print(f"   -> Título Recuperado: {titulo[:65]}...")
        print(f"   -> Similitud Coseno: {sim:.4f} (Umbral mín: {umbral_prod:.2f})")
        print(f"   -> Marca: {meta.get('marca')} | OEM: {meta.get('manual_oem', '')[:50]}")

        # Validación estricta: similitud >= umbral, marca coincide y título contiene el término esperado
        coincide_umbral = sim >= umbral_prod
        coincide_marca = meta.get("marca") == caso["marca_esperada"]
        coincide_tema = caso["termino_titulo_esperado"].lower() in titulo.lower()

        if coincide_umbral and coincide_marca and coincide_tema:
            aciertos_positivos += 1
            print("   [OK] Recuperacion EXACTA: Supera umbral y contenido tematico coincide.")
        else:
            print(f"   [FALLO] Umbral: {coincide_umbral} | Marca: {coincide_marca} | Tema: {coincide_tema}")

    print("\n--- EVALUANDO CASOS NEGATIVOS FUERA DE DOMINIO ---")
    rechazos_correctos = 0
    for j, q_neg in enumerate(casos_negativos, start=1):
        cuerpo, titulo, sim, meta = motor.recuperar_procedimiento_con_metadatos(q_neg, umbral=umbral_prod)
        print(f"\n[Negativo {j}] Consulta fuera de dominio: '{q_neg}'")
        print(f"   -> Similitud Coseno: {sim:.4f}")
        print(f"   -> Título: {titulo}")

        if sim < umbral_prod and titulo == "Coincidencia baja":
            rechazos_correctos += 1
            print("   [OK] Rechazo exitoso: Correctamente clasificado como Coincidencia baja.")
        else:
            print("   [FALLO] Falso positivo: Se aceptó una consulta no automotriz.")

    total_pruebas = len(casos_positivos) + len(casos_negativos)
    total_aciertos = aciertos_positivos + rechazos_correctos
    precision_positivos = (aciertos_positivos / len(casos_positivos)) * 100
    tasa_rechazo_negativos = (rechazos_correctos / len(casos_negativos)) * 100

    print("\n" + "=" * 80)
    print("MÉTRICAS FORMALES DE EVALUACIÓN RAG")
    print("=" * 80)
    print(f"Precision@1 en Casos Positivos: {precision_positivos:.1f}% ({aciertos_positivos}/{len(casos_positivos)})")
    print(f"Tasa de Rechazo Fuera de Dominio: {tasa_rechazo_negativos:.1f}% ({rechazos_correctos}/{len(casos_negativos)})")
    print(f"Efectividad Global RAG: {total_aciertos}/{total_pruebas} ({(total_aciertos/total_pruebas)*100:.1f}%)")
    print("=" * 80)

    assert aciertos_positivos == len(casos_positivos), f"Fallaron {len(casos_positivos) - aciertos_positivos} casos positivos"
    assert rechazos_correctos == len(casos_negativos), f"Fallaron {len(casos_negativos) - rechazos_correctos} rechazos negativos"

if __name__ == "__main__":
    evaluar_rag()
