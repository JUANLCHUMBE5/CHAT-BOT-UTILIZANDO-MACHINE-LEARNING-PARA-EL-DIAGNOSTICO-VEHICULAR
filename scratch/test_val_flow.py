import asyncio
import sys

sys.path.insert(0, "backend")
from sqlalchemy import text
from src.core.services.webhook.validation_workflow import (
    ValidationWorkflow,
    interpretar_confirmacion_whatsapp,
    interpretar_respuesta_validacion_whatsapp,
)
from src.infrastructure.database.connection import obtener_sesion_db


async def test_val_flow():
    msg = '"Buenas, mi carro estaba normal hasta ayer. Hoy salí a la carretera y a los 20 minutos de manejar empecé a sentir que perdía fuerza, como que se ahogaba. Bajé la velocidad y se recuperó. Pero a los 5 minutos otra vez. Ya no puedo pasar de 80. ¿Qué será?'

    print("interpretar_respuesta_validacion_whatsapp:", interpretar_respuesta_validacion_whatsapp(msg))
    print("interpretar_confirmacion_whatsapp:", interpretar_confirmacion_whatsapp(msg))


asyncio.run(test_val_flow())
