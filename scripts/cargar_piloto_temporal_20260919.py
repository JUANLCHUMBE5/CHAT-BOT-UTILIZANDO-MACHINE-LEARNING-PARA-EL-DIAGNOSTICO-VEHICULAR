"""Carga temporal y segura de 20 casos piloto (10 PRE y 10 POST) para Fase 11.5.3.

Lote: PILOTO_TEMPORAL_20260919
"""

import asyncio
import hashlib
import sys
import uuid
from datetime import date
from pathlib import Path

# Setup sys.path
ROOT = Path(__file__).resolve().parent.parent
BACKEND = ROOT / "backend"
if str(BACKEND) not in sys.path:
    sys.path.insert(0, str(BACKEND))

from src.infrastructure.database.connection import obtener_engine
from src.infrastructure.database.models.validation import ValidacionTaller
from src.application.services.validacion_taller import (
    calcular_detalles_campos_ficha2,
    construir_datos_generales_vehiculo,
)

TALLER_ID = uuid.UUID("5313362a-c18d-456f-892d-a8980155c461")
MECANICO_ID = uuid.UUID("aac65a05-9624-4d9b-b6ee-35275c25011c")
LOTE_TAG = "PILOTO_TEMPORAL_20260919"
ORIGEN_TAG = "PILOTO_PROVISIONAL_CLASE"

CASOS_PRE = [
    {
        "idx": 1,
        "marca_modelo": "Toyota Yaris",
        "anio": 2018,
        "km": 85000,
        "comb": "Gasolina",
        "trans": "Mecánica",
        "sintoma": "Motor tiembla en mínimo y aguja de RPM oscila.",
        "desc_sintoma": "Al detenerse en semáforos, el motor pierde estabilidad y vibra; en alta marcha se normaliza.",
        "sistema": "MOTOR",
        "falla_real": "Cuerpo de aceleracion o valvula IAC sucia",
        "pred": "Cuerpo de aceleracion o valvula IAC sucia",
        "correcta": 1,
        "tiempo": 42,
    },
    {
        "idx": 2,
        "marca_modelo": "Hyundai Accent",
        "anio": 2017,
        "km": 110000,
        "comb": "Gasolina",
        "trans": "Mecánica",
        "sintoma": "Chirriador o chillido agudo al frenar.",
        "desc_sintoma": "Sonido metálico al pisar el pedal de freno a baja y media velocidad.",
        "sistema": "FRENOS",
        "falla_real": "Desgaste de pastillas y zapatas de freno",
        "pred": "Discos de freno alabeados o desgastados",
        "correcta": 0,
        "tiempo": 35,
    },
    {
        "idx": 3,
        "marca_modelo": "Nissan Versa",
        "anio": 2019,
        "km": 72000,
        "comb": "Gasolina",
        "trans": None,  # Incompleto en datos de vehículo
        "sintoma": "Demora en encender en frío por las mañanas.",
        "desc_sintoma": "Gira el arrancador varias veces antes de arrancar.",
        "sistema": "ELECTRICO",
        "falla_real": "Bateria descargada o bornes sulfatados",
        "pred": "Bateria descargada o bornes sulfatados",
        "correcta": 1,
        "tiempo": 48,
    },
    {
        "idx": 4,
        "marca_modelo": "Kia Rio",
        "anio": 2016,
        "km": 125000,
        "comb": "Gasolina",
        "trans": "Mecánica",
        "sintoma": "Pedal de embrague duro y cambios raspan al entrar.",
        "desc_sintoma": "Dificultad para engranar primera y retroceso con motor encendido.",
        "sistema": "TRANSMISION",
        "falla_real": "Falla en bombin o bomba hidraulica de embrague",
        "pred": "Disco de embrague desgastado o patinando",
        "correcta": 0,
        "tiempo": 31,
    },
    {
        "idx": 5,
        "marca_modelo": "Chevrolet Sail",
        "anio": 2018,
        "km": None,  # Incompleto
        "comb": None,  # Incompleto
        "trans": "Mecánica",
        "sintoma": "Temperatura sube a zona roja en subidas.",
        "desc_sintoma": "El depósito de refrigerante hierve tras 20 minutos de marcha continua.",
        "sistema": "MOTOR",
        "falla_real": "Falla en termostato o motoventilador de radiador",
        "pred": "Falla en termostato o motoventilador de radiador",
        "correcta": 1,
        "tiempo": 39,
    },
    {
        "idx": 6,
        "marca_modelo": "Toyota Corolla",
        "anio": 2015,
        "km": 140000,
        "comb": "Gasolina",
        "trans": "Automática",
        "sintoma": "Tirones y cabeceo al acelerar con fuerza en carretera.",
        "desc_sintoma": "Jalonea entre 2000 y 3000 RPM en tercera marcha.",
        "sistema": "MOTOR",
        "falla_real": "Falla en bujias o bobinas de encendido (misfire)",
        "pred": "Falla en bujias o bobinas de encendido (misfire)",
        "correcta": 1,
        "tiempo": 44,
    },
    {
        "idx": 7,
        "marca_modelo": "Suzuki Swift",
        "anio": 2019,
        "km": 65000,
        "comb": "Gasolina",
        "trans": "Mecánica",
        "sintoma": "Volante vibra fuertemente solo al pisar el pedal de freno.",
        "desc_sintoma": "Vibración notoria en el timón a más de 70 km/h al frenar.",
        "sistema": "FRENOS",
        "falla_real": "Discos de freno alabeados o desgastados",
        "pred": "Llantas desbalanceadas o desalineadas",
        "correcta": 0,
        "tiempo": 36,
    },
    {
        "idx": 8,
        "marca_modelo": "Nissan Sentra",
        "anio": 2017,
        "km": 98000,
        "comb": "Gasolina",
        "trans": "Mecánica",
        "sintoma": "Luz de batería encendida en tablero y faros tenues.",
        "desc_sintoma": None,  # Incompleto en descripción
        "sistema": "ELECTRICO",
        "falla_real": "Alternador defectuoso o placa de diodos quemada",
        "pred": "Alternador defectuoso o placa de diodos quemada",
        "correcta": 1,
        "tiempo": 51,
    },
    {
        "idx": 9,
        "marca_modelo": "Hyundai i10",
        "anio": 2018,
        "km": 82000,
        "comb": "GNV",
        "trans": "Mecánica",
        "sintoma": "Pérdida de potencia y olor a combustible crudo.",
        "desc_sintoma": "Motor sin fuerza en pendientes pronunciadas.",
        "sistema": "MOTOR",
        "falla_real": "Inyectores sucios o filtro de combustible obstruido",
        "pred": "Bomba de gasolina quemada o con baja presion",
        "correcta": 0,
        "tiempo": 34,
    },
    {
        "idx": 10,
        "marca_modelo": "Kia Cerato",
        "anio": None,  # Incompleto
        "km": None,  # Incompleto
        "comb": None,  # Incompleto
        "trans": None,  # Incompleto
        "sintoma": "Golpeteo seco 'cloc' al pasar por baches en la parte delantera.",
        "desc_sintoma": "pendiente",  # No válido
        "sistema": "SUSPENSION_CHASIS",
        "falla_real": "Bieletas de la barra estabilizadora desgastadas",
        "pred": "Bieletas de la barra estabilizadora desgastadas",
        "correcta": 1,
        "tiempo": 40,
    },
]

CASOS_POST = [
    {
        "idx": 1,
        "marca_modelo": "Toyota Yaris",
        "anio": 2018,
        "km": 85000,
        "comb": "Gasolina",
        "trans": "Mecánica",
        "sintoma": "Motor tiembla en mínimo y aguja de RPM oscila.",
        "desc_sintoma": "Al detenerse en semáforos, el motor pierde estabilidad y vibra; en alta marcha se normaliza.",
        "sistema": "MOTOR",
        "falla_real": "Cuerpo de aceleracion o valvula IAC sucia",
        "pred": "Cuerpo de aceleracion o valvula IAC sucia",
        "correcta": 1,
        "tiempo": 19,
    },
    {
        "idx": 2,
        "marca_modelo": "Hyundai Accent",
        "anio": 2017,
        "km": 110000,
        "comb": "Gasolina",
        "trans": "Mecánica",
        "sintoma": "Chirriador o chillido agudo al frenar.",
        "desc_sintoma": "Sonido metálico al pisar el pedal de freno a baja y media velocidad.",
        "sistema": "FRENOS",
        "falla_real": "Desgaste de pastillas y zapatas de freno",
        "pred": "Desgaste de pastillas y zapatas de freno",
        "correcta": 1,
        "tiempo": 17,
    },
    {
        "idx": 3,
        "marca_modelo": "Nissan Versa",
        "anio": 2019,
        "km": 72000,
        "comb": "Gasolina",
        "trans": "Mecánica",
        "sintoma": "Demora en encender en frío por las mañanas.",
        "desc_sintoma": "Gira el arrancador varias veces antes de arrancar.",
        "sistema": "ELECTRICO",
        "falla_real": "Bateria descargada o bornes sulfatados",
        "pred": "Bateria descargada o bornes sulfatados",
        "correcta": 1,
        "tiempo": 22,
    },
    {
        "idx": 4,
        "marca_modelo": "Kia Rio",
        "anio": 2016,
        "km": 125000,
        "comb": "Gasolina",
        "trans": "Mecánica",
        "sintoma": "Pedal de embrague duro y cambios raspan al entrar.",
        "desc_sintoma": "Dificultad para engranar primera y retroceso con motor encendido.",
        "sistema": "TRANSMISION",
        "falla_real": "Falla en bombin o bomba hidraulica de embrague",
        "pred": "Disco de embrague desgastado o patinando",
        "correcta": 0,
        "tiempo": 16,
    },
    {
        "idx": 5,
        "marca_modelo": "Chevrolet Sail",
        "anio": 2018,
        "km": 95000,
        "comb": "Gasolina",
        "trans": "Mecánica",
        "sintoma": "Temperatura sube a zona roja en subidas.",
        "desc_sintoma": "El depósito de refrigerante hierve tras 20 minutos de marcha continua.",
        "sistema": "MOTOR",
        "falla_real": "Falla en termostato o motoventilador de radiador",
        "pred": "Falla en termostato o motoventilador de radiador",
        "correcta": 1,
        "tiempo": 18,
    },
    {
        "idx": 6,
        "marca_modelo": "Toyota Corolla",
        "anio": 2015,
        "km": 140000,
        "comb": "Gasolina",
        "trans": "Automática",
        "sintoma": "Tirones y cabeceo al acelerar con fuerza en carretera.",
        "desc_sintoma": "Jalonea entre 2000 y 3000 RPM en tercera marcha.",
        "sistema": "MOTOR",
        "falla_real": "Falla en bujias o bobinas de encendido (misfire)",
        "pred": "Falla en bujias o bobinas de encendido (misfire)",
        "correcta": 1,
        "tiempo": 20,
    },
    {
        "idx": 7,
        "marca_modelo": "Suzuki Swift",
        "anio": 2019,
        "km": 65000,
        "comb": None,  # Incompleto en combustible
        "trans": "Mecánica",
        "sintoma": "Volante vibra fuertemente solo al pisar el pedal de freno.",
        "desc_sintoma": "Vibración notoria en el timón a más de 70 km/h al frenar.",
        "sistema": "FRENOS",
        "falla_real": "Discos de freno alabeados o desgastados",
        "pred": "Discos de freno alabeados o desgastados",
        "correcta": 1,
        "tiempo": 21,
    },
    {
        "idx": 8,
        "marca_modelo": "Nissan Sentra",
        "anio": 2017,
        "km": 98000,
        "comb": "Gasolina",
        "trans": "Mecánica",
        "sintoma": "Luz de batería encendida en tablero y faros tenues.",
        "desc_sintoma": "Tensión en bornes cae a 11.8 V con motor encendido y luces altas.",
        "sistema": "ELECTRICO",
        "falla_real": "Alternador defectuoso o placa de diodos quemada",
        "pred": "Alternador defectuoso o placa de diodos quemada",
        "correcta": 1,
        "tiempo": 15,
    },
    {
        "idx": 9,
        "marca_modelo": "Hyundai i10",
        "anio": 2018,
        "km": 82000,
        "comb": "GNV",
        "trans": "Mecánica",
        "sintoma": "Pérdida de potencia y olor a combustible crudo.",
        "desc_sintoma": "Motor sin fuerza en pendientes pronunciadas.",
        "sistema": "MOTOR",
        "falla_real": "Inyectores sucios o filtro de combustible obstruido",
        "pred": "Bomba de gasolina quemada o con baja presion",
        "correcta": 0,
        "tiempo": 23,
    },
    {
        "idx": 10,
        "marca_modelo": "Kia Cerato",
        "anio": 2016,
        "km": 91000,
        "comb": "Gasolina",
        "trans": "Mecánica",
        "sintoma": "Golpeteo seco 'cloc' al pasar por baches en la parte delantera.",
        "desc_sintoma": "Ruido metálico en tren delantero al circular sobre adoquinado.",
        "sistema": "SUSPENSION_CHASIS",
        "falla_real": "Bieletas de la barra estabilizadora desgastadas",
        "pred": "Bieletas de la barra estabilizadora desgastadas",
        "correcta": 1,
        "tiempo": 19,
    },
]


async def cargar_lote():
    engine = obtener_engine()
    fecha_hoy = date(2026, 9, 19)

    registros_a_insertar = []

    # 1. Preparar 10 PRE
    for c in CASOS_PRE:
        idx = c["idx"]
        codigo_caso = f"PILOTO-PRE-{idx:03d}"
        origen_clave = f"{LOTE_TAG}_PRE_{idx:03d}"
        placa_mask = f"PIL-{idx:03d}"
        placa_hash = hashlib.sha256(f"PILOTO_PRE_{idx}".encode()).hexdigest()

        vehiculo_dict = construir_datos_generales_vehiculo(
            marca_modelo=c["marca_modelo"],
            anio=c["anio"],
            kilometraje=c["km"],
            combustible=c["comb"],
            transmision=c["trans"],
        )

        es_comp, cant_comp, detalles = calcular_detalles_campos_ficha2(
            codigo_registro=codigo_caso,
            fecha_atencion=fecha_hoy,
            datos_generales_vehiculo=vehiculo_dict,
            sintomas_reportados=c["sintoma"],
            descripcion_sintoma=c["desc_sintoma"],
            sistema_afectado_probable=c["sistema"],
            diagnostico_confirmado=c["falla_real"],
            tiempo_atencion_minutos=c["tiempo"],
        )

        detalles["_metadata"] = {
            "lote": LOTE_TAG,
            "origen": ORIGEN_TAG,
            "es_dato_oficial": False,
            "caso_codigo": codigo_caso,
            "fase_simulada": "PRETEST",
        }

        reg = ValidacionTaller(
            id=uuid.uuid4(),
            origen_clave=origen_clave,
            taller_id=TALLER_ID,
            mecanico_id=MECANICO_ID,
            fase="Pre-test",
            fecha=fecha_hoy,
            placa_enmascarada=placa_mask,
            placa_hash=placa_hash,
            marca_modelo=c["marca_modelo"],
            sintoma=c["sintoma"],
            descripcion_sintoma=c["desc_sintoma"],
            vehiculo_anio=c["anio"],
            vehiculo_kilometraje=c["km"],
            vehiculo_combustible=c["comb"],
            vehiculo_transmision=c["trans"],
            falla_real=c["falla_real"],
            chatbot_prediccion=c["pred"],
            sistema_afectado_probable=c["sistema"],
            campos_completos=es_comp,
            cantidad_campos_completos=cant_comp,
            detalles_campos=detalles,
            tiempo_diagnostico_minutos=c["tiempo"],
            prediccion_correcta=c["correcta"],
            metodo_confirmacion="PILOTO_NO_APLICA | Inspección física simulada para prueba piloto",
            evidencia_ref=f"{LOTE_TAG} | PILOTO_NO_APLICA | {codigo_caso}",
            estado_registro="verificado",
            sintoma_registrado_correctamente=1,
            normalizacion_correcta=1,
            extraccion_correcta=1,
            clasificacion_procesada=1,
            procesamiento_validado=1,
            tiempo_inferencia_ml_ms=25,
            tipo_registro="THESIS_PRETEST",
        )
        registros_a_insertar.append(reg)

    # 2. Preparar 10 POST
    for c in CASOS_POST:
        idx = c["idx"]
        codigo_caso = f"PILOTO-POST-{idx:03d}"
        origen_clave = f"{LOTE_TAG}_POST_{idx:03d}"
        placa_mask = f"PIL-{idx:03d}"
        placa_hash = hashlib.sha256(f"PILOTO_POST_{idx}".encode()).hexdigest()

        vehiculo_dict = construir_datos_generales_vehiculo(
            marca_modelo=c["marca_modelo"],
            anio=c["anio"],
            kilometraje=c["km"],
            combustible=c["comb"],
            transmision=c["trans"],
        )

        es_comp, cant_comp, detalles = calcular_detalles_campos_ficha2(
            codigo_registro=codigo_caso,
            fecha_atencion=fecha_hoy,
            datos_generales_vehiculo=vehiculo_dict,
            sintomas_reportados=c["sintoma"],
            descripcion_sintoma=c["desc_sintoma"],
            sistema_afectado_probable=c["sistema"],
            diagnostico_confirmado=c["falla_real"],
            tiempo_atencion_minutos=c["tiempo"],
        )

        detalles["_metadata"] = {
            "lote": LOTE_TAG,
            "origen": ORIGEN_TAG,
            "es_dato_oficial": False,
            "caso_codigo": codigo_caso,
            "fase_simulada": "POSTTEST",
        }

        reg = ValidacionTaller(
            id=uuid.uuid4(),
            origen_clave=origen_clave,
            taller_id=TALLER_ID,
            mecanico_id=MECANICO_ID,
            fase="Post-test",
            fecha=fecha_hoy,
            placa_enmascarada=placa_mask,
            placa_hash=placa_hash,
            marca_modelo=c["marca_modelo"],
            sintoma=c["sintoma"],
            descripcion_sintoma=c["desc_sintoma"],
            vehiculo_anio=c["anio"],
            vehiculo_kilometraje=c["km"],
            vehiculo_combustible=c["comb"],
            vehiculo_transmision=c["trans"],
            falla_real=c["falla_real"],
            chatbot_prediccion=c["pred"],
            sistema_afectado_probable=c["sistema"],
            campos_completos=es_comp,
            cantidad_campos_completos=cant_comp,
            detalles_campos=detalles,
            tiempo_diagnostico_minutos=c["tiempo"],
            prediccion_correcta=c["correcta"],
            metodo_confirmacion="PILOTO_NO_APLICA | Inspección física simulada para prueba piloto",
            evidencia_ref=f"{LOTE_TAG} | PILOTO_NO_APLICA | {codigo_caso}",
            estado_registro="verificado",
            sintoma_registrado_correctamente=1,
            normalizacion_correcta=1,
            extraccion_correcta=1,
            clasificacion_procesada=1,
            procesamiento_validado=1,
            tiempo_inferencia_ml_ms=22,
            tipo_registro="THESIS_POSTTEST",
        )
        registros_a_insertar.append(reg)

    # Inserción en base de datos
    from sqlalchemy.ext.asyncio import AsyncSession
    from sqlalchemy import select, delete

    async with AsyncSession(engine, expire_on_commit=False) as session:
        async with session.begin():
            stmt_check = select(ValidacionTaller.id).where(
                ValidacionTaller.evidencia_ref.like(f"%{LOTE_TAG}%")
            )
            existentes = (await session.execute(stmt_check)).scalars().all()
            if existentes:
                print(f"Ya existían {len(existentes)} registros del lote {LOTE_TAG}. Limpiando previos...")
                await session.execute(
                    delete(ValidacionTaller).where(ValidacionTaller.evidencia_ref.like(f"%{LOTE_TAG}%"))
                )

            session.add_all(registros_a_insertar)
        print(f"Insertados exitosamente {len(registros_a_insertar)} registros piloto temporal.")

    await engine.dispose()


if __name__ == "__main__":
    asyncio.run(cargar_lote())
