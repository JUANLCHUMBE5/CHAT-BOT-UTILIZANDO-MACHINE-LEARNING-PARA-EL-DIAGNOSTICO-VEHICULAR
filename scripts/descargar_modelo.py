"""Descarga verificada del artefacto ML desde S3/HTTPS.

El ZIP debe contener exactamente `modelo_diagnostico.pkl` y
`vectorizador_tfidf.pkl`. Nunca se carga un pickle sin verificar su SHA-256.
"""

from __future__ import annotations

import hashlib
import io
from pathlib import Path
import zipfile

import requests

from src.config import settings


ARCHIVOS_REQUERIDOS = {"modelo_diagnostico.pkl", "vectorizador_tfidf.pkl"}


def asegurar_artefactos_modelo() -> bool:
    destino = settings.paths.model_pkl.parent
    vectorizador = settings.paths.vectorizer_pkl
    if settings.paths.model_pkl.exists() and vectorizador.exists():
        return True
    if not settings.model_artifact_url or not settings.model_artifact_sha256:
        return False

    respuesta = requests.get(settings.model_artifact_url, timeout=120)
    respuesta.raise_for_status()
    contenido = respuesta.content
    digest = hashlib.sha256(contenido).hexdigest()
    if not hashlib.compare_digest(digest.lower(), settings.model_artifact_sha256.lower()):
        raise RuntimeError("El SHA-256 del artefacto ML no coincide.")

    with zipfile.ZipFile(io.BytesIO(contenido)) as archivo:
        nombres = {Path(nombre).name for nombre in archivo.namelist() if not nombre.endswith("/")}
        if not ARCHIVOS_REQUERIDOS.issubset(nombres):
            raise RuntimeError("El ZIP del modelo no contiene los archivos requeridos.")
        destino.mkdir(parents=True, exist_ok=True)
        for requerido in ARCHIVOS_REQUERIDOS:
            coincidencias = [n for n in archivo.namelist() if Path(n).name == requerido]
            datos = archivo.read(coincidencias[0])
            (destino / requerido).write_bytes(datos)
    return True


if __name__ == "__main__":
    if not asegurar_artefactos_modelo():
        raise SystemExit("Configure MODEL_ARTIFACT_URL y MODEL_ARTIFACT_SHA256.")
    print("Artefactos ML verificados e instalados.")
