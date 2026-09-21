"""Prueba real de extremo a extremo para Fase 9.10 con persistencia real en PostgreSQL."""

from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

# Añadir backend al sys.path
BASE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(BASE_DIR / "backend"))

from src.application.services import GestorDiagnostico
from src.core.conversacion.models import ConversationPhase, EstadoOperativo
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
    print("FASE 9.10 — PRUEBA REAL END-TO-END CON PERSISTENCIA EN POSTGRESQL")
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

    session_id = "wapp_51955095147_fase9_10_test"
    # Limpiar cualquier residuo previo de prueba
    await repo.close_session(session_id)

    # 3. CASO 1: Reporte inicial de no arranque
    msg_caso_1 = (
        "Buenas, mi carro tiene un problema. Ayer lo dejé estacionado en la calle "
        "y cuando volví en la noche ya no quiso arrancar. Le doy a la llave y hace como "
        "un clic seco, una sola vez, y nada más. Las luces del tablero sí prenden bien, y el radio también."
    )
    print("\n" + "-" * 80)
    print("[3] TURNO 1 (CASO 1 - ARRANQUE):")
    print(f"  Usuario: {msg_caso_1}")

    res_1 = await orquestador.procesar_turno(
        session_id=session_id,
        texto_usuario=msg_caso_1,
        gestor_diagnostico=gestor,
    )
    estado_1 = res_1["estado"]
    case_id_1 = estado_1.case_id

    print(f"  Case ID:            {case_id_1}")
    print(f"  Estado Operativo:   {res_1['estado_operativo']}")
    print(f"  Decisión:           {res_1['decision']}")
    print(f"  Respuesta CarBot:\n    {res_1['respuesta_texto']}")

    assert estado_1.estado_operativo == EstadoOperativo.ARRANQUE
    assert "motor_arranca" in estado_1.hechos
    assert estado_1.hechos["motor_arranca"].valor == "NO"

    # 4. CASO 2: Llegada de mensaje de frenado sobre la misma sesión
    msg_caso_2 = (
        "Buenas, tengo un problema con mi carro. Cuando manejo normalmente todo va bien, "
        "pero cuando freno desde una velocidad más o menos alta empiezo a sentir una vibración fuerte en el volante. "
        "A baja velocidad casi no se siente. No se prende ninguna luz en el tablero y el carro sí frena, "
        "pero la vibración me preocupa. ¿Qué podría ser?"
    )
    print("\n" + "-" * 80)
    print("[4] TURNO 2 (CASO 2 - FRENADO EN EL MISMO NÚMERO DE WHATSAPP):")
    print(f"  Usuario: {msg_caso_2}")

    res_2 = await orquestador.procesar_turno(
        session_id=session_id,
        texto_usuario=msg_caso_2,
        gestor_diagnostico=gestor,
    )
    estado_2 = res_2["estado"]
    case_id_2 = estado_2.case_id

    print(f"  Case ID anterior:        {case_id_1}")
    print(f"  Case ID nuevo:           {case_id_2}")
    print(f"  Decisión Transición:     {res_2.get('decision_transicion')}")
    print(f"  Motivo Transición:       {res_2.get('motivo_transicion')}")
    print(f"  Estado Operativo Previo: {res_2.get('estado_previo')}")
    print(f"  Estado Operativo Actual: {res_2.get('estado_operativo')}")
    print(f"  Consulta Consolidada ML: '{res_2.get('consulta_consolidada')}'")
    print(f"  Hechos Históricos:       {len(estado_2.hechos_historicos)} caso(s) archivado(s)")
    print(f"  Hechos Activos:          {list(estado_2.hechos.keys())}")

    # Verificación de aislamiento estricto
    assert case_id_2 != case_id_1, "El case_id DEBE ser diferente tras la incompatibilidad"
    assert res_2.get("decision_transicion") == "CAMBIO_DE_CASO"
    assert "ARRANQUE" in res_2.get("motivo_transicion", "") and "FRENADO" in res_2.get("motivo_transicion", "")
    assert "motor_arranca" not in estado_2.hechos, "Los hechos de arranque no deben existir en el caso activo"
    assert "no arranca" not in res_2["consulta_consolidada"].lower()
    assert "batería" not in res_2["consulta_consolidada"].lower()

    # 5. Inferencia del modelo ML sobre la consulta limpia generada
    dto_ml = gestor.procesar_consulta_texto(
        texto_usuario=res_2["consulta_consolidada"],
        session_id=session_id,
    )
    print("\n[5] EVALUACIÓN DEL MODELO ML SOBRE LA CONSULTA LIMPIA SEGMENTADA:")
    print(f"  Consulta ML:         '{res_2['consulta_consolidada']}'")
    print(f"  Sistema Principal:   {getattr(dto_ml, 'sistema_principal', 'N/A')}")
    print(f"  Diagnóstico Top 1:   {dto_ml.diagnostico_ml} ({dto_ml.confianza_ml*100:.2f}%)")
    top3_raw = [
        {"falla": p.falla if hasattr(p, "falla") else p["falla"], "probabilidad": round(p.probabilidad if hasattr(p, "probabilidad") else p["probabilidad"], 4)}
        for p in (dto_ml.predicciones_ml or [])[:3]
    ]
    print(f"  Top 3 ML RAW:        {json.dumps(top3_raw, ensure_ascii=False, indent=2)}")

    from src.core.conversacion.formateador_compacto import FormateadorCompacto
    scores_pres = FormateadorCompacto.calcular_scores_presentacion(top3_raw)
    print(f"  Scores Presentación: {json.dumps(scores_pres, ensure_ascii=False, indent=2)}")
    suma_pres = sum(s["porcentaje_presentacion"] for s in scores_pres)
    print(f"  Suma porcentajes:    {suma_pres}% (<= 100% estricto: {suma_pres <= 100})")

    assert "freno" in dto_ml.diagnostico_ml.lower() or "disco" in dto_ml.diagnostico_ml.lower()
    assert "batería" not in dto_ml.diagnostico_ml.lower()
    assert suma_pres <= 100

    # 6. Recuperación y validación del estado directamente desde PostgreSQL
    estado_pg = await repo.get_session(session_id)
    print("\n[6] TRACE DIRECTO DESDE POSTGRESQL:")
    print(f"  Session ID:               {estado_pg.session_id}")
    print(f"  Case ID Activo en BD:     {estado_pg.case_id}")
    print(f"  Estado Operativo en BD:   {estado_pg.estado_operativo.value}")
    print(f"  Hechos Históricos en BD:  {len(estado_pg.hechos_historicos)} caso(s)")
    print(f"  Turnos en Trazabilidad:   {len(estado_pg.trazabilidad)}")

    for t in estado_pg.trazabilidad:
        print(f"\n  --- Traza Turno {t['turno']} ---")
        print(f"    Mensaje:              {t['mensaje_original'][:60]}...")
        print(f"    Decisión:             {t['decision']}")
        print(f"    Decisión Transición:  {t.get('decision_transicion')}")
        print(f"    Motivo Transición:    {t.get('motivo_transicion')}")
        print(f"    Estado Operativo:     {t.get('estado_operativo')}")
        print(f"    Consulta Consolidada: {t.get('consulta_consolidada')}")
        print(f"    Version Orquestador:  {t.get('version_orquestador')}")

    await cerrar_conexion()
    print("\n" + "=" * 80)
    print("TODAS LAS CONDICIONES DE FASE 9.10 FUERON VERIFICADAS CON ÉXITO")
    print("=" * 80)


if __name__ == "__main__":
    asyncio.run(main())
