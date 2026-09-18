import asyncio
import json
import sys
sys.path.insert(0, ".")

from src.application.services import GestorDiagnostico
from src.core.conversacion.orquestador_conversacion import OrquestadorConversacion
from src.core.conversacion.repositorio import InMemoryConversationRepository
from src.core.services.webhook_service import WebhookService

PROMPT_ARRANQUE = (
    "Hola, tengo un vehículo en el taller. El cliente comenta que demora bastante "
    "en encender por las mañanas. Una vez que logra encender, el motor funciona normal "
    "y no se prende ninguna luz de advertencia. Todavía no he revisado batería, "
    "arranque ni sistema de combustible. ¿Qué debería revisar primero?"
)

async def test_reproduccion():
    print("==================================================")
    print("12. REPRODUCCIÓN DIRECTA (PIPELINE 11.4)")
    print("==================================================")
    gestor = GestorDiagnostico()
    repo = InMemoryConversationRepository()
    orq = OrquestadorConversacion(repositorio=repo)

    res_direct = await orq.procesar_mensaje(
        session_id="reproduccion_directa_11_4",
        texto_usuario=PROMPT_ARRANQUE,
        gestor_diagnostico=gestor,
    )
    estado = res_direct["estado"]
    print("INPUT:", PROMPT_ARRANQUE)
    print("EXTRACTED_FACTS:")
    for f in estado.hechos.values():
        print(f"  - {f.campo}: {f.valor} ({f.estado.value}, {f.categoria})")
    print("ACTIVE_PROBLEM:", estado.active_problem_id)
    print("ESTADO_OPERATIVO:", estado.estado_operativo.value)
    from src.core.conversacion.suficiencia_informacion import EvaluadorSuficiencia
    score_suf, cats, es_suf, mot_suf = EvaluadorSuficiencia.evaluar(estado)
    print("SUFFICIENCY:")
    print("  - score_suficiencia:", score_suf)
    print("  - categorias_confirmadas:", cats)
    print("  - es_suficiente:", es_suf)
    print("  - motivo_suficiencia:", mot_suf)
    print("  - decision:", res_direct.get("decision"))
    print("  - motivo_decision:", res_direct.get("motivo_decision"))
    print("QUESTION_SELECTED:")
    print("  - intent:", res_direct.get("question_intent"))
    print("  - pregunta_final:", res_direct.get("pregunta_final"))
    print("SYNTHESIZED_QUERY:", res_direct.get("consulta_consolidada"))
    print("OUTPUT (respuesta_texto):")
    print(res_direct.get("respuesta_texto"))
    print()

    has_ralenti = "detenido en ralentí" in res_direct.get("respuesta_texto", "").lower()
    has_freno = "pedal de freno" in res_direct.get("respuesta_texto", "").lower()
    assert not has_ralenti and not has_freno, "FAIL: Reproducción directa produjo pregunta genérica"
    print("[PASS] Reproducción directa NO produjo la pregunta genérica ralentí/freno.")

    print("\n==================================================")
    print("13. REPRODUCCIÓN CONTRA HANDLER REAL (WebhookService)")
    print("==================================================")
    webhook_svc = WebhookService(gestor)
    res_webhook = await webhook_svc.procesar_mensaje(
        remitente="test_mecanico_local_51955095147",
        meta_message_id="test_meta_msg_11_4",
        tipo_mensaje="text",
        texto_cliente=PROMPT_ARRANQUE,
        placa="WAPP-01",
        marca_modelo="Vehiculo Generico",
        proveedor="meta",
        session_id="test_mecanico_local_51955095147",
        tipo_identificador="telefono",
        nombre_contacto="Juan Leon Mecanico",
    )
    print("WEBHOOK HANDLER STATUS:", res_webhook.get("status"))
    print("WEBHOOK HANDLER OUTPUT (respuesta):")
    resp_wh = res_webhook.get("respuesta", "") or res_webhook.get("mensaje", "") or str(res_webhook)
    print(resp_wh)

    wh_has_ralenti = "detenido en ralentí" in resp_wh.lower()
    wh_has_freno = "pedal de freno" in resp_wh.lower()
    if wh_has_ralenti or wh_has_freno:
        print("[FAIL] WebhookService produjo la pregunta genérica.")
    else:
        print("[PASS] WebhookService NO produjo la pregunta genérica.")

if __name__ == "__main__":
    asyncio.run(test_reproduccion())
