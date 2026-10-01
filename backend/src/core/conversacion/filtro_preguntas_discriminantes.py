"""Filtro y formulador general de preguntas discriminantes post-descarte.

Garantiza que ninguna pregunta solicite hechos ya confirmados, negados o
suficientemente determinados en la memoria conversacional acumulada.
"""

from __future__ import annotations

from typing import Tuple

from src.core.conversacion.models import (
    ConversationState,
    DtcStatus,
    EstadoOperativo,
    FactState,
    QuestionIntent,
)


class FiltroPreguntasDiscriminantes:
    """Evalúa hechos acumulados y formula preguntas discriminantes sin redundancia."""

    @classmethod
    def es_condicion_operativa_conocida(cls, estado: ConversationState) -> bool:
        """Determina si la condición o régimen operativo del vehículo ya está confirmado o negado."""
        if estado.estado_operativo in (
            EstadoOperativo.ARRANQUE,
            EstadoOperativo.RALENTI,
            EstadoOperativo.MARCHA,
            EstadoOperativo.FRENADO,
            EstadoOperativo.ESTACIONADO,
        ):
            return True

        cond = estado.obtener_hecho("condicion_operacion")
        if cond and cond.estado in (FactState.CONFIRMADO, FactState.AUSENTE_NEGADO, FactState.CORREGIDO):
            return True

        for k, h in estado.hechos.items():
            if h.estado in (FactState.CONFIRMADO, FactState.AUSENTE_NEGADO, FactState.CORREGIDO):
                k_l = k.lower()
                v_l = str(h.valor).lower()
                if any(w in k_l or w in v_l for w in ("ralenti", "ralentí", "en_marcha", "acelerar", "frenado", "arranque")):
                    return True

        return estado.ya_preguntado(QuestionIntent.CONDICION_OPERACION)

    @classmethod
    def es_testigo_o_dtc_conocido(cls, estado: ConversationState) -> bool:
        """Determina si el estado de códigos DTC, testigo Check Engine o escáner ya está conocido."""
        if estado.dtc_status in (DtcStatus.DTC_OBSERVADO, DtcStatus.DTC_DESCONOCIDO):
            return True

        testigo = estado.obtener_hecho("sintoma_testigo_check_engine")
        if testigo and testigo.estado in (FactState.CONFIRMADO, FactState.AUSENTE_NEGADO, FactState.CORREGIDO):
            return True

        escaner = estado.obtener_hecho("escaner_disponible")
        if escaner is not None and escaner.estado in (FactState.CONFIRMADO, FactState.AUSENTE_NEGADO, FactState.NO_APLICA, FactState.CORREGIDO):
            return True

        for k, h in estado.hechos.items():
            if h.estado in (FactState.CONFIRMADO, FactState.AUSENTE_NEGADO, FactState.CORREGIDO):
                k_l = k.lower()
                v_l = str(h.valor).lower()
                if any(w in k_l or w in v_l for w in ("check_engine", "testigo", "dtc", "obd", "escaner", "escáner")):
                    return True

        return estado.ya_preguntado(QuestionIntent.CODIGO_DTC)

    @classmethod
    def es_sonido_humo_conocido(cls, estado: ConversationState) -> bool:
        """Determina si la presencia o ausencia de ruidos anómalos o humo ya fue determinada."""
        if estado.obtener_hecho("presencia_ruido") is not None or estado.obtener_hecho("ruido_arranque") is not None:
            return True

        for k, h in estado.hechos.items():
            if h.estado in (FactState.CONFIRMADO, FactState.AUSENTE_NEGADO, FactState.CORREGIDO):
                k_l = k.lower()
                v_l = str(h.valor).lower()
                if any(w in k_l or w in v_l for w in ("cascabeleo", "silbido", "chillido", "golpeteo", "humo", "ruido_metalico")):
                    return True

        return estado.ya_preguntado(QuestionIntent.PRESENCIA_RUIDO)

    @classmethod
    def es_arranque_conocido(cls, estado: ConversationState) -> Tuple[bool, bool]:
        """Retorna (giro_motor_conocido, luces_tablero_conocido)."""
        sabe_giro = estado.obtener_hecho("giro_motor") is not None or estado.obtener_hecho("ruido_arranque") is not None
        sabe_luces = estado.obtener_hecho("luces_se_atenuan") is not None
        return bool(sabe_giro), bool(sabe_luces)

    @classmethod
    def es_pregunta_ya_realizada(cls, texto: str, estado: ConversationState) -> bool:
        """Comprueba si una pregunta idéntica o semánticamente equivalente ya fue formulada."""
        t_norm = texto.strip().lower()
        for p in estado.preguntas_realizadas:
            p_txt = p.get("texto", "").strip().lower()
            if p_txt == t_norm:
                return True
        return False

    @classmethod
    def formular(
        cls,
        estado: ConversationState,
        falla_descartada: str,
    ) -> Tuple[str, QuestionIntent]:
        """
        Formula la pregunta técnica discriminante excluyendo cualquier información ya conocida.

        Regla General:
          HECHO YA CONFIRMADO -> NO REPREGUNTAR ESE HECHO.
          HECHO NEGADO -> NO REPREGUNTARLO sin contradicción.
          HECHO DESCONOCIDO -> PUEDE PREGUNTARSE si aporta discriminación.
        """
        es_arranque = (
            getattr(estado, "estado_operativo", None) == EstadoOperativo.ARRANQUE
            or any("arranc" in str(getattr(h, "valor", "")).lower() for h in estado.hechos.values() if getattr(h, "categoria", "") == "sintoma")
        )

        # Flujo de Arranque
        if es_arranque:
            sabe_giro, sabe_luces = cls.es_arranque_conocido(estado)
            if not sabe_giro:
                txt = "Al intentar dar arranque: ¿el motor gira con lentitud o desgano, o únicamente hace un clic seco sin que el motor gire en absoluto?"
                if not cls.es_pregunta_ya_realizada(txt, estado):
                    return txt, QuestionIntent.COMPORTAMIENTO_ARRANQUE
            if not sabe_luces:
                txt = "Al mantener la llave en posición de arranque: ¿las luces del tablero se atenúan fuertemente o se mantienen con brillo normal?"
                if not cls.es_pregunta_ya_realizada(txt, estado):
                    return txt, QuestionIntent.CAIDA_TENSION_ARRANQUE

            if "prueba_chispa" not in estado.completed_tests and estado.obtener_hecho("resultado_prueba_chispa") is None:
                txt = "¿Se ha verificado si salta chispa constante en las bujías al dar arranque?"
                return txt, QuestionIntent.COMPONENTE_REVISADO

            txt = "¿Has percibido si la bomba de combustible zumba al colocar la llave en contacto?"
            return txt, QuestionIntent.COMPONENTE_REVISADO

        # Flujo No-Arranque (Marcha, Ralentí, Frenado, Desconocido)
        sabe_condicion = cls.es_condicion_operativa_conocida(estado)
        sabe_testigo = cls.es_testigo_o_dtc_conocido(estado)
        sabe_sonido = cls.es_sonido_humo_conocido(estado)

        # Caso 1: Condición conocida (ralentí/marcha) Y Testigo conocido (Check Engine / DTC)
        # -> Excluir condición y excluir testigo. Conservar sólo síntomas desconocidos (sonido / humo).
        if sabe_condicion and sabe_testigo:
            if not sabe_sonido:
                txt = "¿Se detecta algún sonido (cascabeleo, silbido) o humo anormal cuando aparece la falla?"
                if not cls.es_pregunta_ya_realizada(txt, estado):
                    return txt, QuestionIntent.PRESENCIA_RUIDO

            # Si condición, testigo y sonido ya están determinados: preguntar por componente físico
            txt = "¿Has realizado alguna inspección física en componentes relacionados (como bujías, bobinas o mangueras de vacío)?"
            return txt, QuestionIntent.COMPONENTE_REVISADO

        # Caso 2: Condición conocida, pero Testigo/DTC DESCONOCIDO (Información parcial)
        # -> Excluir condición (NO preguntar por ralentí/marcha). Preguntar por testigo y/o sonido.
        if sabe_condicion and not sabe_testigo:
            if not sabe_sonido:
                txt = "¿Se detecta algún sonido (cascabeleo, silbido), humo o testigo encendido en el tablero?"
                if not cls.es_pregunta_ya_realizada(txt, estado):
                    return txt, QuestionIntent.CODIGO_DTC
            txt = "¿El tablero muestra encendido el testigo Check Engine o se ha conectado un escáner OBD-II?"
            return txt, QuestionIntent.CODIGO_DTC

        # Caso 3: Condición DESCONOCIDA, pero Testigo conocido
        # -> Excluir testigo (NO preguntar por Check Engine). Preguntar por condición y sonido.
        if not sabe_condicion and sabe_testigo:
            if not sabe_sonido:
                txt = "¿La falla se manifiesta con el motor en ralentí o bajo aceleración en marcha? ¿Se detecta algún sonido (cascabeleo, silbido) o humo anormal?"
                if not cls.es_pregunta_ya_realizada(txt, estado):
                    return txt, QuestionIntent.CONDICION_OPERACION
            txt = "¿La falla se manifiesta con el motor en ralentí o bajo aceleración en marcha?"
            return txt, QuestionIntent.CONDICION_OPERACION

        # Caso 4: Ni condición ni testigo conocidos
        txt = "¿La falla se manifiesta con el motor en ralentí o bajo aceleración en marcha? ¿Se detecta algún sonido (cascabeleo, silbido), humo o testigo encendido en el tablero?"
        return txt, QuestionIntent.CONDICION_OPERACION
