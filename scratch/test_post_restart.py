import asyncio
import sys
sys.path.insert(0, ".")

from src.application.services import GestorDiagnostico
from src.core.services.webhook_service import WebhookService

PROMPT_ARRANQUE = (
    "Hola, tengo un vehículo en el taller. El cliente comenta que demora bastante "
    "en encender por las mañanas. Una vez que logra encender, el motor funciona normal "
    "y no se prende ninguna luz de advertencia. Todavía no he revisado batería, "
    "arranque ni sistema de combustible. ¿Qué debería revisar primero?"
)

PROMPT_NUEVO_VEHICULO = (
    "Hola, tengo otro vehículo en el taller. El cliente indica que la temperatura del "
    "motor empieza a subir después de unos minutos manejando. También notó que está "
    "perdiendo líquido refrigerante por la parte delantera. Todavía no he revisado "
    "el vehículo ni sé exactamente de dónde viene la fuga. ¿Qué debería revisar primero?"
)

async def main():
    print("==================================================")
    print("TEST POST-RESTART 18: CASO ARRANQUE")
    print("==================================================")
    gestor = GestorDiagnostico()
    svc = WebhookService(gestor)

    # Juan Leon (51955095147) es el usuario tecnico real registrado
    test_phone = "51955095147"
    import time
    res1 = await svc.procesar_mensaje(
        remitente=test_phone,
        meta_message_id=f"msg_post_restart_{time.time_ns()}",
        tipo_mensaje="text",
        texto_cliente=PROMPT_ARRANQUE,
        placa="TST-01",
        marca_modelo="Vehiculo Test",
        proveedor="meta",
        session_id=test_phone,
        tipo_identificador="telefono",
        nombre_contacto="Juan Leon",
    )
    resp1 = res1.get("respuesta", "") or res1.get("mensaje", "") or str(res1)
    print("RESPUESTA 1:\n", resp1.encode('ascii', errors='replace').decode('ascii'))

    has_ralenti = "detenido en ralentí" in resp1.lower()
    has_freno = "pedal de freno" in resp1.lower()
    if has_ralenti or has_freno:
        print("[FAIL 18] Se devolvió la pregunta genérica de ralentí/freno!")
        sys.exit(1)
    else:
        print("[PASS 18] El caso arranque NO devolvió la pregunta genérica incompatible.")

    print("\n==================================================")
    print("TEST POST-RESTART 19: CASO NUEVO VEHICULO")
    print("==================================================")
    res2 = await svc.procesar_mensaje(
        remitente=test_phone,
        meta_message_id="msg_post_restart_02",
        tipo_mensaje="text",
        texto_cliente=PROMPT_NUEVO_VEHICULO,
        placa="TST-02",
        marca_modelo="Vehiculo Test 2",
        proveedor="meta",
        session_id=test_phone,
        tipo_identificador="telefono",
        nombre_contacto="Juan Leon",
    )
    resp2 = res2.get("respuesta", "") or res2.get("mensaje", "") or str(res2)
    print("RESPUESTA 2:\n", resp2.encode('ascii', errors='replace').decode('ascii'))

    has_loop_reinicio = "caso finalizado. he limpiado la memoria" in resp2.lower()
    if has_loop_reinicio:
        print("[FAIL 19] Entró en bucle de reinicio ('Caso finalizado...') en vez de procesar el nuevo vehículo!")
        sys.exit(1)
    else:
        print("[PASS 19] El nuevo vehículo fue consumido y procesado correctamente sin bucle de reinicio.")

if __name__ == "__main__":
    asyncio.run(main())
