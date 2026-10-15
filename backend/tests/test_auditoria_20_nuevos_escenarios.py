"""Pruebas de los 20 nuevos escenarios de auditoría conversacional (ESC-33 a ESC-52).

Evalúa condiciones complejas de taller: descarte múltiple, compresión dispar,
alternador en marcha, fugas de vacío, jerga peruana y sanitización.
"""

import asyncio
import os

PROYECTO_ROOT = r"c:\Users\leonc\OneDrive\Desktop\CHAT_BOT_MACHINLEARNING"
os.environ["DATABASE_ENABLED"] = "false"
os.environ["ML_ROOT"] = os.path.join(PROYECTO_ROOT, "machine_learning")

from src.core.conversacion.orquestador_conversacion import OrquestadorConversacion  # noqa: E402
from src.core.conversacion.repositorio import InMemoryConversationRepository  # noqa: E402
from src.core.gestor_diagnostico import GestorDiagnostico  # noqa: E402


def _crear_entorno():
    repo = InMemoryConversationRepository()
    return OrquestadorConversacion(repositorio=repo), GestorDiagnostico()


def test_esc33_cascabeleo_gasohol_bajo_octanaje():
    """ESC-33: Cascabeleo / pistoneo en subida con combustible de bajo octanaje."""
    async def _run():
        orq, gestor = _crear_entorno()
        ses_id = "test_esc33"
        res = await orq.procesar_turno(
            ses_id,
            "Cascabelea y pistonea feo en subida con gasohol 90 en un Toyota Yaris 2017",
            gestor,
        )
        est = await orq.repositorio.get_session(ses_id)
        assert est.marca == "Toyota"
        assert (
            "cascabeleo" in str(est.hechos).lower()
            or "misfire" in str(est.hechos).lower()
            or "carga" in str(est.hechos).lower()
        )
        assert "freno" not in res["respuesta_texto"].lower()
    asyncio.run(_run())


def test_esc34_humo_azulado_desaceleracion():
    """ESC-34: Humo azulado en desaceleración (retenes de válvula)."""
    async def _run():
        orq, gestor = _crear_entorno()
        ses_id = "test_esc34"
        res = await orq.procesar_turno(
            ses_id,
            "Bota humo azul por el escape al desacelerar o retener en bajada en un Toyota Hilux 2015",
            gestor,
        )
        est = await orq.repositorio.get_session(ses_id)
        assert est.marca == "Toyota"
        assert any("humo" in k.lower() or "aceite" in k.lower() for k in est.hechos.keys())
        assert res["status"] in ("completado", "ok")
    asyncio.run(_run())


def test_esc35_desambiguacion_chicote_embrague():
    """ESC-35: Desambiguación de chicote de embrague vs cable de encendido."""
    async def _run():
        orq, gestor = _crear_entorno()
        ses_id = "test_esc35"
        res = await orq.procesar_turno(
            ses_id,
            "Se rompió el chicote y el pedal quedó en el fondo en un Nissan Tiida mecánico",
            gestor,
        )
        est = await orq.repositorio.get_session(ses_id)
        assert est.marca == "Nissan"
        assert "dtc" not in res["respuesta_texto"].lower()
        assert "embrague" in res["respuesta_texto"].lower() or any(
            "embrague" in h["falla"].lower() for h in (est.top3_actual or [])
        )
    asyncio.run(_run())


def test_esc36_falla_intermitente_trafico_pesado():
    """ESC-36: Falla térmica retardada que surge solo tras 45 minutos de tráfico."""
    async def _run():
        orq, gestor = _crear_entorno()
        ses_id = "test_esc36"
        await orq.procesar_turno(ses_id, "El motor funciona sedita al inicio en un Kia Rio 2016", gestor)
        res2 = await orq.procesar_turno(
            ses_id,
            "Pero tras 45 minutos en tráfico trancado empieza a tironear y calentar",
            gestor,
        )
        est = await orq.repositorio.get_session(ses_id)
        assert est.marca == "Kia"
        assert any("caliente" in str(v.valor).lower() or "temp" in k.lower() for k, v in est.hechos.items())
        assert res2["status"] == "completado"
    asyncio.run(_run())


def test_esc37_alternador_baja_tension_en_marcha():
    """ESC-37: Alternador no carga (11.8V en marcha con luces altas)."""
    async def _run():
        orq, gestor = _crear_entorno()
        ses_id = "test_esc37"
        await orq.procesar_turno(
            ses_id,
            "El carro se apaga andando y prende el testigo de batería en un Hyundai Accent 2014",
            gestor,
        )
        res2 = await orq.procesar_turno(
            ses_id,
            "Medí con multímetro y con motor prendido y luces altas marca 11.8 V",
            gestor,
        )
        est = await orq.repositorio.get_session(ses_id)
        assert "11.8" in res2["respuesta_texto"] or "alternador" in res2["respuesta_texto"].lower() or any(
            "alternador" in h["falla"].lower() or "carga" in h["falla"].lower() for h in (est.top3_actual or [])
        )
    asyncio.run(_run())


def test_esc38_desconexion_maf_empareja():
    """ESC-38: Desconexión voluntaria del sensor MAF para comprobar síntoma."""
    async def _run():
        orq, gestor = _crear_entorno()
        ses_id = "test_esc38"
        await orq.procesar_turno(ses_id, "Tironeaba y fallaba en ralentí en un Nissan Sentra 2013", gestor)
        res2 = await orq.procesar_turno(
            ses_id,
            "Desconecté la ficha del sensor MAF y el motor emparejó al toque",
            gestor,
        )
        est = await orq.repositorio.get_session(ses_id)
        assert est.marca == "Nissan"
        assert any("maf" in k.lower() or "admision" in k.lower() or "inyeccion" in k.lower() for k in est.hechos.keys())
        assert res2["status"] == "completado"
    asyncio.run(_run())


def test_esc39_modo_degradado_estructurado():
    """ESC-39: Modo degradado determinista ante caída o indisponibilidad de LLM."""
    async def _run():
        orq, gestor = _crear_entorno()
        ses_id = "test_esc39"
        res = await orq.procesar_turno(
            ses_id,
            "Tengo un Toyota Corolla 2012 que recalienta en subida y bota agua",
            gestor,
        )
        assert res["status"] in ("completado", "ok")
        assert (
            "refriger" in res["respuesta_texto"].lower()
            or "temperatura" in res["respuesta_texto"].lower()
            or "termostato" in res["respuesta_texto"].lower()
        )
    asyncio.run(_run())


def test_esc40_correccion_transmision_manual():
    """ESC-40: Corrección de transmisión en segundo turno."""
    async def _run():
        orq, gestor = _crear_entorno()
        ses_id = "test_esc40"
        await orq.procesar_turno(ses_id, "El carro patina y vibra al acelerar en un Honda Civic 2015", gestor)
        res2 = await orq.procesar_turno(
            ses_id,
            "Por si acaso es transmisión mecánica manual de 5 velocidades",
            gestor,
        )
        est = await orq.repositorio.get_session(ses_id)
        assert est.marca == "Honda"
        hecho_trans = est.obtener_hecho("transmision") or est.obtener_hecho("caja")
        assert hecho_trans is not None and "MANUAL" in str(hecho_trans.valor).upper()
        assert res2["status"] == "completado"
    asyncio.run(_run())


def test_esc41_extraccion_placa_sin_guion():
    """ESC-41: Extracción y normalización de placa peruana sin guión (ABC123)."""
    async def _run():
        orq, gestor = _crear_entorno()
        ses_id = "test_esc41"
        await orq.procesar_turno(
            ses_id,
            "El carro tironea en un Kia Cerato 2015 con placa B4K123",
            gestor,
        )
        est = await orq.repositorio.get_session(ses_id)
        assert est.placa in ("B4K-123", "B4K123")
        assert est.marca == "Kia"
    asyncio.run(_run())


def test_esc42_compresion_desbalanceada():
    """ESC-42: Medición instrumental de compresión con cilindro bajo (65 PSI)."""
    async def _run():
        orq, gestor = _crear_entorno()
        ses_id = "test_esc42"
        await orq.procesar_turno(ses_id, "Falla un cilindro y tiembla en ralentí en un Toyota Yaris 2011", gestor)
        res2 = await orq.procesar_turno(
            ses_id,
            "Medí compresión: cil 1: 160 psi, cil 2: 65 psi, cil 3: 160 psi, cil 4: 155 psi con compresímetro",
            gestor,
        )
        est = await orq.repositorio.get_session(ses_id)
        assert any("compres" in k.lower() or "psi" in str(v.valor).lower() for k, v in est.hechos.items())
        assert res2["status"] == "completado"
    asyncio.run(_run())


def test_esc43_descarte_multiple_componentes():
    """ESC-43: Descarte conjunto de bujías, bobinas y bomba con repuestos nuevos."""
    async def _run():
        orq, gestor = _crear_entorno()
        ses_id = "test_esc43"
        await orq.procesar_turno(ses_id, "Tiembla en mínimo y tironea en un Suzuki Swift 2015", gestor)
        res2 = await orq.procesar_turno(
            ses_id,
            "Ya cambié bujías, bobinas y bomba nuevas originales y sigue igual la falla",
            gestor,
        )
        est = await orq.repositorio.get_session(ses_id)
        assert len(est.hipotesis_descartadas) >= 2 or any("reemplazado" in k for k in est.hechos)
        assert res2["status"] == "completado"
    asyncio.run(_run())


def test_esc44_fuga_vacio_admision_acelerado():
    """ESC-44: Fuga de vacío en múltiple con ralentí acelerado (1500 RPM)."""
    async def _run():
        orq, gestor = _crear_entorno()
        ses_id = "test_esc44"
        res = await orq.procesar_turno(
            ses_id,
            "El motor queda acelerado a 1500 RPM y se escucha chupar aire en el múltiple de admisión en un Chevrolet Sail",
            gestor,
        )
        est = await orq.repositorio.get_session(ses_id)
        assert est.marca == "Chevrolet"
        assert any("admision" in k.lower() or "ralenti" in k.lower() or "aire" in k.lower() or "vacio" in k.lower() for k in est.hechos.keys())
        assert res["status"] in ("completado", "ok")
    asyncio.run(_run())


def test_esc45_rodamiento_rueda_asimetrico():
    """ESC-45: Ruido de rodamiento que varía según el apoyo dinámico en curva."""
    async def _run():
        orq, gestor = _crear_entorno()
        ses_id = "test_esc45"
        await orq.procesar_turno(ses_id, "Zumba como avión a partir de 60 km/h en un Nissan Versa 2016", gestor)
        res2 = await orq.procesar_turno(
            ses_id,
            "Al doblar a la derecha zumba más fuerte y al doblar a la izquierda se calla",
            gestor,
        )
        est = await orq.repositorio.get_session(ses_id)
        assert "dtc" not in res2["respuesta_texto"].lower()
        assert "rodamiento" in res2["respuesta_texto"].lower() or any(
            "rodamiento" in h["falla"].lower() or "rueda" in h["falla"].lower() for h in (est.top3_actual or [])
        )
    asyncio.run(_run())


def test_esc46_sin_chispa_bomba_activa():
    """ESC-46: Prueba de chispa negativa con alimentación de combustible verificada."""
    async def _run():
        orq, gestor = _crear_entorno()
        ses_id = "test_esc46"
        await orq.procesar_turno(ses_id, "El motor gira pero no enciende en un Toyota Corolla 2008", gestor)
        res2 = await orq.procesar_turno(
            ses_id,
            "La bomba de gasolina sí zumba y manda presión pero no salta chispa en ninguna bujía",
            gestor,
        )
        est = await orq.repositorio.get_session(ses_id)
        assert est.marca == "Toyota"
        assert res2["status"] == "completado"
    asyncio.run(_run())


def test_esc47_ahogo_olor_gasolina_cruda():
    """ESC-47: Ahogo y olor penetrante a combustible crudo en arranque en frío."""
    async def _run():
        orq, gestor = _crear_entorno()
        ses_id = "test_esc47"
        res = await orq.procesar_turno(
            ses_id,
            "El carro se ahoga feo y bota harta baranda a gasolina cruda al prender en frío en un Hyundai Tucson",
            gestor,
        )
        est = await orq.repositorio.get_session(ses_id)
        assert est.marca == "Hyundai"
        assert any("combustible" in k.lower() or "frio" in str(v.valor).lower() or "humo" in k.lower() for k, v in est.hechos.items())
        assert res["status"] in ("completado", "ok")
    asyncio.run(_run())


def test_esc48_sobrecalentamiento_sin_ventilador():
    """ESC-48: Temperatura al máximo con electroventilador inoperativo (Seguridad)."""
    async def _run():
        orq, gestor = _crear_entorno()
        ses_id = "test_esc48"
        res = await orq.procesar_turno(
            ses_id,
            "La aguja de temperatura está en la H roja al tope y el ventilador no arranca en un Kia Rio 2015",
            gestor,
        )
        est = await orq.repositorio.get_session(ses_id)
        assert any("sobrecalentamiento" in k.lower() or "temperatura" in k.lower() for k in est.hechos.keys())
        assert (
            "seguridad" in res["respuesta_texto"].lower()
            or "apague" in res["respuesta_texto"].lower()
            or "detenga" in res["respuesta_texto"].lower()
            or "ventilador" in res["respuesta_texto"].lower()
        )
    asyncio.run(_run())


def test_esc49_respuesta_adverbio_temporal():
    """ESC-49: Respuesta cortísima temporal ('recién ayer empezó')."""
    async def _run():
        orq, gestor = _crear_entorno()
        ses_id = "test_esc49"
        await orq.procesar_turno(ses_id, "No arranca y hace tac tac en un Toyota Yaris 2016", gestor)
        res2 = await orq.procesar_turno(ses_id, "Recién ayer empezó la falla maestro", gestor)
        est = await orq.repositorio.get_session(ses_id)
        assert est.marca == "Toyota"
        assert res2["status"] == "completado"
    asyncio.run(_run())


def test_esc50_correccion_placa_vehicular():
    """ESC-50: Corrección de placa vehicular errónea."""
    async def _run():
        orq, gestor = _crear_entorno()
        ses_id = "test_esc50"
        await orq.procesar_turno(ses_id, "Nissan Sentra 2014 con placa A1B-222 que tironea", gestor)
        await orq.procesar_turno(ses_id, "Disculpa me equivoqué de placa, la correcta es F4K-888", gestor)
        est = await orq.repositorio.get_session(ses_id)
        assert est.placa == "F4K-888"
        assert est.marca == "Nissan"
    asyncio.run(_run())


def test_esc51_resistencia_inyeccion_sql():
    """ESC-51: Contención de intento de inyección SQL."""
    async def _run():
        orq, gestor = _crear_entorno()
        ses_id = "test_esc51"
        res = await orq.procesar_turno(
            ses_id,
            "Tengo un Ford Fiesta con placa ABC-123'; DROP TABLE vehiculos;-- no arranca",
            gestor,
        )
        est = await orq.repositorio.get_session(ses_id)
        assert "DROP TABLE" not in (est.placa or "")
        assert res["status"] in ("completado", "ok")
    asyncio.run(_run())


def test_esc52_consulta_especificaciones_rag():
    """ESC-52: Solicitud de procedimiento de calibración técnica sin síntoma."""
    async def _run():
        orq, gestor = _crear_entorno()
        ses_id = "test_esc52"
        res = await orq.procesar_turno(
            ses_id,
            "¿Cuál es el procedimiento de calibración y reaprendizaje de marcha mínima en cuerpo de aceleración electrónico?",
            gestor,
        )
        assert res["decision"] in ("DETALLE", "DIAGNOSTICAR") or res["status"] == "consulta_tecnica"
        assert (
            "calibración" in res["respuesta_texto"].lower()
            or "calibracion" in res["respuesta_texto"].lower()
            or "reaprendizaje" in res["respuesta_texto"].lower()
            or "aceleración" in res["respuesta_texto"].lower()
            or "aceleracion" in res["respuesta_texto"].lower()
            or "cuerpo" in res["respuesta_texto"].lower()
        )
    asyncio.run(_run())
