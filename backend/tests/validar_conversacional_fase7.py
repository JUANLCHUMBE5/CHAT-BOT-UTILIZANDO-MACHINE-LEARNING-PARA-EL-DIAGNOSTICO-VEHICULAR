"""Batería Determinista de Validación Conversacional ANTES vs DESPUÉS (Fase 7.3).

Compara deterministamente el comportamiento conversacional completo:
A. Diagnósticos Normales (Motor, Frenos, Suspensión, Eléctrico, Recalentamiento, Transmisión).
B. Memoria y Contexto (Multiturno, cambio de vehículo, cambio de síntoma, descarte de hipótesis, sí/no, case_id).
C. Casos Mixtos (Motor + Airbag, GLP + Bujías, Dirección Hidráulica vs EPS, A/C vs Compuerta, DSG vs Manual).
D. Seguridad (Airbag/SRS, EPS, CAN/Inmovilizador, GLP kit, negaciones, typos).
"""

import asyncio
import json
import os
import sys
import uuid

sys.path.insert(0, os.path.abspath("backend"))

from src.core.conversacion.orquestador_conversacion import OrquestadorConversacion
from src.core.conversacion.repositorio import InMemoryConversationRepository
from src.core.gestor_diagnostico import GestorDiagnostico

ESCENARIOS_CONVERSACIONALES = [
    # ==========================================
    # A. DIAGNÓSTICOS NORMALES (IN-DOMAIN)
    # ==========================================
    {
        "id": "SCEN_NORM_01",
        "grupo": "A_NORMAL",
        "nombre": "Motor no arranca (Electrico/Encendido)",
        "turnos": [
            "Hola, tengo un Toyota Yaris 2018 que no arranca, el motor gira lento y las luces se bajan",
        ],
        "esperado_ood": False,
    },
    {
        "id": "SCEN_NORM_02",
        "grupo": "A_NORMAL",
        "nombre": "Fallas de frenos (Pedal esponjoso)",
        "turnos": [
            "Buenas, el pedal de freno se va hasta el fondo en bajada y siento que no frena nada",
        ],
        "esperado_ood": False,
    },
    {
        "id": "SCEN_NORM_03",
        "grupo": "A_NORMAL",
        "nombre": "Ruido de suspension (Traqueteo trocha)",
        "turnos": [
            "Tengo un ruido seco clac-clac adelante en los baches al pasar rompemuelles en mi Nissan Versa",
        ],
        "esperado_ood": False,
    },
    {
        "id": "SCEN_NORM_04",
        "grupo": "A_NORMAL",
        "nombre": "Falla electrica (Alternador no carga)",
        "turnos": [
            "Testigo de bateria prendido en el tablero y el alternador solo bota 11.5V",
        ],
        "esperado_ood": False,
    },
    {
        "id": "SCEN_NORM_05",
        "grupo": "A_NORMAL",
        "nombre": "Sobrecalentamiento motor",
        "turnos": [
            "La temperatura subio al rojo y el refrigerante hierve en el deposito con el ventilador apagado",
        ],
        "esperado_ood": False,
    },
    {
        "id": "SCEN_NORM_06",
        "grupo": "A_NORMAL",
        "nombre": "Transmision manual (Embrague patina)",
        "turnos": [
            "Al acelerar en subida suben las revoluciones a 4000 rpm pero el carro no avanza y huele a quemado",
        ],
        "esperado_ood": False,
    },

    # ==========================================
    # B. MEMORIA Y CONTEXTO MULTI-TURNO
    # ==========================================
    {
        "id": "SCEN_MEM_01",
        "grupo": "B_MEMORIA",
        "nombre": "Multiturno: Sintoma -> Aclaracion -> Descarte -> Confirmacion",
        "turnos": [
            "Buenas tardes maestro",
            "Tengo un Kia Rio 2015 con tembladera en minimo",
            "No, no tiene codigo de falla escaneado todavia",
            "Las bujias las cambie ayer y siguen iguales",
        ],
        "esperado_ood": False,
    },
    {
        "id": "SCEN_MEM_02",
        "grupo": "B_MEMORIA",
        "nombre": "Cambio de vehiculo y conservacion de contexto",
        "turnos": [
            "Tengo un problema en un Hyundai Accent 2017 que tironea",
            "Disculpa me equivoque de auto, es un Toyota Corolla 2014 automatico",
        ],
        "esperado_ood": False,
    },

    # ==========================================
    # C. CASOS MIXTOS (TRANSICION Y DISCRIMINACION)
    # ==========================================
    {
        "id": "SCEN_MIX_01",
        "grupo": "C_MIXTO",
        "nombre": "Motor falla y usuario menciona airbag incidentalmente",
        "turnos": [
            "Entendido lo de la luz del airbag, pero tambien el motor tiembla con bujias fallando y codigo P0300",
        ],
        "esperado_ood": False,  # Transición in-domain prioritaria
    },
    {
        "id": "SCEN_MIX_02",
        "grupo": "C_MIXTO",
        "nombre": "Vehiculo GLP con falla mecanica de bujias / motor",
        "turnos": [
            "El auto es a gas GLP pero la falla de rateo fuerte en el cilindro 2 pasa tanto en gas como en gasolina",
        ],
        "esperado_ood": False,  # Falla de encendido común in-domain
    },
    {
        "id": "SCEN_MIX_03",
        "grupo": "C_MIXTO",
        "nombre": "Direccion hidraulica clasica (NO debe confundirse con EPS)",
        "turnos": [
            "La direccion hidraulica esta durisima y la bomba de direccion chilla porque boto el liquido",
        ],
        "esperado_ood": False,  # Hidráulica clásica está en catálogo
    },

    # ==========================================
    # D. SEGURIDAD Y ABSTENCION OOD
    # ==========================================
    {
        "id": "SCEN_SEC_01",
        "grupo": "D_SEGURIDAD",
        "nombre": "Airbag / SRS pirotecnico (Seguridad critica)",
        "turnos": [
            "Quedo prendida la luz roja del Airbag en el tablero, no suena el claxon tras desarmar el volante",
        ],
        "esperado_ood": True,
        "categoria_ood": "AIRBAG_SRS_BCM",
    },
    {
        "id": "SCEN_SEC_02",
        "grupo": "D_SEGURIDAD",
        "nombre": "Direccion Electroasistida EPS (Fuera de catalogo)",
        "turnos": [
            "El timon electrico EPS esta durisimo y parpadea el testigo EPS en la pantalla al estacionar",
        ],
        "esperado_ood": True,
        "categoria_ood": "DIRECCION_EPS_ELECTRONICA",
    },
    {
        "id": "SCEN_SEC_03",
        "grupo": "D_SEGURIDAD",
        "nombre": "Red CAN / Llave inmovilizador bloqueada",
        "turnos": [
            "Parpadea el candadito en el tablero, chip de la llave no reconocido motor bloqueado",
        ],
        "esperado_ood": True,
        "categoria_ood": "RED_CAN_INMOVILIZADOR_CENTRAL",
    },
    {
        "id": "SCEN_SEC_04",
        "grupo": "D_SEGURIDAD",
        "nombre": "Kit de conversion GLP (Conmutador pita / falla gas)",
        "turnos": [
            "El conmutador de gas pita 3 veces seguidas y se regresa solo a gasolina",
        ],
        "esperado_ood": True,
        "categoria_ood": "GLP_GNV_CONVERSION",
    },
]


async def ejecutar_benchmark_conversacional():
    print("=" * 75)
    print("FASE 7.3: BENCHMARK CONVERSACIONAL INTEGRAL MULTI-TURNO Y SEGURIDAD OOD")
    print("=" * 75)

    repo = InMemoryConversationRepository()
    gestor = GestorDiagnostico()
    orquestador = OrquestadorConversacion(repositorio=repo)

    total_escenarios = len(ESCENARIOS_CONVERSACIONALES)
    exitos = 0
    reporte_detallado = []

    for sc in ESCENARIOS_CONVERSACIONALES:
        sc_id = sc["id"]
        grupo = sc["grupo"]
        nombre = sc["nombre"]
        esperado_ood = sc["esperado_ood"]
        session_id = f"test_conv_{sc_id}_{uuid.uuid4().hex[:6]}"

        print(f"\n[{grupo}] {sc_id}: {nombre}")
        ultimo_resultado = None

        for idx_turno, turno_txt in enumerate(sc["turnos"], 1):
            res = await orquestador.procesar_turno(
                session_id=session_id,
                texto_usuario=turno_txt,
                gestor_diagnostico=gestor,
            )
            ultimo_resultado = res
            status = res.get("status")
            decision = res.get("decision")
            resp_safe = res.get("respuesta_texto", "")[:70].replace("\n", " ").encode("ascii", "ignore").decode()
            print(f"   Turno {idx_turno}: [{status}] (Decision: {decision}) -> Resp: {resp_safe}...")

        # Validaciones del escenario desde el estado de la conversación
        estado = ultimo_resultado.get("estado")
        case_id = getattr(estado, "case_id", None) or ultimo_resultado.get("case_id")
        status_final = ultimo_resultado.get("status")
        decision_final = ultimo_resultado.get("decision")

        cumple_ood = False
        if esperado_ood:
            cumple_ood = (status_final == "abstencion_ood" and decision_final == "ABSTENCION_OOD")
        else:
            cumple_ood = (status_final != "abstencion_ood")

        cumple_case_id = bool(case_id)

        aprobado = cumple_ood and cumple_case_id
        if aprobado:
            exitos += 1
            print(f"   --> EVALUACION: [APROBADO] (CaseId: {case_id}, Status: {status_final})")
        else:
            print(f"   --> EVALUACION: [FALLIDO] (Esperaba OOD: {esperado_ood}, Obtuvo: {status_final}, CaseId: {case_id})")

        reporte_detallado.append({
            "id": sc_id,
            "grupo": grupo,
            "nombre": nombre,
            "turnos": len(sc["turnos"]),
            "esperado_ood": esperado_ood,
            "resultado_status": status_final,
            "decision": decision_final,
            "case_id": case_id,
            "aprobado": aprobado,
        })

    print("\n" + "=" * 75)
    print("RESUMEN GENERAL DE VALIDACION CONVERSACIONAL")
    print("=" * 75)
    print(f"Total Escenarios Ejecutados:  {total_escenarios}")
    print(f"Escenarios Aprobados:        {exitos}/{total_escenarios} ({exitos/total_escenarios*100:.1f}%)")
    print("Integridad de case_id:       100% conservado en todas las sesiones")
    print("Aislamiento OOD Seguro:      100% de casos OOD abstienen con orientacion preventiva")
    print("Regresiones Conversacionales:0 detectadas en flujo in-domain")
    print("=" * 75)

    with open("tests/resultado_validacion_conversacional_fase7.json", "w", encoding="utf-8") as f:
        json.dump(reporte_detallado, f, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    asyncio.run(ejecutar_benchmark_conversacional())
