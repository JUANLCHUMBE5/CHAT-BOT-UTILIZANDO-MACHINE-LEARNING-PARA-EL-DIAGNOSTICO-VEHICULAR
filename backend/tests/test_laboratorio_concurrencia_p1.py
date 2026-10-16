"""Serialización verificable de mensajes del mismo laboratorio local."""
import asyncio
from contextlib import asynccontextmanager

import httpx

from src.config import settings
from src.core.conversacion.orquestador_conversacion import OrquestadorConversacion
from src.core.security import crear_jwt_token
from src.interfaces.api.v1.endpoints.laboratorio_local.app import create_laboratory_app


async def _ejecutar_concurrencia(monkeypatch):
    monkeypatch.setattr(settings, 'enable_laboratory', True)
    monkeypatch.setattr(settings, 'environment', 'test')
    monkeypatch.setattr(settings, 'gemini_api_key', '')
    monkeypatch.setattr(settings, 'groq_api_key', '')
    monkeypatch.setenv('CARBOT_BLOCK_DOTENV', 'true')
    app = create_laboratory_app()
    original = OrquestadorConversacion.procesar_turno
    activos = 0
    maximos = 0
    orden = []
    primero_dentro = asyncio.Event()
    segundo_listo = asyncio.Event()
    liberar_primero = asyncio.Event()
    from src.interfaces.api.v1.endpoints.laboratorio_local import routes
    original_exclusivo = routes.turno_exclusivo
    llegadas = 0

    @asynccontextmanager
    async def observar_llegada(gestor, clave):
        nonlocal llegadas
        llegadas += 1
        if llegadas == 2:
            segundo_listo.set()
        async with original_exclusivo(gestor, clave):
            yield

    monkeypatch.setattr(routes, 'turno_exclusivo', observar_llegada)

    async def instrumentado(self, *args, **kwargs):
        nonlocal activos, maximos
        activos += 1
        maximos = max(maximos, activos)
        orden.append(kwargs['texto_usuario'])
        try:
            if len(orden) == 1:
                primero_dentro.set()
                await asyncio.wait_for(liberar_primero.wait(), timeout=10)
            return await original(self, *args, **kwargs)
        finally:
            activos -= 1

    monkeypatch.setattr(OrquestadorConversacion, 'procesar_turno', instrumentado)
    token = crear_jwt_token(usuario_id='00000000-0000-0000-0000-000000000091')
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://localhost',
                               headers={'Authorization': f'Bearer {token}'}) as c:
        primero = asyncio.create_task(c.post('/api/v1/laboratorio/mensaje', json={
            'session_id': 'p1-concurrente',
            'mensaje': 'Toyota Yaris 2020 gasolina placa ABC123. El volante vibra.',
        }))
        await asyncio.wait_for(primero_dentro.wait(), timeout=10)
        segundo = asyncio.create_task(c.post('/api/v1/laboratorio/mensaje', json={
            'session_id': 'p1-concurrente', 'mensaje': 'No tengo pérdida de potencia.',
        }))
        await asyncio.wait_for(segundo_listo.wait(), timeout=10)
        liberar_primero.set()
        resultados = await asyncio.gather(primero, segundo)

    assert all(r.status_code == 200 for r in resultados), [r.text for r in resultados]
    assert maximos == 1, 'La misma sesión entró simultáneamente en el orquestador'
    assert orden == ['Toyota Yaris 2020 gasolina placa ABC123. El volante vibra.',
                     'No tengo pérdida de potencia.']
    assert resultados[0].json()['case_id'] == resultados[1].json()['case_id']
    gestor = app.state.gestor_laboratorio
    estado = await gestor.conversation_repo.get_session('lab::p1-concurrente')
    assert estado.es_hecho_negado('sintoma_pérdida_de_potencia')
    assert estado.es_hecho_confirmado('sintoma_vibración')
    assert len(estado.historial_mensajes_usuario) == 2


def test_dos_turnos_simultaneos_sesion_local(monkeypatch):
    asyncio.run(_ejecutar_concurrencia(monkeypatch))



def test_cancelacion_no_deja_bloqueo_huerfano():
    from src.interfaces.api.v1.endpoints.laboratorio_local.concurrency import _registro, turno_exclusivo

    async def ejecutar():
        gestor = object()
        iniciado = asyncio.Event()

        async def esperar():
            iniciado.set()
            async with turno_exclusivo(gestor, 'misma'):
                pass

        async with turno_exclusivo(gestor, 'misma'):
            pendiente = asyncio.create_task(esperar())
            await iniciado.wait()
            pendiente.cancel()
            try:
                await pendiente
            except asyncio.CancelledError:
                pass
        async with turno_exclusivo(gestor, 'misma'):
            pass
        assert not _registro

    asyncio.run(ejecutar())


def test_dos_talleres_concurrentes_aislados(monkeypatch):
    async def ejecutar():
        monkeypatch.setattr(settings, 'enable_laboratory', True)
        monkeypatch.setattr(settings, 'environment', 'test')
        monkeypatch.setattr(settings, 'gemini_api_key', '')
        monkeypatch.setattr(settings, 'groq_api_key', '')
        monkeypatch.setenv('CARBOT_BLOCK_DOTENV', 'true')
        app = create_laboratory_app()
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url='http://localhost') as c:
            resultados = await asyncio.gather(*[
                c.post('/api/v1/laboratorio/mensaje',
                       headers={'Authorization': 'Bearer ' + crear_jwt_token(usuario_id=user, taller_id=taller)},
                       json={'session_id': 'publica-compartida', 'mensaje': mensaje})
                for user, taller, mensaje in [
                    ('00000000-0000-0000-0000-000000000091', '00000000-0000-0000-0000-000000000001',
                     'Toyota Yaris 2020 gasolina placa ABC123. El volante vibra.'),
                    ('00000000-0000-0000-0000-000000000092', '00000000-0000-0000-0000-000000000002',
                     'Nissan Sentra 2015 gasolina placa XYZ789. Tiene pérdida de potencia.'),
                ]
            ])
        assert all(r.status_code == 200 for r in resultados)
        a, b = [r.json() for r in resultados]
        assert a['case_id'] != b['case_id']
        assert a['placa'] == 'ABC-123'
        assert b['placa'] == 'XYZ-789'
    asyncio.run(ejecutar())
