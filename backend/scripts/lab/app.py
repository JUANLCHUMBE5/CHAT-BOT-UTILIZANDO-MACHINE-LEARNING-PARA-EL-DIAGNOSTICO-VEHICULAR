"""Aplicación de laboratorio separada: jamás se importa desde main.py."""
from scripts.lab.safety import require_lab_environment

require_lab_environment()

import os  # noqa: E402
from contextlib import asynccontextmanager  # noqa: E402
from pathlib import Path  # noqa: E402

from fastapi import FastAPI, HTTPException, Request  # noqa: E402
from fastapi.responses import FileResponse  # noqa: E402
from fastapi.staticfiles import StaticFiles  # noqa: E402
from pydantic import BaseModel, Field  # noqa: E402
from starlette.middleware.trustedhost import TrustedHostMiddleware  # noqa: E402

from scripts.lab.scenarios import SCENARIOS  # noqa: E402
from scripts.lab.transport import run_scenarios, seed, turn  # noqa: E402

WEB = Path('/lab-web')


@asynccontextmanager
async def lifespan(app):
    await seed()
    yield


app = FastAPI(title='CarBot laboratorio sintético local', lifespan=lifespan)
app.add_middleware(TrustedHostMiddleware, allowed_hosts=['127.0.0.1', 'localhost', 'lab', 'testserver'])


@app.middleware('http')
async def origin_guard(request: Request, call_next):
    origin = request.headers.get('origin')
    if origin and origin not in (f'http://127.0.0.1:{os.getenv("CARBOT_LAB_PORT", "8765")}', f'http://localhost:{os.getenv("CARBOT_LAB_PORT", "8765")}'):
        from fastapi.responses import JSONResponse
        return JSONResponse({'detail': 'Origen externo prohibido'}, status_code=403)
    return await call_next(request)


class Turn(BaseModel):
    scenario: str
    message: str = Field(min_length=1, max_length=4000)


@app.get('/')
async def index():
    return FileResponse(WEB / 'index.html')


@app.get('/lab/scenarios')
async def scenarios():
    return {key: {'vehicle': case['vehicle'], 'plate': case['plate'], 'turns': case['turns']}
            for key, case in SCENARIOS.items()}


@app.post('/lab/turn')
async def chat(body: Turn):
    if body.scenario not in SCENARIOS:
        raise HTTPException(422, 'Escenario desconocido')
    return await turn(body.scenario, body.message)


@app.post('/lab/run')
async def run():
    result = await run_scenarios()
    Path('/artifacts/lab-results.json').write_text(__import__('json').dumps(result, indent=2, default=str))
    return result


@app.get('/lab/results')
async def results():
    import json
    folder = Path('/artifacts')
    output = {'synthetic': True, 'official': False}
    for name in ('summary.json', 'lab-results.json', 'rag-staging.json'):
        if (folder / name).exists():
            output[name] = json.loads((folder / name).read_text(encoding='utf-8-sig'))
    output['coverage'] = (folder / 'coverage.txt').read_text() if (folder / 'coverage.txt').exists() else None
    return output


app.mount('/assets', StaticFiles(directory=WEB), name='lab-assets')


