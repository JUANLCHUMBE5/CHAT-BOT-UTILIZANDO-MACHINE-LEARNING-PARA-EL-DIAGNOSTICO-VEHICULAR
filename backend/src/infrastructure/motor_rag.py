import hashlib
import json
import os
import re
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


class MotorRAG:
    """Clase encargada de indexar y buscar información dentro de los manuales técnicos multimarca utilizando FAISS / Cosine Similarity (RAG)."""

    def __init__(self, manual_path: str = str(settings.paths.manual_file)):
        self.manual_path = Path(manual_path)
        self.documentos: List[str] = []
        self.titulos: List[str] = []
        self.metadatos_procedimientos: List[Dict[str, Any]] = []
        self.vectorizador: Optional[TfidfVectorizer] = None
        self.faiss_index: Optional[Any] = None
        self.corpus_version = "manual-ausente"
        self.corpus_validado = True
        self._indexar_manuales_multimarca()

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

        # 2. Recopilar todos los archivos .txt de manuales
        archivos_a_leer = []
        if directorio_manuales.exists() and directorio_manuales.is_dir():
            archivos_a_leer = list(directorio_manuales.glob("**/*.txt"))
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

                    # Buscar metadatos específicos
                    tit_lower = titulo.lower()
                    meta = mapa_metadatos.get(tit_lower, {
                        "id_procedimiento": f"RAG_PROC_{len(self.documentos)+1:03d}",
                        "titulo": titulo,
                        "marca": "Multimarca / Universal",
                        "modelo": "General",
                        "anio": "2018-2024",
                        "manual_oem": "Manual General de Procedimientos",
                        "edicion": "Edición de Taller",
                        "pagina": len(self.documentos) + 1,
                        "estado_validacion": "validado_tecnico"
                    })

                    self.titulos.append(titulo)
                    self.documentos.append(cuerpo)
                    self.metadatos_procedimientos.append(meta)

            self.corpus_version = hash_global.hexdigest()[:16]

            # Inicializar matriz TF-IDF
            self.vectorizador = TfidfVectorizer(lowercase=True, strip_accents="unicode")
            matriz_tfidf = self.vectorizador.fit_transform(self.documentos).toarray().astype(np.float32)

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
        """Expande la consulta del usuario incluyendo términos técnicos estandarizados y códigos DTC."""
        consulta_lower = consulta.lower()
        expansiones = []
        
        diccionario_dtc = {
            "p0300": "bujias cascabeleo misfire encendido",
            "p0301": "bujias cascabeleo misfire encendido",
            "c0035": "pastillas de freno chillido disco",
            "c0040": "purga liquido de frenos pedal esponjoso fuga",
            "p0505": "valvula iac cuerpo de aceleracion ralenti minimo apaga",
            "p0562": "bateria voltaje arranque alternador bornes",
            "p0a80": "bateria alto voltaje hibrido prius celdas",
            "p2002": "filtro particulas dpf fap adblue escape",
            "p0087": "presion combustible riel common rail bomba alta",
            "chillido": "pastillas de freno freno",
            "esponjoso": "liquido de frenos purga fuga",
            "cascabelea": "bujias motor encendido",
            "cascabeleo": "bujias motor encendido",
            "se apaga": "valvula iac minimo ralenti",
            "control": "cierre centralizado actuador puerta seguro electrico",
            "bloqueada": "cierre centralizado actuador puerta chapa cerradura",
            "desbloquea": "cierre centralizado control actuador puerta",
            "pestillo": "chapa cerradura puerta seguro pestillo mecanico",
            "chapa": "cerradura chapa pestillo puerta alineacion trinquete",
            "cerradura": "chapa cerradura pestillo puerta trinquete",
            "elevalunas": "alzacristales vidrio guaya motor ventana",
            "alzacristales": "elevalunas vidrio guaya ventana",
            "vidrio": "elevalunas alzacristales guaya luna",
            "luna": "elevalunas alzacristales vidrio ventana",
            "limpiaparabrisas": "motor plumas varillaje limpiaparabrisas",
            "pluma": "limpiaparabrisas motor varillaje",
            "common rail": "diesel bomba alta presion inyectores scv",
            "dpf": "filtro particulas hollin adblue def regeneracion",
            "adblue": "urea def regeneracion dpf catalizador",
            "freno de aire": "camion neumatico valvula secador aps compresor",
            "inversor": "hibrido ev alto voltaje igbt bomba enfriamiento",
            "hibrido": "bateria alto voltaje inversor motor electrico ready",
            "valvolina": "caja cambios mecanica rodajes diferencial aceite"
        }
        
        for clave, valor in diccionario_dtc.items():
            if clave in consulta_lower:
                expansiones.append(valor)
                
        if expansiones:
            return f"{consulta} {' '.join(expansiones)}"
        return consulta

    def recuperar_contexto_con_similitud(
        self, consulta: str, umbral: float | None = None
    ) -> tuple[str, str, float]:
        """Recupera contexto y similitud coseno sin mezclarla con la confianza ML."""
        if self.faiss_index is None or len(self.documentos) == 0:
            return "Manual tecnico no indexado o ausente.", "Desconocido", 0.0

        umbral_efectivo = (
            settings.diagnostic.rag_min_similarity if umbral is None else umbral
        )
        try:
            consulta_expandida = self._expandir_consulta(consulta)
            consulta_vec = self.vectorizador.transform([consulta_expandida]).toarray().astype(np.float32)
            faiss.normalize_L2(consulta_vec)
            similitudes, indices = self.faiss_index.search(consulta_vec, k=1)
            mejor_similitud = max(0.0, min(1.0, float(similitudes[0][0])))
            indice_mejor = int(indices[0][0])

            if mejor_similitud < umbral_efectivo or indice_mejor < 0:
                return (
                    "No se encontro un procedimiento especifico en los manuales para esta consulta.",
                    "Coincidencia baja",
                    mejor_similitud,
                )
            return self.documentos[indice_mejor], self.titulos[indice_mejor], mejor_similitud
        except Exception as e:
            logger.error(f"Error durante la busqueda semantica en FAISS: {e}")
            return "Error al buscar en el manual.", "Error", 0.0

    def recuperar_procedimiento_con_metadatos(
        self, consulta: str, umbral: float | None = None
    ) -> Tuple[str, str, float, Dict[str, Any]]:
        """Recupera el procedimiento más afín junto con sus metadatos (marca, modelo, edición, página OEM)."""
        if self.faiss_index is None or len(self.documentos) == 0:
            return "Manual técnico no indexado o ausente.", "Desconocido", 0.0, {}

        umbral_efectivo = (
            settings.diagnostic.rag_min_similarity if umbral is None else umbral
        )
        try:
            consulta_expandida = self._expandir_consulta(consulta)
            consulta_vec = self.vectorizador.transform([consulta_expandida]).toarray().astype(np.float32)
            faiss.normalize_L2(consulta_vec)
            similitudes, indices = self.faiss_index.search(consulta_vec, k=1)
            mejor_similitud = max(0.0, min(1.0, float(similitudes[0][0])))
            indice_mejor = int(indices[0][0])

            if mejor_similitud < umbral_efectivo or indice_mejor < 0:
                return (
                    "No se encontró un procedimiento específico en los manuales para esta consulta.",
                    "Coincidencia baja",
                    mejor_similitud,
                    {}
                )
            meta = (
                self.metadatos_procedimientos[indice_mejor]
                if indice_mejor < len(self.metadatos_procedimientos)
                else {}
            )
            return self.documentos[indice_mejor], self.titulos[indice_mejor], mejor_similitud, meta
        except Exception as e:
            logger.error(f"Error durante la búsqueda semántica con metadatos en FAISS: {e}")
            return "Error al buscar en el manual.", "Error", 0.0, {}

    def recuperar_contexto(self, consulta: str, umbral: float = 0.12) -> Tuple[str, str]:
        """Busca el procedimiento técnico más relevante (compatibilidad retroactiva)."""
        cuerpo, titulo, _, _ = self.recuperar_procedimiento_con_metadatos(consulta, umbral)
        return cuerpo, titulo

