"""Verificación sin carga, regeneración ni modificación de artefactos."""
from __future__ import annotations

import hashlib
import json
from pathlib import Path


def verificar_manifest(root: Path, manifest: Path) -> dict[str, bool]:
    contrato = json.loads(manifest.read_text(encoding="utf-8-sig"))
    resultado = {}
    base = root.resolve()
    for nombre, esperado in contrato["artifacts"].items():
        archivo = (base / nombre).resolve()
        if not archivo.is_relative_to(base):
            raise ValueError("El manifiesto no puede referenciar archivos fuera de su raíz.")
        if not archivo.is_file():
            resultado[nombre] = False
            continue
        contenido = archivo.read_bytes()
        if nombre in contrato.get("canonical_text_lf", []):
            contenido = contenido.replace(b"\r\n", b"\n")
        resultado[nombre] = hashlib.sha256(contenido).hexdigest() == esperado
    return resultado
