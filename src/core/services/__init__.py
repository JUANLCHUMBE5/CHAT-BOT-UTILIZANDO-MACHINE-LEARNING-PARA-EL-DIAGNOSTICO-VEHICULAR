"""Servicios de aplicación y orquestación del dominio CarBot.

Los servicios no se importan de forma ansiosa para evitar ciclos entre el
worker de colas y el orquestador del webhook.
"""

__all__: list[str] = []
