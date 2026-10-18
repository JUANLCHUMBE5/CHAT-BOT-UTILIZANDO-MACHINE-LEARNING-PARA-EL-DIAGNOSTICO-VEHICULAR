"""Pruebas de la integración de Comprensión Semántica (Fase 14.1) en OrquestadorConversacion."""

import json
from unittest.mock import MagicMock, patch

from src.core.conversacion.comprension_semantica import (
    EstadoHechoSemantico,
    interpretar_mensaje_usuario,
)


def test_comprension_semantica_distingue_no_revisado_con_mock_llm():
    """Verifica que el LLM catalogue 'no he comprobado' como NO_REVISADO y no como DESCARTADO."""
    mock_payload = {
        "choices": [
            {
                "message": {
                    "content": json.dumps({
                        "intenciones": ["aclarar_comprobacion", "solicitar_alternativas"],
                        "hechos_nuevos": [
                            {
                                "tipo": "comprobacion",
                                "campo": "sonido_bomba_combustible",
                                "valor": "No se ha verificado si la bomba suena al poner contacto en ON",
                                "estado": "NO_REVISADO",
                                "evidencia_texto": "No he comprobado si la bomba suena al poner contacto en ON"
                            },
                            {
                                "tipo": "condicion",
                                "campo": "nivel_tanque",
                                "valor": "Más de medio nivel",
                                "estado": "CONFIRMADO",
                                "evidencia_texto": "El tanque tiene mas de medio nivel"
                            }
                        ],
                        "pregunta_tecnica_usuario": "¿Qué otras causas podrían explicar estos síntomas y qué dato necesitas?",
                        "solicita_causas_alternativas": True,
                        "solicita_nuevo_caso": False,
                        "solicita_continuar": False,
                        "datos_vehiculo": {},
                        "requiere_aclaracion": False,
                        "explicacion_resumida": "El mecánico aclara que no ha comprobado la bomba y pide causas alternativas"
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

        mensaje = "No he comprobado si la bomba suena al poner contacto en ON. El tanque tiene mas de medio nivel."
        interp = interpretar_mensaje_usuario(mensaje)

        assert interp.origen == "llm_groq"
        assert interp.solicita_causas_alternativas is True
        assert len(interp.hechos_nuevos) == 2
        
        hecho_bomba = next(h for h in interp.hechos_nuevos if "bomba" in h.campo)
        assert hecho_bomba.estado == EstadoHechoSemantico.NO_REVISADO


def test_comprension_semantica_pregunta_tecnica_y_alternativas_mock_llm():
    """Verifica la detección de solicitud de causas alternativas y extracción de pregunta técnica."""
    mock_payload = {
        "choices": [
            {
                "message": {
                    "content": json.dumps({
                        "intenciones": ["solicitar_alternativas"],
                        "hechos_nuevos": [],
                        "pregunta_tecnica_usuario": "¿Qué otras causas podrían explicar estos síntomas y qué dato necesitas?",
                        "solicita_causas_alternativas": True,
                        "solicita_nuevo_caso": False,
                        "solicita_continuar": False,
                        "datos_vehiculo": {},
                        "requiere_aclaracion": False,
                        "explicacion_resumida": "Consulta de hipótesis alternativas"
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

        mensaje = "¿Qué otras causas podrían explicar estos síntomas y qué dato necesitas?"
        interp = interpretar_mensaje_usuario(mensaje)

        assert interp.solicita_causas_alternativas is True
        assert interp.pregunta_tecnica_usuario is not None
        assert "causa" in interp.pregunta_tecnica_usuario.lower() or "dato" in interp.pregunta_tecnica_usuario.lower()


def test_comprension_semantica_nuevo_caso_y_vehiculo_mock_llm():
    """Verifica la detección de intención de nuevo caso y captura de vehículo con errores ortográficos."""
    mock_payload = {
        "choices": [
            {
                "message": {
                    "content": json.dumps({
                        "intenciones": ["reportar_sintoma", "solicitar_nuevo_caso"],
                        "hechos_nuevos": [],
                        "pregunta_tecnica_usuario": None,
                        "solicita_causas_alternativas": False,
                        "solicita_nuevo_caso": True,
                        "solicita_continuar": False,
                        "datos_vehiculo": {
                            "marca": "Nissan",
                            "modelo": "Sentra",
                            "anio": "2018",
                            "placa": None
                        },
                        "requiere_aclaracion": False,
                        "explicacion_resumida": "Nuevo caso para Nissan Sentra 2018"
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

        mensaje = "NEUVO CASO. Tengo un Nissan Sentra 2018 automatico. Pierde potencia en subidas."
        interp = interpretar_mensaje_usuario(mensaje)

        assert interp.solicita_nuevo_caso is True
        assert interp.datos_vehiculo.get("marca") == "Nissan"
        assert interp.datos_vehiculo.get("modelo") == "Sentra"
        assert interp.datos_vehiculo.get("anio") == "2018"


def test_comprension_semantica_fallback_determinista_sin_clave():
    """Verifica que ante ausencia de clave API, el fallback funcione inmediatamente y con contrato seguro."""
    with patch("src.config.settings.groq_api_key", ""):
        mensaje = "No he comprobado la bomba de gasolina. ¿Qué otras causas pueden ser?"
        interp = interpretar_mensaje_usuario(mensaje)

        assert interp.origen == "heuristica_fallback"
        assert interp.solicita_causas_alternativas is True
        assert isinstance(interp.hechos_nuevos, list)
