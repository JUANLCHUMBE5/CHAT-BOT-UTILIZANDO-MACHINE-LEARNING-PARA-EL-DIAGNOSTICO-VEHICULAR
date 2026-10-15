"""Extractor de hechos diagnósticos, detección de correcciones, modificadores y reinicio de casos.

Fachada modular y retrocompatible.
"""

from __future__ import annotations

from src.core.conversacion.extraccion_hechos import (
    PATRON_AFIRMACION_VEHICULAR,
    PATRON_ANIO,
    PATRON_ANTECEDENTE_MARCHA,
    PATRON_ANTECEDENTE_VEHICULAR,
    PATRON_CAUSAL_INYECCION,
    PATRON_CLIC_UNICO,
    PATRON_CLICS_REPETIDOS,
    PATRON_CORRECCION_EXPLICITA,
    PATRON_CORRECCION_VEHICULO,
    PATRON_DEMORA_ARRANQUE,
    PATRON_DTC,
    PATRON_GIRO_LLAVE,
    PATRON_HALLAZGO_MAF,
    PATRON_LUCES_ATENUAN,
    PATRON_MAP_FUERA_RANGO,
    PATRON_MEDICION,
    PATRON_MEZCLA_REPORTADA,
    PATRON_NEGACION_VEHICULAR,
    PATRON_NO_ARRANCA,
    PATRON_PLACA_EXPLICITA,
    PATRON_PLACA_FORMATO,
    PATRON_RADIO_PRENDE,
    PATRON_SENSOR_OXIGENO,
    PATRON_TABLERO_PRENDE,
    PATRONES_COMBUSTIBLE,
    PATRONES_MARCA,
    PATRONES_MODELO,
    PATRONES_REINICIO,
    PATRONES_SALUDO,
    PATRONES_SOLICITUD_DETALLE,
    clasificar_solicitud_caso,
    contiene_informacion_diagnostica,
    detectar_correcciones,
    es_cancelacion_solicitada,
    es_consulta_memoria,
    es_reinicio_solicitado,
    es_saludo,
    es_solicitud_detalle,
    extraer_placa,
    inferir_estado_operativo,
    registrar_rechazos_explicitos,
    seleccionar_entidad_vehicular,
)
from src.core.conversacion.extraccion_hechos import (
    extraer_y_actualizar as _extraer_y_actualizar,
)


def extraer_y_actualizar(estado, texto):
    """Expone los hechos finales del turno, sin positivos transitorios ya negados."""
    extraidos = _extraer_y_actualizar(estado, texto)
    resultado = []
    for item in extraidos:
        vigente = estado.hechos.get(item.get("campo"))
        if vigente is not None and vigente.to_dict() != item:
            continue
        if item.get("categoria") == "sintoma" and item.get("estado") == "AUSENTE_NEGADO":
            item = {**item, "categoria": "sintoma_negado"}
        resultado.append(item)
    return resultado


# Alias retrocompatibles
_seleccionar_entidad_vehicular = seleccionar_entidad_vehicular
_registrar_rechazos_explicitos = registrar_rechazos_explicitos


class ExtractorHechos:
    """Extrae hechos clínicos y gestiona correcciones, modificadores y reinicio conversacional."""

    PATRON_CORRECCION_EXPLICITA = PATRON_CORRECCION_EXPLICITA

    es_saludo = staticmethod(es_saludo)
    es_solicitud_detalle = staticmethod(es_solicitud_detalle)
    extraer_placa = classmethod(lambda cls, texto: extraer_placa(texto))
    es_reinicio_solicitado = staticmethod(es_reinicio_solicitado)
    es_cancelacion_solicitada = staticmethod(es_cancelacion_solicitada)
    es_consulta_memoria = staticmethod(es_consulta_memoria)
    clasificar_solicitud_caso = staticmethod(clasificar_solicitud_caso)
    contiene_informacion_diagnostica = staticmethod(contiene_informacion_diagnostica)
    detectar_correcciones = classmethod(lambda cls, texto: detectar_correcciones(texto))
    _registrar_rechazos_explicitos = staticmethod(registrar_rechazos_explicitos)
    extraer_y_actualizar = classmethod(lambda cls, estado, texto: extraer_y_actualizar(estado, texto))
    inferir_estado_operativo = classmethod(lambda cls, estado, texto: inferir_estado_operativo(estado, texto))


__all__ = [
    "ExtractorHechos",
    "PATRONES_COMBUSTIBLE",
    "PATRONES_MARCA",
    "PATRONES_MODELO",
    "PATRONES_REINICIO",
    "PATRONES_SALUDO",
    "PATRONES_SOLICITUD_DETALLE",
    "PATRON_AFIRMACION_VEHICULAR",
    "PATRON_ANIO",
    "PATRON_ANTECEDENTE_MARCHA",
    "PATRON_ANTECEDENTE_VEHICULAR",
    "PATRON_CAUSAL_INYECCION",
    "PATRON_CLIC_UNICO",
    "PATRON_CLICS_REPETIDOS",
    "PATRON_CORRECCION_EXPLICITA",
    "PATRON_CORRECCION_VEHICULO",
    "PATRON_DEMORA_ARRANQUE",
    "PATRON_DTC",
    "PATRON_GIRO_LLAVE",
    "PATRON_HALLAZGO_MAF",
    "PATRON_LUCES_ATENUAN",
    "PATRON_MAP_FUERA_RANGO",
    "PATRON_MEDICION",
    "PATRON_MEZCLA_REPORTADA",
    "PATRON_NEGACION_VEHICULAR",
    "PATRON_NO_ARRANCA",
    "PATRON_PLACA_EXPLICITA",
    "PATRON_PLACA_FORMATO",
    "PATRON_RADIO_PRENDE",
    "PATRON_SENSOR_OXIGENO",
    "PATRON_TABLERO_PRENDE",
    "_registrar_rechazos_explicitos",
    "_seleccionar_entidad_vehicular",
    "clasificar_solicitud_caso",
    "contiene_informacion_diagnostica",
    "detectar_correcciones",
    "es_cancelacion_solicitada",
    "es_reinicio_solicitado",
    "es_saludo",
    "es_solicitud_detalle",
    "extraer_placa",
    "extraer_y_actualizar",
    "inferir_estado_operativo",
    "registrar_rechazos_explicitos",
    "seleccionar_entidad_vehicular",
]
