"""
CandidateRAGHarness: Harness desacoplado e independiente para ejecutar
y comparar el RAG Baseline (F8.3) y RAG Candidato (V1).
Permite inyectar rutas explícitas de textos, metadatos e índices FAISS.
"""
import sys
import os
import json
import hashlib
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

PROJECT_ROOT = Path("c:/Users/leonc/OneDrive/Desktop/CHAT_BOT_MACHINLEARNING")
BACKEND_DIR = PROJECT_ROOT / "backend"
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

import faiss
from sklearn.feature_extraction.text import TfidfVectorizer

from src.infrastructure.motor_rag import SPANISH_STOP_WORDS

class CandidateRAGHarness:
    """Harness para cargar y evaluar de forma aislada cualquier versión del RAG
    (Baseline F8.3 o Candidato V1) sin alterar el runtime productivo de CarBot."""

    def __init__(
        self,
        texts_dir: Path,
        metadata_path: Path,
        index_path: Optional[Path] = None,
        version_id: str = "CANDIDATE_V1",
        dtc_lookup_service: Optional[Any] = None,
        recompute_index_if_missing: bool = True
    ):
        self.texts_dir = Path(texts_dir)
        self.metadata_path = Path(metadata_path)
        self.index_path = Path(index_path) if index_path else None
        self.version_id = version_id
        self.dtc_lookup_service = dtc_lookup_service
        self.recompute_index_if_missing = recompute_index_if_missing

        self.documentos: List[str] = []
        self.titulos: List[str] = []
        self.metadatos_procedimientos: List[Dict[str, Any]] = []
        self.vectorizador: Optional[TfidfVectorizer] = None
        self.faiss_index: Optional[Any] = None
        self.corpus_version: str = "init"

        self._cargar_corpus_e_indice()

    def _cargar_corpus_e_indice(self):
        # 1. Cargar metadatos
        with open(self.metadata_path, "r", encoding="utf-8") as f:
            lista_meta = json.load(f)

        mapa_metadatos = {}
        for item in lista_meta:
            tit_norm = item.get("titulo", "").strip().lower()
            mapa_metadatos[tit_norm] = item

        # 2. Localizar archivos registrados
        archivos_registrados = {
            str(item.get("archivo_fuente", "")).replace("\\", "/")
            for item in mapa_metadatos.values()
            if item.get("archivo_fuente")
        }

        archivos_a_leer = []
        if self.texts_dir.is_dir():
            archivos_a_leer = sorted(
                ruta
                for ruta in self.texts_dir.glob("**/*.txt")
                if ruta.relative_to(self.texts_dir).as_posix() in archivos_registrados
            )
        elif self.texts_dir.is_file():
            archivos_a_leer = [self.texts_dir]

        if not archivos_a_leer:
            raise FileNotFoundError(f"No se encontraron manuales tecnicos en: {self.texts_dir}")

        vistos = set()
        hash_global = hashlib.sha256()

        for ruta_arch in archivos_a_leer:
            with open(ruta_arch, "r", encoding="utf-8") as f:
                contenido = f.read()
            hash_global.update(contenido.encode("utf-8"))
            secciones = re.findall(
                r"^===\s*(.*?)\s*===\s*$\n(.*?)(?=^===|\Z)",
                contenido,
                flags=re.MULTILINE | re.DOTALL,
            )

            for titulo, cuerpo in secciones:
                titulo = titulo.strip()
                cuerpo = cuerpo.strip()
                tit_lower = titulo.lower()
                if not cuerpo or tit_lower in vistos:
                    continue
                meta = mapa_metadatos.get(tit_lower)
                if meta is None:
                    continue
                vistos.add(tit_lower)

                self.titulos.append(titulo)
                self.documentos.append(cuerpo)
                self.metadatos_procedimientos.append(meta)

        self.corpus_version = hash_global.hexdigest()[:16]

        # 3. Vectorizador TF-IDF consistente con MotorRAG
        textos_vectorizables = [f"{t}\n{c}" for t, c in zip(self.titulos, self.documentos)]
        self.vectorizador = TfidfVectorizer(
            lowercase=True,
            strip_accents="unicode",
            stop_words=SPANISH_STOP_WORDS,
            ngram_range=(1, 2),
            sublinear_tf=True
        )
        matriz_tfidf = self.vectorizador.fit_transform(textos_vectorizables).toarray().astype(np.float32)
        faiss.normalize_L2(matriz_tfidf)

        # 4. Indice FAISS
        dimension = matriz_tfidf.shape[1]
        if self.index_path and self.index_path.exists():
            disco_index = faiss.read_index(str(self.index_path))
            if disco_index.d == dimension and disco_index.ntotal == len(self.documentos):
                self.faiss_index = disco_index
            else:
                if self.recompute_index_if_missing:
                    self.faiss_index = faiss.IndexFlatIP(dimension)
                    self.faiss_index.add(matriz_tfidf)
                else:
                    raise ValueError(
                        f"Dimension/ntotal mismatch in {self.index_path}: "
                        f"disco=(d={disco_index.d}, n={disco_index.ntotal}) vs calculado=(d={dimension}, n={len(self.documentos)})"
                    )
        else:
            self.faiss_index = faiss.IndexFlatIP(dimension)
            self.faiss_index.add(matriz_tfidf)

    def _expandir_consulta(self, consulta: str) -> str:
        from src.infrastructure.motor_rag import MotorRAG
        temp_rag = MotorRAG.__new__(MotorRAG)
        return temp_rag._expandir_consulta(consulta)

    def recuperar_procedimiento(
        self,
        consulta: str,
        macro_sistema: Optional[str] = None,
        top_fallas: Optional[List[Dict[str, Any]]] = None,
        codigos_dtc: Optional[List[str]] = None,
        k_candidatos: int = 25,
        usar_dtc_lookup: bool = False
    ) -> List[Dict[str, Any]]:
        from src.infrastructure.rag.query_builder import construir_consulta_hibrida
        from src.infrastructure.rag.relevance_filter import reordenar_candidatos_rag

        dtc_evidence = []
        codigos_efectivos = list(codigos_dtc or [])
        if usar_dtc_lookup and self.dtc_lookup_service:
            detectados = self.dtc_lookup_service.extraer_codigos(consulta)
            for d in detectados:
                if d not in codigos_efectivos:
                    codigos_efectivos.append(d)
            for c in codigos_efectivos:
                res = self.dtc_lookup_service.lookup(c)
                if res:
                    dtc_evidence.append(res)

        consulta_hibrida = construir_consulta_hibrida(
            consulta_usuario=consulta,
            macro_sistema=macro_sistema,
            top_fallas=top_fallas,
            codigos_dtc=codigos_efectivos,
        )
        consulta_expandida = self._expandir_consulta(consulta_hibrida)
        consulta_vec = self.vectorizador.transform([consulta_expandida]).toarray().astype(np.float32)
        faiss.normalize_L2(consulta_vec)

        k_busqueda = min(k_candidatos, len(self.documentos))
        similitudes, indices = self.faiss_index.search(consulta_vec, k=k_busqueda)

        candidatos = []
        for k_idx in range(k_busqueda):
            doc_idx = int(indices[0][k_idx])
            sim = float(similitudes[0][k_idx])
            if 0 <= doc_idx < len(self.documentos):
                candidatos.append({
                    "indice": doc_idx,
                    "titulo": self.titulos[doc_idx],
                    "documento": self.documentos[doc_idx],
                    "similitud": sim,
                    "metadatos": self.metadatos_procedimientos[doc_idx],
                })

        conf_ml_val = None
        if top_fallas and len(top_fallas) > 0:
            first_f = top_fallas[0]
            conf_ml_val = float(first_f.get("probabilidad", 0.70) if isinstance(first_f, dict) else getattr(first_f, "probabilidad", 0.70))

        candidatos_reordenados = reordenar_candidatos_rag(
            candidatos,
            macro_sistema=macro_sistema,
            top_fallas=top_fallas,
            codigos_dtc=codigos_efectivos,
            confianza_ml=conf_ml_val,
        )
        if dtc_evidence:
            for cand in candidatos_reordenados:
                cand["dtc_evidence"] = dtc_evidence
        return candidatos_reordenados
