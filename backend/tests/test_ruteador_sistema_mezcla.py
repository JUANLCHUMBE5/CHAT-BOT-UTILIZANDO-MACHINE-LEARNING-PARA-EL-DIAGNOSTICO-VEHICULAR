"""Regresiones de la secuencia real anonimizada: mezcla pobre e inyectores."""

from unittest.mock import MagicMock

import pytest

from src.core.conversacion.models import ConversationState
from src.core.conversacion.ruteador_sistema import SISTEMA_INYECCION_MEZCLA, detectar_ruta_sistema
from src.core.conversacion.validador_compatibilidad import ValidadorCompatibilidad


def test_mezcla_pobre_e_inyectores_bloquean_hipotesis_de_refrigeracion_y_iac() -> None:
    estado = ConversationState(session_id="mezcla-anonima")
    estado.historial_mensajes_usuario = [
        "El escáner indica mezcla pobre y el motor falla en ralentí.",
        "Ya revisé la IAC y está bien.",
        "Encontré que los inyectores no inyectan lo suficiente.",
        "El sensor de oxígeno se queda en 0.1 V y lo cambié, pero sigue igual.",
    ]
    ruta = detectar_ruta_sistema(estado)
    assert ruta.sistema == SISTEMA_INYECCION_MEZCLA

    finales, exclusiones = ValidadorCompatibilidad.filtrar_y_ordenar_para_presentacion(
        predicciones_raw=[
            {"falla": "Cuerpo de aceleración o válvula IAC sucia", "probabilidad": 0.98},
            {"falla": "Termostato o motoventilador defectuoso", "probabilidad": 0.11},
            {"falla": "Baja presión de aceite", "probabilidad": 0.06},
        ],
        estado=estado,
        nueva_evidencia=estado.historial_mensajes_usuario[-1],
    )

    texto_final = " ".join(item["falla"].lower() for item in finales)
    assert finales == []  # No fabricar probabilidades ni rescatar hipótesis excluidas.
    assert "iac" not in texto_final
    assert "termostato" not in texto_final
    assert any(item["motivo"] == "SISTEMA_INCOMPATIBLE_CON_EVIDENCIA" for item in exclusiones)


def test_sin_ruta_tecnica_no_se_descartan_candidatas_ml() -> None:
    estado = ConversationState(session_id="sin-ruta")
    finales, _ = ValidadorCompatibilidad.filtrar_y_ordenar_para_presentacion(
        predicciones_raw=[{"falla": "Termostato defectuoso", "probabilidad": 0.70}],
        estado=estado,
    )
    assert finales[0]["falla"] == "Termostato defectuoso"


def test_componentes_ajenos_no_se_admiten_por_palabras_genericas():
    from src.core.conversacion.ruteador_sistema import hipotesis_compatibles_con_ruta
    for falla in ("Bomba de agua defectuosa", "Aire acondicionado no enfría", "Filtro de aceite"):
        assert not hipotesis_compatibles_con_ruta(falla, SISTEMA_INYECCION_MEZCLA)


@pytest.mark.parametrize("falla", [
    "Falla en sistema Flex / Bi-combustible (Alcohol/Etanol)",
    "Descarbonización e inyección directa GDI",
    "Inyectores GLP", "Inyectores GNV", "Filtro DPF diésel",
])
def test_no_asume_equipamiento(falla):
    estado = ConversationState(session_id="vehiculo-sin-equipamiento-confirmado")
    estado.historial_mensajes_usuario = ["Nissan Versa 2016, escáner arroja mezcla pobre"]
    finales, exclusiones = ValidadorCompatibilidad.filtrar_y_ordenar_para_presentacion(
        [{"falla": falla, "probabilidad": 0.97}], estado
    )
    assert finales == []
    assert exclusiones[0]["motivo"] == "EQUIPAMIENTO_NO_CONFIRMADO"


def test_flex_confirmado_es_candidato_permitido():
    estado = ConversationState(session_id="flex-confirmado")
    estado.historial_mensajes_usuario = ["Motor Flex con etanol, mezcla pobre"]
    finales, _ = ValidadorCompatibilidad.filtrar_y_ordenar_para_presentacion(
        [{"falla": "Falla en sistema Flex / Bi-combustible (Alcohol/Etanol)", "probabilidad": 0.31}], estado
    )
    assert finales[0]["probabilidad"] == 0.31


def test_orientacion_baja_confianza_avanza_y_sobrevive_serializacion():
    from src.core.conversacion.evidencia_taller import respuesta_evidencia_insuficiente
    estado = ConversationState(session_id="orientacion")
    estado.historial_mensajes_usuario = ["Mezcla pobre, injectores no inyectan suficiente"]
    primera = respuesta_evidencia_insuficiente(estado)
    estado = ConversationState.from_dict(estado.exportar_dict())
    segunda = respuesta_evidencia_insuficiente(estado)
    assert primera != segunda
    assert "caudal" in primera
    assert "presión" in segunda
    assert "%" not in primera + segunda


def test_hallazgo_de_inyectores_prioriza_sin_inventar_confianza():
    from src.core.diagnostico.coherencia_evidencia import priorizar_evidencia
    from src.core.diagnostico.models import PrediccionML
    candidatas = [PrediccionML(falla="EVAP", probabilidad=0.8),
                 PrediccionML(falla="Inyectores sucios", probabilidad=0.03)]
    finales, motivo = priorizar_evidencia("Encontré que los injectores no inyectan lo suficiente", candidatas)
    assert finales[0].falla == "Inyectores sucios"
    assert finales[0].probabilidad == 0.03
    assert motivo


def test_prompt_llm_conserva_descartes_y_evidencia():
    from src.core.diagnostico.prompt_builder import construir_prompt_diagnostico
    prompt = construir_prompt_diagnostico(
        pregunta_llm="Mezcla pobre", diagnostico_ml="Inyectores", confianza_pct=20,
        titulo_manual="Sin fuente verificada", contexto_llm="", alerta_revision="Revisar en taller",
        evidencia_confirmada=["Caudal insuficiente reportado; prueba pendiente"],
        componentes_descartados=["IAC comprobada en taller"],
    )
    assert "Caudal insuficiente reportado; prueba pendiente" in prompt
    assert "IAC comprobada en taller" in prompt


def test_descarte_se_asocia_al_componente_y_resultado():
    from src.core.conversacion.ruteador_sistema import tiene_descarte_de_componente
    estado = ConversationState(session_id="descarte")
    estado.historial_mensajes_usuario = ["La IAC falla", "Ya revisé el fusible y está bien"]
    assert not tiene_descarte_de_componente(estado, "Válvula IAC sucia")
    estado.historial_mensajes_usuario.append("Revisé la IAC y está mal")
    assert not tiene_descarte_de_componente(estado, "Válvula IAC sucia")
    estado.historial_mensajes_usuario.append("La IAC funciona bien")
    assert tiene_descarte_de_componente(estado, "Válvula IAC sucia")


def test_categorias_especificas():
    for mensaje, esperado in (
        ("Falla de bobina", "ENCENDIDO"),
        ("Problema de programación ECU", "PROGRAMACION"),
        ("Fuga de refrigerante", "REFRIGERACION"),
        ("Desgaste de pastillas", "FRENOS"),
    ):
        estado = ConversationState(session_id="categorias")
        estado.historial_mensajes_usuario = [mensaje]
        assert detectar_ruta_sistema(estado).sistema == esperado


def test_formateador_respeta_supresion_de_pregunta_repetida():
    from src.core.conversacion.formateador_compacto import FormateadorCompacto
    respuesta = FormateadorCompacto.formatear_respuesta_diagnostico(
        [{"falla": "Inyectores sucios", "probabilidad": 0.42}], pregunta_personalizada=""
    )
    assert "¿" not in respuesta
    assert "42%" in respuesta


@pytest.mark.anyio
async def test_secuencia_mecanico_con_memoria_y_dto_coherente():
    from src.core.conversacion.orquestador_conversacion import OrquestadorConversacion
    from src.core.conversacion.repositorio import InMemoryConversationRepository
    from src.core.diagnostico.models import ResultadoDiagnostico
    repo = InMemoryConversationRepository()
    orquestador = OrquestadorConversacion(repo)
    gestor = MagicMock()
    del gestor.session_manager
    gestor.procesar_consulta_texto.return_value = ResultadoDiagnostico(
        respuesta_texto="Predicción incompatible simulada para regresión",
        diagnostico_ml="Válvula IAC sucia", confianza_ml=0.98,
        contexto_manual="Procedimiento IAC", titulo_manual="IAC",
        predicciones_ml=[
            {"falla": "Válvula IAC sucia", "probabilidad": 0.98},
            {"falla": "Termostato defectuoso", "probabilidad": 0.01},
            {"falla": "Presión de aceite baja", "probabilidad": 0.01},
        ],
    )
    preguntas = []
    for mensaje in (
        "El scaner arroja mezcla pobre en el sistema",
        "P0171 en ralenti, ahora que esta caliente sigue el DTC",
        "Encontré que los injectores no inyectan lo suficiente",
        "El sensor de oxígeno se queda en 0.1",
        "Es el sensor anterior medido con escáner",
        "Cambié el sensor y hace lo mismo",
    ):
        resultado = await orquestador.procesar_turno("mecanico", mensaje, gestor)
        respuesta = resultado["respuesta_texto"]
        assert "termostato" not in respuesta.lower()
        assert "iac" not in respuesta.lower()
        assert "65%" not in respuesta
        assert "¿se ha conectado" not in respuesta
        if resultado.get("pregunta_final"):
            pregunta = resultado["pregunta_final"]
            assert pregunta not in preguntas
            preguntas.append(pregunta)
        if resultado.get("dto"):
            dto = resultado["dto"]
            assert [p.model_dump() for p in dto.predicciones_ml] == resultado["top3_actual"]
        # Simula serialización durable entre mensajes.
        estado = await repo.get_session("mecanico")
        await repo.save_session("mecanico", ConversationState.from_dict(estado.exportar_dict()))
    estado = await repo.get_session("mecanico")
    assert estado.obtener_valor_confirmado("escaner_disponible") == "SI"
    assert estado.obtener_valor_confirmado("temperatura") == "caliente"
    assert any("injectores" in h.valor for h in estado.hechos.values())
