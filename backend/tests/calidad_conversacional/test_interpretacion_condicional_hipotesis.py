# -*- coding: utf-8 -*-
"""Pruebas unitarias e integrales para interpretacion condicional vs comprobaciones reales."""

import pytest
from src.core.conversacion.models import ConversationState, FactState, FactType
from src.core.conversacion.extraccion_hechos.actualizador_estado import extraer_y_actualizar
from src.core.conversacion.clasificador_mensajes import clasificar_mensaje


class TestInterpretacionCondicionalYHipotetica:
    """Valida que CarBot no confunda hipotesis o suposiciones con comprobaciones fisicas."""

    def test_pregunta_hipotetica_bomba_no_descarta(self):
        estado = ConversationState(session_id="test_hip_1")
        texto = "¿Qué otra cosa podría ser si la bomba está bien?"
        extraer_y_actualizar(estado, texto)

        # No debe agregarse a hipotesis descartadas
        assert "componente:bomba_combustible" not in estado.hipotesis_descartadas
        # No debe haber hecho de comprobacion fisica confirmada
        assert "componente_comprobado_bomba_combustible" not in estado.hechos

    def test_condicional_si_la_bomba_esta_bien_que_reviso(self):
        estado = ConversationState(session_id="test_hip_2")
        texto = "Si la bomba de gasolina está bien, ¿qué más reviso?"
        extraer_y_actualizar(estado, texto)

        assert "componente:bomba_combustible" not in estado.hipotesis_descartadas
        assert "componente_comprobado_bomba_combustible" not in estado.hechos

    def test_suponiendo_que_bomba_este_bien(self):
        estado = ConversationState(session_id="test_hip_3")
        texto = "Suponiendo que la bomba esté bien, ¿por qué no enciende?"
        extraer_y_actualizar(estado, texto)

        assert "componente:bomba_combustible" not in estado.hipotesis_descartadas
        assert "componente_comprobado_bomba_combustible" not in estado.hechos

    def test_duda_no_se_si_bomba_esta_bien(self):
        estado = ConversationState(session_id="test_hip_4")
        texto = "No sé si la bomba de gasolina está bien"
        extraer_y_actualizar(estado, texto)

        assert "componente:bomba_combustible" not in estado.hipotesis_descartadas
        assert "componente_comprobado_bomba_combustible" not in estado.hechos

    def test_comprobacion_fisica_real_si_descarta_y_confirma(self):
        estado = ConversationState(session_id="test_real_1")
        texto = "Revisé la bomba de gasolina y está bien"
        extraer_y_actualizar(estado, texto)

        assert "componente:bomba_combustible" in estado.hipotesis_descartadas
        assert "componente_comprobado_bomba_combustible" in estado.hechos
        hecho = estado.hechos["componente_comprobado_bomba_combustible"]
        assert hecho.estado == FactState.CONFIRMADO

    def test_comprobacion_real_con_presion(self):
        estado = ConversationState(session_id="test_real_2")
        texto = "La bomba de gasolina está bien, ya medí 45 psi"
        extraer_y_actualizar(estado, texto)

        assert "componente:bomba_combustible" in estado.hipotesis_descartadas
        assert "componente_comprobado_bomba_combustible" in estado.hechos

    def test_respuesta_afirmativa_con_coma(self):
        estado = ConversationState(session_id="test_real_3")
        texto = "Sí, la bomba de gasolina está bien"
        extraer_y_actualizar(estado, texto)

        assert "componente:bomba_combustible" in estado.hipotesis_descartadas
        assert "componente_comprobado_bomba_combustible" in estado.hechos

    def test_descarte_explicito_sin_comprobacion_fisica(self):
        estado = ConversationState(session_id="test_desc_1")
        texto = "Descarté la bomba de gasolina"
        extraer_y_actualizar(estado, texto)

        assert "componente:bomba_combustible" in estado.hipotesis_descartadas
        assert "componente_comprobado_bomba_combustible" not in estado.hechos
        assert "rechazo_usuario_bomba_combustible" in estado.hechos
        assert estado.hechos["rechazo_usuario_bomba_combustible"].estado == FactState.AMBIGUO

    def test_negacion_de_revision(self):
        estado = ConversationState(session_id="test_neg_1")
        texto = "No he revisado la bomba de gasolina"
        extraer_y_actualizar(estado, texto)

        assert "componente:bomba_combustible" not in estado.hipotesis_descartadas
        assert "componente_comprobado_bomba_combustible" not in estado.hechos

    def test_frase_mixta_comprobacion_real_y_pregunta_hipotetica(self):
        """Comprobacion real de inyectores junto a pregunta condicional sobre la bomba."""
        estado = ConversationState(session_id="test_mix_1")
        texto = "Revisé los inyectores y están bien, pero ¿qué otra cosa podría ser si la bomba de gasolina está bien?"
        extraer_y_actualizar(estado, texto)

        # Inyectores: comprobados y descartados
        assert "componente:inyector" in estado.hipotesis_descartadas
        assert "componente_comprobado_inyector" in estado.hechos
        assert estado.hechos["componente_comprobado_inyector"].estado == FactState.CONFIRMADO

        # Bomba: condicional e hipotetica -> NO debe descartarse ni confirmarse fisicamente
        assert "componente:bomba_combustible" not in estado.hipotesis_descartadas
        assert "componente_comprobado_bomba_combustible" not in estado.hechos

    def test_clasificador_no_clasifica_hipotetica_como_descarte(self):
        estado = ConversationState(session_id="test_clasif_1")
        texto = "¿Qué otra cosa podría ser si la bomba está bien?"
        tipo = clasificar_mensaje(texto, estado)
        assert tipo != "descarte"

    def test_multiturno_conversacion_pregunta_hipotetica(self):
        """Valida que en una conversacion multiturno con GestorDiagnostico, una pregunta hipotetica no descarte componentes."""
        from src.core.gestor_diagnostico import GestorDiagnostico
        gestor = GestorDiagnostico()
        sid = "test_multi_hip_e2e"

        # Turno 1: Falla inicial
        r1 = gestor.procesar_consulta_texto("Toyota Corolla 2012 le doy arranque pero no prende", session_id=sid, proveedor="web")
        sesion = gestor.session_manager.obtener_sesion(sid)
        assert sesion.conversation_state.marca == "Toyota"
        assert sesion.conversation_state.modelo == "Corolla"

        # Turno 2: Pregunta exploratoria hipotetica
        r2 = gestor.procesar_consulta_texto("¿Qué otra cosa podría ser si la bomba de gasolina está bien?", session_id=sid, proveedor="web")
        sesion = gestor.session_manager.obtener_sesion(sid)
        # La bomba de combustible NO debe haber sido descartada
        assert "componente:bomba_combustible" not in sesion.conversation_state.hipotesis_descartadas
        assert "componente_comprobado_bomba_combustible" not in sesion.conversation_state.hechos

        # Turno 3: Comprobacion fisica real
        r3 = gestor.procesar_consulta_texto("Ya revisé las bujías y dan buena chispa", session_id=sid, proveedor="web")
        sesion = gestor.session_manager.obtener_sesion(sid)
        assert "componente:bujia" in sesion.conversation_state.hipotesis_descartadas
        assert "componente_comprobado_bujia" in sesion.conversation_state.hechos
