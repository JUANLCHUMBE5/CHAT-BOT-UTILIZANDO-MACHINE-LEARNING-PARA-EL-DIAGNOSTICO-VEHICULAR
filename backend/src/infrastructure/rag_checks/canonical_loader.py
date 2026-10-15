"""Recupera el TF-IDF original y verifica cada vector del índice inmutable.

El corpus histórico solo define el espacio de embeddings. Las respuestas usan
los textos vigentes verificados, incluidos retiros y correcciones de seguridad.
"""

import hashlib
import json
import re
from pathlib import Path

import faiss
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer

from src.core.logger import logger
from src.infrastructure.rag_checks.frozen_integrity import FrozenRAGMismatch, validar_espacio_congelado
from src.infrastructure.rag_checks.vectorizer_config import SPANISH_STOP_WORDS


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _ruta_segura(base: Path, relative: str) -> Path:
    path = (base / relative).resolve()
    if not path.is_relative_to(base.resolve()):
        raise FrozenRAGMismatch("Ruta fuera del paquete RAG")
    return path


def leer_documentos(texts_dir: Path, metadata: list[dict]) -> tuple[list, list, list]:
    by_title = {item["titulo"].strip().lower(): item for item in metadata}
    registered = {item["archivo_fuente"].replace("\\", "/") for item in metadata}
    titles, documents, metas = [], [], []
    seen = set()
    for relative in sorted(registered):
        content = _ruta_segura(texts_dir, relative).read_text(encoding="utf-8")
        for title, body in re.findall(
            r"^===\s*(.*?)\s*===\s*$\n(.*?)(?=^===|\Z)", content, flags=re.M | re.S,
        ):
            title, body = title.strip(), body.strip()
            key = title.lower()
            if not body or key in seen or key not in by_title:
                continue
            seen.add(key)
            titles.append(title)
            documents.append(body)
            metas.append(by_title[key])
    return titles, documents, metas


def cargar_candidato_congelado(motor) -> None:
    manuals = motor.manual_path.parent if motor.manual_path.is_file() else motor.manual_path
    base = manuals / "candidates" / "v1"
    bundle_path = base / "manifests" / "verified_frozen_bundle.json"
    bundle = json.loads(bundle_path.read_text(encoding="utf-8"))
    for relative, expected in bundle["files"].items():
        if _sha(_ruta_segura(base, relative).read_bytes()) != expected:
            raise FrozenRAGMismatch(f"Hash RAG incompatible: {relative}")
    index_path = base / "indexes" / "indice_faiss_v1.index"
    if _sha(index_path.read_bytes()) != bundle["index_sha256"]:
        raise FrozenRAGMismatch("Hash del índice congelado incompatible")

    snapshot = _ruta_segura(base, bundle["snapshot_dir"])
    original_meta = json.loads((snapshot / "metadata" / "metadatos_manuales_v1.json").read_text(encoding="utf-8"))
    current_meta = json.loads((base / "metadata" / "metadatos_schema_v2.json").read_text(encoding="utf-8"))
    titles, indexed, indexed_meta = leer_documentos(snapshot / "texts", original_meta)
    current_titles, documents, metas = leer_documentos(base / "texts", current_meta)
    entries = bundle["entries"]
    if titles != current_titles or len(titles) != len(entries):
        raise FrozenRAGMismatch("Correspondencia ordinal de documentos incompatible")
    for position, entry in enumerate(entries):
        original_id = indexed_meta[position].get("id_procedimiento")
        served_id = metas[position].get("doc_id")
        if position != entry["position"] or original_id != entry["doc_id"] or served_id != original_id:
            raise FrozenRAGMismatch("Identidad documental incompatible con FAISS")
        for body, field in ((indexed[position], "indexed_text_sha256"),
                            (documents[position], "served_text_sha256")):
            if _sha(f"{titles[position]}\n{body}".encode()) != entry[field]:
                raise FrozenRAGMismatch(f"Texto RAG incompatible: {original_id}")

    vectorizer = TfidfVectorizer(
        lowercase=True, strip_accents="unicode", stop_words=SPANISH_STOP_WORDS,
        ngram_range=(1, 2), sublinear_tf=True,
    )
    matrix = vectorizer.fit_transform([f"{t}\n{c}" for t, c in zip(titles, indexed)])
    index = faiss.read_index(str(index_path))
    validar_espacio_congelado(index, vectorizer, len(titles))
    if index.d != bundle["dimension"] or index.ntotal != bundle["document_count"]:
        raise FrozenRAGMismatch("Dimensión o tamaño distinto del paquete original")
    for position in range(len(titles)):
        row = matrix.getrow(position).toarray().astype(np.float32)
        faiss.normalize_L2(row)
        if not np.allclose(row[0], index.reconstruct(position), rtol=1e-6, atol=1e-7):
            raise FrozenRAGMismatch(f"Vector original incompatible en posición {position}")

    compatible_meta = []
    for item in metas:
        meta = dict(item)
        meta["id_procedimiento"] = item["doc_id"]
        meta.setdefault("manual_oem", item.get("source_title") or item.get("source_id"))
        meta.setdefault("estado_validacion", "corpus_preliminar_taller")
        meta["embedding_source_commit"] = bundle["source_git_commit"]
        compatible_meta.append(meta)
    motor.titulos, motor.documentos = titles, documents
    motor.metadatos_procedimientos = compatible_meta
    motor.vectorizador, motor.faiss_index = vectorizer, index
    motor.corpus_version = _sha(bundle_path.read_bytes())[:16]
    try:
        from src.infrastructure.dtc.dtc_lookup_service import DtcLookupService

        motor.dtc_service = DtcLookupService()
    except (ImportError, OSError, ValueError) as exc:
        logger.warning("DTC auxiliar no disponible: %s", type(exc).__name__)
    logger.info("RAG congelado verificado: %s documentos, %s dimensiones", len(titles), index.d)
