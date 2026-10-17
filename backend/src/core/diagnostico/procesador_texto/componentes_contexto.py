"""Señales técnicas que permiten omitir aclaraciones genéricas de combustible."""

from src.core.logger import logger
from src.core.security import anonimizar_identificador


def registrar_recepcion(texto_normalizado, placa, session_id, proveedor):
    placa_anonima = anonimizar_identificador(placa or "")
    session_id_anon = anonimizar_identificador(session_id or "")
    logger.info(
        f"Procesando consulta texto (Longitud: {len(texto_normalizado)} caracteres) | "
        f"Placa Anonimizada: {placa_anonima} | Session ID Anonimizado: {session_id_anon} | Proveedor: {proveedor}"
    )


def tiene_componente_tecnico(texto_evaluar: str) -> bool:
    texto_l = texto_evaluar.lower()
    return any(
        c in texto_l
        for c in (
            "bobina", "bujia", "bujía", "inyector", "sensor", "valvula", "válvula",
            "compresion", "compresión", "bomba de gasolina", "bomba de combustible",
            "cables de bujia", "distribuidor", "catalizador", "egr", "maf", "map", "cilindro",
            "presion de combustible", "presión de combustible", "la bomba", "manometro", "manómetro",
            "cae fuerte", "aforador", "tanque casi vacio", "tanque casi vacío",
            "parpadea", "destella", "misfire", "tps", "cuerpo de aceleracion", "cuerpo de aceleración",
            "mariposa", "iac", "turbo", "intercooler", "dpf", "adblue", "fap",
            "ecu", "computadora", "alternador", "bateria", "batería",
            "cascabelea", "cascabeleo", "preignicion", "preignición",
        )
    )
