"""REST real con PostgreSQL; solo el cálculo ML/LLM se sustituye por salida determinista."""
import uuid

import pytest
from fastapi import Request
from sqlalchemy import func, select

from src.config import settings
from src.core.gestor_diagnostico import GestorDiagnostico, ResultadoDiagnostico
from src.infrastructure.database.models.diagnostics import Diagnostico, Vehiculo
from src.infrastructure.database.repositories.taller_repository import TallerRepository
from src.infrastructure.database.repositories.usuario_repository import UsuarioRepository
from src.interfaces.api.v1.endpoints.diagnostico import analizar_sintoma
from src.interfaces.api.v1.schemas import ConsultaDiagnostico


@pytest.mark.anyio
async def test_rest_provisionales_talleres_y_memoria_solo_lectura(async_db_session, monkeypatch):
    session = async_db_session
    owners = []
    for _ in range(2):
        t = await TallerRepository(session).crear_taller(nombre="Synthetic remediation " + uuid.uuid4().hex)
        repo = UsuarioRepository(session)
        roles = await repo.asegurar_roles_estandar()
        u = await repo.crear_usuario(
            taller_id=t.id, rol_id=roles["mecanico"].id, nombres="Synthetic mechanic",
            whatsapp_hash=uuid.uuid4().hex * 2, whatsapp_ultimos4="0000",
        )
        owners.append({"taller_id": str(t.id), "usuario_id": str(u.id)})
    await session.commit()
    monkeypatch.setattr(settings, "gemini_api_key", "")
    gestor = GestorDiagnostico()
    seen = []

    def pipeline(*args, **kwargs):
        seen.append(kwargs["session_id"])
        return ResultadoDiagnostico(
            respuesta_texto="Salida sintética de prueba; no confirma una falla.",
            diagnostico_ml="Hipótesis pendiente", confianza_ml=0.0,
            contexto_manual="", titulo_manual="", modo_diagnostico="diagnostico_degradado_ml_rag",
        )

    monkeypatch.setattr(gestor, "procesar_consulta_texto", pipeline)
    request = Request({"type": "http", "method": "POST", "path": "/api/v1/diagnostico/analizar",
                       "headers": [], "client": ("127.0.0.1", 1234)})
    vehicle_count = await session.scalar(select(func.count()).select_from(Vehiculo))
    ids = []
    for owner in (owners[0], owners[0], owners[1]):
        response = await analizar_sintoma(
            request=request, consulta=ConsultaDiagnostico(sintoma="Demora en arrancar en frío",
                                                         session_id="same-client-session"),
            token_payload=owner, gestor=gestor,
        )
        ids.append(uuid.UUID(response.diagnostico_id))
    assert seen[0] == seen[1] and seen[1] != seen[2]
    records = [(await session.get(Diagnostico, identity)) for identity in ids]
    assert all(r.vehiculo_id is None for r in records)
    traces = [r.trazabilidad for r in records]
    assert traces[0]["case_id"] == traces[1]["case_id"] != traces[2]["case_id"]
    assert traces[0]["identificador_provisional"] == traces[1]["identificador_provisional"]
    assert traces[1]["identificador_provisional"] != traces[2]["identificador_provisional"]
    assert await session.scalar(select(func.count()).select_from(Vehiculo)) == vehicle_count
    count_before = await session.scalar(select(func.count()).select_from(Diagnostico))
    state_before = gestor.session_manager.obtener_sesion(seen[0]).case_id
    await analizar_sintoma(
        request=request, consulta=ConsultaDiagnostico(
            sintoma="¿Qué síntomas tienes registrados? No generes un nuevo diagnóstico.",
            session_id="same-client-session",
        ), token_payload=owners[0], gestor=gestor,
    )
    assert await session.scalar(select(func.count()).select_from(Diagnostico)) == count_before
    assert gestor.session_manager.obtener_sesion(seen[0]).case_id == state_before


@pytest.mark.anyio
async def test_rest_recuperacion_sesion_tras_reinicio_api(async_db_session, monkeypatch):
    session = async_db_session
    t = await TallerRepository(session).crear_taller(nombre="Taller Reinicio " + uuid.uuid4().hex[:8])
    repo = UsuarioRepository(session)
    roles = await repo.asegurar_roles_estandar()
    u = await repo.crear_usuario(
        taller_id=t.id, rol_id=roles["mecanico"].id, nombres="Mecanico Reinicio",
        whatsapp_hash=uuid.uuid4().hex * 2, whatsapp_ultimos4="1111",
    )
    owner = {"taller_id": str(t.id), "usuario_id": str(u.id)}
    await session.commit()
    monkeypatch.setattr(settings, "gemini_api_key", "")

    # Instancia 1 de API antes del reinicio
    gestor_1 = GestorDiagnostico()
    request = Request({"type": "http", "method": "POST", "path": "/api/v1/diagnostico/analizar",
                       "headers": [], "client": ("127.0.0.1", 1234)})

    resp1 = await analizar_sintoma(
        request=request,
        consulta=ConsultaDiagnostico(
            sintoma="Toyota Yaris 2018 con chillido agudo al frenar",
            session_id="sesion-reinicio-test",
            placa="ABC-123",
            marca="Toyota",
            modelo="Yaris",
            anio=2018,
        ),
        token_payload=owner,
        gestor=gestor_1,
    )
    diag1 = await session.get(Diagnostico, uuid.UUID(resp1.diagnostico_id))
    assert diag1 is not None
    case_id_1 = diag1.trazabilidad.get("case_id")
    assert case_id_1 is not None
    session_key = diag1.trazabilidad["session_id"]

    # SIMULAR REINICIO COMPLETO DE API: nueva instancia de GestorDiagnostico con memoria vacía
    gestor_2 = GestorDiagnostico()
    assert gestor_2.session_manager.obtener_sesion(session_key) is None

    # Turno 2 con la API reiniciada
    resp2 = await analizar_sintoma(
        request=request,
        consulta=ConsultaDiagnostico(
            sintoma="El chillido ocurre al pisar el pedal a fondo a baja velocidad",
            session_id="sesion-reinicio-test",
            placa="ABC-123",
        ),
        token_payload=owner,
        gestor=gestor_2,
    )
    diag2 = await session.get(Diagnostico, uuid.UUID(resp2.diagnostico_id))
    assert diag2 is not None
    case_id_2 = diag2.trazabilidad.get("case_id")
    # Continuidad verificada tras reinicio
    assert case_id_2 == case_id_1

    # Comprobar que en gestor_2 la sesión recuperó los síntomas y el vehículo
    sesion_recuperada = gestor_2.session_manager.obtener_sesion(session_key)
    assert sesion_recuperada is not None
    assert sesion_recuperada.case_id == case_id_1
    assert any("chillido agudo al frenar" in s.lower() for s in sesion_recuperada.sintomas)
    assert any("pisar el pedal a fondo" in s.lower() for s in sesion_recuperada.sintomas)

    # SIMULAR OTRO REINICIO Y CONSULTA DE MEMORIA DE SOLO LECTURA
    gestor_3 = GestorDiagnostico()
    assert gestor_3.session_manager.obtener_sesion(session_key) is None
    diags_count_before = await session.scalar(select(func.count()).select_from(Diagnostico))

    resp_mem = await analizar_sintoma(
        request=request,
        consulta=ConsultaDiagnostico(
            sintoma="¿Qué síntomas tienes registrados? No generes un nuevo diagnóstico.",
            session_id="sesion-reinicio-test",
        ),
        token_payload=owner,
        gestor=gestor_3,
    )
    assert resp_mem is not None
    # No crea nuevos diagnósticos
    assert await session.scalar(select(func.count()).select_from(Diagnostico)) == diags_count_before
    # La memoria fue recuperada y mantiene el case_id
    sesion_mem = gestor_3.session_manager.obtener_sesion(session_key)
    assert sesion_mem is not None
    assert sesion_mem.case_id == case_id_1


@pytest.mark.anyio
async def test_rest_aislamiento_multitaller_multisesion(async_db_session, monkeypatch):
    session = async_db_session
    taller_repo = TallerRepository(session)
    user_repo = UsuarioRepository(session)
    roles = await user_repo.asegurar_roles_estandar()

    # Taller A con Mecánico A
    ta = await taller_repo.crear_taller(nombre="Taller A " + uuid.uuid4().hex[:8])
    ua = await user_repo.crear_usuario(
        taller_id=ta.id, rol_id=roles["mecanico"].id, nombres="Mecanico A",
        whatsapp_hash=uuid.uuid4().hex * 2, whatsapp_ultimos4="2222",
    )
    owner_a = {"taller_id": str(ta.id), "usuario_id": str(ua.id)}

    # Taller B con Mecánico B
    tb = await taller_repo.crear_taller(nombre="Taller B " + uuid.uuid4().hex[:8])
    ub = await user_repo.crear_usuario(
        taller_id=tb.id, rol_id=roles["mecanico"].id, nombres="Mecanico B",
        whatsapp_hash=uuid.uuid4().hex * 2, whatsapp_ultimos4="3333",
    )
    owner_b = {"taller_id": str(tb.id), "usuario_id": str(ub.id)}
    await session.commit()
    monkeypatch.setattr(settings, "gemini_api_key", "")

    request = Request({"type": "http", "method": "POST", "path": "/api/v1/diagnostico/analizar",
                       "headers": [], "client": ("127.0.0.1", 1234)})

    # Mecánico A: Sesión 1 (Yaris) y Sesión 2 (Corolla)
    gestor_a = GestorDiagnostico()
    r_a1 = await analizar_sintoma(
        request=request,
        consulta=ConsultaDiagnostico(sintoma="Toyota Yaris vibra al frenar", session_id="sesion-compartida", placa="AAA-111"),
        token_payload=owner_a, gestor=gestor_a,
    )
    r_a2 = await analizar_sintoma(
        request=request,
        consulta=ConsultaDiagnostico(sintoma="Toyota Corolla no enciende", session_id="sesion-corolla", placa="BBB-222"),
        token_payload=owner_a, gestor=gestor_a,
    )

    # Mecánico B en Taller B: usa el mismo session_id string ("sesion-compartida"), pero con Sentra
    gestor_b = GestorDiagnostico()
    r_b1 = await analizar_sintoma(
        request=request,
        consulta=ConsultaDiagnostico(sintoma="Nissan Sentra humo negro", session_id="sesion-compartida", placa="CCC-333"),
        token_payload=owner_b, gestor=gestor_b,
    )

    d_a1 = await session.get(Diagnostico, uuid.UUID(r_a1.diagnostico_id))
    d_a2 = await session.get(Diagnostico, uuid.UUID(r_a2.diagnostico_id))
    d_b1 = await session.get(Diagnostico, uuid.UUID(r_b1.diagnostico_id))

    # Aislamiento estricto de case_id y session_id
    assert d_a1.trazabilidad["session_id"] != d_a2.trazabilidad["session_id"]
    assert d_a1.trazabilidad["session_id"] != d_b1.trazabilidad["session_id"]
    assert d_a1.trazabilidad["case_id"] != d_a2.trazabilidad["case_id"]
    assert d_a1.trazabilidad["case_id"] != d_b1.trazabilidad["case_id"]

    # Simular reinicio y verificar que cada sesión se recupera sin contaminación
    gestor_nuevo = GestorDiagnostico()
    r_a1_t2 = await analizar_sintoma(
        request=request,
        consulta=ConsultaDiagnostico(sintoma="La vibración del Yaris es en el pedal", session_id="sesion-compartida", placa="AAA-111"),
        token_payload=owner_a, gestor=gestor_nuevo,
    )
    d_a1_t2 = await session.get(Diagnostico, uuid.UUID(r_a1_t2.diagnostico_id))
    assert d_a1_t2.trazabilidad["case_id"] == d_a1.trazabilidad["case_id"]

    r_b1_t2 = await analizar_sintoma(
        request=request,
        consulta=ConsultaDiagnostico(sintoma="El humo negro del Sentra huele a gasolina", session_id="sesion-compartida", placa="CCC-333"),
        token_payload=owner_b, gestor=gestor_nuevo,
    )
    d_b1_t2 = await session.get(Diagnostico, uuid.UUID(r_b1_t2.diagnostico_id))
    assert d_b1_t2.trazabilidad["case_id"] == d_b1.trazabilidad["case_id"]
    assert d_b1_t2.trazabilidad["case_id"] != d_a1_t2.trazabilidad["case_id"]


@pytest.mark.anyio
async def test_rest_recuperacion_durable_tras_caida_redis(async_db_session, monkeypatch):
    """Verifica que si Redis pierde la clave (reinicio/evicción), la sesión se recupera desde PostgreSQL."""
    session = async_db_session
    t = await TallerRepository(session).crear_taller(nombre="Taller Redis Drop " + uuid.uuid4().hex[:8])
    repo = UsuarioRepository(session)
    roles = await repo.asegurar_roles_estandar()
    u = await repo.crear_usuario(
        taller_id=t.id, rol_id=roles["mecanico"].id, nombres="Mecanico Redis",
        whatsapp_hash=uuid.uuid4().hex * 2, whatsapp_ultimos4="7777",
    )
    owner = {"taller_id": str(t.id), "usuario_id": str(u.id)}
    await session.commit()
    monkeypatch.setattr(settings, "gemini_api_key", "")

    gestor_1 = GestorDiagnostico()
    request = Request({"type": "http", "method": "POST", "path": "/api/v1/diagnostico/analizar",
                       "headers": [], "client": ("127.0.0.1", 1234)})

    resp1 = await analizar_sintoma(
        request=request,
        consulta=ConsultaDiagnostico(
            sintoma="Nissan Tiida cascabelea en subida",
            session_id="sesion-resistencia-redis",
            placa="TII-999",
            marca="Nissan",
            modelo="Tiida",
        ),
        token_payload=owner,
        gestor=gestor_1,
    )
    diag1 = await session.get(Diagnostico, uuid.UUID(resp1.diagnostico_id))
    case_id_orig = diag1.trazabilidad["case_id"]
    session_key = diag1.trazabilidad["session_id"]

    # Simular caída o pérdida total de clave en Redis
    from src.core.conversacion.session_persistence import _cliente_redis
    redis_client = _cliente_redis()
    if redis_client:
        await redis_client.delete(f"carbot:rest:session:{session_key}")

    # Nueva instancia de gestor con memoria vacía y Redis vacío -> debe recuperarse de PostgreSQL
    gestor_2 = GestorDiagnostico()
    assert gestor_2.session_manager.obtener_sesion(session_key) is None

    resp2 = await analizar_sintoma(
        request=request,
        consulta=ConsultaDiagnostico(
            sintoma="El cascabeleo aumenta con el aire acondicionado encendido",
            session_id="sesion-resistencia-redis",
            placa="TII-999",
        ),
        token_payload=owner,
        gestor=gestor_2,
    )
    diag2 = await session.get(Diagnostico, uuid.UUID(resp2.diagnostico_id))
    assert diag2.trazabilidad["case_id"] == case_id_orig

    sesion_recuperada = gestor_2.session_manager.obtener_sesion(session_key)
    assert sesion_recuperada is not None
    assert sesion_recuperada.case_id == case_id_orig
    assert any("cascabele" in s.lower() and "subida" in s.lower() for s in sesion_recuperada.sintomas)
    assert any("aire acondicionado" in s.lower() for s in sesion_recuperada.sintomas)


@pytest.mark.anyio
async def test_rest_conservacion_hechos_mediciones_y_negaciones(async_db_session, monkeypatch):
    """Verifica que síntomas, negaciones y mediciones se conserven entre turnos sin borrado accidental."""
    session = async_db_session
    t = await TallerRepository(session).crear_taller(nombre="Taller Hechos " + uuid.uuid4().hex[:8])
    repo = UsuarioRepository(session)
    roles = await repo.asegurar_roles_estandar()
    u = await repo.crear_usuario(
        taller_id=t.id, rol_id=roles["mecanico"].id, nombres="Mecanico Hechos",
        whatsapp_hash=uuid.uuid4().hex * 2, whatsapp_ultimos4="8888",
    )
    owner = {"taller_id": str(t.id), "usuario_id": str(u.id)}
    await session.commit()
    monkeypatch.setattr(settings, "gemini_api_key", "")

    gestor = GestorDiagnostico()
    request = Request({"type": "http", "method": "POST", "path": "/api/v1/diagnostico/analizar",
                       "headers": [], "client": ("127.0.0.1", 1234)})

    # Turno 1: Síntoma confirmado y negación explícita
    resp1 = await analizar_sintoma(
        request=request,
        consulta=ConsultaDiagnostico(
            sintoma="Toyota Hilux no acelera bien pero no bota humo negro",
            session_id="sesion-hechos-hilux",
            placa="HLX-555",
            marca="Toyota",
            modelo="Hilux",
        ),
        token_payload=owner,
        gestor=gestor,
    )
    diag1 = await session.get(Diagnostico, uuid.UUID(resp1.diagnostico_id))
    session_key = diag1.trazabilidad["session_id"]
    case_id_orig = diag1.trazabilidad["case_id"]

    # Turno 2: Medición técnica reportada
    resp2 = await analizar_sintoma(
        request=request,
        consulta=ConsultaDiagnostico(
            sintoma="Mapeo de presión de riel muestra 300 bar en ralentí",
            session_id="sesion-hechos-hilux",
            placa="HLX-555",
        ),
        token_payload=owner,
        gestor=gestor,
    )
    diag2 = await session.get(Diagnostico, uuid.UUID(resp2.diagnostico_id))
    assert diag2.trazabilidad["case_id"] == case_id_orig

    sesion = gestor.session_manager.obtener_sesion(session_key)
    assert sesion is not None
    assert sesion.case_id == case_id_orig
    assert len(sesion.sintomas) == 2
    # El estado conversacional conserva los hechos extraídos
    assert sesion.conversation_state is not None
    assert len(sesion.conversation_state.hechos) >= 1


