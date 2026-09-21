"""Prueba real de extremo a extremo para Fase 9.11 con persistencia real en PostgreSQL.

Reproduce exactamente el flujo de WhatsApp del incidente real:
Turno 1: Tirones y pérdida de fuerza al acelerar / pendiente.
Turno 2: Respuesta térmica (frío y caliente, peor al acelerar fuerte).
Turno 3: 'No lo he revisado. No tengo herramientas para comprobar la chispa ni medir la presión de gasolina.'
Turno 4: Verificación sensorial sin herramientas (Plan B).
"""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

# Añadir backend al sys.path
BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR / "backend"))
sys.stdout.reconfigure(encoding="utf-8")

from src.application.services import GestorDiagnostico
from src.core.conversacion.models import ConversationPhase, EstadoOperativo, QuestionIntent
from src.core.conversacion.orquestador_conversacion import OrquestadorConversacion
from src.core.conversacion.repositorio import PostgresConversationRepository
from src.core.version import (
    APP_VERSION,
    CODE_BUILD_ID,
    ORCHESTRATOR_VERSION,
    obtener_telemetria_proceso,
    verificar_paridad_runtime,
)
from src.infrastructure.database.connection import cerrar_conexion, comprobar_conexion


async def main() -> None:
    print("=" * 80)
    print("FASE 9.11 — AUDITORÍA Y COMPROBACIÓN REAL DE PLAN B SIN HERRAMIENTAS")
    print("=" * 80)

    # 1. Comprobación de versiones y paridad de procesos
    telemetria_api = obtener_telemetria_proceso("api")
    telemetria_worker = obtener_telemetria_proceso("worker")
    paridad = verificar_paridad_runtime(telemetria_api, telemetria_worker)

    print("\n[1] TELEMETRÍA EN RUNTIME Y PARIDAD DE PROCESOS:")
    print(f"  APP_VERSION:          {APP_VERSION}")
    print(f"  ORCHESTRATOR_VERSION: {ORCHESTRATOR_VERSION}")
    print(f"  CODE_BUILD_ID:        {CODE_BUILD_ID}")
    print(f"  PID API:              {telemetria_api['pid']}")
    print(f"  PID Worker:           {telemetria_worker['pid']}")
    print(f"  Paridad API-Worker:   {'COMPROBADA (100% IDÉNTICO)' if paridad else 'DISCREPANCIA'}")
    assert paridad, "Discrepancia entre API y Worker"

    # 2. Conectar a PostgreSQL
    await comprobar_conexion()
    print("\n[2] CONEXIÓN A POSTGRESQL: EXITOSA")

    repo = PostgresConversationRepository()
    gestor = GestorDiagnostico()
    orquestador = OrquestadorConversacion(repositorio=repo)

    session_id = "wapp_51955095147_fase9_11_audit"
    # Limpiar cualquier residuo previo de prueba
    await repo.close_session(session_id)

    # -------------------------------------------------------------------------
    # TURNO 1: Reporte del síntoma inicial
    # -------------------------------------------------------------------------
    print("\n" + "-" * 80)
    print("TURNO 1: SÍNTOMA INICIAL (Tirones en marcha)")
    print("-" * 80)
    msg_t1 = (
        "Cuando voy avanzando y acelero, el motor comienza a tironear y pierde fuerza. "
        "En ralentí se mantiene normal. Empeora al subir una pendiente o acelerar fuerte."
    )
    print(f"Usuario >> {msg_t1}")
    r1 = await orquestador.procesar_turno(
        session_id=session_id,
        texto_usuario=msg_t1,
        gestor_diagnostico=gestor,
        placa="WAPP-911",
        marca_modelo="Vehiculo Generico",
    )
    print(f"\nCarBot  << [{r1['decision']}] {r1['respuesta_texto']}")
    print(f"Traza T1: fase={r1['fase']}, es_pregunta={r1['es_pregunta']}, intent={r1.get('question_intent')}")

    # -------------------------------------------------------------------------
    # TURNO 2: Respuesta a la aclaración de temperatura
    # -------------------------------------------------------------------------
    print("\n" + "-" * 80)
    print("TURNO 2: RESPUESTA DE TEMPERATURA")
    print("-" * 80)
    msg_t2 = "Se siente tanto en frío como en caliente, pero cuando acelero fuerte o subo una pendiente se nota mucho más."
    print(f"Usuario >> {msg_t2}")
    r2 = await orquestador.procesar_turno(
        session_id=session_id,
        texto_usuario=msg_t2,
        gestor_diagnostico=gestor,
    )
    print(f"\nCarBot  << [{r2['decision']}]")
    print(r2["respuesta_texto"])
    print(f"Traza T2: fase={r2['fase']}, decision={r2['decision']}, diagnostico_ml={r2.get('diagnostico_ml')}")

    # -------------------------------------------------------------------------
    # TURNO 3: INCIDENTE REAL (Usuario sin herramientas para chispa ni presión)
    # -------------------------------------------------------------------------
    print("\n" + "-" * 80)
    print("TURNO 3: INCIDENTE REAL — INDISPONIBILIDAD EXPLÍCITA DE HERRAMIENTAS")
    print("-" * 80)
    msg_t3 = "No lo he revisado. No tengo herramientas para comprobar la chispa ni medir la presión de gasolina."
    print(f"Usuario >> {msg_t3}")
    r3 = await orquestador.procesar_turno(
        session_id=session_id,
        texto_usuario=msg_t3,
        gestor_diagnostico=gestor,
    )
    print(f"\nCarBot  << [{r3['decision']}]")
    print(r3["respuesta_texto"])

    # Verificaciones obligatorias de PostgreSQL
    estado_t3 = await repo.get_session(session_id)
    assert estado_t3 is not None, "Estado no persistido en PostgreSQL"

    print("\n[3] AUDITORÍA DE ESTADO EN POSTGRESQL TRAS TURNO 3:")
    print(f"  Case ID:                     {estado_t3.case_id}")
    print(f"  Herramientas No Disponibles: {estado_t3.herramientas_no_disponibles}")
    print(f"  Pruebas Bloqueadas:          {[p['prueba'] for p in estado_t3.pruebas_no_disponibles]}")
    print(f"  Hipótesis descartadas:       {estado_t3.hipotesis_descartadas}")
    print(f"  Top 3 Actual:                {[h['falla'] for h in estado_t3.top3_actual]}")

    # Validaciones técnicas
    resp_t3_lower = r3["respuesta_texto"].lower()
    assert "deseas que te detalle el procedimiento" not in resp_t3_lower, "FALLO: Repitió pregunta genérica de procedimiento"
    assert "has podido verificar este punto" not in resp_t3_lower, "FALLO: Repitió pregunta anterior"
    assert "chispa" in estado_t3.herramientas_no_disponibles or "manometro" in estado_t3.herramientas_no_disponibles, "FALLO: Herramienta no registrada"
    assert estado_t3.es_prueba_bloqueada("comprobar_chispa_bobinas"), "FALLO: Prueba de chispa no bloqueada"
    assert estado_t3.es_prueba_bloqueada("medir_presion_gasolina"), "FALLO: Prueba de presión no bloqueada"
    assert len(estado_t3.hipotesis_descartadas) == 0, "FALLO: Se descartó erróneamente una hipótesis"
    assert r3["decision"] == "PLAN_B", f"FALLO: Decisión no es PLAN_B, fue {r3['decision']}"
    assert any(w in resp_t3_lower for w in ("sin herramientas", "visual", "bobinas", "cables", "aceite")), "FALLO: No activó Plan B sensorial"

    # -------------------------------------------------------------------------
    # TURNO 4: Usuario realiza comprobación visual sin herramientas (Plan B)
    # -------------------------------------------------------------------------
    print("\n" + "-" * 80)
    print("TURNO 4: RESULTADO DE PLAN B SENSORIAL SIN HERRAMIENTAS")
    print("-" * 80)
    msg_t4 = "Ya revisé visualmente las bobinas y cables. No se ven rotas ni hay aceite, pero el cable de la bobina 2 tiene como un sulfato blanco en la conexión."
    print(f"Usuario >> {msg_t4}")
    r4 = await orquestador.procesar_turno(
        session_id=session_id,
        texto_usuario=msg_t4,
        gestor_diagnostico=gestor,
    )
    print(f"\nCarBot  << [{r4['decision']}]")
    print(r4["respuesta_texto"])

    await cerrar_conexion()
    print("\n" + "=" * 80)
    print("RESULTADO DE LA AUDITORÍA POSTGRESQL: EXITOSA (100% CONFORME)")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
