"""Demostración y verificación del flujo completo tripartito: ML -> RAG -> LLM."""

import sys
from pathlib import Path

# Configurar salida en UTF-8 para soporte de emojis y caracteres especiales
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

raiz = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(raiz / "backend"))

from src.core.gestor_diagnostico import GestorDiagnostico

gestor = GestorDiagnostico()

casos_prueba = [
    {
        "vehiculo": "Toyota Yaris 2018",
        "consulta": "Tengo código P0301 en el escáner, el motor tiembla al acelerar y pierde fuerza en subidas",
    },
    {
        "vehiculo": "Nissan Sentra 2017",
        "consulta": "Parpadeo de luces en el tablero, la radio se reinicia y la batería no carga bien en marcha",
    },
    {
        "vehiculo": "Hyundai Elantra 2019",
        "consulta": "Al frenar a 90 km/h en carretera el pedal y el timón vibran muy fuerte, sin ruidos metálicos",
    },
    {
        "vehiculo": "Chevrolet Cruze 2016",
        "consulta": "Check Engine encendido con código P0171 mezcla pobre, tironea en frío y consume más combustible",
    },
]

print("======================================================================")
print("   DEMOSTRACIÓN DE INTEGRACIÓN END-TO-END: ML -> RAG -> LLM")
print("======================================================================\n")

for i, caso in enumerate(casos_prueba, start=1):
    print(f">>> CASO {i}: {caso['vehiculo']}")
    print(f"Consulta del mecánico: \"{caso['consulta']}\"")

    resultado = gestor.procesar_consulta_texto(
        texto_usuario=caso["consulta"],
        marca_modelo=caso["vehiculo"],
        session_id=f"test_session_{i}",
        diferir_encolado_persistente=True,
    )

    print("\n1. PREDICCIÓN MACHINE LEARNING (Linear SVM + TF-IDF):")
    print(f"   - Diagnóstico Top 1: {resultado.diagnostico_ml}")
    print(f"   - Confianza ML: {resultado.confianza_ml * 100:.1f}%")
    print(f"   - Latencia ML: {resultado.tiempo_ml_ms} ms")
    if resultado.predicciones_ml:
        print("   - Diagnóstico Diferencial (Top 3):")
        for p in resultado.predicciones_ml[:3]:
            print(f"     * {p.falla}: {p.probabilidad * 100:.1f}%")

    print("\n2. RECUPERACIÓN RAG (FAISS + 200 Manuales OEM):")
    print(f"   - Procedimiento recuperado: {resultado.titulo_manual}")
    print(f"   - Similitud semántica RAG: {resultado.similitud_rag:.1f}%")
    print(f"   - Latencia RAG: {resultado.tiempo_rag_ms} ms")
    if resultado.contexto_manual:
        primeras_lineas = "\n     ".join(
            [line for line in resultado.contexto_manual.strip().split("\n") if line.strip()][:4]
        )
        print(f"   - Fragmento OEM entregado al LLM:\n     {primeras_lineas}")

    print("\n3. SÍNTESIS Y REPORTE ESTRUCTURADO (LLM / FORMATO TALLER):")
    print(f"   - Modo de diagnóstico: {resultado.modo_diagnostico}")
    print(f"   - Tiempo total pipeline: {resultado.tiempo_total_ms} ms")
    lineas_resp = resultado.respuesta_texto.strip().split("\n")
    print("   - Mensaje entregado al mecánico:")
    for line in lineas_resp[:12]:
        print(f"     {line}")
    print("\n" + "=" * 70 + "\n")
