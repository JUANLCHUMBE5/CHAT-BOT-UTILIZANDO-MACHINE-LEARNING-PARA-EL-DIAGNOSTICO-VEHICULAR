"""Rutas locales de prueba con contratos existentes."""
import re
import time
import uuid

from fastapi import APIRouter, Depends, HTTPException

from src.core.conversacion.extractor_hechos import ExtractorHechos
from src.core.conversacion.models import FactState
from src.core.conversacion.repositorio import InMemoryConversationRepository
from src.core.gestor_diagnostico import GestorDiagnostico

from .access import obtener_gestor, verificar_laboratorio_permitido
from .checks import _evaluar_comprobaciones
from .concurrency import turno_exclusivo
from .schemas import MensajeLabRequest, MensajeLabResponse

router = APIRouter()
_PATRON_SESSION_ID = re.compile(r"^[A-Za-z0-9_.:-]{1,80}$")

def _normalizar_session_id_lab(session_id: str) -> tuple[str, str]:
    limpio = (session_id or "").strip() or f"lab_{uuid.uuid4().hex[:8]}"
    if not _PATRON_SESSION_ID.fullmatch(limpio):
        raise HTTPException(
            status_code=400,
            detail="Identificador de sesión de laboratorio inválido.",
        )
    clave_interna = limpio if limpio.startswith("lab::") else f"lab::{limpio}"
    return limpio, clave_interna


@router.post("/mensaje", response_model=MensajeLabResponse, summary="Procesar turno en el orquestador real")
async def procesar_mensaje_laboratorio(
    req: MensajeLabRequest,
    _auth: None = Depends(verificar_laboratorio_permitido),
    gestor: GestorDiagnostico = Depends(obtener_gestor),
):
    """Ejecuta un mensaje de prueba sobre el motor de inferencia real de CarBot en sesión aislada."""
    _, session_key = _normalizar_session_id_lab(req.session_id)
    async with turno_exclusivo(gestor, session_key):
        return await _procesar_turno(req, gestor)


async def _procesar_turno(req: MensajeLabRequest, gestor: GestorDiagnostico):
    session_id_publico, session_key = _normalizar_session_id_lab(req.session_id)
    t0 = time.perf_counter()

    # Obtener o crear sesión aislada del laboratorio
    sesion = gestor.session_manager.obtener_o_crear_sesion(session_key)
    caso_previo_id = sesion.case_id
    sintomas_previos = [
        str(h.valor) for h in sesion.conversation_state.hechos.values()
        if h.categoria == "sintoma" and h.estado == FactState.CONFIRMADO
    ]

    # 1. Detección de cambio de caso / nuevo diagnóstico respetando negaciones y consultas de memoria
    es_cambio_caso = (
        ExtractorHechos.es_reinicio_solicitado(req.mensaje)
        and not ExtractorHechos.es_consulta_memoria(req.mensaje)
    )
    if es_cambio_caso:
        sesion.finalizar_caso(preservar_vehiculo=False)
        sintomas_previos = []

    estado_previo = sesion.conversation_state

    from src.core.conversacion.orquestador_conversacion import OrquestadorConversacion

    repo = getattr(gestor, "conversation_repo", None)
    if repo is None:
        repo = InMemoryConversationRepository()
        try:
            setattr(gestor, "conversation_repo", repo)
        except Exception:
            pass

    await repo.save_session(session_key, estado_previo)

    orquestador = OrquestadorConversacion(repositorio=repo)
    res_turno = await orquestador.procesar_turno(
        session_id=session_key,
        texto_usuario=req.mensaje,
        gestor_diagnostico=gestor,
        placa=sesion.placa or estado_previo.placa or "",
        marca_modelo=sesion.marca_modelo or "",
        proveedor="laboratorio",
        diferir_encolado_persistente=True,
    )

    estado_actual = res_turno.get("estado") or estado_previo
    sesion.conversation_state = estado_actual
    sesion.case_id = estado_actual.case_id
    if estado_actual.placa:
        sesion.placa = estado_actual.placa
    if estado_actual.marca and estado_actual.modelo:
        sesion.marca_modelo = f"{estado_actual.marca} {estado_actual.modelo} {estado_actual.anio or ''}".strip()

    gestor.session_manager.cargar_contexto(
        session_key,
        {
            "case_id": estado_actual.case_id,
            "conversation_state": estado_actual.exportar_dict(),
            "placa": estado_actual.placa,
        },
    )

    dto = res_turno.get("dto")
    respuesta_texto = res_turno.get("respuesta_texto", "")
    diagnostico_ml = res_turno.get("diagnostico_ml")
    confianza_ml = float(res_turno.get("confianza_ml", 0.0))
    status_turno = res_turno.get("status")
    decision_turno = res_turno.get("decision")

    estados_sin_inferencia = {
        "consulta_memoria",
        "saludo",
        "saludo_caso_activo",
        "resumen_caso",
        "resumen_descartes",
        "explicacion_causal",
        "tolerancia_oem",
        "entrada_insuficiente",
    }
    if (
        status_turno in estados_sin_inferencia
        or decision_turno in (
            "CONSULTA_MEMORIA",
            "SALUDO",
            "RESUMEN_CASO",
            "RESUMEN_DESCARTES",
            "OPCION_NUMERICA_INVALIDA",
        )
        or ExtractorHechos.es_consulta_memoria(req.mensaje)
    ):
        etiqueta_op = diagnostico_ml or "consulta de memoria técnica"
        if "no aplica" not in str(etiqueta_op).lower():
            diagnostico_ml = f"No aplica ({etiqueta_op})"
        confianza_ml = 0.0
        modo_diagnostico = "memoria_tecnica" if status_turno == "consulta_memoria" else (status_turno or "sin_inferencia")
    else:
        modo_diagnostico = getattr(dto, "modo_diagnostico", "conversacional") if dto else "conversacional"

    vehiculo_partes = [str(v) for v in (estado_actual.marca, estado_actual.modelo, estado_actual.anio) if v]
    vehiculo_str = " ".join(vehiculo_partes) or None

    sintomas_conf = [
        str(h.valor) for h in estado_actual.hechos.values()
        if h.categoria == "sintoma" and h.estado == FactState.CONFIRMADO
    ]
    sintomas_neg = [
        str(h.valor) for h in estado_actual.hechos.values()
        if h.estado == FactState.AUSENTE_NEGADO and h.categoria in {"sintoma", "polaridad", "sistema_normal"}
    ]
    limitaciones = [
        *estado_actual.herramientas_no_disponibles,
        *[str(p.get("prueba")) for p in estado_actual.pruebas_no_disponibles if isinstance(p, dict)],
    ]

    t_total = round((time.perf_counter() - t0) * 1000, 2)
    comprobaciones = _evaluar_comprobaciones(
        estado=estado_actual,
        respuesta_texto=respuesta_texto,
        caso_previo_id=caso_previo_id,
        es_cambio_caso=es_cambio_caso,
        texto_usuario=req.mensaje,
        decision_turno=decision_turno,
        sintomas_previos=sintomas_previos,
    )
    top3 = res_turno.get("top3_actual") or getattr(estado_actual, "top3_actual", [])

    return MensajeLabResponse(
        session_id=session_id_publico,
        case_id=estado_actual.case_id,
        placa=estado_actual.placa,
        vehiculo=vehiculo_str,
        respuesta_texto=respuesta_texto,
        modo_diagnostico=modo_diagnostico,
        diagnostico_ml=diagnostico_ml,
        confianza_ml=confianza_ml,
        contexto_manual=getattr(dto, "contexto_manual", "") if dto else "",
        titulo_manual=getattr(dto, "titulo_manual", "") if dto else "",
        similitud_rag=float(getattr(dto, "similitud_rag", 0.0)) if dto else 0.0,
        tiempo_total_ms=t_total,
        sintomas_confirmados=sintomas_conf,
        sintomas_negados=sintomas_neg,
        limitaciones=limitaciones,
        fase=estado_actual.fase.value if hasattr(estado_actual.fase, "value") else str(estado_actual.fase),
        top3_actual=top3,
        comprobaciones=comprobaciones,
    )


@router.post("/reiniciar", summary="Reiniciar sesión de prueba en memoria")
async def reiniciar_sesion_laboratorio(
    session_id: str,
    _auth: None = Depends(verificar_laboratorio_permitido),
    gestor: GestorDiagnostico = Depends(obtener_gestor),
):
    """Limpia el estado conversacional de la sesión de prueba aislada."""
    session_id_publico, session_key = _normalizar_session_id_lab(session_id)
    async with turno_exclusivo(gestor, session_key):
        gestor.session_manager.reiniciar_sesion(session_key)
        repo = getattr(gestor, "conversation_repo", None)
        if repo and hasattr(repo, "delete_session"):
            await repo.delete_session(session_key)

    return {"status": "ok", "mensaje": f"Sesión de laboratorio '{session_id_publico}' reiniciada."}


@router.post("/ejecutar-caso/{caso_nombre}", summary="Reproducir caso predefinido con pruebas automáticas")
async def ejecutar_caso_predefinido(
    caso_nombre: str,
    _auth: None = Depends(verificar_laboratorio_permitido),
    gestor: GestorDiagnostico = Depends(obtener_gestor),
):
    """Reproduce paso a paso Caso A (Toyota) o Caso B (Nissan) con el orquestador real."""
    caso_nombre = caso_nombre.lower().strip()
    session_id = f"lab_replay_{caso_nombre}_{uuid.uuid4().hex[:6]}"

    if caso_nombre in {"toyota", "yaris", "caso_a"}:
        turnos = [
            "Mi vehículo es un Toyota Yaris 2020, placa ABC123. Cuando freno escucho un chirrido en las ruedas delanteras y siento que el pedal vibra. El problema empezó hace tres días. ¿Qué podría estar fallando?",
            "El pedal no está esponjoso ni se va al fondo, pero sí siento vibraciones en el volante cuando freno. No tengo un reloj comparador ni puedo desmontar las ruedas.",
            "¿Cuál es la memoria técnica registrada?",
        ]
    elif caso_nombre in {"nissan", "sentra", "caso_b"}:
        turnos = [
            "Quiero iniciar un diagnóstico nuevo para otro vehículo. Es un Nissan Sentra 2021, placa XYZ789. No presenta problemas de frenos. Escucho golpes metálicos en la suspensión delantera cuando paso por baches. ¿Qué podría estar fallando?",
        ]
    else:
        raise HTTPException(status_code=400, detail=f"Caso no reconocido: {caso_nombre}. Use 'toyota' o 'nissan'.")

    resultados_turnos = []
    for turno_idx, msg in enumerate(turnos, start=1):
        res = await procesar_mensaje_laboratorio(
            MensajeLabRequest(session_id=session_id, mensaje=msg),
            _auth=None,
            gestor=gestor,
        )
        resultados_turnos.append({
            "turno": turno_idx,
            "mensaje_enviado": msg,
            "respuesta": res.model_dump(),
        })

    return {
        "caso": caso_nombre,
        "session_id": session_id,
        "total_turnos": len(turnos),
        "resultados": resultados_turnos,
    }
