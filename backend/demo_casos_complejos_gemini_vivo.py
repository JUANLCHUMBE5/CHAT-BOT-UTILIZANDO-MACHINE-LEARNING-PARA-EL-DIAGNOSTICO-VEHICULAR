"""
Demostración en VIVO con Google Gemini LLM + FAISS RAG + Linear SVM TF-IDF.
Evalúa casos novedosos, complejos y desafiantes llamando a la API de Gemini en tiempo real.
"""

import sys
import time

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, ".")

from src.core.gestor_diagnostico import GestorDiagnostico

gestor = GestorDiagnostico()

# 6 Casos inéditos, sumamente complejos y redactados en lenguaje de taller real
CASOS_COMPLEJOS_DESAFIO = [
    {
        "id": 1,
        "categoria": "Transmisión CVT y Temperatura (Nissan Sentra)",
        "consulta": "Maestro, mi Nissan Sentra 2020 en carretera después de manejar 1 hora a 100 km/h empieza a zumbar fuerte la caja CVT, pierde fuerza de golpe, las revoluciones suben pero no acelera y me salió el mensaje de sobrecalentamiento de transmisión en el tablero.",
        "falla_esperada": "Sobrecalentamiento o solenoides en caja automatica CVT / DSG",
    },
    {
        "id": 2,
        "categoria": "Sistema Híbrido Alta Tensión (Toyota Prius)",
        "consulta": "Buenas tardes mecánico, tengo un Toyota Prius híbrido y en la autopista se encendió el triángulo rojo de advertencia con el mensaje de revisar sistema híbrido. En el escáner me arroja el código DTC P0A80 y el ventilador de la batería trasera suena a máxima velocidad.",
        "falla_esperada": "Degradacion o falla en paquete de bateria de alto voltaje (EV / Hibridos)",
    },
    {
        "id": 3,
        "categoria": "Sobrealimentación y Turbo (Motor Diésel / Pick-up)",
        "consulta": "Causa, cuando le piso el acelerador a fondo a la camioneta para pasar un camión suena un soplido fuertísimo como si se reventara una llanta debajo del capó, pierde toda la fuerza y encontré una manguera del intercooler totalmente rajada botando aceite y aire a presión.",
        "falla_esperada": "Fuga en mangueras de intercooler o turbocompresor danado",
    },
    {
        "id": 4,
        "categoria": "Embrague Hidráulico (Hyundai Accent)",
        "consulta": "Amigo una consulta urgente, estaba manejando por la Javier Prado y de repente el pedal de embrague se cayó al piso por completo, quedó aguado como trapo y por más que lo bombee no regresa ni entran primera ni segunda, tuve que orillarme con luces de emergencia.",
        "falla_esperada": "Falla en bombin o bomba hidraulica de embrague",
    },
    {
        "id": 5,
        "categoria": "Frenos Convencionales y Alabeo Dinámico",
        "consulta": "Hola maestro, cuando voy en bajada a más de 80 km/h y piso el pedal de freno suavemente, el pedal me zapatea contra el pie con mucha fuerza y el timón tiembla de un lado a otro como loco, pero si suelto el freno el carro anda sedita y sin ruidos.",
        "falla_esperada": "Discos de freno alabeados o desgastados",
    },
    {
        "id": 6,
        "categoria": "Freno Neumático Pesado (Camión de Carga)",
        "consulta": "En el camión de 3 ejes se escucha un escape continuo de aire comprimido por los pulmones de freno del eje posterior cada vez que aplico el freno de servicio, y en los manómetros del tablero la aguja de los tanques de aire cae de 8 bares a 4 bares de golpe.",
        "falla_esperada": "Fugas de aire o fallos en el sistema de frenos neumático (Camiones)",
    },
]

print("=" * 85)
print("DEMOSTRACIÓN EN VIVO: LLAMADAS REALES A GOOGLE GEMINI LLM + FAISS RAG + LINEAR SVM")
print("Total de casos desafiantes en vivo:", len(CASOS_COMPLEJOS_DESAFIO))
print("=" * 85 + "\n")

for caso in CASOS_COMPLEJOS_DESAFIO:
    print(f"▶ [CASO {caso['id']}] {caso['categoria']}")
    print(f"• Consulta del Usuario: \"{caso['consulta']}\"")

    t_inicio = time.perf_counter()
    # slot_gemini_preconcedido=True FUERZA a llamar en vivo a Google Gemini por internet
    res = gestor.procesar_consulta_texto(
        texto_usuario=caso["consulta"],
        placa=f"LIVE-{caso['id']:02d}",
        proveedor="meta",
        slot_gemini_preconcedido=True,
    )
    duracion = time.perf_counter() - t_inicio

    print(f"• Tiempo de Respuesta Real: {duracion:.2f} segundos (Inferencia SVM: {res.tiempo_ml_ms}ms, Búsqueda RAG: {res.tiempo_rag_ms}ms, Gemini LLM: {res.tiempo_llm_ms}ms)")
    print(f"• Diagnóstico ML (Linear SVM): {res.diagnostico_ml} (Confianza: {int((res.confianza_ml or 0)*100)}%)")
    print(f"• Manual Técnico RAG Recuperado: {res.titulo_manual or 'Procedimiento general'}")
    print(f"• Modo de Respuesta: {res.modo_diagnostico}")
    print("\n📝 RESPUESTA ESTRUCTURADA GENERADA POR GEMINI LLM PARA EL MECÁNICO:")
    print("=" * 70)
    print(res.respuesta_texto)
    print("=" * 70 + "\n")
    time.sleep(2)  # Pausa de cortesía para respetar la cuota de la API de Gemini
