"""Prueba de carga segura; no suplanta webhooks ni envía WhatsApp real."""

from __future__ import annotations

import os
import random
import uuid

from locust import HttpUser, between, task

CONSULTAS = [
    "El pedal de freno se hunde hasta el fondo y rechina al frenar",
    "Chirrido metalico al pisar el freno a baja velocidad",
    "El carro no arranca y solo suena un clic",
    "El motor vibra fuerte en ralenti como si trabajara en tres cilindros",
    "Tironea al acelerar y pierde potencia en subida",
    "Humo negro y alto consumo de combustible",
    "El embrague patina al arrancar en primera",
    "La temperatura sube y hierve el refrigerante",
]


class MecanicoCarBotUser(HttpUser):
    wait_time = between(1, 3)
    token: str

    def on_start(self) -> None:
        usuario = os.getenv("LOCUST_AUTH_USERNAME", "")
        clave = os.getenv("LOCUST_AUTH_PASSWORD", "")
        if not usuario or not clave:
            raise RuntimeError("Defina LOCUST_AUTH_USERNAME y LOCUST_AUTH_PASSWORD.")
        with self.client.post(
            "/api/v1/auth/login",
            json={"username": usuario, "password": clave},
            name="POST /api/v1/auth/login",
            catch_response=True,
        ) as respuesta:
            if respuesta.status_code != 200:
                respuesta.failure(f"Login rechazo la carga: HTTP {respuesta.status_code}")
                raise RuntimeError("No fue posible autenticar Locust.")
            self.token = respuesta.json()["access_token"]

    @task(4)
    def diagnosticar(self) -> None:
        with self.client.post(
            "/api/v1/diagnostico/analizar",
            headers={"Authorization": f"Bearer {self.token}"},
            json={
                "sintoma": random.choice(CONSULTAS),
                "session_id": f"locust-{uuid.uuid4().hex}",
            },
            name="POST /api/v1/diagnostico/analizar",
            catch_response=True,
        ) as respuesta:
            if respuesta.status_code != 200:
                respuesta.failure(f"Diagnostico HTTP {respuesta.status_code}")
            elif "falla_predicha" not in respuesta.json():
                respuesta.failure("Respuesta sin falla_predicha")

    @task(1)
    def readiness(self) -> None:
        with self.client.get("/health/ready", catch_response=True) as respuesta:
            if respuesta.status_code != 200:
                respuesta.failure("Aplicacion no preparada")
