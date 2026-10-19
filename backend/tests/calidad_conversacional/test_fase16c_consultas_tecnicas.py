"""Pruebas de regresión de Fase 16C: Despacho y reconocimiento de consultas técnicas y procedimentales."""

import pytest

from src.core.conversacion.extraccion_hechos.clasificador_mensajes import es_solicitud_detalle
from src.core.conversacion.orquestador_conversacion import OrquestadorConversacion
from src.core.conversacion.repositorio import InMemoryConversationRepository
from src.core.gestor_diagnostico import GestorDiagnostico


class TestFase16CReconocimientoLinguistico:
    """Valida que los patrones reconozcan variantes de taller y no generen falsos positivos."""

    @pytest.mark.parametrize(
        "frase",
        [
            "¿Cómo se calibra el cuerpo de aceleración electrónico sin escáner?",
            "¿Cómo medir contrapresión en el escape con manómetro?",
            "¿Cómo comprobar consumo parásito de batería con multímetro en serie?",
            "¿Cómo se mide el alabeo del disco de freno con reloj comparador?",
            "¿Cómo se prueba el retorno de inyectores con probetas graduadas?",
            "¿Cómo probar sensor MAF con osciloscopio?",
            "¿Cómo calibrar mariposa motorizada?",
            "¿Cómo ajustar la holgura de válvulas en frío?",
            "¿Cómo purgar el circuito de refrigeración correctamente?",
            "paso a paso para medir compresión de cilindros",
            "dame el procedimiento de calibración",
            "explícame cómo se hace la prueba de estanqueidad",
            "guía para revisar caída de tensión en arranque",
            "instrucciones para medir presión de bomba de gasolina",
        ],
    )
    def test_variantes_verbales_taller_positivas(self, frase):
        assert es_solicitud_detalle(frase) is True

    @pytest.mark.parametrize(
        "frase_negativa",
        [
            "Medí compresión: 175 psi parejo en los 4 cilindros, mecánica OK.",
            "Obtuve 12.4V en batería y al dar arranque cayó a 10.2V.",
            "Dio 3.5 bar de presión en el riel de inyección.",
            "¿Qué otra cosa podría ser si la bomba está bien?",
            "La medición dio dentro de rango especificado, ¿qué más comprobamos?",
            "No es Toyota, es un Nissan Sentra 2012.",
            "El cliente mencionó que su otro auto es un Ford, pero estamos revisando este.",
            "Sigue fallando en subida y tira humo negro.",
        ],
    )
    def test_casos_negativos_no_son_solicitud_detalle(self, frase_negativa):
        assert es_solicitud_detalle(frase_negativa) is False

    def test_mensaje_mixto_medicion_con_consulta_procedimental(self):
        msg = "Medí 35 psi en riel, ¿cómo se calibra el cuerpo de aceleración?"
        assert es_solicitud_detalle(msg) is True


@pytest.mark.asyncio
class TestFase16COrquestadorConsultasTecnicas:
    """Valida el despacho en el Orquestador con y sin caso activo."""

    async def test_despacho_consulta_tecnica_con_caso_activo(self):
        repo = InMemoryConversationRepository()
        orquestador = OrquestadorConversacion(repositorio=repo)
        gestor = GestorDiagnostico()
        session_id = "test_fase16c_caso_activo_001"

        # Turno 1: Iniciar diagnóstico con síntoma y vehículo
        t1 = await orquestador.procesar_turno(
            session_id=session_id,
            texto_usuario="Tengo un Nissan Tiida 2015 que tiembla mucho en ralentí.",
            gestor_diagnostico=gestor,
        )
        assert t1.get("estado") is not None
        assert t1["estado"].marca == "Nissan"
        assert t1["estado"].modelo == "Tiida"
        assert len(t1["estado"].active_symptoms) > 0

        # Turno 2: Consulta técnica procedimental durante caso activo
        t2 = await orquestador.procesar_turno(
            session_id=session_id,
            texto_usuario="¿Cómo se calibra el cuerpo de aceleración electrónico sin escáner?",
            gestor_diagnostico=gestor,
        )
        assert t2["decision"] == "DETALLE"
        assert t2["status"] in ("solicitud_detalle", "consulta_tecnica")
        # Verifica conservación del vehículo y síntomas en el estado
        assert t2["estado"].marca == "Nissan"
        assert t2["estado"].modelo == "Tiida"
        assert len(t2["estado"].active_symptoms) > 0

    async def test_no_desvia_a_detalle_si_es_pregunta_alternativa(self):
        repo = InMemoryConversationRepository()
        orquestador = OrquestadorConversacion(repositorio=repo)
        gestor = GestorDiagnostico()
        session_id = "test_fase16c_alternativa_002"

        # Turno 1: Apertura
        await orquestador.procesar_turno(
            session_id=session_id,
            texto_usuario="Toyota Hilux 2018 no acelera bien en subida.",
            gestor_diagnostico=gestor,
        )
        # Turno 2: Pregunta por causas alternativas (NO debe ser DETALLE)
        t2 = await orquestador.procesar_turno(
            session_id=session_id,
            texto_usuario="¿Qué otra cosa podría ser si la bomba de combustible está bien?",
            gestor_diagnostico=gestor,
        )
        assert t2["decision"] != "DETALLE"

    async def test_no_desvia_a_detalle_si_es_reporte_medicion_puro(self):
        repo = InMemoryConversationRepository()
        orquestador = OrquestadorConversacion(repositorio=repo)
        gestor = GestorDiagnostico()
        session_id = "test_fase16c_medicion_003"

        await orquestador.procesar_turno(
            session_id=session_id,
            texto_usuario="Hyundai Accent 2017 cascabelea.",
            gestor_diagnostico=gestor,
        )
        t2 = await orquestador.procesar_turno(
            session_id=session_id,
            texto_usuario="Medí compresión: 175 psi parejo en los 4 cilindros, mecánica OK.",
            gestor_diagnostico=gestor,
        )
        assert t2["decision"] != "DETALLE"
