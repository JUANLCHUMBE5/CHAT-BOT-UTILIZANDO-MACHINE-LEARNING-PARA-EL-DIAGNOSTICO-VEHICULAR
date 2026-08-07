import os
import hashlib
import numpy as np
try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False

from sklearn.feature_extraction.text import TfidfVectorizer
from src.core.logger import logger
from src.config import settings

class MotorRAG:
    """Clase encargada de indexar y buscar información dentro de los manuales técnicos utilizando FAISS / Cosine Similarity (RAG)."""
    
    def __init__(self, manual_path: str = settings.MANUAL_TALLER_PATH):
        self.manual_path = manual_path
        self.documentos = []
        self.titulos = []
        self.vectorizador = None
        self.faiss_index = None
        self.corpus_version = "manual-ausente"
        self._indexar_manual()

    def _indexar_manual(self):
        if not os.path.exists(self.manual_path):
            logger.error(f"No se encontró el manual técnico en: {self.manual_path}")
            return
            
        try:
            with open(self.manual_path, "r", encoding="utf-8") as f:
                contenido = f.read()
            self.corpus_version = hashlib.sha256(contenido.encode("utf-8")).hexdigest()[:16]
            
            # Separar secciones por delimitador ===
            secciones = [sec.strip() for sec in contenido.split("===") if sec.strip()]
            for sec in secciones:
                lineas = sec.split("\n")
                titulo = lineas[0] if lineas else "Procedimiento de Taller"
                cuerpo = "\n".join(lineas[1:])
                self.titulos.append(titulo)
                self.documentos.append(cuerpo)
                
            # Inicializar matriz TF-IDF
            self.vectorizador = TfidfVectorizer(lowercase=True, strip_accents='unicode')
            matriz_tfidf = self.vectorizador.fit_transform(self.documentos).toarray().astype(np.float32)
            
            # Normalización L2 para producto interno (equivalente a Cosine Similarity en FAISS)
            if not FAISS_AVAILABLE:
                raise RuntimeError("faiss-cpu no está instalado.")
            faiss.normalize_L2(matriz_tfidf)
            
            # Indexar vectores en FAISS IndexFlatIP (Inner Product)
            dimension = matriz_tfidf.shape[1]
            self.faiss_index = faiss.IndexFlatIP(dimension)
            self.faiss_index.add(matriz_tfidf)
            
            logger.info(f"RAG e índice FAISS creados con éxito: {len(self.documentos)} procedimientos indexados (Dimensión: {dimension}).")
        except Exception as e:
            logger.error(f"Error al indexar manual en FAISS: {e}")

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
            "chillido": "pastillas de freno freno",
            "esponjoso": "liquido de frenos purga fuga",
            "cascabelea": "bujias motor encendido",
            "cascabeleo": "bujias motor encendido",
            "se apaga": "valvula iac minimo ralenti"
        }
        
        for clave, valor in diccionario_dtc.items():
            if clave in consulta_lower:
                expansiones.append(valor)
                
        if expansiones:
            return f"{consulta} {' '.join(expansiones)}"
        return consulta

    def recuperar_contexto(self, consulta: str, umbral: float = 0.12) -> tuple:
        """Busca el procedimiento técnico más relevante para la consulta utilizando el índice FAISS (RETRIEVAL)."""
        if self.faiss_index is None or len(self.documentos) == 0:
            return "Manual técnico no indexado o ausente.", "Desconocido"
            
        try:
            consulta_expandida = self._expandir_consulta(consulta)
            consulta_vec = self.vectorizador.transform([consulta_expandida]).toarray().astype(np.float32)
            faiss.normalize_L2(consulta_vec)
            
            similitudes, indices = self.faiss_index.search(consulta_vec, k=1)
            mejor_similitud = float(similitudes[0][0])
            indice_mejor = int(indices[0][0])
            
            if mejor_similitud < umbral or indice_mejor < 0:
                return "No se encontró un procedimiento específico en nuestros manuales para esta consulta.", "Coincidencia baja"
                
            return self.documentos[indice_mejor], self.titulos[indice_mejor]
        except Exception as e:
            logger.error(f"Error durante la búsqueda semántica en FAISS: {e}")
            return "Error al buscar en el manual.", "Error"
