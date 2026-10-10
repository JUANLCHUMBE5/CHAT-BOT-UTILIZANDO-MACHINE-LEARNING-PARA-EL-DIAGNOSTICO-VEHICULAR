from __future__ import annotations

from src.core.conversacion.models import ConversationState
from src.core.diagnostico.text_processor import procesar_consulta_texto
from src.core.session_manager import SessionManager


class _ModeloMLSpy:
    def __init__(self) -> None:
        self.consultas: list[str] = []

    def predecir_top_fallas(self, texto: str, limite: int = 3) -> list[dict]:
        self.consultas.append(texto)
        return [{"falla": "Sobrecalentamiento del motor", "probabilidad": 0.76}]


class _RagSpy:
    corpus_validado = False

    def __init__(self) -> None:
        self.consultas: list[str] = []
        self.argumentos: list[dict] = []

    def recuperar_procedimiento_hibrido(self, **kwargs):
        self.argumentos.append(kwargs)
        self.consultas.append(kwargs["consulta"])
        return "fragmento preliminar de refrigeración", "Radiador", 0.91, {
            "falla": None,
            "macro_sistema": "MOTOR",
        }


class _GestorSpy:
    def __init__(self) -> None:
        self.session_manager = SessionManager()
        self.modelo_ml = _ModeloMLSpy()
        self.motor_rag = _RagSpy()
        self.api_key = None
        self.argumentos_llm = None

    @staticmethod
    def _es_saludo_o_contacto_inicial(_texto):
        return False, ""

    @staticmethod
    def _es_respuesta_cordial(_texto):
        return False

    @staticmethod
    def _extraer_contexto_combustible(_texto):
        return None, None

    @staticmethod
    def _es_perdida_potencia_bajo_carga(_texto):
        return False

    @staticmethod
    def _purificar_sintoma_para_vectorizador_ml(texto):
        return texto

    @staticmethod
    def _es_consulta_ambigua(_texto):
        return False, ""

    @staticmethod
    def _es_continuacion_contextual(_texto):
        return True

    @staticmethod
    def _formatear_perfil_vehiculo(_perfil):
        return ""

    def _generar_respuesta_con_metadatos(self, **kwargs):
        self.argumentos_llm = kwargs
        return "respuesta simulada", {"usado": False, "modo": "degradado"}

    @staticmethod
    def _registrar_en_tracker(**_kwargs):
        return None


def test_contexto_activo_llega_sin_mezcla_a_ml_rag_y_llm():
    gestor = _GestorSpy()
    state = ConversationState(session_id="mecanico-42", case_id="case-B")
    state.placa = "XYZ789"
    state.marca = "Mazda"
    state.modelo = "3"
    state.active_system = "refrigeracion"
    gestor.session_manager.cargar_contexto(
        state.session_id,
        {
            "case_id": "case-B",
            "conversation_state": state.exportar_dict(),
            "sintomas": ["mezcla pobre"],
            "placa": "ABC123",
        },
    )
    query = "Mazda 3 presenta recalentamiento en tráfico"

    resultado = procesar_consulta_texto(
        gestor,
        texto_usuario=query,
        placa="XYZ789",
        marca_modelo="Mazda 3",
        session_id=state.session_id,
        proveedor="api",
        orquestado=True,
        case_id="case-B",
    )

    consulta_normalizada = resultado.sintoma_evaluado
    assert consulta_normalizada == query.casefold()
    assert gestor.modelo_ml.consultas == [consulta_normalizada]
    assert gestor.motor_rag.consultas == [consulta_normalizada]
    assert gestor.motor_rag.argumentos[0]["consulta"] == consulta_normalizada
    assert gestor.argumentos_llm["pregunta"] == consulta_normalizada
    assert gestor.argumentos_llm["contexto_manual"] == ""
    assert gestor.argumentos_llm["case_id"] == "case-B"
    assert "mezcla pobre" not in " ".join(gestor.modelo_ml.consultas + gestor.motor_rag.consultas)
