"""Smoke de regresión ejecutable sin pytest ni servicios externos."""

import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock

from src.core.conversacion.models import ConversationState
from src.core.conversacion.orquestador_conversacion import OrquestadorConversacion
from src.core.conversacion.repositorio import InMemoryConversationRepository
from src.core.conversacion.revision_mezcla import registrar_revision_mezcla


class VersaContextAfterTrimRequestTest(unittest.IsolatedAsyncioTestCase):
    async def test_contexto_operativo_despues_de_pedir_trim_llega_a_ml(self):
        gestor = SimpleNamespace(
            session_manager=None,
            procesar_consulta_texto=MagicMock(
                return_value=SimpleNamespace(
                    diagnostico_ml="Mezcla pobre en sistema de admisión",
                    confianza_ml=0.42,
                    predicciones_ml=[
                        SimpleNamespace(falla="Mezcla pobre en sistema de admisión", probabilidad=0.42),
                    ],
                    contexto_manual="Procedimiento de inspección del sistema de admisión",
                    contexto_manual_verificado="",
                    titulo_manual="Inspección de admisión",
                    respuesta_texto="",
                    llm_usado=False,
                    respuesta_limitada=True,
                )
            ),
        )
        flujo = OrquestadorConversacion(InMemoryConversationRepository())
        session_id = "versa-contexto-medicion-local"

        inicial = await flujo.procesar_turno(
            session_id,
            "Se prende el check y arroja mezcla pobre",
            gestor,
            placa="REPLAY-VERSA",
            marca_modelo="Nissan Versa 2016",
            proveedor="replay_local",
        )
        self.assertIn("STFT/LTFT", inicial["respuesta_texto"])
        gestor.procesar_consulta_texto.assert_not_called()

        siguiente = await flujo.procesar_turno(
            session_id,
            "Al acelerar y en caliente",
            gestor,
            placa="REPLAY-VERSA",
            marca_modelo="Nissan Versa 2016",
            proveedor="replay_local",
        )

        gestor.procesar_consulta_texto.assert_called_once()
        self.assertEqual(siguiente["estado"].active_system, "combustible_admision")
        self.assertIn("mezcla pobre", siguiente["consulta_consolidada"].lower())
        self.assertIn("caliente", siguiente["consulta_consolidada"].lower())
        self.assertNotIn("pendiente de una medición objetiva", siguiente["respuesta_texto"].lower())

        maf = await flujo.procesar_turno(
            session_id,
            "El MAF da lecturas raras",
            gestor,
            placa="REPLAY-VERSA",
            marca_modelo="Nissan Versa 2016",
            proveedor="replay_local",
        )
        self.assertIn("MAF", maf["respuesta_texto"])

        afirmacion = await flujo.procesar_turno(
            session_id,
            "Sí",
            gestor,
            placa="REPLAY-VERSA",
            marca_modelo="Nissan Versa 2016",
            proveedor="replay_local",
        )
        self.assertIn("g/s", afirmacion["respuesta_texto"])
        self.assertEqual(afirmacion["estado"].active_system, "combustible_admision")

    async def test_cuerpo_sin_aceleracion_se_reconoce_como_revision_en_inyeccion(self):
        estado = ConversationState(
            session_id="versa-revision-cuerpo",
            active_system="combustible_admision",
        )
        hecho = registrar_revision_mezcla(estado, "Ya revisé el cuerpo y está bien")
        self.assertIsNotNone(hecho)
        self.assertIsNotNone(estado.obtener_hecho("revision_normal_cuerpo_aceleracion"))


if __name__ == "__main__":
    unittest.main()
