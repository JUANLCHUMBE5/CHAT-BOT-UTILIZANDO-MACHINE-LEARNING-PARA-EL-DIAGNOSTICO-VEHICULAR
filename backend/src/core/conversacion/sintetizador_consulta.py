"""Sintetizador de consultas diagnósticas clínicas consolidadas para el pipeline ML + RAG."""

from __future__ import annotations

import re
from typing import List

from src.core.conversacion.models import ConversationState, FactState


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
        if estado.combustible:
            vehiculo_tokens.append(f"a {estado.combustible}")

        if vehiculo_tokens:
            partes.append(" ".join(vehiculo_tokens))

        # 2. Síntomas clínicos confirmados
        sintomas_confirmados = []
        vistos_sintomas = set()
        for h in estado.hechos.values():
            if h.categoria == "sintoma" and h.estado == FactState.CONFIRMADO:
                v = h.valor
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
            msg_base = estado.historial_mensajes_usuario[0]
            if temp == "caliente":
                msg_base = re.sub(r"\b(?:cuando\s+est[aá]\s+)?fr[ií]o\b", "", msg_base, flags=re.IGNORECASE)
            elif temp == "frío":
                msg_base = re.sub(r"\b(?:cuando\s+est[aá]\s+)?caliente\b", "", msg_base, flags=re.IGNORECASE)
            msg_base = re.sub(r"\s+", " ", msg_base).strip()
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
            h.valor for h in estado.hechos.values()
            if h.categoria == "medicion" and h.estado == FactState.CONFIRMADO
        ]
        if meds:
            partes.append(f"medición {', '.join(meds)}")

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
            if h.categoria in ("componente_descartado", "antecedente") and h.estado == FactState.CONFIRMADO
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

        # Si no hubo hechos estructurados, usar el último mensaje limpio como salvaguarda
        if not partes:
            if estado.historial_mensajes_usuario:
                return estado.historial_mensajes_usuario[-1].strip()
            return "Consulta vehicular técnica general"

        return ". ".join(partes).strip() + "."
