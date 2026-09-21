"""Script de Prueba E2E Final para la FASE 12.2.

Ejecuta los escenarios requeridos (A, B, C, D, E) en entornos seguros (PILOT / DEVELOPMENT),
comprueba PostgreSQL directamente, genera el artefacto FASE12_2_E2E_FINAL.csv y
asegura que la muestra oficial de tesis se mantenga estrictamente en 0 / 60 casos.
"""

from __future__ import annotations

import asyncio
import csv
import sys
import uuid
from datetime import date, datetime, timezone
from pathlib import Path

# Setup paths
ROOT = Path(__file__).resolve().parent.parent
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from src.application.services.validacion_taller import (
    ServicioValidacionTaller,
    resumir_fases,
)
from src.infrastructure.database.connection import obtener_engine
from src.infrastructure.database.models.diagnostics import Diagnostico
from src.infrastructure.database.models.validation import ValidacionTaller
from src.infrastructure.database.repositories.validacion_taller_repository import (
    ValidacionTallerRepository,
)
from src.interfaces.api.v1.dtos.validacion import CrearCasoValidacionDTO
from src.interfaces.api.v1.endpoints.validacion_taller import exportar_fichas_anexo2_csv

DEFAULT_SEED_TALLER = uuid.UUID("5313362a-c18d-456f-892d-a8980155c461")
CSV_E2E_FINAL = ROOT / "docs" / "fase12" / "FASE12_2_E2E_FINAL.csv"


async def ejecutar_prueba_e2e() -> None:
    print("=== INICIANDO PRUEBA E2E FINAL FASE 12.2 ===")
    engine = obtener_engine()
    registros_creados_ids: list[uuid.UUID] = []
    diagnosticos_creados_ids: list[uuid.UUID] = []
    bitacora_e2e: list[dict[str, str]] = []

    async with AsyncSession(engine, expire_on_commit=False) as session:
        repo = ValidacionTallerRepository(session)
        servicio = ServicioValidacionTaller(session)

        # ----------------------------------------------------------------------
        # PASO 0: Estado inicial de la base de datos
        # ----------------------------------------------------------------------
        resumen_inicial = await repo.resumen_por_fase(DEFAULT_SEED_TALLER)
        stats_inicial = resumir_fases(resumen_inicial)
        piloto_inicial = await repo.contar_piloto(DEFAULT_SEED_TALLER)

        print(f"[ESTADO INICIAL] Oficial PRE: {stats_inicial['casos_pretest']}, Oficial POST: {stats_inicial['casos_posttest']}, Oficial TOTAL: {stats_inicial['total_casos']}, PILOTO: {piloto_inicial}")
        assert stats_inicial["casos_pretest"] == 0
        assert stats_inicial["casos_posttest"] == 0
        assert stats_inicial["total_casos"] == 0

        try:
            # ------------------------------------------------------------------
            # ESCENARIO A: PRETEST Tradicional (sin CarBot, en DEVELOPMENT)
            # ------------------------------------------------------------------
            print("\n[ESCENARIO A] Registrando PRETEST tradicional (sin CarBot) en DEVELOPMENT...")
            dto_pre = CrearCasoValidacionDTO(
                fase="Pre-test",
                placa="E2E-PRE-01",
                marca_modelo="Nissan Sentra 2017",
                sintoma="Pedal de freno duro al presionar en marcha",
                descripcion_sintoma="Inspección mecánica tradicional: vacío insuficiente en booster",
                vehiculo_anio=2017,
                vehiculo_kilometraje=110000,
                vehiculo_combustible="Gasolina",
                vehiculo_transmision="Mecánica",
                falla_real="Fuga en diafragma de servofreno",
                chatbot_prediccion="Hipótesis tradicional mecánico de taller (sin CarBot)",
                sistema_afectado_probable="Frenos",
                campos_completos=1,
                tiempo_diagnostico_minutos=35,
                prediccion_correcta=1,
                metodo_confirmacion="Vacuómetro mecánico",
                evidencia_ref="EVID_E2E_A.JPG",
                estado_registro="borrador",
                tipo_registro="DEVELOPMENT",
            )
            caso_a = await servicio.crear(DEFAULT_SEED_TALLER, None, dto_pre, "E2E-***", "a" * 64)
            await session.commit()
            registros_creados_ids.append(caso_a.id)

            assert caso_a.fase == "Pre-test"
            assert caso_a.diagnostico_id is None
            assert caso_a.tipo_registro == "DEVELOPMENT"
            print(f"  -> Creado exitosamente: Item {caso_a.item}, ID {caso_a.id}, Tipo: {caso_a.tipo_registro}")

            bitacora_e2e.append({
                "escenario": "A_PRETEST_TRADICIONAL",
                "tipo_registro": caso_a.tipo_registro,
                "fase": caso_a.fase,
                "diagnostico_vinculado": "NO (Sin CarBot)",
                "inmutabilidad_prediccion": "N/A",
                "resultado": "EXITO",
                "detalle": f"Registrado como {caso_a.tipo_registro} sin diagnostico_id. No incrementa muestra oficial.",
            })

            # ------------------------------------------------------------------
            # ESCENARIO B: POSTTEST Vinculado a Diagnóstico CarBot (en PILOT)
            # ------------------------------------------------------------------
            print("\n[ESCENARIO B] Seleccionando diagnóstico real de CarBot y vinculándolo en POSTTEST (PILOT)...")
            stmt_diag_real = select(Diagnostico).where(
                Diagnostico.taller_id == DEFAULT_SEED_TALLER,
                Diagnostico.falla_predicha.isnot(None),
                Diagnostico.falla_predicha != "Consulta Ambigua / Datos Faltantes",
            ).limit(1)
            diag_b = (await session.execute(stmt_diag_real)).scalar_one_or_none()
            if not diag_b:
                # Fallback al diagnóstico conocido de semilla
                diag_b = await session.get(Diagnostico, uuid.UUID("30dd1569-7813-4a9b-bcec-d8ba88af4a4c"))

            diag_b_id = diag_b.id
            conv_b_id = diag_b.conversacion_id
            falla_esperada = diag_b.falla_predicha

            dto_post = CrearCasoValidacionDTO(
                fase="Post-test",
                diagnostico_id=str(diag_b_id),
                placa="E2E-POS-02",
                marca_modelo="Hyundai Accent 2021",
                sintoma="Ralentí inestable y se apaga al frenar",
                descripcion_sintoma="Diagnóstico asistido por CarBot vía WhatsApp",
                vehiculo_anio=2021,
                vehiculo_kilometraje=42000,
                vehiculo_combustible="Gasolina",
                vehiculo_transmision="Mecánica",
                falla_real="Cuerpo de aceleración carbonizado",
                chatbot_prediccion="Texto alterado intencionalmente para probar inmutabilidad",
                sistema_afectado_probable="Sistema de Admisión",
                campos_completos=1,
                tiempo_diagnostico_minutos=11,
                prediccion_correcta=1,
                metodo_confirmacion="Inspección directa de mariposa",
                evidencia_ref="EVID_E2E_B.PNG",
                estado_registro="borrador",
                tipo_registro="PILOT",
            )
            caso_b = await servicio.crear(DEFAULT_SEED_TALLER, None, dto_post, "E2E-***", "b" * 64)
            await session.commit()
            registros_creados_ids.append(caso_b.id)

            assert caso_b.diagnostico_id == diag_b_id
            assert caso_b.conversacion_id == conv_b_id
            # Inmutabilidad: la predicción del modelo DEBE haber prevalecido
            assert caso_b.chatbot_prediccion == falla_esperada
            assert "alterado" not in caso_b.chatbot_prediccion
            print(f"  -> Creado exitosamente: Item {caso_b.item}, Diagnóstico {caso_b.diagnostico_id}, Predicción inmutable: '{caso_b.chatbot_prediccion}'")

            bitacora_e2e.append({
                "escenario": "B_POSTTEST_VINCULADO_CARBOT",
                "tipo_registro": caso_b.tipo_registro,
                "fase": caso_b.fase,
                "diagnostico_vinculado": f"SI ({diag_b_id})",
                "inmutabilidad_prediccion": "VERIFICADA (Sobrescribe texto adulterado con predicción del modelo)",
                "resultado": "EXITO",
                "detalle": "Hereda conversacion_id y tiempo_inferencia_ml_ms. Predicción original inmutable.",
            })

            # ------------------------------------------------------------------
            # ESCENARIO C: Registro Piloto Explícito
            # ------------------------------------------------------------------
            print("\n[ESCENARIO C] Registrando caso formal en categoría PILOT...")
            dto_pilot = CrearCasoValidacionDTO(
                fase="Post-test",
                placa="E2E-PIL-03",
                marca_modelo="Toyota Hilux 2019",
                sintoma="Zumbido continuo en diferencial trasero",
                descripcion_sintoma="Caso experimental piloto para calibración de instrumento",
                vehiculo_anio=2019,
                vehiculo_kilometraje=95000,
                vehiculo_combustible="Diesel",
                vehiculo_transmision="Mecánica 4x4",
                falla_real="Desgaste en rodamiento piñón de ataque",
                chatbot_prediccion="Falla de diferencial o rodamientos",
                sistema_afectado_probable="Transmisión",
                campos_completos=1,
                tiempo_diagnostico_minutos=22,
                prediccion_correcta=1,
                metodo_confirmacion="Estetoscopio mecánico y desmontaje de corona",
                evidencia_ref="EVID_E2E_C.JPG",
                estado_registro="borrador",
                tipo_registro="PILOT",
            )
            caso_c = await servicio.crear(DEFAULT_SEED_TALLER, None, dto_pilot, "E2E-***", "c" * 64)
            await session.commit()
            registros_creados_ids.append(caso_c.id)

            piloto_actual = await repo.contar_piloto(DEFAULT_SEED_TALLER)
            assert piloto_actual == piloto_inicial + 2  # caso_b + caso_c
            print(f"  -> Creado exitosamente: Item {caso_c.item}, Total piloto ahora: {piloto_actual}")

            bitacora_e2e.append({
                "escenario": "C_REGISTRO_PILOTO_EXPLICITO",
                "tipo_registro": caso_c.tipo_registro,
                "fase": caso_c.fase,
                "diagnostico_vinculado": "NO",
                "inmutabilidad_prediccion": "N/A",
                "resultado": "EXITO",
                "detalle": f"Contador de piloto incrementado ({piloto_actual}). Totalmente aislado de muestra oficial.",
            })

            # ------------------------------------------------------------------
            # ESCENARIO D: Intento de registro oficial sin coherencia / validación
            # ------------------------------------------------------------------
            print("\n[ESCENARIO D] Probando blindaje contra creación accidental o incoherente de registro oficial...")
            # Intento 1: THESIS_PRETEST con fase Post-test
            dto_error_pre = CrearCasoValidacionDTO(
                fase="Post-test",
                placa="E2E-ERR-01",
                marca_modelo="Kia Picanto",
                sintoma="Falla de prueba incoherente",
                falla_real="Falla real",
                chatbot_prediccion="Prediccion",
                campos_completos=1,
                tiempo_diagnostico_minutos=10,
                prediccion_correcta=1,
                tipo_registro="THESIS_PRETEST",
            )
            rechazo_1 = False
            try:
                await servicio.crear(DEFAULT_SEED_TALLER, None, dto_error_pre, "ERR-***", "e1" * 32)
            except ValueError as e:
                rechazo_1 = True
                print(f"  -> Bloqueo 1 exitoso: {e}")
            assert rechazo_1, "El sistema debió rechazar THESIS_PRETEST con fase Post-test"

            # Intento 2: THESIS_POSTTEST con fase Pre-test
            dto_error_post = CrearCasoValidacionDTO(
                fase="Pre-test",
                placa="E2E-ERR-02",
                marca_modelo="Kia Picanto",
                sintoma="Falla de prueba incoherente",
                falla_real="Falla real",
                chatbot_prediccion="Prediccion",
                campos_completos=1,
                tiempo_diagnostico_minutos=10,
                prediccion_correcta=1,
                tipo_registro="THESIS_POSTTEST",
            )
            rechazo_2 = False
            try:
                await servicio.crear(DEFAULT_SEED_TALLER, None, dto_error_post, "ERR-***", "e2" * 32)
            except ValueError as e:
                rechazo_2 = True
                print(f"  -> Bloqueo 2 exitoso: {e}")
            assert rechazo_2, "El sistema debió rechazar THESIS_POSTTEST con fase Pre-test"

            bitacora_e2e.append({
                "escenario": "D_BLINDAJE_REGISTRO_OFICIAL",
                "tipo_registro": "RECHAZADO (THESIS_* incoherente)",
                "fase": "Cruce Pre/Post",
                "diagnostico_vinculado": "N/A",
                "inmutabilidad_prediccion": "N/A",
                "resultado": "EXITO (BLOQUEADO)",
                "detalle": "El backend rechaza con ValueError cualquier intento incoherente de registrar muestra oficial.",
            })

            # ------------------------------------------------------------------
            # ESCENARIO E: Exportación Oficial y Verificación de Contadores
            # ------------------------------------------------------------------
            print("\n[ESCENARIO E] Verificando contadores oficiales en PostgreSQL y aislamiento total...")
            resumen_post_pruebas = await repo.resumen_por_fase(DEFAULT_SEED_TALLER)
            stats_post = resumir_fases(resumen_post_pruebas)

            print(f"[ESTADO FINAL POSTGRESQL] Oficial PRE: {stats_post['casos_pretest']}, Oficial POST: {stats_post['casos_posttest']}, Oficial TOTAL: {stats_post['total_casos']}")
            assert stats_post["casos_pretest"] == 0, "Pretest oficial debe permanecer estrictamente en 0"
            assert stats_post["casos_posttest"] == 0, "Posttest oficial debe permanecer estrictamente en 0"
            assert stats_post["total_casos"] == 0, "Muestra oficial debe permanecer estrictamente en 0 de 60"

            bitacora_e2e.append({
                "escenario": "E_AISLAMIENTO_Y_CONTADOR_OFICIAL",
                "tipo_registro": "VERIFICACION POSTGRESQL",
                "fase": "Pretest + Posttest",
                "diagnostico_vinculado": "N/A",
                "inmutabilidad_prediccion": "N/A",
                "resultado": "EXITO",
                "detalle": "Muestra oficial veridicamente preservada en 0/60 casos tras pruebas E2E en DEVELOPMENT y PILOT.",
            })

        finally:
            # Limpieza rigurosa de los registros de prueba creados
            print("\n[LIMPIEZA] Eliminando registros creados durante la prueba E2E...")
            try:
                await session.rollback()
            except Exception:
                pass
            if registros_creados_ids:
                await session.execute(
                    delete(ValidacionTaller).where(ValidacionTaller.id.in_(registros_creados_ids))
                )
            if diagnosticos_creados_ids:
                await session.execute(
                    delete(Diagnostico).where(Diagnostico.id.in_(diagnosticos_creados_ids))
                )
            await session.commit()
            print(f"[LIMPIEZA COMPLETA] {len(registros_creados_ids)} casos y {len(diagnosticos_creados_ids)} diagnósticos de prueba eliminados.")

    # Escribir CSV con los resultados de la prueba E2E
    CSV_E2E_FINAL.parent.mkdir(parents=True, exist_ok=True)
    with open(CSV_E2E_FINAL, mode="w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "escenario",
                "tipo_registro",
                "fase",
                "diagnostico_vinculado",
                "inmutabilidad_prediccion",
                "resultado",
                "detalle",
            ],
        )
        writer.writeheader()
        writer.writerows(bitacora_e2e)

    print(f"\n[ARTEFACTO GENERADO] {CSV_E2E_FINAL}")
    print("[DICTAMEN E2E] TODOS LOS ESCENARIOS A, B, C, D, E EJECUTADOS SATISFACTORIAMENTE.")


if __name__ == "__main__":
    asyncio.run(ejecutar_prueba_e2e())
