"""
analizar_respuestas_test.py
Script integral para ejecutar pruebas y analizar los resultados y respuestas
del Chatbot de Diagnóstico Vehicular con Machine Learning (Tesis UCV 2026).
"""

import os
import sys
import time

# Asegurar codificación UTF-8 en consola Windows
os.environ["PYTHONUTF8"] = "1"
if sys.stdout.encoding != "utf-8":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

# Asegurar que backend esté en el sys.path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from src.core.gestor_diagnostico import GestorDiagnostico
from src.core.traductor_jerga import normalizar_jerga_peruana


def ejecutar_pruebas_obtencion_respuestas():
    print("=" * 85)
    print("  🚗 CARBOT — ANÁLISIS DE PRUEBAS DE RESPUESTAS Y MACHINE LEARNING")
    print("  Tesis: Diagnóstico Vehicular con Machine Learning | UCV 2026")
    print("=" * 85)
    print()

    print("⏳ [1/3] Inicializando modelos de IA, FAISS RAG y clasificador...")
    gestor = GestorDiagnostico(gemini_api_key="demo_key")
    print("✅ Modelos cargados en memoria con éxito.")
    print()

    # Batería de casos de prueba representativos
    casos_prueba = [
        {
            "categoria": "Sistema de Frenos (Desgaste y Ruido)",
            "entrada": "las pastillas de freno chillan horrible cuando freno en la bajada",
            "placa": "BC-4521",
            "marca": "Toyota Yaris 2018"
        },
        {
            "categoria": "Sistema de Motor / Encendido (Jerga Peruana)",
            "entrada": "mi carro se chupa en la subida y el motor cascabelea con gasolina de 90",
            "placa": "X1A-890",
            "marca": "Nissan Versa 2019"
        },
        {
            "categoria": "Sistema de Transmisión (Pérdida de tracción)",
            "entrada": "la caja automatica patina y da tirones al pasar de primera a segunda",
            "placa": "F7U-312",
            "marca": "Kia Rio 2020"
        },
        {
            "categoria": "Sistema de Suspensión (Ruidos en baches)",
            "entrada": "siento un golpe seco en los baches y amortiguador bota liquido aceitoso",
            "placa": "W2B-109",
            "marca": "Hyundai Accent 2017"
        },
        {
            "categoria": "Diagnóstico por Código Scanner OBD-II",
            "entrada": "el scanner me arroja codigo de error P0300 falla de encendido en cilindros",
            "placa": "Z3E-554",
            "marca": "Chevrolet Sail 2018"
        },
        {
            "categoria": "Control de Ambigüedad (Filtro de Calidad)",
            "entrada": "el carro falla",
            "placa": "T8Y-990",
            "marca": "Vehiculo No Especificado"
        },
        {
            "categoria": "Contacto Inicial / Saludo",
            "entrada": "Hola buenas tardes necesito una consulta",
            "placa": "P1Q-001",
            "marca": "Consulta General"
        },
    ]

    print("=" * 85)
    print("🔍 [2/3] EJECUCIÓN DE PRUEBAS DE PIPELINE (ENTRADA -> ML -> RAG -> RESPUESTA)")
    print("=" * 85)

    aciertos = 0
    tiempos = []

    for i, caso in enumerate(casos_prueba, start=1):
        print(f"\n─────────────────────────────────────────────────────────────────────────────")
        print(f"📌 CASO DE PRUEBA #{i}: {caso['categoria']}")
        print(f"─────────────────────────────────────────────────────────────────────────────")
        print(f"👤 Entrada Usuario:   \"{caso['entrada']}\"")
        print(f"🚘 Vehículo:          {caso['marca']} | Placa: {caso['placa']}")

        inicio = time.time()

        # 1. Normalización de jerga
        texto_norm = normalizar_jerga_peruana(caso['entrada'])
        print(f"🔄 Jerga Normalizada: \"{texto_norm}\"")

        # 2. Ejecutar procesamiento del gestor
        resultado = gestor.procesar_consulta_texto(
            texto_usuario=caso['entrada'],
            placa=caso['placa'],
            marca_modelo=caso['marca']
        )

        duracion_ms = (time.time() - inicio) * 1000
        tiempos.append(duracion_ms)

        # 3. Mostrar análisis de resultados
        print(f"🤖 Diagnóstico ML:    {resultado.diagnostico_ml}")
        print(f"📊 Certeza / Conf.:   {resultado.confianza_ml * 100:.2f}%")
        print(f"📚 Manual RAG:        {resultado.titulo_manual or 'N/A'}")
        print(f"⏱️  Tiempo Ejecución:  {duracion_ms:.2f} ms")
        print(f"⚙️  Modo / Estado:     {resultado.modo_diagnostico} (Req. Humana: {resultado.requiere_revision_humana})")
        print(f"\n💬 RESPUESTA GENERADA AL CLIENTE:")
        print("   " + "\n   ".join(resultado.respuesta_texto.split("\n")[:8]))
        if len(resultado.respuesta_texto.split("\n")) > 8:
            print("   ...")

        if resultado.confianza_ml > 0 or resultado.modo_diagnostico in ("saludo", "esperando_clarificacion"):
            aciertos += 1

    print("\n" + "=" * 85)
    print("📊 [3/3] RESUMEN DE RENDIMIENTO DE LAS PRUEBAS DE OBTENCIÓN DE RESPUESTAS")
    print("=" * 85)
    print(f"✔ Casos Evaluados:            {len(casos_prueba)}")
    print(f"✔ Casos Procesados con Éxito: {aciertos}/{len(casos_prueba)} ({(aciertos/len(casos_prueba))*100:.1f}%)")
    print(f"✔ Tiempo Promedio de Respuesta:{sum(tiempos)/len(tiempos):.2f} ms por diagnóstico")
    print("=" * 85)
    print()


if __name__ == "__main__":
    ejecutar_pruebas_obtencion_respuestas()
