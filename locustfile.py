"""
Pruebas de carga y estrés con Locust para simular 50 mecánicos concurrentes consultando CarBot.
"""

from locust import HttpUser, task, between
import random
import uuid

CONSULTAS_MECANICOS = [
    "El pedal de freno se hunde hasta el fondo y rechina al frenar",
    "Chirrido metálico agudo cada vez que piso el freno a baja velocidad",
    "El carro no arranca por las mañanas solo suena un clic en el motor de arranque",
    "El motor vibra y tiembla fuerte en ralentí como si trabajara en 3 cilindros",
    "Tironea al acelerar a fondo y pierde potencia en subida",
    "Humo negro por el tubo de escape y alto consumo de gasolina",
    "Se siente olor a quemado y el motor patina al soltar el embrague",
    "La temperatura sube al máximo en tráfico y hierve el refrigerante",
    "Golpeteo seco en la rueda delantera derecha al pasar baches",
    "El testigo de batería se enciende en el tablero y las luces bajan de intensidad",
]


class MecanicoCarBotUser(HttpUser):
    wait_time = between(1, 3)

    @task(3)
    def consultar_diagnostico_webhook(self):
        """Simula una consulta técnica enviada por un mecánico mediante webhook."""
        consulta = random.choice(CONSULTAS_MECANICOS)
        phone = f"+51999{random.randint(100000, 999999)}"
        msg_id = f"wamid_locust_{uuid.uuid4().hex[:12]}"

        payload = {
            "object": "whatsapp_business_account",
            "entry": [{
                "id": "123456789",
                "changes": [{
                    "value": {
                        "messaging_product": "whatsapp",
                        "metadata": {
                            "display_phone_number": "51999999999",
                            "phone_number_id": "10001"
                        },
                        "contacts": [{"profile": {"name": "Mecanico Test"}, "wa_id": phone}],
                        "messages": [{
                            "from": phone,
                            "id": msg_id,
                            "timestamp": "1723000000",
                            "text": {"body": consulta},
                            "type": "text"
                        }]
                    },
                    "field": "messages"
                }]
            }]
        }
        self.client.post("/api/v1/webhook", json=payload)

    @task(1)
    def consultar_healthcheck(self):
        """Monitorea el endpoint de salud del microservicio."""
        self.client.get("/health")
