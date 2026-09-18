import asyncio
import json
import sys
sys.path.insert(0, 'backend')
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

from unittest.mock import MagicMock
from src.core.gestor_diagnostico import GestorDiagnostico
from src.core.services.webhook.diagnostic_workflow import TechnicalDiagnosticWorkflow

async def main():
    gestor = GestorDiagnostico()
    
    # Mock de conversacion y usuario como los usa el webhook
    conv = MagicMock()
    conv.id = "parity-test-session-001"
    conv.contexto = {}
    
    usuario = MagicMock()
    usuario.id = "mecanico-001"
    usuario.taller_id = "taller-001"
    usuario.nombres = "Mecánico Test"
    
    texto = (
        "Buenas, mi carro tiene un problema. Ayer lo dejé estacionado en la calle y cuando "
        "volví en la noche ya no quiso arrancar. Le doy a la llave y hace como un clic seco, "
        "una sola vez, y nada más. Las luces del tablero sí prenden bien, y el radio también."
    )
    
    print("=== EJECUTANDO TechnicalDiagnosticWorkflow.preparar ===")
    res = await TechnicalDiagnosticWorkflow.preparar(
        gestor=gestor,
        conversacion=conv,
        usuario=usuario,
        remitente="51955095147",
        proveedor="meta",
        tipo_mensaje="text",
        texto_cliente=texto,
        audio_id="",
        placa="WAPP-01",
        marca_modelo="Vehiculo Generico",
    )
    
    print("\n--- RESULTADO WORKFLOW ---")
    print("Respuesta enviada:", res.dto.respuesta_texto)
    print("Diagnóstico ML / Intención:", res.dto.diagnostico_ml)
    print("Modo diagnóstico:", res.dto.modo_diagnostico)
    print("Duración ms:", res.duracion_ms)
    print("\n--- CONTEXTO PERSISTIDO EN CONVERSACION ---")
    cs = conv.contexto.get("conversation_state", {})
    print("Estado operativo en CS:", cs.get("estado_operativo"))
    print("Hechos guardados:", list(cs.get("hechos", {}).keys()))
    print("Preguntas realizadas:", [p.get("intent") for p in cs.get("preguntas_realizadas", [])])
    print("Texto última pregunta:", cs.get("preguntas_realizadas", [{}])[-1].get("texto") if cs.get("preguntas_realizadas") else None)
    if cs.get("trazabilidad"):
        tr = cs["trazabilidad"][-1]
        print("Versión orquestador:", tr.get("version_orquestador"))
        print("Candidatas:", tr.get("preguntas_candidatas"))
        print("Descartadas:")
        for d in tr.get("preguntas_descartadas", []):
            print("  -", d["intent"], ":", d["motivo"])

    print("\n=== TURNO 2: EL USUARIO RESPONDE 'SE APAGAN POR COMPLETO' ===")
    res2 = await TechnicalDiagnosticWorkflow.preparar(
        gestor=gestor,
        conversacion=conv,
        usuario=usuario,
        remitente="51955095147",
        proveedor="meta",
        tipo_mensaje="text",
        texto_cliente="se apagan por completo al dar arranque",
        audio_id="",
        placa="WAPP-01",
        marca_modelo="Vehiculo Generico",
    )
    print("Respuesta enviada T2:\n", res2.dto.respuesta_texto)
    print("Modo diagnóstico T2:", res2.dto.modo_diagnostico)

if __name__ == "__main__":
    asyncio.run(main())
