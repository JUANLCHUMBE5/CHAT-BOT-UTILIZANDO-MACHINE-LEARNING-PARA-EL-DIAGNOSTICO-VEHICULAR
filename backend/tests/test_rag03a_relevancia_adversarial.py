"""
Pruebas adversariales de relevancia documental y abstención técnica RAG-03A.
Valida:
1. Descarte de falsos positivos en lubricación (presión de aceite con manómetro -> abstención limpia).
2. Distinción de 'en ralentí' como condición de medición vs falla de marcha mínima.
3. Desacoplamiento de impulsos SVM/ML espurios (refrigeración vs CKP/CMP).
4. Compatibilidad vehicular y de fluidos.
"""

import pytest

from src.infrastructure.motor_rag import MotorRAG


@pytest.fixture(scope="module")
def rag():
    return MotorRAG()


class TestAdversarialLubricacion:
    """Valida que consultas sobre medición de presión de aceite no se desvíen a VVT, cambio de aceite o correa."""

    def test_medicion_presion_aceite_con_manometro_se_abstiene(self, rag):
        consulta = "Procedimiento para medir la presion de aceite de motor con manometro mecanico en ralenti"
        doc, titulo, sim, meta = rag.recuperar_procedimiento_hibrido(
            consulta=consulta,
            macro_sistema="MOTOR",
            top_fallas=[{"falla": "Cuerpo de aceleracion o valvula IAC sucia", "probabilidad": 0.85}],
        )
        assert titulo == "Coincidencia baja" or sim < 0.10, (
            f"Se esperaba abstención documental por falta de procedimiento de manómetro en corpus, se obtuvo: {titulo} ({sim})"
        )
        assert "vvt" not in titulo.lower(), (
            "Falso positivo: Solenoide VVT no debe responder medición manométrica"
        )
        assert "cambio de aceite" not in titulo.lower(), (
            "Falso positivo: Cambio de aceite no responde medición manométrica"
        )
        assert "correa" not in titulo.lower(), (
            "Falso positivo: Correa en aceite no responde medición manométrica"
        )

    def test_medicion_presion_aceite_frio_caliente_se_abstiene(self, rag):
        consulta = "Prueba de presion de aceite de motor con manometro en frio y caliente"
        doc, titulo, sim, meta = rag.recuperar_procedimiento_hibrido(
            consulta=consulta,
            macro_sistema="MOTOR",
        )
        assert titulo == "Coincidencia baja" or sim < 0.10


class TestAdversarialCondicionRalenti:
    """Valida que 'en ralentí' como condición de prueba no desvíe a la válvula IAC o cuerpo de aceleración."""

    def test_presion_riel_en_ralenti_no_recupera_iac(self, rag):
        consulta = "Cual es la presion de riel de combustible common rail en ralenti"
        doc, titulo, sim, meta = rag.recuperar_procedimiento_hibrido(
            consulta=consulta,
            macro_sistema="MOTOR",
            codigos_dtc=["P0087"],
        )
        assert "riel" in titulo.lower() or "presi" in titulo.lower()
        assert "iac" not in titulo.lower() and "cuerpo de aceleraci" not in titulo.lower()

    def test_caida_tension_alternador_en_ralenti_no_recupera_iac(self, rag):
        consulta = "Medicion de caida de tension en terminales de alternador con motor en ralenti"
        doc, titulo, sim, meta = rag.recuperar_procedimiento_hibrido(
            consulta=consulta,
            macro_sistema="ELECTRICO",
            top_fallas=[
                {"falla": "Alternador con diodo quemado o regulador defectuoso", "probabilidad": 0.80}
            ],
        )
        assert "iac" not in titulo.lower() and "cuerpo de aceleraci" not in titulo.lower()
        assert (
            "alternador" in titulo.lower()
            or "carga" in titulo.lower()
            or "voltaje" in titulo.lower()
            or "coincidencia baja" in titulo.lower()
        )

    def test_sintoma_genuino_ralenti_inestable_si_recupera_iac(self, rag):
        consulta = "El motor oscila en ralenti inestable y se apaga en marcha minima"
        doc, titulo, sim, meta = rag.recuperar_procedimiento_hibrido(
            consulta=consulta,
            macro_sistema="MOTOR",
            top_fallas=[{"falla": "Cuerpo de aceleracion o valvula IAC sucia", "probabilidad": 0.88}],
        )
        assert "cuerpo de aceleraci" in titulo.lower() or "iac" in titulo.lower()
        assert sim >= 0.15


class TestAdversarialRefrigeracionYSensores:
    """Valida que preguntas de fugas de refrigerante no se desvíen hacia CKP/CMP ni a enfriador de aceite."""

    def test_fuga_refrigerante_con_top_ml_ckp_recupera_enfriamiento(self, rag):
        consulta = "Prueba de estanqueidad y detector de fugas en radiador o mangueras de refrigerante"
        doc, titulo, sim, meta = rag.recuperar_procedimiento_hibrido(
            consulta=consulta,
            macro_sistema="MOTOR",
            top_fallas=[
                {
                    "falla": "Falla en sensor de posicion de ciguenal (CKP) o arbol de levas (CMP)",
                    "probabilidad": 0.85,
                }
            ],
        )
        assert (
            "enfriamiento" in titulo.lower()
            or "refrigeraci" in titulo.lower()
            or "radiador" in titulo.lower()
        )
        assert "ckp" not in titulo.lower() and "cmp" not in titulo.lower() and "cigue" not in titulo.lower()

    def test_prueba_quimica_co2_culata_no_recupera_enfriador_aceite(self, rag):
        consulta = "Prueba quimica de CO2 en liquido refrigerante con detector para junta de culata"
        doc, titulo, sim, meta = rag.recuperar_procedimiento_hibrido(
            consulta=consulta,
            macro_sistema="MOTOR",
        )
        assert "enfriador de aceite" not in titulo.lower()


class TestAdversarialCompatibilidadVehicular:
    """Valida que procedimientos de una marca específica sean severamente penalizados en consultas de otra marca."""

    def test_procedimiento_especifico_otra_marca_es_penalizado(self, rag):
        candidatos = [
            {
                "indice": 0,
                "titulo": "PROCEDIMIENTO: CALIBRACIÓN CUERPO ACELERACIÓN NISSAN VERSA HR16DE",
                "documento": "Procedimiento específico para cuerpo de mariposa Nissan.",
                "similitud": 0.25,
                "metadatos": {
                    "sistema": "MOTOR",
                    "make": "Nissan",
                    "model": "Versa",
                    "vehicle_scope": "VEHICLE_SPECIFIC",
                    "falla": "Cuerpo de aceleracion o valvula IAC sucia",
                    "codigos_dtc": [],
                },
            }
        ]
        from src.infrastructure.rag.relevance_filter import reordenar_candidatos_rag

        reord = reordenar_candidatos_rag(
            candidatos,
            macro_sistema="MOTOR",
            marca="Toyota",
            modelo="Corolla",
            consulta="calibracion de aceleracion en toyota corolla",
        )
        # Factor penalización para otra marca es 0.05
        assert reord[0]["similitud"] < 0.05
