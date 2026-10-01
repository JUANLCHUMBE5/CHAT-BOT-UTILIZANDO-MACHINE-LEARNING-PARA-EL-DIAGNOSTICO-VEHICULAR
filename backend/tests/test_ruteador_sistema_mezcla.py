"""Regresiones de la secuencia real anonimizada: mezcla pobre e inyectores."""

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
    assert "inyector" in texto_final
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
