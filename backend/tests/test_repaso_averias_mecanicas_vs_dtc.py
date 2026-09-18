"""Pruebas rigurosas de la regla de tesis sobre averías mecánicas puras sin control electrónico vs escáner DTC."""

from __future__ import annotations

from src.core.gemini_queue.models import SolicitudGeminiEncolada
from src.core.gemini_queue.summary_formatter import crear_resumen_whatsapp
from src.core.taxonomy.directrices_mecanicas import DIRECTRICES_MECANICAS


def test_invariante_directrices_mecanicas_puras_sin_escaner():
    """
    Toda directriz con es_mecanica_pura=True debe cumplir:
    1. requiere_escaner == False
    2. La prueba sugerida no debe requerir escaneo de códigos de falla.
    """
    mecanicas_puras = [d for d in DIRECTRICES_MECANICAS if d.es_mecanica_pura]
    assert len(mecanicas_puras) >= 5, "Debe haber al menos 5 averías mecánicas puras catalogadas"

    for directriz in mecanicas_puras:
        assert directriz.requiere_escaner is False, f"{directriz.falla} no debe requerir escáner"

        prueba_l = directriz.prueba_sugerida.lower()
        palabras_prohibidas = ["escáner", "escaner", "escanear dtc", "código de error", "código de falla"]
        for prohibida in palabras_prohibidas:
            assert prohibida not in prueba_l, (
                f"Directriz mecánica pura '{directriz.falla}' sugiere '{prohibida}' en: {directriz.prueba_sugerida}"
            )


def test_alabeo_discos_exige_reloj_comparador():
    directriz = next((d for d in DIRECTRICES_MECANICAS if "alabeados" in d.falla.lower()), None)
    assert directriz is not None
    assert directriz.es_mecanica_pura is True
    assert "reloj comparador" in directriz.prueba_sugerida.lower()
    assert "0.05 mm" in directriz.prueba_sugerida


def test_desgaste_pastillas_exige_medicion_fisica():
    directriz = next((d for d in DIRECTRICES_MECANICAS if "pastillas" in d.falla.lower()), None)
    assert directriz is not None
    assert directriz.es_mecanica_pura is True
    assert "espesor" in directriz.prueba_sugerida.lower()
    assert "3 mm" in directriz.prueba_sugerida


def test_fuga_hidraulica_frenos_prueba_estatica_pedal():
    directriz = next((d for d in DIRECTRICES_MECANICAS if "fuga hidraulica" in d.falla.lower()), None)
    assert directriz is not None
    assert directriz.es_mecanica_pura is True
    assert "retención estática del pedal" in directriz.prueba_sugerida.lower() or "retencion" in directriz.prueba_sugerida.lower()


def test_resumen_whatsapp_alabeo_discos_sugiere_reloj_comparador_no_dtc():
    solicitud = SolicitudGeminiEncolada(
        sintoma="El pedal y el timón vibran fuerte cuando piso el freno bajando a 80 km/h",
        diagnostico_ml="Discos de freno alabeados o desgastados",
        confianza_ml=0.88,
        contexto_manual="Manual de frenos: tolerancia máx 0.05 mm",
        titulo_manual="Manual Frenos OEM",
    )
    resumen = crear_resumen_whatsapp(solicitud, "Texto LLM")

    assert "reloj comparador" in resumen.lower()
    assert "escáner obd-ii" not in resumen.lower()
    assert "escanear dtc" not in resumen.lower()
    assert "runout" in resumen.lower() or "alabeo" in resumen.lower()


def test_resumen_whatsapp_desbalanceo_sugiere_balanceo_no_dtc():
    solicitud = SolicitudGeminiEncolada(
        sintoma="El carro tiembla en autopista a 90 sin pisar el pedal de freno",
        diagnostico_ml="Llantas desbalanceadas o desalineadas",
        confianza_ml=0.85,
        contexto_manual="Manual de tren delantero y geometría de suspensión",
        titulo_manual="Manual Chasis OEM",
    )
    resumen = crear_resumen_whatsapp(solicitud, "Texto LLM")

    assert "balanceo dinámico" in resumen.lower() or "balanceo dinamico" in resumen.lower()
    assert "alineación" in resumen.lower() or "alineacion" in resumen.lower()
    assert "escáner obd-ii" not in resumen.lower()


def test_resumen_whatsapp_pastillas_sugiere_inspeccion_espesor():
    solicitud = SolicitudGeminiEncolada(
        sintoma="Chirrido agudo constante al presionar el freno",
        diagnostico_ml="Desgaste de pastillas y zapatas de freno",
        confianza_ml=0.82,
        contexto_manual="Inspección de desgaste de material de fricción",
        titulo_manual="Manual Frenos OEM",
    )
    resumen = crear_resumen_whatsapp(solicitud, "Texto LLM")

    assert "inspección visual del espesor" in resumen.lower() or "espesor de pastillas" in resumen.lower()
    assert "escáner obd-ii" not in resumen.lower()


def test_resumen_whatsapp_falla_electronica_si_sugiere_escaner_y_dtc():
    solicitud = SolicitudGeminiEncolada(
        sintoma="Jalonea al acelerar, parpadea luz check engine con código P0301",
        diagnostico_ml="Falla en bujias o bobinas de encendido (misfire)",
        confianza_ml=0.90,
        contexto_manual="Procedimiento de encendido y códigos P0300-P0304",
        titulo_manual="Manual Encendido OEM",
    )
    resumen = crear_resumen_whatsapp(solicitud, "Texto LLM")

    assert "obd" in resumen.lower() or "dtc" in resumen.lower() or "bobina" in resumen.lower()
    assert "p0301" in resumen.lower() or "chispa" in resumen.lower()
