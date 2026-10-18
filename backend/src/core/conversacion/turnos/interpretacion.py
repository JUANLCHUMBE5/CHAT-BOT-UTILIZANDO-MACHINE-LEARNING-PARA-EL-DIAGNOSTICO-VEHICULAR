"""Etapa interpretacion; contexto por turno."""

from __future__ import annotations

import re
from importlib import import_module as _importar

from src.core.conversacion.extraccion_hechos.patrones_hechos import PATRON_CORRECCION_VEHICULO
from src.core.conversacion.extractor_hechos import ExtractorHechos
from src.core.conversacion.models import FactState, FactType
from src.core.logger import logger


async def interpretacion(self, turno):
    turno.interp_semantica = None
    try:
        turno.EstadoHechoSemantico = _importar(
            "src.core.conversacion.comprension_semantica"
        ).EstadoHechoSemantico
        turno.TipoHechoSemantico = _importar("src.core.conversacion.comprension_semantica").TipoHechoSemantico
        turno.interpretar_mensaje_usuario = _importar(
            "src.core.conversacion.comprension_semantica"
        ).interpretar_mensaje_usuario
        turno.interp_semantica = turno.interpretar_mensaje_usuario(
            turno.texto_limpio, contexto_estado=turno.estado
        )
        if turno.interp_semantica and turno.interp_semantica.datos_vehiculo:
            if not turno.estado.marca and turno.interp_semantica.datos_vehiculo.get("marca"):
                turno.estado.marca = turno.interp_semantica.datos_vehiculo["marca"]
                turno.estado.registrar_hecho(
                    "marca",
                    turno.estado.marca,
                    categoria="vehiculo",
                    tipo=FactType.CONDICION,
                    texto_crudo=turno.texto_limpio,
                )
            if not turno.estado.modelo and turno.interp_semantica.datos_vehiculo.get("modelo"):
                turno.estado.modelo = turno.interp_semantica.datos_vehiculo["modelo"]
                turno.estado.registrar_hecho(
                    "modelo",
                    turno.estado.modelo,
                    categoria="vehiculo",
                    tipo=FactType.CONDICION,
                    texto_crudo=turno.texto_limpio,
                )
            if not turno.estado.anio and turno.interp_semantica.datos_vehiculo.get("anio"):
                turno.estado.anio = str(turno.interp_semantica.datos_vehiculo["anio"])
                turno.estado.registrar_hecho(
                    "anio",
                    turno.estado.anio,
                    categoria="vehiculo",
                    tipo=FactType.CONDICION,
                    texto_crudo=turno.texto_limpio,
                )
            if not turno.estado.placa and turno.interp_semantica.datos_vehiculo.get("placa"):
                turno.estado.placa = turno.interp_semantica.datos_vehiculo["placa"]
                turno.estado.registrar_hecho(
                    "placa",
                    turno.estado.placa,
                    categoria="vehiculo",
                    tipo=FactType.CONDICION,
                    texto_crudo=turno.texto_limpio,
                )
        if turno.interp_semantica:
            for turno.hs in turno.interp_semantica.hechos_nuevos:
                if turno.hs.estado == turno.EstadoHechoSemantico.NO_REVISADO:
                    turno.estado.registrar_hecho(
                        campo=turno.hs.campo,
                        valor=turno.hs.valor,
                        categoria="inspeccion_pendiente",
                        estado=FactState.NO_REVISADO,
                        texto_crudo=turno.hs.evidencia_texto,
                        tipo=FactType.CONDICION,
                    )
                elif turno.hs.estado == turno.EstadoHechoSemantico.REEMPLAZADO:
                    turno.estado.registrar_hecho(
                        campo=turno.hs.campo,
                        valor=turno.hs.valor,
                        categoria="componente_reemplazado",
                        estado=FactState.CONFIRMADO,
                        texto_crudo=turno.hs.evidencia_texto,
                        tipo=FactType.CONDICION,
                    )
                elif turno.hs.estado == turno.EstadoHechoSemantico.DESCARTADO:
                    turno.estado.registrar_hecho(
                        campo=turno.hs.campo,
                        valor=turno.hs.valor,
                        categoria="componente_descartado",
                        estado=FactState.CONFIRMADO,
                        texto_crudo=turno.hs.evidencia_texto,
                        tipo=FactType.CAUSA,
                    )
                    if turno.hs.campo not in turno.estado.hipotesis_descartadas:
                        turno.estado.hipotesis_descartadas.append(turno.hs.campo)
                elif turno.hs.estado == turno.EstadoHechoSemantico.AUSENTE_NEGADO:
                    turno.estado.registrar_hecho(
                        campo=turno.hs.campo,
                        valor=turno.hs.valor,
                        categoria="sintoma",
                        estado=FactState.AUSENTE_NEGADO,
                        texto_crudo=turno.hs.evidencia_texto,
                        tipo=FactType.SINTOMA,
                    )
                elif turno.hs.tipo == turno.TipoHechoSemantico.CONDICION:
                    turno.estado.registrar_hecho(
                        campo=turno.hs.campo,
                        valor=turno.hs.valor,
                        categoria="condicion",
                        estado=FactState.CONFIRMADO,
                        texto_crudo=turno.hs.evidencia_texto,
                        tipo=FactType.CONDICION,
                    )
                elif turno.hs.tipo == turno.TipoHechoSemantico.SINTOMA:
                    if turno.hs.valor and turno.hs.valor not in turno.estado.active_symptoms:
                        turno.estado.active_symptoms.append(turno.hs.valor)
                    turno.estado.registrar_hecho(
                        campo=turno.hs.campo,
                        valor=turno.hs.valor,
                        categoria="sintoma",
                        estado=FactState.CONFIRMADO,
                        texto_crudo=turno.hs.evidencia_texto,
                        tipo=FactType.SINTOMA,
                    )
    except Exception as exc:
        turno.exc = exc
        logger.warning(f"[OrquestadorConversacion] Error no bloqueante en comprensión semántica: {turno.exc}")
    turno.estado_previo_hechos = dict(turno.estado.hechos)
    turno.hechos_extraidos = ExtractorHechos.extraer_y_actualizar(turno.estado, turno.texto_limpio)
    turno.registrar_evidencia = _importar("src.core.conversacion.evidencia_taller").registrar_evidencia
    turno.hechos_extraidos.extend(turno.registrar_evidencia(turno.estado, turno.texto_limpio))
    if turno.interpretacion_corta and "hecho" in turno.interpretacion_corta:
        turno.hechos_extraidos.append(turno.interpretacion_corta["hecho"])
    if turno.texto_limpio not in turno.estado.historial_mensajes_usuario:
        turno.estado.historial_mensajes_usuario.append(turno.texto_limpio)
    turno.resolver_sistema_activo = _importar(
        "src.core.diagnostico.enrutador_sistema"
    ).resolver_sistema_activo
    turno.texto_ruteo = turno.texto_limpio
    if turno.estado.active_system == "ambiguo":
        turno.texto_ruteo = " ".join(turno.estado.historial_mensajes_usuario[-2:])
    turno.estado.active_system = turno.resolver_sistema_activo(turno.texto_ruteo, turno.estado.active_system)
    turno.registrar_revision_mezcla = _importar(
        "src.core.conversacion.revision_mezcla"
    ).registrar_revision_mezcla
    turno.revision_mezcla = turno.registrar_revision_mezcla(turno.estado, turno.texto_limpio)
    if turno.revision_mezcla:
        turno.hechos_extraidos.append(turno.revision_mezcla)
        if turno.interpretacion_corta and turno.interpretacion_corta.get("categoria_respuesta") in (
            "REVISION_AMBIGUA",
            "DIAGNOSTICO_DESCARTADO",
        ):
            turno.interpretacion_corta = None
    turno.es_no_sintoma = bool(
        turno.texto_limpio.strip().startswith("¿")
        or PATRON_CORRECCION_VEHICULO.search(turno.texto_limpio)
        or getattr(turno.estado, "turno_ultima_correccion", None) == turno.estado.turno_actual
        or re.fullmatch(
            "\\s*(?:gasolina|di[eé]sel|petr[oó]leo|glp|gnv|nafta)\\s*", turno.texto_limpio, re.IGNORECASE
        )
        or re.search(
            "^\\s*(?:no\\s+tengo|no\\s+dispongo|no\\s+cuento|no\\s+poseo)\\b",
            turno.texto_limpio,
            re.IGNORECASE,
        )
        or ExtractorHechos.es_saludo(turno.texto_limpio)
        or bool(
            re.search(
                "\\b(?:muchas\\s+gracias|gracias|perfecto|excelente|qued[oó]\\s+clar[ií]simo)\\b",
                turno.texto_limpio,
                re.IGNORECASE,
            )
        )
    )
    turno.hay_sintoma_en_hechos = any(
        (
            isinstance(h, dict)
            and (h.get("categoria") == "sintoma" or h.get("tipo") in (FactType.SINTOMA, "SINTOMA"))
            for h in turno.hechos_extraidos
        )
    )
    if (
        turno.hay_sintoma_en_hechos
        or (not turno.es_no_sintoma and ExtractorHechos.contiene_informacion_diagnostica(turno.texto_limpio))
    ) and turno.texto_limpio not in turno.estado.active_symptoms:
        turno.estado.active_symptoms.append(turno.texto_limpio)
    turno.es_evidencia_duplicada = False
    if turno.hechos_extraidos and turno.estado.top3_actual:
        turno.campos_eval = [
            h.get("campo") for h in turno.hechos_extraidos if isinstance(h, dict) and "campo" in h
        ]
        if turno.campos_eval and all(
            (
                c in turno.estado_previo_hechos
                and turno.estado_previo_hechos[c].valor == getattr(turno.estado.hechos.get(c), "valor", None)
                for c in turno.campos_eval
            )
        ):
            turno.es_evidencia_duplicada = True
