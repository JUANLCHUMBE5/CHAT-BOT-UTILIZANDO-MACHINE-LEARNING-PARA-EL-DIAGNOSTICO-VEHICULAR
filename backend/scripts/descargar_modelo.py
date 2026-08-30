"""Descarga verificada del artefacto ML desde S3/HTTPS.

El ZIP debe contener exactamente `modelo_diagnostico.pkl` y
`vectorizador_tfidf.pkl`. Nunca se carga un pickle sin verificar su SHA-256.
"""

from __future__ import annotations

import hashlib
import io
import zipfile
from pathlib import Path

import requests

from src.config import settings

ARCHIVOS_REQUERIDOS = {"modelo_diagnostico.pkl", "vectorizador_tfidf.pkl"}


def _sha256_archivo(ruta: Path) -> str:
    digest = hashlib.sha256()
    with ruta.open("rb") as archivo:
        for bloque in iter(lambda: archivo.read(1024 * 1024), b""):
            digest.update(bloque)
    return digest.hexdigest()


def _verificar_archivo(ruta: Path, esperado: str) -> None:
    if esperado and not hashlib.compare_digest(_sha256_archivo(ruta), esperado.lower()):
        raise RuntimeError(f"El SHA-256 del artefacto {ruta.name} no coincide.")


def asegurar_artefactos_modelo() -> bool:
    destino = settings.paths.model_pkl.parent
    vectorizador = settings.paths.vectorizer_pkl
    if settings.paths.model_pkl.exists() and vectorizador.exists():
        _verificar_archivo(settings.paths.model_pkl, settings.model_pkl_sha256)
        _verificar_archivo(vectorizador, settings.vectorizer_pkl_sha256)
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
            esperado = (
                settings.model_pkl_sha256
                if requerido == "modelo_diagnostico.pkl"
                else settings.vectorizer_pkl_sha256
            )
            digest_archivo = hashlib.sha256(datos).hexdigest()
            if esperado and not hashlib.compare_digest(digest_archivo, esperado.lower()):
                raise RuntimeError(f"El SHA-256 interno de {requerido} no coincide.")
            (destino / requerido).write_bytes(datos)
    return True


if __name__ == "__main__":
    if not asegurar_artefactos_modelo():
        raise SystemExit("Configure MODEL_ARTIFACT_URL y MODEL_ARTIFACT_SHA256.")
    print("Artefactos ML verificados e instalados.")
