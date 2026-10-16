"""Readiness verificable del stack, sin esperas fijas como condición de éxito."""
import time

import httpx

from scripts.lab.safety import require_lab_environment

require_lab_environment()
end = time.monotonic() + 60
while time.monotonic() < end:
    try:
        response = httpx.get('http://api:8000/health/ready', timeout=5)
        if response.status_code == 200 and response.json()['componentes']['rag']:
            print('API, PostgreSQL, SystemWorker, SVM y RAG ready')
            break
    except (httpx.HTTPError, KeyError):
        pass
    time.sleep(0.5)
else:
    raise RuntimeError('Stack no listo con RAG dentro de 60 segundos')
