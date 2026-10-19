"""Proyección de mediciones con unidad inferida de la pregunta activa, sin límites OEM."""

import re
from decimal import Decimal, InvalidOperation


def mediciones_con_procedencia(estado):
    def campo(nombre, defecto):
        return estado.get(nombre, defecto) if isinstance(estado, dict) else getattr(estado, nombre, defecto)

    historia = campo("historial_mensajes_usuario", [])
    medidas = campo("measurements", {})
    numeros = set()
    for mensaje in historia:
        for token in re.findall(r"(?<!\w)-?\d+(?:[.,]\d+)?(?!\w)", str(mensaje)):
            try:
                numeros.add(Decimal(token.replace(",", ".")))
            except InvalidOperation:
                continue
    resultado = list(historia)
    for medida in medidas.values():
        try:
            valor = Decimal(str(medida["valor"]))
        except (KeyError, TypeError, InvalidOperation):
            continue
        unidad = medida.get("unidad")
        # La cifra debe existir en la entrada literal del caso actual. La unidad
        # procede de la medición estructurada y su pregunta, nunca del texto saliente.
        if valor.is_finite() and valor in numeros and unidad:
            resultado.append(f"Lectura reportada: {medida['valor']} {unidad}.")
    return resultado
