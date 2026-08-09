from typing import Optional, Tuple
import os
import threading
import uuid
import requests
import numpy as np
from pydantic import BaseModel
from src.core.interfaces import IModeloML, IMotorRAG
from src.infrastructure.container import ServiceContainer
from src.core.audio_processor import AudioProcessor
from src.core.session_manager import SessionManager
from src.core.traductor_jerga import normalizar_jerga_peruana
from src.core.sanitizer import sanitizar_prompt_usuario
from src.core.security import anonimizar_identificador
from src.core.gemini_queue import gemini_rate_limiter, SolicitudGeminiEncolada
from src.core.logger import logger
from src.config import settings

from src.core.taxonomy.catalogo_fallas import CATALOGO_TAXONOMIA

_tracker_lock = threading.Lock()

# Vocabulario de componentes automotrices derivado de taxonomía y sistemas vehiculares
VOCABULARIO_COMPONENTES = [
    "freno", "frenos", "pastilla", "pastillas", "disco", "discos", "zapata", "zapatas", "tambor", "pedal",
    "booster", "servofreno", "abs", "pulmon", "secador", "aps", "camion", "camiones",
    "motor", "bujia", "bujias", "bobina", "bobinas", "piston", "pistones", "anillos", "culata", "empaque",
    "faja", "cadena", "distribucion", "tiempo", "aceite", "bomba", "lubricacion", "carter",
    "inyector", "inyectores", "filtro", "combustible", "gasolina", "diesel", "diésel", "petroleo", "riel",
    "gnv", "glp", "gas natural", "reductor", "vaporizador", "riel de gas", "inyector de gas",
    "common rail", "scv", "iac", "mariposa", "acelerador", "aceleracion", "sensor", "oxigeno", "lambda", "maf", "map",
    "embrague", "clutch", "bombin", "prensa", "collarin", "caja", "cambio", "cambios", "transmision",
    "automatica", "mecanica", "cvt", "dsg", "dualogic", "diferencial", "rodaje", "rodajes", "valvolina",
    "refrigeracion", "termostato", "radiador", "ventilador", "electroventilador", "refrigerante", "manguera",
    "electrico", "eléctrico", "alternador", "bateria", "batería", "borne", "bornes", "arranque", "arrancador",
    "solenoide", "ignicion", "fusible", "rele", "cableado",
    "suspension", "suspensión", "amortiguador", "amortiguadores", "buche", "bujes", "trapecio", "rotula", "rótula",
    "palier", "palieres", "homocinetica", "homocinética", "tripoide", "cremallera", "direccion", "dirección",
    "timon", "timón", "volante", "eps", "llanta", "llantas", "rueda", "ruedas", "aro",
    "clima", "aire", "acondicionado", "a/c", "compresor", "gas", "r134a", "evaporador", "condensador",
    "turbo", "turbocompresor", "intercooler", "vgt", "wastegate", "dpf", "fap", "adblue", "def", "escape", "catalizador",
    "puerta", "puertas", "chapa", "chapas", "pestillo", "pestillos", "cerradura", "cerraduras", "seguro", "seguros",
    "control", "mando", "remoto", "actuador", "trinquete", "manija", "tirador",
    "ventana", "ventanas", "vidrio", "vidrios", "luna", "lunas", "elevalunas", "alzacristales", "guaya",
    "limpiaparabrisas", "pluma", "plumas", "parabrisas", "plumillas",
    "hibrido", "híbrido", "ev", "inversor", "alto voltaje", "hv", "prius", "regenerativo",
    "caliper", "mordaza", "bomba principal de freno", "modulo abs", "modulo de abs",
    "calefaccion", "radiador de calefaccion", "soplador", "ventilador de cabina", "resistencia de soplador",
    "eje", "eje posterior", "eje rigido", "cruceta", "junta universal", "cardan", "acople viscoso",
    "faro", "luz delantera", "claxon", "bocina", "lavaparabrisas", "bomba lavaparabrisas",
    "canister", "valvula de purga", "convertidor catalitico", "multiple de escape", "tapa de combustible",
    "sensor de detonacion", "eje balanceador", "bujia de precalentamiento", "soporte de motor",
    "valvula de admision", "valvula de escape", "tapa de valvulas", "pcv", "filtro de aire",
    "regulador de presion", "tanque de combustible", "tps", "sensor de posicion del acelerador",
    "liquido de direccion", "direccion hidraulica", "convertidor de par", "cubo de rueda", "tpms"
]


def _vocabulario_desde_taxonomia() -> set[str]:
    """Extrae terminos utiles para que el filtro evolucione con la taxonomia."""
    ignoradas = {
        "para", "con", "del", "los", "las", "una", "por", "falla", "sistema",
        "alta", "baja", "media", "motor", "vehiculo", "vehicular",
    }
    terminos: set[str] = set()
    for falla in CATALOGO_TAXONOMIA.values():
        textos = [falla.sistema, falla.falla_principal, *falla.posibles_causas]
        for texto in textos:
            palabras = "".join(
                caracter.lower() if caracter.isalnum() else " " for caracter in texto
            ).split()
            terminos.update(
                palabra for palabra in palabras if len(palabra) >= 3 and palabra not in ignoradas
            )
    return terminos


VOCABULARIO_COMPONENTES = sorted(
    set(VOCABULARIO_COMPONENTES) | _vocabulario_desde_taxonomia()
)

VERBOS_FALLA = [
    "no abre", "no cierra", "trabado", "trabada", "trancado", "trancada", "chueco", "chueca", "inclinado", "inclinada",
    "desalineado", "desalineada", "bloqueado", "bloqueada", "desbloquea", "salta", "no sube", "no baja", "se cayo", "se cayó",
    "chirria", "chirría", "chillido", "rechina", "rechinido", "vibra", "vibracion", "vibración", "tiembla", "cascabelea",
    "cascabeleo", "golpeteo", "crujido", "chasquido", "sonido", "ruido", "se apaga", "apaga", "pierde fuerza", "sin fuerza",
    "no arranca", "cuesta arrancar", "jalonea", "jaloneo", "tirones", "gotea", "fuga", "bota", "humo", "recalienta",
    "hierve", "patina", "esponjoso", "duro", "pesado", "no responde", "no funciona", "falla", "defectuoso", "quemado", "roto", "partido",
    "suelto", "oxido", "sulfatado", "baja presion", "alta presion", "no enfria", "no marca", "oscila",
    "permanece encendido", "se amarra", "bambolea", "se inclina", "rebota", "pulsa", "demora en acoplar",
    "flujo debil", "poca presion", "olor", "raspa", "golpea", "se mueve demasiado", "trabaja disparejo"
]

# Mantener compatibilidad retroactiva con PALABRAS_MECANICAS
PALABRAS_MECANICAS = VOCABULARIO_COMPONENTES[:30]


class ResultadoDiagnostico(BaseModel):
    """DTO inmutable de respuesta de diagnóstico por solicitud (evita condiciones de carrera)."""
    respuesta_texto: str
    diagnostico_ml: str
    confianza_ml: float
    contexto_manual: str
    titulo_manual: str
    similitud_rag: float = 0.0
    requiere_revision_humana: bool = False
    estado_sesion: str = "completado"
    modo_diagnostico: str = "completo_ml_rag_llm"
    llm_usado: bool = False
    llm_modelo: str | None = None
    tokens_entrada: int = 0
    tokens_salida: int = 0
    posicion_cola: int = 0
    tiempo_espera_cola: float = 0.0
    solicitud_id: str | None = None
    sintoma_evaluado: str = ""


class GestorDiagnostico:
    """
    Clase orquestadora THREAD-SAFE encargada de coordinar el flujo de diagnóstico tripartito (ML + RAG + LLM).
    No almacena estado mutable de solicitudes previas.
    """
    
    def __init__(self, gemini_api_key: str = "", modelo_ml: Optional[IModeloML] = None, motor_rag: Optional[IMotorRAG] = None):
        self.api_key = gemini_api_key or settings.GEMINI_API_KEY
        # Inyección de dependencias vía ServiceContainer Singleton (evita duplicación de memoria)
        self.modelo_ml: IModeloML = modelo_ml or ServiceContainer.get_modelo_ml()
        self.motor_rag: IMotorRAG = motor_rag or ServiceContainer.get_motor_rag()
        self.procesador_audio = AudioProcessor()
        self.session_manager = SessionManager()

    def _es_saludo_o_contacto_inicial(self, texto: str) -> Tuple[bool, str]:
        """Detecta si el mensaje es un saludo o contacto inicial sin detalles mecánicos."""
        texto_limpio = texto.strip().lower()

        saludos = [
            "hola", "holaa", "holaaa", "buenas", "buenos dias", "buenas tardes", "buenas noches",
            "hola tengo un problema", "hola tengo problemas",
            "tengo una falla", "hola buenas", "saludos", "hola que tal", "ayuda", "consulta"
        ]
        
        tiene_componente = any(pm in texto_limpio for pm in VOCABULARIO_COMPONENTES)
        tiene_verbo = any(vf in texto_limpio for vf in VERBOS_FALLA)
        
        if texto_limpio in saludos or (any(s in texto_limpio for s in ["hola", "buenas"]) and not tiene_componente and not tiene_verbo):
            return True, "👋 ¡Hola! Bienvenido a CarBot. Por favor, cuéntame: **¿Qué problema o síntoma presenta tu vehículo hoy?**"
        return False, ""

    @staticmethod
    def _es_continuacion_contextual(texto: str) -> bool:
        """Reconoce datos adicionales que deben unirse al síntoma anterior."""
        limpio = texto.strip().lower()
        conectores = (
            "pero ", "ademas ", "además ", "tambien ", "también ",
            "y tambien ", "y además ", "el auto es ", "el carro es ",
            "funciona con ", "usa ", "es a gnv", "es gnv", "es a glp",
            "cuando usa ", "solo pasa ", "me olvide ", "me olvidé ",
        )
        return any(limpio.startswith(valor) or valor in limpio for valor in conectores)

    def _es_consulta_ambigua(self, texto: str) -> Tuple[bool, str]:
        """Determina si la consulta del usuario es incompleta o ambigua utilizando contexto técnico dinámico."""
        texto_limpio = texto.strip().lower()
        words = texto_limpio.split()
        
        frases_ambiguas = [
            "el carro falla", "mi auto falla", "mi carro falla", "tengo un problema", "tengo problemas",
            "tengo una falla", "ayuda", "falla el carro", "mi vehiculo falla", "mi coche falla",
            "falla mi carro", "mi auto tiene una falla", "ayuda con mi carro"
        ]
        
        # Consulta explícitamente genérica o vacía
        if texto_limpio in frases_ambiguas:
            return True, "⚠️ Por favor, especifique el síntoma con más detalle (ej. si ocurre al frenar, al acelerar, al arrancar, al abrir puertas o si se escucha algún ruido/chillido)."

        # Si el mensaje es descriptivo (>= 6 palabras) no declararlo ambiguo ciegamente
        if len(words) >= 6:
            return False, ""

        tiene_componente = any(comp in texto_limpio for comp in VOCABULARIO_COMPONENTES)
        tiene_verbo_falla = any(vf in texto_limpio for vf in VERBOS_FALLA)
        
        if tiene_componente and tiene_verbo_falla:
            return False, ""

        if len(words) < 3 or (not tiene_componente and not tiene_verbo_falla):
            # Preguntas de aclaración contextualizadas según el sistema mencionado
            if any(k in texto_limpio for k in ["puerta", "chapa", "cerradura", "pestillo", "seguro"]):
                return True, "⚠️ Por favor, especifique el síntoma con más detalle. Por ejemplo: ¿El control remoto acciona las demás puertas? ¿Se escucha accionar el actuador eléctrico? ¿La puerta abre manualmente con la llave o la manija exterior?"
            if any(k in texto_limpio for k in ["vidrio", "luna", "elevalunas", "ventana", "alzacristales"]):
                return True, "⚠️ Por favor, especifique el síntoma con más detalle. Por ejemplo: ¿El motor del elevalunas emite sonido al presionar el botón? ¿El vidrio se cayó dentro de la puerta o está atascado en las guías?"
            return True, "⚠️ Por favor, especifique el síntoma con más detalle (ej. si ocurre al frenar, al acelerar, al arrancar, al abrir puertas o si se escucha algún ruido/chillido)."

        return False, ""

    def _registrar_en_tracker(
        self, 
        placa: str, 
        marca_modelo: str, 
        sintoma: str, 
        diagnostico_ml: str, 
        campos_completos: int = 1
    ):
        """Registra el evento de diagnóstico de forma anónima y segura en data/tracker_diagnosticos.csv."""
        try:
            import csv
            import datetime
            import time

            tracker_path = settings.TRACKER_PATH
            os.makedirs(os.path.dirname(tracker_path), exist_ok=True)

            nueva_fila = [
                time.time_ns(),
                "Post-test",
                datetime.date.today().isoformat(),
                anonimizar_identificador(placa),
                marca_modelo or "Generico",
                sintoma,
                diagnostico_ml,
                diagnostico_ml,
                campos_completos,
                1,
                1,
            ]
            encabezado = [
                "item", "fase", "fecha", "placa", "marca_modelo", "sintoma",
                "falla_real", "chatbot_prediccion", "campos_completos",
                "tiempo_diagnostico_minutos", "prediccion_correcta",
            ]

            with _tracker_lock:
                archivo_nuevo = not os.path.exists(tracker_path) or os.path.getsize(tracker_path) == 0
                with open(tracker_path, mode="a", newline="", encoding="utf-8") as f:
                    writer = csv.writer(f)
                    if archivo_nuevo:
                        writer.writerow(encabezado)
                    writer.writerow(nueva_fila)
        except Exception as e:
            logger.warning(f"No se pudo registrar en tracker CSV: {e}")

    def procesar_consulta_texto(
        self, 
        texto_usuario: str, 
        placa: Optional[str] = None, 
        marca_modelo: Optional[str] = None, 
        session_id: Optional[str] = None,
        remitente: Optional[str] = None,
        proveedor: str = "meta",
        taller_id: Optional[str] = None,
        usuario_id: Optional[str] = None,
        conversacion_id: Optional[str] = None,
        slot_gemini_preconcedido: Optional[bool] = None,
        diferir_encolado_persistente: bool = False,
    ) -> ResultadoDiagnostico:
        """
        Flujo tripartito secuencial THREAD-SAFE para consultas de texto:
        1. ML clasifica el síntoma y calcula confianza.
        2. RAG recupera el procedimiento del manual de taller.
        3. Gemini LLM sintetiza la respuesta técnica estructurada en 3 secciones.
        """
        # 0. Sanitizar y normalizar entrada
        texto_sanitizado = sanitizar_prompt_usuario(texto_usuario)
        texto_normalizado = normalizar_jerga_peruana(texto_sanitizado)

        placa_anonima = anonimizar_identificador(placa or "")
        session_id_anon = anonimizar_identificador(session_id or "")
        logger.info(
            f"Procesando consulta texto (Longitud: {len(texto_normalizado)} caracteres) | "
            f"Placa Anonimizada: {placa_anonima} | Session ID Anonimizado: {session_id_anon} | Proveedor: {proveedor}"
        )

        # 0.1. Validar si es un saludo / contacto inicial sin síntoma
        es_saludo, mensaje_saludo = self._es_saludo_o_contacto_inicial(texto_normalizado)
        if es_saludo:
            if session_id:
                self.session_manager.reiniciar_sesion(session_id)
            return ResultadoDiagnostico(
                respuesta_texto=mensaje_saludo,
                diagnostico_ml="Consulta General / Saludo",
                confianza_ml=1.0,
                contexto_manual="",
                titulo_manual="",
                modo_diagnostico="saludo",
            )

        # Identificar clave de sesión multiturno
        clave_sesion = session_id or (placa if placa not in (None, "REST-API", "WAPP-01") else None)

        if clave_sesion:
            sesion_anterior = self.session_manager.obtener_sesion(clave_sesion)
            if (
                sesion_anterior
                and sesion_anterior.sintomas
                and sesion_anterior.estado == "completo"
                and not self._es_continuacion_contextual(texto_normalizado)
            ):
                self.session_manager.reiniciar_sesion(clave_sesion)
            sesion = self.session_manager.acumular_input_usuario(
                session_id=clave_sesion,
                texto_usuario=texto_normalizado,
                placa=placa,
                marca_modelo=marca_modelo
            )
            texto_evaluar = sesion.obtener_sintoma_completo()
            marca_evaluar = marca_modelo or sesion.marca_modelo
            placa_evaluar = placa or sesion.placa
        else:
            texto_evaluar = texto_normalizado
            marca_evaluar = marca_modelo
            placa_evaluar = placa

        # 0.2 Validar ambigüedad / datos faltantes
        es_ambigua, mensaje_aclaracion = self._es_consulta_ambigua(texto_evaluar)
        if es_ambigua:
            if clave_sesion:
                self.session_manager.obtener_o_crear_sesion(clave_sesion).estado = "esperando_clarificacion"
            return ResultadoDiagnostico(
                respuesta_texto=mensaje_aclaracion,
                diagnostico_ml="Consulta Ambigua / Datos Faltantes",
                confianza_ml=0.0,
                contexto_manual="",
                titulo_manual="",
                requiere_revision_humana=True,
                estado_sesion="esperando_clarificacion",
                modo_diagnostico="esperando_clarificacion",
            )

        # =========================================================
        # PASO 1: Machine Learning Supervisado (Predicción de falla)
        # =========================================================
        diagnostico_predictivo, confianza = self.modelo_ml.predecir_falla_con_confianza(texto_evaluar)
        
        # =========================================================
        # PASO 2: Motor RAG (Recuperación del manual de procedimientos)
        # =========================================================
        if hasattr(self.motor_rag, "recuperar_contexto_con_similitud"):
            contexto_manual, titulo_manual, similitud_rag = (
                self.motor_rag.recuperar_contexto_con_similitud(texto_evaluar)
            )
        else:
            contexto_manual, titulo_manual = self.motor_rag.recuperar_contexto(texto_evaluar)
            similitud_rag = 0.0

        rag_valido = (
            contexto_manual
            and "No se encontró" not in contexto_manual
            and "Manual técnico no indexado" not in contexto_manual
            and "Coincidencia baja" not in titulo_manual
            and "Desconocido" not in titulo_manual
            and "Error" not in titulo_manual
        )

        # ML y RAG conservan medidas separadas: RAG no aumenta la confianza ML.
        if confianza < 0.10:
            if rag_valido:
                diagnostico_predictivo = f"Hipótesis ML de baja confianza: {diagnostico_predictivo}"
                requiere_revision_humana = True
            else:
                return ResultadoDiagnostico(
                    respuesta_texto=(
                        "⚠️ **Síntoma no reconocido con suficiente certeza (< 10%)**\n\n"
                        "El modelo de Machine Learning requiere una descripción un poco más detallada del síntoma.\n"
                        "Por favor, indique el sistema o componente afectado (ej. **frenos**, **motor**, **carrocería/puertas**, **encendido/batería**, **transmisión** o **acelerador/mínimo**)."
                    ),
                    diagnostico_ml="Baja Confianza / Indeterminado",
                    confianza_ml=confianza,
                    contexto_manual="",
                    titulo_manual="",
                    similitud_rag=similitud_rag,
                    requiere_revision_humana=True,
                    modo_diagnostico="baja_confianza",
                )
        else:
            requiere_revision_humana = confianza < settings.diagnostic.confidence_threshold

        if rag_valido and not getattr(self.motor_rag, "corpus_validado", False):
            requiere_revision_humana = True
        
        # =========================================================
        # PASO 3: Gemini LLM (Síntesis técnica y estructuración)
        # =========================================================
        respuesta_explicativa, uso_llm = self._generar_respuesta_con_metadatos(
            pregunta=texto_evaluar,
            diagnostico_ml=diagnostico_predictivo,
            confianza_ml=confianza,
            contexto_manual=contexto_manual,
            titulo_manual=titulo_manual,
            requiere_revision_humana=requiere_revision_humana,
            remitente=remitente,
            proveedor=proveedor,
            taller_id=taller_id,
            usuario_id=usuario_id,
            conversacion_id=conversacion_id,
            slot_gemini_preconcedido=slot_gemini_preconcedido,
            diferir_encolado_persistente=diferir_encolado_persistente,
        )
        
        # Registrar en tracker CSV
        self._registrar_en_tracker(
            placa=placa_evaluar or "DESCONOCIDO",
            marca_modelo=marca_evaluar or "Generico",
            sintoma=texto_evaluar,
            diagnostico_ml=diagnostico_predictivo,
            campos_completos=1
        )

        # Conservar brevemente el contexto para mensajes complementarios como
        # "pero el auto es a GNV". Una consulta nueva reinicia la sesión arriba.
        if clave_sesion:
            self.session_manager.obtener_o_crear_sesion(clave_sesion).estado = "completo"
        
        modo = uso_llm.get("modo", "completo_ml_rag_llm" if uso_llm.get("usado") else "diagnostico_degradado_ml_rag")

        return ResultadoDiagnostico(
            respuesta_texto=respuesta_explicativa,
            diagnostico_ml=diagnostico_predictivo,
            confianza_ml=confianza,
            contexto_manual=contexto_manual,
            titulo_manual=titulo_manual,
            similitud_rag=similitud_rag,
            requiere_revision_humana=requiere_revision_humana,
            modo_diagnostico=modo,
            solicitud_id=uso_llm.get("solicitud_id"),
            llm_usado=uso_llm.get("usado", False),
            llm_modelo=uso_llm.get("modelo"),
            tokens_entrada=uso_llm.get("tokens_entrada", 0),
            tokens_salida=uso_llm.get("tokens_salida", 0),
            posicion_cola=uso_llm.get("posicion_cola", 0),
            tiempo_espera_cola=uso_llm.get("tiempo_espera_cola", 0.0),
            sintoma_evaluado=texto_evaluar,
        )

    def procesar_consulta_audio(self, audio_id: str, datos_audio_vector: Optional[np.ndarray] = None) -> str:
        """Procesa análisis acústico espectral (FFT + RMS) sobre la señal de audio."""
        if datos_audio_vector is None or len(datos_audio_vector) == 0:
            raise ValueError(
                "No se recibieron muestras reales de audio. "
                "No es seguro emitir un diagnostico acustico simulado."
            )
        
        tipo_senal, diagnostico_acustico = self.procesador_audio.analizar_audio(datos_audio_vector)
        
        datos_norm = self.procesador_audio.normalizar_audio(datos_audio_vector.flatten())
        fft_resultado = np.abs(np.fft.rfft(datos_norm))
        frecuencias = np.fft.rfftfreq(len(datos_norm), d=1.0/self.procesador_audio.samplerate)
        freq_dominante = int(frecuencias[np.argmax(fft_resultado)])

        return (
            f"🎙️ **Análisis Acústico Espectral de Audio**\n\n"
            f"• **Tipo de señal detectada:** {tipo_senal}\n"
            f"• **Frecuencia Dominante (FFT):** {freq_dominante} Hz\n"
            f"• **Diagnóstico Sugerido:** {diagnostico_acustico}\n"
            f"• **Recomendación:** Se sugiere inspección física directa en el taller mecánico."
        )

    def _generar_respuesta_con_metadatos(
        self, 
        pregunta: str, 
        diagnostico_ml: str, 
        contexto_manual: str, 
        confianza_ml: float = 0.85, 
        titulo_manual: str = "",
        requiere_revision_humana: bool = False,
        remitente: Optional[str] = None,
        proveedor: str = "meta",
        taller_id: Optional[str] = None,
        usuario_id: Optional[str] = None,
        conversacion_id: Optional[str] = None,
        slot_gemini_preconcedido: Optional[bool] = None,
        diferir_encolado_persistente: bool = False,
    ) -> tuple[str, dict]:
        """
        Sintetiza la respuesta final con Gemini LLM integrando Síntoma + ML + RAG.
        Envía la API key exclusivamente mediante encabezado x-goog-api-key (no en la URL).
        Maneja la cola real de 12 req/min y recurre a fallback degradado solo ante falla real de red o indisponibilidad.
        """
        confianza_pct = int(confianza_ml * 100)
        alerta_revision = (
            "\n⚠️ *Nota:* Se requiere inspección física obligatoria: la confianza ML "
            "es insuficiente o el procedimiento RAG aún no tiene fuente OEM validada.\n"
            if requiere_revision_humana
            else ""
        )
        
        prompt_sistema = f"""
        Eres 'CarBot', el asistente técnico de diagnóstico de precisión para mecánicos de taller automotriz.

        INFORMACIÓN CLAVE DE IA:
        - Diagnóstico Principal (Machine Learning): {diagnostico_ml} (Confianza del modelo: {confianza_pct}%){alerta_revision}
        - Manual Técnico Recuperado (RAG): [{titulo_manual}]
        {contexto_manual}
        
        Consulta técnica del usuario: "{pregunta}"
        
        REGLAS DE SEGURIDAD:
        1. La predicción ML es una HIPÓTESIS, no una falla confirmada.
        2. Usa exclusivamente pruebas y procedimientos presentes en el contexto RAG. No inventes pares de apriete, piezas ni pasos.
        3. Si se marca revisión humana, exige inspección antes de desmontar o reemplazar componentes.
        4. Si ML y manual no son coherentes, indícalo y limita la respuesta a pruebas de verificación seguras.
        5. Si la consulta menciona GNV/GLP y pérdida de fuerza, indica primero una prueba comparativa controlada gasolina vs gas. Si solo falla a gas, prioriza presión del reductor, filtros, inyectores y calibración GNV; si falla con ambos, revisa encendido, admisión, escape, compresión y alimentación. No atribuyas la falla al embrague solo por mencionar GNV.
        6. Estructura la respuesta en las siguientes 3 secciones:

        🛠️ **1. Posible Falla Vehicular**
        Presenta la hipótesis principal ({diagnostico_ml}), su confianza ({confianza_pct}%) y qué evidencia falta para confirmarla.

        📖 **2. Procedimiento Técnico de Reparación**
        Primero pruebas de confirmación; luego, solo si corresponde, pasos extraídos del manual RAG.

        ⏱️ **3. Tiempo Estimado y Gravedad**
        Indica urgencia, riesgos y necesidad de validación por el mecánico. No prometas un tiempo si el manual no lo sustenta.
        """
        
        if self.api_key:
            slot_disponible = (
                gemini_rate_limiter.intentar_adquirir_slot()
                if slot_gemini_preconcedido is None
                else slot_gemini_preconcedido
            )
            if slot_disponible:
                try:
                    modelo = getattr(settings, "GEMINI_MODEL", "gemini-3.5-flash-lite")
                    url = f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent"
                    headers = {
                        "Content-Type": "application/json",
                        "x-goog-api-key": self.api_key,
                    }
                    payload = {
                        "contents": [{"parts": [{"text": prompt_sistema}]}]
                    }
                    response = requests.post(url, json=payload, headers=headers, timeout=10)
                    if response.status_code == 200:
                        data = response.json()
                        metadata = data.get("usageMetadata", {})
                        texto_gemini = data['candidates'][0]['content']['parts'][0]['text'].strip()
                        return texto_gemini, {
                            "usado": True,
                            "modelo": modelo,
                            "modo": "completo_ml_rag_llm",
                            "tokens_entrada": int(metadata.get("promptTokenCount", max(1, len(prompt_sistema) // 4))),
                            "tokens_salida": int(metadata.get("candidatesTokenCount", max(1, len(texto_gemini) // 4))),
                        }
                    logger.warning(f"[Gemini API] Código HTTP {response.status_code}; activando fallback degradado.")
                except Exception as e:
                    logger.error(f"[Gemini API Error] Fallo al consultar Gemini: {e}. Activando fallback degradado.")
            else:
                proveedor_normalizado = "meta" if proveedor.lower() in ("meta", "whatsapp") else proveedor.lower()
                if diferir_encolado_persistente:
                    # El webhook creará el trabajo dentro de su misma transacción,
                    # una vez exista el diagnóstico al que debe quedar vinculado.
                    solicitud = SolicitudGeminiEncolada(
                        id=str(uuid.uuid4()),
                        sintoma=pregunta,
                        diagnostico_ml=diagnostico_ml,
                        confianza_ml=confianza_ml,
                        contexto_manual=contexto_manual,
                        titulo_manual=titulo_manual,
                        requiere_revision_humana=requiere_revision_humana,
                        remitente=remitente,
                        proveedor=proveedor_normalizado,
                        taller_id=taller_id,
                        usuario_id=usuario_id,
                        conversacion_id=conversacion_id,
                    )
                    posicion = gemini_rate_limiter.tamaño_cola() + 1
                    espera_segundos = gemini_rate_limiter.tiempo_espera_estimado()
                else:
                    solicitud, posicion, espera_segundos = gemini_rate_limiter.encolar_solicitud(
                        sintoma=pregunta,
                        diagnostico_ml=diagnostico_ml,
                        confianza_ml=confianza_ml,
                        contexto_manual=contexto_manual,
                        titulo_manual=titulo_manual,
                        requiere_revision_humana=requiere_revision_humana,
                        remitente=remitente,
                        proveedor=proveedor_normalizado,
                        taller_id=taller_id,
                        usuario_id=usuario_id,
                        conversacion_id=conversacion_id,
                    )
                logger.info(
                    f"[Gemini Queue] Solicitud {solicitud.id[:8]} colocada en cola de espera (Posición: {posicion}, Espera: ~{espera_segundos}s, Proveedor: {proveedor})."
                )
                mensaje_cola = (
                    f"⏳ *Analizando consulta (cola #{posicion})*\n"
                    f"Hipótesis preliminar, no confirmada: *{diagnostico_ml}* ({confianza_pct}%).\n"
                    "En breve recibirás el resumen; el detalle quedará en el panel."
                )
                return mensaje_cola, {
                    "usado": False,
                    "modelo": None,
                    "modo": "en_cola_gemini",
                    "solicitud_id": solicitud.id,
                    "tokens_entrada": 0,
                    "tokens_salida": 0,
                    "posicion_cola": posicion,
                    "tiempo_espera_cola": espera_segundos,
                }
                
        # Fallback local de emergencia marcado explícitamente como modo degradado
        no_manual = "No se encontró" in contexto_manual or "Coincidencia baja" in titulo_manual
        
        seccion_1 = f"🛠️ **1. Posible Falla Vehicular (Modo Degradado ML+RAG):**\n• **Diagnóstico Sugerido (ML):** {diagnostico_ml}\n• **Certeza del Modelo:** {confianza_pct}%{alerta_revision}"
        
        if no_manual:
            seccion_2 = "📖 **2. Procedimiento Técnico de Reparación:**\n⚠️ *Nota:* No se encontró un procedimiento específico en el manual de taller para esta consulta. Se sugiere revisión visual directa."
            seccion_3 = "⏱️ **3. Tiempo Estimado y Gravedad:**\n• **Tiempo Estimado:** 30-45 minutos (Evaluación inicial)\n• **Gravedad:** Por determinar en taller"
        else:
            seccion_2 = f"📖 **2. Procedimiento Técnico de Reparación ({titulo_manual}):**\n{contexto_manual}"
            seccion_3 = "⏱️ **3. Tiempo Estimado y Gravedad:**\n• **Recomendación Técnica:** Siga los pasos del manual de taller adjunto y realice las pruebas de verificación correspondientes."
            
        return f"{seccion_1}\n\n{seccion_2}\n\n{seccion_3}", {
            "usado": False,
            "modelo": None,
            "modo": "diagnostico_degradado_ml_rag",
            "tokens_entrada": 0,
            "tokens_salida": 0,
        }

    def generar_respuesta_conversacional(
        self,
        pregunta: str,
        diagnostico_ml: str,
        contexto_manual: str,
        confianza_ml: float = 0.85,
        titulo_manual: str = "",
        requiere_revision_humana: bool = False,
    ) -> str:
        """API compatible: devuelve únicamente el texto generado."""
        texto, _ = self._generar_respuesta_con_metadatos(
            pregunta=pregunta,
            diagnostico_ml=diagnostico_ml,
            contexto_manual=contexto_manual,
            confianza_ml=confianza_ml,
            titulo_manual=titulo_manual,
            requiere_revision_humana=requiere_revision_humana,
        )
        return texto
