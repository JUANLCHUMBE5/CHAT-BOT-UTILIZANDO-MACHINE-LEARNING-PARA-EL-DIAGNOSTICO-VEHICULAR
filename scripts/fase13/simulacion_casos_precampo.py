"""Simulación de Casos Pre-campo A a G en entornos aislados (TEST/PILOT).

Valida todas las reglas de negocio e invariantes sin contaminar la muestra oficial de tesis:
- CASO A: PRE tradicional completo (PILOT, sin CarBot).
- CASO B: POST asistido completo (PILOT, CarBot inmutable).
- CASO C: Registro incompleto bloqueado (degradado a borrador sin evidencia).
- CASO D: Intento de adulteración de predicción (inmutabilidad forzada por backend).
- CASO E: Intento de exportar PILOT como oficial (estricta exclusión en exportación).
- CASO F: Fase y tipo incompatibles (rechazo con ValueError).
- CASO G: Omisión de entorno (defaults a DEVELOPMENT, jamás THESIS).

Al finalizar, ejecuta limpieza completa dejando la base de datos intacta.
"""

from __future__ import annotations

import asyncio
import hashlib
import sys
import uuid
from datetime import datetime, timezone
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from src.application.services.validacion_taller import ServicioValidacionTaller
from src.infrastructure.database.connection import obtener_engine
from src.infrastructure.database.models.catalogs import Usuario
from src.infrastructure.database.models.diagnostics import Diagnostico
from src.infrastructure.database.models.validation import ValidacionTaller
from src.infrastructure.database.repositories.validacion_taller_repository import ValidacionTallerRepository
from src.interfaces.api.v1.dtos.validacion import CrearCasoValidacionDTO


async def ejecutar_simulacion() -> dict[str, bool]:
    engine = obtener_engine()
    resultados: dict[str, bool] = {}
    ids_creados: list[uuid.UUID] = []
    diag_test_id: uuid.UUID | None = None

    async with AsyncSession(engine, expire_on_commit=False) as session:
        servicio = ServicioValidacionTaller(session)
        repo = ValidacionTallerRepository(session)

        # 0. Obtener usuario y taller real para FK
        user_row = (await session.execute(select(Usuario.id, Usuario.taller_id).limit(1))).first()
        if not user_row:
            raise RuntimeError("No se encontró ningún usuario en la base de datos.")
        test_user_id, test_taller_id = user_row[0], user_row[1]
        print(f"Usuario de prueba: {test_user_id} | Taller: {test_taller_id}")

        # Verificación inicial de contadores oficiales
        print("\n--- PASO 0: VERIFICACIÓN DE CONTADORES INICIALES ---")
        stmt_pre = select(func.count()).where(
            ValidacionTaller.tipo_registro == "THESIS_PRETEST",
            ValidacionTaller.estado_registro == "verificado",
        )
        pre_init = (await session.execute(stmt_pre)).scalar_one()

        stmt_post = select(func.count()).where(
            ValidacionTaller.tipo_registro == "THESIS_POSTTEST",
            ValidacionTaller.estado_registro == "verificado",
        )
        post_init = (await session.execute(stmt_post)).scalar_one()

        print(f"Pre-test oficial inicial: {pre_init}/30")
        print(f"Post-test oficial inicial: {post_init}/30")
        print(f"Total oficial inicial: {pre_init + post_init}/60")
        assert pre_init == 0 and post_init == 0, "ERROR: Hay registros oficiales verificados antes del test!"

        # Crear Diagnóstico sintético previo para pruebas de POST
        diag_test_id = uuid.uuid4()
        diag_dummy = Diagnostico(
            id=diag_test_id,
            taller_id=test_taller_id,
            mecanico_id=test_user_id,
            sintoma_original="Motor no arranca y se escucha un chasquido metálico seco",
            falla_predicha="Falla en motor de arranque o solenoide defectuoso (clac seco o carbones gastados)",
            confianza=Decimal("0.9200"),
            fuente="ml",
            modo_diagnostico="completo_ml_rag_llm",
            estado="generado",
            duracion_ms=45,
            tiempo_inferencia_ml_ms=45,
            creado_en=datetime.now(timezone.utc),
        )
        session.add(diag_dummy)
        await session.commit()
        print(f"Diagnóstico de prueba creado: {diag_test_id}")

        try:
            # -------------------------------------------------------------
            # CASO A: PRE tradicional completo en entorno PILOT
            # -------------------------------------------------------------
            print("\n--- CASO A: PRE TRADICIONAL COMPLETO (PILOT) ---")
            dto_a = CrearCasoValidacionDTO(
                fase="Pre-test",
                fecha="2026-09-20",
                placa="PIL-001",
                marca_modelo="Toyota Yaris 2018",
                sintoma="Pedal de freno vibra fuertemente al frenar a más de 60 km/h",
                descripcion_sintoma="Vibración en timón y pedal de freno a altas velocidades en autopista",
                vehiculo_anio=2018,
                vehiculo_kilometraje=85000,
                vehiculo_combustible="Gasolina",
                vehiculo_transmision="Manual",
                falla_real="Discos de freno alabeados o desgastados",
                chatbot_prediccion="Discos de freno alabeados",
                sistema_afectado_probable="Sistema de Frenos",
                campos_completos=1,
                tiempo_diagnostico_minutos=35,
                prediccion_correcta=1,
                metodo_confirmacion="Reloj comparador centesimal en disco",
                evidencia_ref="INFORME-METROLOGIA-001.jpg",
                estado_registro="verificado",
                tipo_registro="PILOT",
                diagnostico_id=None,
                conversacion_id=None,
            )
            caso_a = await servicio.crear(
                taller_id=test_taller_id,
                usuario_id=test_user_id,
                dto=dto_a,
                placa_enmascarada="PIL-***",
                placa_hash=hashlib.sha256(dto_a.placa.encode()).hexdigest(),
            )
            ids_creados.append(caso_a.id)
            await session.commit()

            assert caso_a.tipo_registro == "PILOT"
            assert caso_a.estado_registro == "verificado"
            assert caso_a.diagnostico_id is None
            assert caso_a.campos_completos == 1
            resultados["CASO_A"] = True
            print("[OK] CASO A superado: PRE tradicional registrado en PILOT sin requerir CarBot.")

            # -------------------------------------------------------------
            # CASO B: POST asistido completo en entorno PILOT
            # -------------------------------------------------------------
            print("\n--- CASO B: POST ASISTIDO COMPLETO (PILOT) ---")
            dto_b = CrearCasoValidacionDTO(
                fase="Post-test",
                fecha="2026-09-20",
                placa="PIL-999",
                marca_modelo="Nissan Versa 2020",
                sintoma="Motor no arranca y se escucha un chasquido metálico seco",
                descripcion_sintoma="Al girar la llave en ignición no gira el motor",
                vehiculo_anio=2020,
                vehiculo_kilometraje=62000,
                vehiculo_combustible="Gasolina",
                vehiculo_transmision="Automatica",
                falla_real="Falla en motor de arranque o solenoide defectuoso (clac seco o carbones gastados)",
                chatbot_prediccion="Falla en motor de arranque o solenoide defectuoso (clac seco o carbones gastados)",
                sistema_afectado_probable="Sistema de Arranque y Eléctrico",
                campos_completos=1,
                tiempo_diagnostico_minutos=14,
                prediccion_correcta=1,
                metodo_confirmacion="Prueba de caída de tensión en solenoide y banco de prueba de arranque",
                evidencia_ref="OSCILOGRAMA-ARRANQUE-002.pdf",
                estado_registro="verificado",
                tipo_registro="PILOT",
                diagnostico_id=str(diag_test_id),
                sintoma_registrado_correctamente=1,
                normalizacion_correcta=1,
                extraccion_correcta=1,
                clasificacion_procesada=1,
            )
            caso_b = await servicio.crear(
                taller_id=test_taller_id,
                usuario_id=test_user_id,
                dto=dto_b,
                placa_enmascarada="PIL-***",
                placa_hash=hashlib.sha256(dto_b.placa.encode()).hexdigest(),
            )
            ids_creados.append(caso_b.id)
            await session.commit()

            assert caso_b.tipo_registro == "PILOT"
            assert caso_b.estado_registro == "verificado"
            assert caso_b.diagnostico_id == diag_test_id
            assert caso_b.chatbot_prediccion == diag_dummy.falla_predicha
            assert caso_b.tiempo_inferencia_ml_ms == 45
            assert caso_b.procesamiento_validado == 1
            resultados["CASO_B"] = True
            print("[OK] CASO B superado: POST asistido vinculado a CarBot con telemetría y diagnóstico inmutable.")

            # -------------------------------------------------------------
            # CASO C: Registro incompleto (falta evidencia/método)
            # -------------------------------------------------------------
            print("\n--- CASO C: REGISTRO INCOMPLETO (SIN EVIDENCIA) ---")
            dto_c = CrearCasoValidacionDTO(
                fase="Pre-test",
                fecha="2026-09-20",
                placa="PIL-003",
                marca_modelo="Kia Rio 2019",
                sintoma="Ruido al girar",
                descripcion_sintoma="Crujido en curva",
                falla_real="Juntas homocineticas o palieres danados",
                chatbot_prediccion="Juntas homocineticas",
                campos_completos=0,
                tiempo_diagnostico_minutos=25,
                prediccion_correcta=1,
                metodo_confirmacion="",  # Vacío intencionalmente
                evidencia_ref="",        # Vacío intencionalmente
                estado_registro="verificado",  # Intenta declararse verificado sin evidencia
                tipo_registro="PILOT",
            )
            caso_c = await servicio.crear(
                taller_id=test_taller_id,
                usuario_id=test_user_id,
                dto=dto_c,
                placa_enmascarada="PIL-***",
                placa_hash=hashlib.sha256(dto_c.placa.encode()).hexdigest(),
            )
            ids_creados.append(caso_c.id)
            await session.commit()

            assert caso_c.estado_registro == "borrador", "ERROR: Se debió degradar a borrador"
            resultados["CASO_C"] = True
            print("[OK] CASO C superado: Registro sin evidencia física fue degradado automáticamente a 'borrador'.")

            # -------------------------------------------------------------
            # CASO D: Intento de adulterar predicción CarBot
            # -------------------------------------------------------------
            print("\n--- CASO D: INTENTO DE ADULTERAR PREDICCIÓN ORIGINAL ---")
            dto_d = CrearCasoValidacionDTO(
                fase="Post-test",
                fecha="2026-09-20",
                placa="PIL-004",
                marca_modelo="Nissan Versa 2020",
                sintoma="Motor no arranca",
                falla_real="Falla en motor de arranque o solenoide defectuoso (clac seco o carbones gastados)",
                chatbot_prediccion="PREDICCION_FALSA_ADULTERADA_POR_USUARIO",  # Intento de alterar
                sistema_afectado_probable="Sistema de Arranque",
                campos_completos=1,
                tiempo_diagnostico_minutos=18,
                prediccion_correcta=1,
                metodo_confirmacion="Inspeccion",
                evidencia_ref="EVIDENCIA.jpg",
                estado_registro="verificado",
                tipo_registro="PILOT",
                diagnostico_id=str(diag_test_id),  # Vinculado al diagnóstico original
            )
            caso_d = await servicio.crear(
                taller_id=test_taller_id,
                usuario_id=test_user_id,
                dto=dto_d,
                placa_enmascarada="PIL-***",
                placa_hash=hashlib.sha256(dto_d.placa.encode()).hexdigest(),
            )
            ids_creados.append(caso_d.id)
            await session.commit()

            assert caso_d.chatbot_prediccion == diag_dummy.falla_predicha, "ERROR: La predicción fue adulterada!"
            assert caso_d.chatbot_prediccion != "PREDICCION_FALSA_ADULTERADA_POR_USUARIO"
            resultados["CASO_D"] = True
            print("[OK] CASO D superado: El backend protegió la predicción original ignorando la alteración enviada.")

            # -------------------------------------------------------------
            # CASO E: Intento de exportar PILOT como oficial
            # -------------------------------------------------------------
            print("\n--- CASO E: INTENTO DE EXPORTAR PILOT COMO OFICIAL ---")
            # Consultamos la exportación de Anexo 2 (solo verificados oficiales)
            casos_oficiales = await repo.listar_todos(test_taller_id, solo_verificados=True)
            assert len(casos_oficiales) == 0, f"ERROR: La exportación oficial contiene {len(casos_oficiales)} casos cuando debería ser 0!"
            resultados["CASO_E"] = True
            print("[OK] CASO E superado: Los registros PILOT (incluso verificados) son 100% excluidos de la exportación oficial.")

            # -------------------------------------------------------------
            # CASO F: Fase y tipo incompatibles
            # -------------------------------------------------------------
            print("\n--- CASO F: FASE Y TIPO INCOMPATIBLES ---")
            dto_f1 = CrearCasoValidacionDTO(
                fase="Post-test",  # Fase Post pero tipo PRE
                tipo_registro="THESIS_PRETEST",
                placa="INC-001",
                marca_modelo="Toyota Yaris",
                sintoma="Falla al arrancar",
                falla_real="Falla en motor de arranque",
                chatbot_prediccion="Falla en motor de arranque",
                campos_completos=1,
                tiempo_diagnostico_minutos=20,
                prediccion_correcta=1,
            )
            incompatible_f1 = False
            try:
                await servicio.crear(
                    taller_id=test_taller_id,
                    usuario_id=test_user_id,
                    dto=dto_f1,
                    placa_enmascarada="INC-***",
                    placa_hash=hashlib.sha256(dto_f1.placa.encode()).hexdigest(),
                )
            except ValueError as ve:
                incompatible_f1 = True
                print(f"[OK] Bloqueo exitoso F1: {ve}")

            dto_f2 = CrearCasoValidacionDTO(
                fase="Pre-test",  # Fase Pre pero tipo POST
                tipo_registro="THESIS_POSTTEST",
                placa="INC-002",
                marca_modelo="Toyota Yaris",
                sintoma="Falla al arrancar",
                falla_real="Falla en motor de arranque",
                chatbot_prediccion="Falla en motor de arranque",
                campos_completos=1,
                tiempo_diagnostico_minutos=20,
                prediccion_correcta=1,
            )
            incompatible_f2 = False
            try:
                await servicio.crear(
                    taller_id=test_taller_id,
                    usuario_id=test_user_id,
                    dto=dto_f2,
                    placa_enmascarada="INC-***",
                    placa_hash=hashlib.sha256(dto_f2.placa.encode()).hexdigest(),
                )
            except ValueError as ve:
                incompatible_f2 = True
                print(f"[OK] Bloqueo exitoso F2: {ve}")

            assert incompatible_f1 and incompatible_f2, "ERROR: Debió rechazarse la incoherencia de fase/tipo"
            resultados["CASO_F"] = True
            print("[OK] CASO F superado: Combinaciones incompatibles rechazadas estrictamente.")

            # -------------------------------------------------------------
            # CASO G: Omisión de environment (default a DEVELOPMENT)
            # -------------------------------------------------------------
            print("\n--- CASO G: OMISIÓN DE ENTORNO (DEFAULT A DEVELOPMENT) ---")
            dto_g = CrearCasoValidacionDTO(
                fase="Pre-test",
                placa="DEV-001",
                marca_modelo="Hyundai Accent",
                sintoma="Luz de check encendida en tablero",
                falla_real="Falla en sensor de oxigeno o mezcla rica",
                chatbot_prediccion="Sensor de oxigeno",
                campos_completos=1,
                tiempo_diagnostico_minutos=20,
                prediccion_correcta=1,
                tipo_registro=None,  # Omisión deliberada
            )
            caso_g = await servicio.crear(
                taller_id=test_taller_id,
                usuario_id=test_user_id,
                dto=dto_g,
                placa_enmascarada="DEV-***",
                placa_hash=hashlib.sha256(dto_g.placa.encode()).hexdigest(),
            )
            ids_creados.append(caso_g.id)
            await session.commit()

            assert caso_g.tipo_registro == "DEVELOPMENT", f"ERROR: Se esperaba DEVELOPMENT pero se obtuvo {caso_g.tipo_registro}"
            assert caso_g.tipo_registro not in ("THESIS_PRETEST", "THESIS_POSTTEST")
            resultados["CASO_G"] = True
            print("[OK] CASO G superado: Registro sin entorno especificado quedó blindado como DEVELOPMENT.")

        finally:
            # -------------------------------------------------------------
            # LIMPIEZA TOTAL (TEARDOWN)
            # -------------------------------------------------------------
            print("\n--- TEARDOWN: LIMPIEZA DE CASOS DE SIMULACIÓN ---")
            await session.rollback()
            if ids_creados:
                stmt_del = delete(ValidacionTaller).where(ValidacionTaller.id.in_(ids_creados))
                await session.execute(stmt_del)
                await session.commit()
                print(f"Eliminados {len(ids_creados)} registros temporales de simulación.")

            if diag_test_id:
                stmt_del_diag = delete(Diagnostico).where(Diagnostico.id == diag_test_id)
                await session.execute(stmt_del_diag)
                await session.commit()
                print("Diagnóstico de prueba eliminado.")

            # Comprobar contadores post-limpieza
            stmt_pre_fin = select(func.count()).where(
                ValidacionTaller.tipo_registro == "THESIS_PRETEST",
                ValidacionTaller.estado_registro == "verificado",
            )
            pre_fin = (await session.execute(stmt_pre_fin)).scalar_one()

            stmt_post_fin = select(func.count()).where(
                ValidacionTaller.tipo_registro == "THESIS_POSTTEST",
                ValidacionTaller.estado_registro == "verificado",
            )
            post_fin = (await session.execute(stmt_post_fin)).scalar_one()

            print(f"Pre-test oficial final: {pre_fin}/30")
            print(f"Post-test oficial final: {post_fin}/30")
            print(f"Total oficial final: {pre_fin + post_fin}/60")
            assert pre_fin == 0 and post_fin == 0, "ERROR: Contadores oficiales afectados tras limpieza!"

    print("\n=======================================================")
    print("RESUMEN DE RESULTADOS DE LA SIMULACIÓN PRE-CAMPO (A-G):")
    for k, v in resultados.items():
        print(f"  {k}: {'APROBADO' if v else 'FALLIDO'}")
    print("=======================================================")
    return resultados


if __name__ == "__main__":
    res = asyncio.run(ejecutar_simulacion())
    all_passed = all(res.values()) and len(res) == 7
    sys.exit(0 if all_passed else 1)
