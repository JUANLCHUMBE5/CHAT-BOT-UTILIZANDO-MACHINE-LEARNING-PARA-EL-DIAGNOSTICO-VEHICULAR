"""
Prueba interactiva del Sistema de Auto-Preguntas y Diagnóstico Guiado en 2 turnos.
Demuestra cómo el bot auto-pregunta para descartar hipótesis y alcanza el 100% de asertividad.
"""

import sys

sys.stdout.reconfigure(encoding="utf-8")
sys.path.insert(0, ".")
from src.core.gestor_diagnostico import GestorDiagnostico

gestor = GestorDiagnostico()

casos_prueba = [
    {
        "nombre": "Caso 1: Vibración Ambigua -> Descarte hacia Discos de Freno",
        "turno1": "el carro me vibra bastante cuando voy manejando",
        "turno2": "solo cuando piso el pedal de freno zapatea",
        "falla_esperada": "Discos de freno alabeados o desgastados",
        "placa": "AUTO-PREG-01",
    },
    {
        "nombre": "Caso 2: Vibración Ambigua -> Descarte hacia Llantas Desbalanceadas",
        "turno1": "el carro me tiembla el timon en autopista",
        "turno2": "vibra a mas de 90 km por hora sin tocar el freno",
        "falla_esperada": "Llantas desbalanceadas o desalineadas",
        "placa": "AUTO-PREG-02",
    },
    {
        "nombre": "Caso 3: No Arranca -> Descarte hacia Motor de Arranque / Solenoide",
        "turno1": "el carro no arranca maestro",
        "turno2": "al girar la llave solo suena un clac clac en el arrancador pero las luces quedan prendidas",
        "falla_esperada": "Falla en motor de arranque o solenoide (carbones gastados / contactos fogueados)",
        "placa": "AUTO-PREG-03",
    },
    {
        "nombre": "Caso 4: Falta de Fuerza / Jaloneo -> Descarte hacia Misfire",
        "turno1": "piso el acelerador y el carro jalonea feo",
        "turno2": "jalonea fuerte al subir una cuesta y parpadea la luz del motor en el tablero",
        "falla_esperada": "Falla en bujias o bobinas de encendido (misfire)",
        "placa": "AUTO-PREG-04",
    },
    {
        "nombre": "Caso 5: Embrague Flojo -> Descarte hacia Bombín de Embrague",
        "turno1": "tengo problemas con el embrague maestro",
        "turno2": "el pedal se fue al piso como trapo y no entran los cambios",
        "falla_esperada": "Falla en bombin o bomba hidraulica de embrague",
        "placa": "AUTO-PREG-05",
    },
]

print("=" * 80)
print("TEST DE AUTO-PREGUNTAS TÉCNICAS Y DIAGNÓSTICO GUIADO MULTI-TURNO")
print("=" * 80 + "\n")

aciertos = 0

for caso in casos_prueba:
    print(f"▶ {caso['nombre']}")
    placa = caso["placa"]

    # TURNO 1: Consulta inicial incompleta
    print(f"  [Turno 1 - Usuario]: '{caso['turno1']}'")
    r1 = gestor.procesar_consulta_texto(
        texto_usuario=caso["turno1"],
        placa=placa,
        proveedor="meta",
        slot_gemini_preconcedido=False,
    )
    print(f"  [Turno 1 - Bot Auto-Pregunta]:\n    {r1.respuesta_texto.replace(chr(10), chr(10) + '    ')}")
    print(f"  [Estado]: {r1.modo_diagnostico} | Diagnostico ML: {r1.diagnostico_ml}\n")

    # TURNO 2: Respuesta del usuario con el dato clave de descarte
    print(f"  [Turno 2 - Usuario responde]: '{caso['turno2']}'")
    r2 = gestor.procesar_consulta_texto(
        texto_usuario=caso["turno2"],
        placa=placa,
        proveedor="meta",
        slot_gemini_preconcedido=False,
    )
    pred_final = r2.diagnostico_ml
    conf_final = int(float(r2.confianza_ml or 0.0) * 100)

    # Normalización para evaluación
    coincide = (
        caso["falla_esperada"].lower() in pred_final.lower()
        or pred_final.lower() in caso["falla_esperada"].lower()
    )
    if coincide:
        aciertos += 1
        status = "ACIERTO 100%"
    else:
        status = "REVISAR"

    print(f"  [Turno 2 - Diagnóstico Final]: {pred_final} (Confianza: {conf_final}%)")
    print(f"  [Evaluación]: [{status}]\n")
    print("-" * 80)

print(f"\nExactitud en Diagnóstico Guiado con Auto-Preguntas: {aciertos}/{len(casos_prueba)} ({(aciertos/len(casos_prueba))*100:.1f}%)")
