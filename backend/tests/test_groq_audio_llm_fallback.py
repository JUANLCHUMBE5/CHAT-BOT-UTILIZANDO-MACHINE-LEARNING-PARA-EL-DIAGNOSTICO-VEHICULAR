"""Regresiones para Groq como transcriptor de audio y fallback LLM."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from src.config import PathConfig, settings
from src.core.audio_processor import AudioProcessor
from src.core.diagnostico.response_generator import generar_respuesta_con_metadatos
from src.core.llm import generar_respuesta_groq, transcribir_audio_groq


class _ResponseOK:
    status_code = 200

    def json(self):
        return {"text": "el motor pierde fuerza en subida"}


def test_groq_transcribe_audio_whisper(monkeypatch):
    monkeypatch.setattr(settings, "groq_api_key", "clave-test")
    monkeypatch.setattr(settings, "groq_audio_enabled", True)
    monkeypatch.setattr(settings, "groq_audio_model", "whisper-large-v3-turbo")

    captured = {}

    def post_mock(url, headers=None, files=None, data=None, timeout=None):
        captured["url"] = url
        captured["headers"] = headers
        captured["files"] = files
        captured["data"] = data
        captured["timeout"] = timeout
        return _ResponseOK()

    monkeypatch.setattr("src.core.llm.groq_client.requests.post", post_mock)

    texto = transcribir_audio_groq(b"audio-real", "audio/ogg")

    assert texto == "el motor pierde fuerza en subida"
    assert captured["url"].endswith("/audio/transcriptions")
    assert captured["data"]["model"] == "whisper-large-v3-turbo"
    assert captured["headers"]["Authorization"].startswith("Bearer ")


def test_audio_processor_prioriza_groq_sobre_gemini(monkeypatch):
    monkeypatch.setattr(settings, "groq_api_key", "clave-test")
    monkeypatch.setattr(settings, "groq_audio_enabled", True)

    llamado = {"groq": False}

    def transcribir_mock(audio_bytes, mime_type="audio/ogg", nombre_archivo="nota_voz.ogg"):
        llamado["groq"] = True
        return "sensor de oxígeno con mezcla pobre"

    monkeypatch.setattr("src.core.llm.transcribir_audio_groq", transcribir_mock)

    texto = AudioProcessor().transcribir_nota_de_voz("media-1", b"audio", "audio/ogg", api_key="")

    assert texto == "sensor de oxígeno con mezcla pobre"
    assert llamado["groq"] is True


def test_respuesta_usa_groq_si_no_hay_gemini(monkeypatch):
    monkeypatch.setattr(settings, "groq_api_key", "clave-test")
    monkeypatch.setattr(settings, "groq_chat_enabled", True)

    def generar_groq_mock(prompt_sistema, *, tipo_consulta="diagnostico"):
        assert "inyectores" in prompt_sistema.lower()
        return "Revisa presión de combustible e inyectores antes de reemplazar piezas.", {
            "usado": True,
            "modelo": "llama-3.1-8b-instant",
            "proveedor": "groq",
            "modo": "completo_ml_rag_llm",
            "tokens_entrada": 10,
            "tokens_salida": 8,
        }

    monkeypatch.setattr("src.core.diagnostico.response_generator.generar_respuesta_groq", generar_groq_mock)
    gestor = SimpleNamespace(api_key="", _http_session=None)

    texto, metadata = generar_respuesta_con_metadatos(
        gestor,
        pregunta="Encontré que los inyectores no inyectan lo suficiente",
        diagnostico_ml="Sistema de inyección deficiente",
        contexto_manual="Prueba presión de combustible e inyectores.",
        confianza_ml=0.82,
    )

    assert "presión de combustible" in texto
    assert metadata["proveedor"] == "groq"
    assert metadata["usado"] is True


def test_groq_gpt_oss_limita_razonamiento_para_no_devolver_texto_vacio(monkeypatch):
    monkeypatch.setattr(settings, "groq_api_key", "clave-test")
    monkeypatch.setattr(settings, "groq_chat_enabled", True)
    monkeypatch.setattr(settings, "groq_model", "openai/gpt-oss-20b")
    capturado = {}

    class Respuesta:
        status_code = 200

        @staticmethod
        def json():
            return {"choices": [{"message": {"content": "Respuesta técnica."}}]}

    def post_mock(_url, **kwargs):
        capturado.update(kwargs["json"])
        return Respuesta()

    monkeypatch.setattr("src.core.llm.groq_client.requests.post", post_mock)
    texto, metadata = generar_respuesta_groq("Contexto RAG de prueba.")

    assert texto == "Respuesta técnica."
    assert metadata["proveedor"] == "groq"
    assert capturado["reasoning_effort"] == "low"
    assert capturado["include_reasoning"] is False


def test_tracker_csv_permite_ruta_persistente_separada_del_ml(monkeypatch):
    monkeypatch.setenv("TRACKER_CSV_PATH", "/app/backend/data/tracker_diagnosticos.csv")

    paths = PathConfig()

    assert paths.tracker_csv == Path("/app/backend/data/tracker_diagnosticos.csv")
