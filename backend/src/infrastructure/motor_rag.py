import hashlib
import json
import os
import re
import unicodedata
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import numpy as np

try:
    import faiss

    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False

from sklearn.feature_extraction.text import TfidfVectorizer

from src.config import settings
from src.core.logger import logger
from src.infrastructure.rag_checks.frozen_integrity import FrozenRAGMismatch
from src.infrastructure.rag_checks.vectorizer_config import SPANISH_STOP_WORDS


def validar_coherencia_paquete_experimental(
    corpus_data, vectorizador, faiss_index, tolerancia_l2=1e-6, manifiesto=None, directorio_artefactos=None
):
    if manifiesto and isinstance(manifiesto, dict) and manifiesto.get("esquema") == "carbot.rag_experimental/1.0.0" and directorio_artefactos:
        from src.infrastructure.rag.paquete_experimental import validar_vectores
        return validar_vectores(corpus_data, vectorizador, faiss_index, manifiesto, directorio_artefactos, tolerancia_l2)

    n_docs = len(corpus_data)
    if faiss_index.ntotal != n_docs:
        return False, [], f"Discrepancia en cantidad: {n_docs} docs vs {faiss_index.ntotal} vectores en índice FAISS."

    n_features = getattr(vectorizador, "n_features_in_", None)
    if n_features is None and hasattr(vectorizador, "idf_"):
        n_features = vectorizador.idf_.shape[0]

    if n_features is not None and n_features != faiss_index.d:
        return False, [], f"Discrepancia en dimensión: vectorizador ({n_features}) vs FAISS ({faiss_index.d})."

    if manifiesto:
        if "total_documentos_corpus_B" in manifiesto:
            esperado_n = manifiesto["total_documentos_corpus_B"]
            if n_docs != esperado_n:
                return False, [], f"Discrepancia con manifiesto: esperado {esperado_n} documentos, hallados {n_docs}."

        if "dimension_vectorial" in manifiesto:
            esperada_d = manifiesto["dimension_vectorial"]
            if faiss_index.d != esperada_d:
                return False, [], f"Discrepancia con dimensión de manifiesto: esperada {esperada_d}, hallada {faiss_index.d}."

        hashes_artefactos = manifiesto.get("hashes_artefactos", {})
        if hashes_artefactos and directorio_artefactos and Path(directorio_artefactos).exists():
            directorio_path = Path(directorio_artefactos)
            for nombre_archivo, hash_esperado in hashes_artefactos.items():
                coincidencias = list(directorio_path.rglob(nombre_archivo))
                if not coincidencias:
                    coincidencias = list(directorio_path.parent.rglob(nombre_archivo))
                if coincidencias:
                    ruta_arch = coincidencias[0]
                    hash_calc = hashlib.sha256(ruta_arch.read_bytes()).hexdigest()
                    if hash_calc != hash_esperado:
                        return (
                            False,
                            [],
                            f"Discrepancia criptográfica en {nombre_archivo}: hash esperado {hash_esperado}, calculado {hash_calc}.",
                        )

    textos = [f"{doc.get('titulo', '')}\n{doc.get('texto', '')}" for doc in corpus_data]
    try:
        X = vectorizador.transform(textos).toarray().astype(np.float32)
        if hasattr(faiss, "normalize_L2") and faiss_index.d > 0 and X.shape[1] == faiss_index.d:
            faiss.normalize_L2(X)
        reconstruidos = np.zeros((faiss_index.ntotal, faiss_index.d), dtype=np.float32)
        for i in range(faiss_index.ntotal):
            reconstruidos[i] = faiss_index.reconstruct(i)

        diff = np.abs(X - reconstruidos)
        max_err = float(np.max(diff))

        mismatched = []
        for i in range(n_docs):
            err_i = float(np.max(np.abs(X[i] - reconstruidos[i])))
            if err_i > tolerancia_l2:
                doc_id = corpus_data[i].get("doc_id") or corpus_data[i].get("id_procedimiento") or f"doc_{i}"
                mismatched.append({
                    "indice": i,
                    "doc_id": doc_id,
                    "max_error": round(err_i, 8),
                })

        if mismatched:
            return (
                False,
                mismatched,
                f"Discrepancia vectorial en {len(mismatched)} documentos (error máximo: {max_err:.8f} > {tolerancia_l2}).",
            )

        return True, [], f"Paquete experimental verificado con éxito (error máximo: {max_err:.8f} <= {tolerancia_l2})."
    except Exception as exc:
        return False, [], f"Error al verificar coherencia vectorial: {exc}" 


def _normalizar_texto_rag(texto: str) -> str:
    texto = unicodedata.normalize("NFD", str(texto or "").lower())
    return "".join(caracter for caracter in texto if unicodedata.category(caracter) != "Mn")


def _consulta_indica_fuga_refrigerante(consulta: str) -> bool:
    texto = _normalizar_texto_rag(consulta)
    if re.search(
        r"\b(?:co2|quimico|quimica|reactivo|bromotimol|falso\s+negativo|comprobador|analizador|burbujas)\b",
        texto,
    ):
        return False
    fluido = r"(?:refrigerante|anticongelante|agua|coolant)"
    fuga_negada = re.search(
        rf"\b(?:no\s+(?:hay|presenta|tiene|se observa|se detecta)|sin)\b"
        rf".{{0,30}}\b(?:fuga|perdida|goteo)\b.{{0,45}}\b{fluido}\b|"
        rf"\bno\s+(?:pierde|esta perdiendo|consume|gotea)\b.{{0,35}}\b{fluido}\b",
        texto,
    )
    if fuga_negada:
        return False

    tiene_fluido = re.search(rf"\b{fluido}\b", texto)
    tiene_fuga = re.search(r"\b(?:fuga|fugas|pierde|perdiendo|perdida|gotea|goteando)\b", texto)
    if tiene_fluido and tiene_fuga:
        return True

    contexto_refrigeracion = re.search(
        r"\b(?:recalienta|sobrecalentamiento|temperatura|radiador|refrigeracion)\b", texto
    )
    evidencia_goteo = re.search(r"\b(?:mancha|charco|goteo|gotea)\b.{0,35}\b(?:piso|suelo)\b", texto)
    return bool(contexto_refrigeracion and evidencia_goteo)


def _candidato_trata_fuga_refrigerante(candidato: Dict[str, Any]) -> bool:
    meta = candidato.get("metadatos") or {}
    texto = _normalizar_texto_rag(f"{meta.get('falla', '')} {candidato.get('titulo', '')}")
    return bool(
        re.search(r"\bfuga\b.{0,60}\b(?:refrigerante|radiador|enfriamiento)\b", texto)
        or re.search(r"\b(?:refrigerante|radiador|enfriamiento)\b.{0,60}\bfuga\b", texto)
    )


def _validar_coherencia_vectorial(vectorizador: Any, indice: Any, cantidad_documentos: int) -> None:
    """Rechaza paquetes cuyo vectorizador no corresponde con su índice FAISS."""
    dimension_vectorizador = len(getattr(vectorizador, "vocabulary_", {}))
    dimension_indice = int(getattr(indice, "d", 0))
    vectores_indice = int(getattr(indice, "ntotal", -1))

    if dimension_vectorizador <= 0 or dimension_indice <= 0:
        raise ValueError("El vectorizador o el índice FAISS no declara una dimensión válida.")
    if dimension_vectorizador != dimension_indice:
        raise ValueError(
            "Vectorizador e índice FAISS incompatibles: "
            f"{dimension_vectorizador} != {dimension_indice}."
        )
    if vectores_indice != cantidad_documentos:
        raise ValueError(
            "El índice FAISS y el corpus no tienen la misma cantidad de vectores: "
            f"{vectores_indice} != {cantidad_documentos}."
        )


class MotorRAG:
    """Clase encargada de indexar y buscar información dentro de los manuales técnicos multimarca utilizando FAISS / Cosine Similarity (RAG)."""

    def __init__(
        self,
        manual_path: str = str(settings.paths.manual_file),
        rag_version: Optional[str] = None,
    ):
        self.manual_path = Path(manual_path)
        raw_version = (
            rag_version
            or os.getenv("CARBOT_RAG_VERSION")
            or getattr(settings.paths, "rag_version", "baseline_f8_3")
        )
        self.rag_version_id = str(raw_version).strip().lower()
        self.documentos: List[str] = []
        self.titulos: List[str] = []
        self.metadatos_procedimientos: List[Dict[str, Any]] = []
        self.vectorizador: Optional[TfidfVectorizer] = None
        self.faiss_index: Optional[Any] = None
        self.corpus_version = "manual-ausente"
        # El corpus actual es referencial/experimental para tesis; FUENTES_Y_VALIDACION.md documenta su estado.
        self.corpus_validado = False
        self.discrepancias_paquete: List[Dict[str, Any]] = []
        self.dtc_service: Optional[Any] = None

        if self.rag_version_id in ("candidate_v1", "v1", "rag_candidato_v1"):
            self.rag_version = "RAG_CANDIDATO_V1"
            self._cargar_candidato_v1()
        elif self.rag_version_id in (
            "experimental_rag03e",
            "rag03e",
            "rag03c2",
            "rag03c3",
            "rag03f",
            "rag03g",
        ):
            self.rag_version = "RAG_EXPERIMENTAL_RAG03E"
            self._cargar_experimental_rag03e()
        elif self.rag_version_id in ("baseline_f8_3", "baseline"):
            self.rag_version = "RAG_BASELINE_F8_3"
            self._indexar_manuales_multimarca()
        else:
            raise ValueError(f"CARBOT_RAG_VERSION no soportado: {self.rag_version_id}")

    def _cargar_candidato_v1(self):
        """Carga el paquete original verificado sin reconstruir el índice."""
        from src.infrastructure.rag_checks.canonical_loader import cargar_candidato_congelado

        manuals = self.manual_path.parent if self.manual_path.is_file() else self.manual_path
        if not (manuals / "candidates/v1/manifests/verified_frozen_bundle.json").is_file():
            raise FileNotFoundError("Paquete RAG incompleto; selección experimental explícita rechazada")
        try:
            cargar_candidato_congelado(self)
            _validar_coherencia_vectorial(self.vectorizador, self.faiss_index, len(self.documentos))
        except (FrozenRAGMismatch, OSError, ValueError, KeyError) as exc:
            logger.error("RAG congelado no disponible: %s", exc)
            self.faiss_index = None
            self.rag_version = "RAG_CANDIDATO_V1 (INCOMPATIBLE)"
            raise RuntimeError("Paquete RAG_CANDIDATO_V1 inválido") from exc

    def _cargar_experimental_rag03e(self):
        from src.config import PROJECT_ROOT
        from src.infrastructure.rag.paquete_experimental import cargar_paquete

        corpus, self.vectorizador, self.faiss_index, manifest = cargar_paquete(PROJECT_ROOT)
        self.documentos = [d["texto"] for d in corpus]
        self.titulos = [d["titulo"] for d in corpus]
        self.metadatos_procedimientos = [
            dict(d, id_procedimiento=d["doc_id"], make=d.get("marca"), model=d.get("modelo")) for d in corpus
        ]
        self.corpus_version = manifest["version"]
        self.rag_version = manifest["version"]
        self.corpus_validado = False

    def _indexar_manuales_multimarca(self):
        """Indexa todos los manuales del directorio de manuales y carga metadatos_manuales.json si está disponible."""
        directorio_manuales = self.manual_path.parent if self.manual_path.is_file() else self.manual_path

        # 1. Cargar metadatos_manuales.json si existe
        ruta_meta_json = directorio_manuales / "metadatos_manuales.json"
        mapa_metadatos: Dict[str, Dict[str, Any]] = {}
        if ruta_meta_json.exists():
            try:
                with open(ruta_meta_json, "r", encoding="utf-8") as f:
                    lista_meta = json.load(f)
                for item in lista_meta:
                    tit_norm = item.get("titulo", "").strip().lower()
                    mapa_metadatos[tit_norm] = item
                logger.info(f"Metadatos RAG cargados exitosamente: {len(mapa_metadatos)} registros.")
            except Exception as e:
                logger.warning(f"No se pudo cargar metadatos_manuales.json: {e}")

        # 2. Indexar solo archivos registrados en el catálogo técnico.
        # Las guías web y síntomas se conservan fuera del índice operativo.
        archivos_registrados = {
            str(item.get("archivo_fuente", "")).replace("\\", "/")
            for item in mapa_metadatos.values()
            if item.get("archivo_fuente")
        }
        archivos_a_leer = []
        if directorio_manuales.exists() and directorio_manuales.is_dir():
            archivos_a_leer = sorted(
                ruta
                for ruta in directorio_manuales.glob("**/*.txt")
                if ruta.relative_to(directorio_manuales).as_posix() in archivos_registrados
            )
        elif self.manual_path.exists():
            archivos_a_leer = [self.manual_path]

        if not archivos_a_leer:
            logger.error(f"No se encontraron manuales técnicos en: {directorio_manuales}")
            return

        try:
            vistos: set[str] = set()
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
                    huella = hashlib.sha256(f"{titulo}\n{cuerpo}".encode("utf-8")).hexdigest()
                    if not cuerpo or huella in vistos:
                        continue
                    vistos.add(huella)

                    # Un fragmento sin metadatos no pertenece al corpus operativo.
                    tit_lower = titulo.lower()
                    meta = mapa_metadatos.get(tit_lower)
                    if meta is None:
                        logger.warning("Fragmento RAG omitido por falta de metadatos: %s", titulo)
                        continue

                    self.titulos.append(titulo)
                    self.documentos.append(cuerpo)
                    self.metadatos_procedimientos.append(meta)

            self.corpus_version = hash_global.hexdigest()[:16]

            # Fusión de título + cuerpo para vectorización TF-IDF con stop words
            textos_vectorizables = [f"{t}\n{c}" for t, c in zip(self.titulos, self.documentos)]
            self.vectorizador = TfidfVectorizer(
                lowercase=True,
                strip_accents="unicode",
                stop_words=SPANISH_STOP_WORDS,
                ngram_range=(1, 2),
                sublinear_tf=True,
            )
            matriz_tfidf = self.vectorizador.fit_transform(textos_vectorizables).toarray().astype(np.float32)

            # Normalización L2 para producto interno (equivalente a Cosine Similarity en FAISS)
            if not FAISS_AVAILABLE:
                raise RuntimeError("faiss-cpu no está instalado.")
            faiss.normalize_L2(matriz_tfidf)

            # Indexar vectores en FAISS IndexFlatIP (Inner Product)
            dimension = matriz_tfidf.shape[1]
            self.faiss_index = faiss.IndexFlatIP(dimension)
            self.faiss_index.add(matriz_tfidf)

            logger.info(
                f"RAG Multimarca e índice FAISS creados con éxito: {len(self.documentos)} procedimientos indexados (Dimensión: {dimension})."
            )
        except Exception as e:
            logger.error(f"Error al indexar manuales multimarca en FAISS: {e}")

    def _expandir_consulta(self, consulta: str) -> str:
        from src.infrastructure.rag_checks.query_expansion import expandir_consulta

        return expandir_consulta(consulta)

    def recuperar_procedimiento_hibrido(
        self,
        consulta: str,
        macro_sistema: Optional[str] = None,
        top_fallas: Optional[List[Dict[str, Any]]] = None,
        codigos_dtc: Optional[List[str]] = None,
        marca: Optional[str] = None,
        modelo: Optional[str] = None,
        umbral: float | None = None,
        k_candidatos: int = 25,
    ) -> Tuple[str, str, float, Dict[str, Any]]:
        """Recupera el procedimiento técnico óptimo combinando similitud FAISS con señales de ML y DTC."""
        if self.faiss_index is None or len(self.documentos) == 0:
            return "Manual técnico no indexado o ausente.", "Desconocido", 0.0, {}

        umbral_efectivo = settings.diagnostic.rag_min_similarity if umbral is None else umbral
        try:
            from src.core.diagnostico.enrutador_sistema import (
                detectar_areas_tecnicas,
                filtrar_candidatos_por_area,
            )
            from src.infrastructure.rag.query_builder import construir_consulta_hibrida
            from src.infrastructure.rag.relevance_filter import (
                reordenar_candidatos_rag,
                tiene_anclaje_lexico,
            )

            areas_consulta = detectar_areas_tecnicas(consulta)

            consulta_hibrida = construir_consulta_hibrida(
                consulta_usuario=consulta,
                macro_sistema=macro_sistema,
                top_fallas=top_fallas,
                codigos_dtc=codigos_dtc,
                marca=marca,
                modelo=modelo,
                areas_consulta=areas_consulta,
            )
            consulta_expandida = self._expandir_consulta(consulta_hibrida)
            consulta_vec = self.vectorizador.transform([consulta_expandida]).toarray().astype(np.float32)
            faiss.normalize_L2(consulta_vec)

            consulta_map_explicita = any(
                termino in consulta.lower()
                for termino in ("sensor map", "carga absoluta", "presion absoluta", "presión absoluta")
            )
            # Para MAP, explorar el corpus completo antes de restringirlo a la
            # única ficha de admisión que resuelve la discrepancia con MAF.
            k_busqueda = (
                len(self.documentos) if consulta_map_explicita else min(k_candidatos, len(self.documentos))
            )
            similitudes, indices = self.faiss_index.search(consulta_vec, k_busqueda)

            candidatos = []
            for sim, doc_idx in zip(similitudes[0], indices[0]):
                if 0 <= doc_idx < len(self.documentos):
                    if np.isnan(sim) or np.isinf(sim):
                        continue
                    candidatos.append(
                        {
                            "indice": doc_idx,
                            "titulo": self.titulos[doc_idx],
                            "documento": self.documentos[doc_idx],
                            "similitud": sim,
                            "metadatos": (
                                self.metadatos_procedimientos[doc_idx]
                                if doc_idx < len(self.metadatos_procedimientos)
                                else {}
                            ),
                        }
                    )

            if consulta_map_explicita:
                candidatos = [
                    candidato
                    for candidato in candidatos
                    if (candidato.get("metadatos") or {}).get("id_procedimiento") == "RAG_PROC_116"
                ]
            # Una mención explícita de subsistema prevalece sobre una clase ML
            # genérica: el documento recuperado debe tratar el área consultada.
            candidatos = filtrar_candidatos_por_area(candidatos, areas_consulta)
            if not areas_consulta and not (macro_sistema or top_fallas or codigos_dtc):
                candidatos = [
                    candidato for candidato in candidatos if tiene_anclaje_lexico(consulta, candidato)
                ]
            if not candidatos:
                if not areas_consulta:
                    return (
                        "No se encontro un procedimiento especifico en los manuales para esta consulta.",
                        "Coincidencia baja",
                        0.0,
                        {},
                    )
                return (
                    "No se encontró un procedimiento compatible con el sistema mencionado.",
                    "Sin procedimiento compatible verificado",
                    0.0,
                    {},
                )

            # Reordenar ponderando por Macro-Sistema ML, códigos DTC, Top-2 de fallas y compatibilidad vehicular
            conf_ml_val = None
            if top_fallas and len(top_fallas) > 0:
                first_f = top_fallas[0]
                conf_ml_val = float(
                    first_f.get("probabilidad", 0.70)
                    if isinstance(first_f, dict)
                    else getattr(first_f, "probabilidad", 0.70)
                )

            candidatos_reordenados = reordenar_candidatos_rag(
                candidatos,
                macro_sistema=macro_sistema,
                top_fallas=top_fallas,
                codigos_dtc=codigos_dtc,
                confianza_ml=conf_ml_val,
                marca=marca,
                modelo=modelo,
                consulta=consulta,
            )

            from src.core.diagnostico.coherencia_evidencia import documento_compatible

            candidatos_reordenados = [
                candidato
                for candidato in candidatos_reordenados
                if documento_compatible(
                    consulta,
                    candidato.get("titulo", ""),
                    candidato.get("documento", ""),
                )
            ]

            # Una fuga de refrigerante es un hallazgo explícito y más específico
            # que el síntoma general de recalentamiento. Si existe un procedimiento
            # compatible de fuga en el conjunto recuperado, debe preceder al de
            # termostato/ventilador para que text_processor no lo descarte después
            # por discrepancia con la falla ML ya afinada por evidencia.
            if _consulta_indica_fuga_refrigerante(consulta):
                candidatos_fuga = [
                    candidato
                    for candidato in candidatos_reordenados
                    if _candidato_trata_fuga_refrigerante(candidato)
                ]
                if candidatos_fuga:
                    ids_fuga = {candidato["indice"] for candidato in candidatos_fuga}
                    restantes = [
                        candidato
                        for candidato in candidatos_reordenados
                        if candidato["indice"] not in ids_fuga
                    ]
                    candidatos_reordenados = candidatos_fuga + restantes

            # Control de coherencia y no-contaminación de macrosistema:
            # Si se especificó un macro-sistema y no hay códigos DTC explícitos que justifiquen otra área,
            # ningún procedimiento de un macrosistema incompatible debe ser entregado al usuario ni al LLM.
            if macro_sistema and str(macro_sistema).strip().upper() != "DESCONOCIDO":
                macro_obj = str(macro_sistema).strip().upper()
                sistemas_afines_comp = {
                    ("INSTRUMENTAL", "MOTOR"),
                    ("MOTOR", "INSTRUMENTAL"),
                    ("TRANSMISION", "MOTOR"),
                    ("MOTOR", "TRANSMISION"),
                    ("SUSPENSION", "DIRECCION"),
                    ("DIRECCION", "SUSPENSION"),
                    ("SUSPENSION_CHASIS", "DIRECCION"),
                    ("DIRECCION", "SUSPENSION_CHASIS"),
                    ("SUSPENSION", "SUSPENSION_CHASIS"),
                    ("SUSPENSION_CHASIS", "SUSPENSION"),
                }
                candidatos_compatibles = []
                for cand in candidatos_reordenados:
                    c_meta = cand.get("metadatos") or {}
                    c_sis = str(c_meta.get("sistema") or c_meta.get("system") or "").strip().upper()
                    c_dtcs = [
                        str(d).strip().upper()
                        for d in (c_meta.get("codigos_dtc") or c_meta.get("dtcs_relacionados") or [])
                        if d
                    ]
                    coincide_dtc_cand = bool(
                        codigos_dtc and any(str(d).strip().upper() in c_dtcs for d in codigos_dtc if d)
                    )
                    if (
                        coincide_dtc_cand
                        or not c_sis
                        or c_sis == macro_obj
                        or (macro_obj, c_sis) in sistemas_afines_comp
                    ):
                        candidatos_compatibles.append(cand)

                candidatos_reordenados = candidatos_compatibles

            if not candidatos_reordenados or candidatos_reordenados[0]["similitud"] < umbral_efectivo:
                return (
                    "No se encontró un procedimiento específico en los manuales para esta consulta.",
                    "Coincidencia baja",
                    candidatos_reordenados[0]["similitud"] if candidatos_reordenados else 0.0,
                    {},
                )

            mejor = candidatos_reordenados[0]
            metadatos_ret = dict(mejor.get("metadatos") or {})
            metadatos_ret["score_base"] = mejor.get("score_base", mejor.get("similitud", 0.0))
            metadatos_ret["similitud_rerank"] = mejor.get("similitud", 0.0)
            metadatos_ret["categoria_doc"] = mejor.get("categoria_doc", "PROCEDIMIENTO_GENERAL")
            metadatos_ret["dictamen_seguridad"] = mejor.get("dictamen_seguridad", "Aprobado")
            return mejor["documento"], mejor["titulo"], mejor["similitud"], metadatos_ret
        except Exception as e:
            logger.error(f"Error durante la recuperación híbrida en FAISS: {e}")
            return "Error al buscar en el manual.", "Error", 0.0, {}

    def recuperar_contexto_con_similitud(
        self,
        consulta: str,
        umbral: float | None = None,
        macro_sistema: Optional[str] = None,
        top_fallas: Optional[List[Dict[str, Any]]] = None,
        codigos_dtc: Optional[List[str]] = None,
    ) -> tuple[str, str, float]:
        """Recupera contexto y similitud coseno con soporte de señales híbridas opcionales."""
        doc, tit, sim, _ = self.recuperar_procedimiento_hibrido(
            consulta=consulta,
            macro_sistema=macro_sistema,
            top_fallas=top_fallas,
            codigos_dtc=codigos_dtc,
            umbral=umbral,
        )
        return doc, tit, sim

    def recuperar_procedimiento_con_metadatos(
        self,
        consulta: str,
        umbral: float | None = None,
        macro_sistema: Optional[str] = None,
        top_fallas: Optional[List[Dict[str, Any]]] = None,
        codigos_dtc: Optional[List[str]] = None,
        marca: Optional[str] = None,
        modelo: Optional[str] = None,
    ) -> Tuple[str, str, float, Dict[str, Any]]:
        """Recupera el procedimiento más afín junto con sus metadatos (marca, modelo, edición, página OEM)."""
        return self.recuperar_procedimiento_hibrido(
            consulta=consulta,
            macro_sistema=macro_sistema,
            top_fallas=top_fallas,
            codigos_dtc=codigos_dtc,
            marca=marca,
            modelo=modelo,
            umbral=umbral,
        )

    def recuperar_contexto(self, consulta: str, umbral: float = 0.12) -> Tuple[str, str]:
        """Busca el procedimiento técnico más relevante (compatibilidad retroactiva)."""
        cuerpo, titulo, _, _ = self.recuperar_procedimiento_con_metadatos(consulta, umbral)
        return cuerpo, titulo
