"""Transporte real API -> SystemWorker -> PostgreSQL, únicamente con datos sintéticos."""
import asyncio
import json
import time
import uuid

import asyncpg
import httpx

from scripts.e2e.run_stack_validation import (
    DATABASE_URL,
    _context_for_sender,
    _evidence_text,
    _identity_hash,
    _seed_workshops,
    _send,
    _state_for_evaluation,
    _wait_job,
)
from scripts.lab.scenarios import SCENARIOS

LOCKS = {key: asyncio.Lock() for key in SCENARIOS}


async def seed():
    db = await asyncpg.connect(DATABASE_URL)
    try:
        await _seed_workshops(db)
        role = await db.fetchval("SELECT id FROM roles WHERE codigo='mecanico'")
        for case in SCENARIOS.values():
            workshop = await db.fetchval('SELECT id FROM talleres WHERE telefono_id_meta=$1', case['phone'])
            user = uuid.uuid5(uuid.NAMESPACE_URL, 'carbot-lab:' + case['sender'])
            await db.execute('''INSERT INTO usuarios (id,taller_id,rol_id,nombres,username,
                whatsapp_hash,whatsapp_ultimos4,activo,bloqueado,debe_cambiar_password,creado_en,actualizado_en)
                VALUES ($1,$2,$3,'Mecánico sintético','lab-' || $4,$5,$6,true,false,false,now(),now())
                ON CONFLICT (whatsapp_hash) DO NOTHING''', user, workshop, role,
                case['plate'], _identity_hash(case['sender']), case['sender'][-4:])
            await db.execute('''INSERT INTO conversaciones (id,taller_id,usuario_id,canal,estado,
                iniciada_en,ultimo_mensaje_en,ventana_servicio_hasta,contexto,creado_en,actualizado_en)
                VALUES ($1,$2,$3,'whatsapp','abierta',now(),now(),now()+interval '24 hours',$4::jsonb,now(),now())
                ON CONFLICT (id) DO NOTHING''', uuid.uuid5(uuid.NAMESPACE_URL, 'lab:' + case['sender']),
                workshop, user, json.dumps({'placa': case['plate'], 'placa_posttest': case['plate']}))
    finally:
        await db.close()


async def turn(key, message, message_id=None):
    case = SCENARIOS[key]
    async with LOCKS[key]:
        db = await asyncpg.connect(DATABASE_URL)
        try:
            start = time.perf_counter()
            async with httpx.AsyncClient() as client:
                response = await _send(client, message_id or 'LAB-' + str(uuid.uuid4()),
                                       case['sender'], case['phone'], message)
            job = await _wait_job(db, response['trabajo_id'])
            state = _state_for_evaluation(await _context_for_sender(db, case['sender']))
            assert message in state.historial_mensajes_usuario, 'Turno completado ausente del historial'
            rows = await db.fetch('''SELECT m.texto FROM mensajes m
                JOIN conversaciones c ON c.id=m.conversacion_id
                JOIN identidades_whatsapp i ON i.usuario_id=c.usuario_id
                WHERE i.identificador_hash=$1 AND m.direccion='salida'
                ORDER BY m.ocurrido_en DESC LIMIT 1''', _identity_hash(case['sender']))
            return {'case_id': state.case_id, 'state': state.exportar_dict(incluir_trazabilidad=False),
                    'evidence': _evidence_text(state), 'job': str(job['estado']),
                    'reply': rows[0]['texto'] if rows else 'Sin respuesta saliente persistida.',
                    'elapsed_ms': round((time.perf_counter() - start) * 1000, 2)}
        finally:
            await db.close()


async def run_scenarios():
    results = []
    for key, case in SCENARIOS.items():
        turns = []
        for message in case['turns']:
            turns.append(await turn(key, message))
        checks = {'stable_case': bool(turns[-1]['case_id']) and len({t['case_id'] for t in turns}) == 1,
                  'memory_read_only': all(turns[-1]['state'].get(k) == turns[-2]['state'].get(k)
                                          for k in ('case_id', 'top3_actual', 'dominio_probable', 'placa')),
                  'vehicle': ' '.join(str(turns[-1]['state'].get(k, '')) for k in ('marca', 'modelo')) == case['vehicle'],
                  'fuel': turns[-1]['state'].get('combustible', '').casefold() == 'gasolina',
                  'facts': {v: v.casefold() in turns[-1]['evidence'].casefold() for v in case['expected']},
                  'plate': turns[-1]['state'].get('placa') == case['plate']}
        results.append({'scenario': key, 'checks': checks, 'turns': turns})
    return {'synthetic': True, 'official': False, 'results': results,
            'passed': len({r['turns'][-1]['case_id'] for r in results}) == len(results)
            and all(r['checks']['stable_case'] and r['checks']['plate']
                          and r['checks']['memory_read_only'] and r['checks']['vehicle'] and r['checks']['fuel']
                          and all(r['checks']['facts'].values()) for r in results)}

