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

SPANISH_STOP_WORDS = [
    "a", "al", "algo", "algunas", "algunos", "ante", "antes", "como", "con", "contra",
    "cual", "cuando", "de", "del", "desde", "donde", "durante", "e", "el", "ella",
    "ellas", "ellos", "en", "entre", "era", "erais", "eramos", "eran", "eras", "es",
    "esa", "esas", "ese", "eso", "esos", "esta", "estas", "este", "estos", "fue",
    "fuera", "fueran", "fueras", "fueron", "fuese", "fui", "fuimos", "fuiste", "fuisteis",
    "ha", "habeis", "habia", "habiais", "habiamos", "habian", "habias", "habida",
    "habidas", "habido", "habidos", "habiendo", "han", "has", "hasta", "hay",
    "haya", "hayais", "hayamos", "hayan", "hayas", "he", "hemos", "hube", "hubiera",
    "hubieran", "hubieras", "hubieron", "hubiese", "hubimos", "hubiste", "hubisteis",
    "hubo", "la", "las", "le", "les", "lo", "los", "mas", "me", "mi", "mia", "mias",
    "mio", "mios", "mis", "mucho", "muchos", "muy", "nada", "ni", "no", "nos",
    "nosotras", "nosotros", "nuestra", "nuestras", "nuestro", "nuestros", "o", "os",
    "otra", "otras", "otro", "otros", "para", "pero", "poco", "por", "porque", "que",
    "quien", "quienes", "se", "sea", "seais", "seamos", "sean", "seas", "ser", "sera",
    "seran", "seras", "sere", "seremos", "seria", "seriais", "seriamos", "serian",
    "serias", "si", "sin", "sobre", "sois", "somos", "son", "soy", "su",
    "sus", "suya", "suyas", "suyo", "suyos", "tambien", "tanto", "te", "tenemos",
    "tenga", "tengais", "tengamos", "tengan", "tengas", "tengo", "ti", "tiene", "tienen",
    "tienes", "todo", "todos", "tu", "tus", "tuve", "tuviera", "tuvieran", "tuvieras",
    "tuvieron", "tuviese", "tuvimos", "tuviste", "tuvisteis", "tuvo", "tuya", "tuyas",
    "tuyo", "tuyos", "un", "una", "unas", "uno", "unos", "vosotras", "vosotros",
    "vuestra", "vuestras", "vuestro", "vuestros", "y", "ya", "yo"
]


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
        self.dtc_service: Optional[Any] = None

        if self.rag_version_id in ("candidate_v1", "v1", "rag_candidato_v1"):
            self.rag_version = "RAG_CANDIDATO_V1"
            self._cargar_candidato_v1()
        else:
            self.rag_version = "RAG_BASELINE_F8_3"
            self._indexar_manuales_multimarca()

    def _cargar_candidato_v1(self):
        """Carga artefactos congelados y auditados de RAG_CANDIDATO_V1."""
        directorio_manuales = self.manual_path.parent if self.manual_path.is_file() else self.manual_path
        cand_base = directorio_manuales / "candidates" / "v1"
        ruta_meta_json = cand_base / "metadata" / "metadatos_schema_v2.json"
        ruta_indice = cand_base / "indexes" / "indice_faiss_v1.index"
        ruta_textos = cand_base / "texts"
        ruta_manifest = cand_base / "manifests" / "corpus_manifest.json"

        if not ruta_meta_json.exists() or not ruta_indice.exists():
            logger.error(
                f"Artefactos de RAG_CANDIDATO_V1 incompletos en {cand_base}. Fallback a baseline."
            )
            self.rag_version = "RAG_BASELINE_F8_3 (Fallback)"
            self._indexar_manuales_multimarca()
            return

        try:
            with open(ruta_meta_json, "r", encoding="utf-8") as f:
                lista_meta = json.load(f)

            mapa_metadatos = {}
            for item in lista_meta:
                meta_compat = dict(item)
                proc_id = item.get("doc_id") or item.get("id_procedimiento")
                meta_compat["id_procedimiento"] = proc_id
                if "manual_oem" not in meta_compat:
                    meta_compat["manual_oem"] = item.get("source_title") or item.get("source_id") or "Manual OEM"
                if "archivo_fuente" not in meta_compat:
                    meta_compat["archivo_fuente"] = item.get("archivo_fuente") or f"candidates/v1/texts/{proc_id}.txt"
                tit_norm = item.get("titulo", "").strip().lower()
                mapa_metadatos[tit_norm] = meta_compat

            archivos_registrados = {
                str(item.get("archivo_fuente", "")).replace("\\", "/")
                for item in mapa_metadatos.values()
                if item.get("archivo_fuente")
            }

            archivos_a_leer = []
            if ruta_textos.is_dir():
                archivos_a_leer = sorted(
                    ruta
                    for ruta in ruta_textos.glob("**/*.txt")
                    if ruta.relative_to(ruta_textos).as_posix() in archivos_registrados
                )
            elif ruta_textos.is_file():
                archivos_a_leer = [ruta_textos]

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

            if ruta_manifest.exists():
                with open(ruta_manifest, "rb") as mf:
                    self.corpus_version = hashlib.sha256(mf.read()).hexdigest()[:16]
            else:
                self.corpus_version = hash_global.hexdigest()[:16]

            # Vectorizador con vocabulario idéntico al del índice congelado
            textos_vectorizables = [f"{t}\n{c}" for t, c in zip(self.titulos, self.documentos)]
            self.vectorizador = TfidfVectorizer(
                lowercase=True,
                strip_accents="unicode",
                stop_words=SPANISH_STOP_WORDS,
                ngram_range=(1, 2),
                sublinear_tf=True,
            )
            self.vectorizador.fit(textos_vectorizables)

            # Cargar índice FAISS preconstruido y validado
            if not FAISS_AVAILABLE:
                raise RuntimeError("faiss-cpu no está instalado.")
            self.faiss_index = faiss.read_index(str(ruta_indice))

            # Conectar servicio DTC estructurado
            try:
                from src.infrastructure.dtc.dtc_lookup_service import DtcLookupService
                self.dtc_service = DtcLookupService()
            except Exception as dtc_e:
                logger.warning(f"No se pudo enlazar DtcLookupService en MotorRAG: {dtc_e}")

            logger.info(
                f"RAG_CANDIDATO_V1 cargado exitosamente: {len(self.documentos)} procedimientos indexados "
                f"(Dimensión FAISS: {self.faiss_index.d}, Versión: {self.corpus_version})."
            )
        except Exception as e:
            logger.error(f"Error al cargar RAG_CANDIDATO_V1: {e}. Activando baseline.")
            self.rag_version = "RAG_BASELINE_F8_3 (Fallback Error)"
            self.documentos.clear()
            self.titulos.clear()
            self.metadatos_procedimientos.clear()
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
                sublinear_tf=True
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
        """Expande la consulta del usuario incluyendo términos técnicos estandarizados y códigos DTC."""
        consulta_limpia = str(consulta or "").strip()[:4000]
        consulta_lower = consulta_limpia.lower()
        expansiones = []
        vibracion_al_frenar = "vibr" in consulta_lower and "fren" in consulta_lower
        if vibracion_al_frenar:
            expansiones.append("vibracion pedal freno discos deformados durante frenado")
        
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
            "p2135": "cuerpo de aceleracion mariposa electronica tps",
            "p0011": "valvula solenoide ocv sincronizacion variable vvt",
            "p0700": "transmision automatica cvt caja solenoide sobrecalentamiento",
            "p0841": "sensor presion fluido transmision cvt",
            "cvt": "transmision continuamente variable cvt poleas fluido ns3 nissan",
            "chillido": "pastillas de freno freno",
            "esponjoso": "liquido de frenos purga fuga bombin",
            "cascabelea": "bujias motor encendido ocv vvt",
            "cascabeleo": "bujias motor encendido ocv vvt",
            "se apaga": "valvula iac cuerpo aceleracion ralenti",
            "pestillo": "chapa cerradura puerta seguro pestillo mecanico",
            "elevalunas": "alzacristales vidrio guaya motor ventana",
            "alzacristales": "elevalunas vidrio guaya ventana",
            "limpiaparabrisas": "motor plumas varillaje limpiaparabrisas",
            "common rail": "diesel bomba alta presion inyectores scv",
            "dpf": "filtro particulas hollin adblue def regeneracion",
            "adblue": "urea def regeneracion dpf catalizador",
            "freno de aire": "camion neumatico valvula secador aps compresor",
            "inversor": "hibrido ev alto voltaje igbt bomba enfriamiento",
            "hibrido": "bateria alto voltaje inversor motor electrico ready",
            "valvolina": "caja cambios mecanica rodajes diferencial aceite",
            "gnv": "gas natural vehicular rampa reductor 5ta generacion gas",
            "glp": "gas licuado petroleo rampa reductor 5ta generacion gas",
            "desembraga": "embrague bombin plato prensa disco hidraulico",
            "puerta": "cierre centralizado actuador puerta seguro electrico chapa",
            "desbloquea": "cierre centralizado control remoto actuador puerta",
            "bloqueada": "cierre centralizado actuador puerta chapa cerradura",
            "chapa": "cerradura chapa pestillo puerta trinquete",
            "cerradura": "chapa cerradura pestillo puerta trinquete",
            "humo blanco": "empaquetadura culata refrigerante motor sobrecalentamiento",
            "humo negro": "mezcla rica inyectores filtro aire maf map sensor oxigeno",
            "vibra": "vibracion volante asiento pedal velocidad balanceo alineacion freno soportes",
            "pierde fuerza": "perdida potencia aceleracion subida combustible aire escape transmision",
            "pierde potencia": "perdida potencia aceleracion subida combustible aire escape transmision",
            "culata": "empaquetadura culata refrigerante motor sobrecalentamiento",
            "refrigerante": "termostato ventilador fuga refrigerante culata",
            "alternador": "alternador bateria sistema electrico carga bornes",
            "bateria": "bateria alternador voltaje arranque sistema electrico",
            "acople": "direccion asistida electrica eps mdps columna chasquido volante timon",
            "mariposa": "cuerpo de aceleracion electronico drive-by-wire marcha minima ralenti",
            "can bus": "red de comunicacion multiplexada can bus terminacion 60 ohms dlc osciloscopio",
            "can-h": "red can bus alta velocidad terminacion dlc obd2",
            "evap": "sistema evaporacion emisiones canister valvula purga fuga vacio tanque",
            "canister": "sistema evaporacion emisiones evap purga vacio tanque combustible",
            "sensor de oxigeno": "sonda lambda sensor aire combustible a/f banda ancha calefactor",
            "sensor a/f": "sensor relacion aire combustible banda ancha calefactor mezcla",
            "ibs": "sensor bateria corriente inteligente carga alternador pilotado",
            "termostato": "refrigeracion termostato purga temperatura sobrecalentamiento radiador",
            "p0128": "termostato refrigerante motor temperatura baja refrigeracion",
            "p0440": "sistema evap emisiones purga canister fuga tanque",
            "p0442": "sistema evap emisiones purga canister microfuga vacio",
            "p0455": "sistema evap emisiones purga canister fuga grande tapa tanque",
            "p0620": "circuito control alternador carga inteligente pilotado",
            "u0100": "red can bus perdida comunicacion ecm modulo motor",
            "u0101": "red can bus perdida comunicacion tcm transmision caja",
            "u0121": "red can bus perdida comunicacion abs frenos modulo",
            "abs": "modulo abs frenos purga electrovalvulas sensor rueda bomba escaner sangrado",
            "purgar": "purgado purga sangrado liquido frenos modulo abs aire",
            "gdi": "inyeccion directa gdi tsi bomba alta presion riel combustible hpfp",
            "tsi": "inyeccion directa gdi tsi bomba alta presion riel combustible hpfp",
            "turbo": "turboalimentador wastegate actuador sobrealimentacion intercooler soplido",
            "intercooler": "turbo sobrealimentacion fuga cañeria aire presion underboost",
            "dsg": "transmision doble embrague mecatronica dsg dct robotizada k1 k2",
            "dct": "transmision doble embrague mecatronica dsg dct robotizada k1 k2",
            "epb": "freno estacionamiento electrico epb servomotor caliper trasero modo servicio",
            "freno de mano electrico": "freno estacionamiento electrico epb servomotor caliper trasero modo servicio",
            "haldex": "traccion integral awd haldex acoplador multidisco diferencial trasero",
            "awd": "traccion integral awd haldex acoplador multidisco diferencial trasero",
            "sas": "sensor angulo direccion sas calibracion punto cero esp antiderrape",
            "scv": "valvula reguladora succion scv bomba common rail diesel presion riel",
            "p0299": "turbo sobrealimentacion baja underboost wastegate fuga intercooler",
            "p0234": "turbo sobrepresion overboost wastegate actuador regulador",
            "c1555": "freno estacionamiento electrico epb servomotor caliper motor",
            "c1260": "sensor angulo direccion sas calibracion punto cero esp",
            "retorno": "inyectores common rail retorno probetas valvula scv diesel riel bomba",
            "diesel": "diesel common rail bomba alta presion inyectores scv retorno dpf arranque",
            "arrancador": "motor de arranque solenoide carbones terminal 50 no da marcha clac seco",
            "clac": "motor de arranque solenoide clac seco carbones no da marcha terminal 50",
            "mudo": "motor de arranque solenoide no da marcha clac seco se queda mudo",
            "no da marcha": "motor de arranque solenoide carbones terminal 50 no da marcha clac seco",
            "no da arranque": "motor de arranque solenoide carbones terminal 50 no da marcha clac seco",
            "en caliente": "sensor de posicion cigueñal ckp efecto hall inductivo dilatacion termica bobina p0335 bomba gasolina",
            "calienta": "sensor de posicion cigueñal ckp efecto hall inductivo dilatacion termica bobina p0335 bomba gasolina",
            "enfrie": "sensor de posicion cigueñal ckp efecto hall inductivo dilatacion termica bobina p0335",
            "enfria": "sensor de posicion cigueñal ckp efecto hall inductivo dilatacion termica bobina p0335",
            "gira con fuerza": "arrancador operativo no enciende falta chispa pulso inyeccion sensor ckp cigueñal p0335",
            "no enciende": "sensor ckp cigueñal chispa pulso inyeccion bomba gasolina p0335",
            "cortaran la corriente": "sensor ckp cigueñal rele principal efi encendido p0335",
            "corta corriente": "sensor ckp cigueñal rele principal efi encendido p0335",
            "apaga de golpe": "sensor ckp cigueñal rele principal efi corte encendido p0335",
            "zumbido": "bomba de combustible tanque zumbido alta presion rampa caudal p0087",
            "asiento trasero": "bomba de combustible aforador tanque zumbido presion p0087",
            "asientos de atras": "bomba de combustible aforador tanque zumbido presion p0087",
            "asientos de atrás": "bomba de combustible aforador tanque zumbido presion p0087",
            "ahoga": "falta de combustible presion bomba caudal inyectores mezcla pobre p0171 p0087",
            "tironea": "tironeo perdida potencia combustible bujias bobinas presion caudal p0087 p0300",
            "tirones": "tironeo perdida potencia combustible bujias bobinas presion caudal p0087 p0300",
            "bomba de gasolina": "presion combustible riel caida caudal bajo carga tanque p0087",
            "silbido": "servofreno booster vacio pedal duro fuga linea de vacio multiple admision soplido",
            "servofreno": "booster servofreno linea de vacio pedal duro fuga vacio diafragma valvula check",
            "booster": "servofreno booster vacio pedal duro fuga diafragma retencion valvula check",
            "patina": "disco de embrague desgastado patinando prensa calado en 4ta marcha revoluciones suben sin velocidad",
            "patinando": "disco de embrague desgastado patinando prensa calado en 4ta marcha revoluciones suben sin velocidad",
            "asbesto": "disco de embrague desgastado patinando olor a quemado prensa calado",
            "wub-wub": "rodamiento de maza rodaje de rueda zumbido rodadura ruleman",
            "wub": "rodamiento de maza rodaje de rueda zumbido rodadura ruleman"
        }
        
        # Evitar falsos amigos cuando el motor de arranque sí gira con fuerza
        arranque_falla = any(x in consulta_lower for x in ["no da arranque", "no da marcha", "no gira el motor", "se queda mudo", "clac seco"])
        es_zumbido_mecanico = any(x in consulta_lower for x in ["rueda", "maza", "caja", "transmision", "rodamiento", "rodaje", "curva", "embrague"])
        
        for clave, valor in diccionario_dtc.items():
            if clave == "vibra" and vibracion_al_frenar:
                continue
            if clave in ["arrancador", "clac", "mudo", "no da marcha", "no da arranque"] and not arranque_falla and "gira con fuerza" in consulta_lower:
                continue
            if clave == "zumbido" and es_zumbido_mecanico:
                if any(x in consulta_lower for x in ["rueda", "maza", "curva"]):
                    expansiones.append("rodamiento de maza rodaje de rueda zumbido rodadura alabeo")
                elif any(x in consulta_lower for x in ["caja", "transmision", "embrague", "neutro"]):
                    expansiones.append("rodajes transmision manual eje primario crapodina collarin zumbido caja")
                continue
            if clave in consulta_lower:
                expansiones.append(valor)
                
        if expansiones:
            return f"{consulta_limpia} {' '.join(expansiones)}"
        return consulta_limpia

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
            from src.infrastructure.rag.query_builder import construir_consulta_hibrida
            from src.infrastructure.rag.relevance_filter import reordenar_candidatos_rag

            consulta_hibrida = construir_consulta_hibrida(
                consulta_usuario=consulta,
                macro_sistema=macro_sistema,
                top_fallas=top_fallas,
                codigos_dtc=codigos_dtc,
                marca=marca,
                modelo=modelo,
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
                        "metadatos": (
                            self.metadatos_procedimientos[doc_idx]
                            if doc_idx < len(self.metadatos_procedimientos)
                            else {}
                        ),
                    })

            # Reordenar ponderando por Macro-Sistema ML, códigos DTC y Top-2 de fallas
            conf_ml_val = None
            if top_fallas and len(top_fallas) > 0:
                first_f = top_fallas[0]
                conf_ml_val = float(first_f.get("probabilidad", 0.70) if isinstance(first_f, dict) else getattr(first_f, "probabilidad", 0.70))

            candidatos_reordenados = reordenar_candidatos_rag(
                candidatos,
                macro_sistema=macro_sistema,
                top_fallas=top_fallas,
                codigos_dtc=codigos_dtc,
                confianza_ml=conf_ml_val,
            )

            if not candidatos_reordenados or candidatos_reordenados[0]["similitud"] < umbral_efectivo:
                return (
                    "No se encontró un procedimiento específico en los manuales para esta consulta.",
                    "Coincidencia baja",
                    candidatos_reordenados[0]["similitud"] if candidatos_reordenados else 0.0,
                    {}
                )

            mejor = candidatos_reordenados[0]
            return mejor["documento"], mejor["titulo"], mejor["similitud"], mejor["metadatos"]
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
        if macro_sistema or top_fallas or codigos_dtc:
            doc, tit, sim, _ = self.recuperar_procedimiento_hibrido(
                consulta=consulta,
                macro_sistema=macro_sistema,
                top_fallas=top_fallas,
                codigos_dtc=codigos_dtc,
                umbral=umbral,
            )
            return doc, tit, sim

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
        if macro_sistema or top_fallas or codigos_dtc:
            return self.recuperar_procedimiento_hibrido(
                consulta=consulta,
                macro_sistema=macro_sistema,
                top_fallas=top_fallas,
                codigos_dtc=codigos_dtc,
                marca=marca,
                modelo=modelo,
                umbral=umbral,
            )

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

