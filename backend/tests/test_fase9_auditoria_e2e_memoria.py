"""Suite de pruebas E2E y Auditoría Integral de Conversación Natural y Memoria Persistente (Fase 9).

Cubre:
- Objetivo 1: Comprensión natural de entradas (afirmaciones, negaciones, incertidumbre, jergas, ortografía).
- Objetivo 2: Memoria persistente y tolerancia a pausas temporales (30s a 24h, TTL 86,400s).
- Objetivo 3: Interrupciones ("espérame", "dame 10 minutos", "ya regresé", "seguimos").
- Objetivo 4: Preguntas diferenciadoras y parada oportuna de preguntas.
- Objetivo 5: Diferenciación entre usuario común y mecánico profesional (Corolla 1NZ, P0302, prueba cruzada).
- Resiliencia de sincronización DB si Redis está ausente o vacío.
"""

from __future__ import annotations

import time
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from src.core.conversacion.models import (
    ConversationPhase,
    ConversationState,
    DtcStatus,
    EstadoOperativo,
    FactState,
    QuestionIntent,
)
from src.core.conversacion.session_persistence import (
    persistir_sesion_en_almacenes,
    sincronizar_sesion_desde_persistencia,
)
from src.core.conversacion.respuestas_cortas.interprete_intenciones import (
    interpretar_respuesta_corta,
)
from src.core.conversacion.respuestas_cortas.patrones_deteccion import (
    es_respuesta_corta,
    PATRON_AMBIGUO,
    PATRON_NO_SE,
)
from src.core.conversacion.extraccion_hechos.comprobaciones_mecanicas import (
    extraer_comprobaciones_mecanicas,
)
from src.core.conversacion.orquestador.manejador_intenciones_especiales import (
    ManejadorIntencionesEspeciales,
)
from src.core.conversacion.generacion_preguntas.compatibilidad import (
    es_pregunta_compatible,
    puede_preguntar,
)
from src.core.session_manager import DiagnosticSession, SessionManager
from src.core.traductor_jerga import normalizar_jerga_peruana


# ==============================================================================
# OBJETIVO 1: COMPRENSIÓN NATURAL DE ENTRADAS (20 CASOS)
# ==============================================================================

@pytest.mark.parametrize(
    "texto_afirmacion",
    [
        "sí", "si", "si causa", "ajá", "así es", "correcto", "exactamente",
        "eso mismo", "afirmativo", "sí maestro", "claro que sí", "por supuesto",
    ],
)
def test_comprension_afirmaciones_naturales(texto_afirmacion: str):
    """Verifica que respuestas afirmativas directas o peruanas se interpreten como AFIRMACIÓN."""
    estado = ConversationState(session_id="test_afirmacion")
    estado.pending_question = {
        "texto": "¿El motor vibra intensamente al estar detenido en ralentí?",
        "intent": QuestionIntent.COMPORTAMIENTO_MOTOR.value,
    }
    estado.preguntas_realizadas.append({
        "texto": "¿El motor vibra intensamente al estar detenido en ralentí?",
        "intent": QuestionIntent.COMPORTAMIENTO_MOTOR.value,
    })
    res = interpretar_respuesta_corta(estado, texto_afirmacion)
    assert res is not None
    assert res["categoria_respuesta"] == "AFIRMACION"
    assert res["valor"] in ("sí", "si", "SI")


@pytest.mark.parametrize(
    "texto_negacion",
    [
        "no", "para nada", "negativo", "nunca", "eso no pasa",
        "ya revisé y está bien", "no maestro", "de ninguna manera",
    ],
)
def test_comprension_negaciones_naturales(texto_negacion: str):
    """Verifica que respuestas negativas directas o peruanas se interpreten como NEGACIÓN."""
    estado = ConversationState(session_id="test_negacion")
    estado.pending_question = {
        "texto": "¿La vibración ocurre únicamente al acelerar con fuerza en subidas?",
        "intent": QuestionIntent.CONDICION_OPERACION.value,
    }
    estado.preguntas_realizadas.append({
        "texto": "¿La vibración ocurre únicamente al acelerar con fuerza en subidas?",
        "intent": QuestionIntent.CONDICION_OPERACION.value,
    })
    res = interpretar_respuesta_corta(estado, texto_negacion)
    assert res is not None
    assert res["categoria_respuesta"] in ("NEGACION", "SINTOMA_DESCARTADO", "REVISION_AMBIGUA")
    assert res["valor"] in ("no", "NO", texto_negacion)


@pytest.mark.parametrize(
    "texto_incertidumbre",
    [
        "no sé", "creo que sí", "no estoy seguro", "puede ser",
        "tendría que revisar", "no tengo cómo comprobarlo", "ni idea",
    ],
)
def test_comprension_respuestas_inciertas(texto_incertidumbre: str):
    """Verifica que respuestas inciertas NO se conviertan en afirmaciones ni nieguen fallas erróneamente."""
    estado = ConversationState(session_id="test_incertidumbre")
    estado.pending_question = {
        "texto": "¿La temperatura sube en tráfico o en carretera?",
        "intent": QuestionIntent.TEMPERATURA_APARICION.value,
    }
    estado.preguntas_realizadas.append({
        "texto": "¿La temperatura sube en tráfico o en carretera?",
        "intent": QuestionIntent.TEMPERATURA_APARICION.value,
    })
    res = interpretar_respuesta_corta(estado, texto_incertidumbre)
    assert res is not None
    assert res["categoria_respuesta"] in ("DESCONOCIDO", "AMBIGUO", "NO_SABE_REALIZAR_PRUEBA")
    # Nunca debe ser confirmado como avería
    assert res.get("valor") not in ("SI", "sí", "si")


@pytest.mark.parametrize(
    "jerga, termino_esperado",
    [
        ("el carro se chupa en subida", "pierde potencia"),
        ("el motor cascabelea al acelerar", "preignicion"),
        ("el motor cabecea en mínimo", "vibracion e inestabilidad"),
        ("la llanta se amarra", "freno pegado"),
        ("el auto está chancho", "pierde potencia"),
        ("suena como lata al pasar baches", "ruido metalico o golpeteo suelto"),
        ("el motor está temblando feo", "vibracion excesiva e inestabilidad"),
    ],
)
def test_traduccion_jergas_peruanas(jerga: str, termino_esperado: str):
    """Verifica la traducción y normalización de expresiones automotrices peruanas."""
    traducido = normalizar_jerga_peruana(jerga)
    assert termino_esperado in traducido


@pytest.mark.parametrize(
    "error_tipeo, esperado",
    [
        ("el auto no aranca en la mañana", "no arranca"),
        ("frena malaso cuando piso el pedal", "frena muy mal"),
        ("suena cuado giro todo el timon", "suena cuando giro"),
        ("el motor se calienta muxo", "se calienta mucho"),
    ],
)
def test_normalizacion_ortografica(error_tipeo: str, esperado: str):
    """Verifica correcciones ortográficas y de dictado comunes en talleres y chat."""
    res = normalizar_jerga_peruana(error_tipeo)
    assert esperado in res


# ==============================================================================
# OBJETIVO 2: MEMORIA PERSISTENTE Y SALTOS DE TIEMPO (10 CASOS)
# ==============================================================================

@pytest.mark.parametrize(
    "pausa_segundos",
    [
        30,        # 30 segundos
        120,       # 2 minutos
        360,       # 6 minutos
        420,       # 7 minutos
        600,       # 10 minutos
        1800,      # 30 minutos
        3600,      # 1 hora
        14400,     # 4 horas
        43200,     # 12 horas
        82800,     # 23 horas
    ],
)
def test_memoria_no_expira_dentro_de_24_horas(pausa_segundos: int):
    """Verifica que pausas de hasta 23 horas conserven el caso íntegro en memoria y sesión."""
    ahora = time.time()
    t_creacion = ahora - pausa_segundos
    sesion = DiagnosticSession(session_id="test_ttl")
    sesion.updated_at = t_creacion
    
    # Dentro de 24h (86,400s) la sesión sigue vigente
    assert sesion.ha_expirado(ttl_segundos=86400) is False


def test_memoria_expira_despues_de_24_horas():
    """Verifica que después de 24 horas (86,401s), la sesión sea purgada limpiamente."""
    ahora = time.time()
    t_antiguo = ahora - 86401
    sesion = DiagnosticSession(session_id="test_expirada")
    sesion.updated_at = t_antiguo
    assert sesion.ha_expirado(ttl_segundos=86400) is True


@pytest.mark.asyncio
async def test_recuperacion_desde_postgres_si_redis_vacio():
    """Verifica que si Redis pierde la clave (flushall/reinicio), se recupere desde PostgreSQL."""
    session_id = "test_resiliencia_redis"
    estado_original = ConversationState(session_id=session_id)
    estado_original.placa = "ABC-123"
    estado_original.marca = "Toyota"
    estado_original.modelo = "Yaris"
    estado_original.falla_principal = "bomba_combustible"
    estado_original.registrar_hecho("presion_riel", "1.8 bar", categoria="medicion")

    gestor_mock = MagicMock()
    gestor_mock.session_manager = SessionManager(ttl_seconds=86400)

    contexto_db = {
        "case_id": estado_original.case_id,
        "conversation_state": estado_original.exportar_dict(),
    }

    with patch("src.core.conversacion.session_persistence.recuperar_contexto_sesion_redis", new_callable=AsyncMock) as mock_redis_ctx:
        mock_redis_ctx.return_value = None  # Simula Redis vacío o reiniciado

        recuperado = await sincronizar_sesion_desde_persistencia(
            gestor=gestor_mock,
            sesion_efectiva=session_id,
            contexto_db=contexto_db,
        )

        assert recuperado is True
        sesion_recup = gestor_mock.session_manager.obtener_sesion(session_id)
        assert sesion_recup is not None
        assert sesion_recup.conversation_state.placa == "ABC-123"
        assert sesion_recup.conversation_state.marca == "Toyota"
        assert sesion_recup.conversation_state.obtener_hecho("presion_riel").valor == "1.8 bar"


# ==============================================================================
# OBJETIVO 3: CONTINUIDAD REAL DEL DIAGNÓSTICO E INTERRUPCIONES (10 CASOS)
# ==============================================================================

@pytest.mark.parametrize(
    "frase_espera",
    [
        "espérame un rato",
        "espera un momento",
        "estoy revisando",
        "ahorita te digo",
        "dame 10 minutos",
        "reviso y te aviso",
        "un momento por favor",
    ],
)
@pytest.mark.asyncio
async def test_interrupcion_espera_no_borra_diagnostico(frase_espera: str):
    """Verifica que mensajes de espera no fuercen diagnósticos ni cambien la fase activa."""
    estado = ConversationState(session_id="test_pausa")
    estado.placa = "B7K-410"
    estado.falla_principal = "bobina_de_encendido"
    estado.pending_question = {"texto": "¿La chispa salta en todos los cilindros?", "intent": QuestionIntent.COMPONENTE_REVISADO.value}
    estado.fase = ConversationPhase.ACLARANDO

    repo_mock = MagicMock()
    repo_mock.save_session = AsyncMock()

    resp = await ManejadorIntencionesEspeciales.procesar_intencion_especial(
        estado=estado,
        texto_limpio=frase_espera,
        session_id="test_pausa",
        gestor_diagnostico=None,
        repositorio=repo_mock,
        t0=time.perf_counter(),
    )

    assert resp is not None
    assert resp["decision"] == "PAUSA_ESPERA"
    assert resp["status"] == "espera_usuario"
    assert resp["es_pregunta"] is False
    assert estado.fase == ConversationPhase.ACLARANDO
    assert estado.falla_principal == "bobina_de_encendido"
    assert estado.placa == "B7K-410"
    assert estado.pending_question is not None


@pytest.mark.parametrize(
    "frase_retoma",
    [
        "ya regresé",
        "seguimos",
        "continuemos donde quedamos",
        "ya estoy listo",
        "listo, continuemos",
    ],
)
@pytest.mark.asyncio
async def test_retoma_caso_recuerda_pregunta_pendiente(frase_retoma: str):
    """Verifica que al reanudar se recuerde el vehículo y la pregunta que quedó pendiente."""
    estado = ConversationState(session_id="test_retoma")
    estado.marca = "Toyota"
    estado.modelo = "Corolla"
    estado.falla_principal = "sensor_maf"
    estado.pending_question = {"texto": "¿El sensor MAF tiene voltaje de referencia de 5V?", "intent": QuestionIntent.MEDICION_VOLTAJE.value}

    repo_mock = MagicMock()
    repo_mock.save_session = AsyncMock()

    resp = await ManejadorIntencionesEspeciales.procesar_intencion_especial(
        estado=estado,
        texto_limpio=frase_retoma,
        session_id="test_retoma",
        gestor_diagnostico=None,
        repositorio=repo_mock,
        t0=time.perf_counter(),
    )

    assert resp is not None
    assert resp["decision"] == "RETOMA_DIAGNOSTICO"
    assert resp["status"] == "retoma_caso"
    assert resp["es_pregunta"] is True
    assert "Corolla" in resp["respuesta_texto"]
    assert "voltaje de referencia de 5V" in resp["respuesta_texto"]


# ==============================================================================
# OBJETIVO 4: PREGUNTAS INTELIGENTES Y PARADA OPORTUNA (10 CASOS)
# ==============================================================================

def test_parada_cuando_alcanza_max_repreguntas():
    """Verifica que el bot sepa cuándo dejar de preguntar y no formule preguntas infinitas."""
    estado = ConversationState(session_id="test_max_preguntas")
    estado.max_repreguntas = 3
    estado.turnos_repregunta = 3

    assert puede_preguntar(QuestionIntent.TEMPERATURA_APARICION, estado) is False
    assert puede_preguntar(QuestionIntent.CONDICION_OPERACION, estado) is False


def test_no_repetir_pregunta_identica():
    """Verifica que una pregunta idéntica formulada antes sea bloqueada."""
    estado = ConversationState(session_id="test_no_repetir")
    pregunta = "¿Has conectado un escáner automotriz OBD-II?"
    estado.preguntas_realizadas.append({"texto": pregunta, "intent": QuestionIntent.CODIGO_DTC.value})

    compatible, motivo = es_pregunta_compatible(QuestionIntent.CODIGO_DTC, pregunta, estado)
    assert compatible is False
    assert motivo == "PREGUNTA_REPETIDA"


def test_incompatibilidad_arranque_con_frenado():
    """Verifica que en contexto de falla de arranque no se formulen preguntas de frenado."""
    estado = ConversationState(session_id="test_incompatibilidad")
    estado.estado_operativo = EstadoOperativo.ARRANQUE

    compatible, motivo = es_pregunta_compatible(
        QuestionIntent.CONDICION_OPERACION,
        "¿La vibración se siente únicamente al pisar el freno en carretera?",
        estado,
    )
    assert compatible is False
    assert motivo in ("INCOMPATIBLE_ESTADO_OPERATIVO", "INTENT_YA_RESUELTO")


# ==============================================================================
# OBJETIVO 5: DIFERENCIAR MECÁNICO Y PROPIETARIO (10 CASOS)
# ==============================================================================

def test_caso_mecanico_corolla_1nz_p0302_prueba_cruzada():
    """Caso real de taller: Mecánico reporta Corolla 1NZ, P0302, bobina 2 intercambiada, persiste falla.
    
    CarBot debe:
    1. Registrar DTC P0302 sin volver a preguntar si tiene escáner.
    2. Reconocer la prueba cruzada de bobina 2.
    3. Descartar la bobina de encendido como causa raíz al persistir la falla.
    4. NO preguntar de nuevo si revisó la bobina ni si tiene DTC.
    """
    estado = ConversationState(session_id="test_mecanico_1nz")
    texto_mecanico = "Tengo un Toyota Corolla motor 1NZ, ralentí inestable, arroja DTC P0302. Ya intercambié la bobina 2 con la del cilindro 1 y la falla persiste en el cilindro 2."

    hechos = extraer_comprobaciones_mecanicas(estado, texto_mecanico, texto_mecanico.lower())
    assert any(h["campo"] == "prueba_intercambio_bobina" for h in hechos)
    
    # La bobina debe estar descartada
    assert any("bobina" in d for d in estado.hipotesis_descartadas)

    # Verificar que el generador de preguntas NO intente preguntar sobre bobina
    comp_bobina, motivo_b = es_pregunta_compatible(
        QuestionIntent.COMPONENTE_REVISADO,
        "¿Has probado intercambiar la bobina para ver si el fallo se traslada?",
        estado,
    )
    assert comp_bobina is False
    assert motivo_b in ("COMPONENTE_YA_DESCARTADO", "HECHO_YA_CONOCIDO")


def test_caso_piezas_ya_cambiadas_descarte_automatico():
    """Si el usuario reporta que ya cambió bujías y la falla continúa igual, se descartan bujías."""
    estado = ConversationState(session_id="test_piezas_cambiadas")
    texto = "Ya cambié las bujías y sigue la falla de tirones."

    hechos = extraer_comprobaciones_mecanicas(estado, texto, texto.lower())
    assert any("bujia" in d for d in estado.hipotesis_descartadas)

    # El generador de preguntas no debe insistir en comprobar bujías
    comp_bujia, motivo = es_pregunta_compatible(
        QuestionIntent.COMPONENTE_REVISADO,
        "¿Revisaste el estado y calibración de las bujías?",
        estado,
    )
    assert comp_bujia is False
    assert motivo in ("COMPONENTE_YA_DESCARTADO", "HECHO_YA_CONOCIDO")
