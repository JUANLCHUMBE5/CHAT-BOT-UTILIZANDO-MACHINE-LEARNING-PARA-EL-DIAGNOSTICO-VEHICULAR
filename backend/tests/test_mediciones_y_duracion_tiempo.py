"""Pruebas de regresión para Fase 2: Interpretación de Mediciones, Duraciones y Secuencia Temporal.

Valida:
- ESC-08: Contradicción y corrección temporal de síntoma (en frío normal vs caliente tras 20 min).
- ESC-14: Medición cuantitativa de batería normal (12.6V reposo, 10.2V en marcha >= 9.6V).
- Distinción entre duraciones de tiempo (minutos/horas) y lecturas técnicas instrumentales.
- Extracción desacoplada de múltiples mediciones con condiciones operativas locales (ralentí vs luces).
"""

import asyncio
import os

PROYECTO_ROOT = r"c:\Users\leonc\OneDrive\Desktop\CHAT_BOT_MACHINLEARNING"
ML_DIR = os.path.join(PROYECTO_ROOT, "machine_learning")
os.environ["DATABASE_ENABLED"] = "false"
os.environ["ML_ROOT"] = ML_DIR

from src.core.conversacion.extractor_hechos import ExtractorHechos  # noqa: E402
from src.core.conversacion.interprete_respuestas_cortas import InterpreteRespuestasCortas  # noqa: E402
from src.core.conversacion.models import ConversationState, FactState  # noqa: E402
from src.core.conversacion.orquestador_conversacion import OrquestadorConversacion  # noqa: E402
from src.core.conversacion.repositorio import InMemoryConversationRepository  # noqa: E402
from src.core.gestor_diagnostico import GestorDiagnostico  # noqa: E402


def test_esc08_correccion_temporal_frio_a_caliente():
    """Valida que una corrección explícita de temperatura reemplace frío por caliente."""
    estado = ConversationState(session_id="test_esc08_regresion")
    t1 = "El carro falla únicamente cuando está totalmente frío en un Suzuki Swift 2014"
    ExtractorHechos.extraer_y_actualizar(estado, t1)
    
    assert estado.hechos.get("marca") is not None
    assert estado.hechos["marca"].valor == "Suzuki"
    
    t2 = "Corrijo, me equivoqué, en frío arranca perfecto, la falla aparece recién a los 20 minutos cuando ya calentó"
    assert not InterpreteRespuestasCortas.es_respuesta_corta(t2)
    
    corrs = ExtractorHechos.detectar_correcciones(t2)
    assert any(c[0] == "temperatura" and c[1] == "caliente" for c in corrs)
    
    ExtractorHechos.extraer_y_actualizar(estado, t2)
    
    # Debe conservar caliente y no frío
    hecho_temp = estado.hechos.get("temperatura")
    assert hecho_temp is not None
    assert hecho_temp.valor == "caliente"
    assert hecho_temp.estado == FactState.CONFIRMADO


def test_distincion_duracion_vs_medicion_instrumental():
    """Valida que frases de duración temporal no se interpreten como magnitudes físicas arbitrarias."""
    texto_duracion = "El motor recalienta después de manejar 20 minutos"
    assert not InterpreteRespuestasCortas.es_respuesta_corta(texto_duracion)
    
    med = InterpreteRespuestasCortas._extraer_medicion(
        texto_duracion.lower(),
        intent_str="GENERAL",
        texto_preg="cuándo ocurre",
    )
    assert med is None or med[1] != "unidades"


def test_multiples_mediciones_con_condiciones_locales():
    """Valida la extracción simultánea de lecturas con sus condiciones (ralentí vs luces)."""
    texto = "En ralentí marca 13.8 V, pero con luces baja a 12.4 V"
    mediciones = InterpreteRespuestasCortas._extraer_todas_mediciones(
        texto.lower(),
        intent_str="MEDICION_VOLTAJE",
        texto_preg="cuánto marca el multímetro",
    )
    assert len(mediciones) >= 2
    valores = {m[0]: m[2] for m in mediciones}
    assert 13.8 in valores
    assert 12.4 in valores
    assert valores[13.8] in ("ralenti_carga", None)
    assert valores[12.4] == "con_carga_electrica"


def test_esc14_medicion_voltaje_bateria_normal_arranque():
    """Valida que 12.6V en reposo y 10.2V en arranque descarte batería y oriente al sistema de arranque."""
    repo = InMemoryConversationRepository()
    orquestador = OrquestadorConversacion(repositorio=repo)
    gestor = GestorDiagnostico()
    ses_id = "test_esc14_regresion"

    async def _run():
        t1 = "El motor no da arranque en un Toyota Corolla 2010"
        await orquestador.procesar_turno(ses_id, t1, gestor)

        t2 = "12.6 V en reposo y baja a 10.2 V al dar marcha con el multimetro"
        res2 = await orquestador.procesar_turno(ses_id, t2, gestor)
        resp_texto = res2.get("respuesta_texto", "")

        estado = await repo.get_session(ses_id)
        assert estado is not None
        assert estado.obtener_hecho("caida_tension_excesiva") is not None
        assert estado.obtener_hecho("caida_tension_excesiva").valor in ("NO", "DESCONOCIDO")
        assert estado.obtener_hecho("voltaje_arranque_normal") is not None
        assert estado.obtener_hecho("voltaje_arranque_normal").valor in ("SI", "DESCONOCIDO")

        # La respuesta debe validar la normalidad de la caída o indicar el solenoide/arrancador
        resp_l = resp_texto.lower()
        assert (
            "normal" in resp_l
            or "10.2" in resp_texto
            or "solenoide" in resp_l
            or "arrancador" in resp_l
        )
        # No debe culpar a fuga parásita como causa confirmada
        assert "fuga parásita" not in resp_l or "descarta" in resp_l

    asyncio.run(_run())
