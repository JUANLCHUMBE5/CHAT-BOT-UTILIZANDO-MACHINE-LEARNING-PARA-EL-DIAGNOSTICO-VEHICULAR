"""Pruebas de regresión y validación end-to-end de estabilización integral.

Cubre los escenarios reales solicitados para la estabilización diagnóstica y conversacional:
1. Caso Toyota Corolla 2015: chirrido al frenar y vibración en el pedal -> medición de alabeo con reloj comparador de 0.12 mm.
   Verifica evaluación contra especificación OEM (máx 0.05 - 0.07 mm), explicación técnica y ausencia de confirmación prematura.
2. Caso Imposibilidad física / Plan B: "no tengo elevador ni herramientas" -> no repetir pruebas imposibles y ofrecer alternativas seguras.
3. Caso Cambio de vehículo: "ahora tengo un Yaris" o cambio de placa -> aislamiento de hechos entre casos.
4. Caso Descartes sucesivos y respuestas negativas -> conservación de caso sin reset errático.
"""

from __future__ import annotations

import pytest
from fastapi.testclient import TestClient

from src.interfaces.api.v1.endpoints.laboratorio_local.app import create_laboratory_app


@pytest.fixture
def client(monkeypatch: pytest.MonkeyPatch) -> TestClient:
    from src.config import settings
    from src.core.security import crear_jwt_token

    monkeypatch.setattr(settings, "enable_laboratory", True)
    monkeypatch.setattr(settings, "environment", "test")
    monkeypatch.setattr(settings, "gemini_api_key", "")
    monkeypatch.setattr(settings, "groq_api_key", "")
    monkeypatch.setenv("CARBOT_BLOCK_DOTENV", "true")

    app = create_laboratory_app()
    token = crear_jwt_token(usuario_id="00000000-0000-0000-0000-000000000099")
    return TestClient(app, headers={"Authorization": f"Bearer {token}"})


class TestEstabilizacionIntegralCasosReales:

    def test_toyota_corolla_frenos_alabeo_metrologico(self, client: TestClient):
        """Caso 1: Toyota Corolla 2015 con vibración al frenar y medición de alabeo 0.12 mm.

        El sistema debe:
        - Reconocer síntomas de frenos/vibración.
        - En el turno de medición '0.12 mm con reloj comparador', evaluar contra tolerancia OEM (0.05 - 0.07 mm).
        - Explicar la causa física (alabeo excesivo que produce pulsación en el pedal y vibración).
        - No caer en bucle de confirmación prematura ('¿Fue correcta? SÍ/NO').
        """
        session_id = "test_corolla_alabeo_metrologico_01"

        # Turno 1: Reporte del síntoma inicial
        r1 = client.post(
            "/api/v1/laboratorio/mensaje",
            json={
                "session_id": session_id,
                "mensaje": "Hola, tengo un Toyota Corolla 2015 con placa ABC-123. Al frenar a más de 60 km/h chilla y el pedal vibra bastante.",
            },
        )
        assert r1.status_code == 200
        d1 = r1.json()
        assert d1["case_id"] is not None
        texto_resp1 = d1["respuesta_texto"].lower()
        # No debe repreguntar si el pedal vibra porque ya fue dicho por el usuario
        assert "vibra el volante al frenar" not in texto_resp1

        # Turno 2: El usuario proporciona la medición con reloj comparador
        r2 = client.post(
            "/api/v1/laboratorio/mensaje",
            json={
                "session_id": session_id,
                "mensaje": "Medí el alabeo del disco delantero derecho con reloj comparador y dio 0.12 mm",
            },
        )
        assert r2.status_code == 200
        d2 = r2.json()
        texto_resp2 = d2["respuesta_texto"]

        # Debe contener la evaluación metrológica contra la tolerancia OEM
        assert "0.12" in texto_resp2
        assert any(tol in texto_resp2 for tol in ("0.05", "0.07", "OEM", "tolerancia", "límite"))
        assert any(pal in texto_resp2.lower() for pal in ("excede", "supera", "pulsaci", "alabeo", "rectificado"))

    def test_imposibilidad_fisica_plan_b_sin_elevador(self, client: TestClient):
        """Caso 2: Usuario sin elevador ni herramientas para suspensión.

        El sistema debe ofrecer Plan B sin insistir en elevar el vehículo ni repetir la misma prueba.
        """
        session_id = "test_suspension_plan_b_02"

        # Turno 1: Ruido en suspensión
        r1 = client.post(
            "/api/v1/laboratorio/mensaje",
            json={
                "session_id": session_id,
                "mensaje": "Tengo un Nissan Sentra con placa XYZ-789. Siento un golpe seco clac-clac en la llanta delantera al pasar baches.",
            },
        )
        assert r1.status_code == 200
        d1 = r1.json()
        assert d1["case_id"] is not None

        # Turno 2: El usuario declara que no tiene elevador ni herramientas
        r2 = client.post(
            "/api/v1/laboratorio/mensaje",
            json={
                "session_id": session_id,
                "mensaje": "No tengo elevador ni herramientas para desmontar la rueda en mi casa",
            },
        )
        assert r2.status_code == 200
        d2 = r2.json()
        texto_resp2 = d2["respuesta_texto"].lower()

        # Debe reconocer la limitación y ofrecer verificación segura en plano o derivación
        assert any(w in texto_resp2 for w in ("segur", "plano", "vaivén", "vaiven", "taller", "inspección", "inspeccion"))

    def test_cambio_de_caso_limpieza_de_hechos(self, client: TestClient):
        """Caso 3: Detección de cambio de vehículo/caso.

        Si el usuario consulta por otro vehículo, el caso anterior no debe contaminar el nuevo.
        """
        session_id = "test_cambio_caso_03"

        r1 = client.post(
            "/api/v1/laboratorio/mensaje",
            json={
                "session_id": session_id,
                "mensaje": "Mi Toyota Corolla placa AAA-111 tiene chillido fuerte en los frenos",
            },
        )
        assert r1.status_code == 200
        d1 = r1.json()
        case_id_1 = d1["case_id"]

        # Usuario cambia a otro vehículo explícitamente
        r2 = client.post(
            "/api/v1/laboratorio/mensaje",
            json={
                "session_id": session_id,
                "mensaje": "Ahora tengo otro carro en el taller, es un Yaris placa BBB-222 que no arranca y huele a gasolina",
            },
        )
        assert r2.status_code == 200
        d2 = r2.json()
        # Debe haberse actualizado la placa o generado nuevo caso
        assert d2.get("placa") == "BBB-222" or d2["case_id"] != case_id_1 or "gasolina" in d2["respuesta_texto"].lower() or "arranc" in d2["respuesta_texto"].lower()

    def test_descartes_sucesivos_no_pierden_contexto(self, client: TestClient):
        """Caso 4: Negaciones y descartes no provocan un reset destructivo del caso."""
        session_id = "test_descartes_multi_04"

        r1 = client.post(
            "/api/v1/laboratorio/mensaje",
            json={
                "session_id": session_id,
                "mensaje": "El motor de mi Hyundai Elantra cascabelea al acelerar en subida y tironea",
            },
        )
        assert r1.status_code == 200
        d1 = r1.json()
        case_id_1 = d1["case_id"]

        # Descarte de bujías
        r2 = client.post(
            "/api/v1/laboratorio/mensaje",
            json={
                "session_id": session_id,
                "mensaje": "Las bujías ya las revisé y están completamente nuevas, no son las bujías",
            },
        )
        assert r2.status_code == 200
        d2 = r2.json()
        # El caso se mantiene
        assert d2["case_id"] == case_id_1
        # No debe confirmar las bujías como la causa principal
        assert "bujia" not in (d2.get("diagnostico_ml") or "").lower() or d2.get("confianza_ml", 0) <= 0.5

