"""Sintetizador de consultas diagnósticas clínicas consolidadas para el pipeline ML + RAG."""

from __future__ import annotations

import re
from typing import List

from src.core.conversacion.models import ConversationState, FactState


def _retirar_condicion_obsoleta(texto: str, temperatura_confirmada: str | None) -> str:
    """Evita que una frase histórica contradiga la corrección estructurada del mecánico."""
    if temperatura_confirmada == "caliente":
        texto = re.sub(r"\b(?:cuando\s+est[aá]\s+)?fr[ií]o\b", "", texto, flags=re.IGNORECASE)
    elif temperatura_confirmada == "frío":
        texto = re.sub(r"\b(?:cuando\s+est[aá]\s+)?caliente\b", "", texto, flags=re.IGNORECASE)
    return re.sub(r"\s+", " ", texto).strip()


class SintetizadorConsulta:
    """Reconstruye una consulta diagnóstica limpia a partir de hechos estructurados confirmados."""

    @classmethod
    def sintetizar(cls, estado: ConversationState) -> str:
        """Construye un texto diagnóstico coherente y representativo sin concatenaciones ciegas."""
        partes: List[str] = []

        # 1. Identificación del vehículo
        vehiculo_tokens = []
        if estado.marca:
            vehiculo_tokens.append(estado.marca)
        if estado.modelo:
            vehiculo_tokens.append(estado.modelo)
        if estado.anio:
            vehiculo_tokens.append(f"año {estado.anio}")
        if estado.motor:
            vehiculo_tokens.append(f"motor {estado.motor}")
        if estado.combustible:
            vehiculo_tokens.append(f"a {estado.combustible}")
        if estado.transmision:
            vehiculo_tokens.append(f"transmisión {estado.transmision}")

        if vehiculo_tokens:
            partes.append(" ".join(vehiculo_tokens))

        # 2. Síntomas clínicos confirmados
        sintomas_confirmados = []
        vistos_sintomas = set()
        for h in estado.hechos.values():
            if h.categoria == "sintoma" and h.estado == FactState.CONFIRMADO:
                v = str(h.valor).strip()
                # Omitir banderas binarias crudas como "SI" o "TRUE" registradas como síntoma
                if v.upper() in ("SI", "SÍ", "TRUE", "1", "NO", "FALSE", "0"):
                    continue
                # Normalizar redundancia en síntomas de climatización
                if "climatización" in v.lower() or "aire acondicionado no enfría" in v.lower():
                    v = "aire acondicionado no enfría / sale aire caliente"
                if v not in vistos_sintomas:
                    vistos_sintomas.add(v)
                    sintomas_confirmados.append(v)

        temp = estado.obtener_valor_confirmado("temperatura")

        if sintomas_confirmados:
            sintomas_str = ", ".join(sintomas_confirmados)
            partes.append(f"presenta {sintomas_str}")
        elif estado.historial_mensajes_usuario:
            msg_base = _retirar_condicion_obsoleta(estado.historial_mensajes_usuario[0], temp)
            if msg_base:
                partes.append(msg_base)

        # 2b. Ubicación del síntoma
        ubica = estado.obtener_valor_confirmado("ubicacion_sintoma")
        if ubica:
            partes.append(ubica)

        # 3. Condición de operación / disparador
        condicion = estado.obtener_valor_confirmado("condicion_operacion")
        if condicion:
            if condicion.lower().startswith(("al ", "en ", "deja ", "cuando ")):
                partes.append(condicion)
            else:
                partes.append(f"cuando está {condicion}")

        # 3b. Condición de velocidad
        vel = estado.obtener_valor_confirmado("condicion_velocidad")
        if vel:
            partes.append(vel)

        # 3c. Comportamiento de arranque / giro motor
        giro = estado.obtener_valor_confirmado("giro_motor")
        if giro:
            partes.append(f"el motor {giro}")

        # 4. Condición de temperatura
        if temp:
            partes.append(f"ocurre en {temp}")

        # 5. Hechos negativos relevantes de polaridad clínica
        falla_sin_freno = estado.obtener_hecho("falla_sin_frenar")
        if falla_sin_freno and falla_sin_freno.estado == FactState.AUSENTE_NEGADO:
            partes.append("sin frenar no vibra")
        vib_pedal = estado.obtener_hecho("vibracion_pedal")
        if vib_pedal and vib_pedal.estado == FactState.AUSENTE_NEGADO:
            partes.append("en pedal casi no siente vibración")
        vib_carroc = estado.obtener_hecho("vibracion_carroceria")
        if vib_carroc and vib_carroc.estado == FactState.AUSENTE_NEGADO:
            partes.append("resto del vehículo no vibra")
        func_mot = estado.obtener_hecho("funcionamiento_motor")
        if func_mot:
            partes.append("una vez que logra encender el motor funciona normal")
        testigo = estado.obtener_hecho("sintoma_testigo_check_engine")
        if testigo and testigo.estado == FactState.AUSENTE_NEGADO:
            partes.append("sin testigos de advertencia en el tablero")

        # 6. Evolución y respuesta a acciones
        evol = estado.obtener_valor_confirmado("evolucion_accion")
        if evol:
            partes.append(evol)

        # 7. Códigos DTC confirmados
        dtcs = [
            h.valor for h in estado.hechos.values()
            if h.categoria == "dtc" and h.estado == FactState.CONFIRMADO
        ]
        if dtcs:
            partes.append(f"código de escáner {', '.join(dtcs)}")

        # 8. Mediciones técnicas confirmadas
        meds = [
            h.valor for campo, h in estado.hechos.items()
            if (
                h.categoria == "medicion"
                and h.estado == FactState.CONFIRMADO
                and campo not in {"valor_medicion", "unidad_medicion", "condicion_medicion"}
            )
        ]
        if meds:
            partes.append(f"medición/evidencia técnica {', '.join(meds)}")

        # 8.1 Modificadores ambientales o eléctricos
        mods = [
            h.valor for h in estado.hechos.values()
            if h.categoria == "modificador" and h.estado == FactState.CONFIRMADO
        ]
        if mods:
            # Si la queja ya es de climatización, omitir modificador redundante de A/C
            if any("aire acondicionado" in str(s).lower() or "climatizac" in str(s).lower() for s in sintomas_confirmados):
                mods = [m for m in mods if "A/C" not in str(m)]
            if mods:
                partes.append(f"con {', '.join(mods)}")

        # 9. Antecedentes y componentes descartados
        descartes = [
            h.valor for h in estado.hechos.values()
            if h.categoria in (
                "componente_descartado",
                "componente_comprobado",
                "componente_reemplazado",
                "antecedente",
                "verificacion_fisica",
                "comprobacion_fisica",
            )
            and h.estado in (FactState.CONFIRMADO, FactState.DESCARTADO)
        ]
        if descartes:
            partes.append(f"antecedente: {', '.join(descartes)}")

        # 10. Inspecciones pendientes reportadas
        no_rev = [
            h.valor for h in estado.hechos.values()
            if h.estado == FactState.NO_REVISADO
        ]
        if no_rev:
            partes.append(f"pendiente revisar: {', '.join(no_rev)}")

        # 11. Pruebas, mediciones y correcciones aportadas durante la sesión.
        # Se incluyen explícitamente para que ML/LLM no pierdan una pista que el
        # extractor aún no haya normalizado a un campo conocido.
        if estado.completed_tests:
            resultados = ", ".join(
                f"{nombre}: {resultado}"
                for nombre, resultado in estado.completed_tests.items()
            )
            partes.append(f"pruebas ya realizadas (resultado reportado): {resultados}")

        if estado.measurements:
            mediciones = []
            for medicion in estado.measurements.values():
                if not isinstance(medicion, dict):
                    continue
                tipo = medicion.get("tipo", "medición")
                valor = medicion.get("valor", "")
                unidad = medicion.get("unidad", "")
                contexto = medicion.get("contexto")
                dato = f"{tipo}: {valor} {unidad}".strip()
                if contexto:
                    dato += f" ({contexto})"
                mediciones.append(dato)
            if mediciones:
                partes.append(f"mediciones reportadas: {', '.join(mediciones)}")

        if estado.hipotesis_descartadas:
            partes.append(
                "hipótesis descartadas explícitamente por el mecánico: "
                + ", ".join(estado.hipotesis_descartadas)
            )

        aportes_recientes = list(dict.fromkeys(
            _retirar_condicion_obsoleta(texto, temp)
            for texto in estado.historial_mensajes_usuario[-4:] if texto.strip()
        ))
        if aportes_recientes:
            partes.append(
                "últimos aportes textuales del mecánico (declaraciones, conservar su sentido): "
                + " | ".join(aportes_recientes)
            )

        # Si no hubo hechos estructurados, usar el último mensaje limpio como salvaguarda
        if not partes:
            if estado.historial_mensajes_usuario:
                return estado.historial_mensajes_usuario[-1].strip()
            return "Consulta vehicular técnica general"

        return ". ".join(partes).strip() + "."
