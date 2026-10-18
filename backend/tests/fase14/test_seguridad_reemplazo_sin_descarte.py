"""Pruebas de seguridad diagnóstica ante sustitución de componentes y antecedentes técnicos.

Verifica que mensajes como:
"Las bujías ya las cambié ayer y sigue exactamente igual"
- Extraigan correctamente la acción de reemplazo o antecedente técnico.
- NO interpreten automáticamente el reemplazo como confirmación de reparación.
- NO descarten todo el sistema de encendido ni borren las bujías de consideración técnica sin evidencia de banco/medición.
- Mantengan las hipótesis SVM evaluables según síntomas persistentes y comprobaciones.
- No generen descarte irreversible en el estado conversacional.
"""

import json
from unittest.mock import MagicMock, patch

import pytest

from src.core.conversacion.comprension_semantica.contratos import (
    EstadoHechoSemantico,
)
from src.core.conversacion.comprension_semantica.interprete import (
    interpretar_mensaje_usuario,
)
from src.core.conversacion.orquestador_conversacion import OrquestadorConversacion
from src.core.conversacion.repositorio import InMemoryConversationRepository
from src.core.conversacion.state_models.state import ConversationState
from src.core.gestor_diagnostico import GestorDiagnostico


def test_extraccion_semantica_reemplazo_no_descarta():
    """Verifica que el intérprete semántico catalogue el reemplazo con estado REEMPLAZADO."""
    mock_payload = {
        "choices": [
            {
                "message": {
                    "content": json.dumps({
                        "intenciones": ["reportar_sintoma", "aclarar_comprobacion"],
                        "hechos_nuevos": [
                            {
                                "tipo": "comprobacion",
                                "campo": "bujias",
                                "valor": "Cambiadas ayer, falla persiste idéntica",
                                "estado": "REEMPLAZADO",
                                "evidencia_texto": "Las bujías ya las cambié ayer y sigue exactamente igual"
                            }
                        ],
                        "pregunta_tecnica_usuario": None,
                        "solicita_causas_alternativas": False,
                        "solicita_nuevo_caso": False,
                        "solicita_continuar": False,
                        "datos_vehiculo": {},
                        "requiere_aclaracion": False,
                        "explicacion_resumida": "El mecánico indica que reemplazó las bujías pero el síntoma persiste"
                    })
                }
            }
        ]
    }

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = mock_payload

    with patch("requests.post", return_value=mock_resp), \
         patch("src.config.settings.groq_api_key", "mock_key"), \
         patch("src.config.settings.groq_chat_enabled", True):

        mensaje = "Las bujías ya las cambié ayer y sigue exactamente igual"
        interp = interpretar_mensaje_usuario(mensaje)

        assert len(interp.hechos_nuevos) == 1
        hecho = interp.hechos_nuevos[0]
        assert hecho.campo == "bujias"
        assert hecho.estado == EstadoHechoSemantico.REEMPLAZADO
        assert hecho.estado != EstadoHechoSemantico.DESCARTADO


@pytest.mark.anyio
async def test_orquestador_reemplazo_no_agrega_a_hipotesis_descartadas():
    """El orquestador debe registrar el antecedente pero NO agregar el componente a hipotesis_descartadas."""
    gestor = GestorDiagnostico()
    gestor.api_key = ""
    repo = InMemoryConversationRepository()
    gestor.conversation_repo = repo
    orquestador = OrquestadorConversacion(repositorio=repo)

    session_id = "test_reemplazo_seguro"
    estado_inicial = ConversationState(session_id=session_id)
    estado_inicial.marca = "Nissan"
    estado_inicial.modelo = "Sentra"
    estado_inicial.anio = "2018"
    estado_inicial.placa = "ABC-123"
    estado_inicial.active_symptoms = ["tirones al acelerar", "cascabeleo"]
    await repo.save_session(session_id, estado_inicial)

    mock_payload = {
        "choices": [
            {
                "message": {
                    "content": json.dumps({
                        "intenciones": ["aclarar_comprobacion"],
                        "hechos_nuevos": [
                            {
                                "tipo": "comprobacion",
                                "campo": "bujias",
                                "valor": "Cambiadas ayer y sigue igual",
                                "estado": "REEMPLAZADO",
                                "evidencia_texto": "Las bujías ya las cambié ayer y sigue exactamente igual"
                            }
                        ],
                        "pregunta_tecnica_usuario": None,
                        "solicita_causas_alternativas": False,
                        "solicita_nuevo_caso": False,
                        "solicita_continuar": False,
                        "datos_vehiculo": {},
                        "requiere_aclaracion": False,
                        "explicacion_resumida": "Antecedente de bujías nuevas sin solución"
                    })
                }
            }
        ]
    }

    mock_resp = MagicMock()
    mock_resp.status_code = 200
    mock_resp.json.return_value = mock_payload

    with patch("requests.post", return_value=mock_resp), \
         patch("src.config.settings.groq_api_key", "mock_key"), \
         patch("src.config.settings.groq_chat_enabled", True):

        mensaje = "Las bujías ya las cambié ayer y sigue exactamente igual"
        res = await orquestador.procesar_turno(
            session_id=session_id,
            texto_usuario=mensaje,
            gestor_diagnostico=gestor,
        )

        estado = res["estado"]

        # 1. Comprobar que bujías NO está en hipotesis_descartadas
        assert "bujias" not in estado.hipotesis_descartadas
        assert "sistema_encendido" not in estado.hipotesis_descartadas

        # 2. Comprobar que no se descartan todas las hipótesis ni se declara reparado
        assert estado.fase.value != "cerrado"

        # 3. Comprobar que quedó registrado en hechos
        hecho_registrado = estado.hechos.get("bujias") or estado.hechos.get("componente_reemplazado_bujias")
        assert hecho_registrado is not None
        cat = getattr(hecho_registrado, "categoria", None) or hecho_registrado.categoria
        assert cat in ("componente_reemplazado", "antecedente", "inspeccion_pendiente")


def test_fallback_semantico_reemplazo_no_descarta():
    """El fallback determinista también debe evitar catalogar el cambio como descarte irreversible."""
    with patch("src.config.settings.groq_api_key", ""):
        mensaje = "Las bujías ya las cambié ayer y sigue exactamente igual"
        interp = interpretar_mensaje_usuario(mensaje)

        for h in interp.hechos_nuevos:
            assert h.estado != EstadoHechoSemantico.DESCARTADO, f"Hecho {h.campo} marcado erróneamente como DESCARTADO"
