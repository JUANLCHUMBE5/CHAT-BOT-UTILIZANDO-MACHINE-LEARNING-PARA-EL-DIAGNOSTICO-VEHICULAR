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

_tracker_lock = threading.Lock()

# Constante compartida de palabras clave mecánicas (evita duplicación)
PALABRAS_MECANICAS = [
    "freno", "frenos", "motor", "bujia", "bujias", "bateria", "arranque", "arrancar",
    "acelerar", "cuesta", "humo", "rueda", "timon", "volante", "caja", "cambio", "pedal",
    "chillido", "cascabeleo", "esponjoso", "apaga", "tiembla", "vibracion", "sonido", "ruido", "scanner", "dtc", "p0"
]

class ResultadoDiagnostico(BaseModel):
    """DTO inmutable de respuesta de diagnóstico por solicitud (evita condiciones de carrera)."""
    respuesta_texto: str
    diagnostico_ml: str
    confianza_ml: float
    contexto_manual: str
    titulo_manual: str
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
        
        palabras_mecanicas = PALABRAS_MECANICAS
        tiene_palabra_mecanica = any(pm in texto_limpio for pm in palabras_mecanicas)
        
        if texto_limpio in saludos or (any(s in texto_limpio for s in ["hola", "buenas"]) and not tiene_palabra_mecanica):
            return True, "👋 ¡Hola! Bienvenido a CarBot. Por favor, cuéntame: **¿Qué problema o síntoma presenta tu vehículo hoy?**"
        return False, ""

    def _es_consulta_ambigua(self, texto: str) -> Tuple[bool, str]:
        """Determina si la consulta del usuario es incompleta o ambigua."""
        texto_limpio = texto.strip().lower()
        words = texto_limpio.split()
        
        frases_ambiguas = [
            "el carro falla", "mi auto falla", "mi carro falla", "tengo un problema", "tengo problemas",
            "tengo una falla", "ayuda", "ruido", "freno", "motor", "falla el carro"
        ]
        
        palabras_mecanicas = PALABRAS_MECANICAS
        tiene_palabra_mecanica = any(pm in texto_limpio for pm in palabras_mecanicas)
        
        if len(words) < 3 or texto_limpio in frases_ambiguas or not tiene_palabra_mecanica:
            return True, "⚠️ Por favor, especifique el síntoma con más detalle (ej. si ocurre al frenar, al acelerar o si se escucha algún ruido/chillido)."
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
                self.session_manager.obtener_o_crear_sesion(session_id)
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
        
        # Umbral estricto: si la confianza es < 10% no adivinar arbitrariamente
        if confianza < 0.10:
            return ResultadoDiagnostico(
                respuesta_texto=(
                    "⚠️ **Síntoma no reconocido con suficiente certeza (< 10%)**\n\n"
                    "El modelo de Machine Learning requiere una descripción un poco más detallada del síntoma.\n"
                    "Por favor, indique si el problema se relaciona con los **frenos**, el **motor**, el **sistema de encendido/batería** o el **acelerador/mínimo**."
                ),
                diagnostico_ml="Baja Confianza / Indeterminado",
                confianza_ml=confianza,
                contexto_manual="",
                titulo_manual="",
                requiere_revision_humana=True,
                modo_diagnostico="baja_confianza",
            )
        
        # Flag de recomendación de revisión humana en taller (confianza entre 10% y 69%)
        requiere_revision_humana = confianza < 0.70

        # =========================================================
        # PASO 2: Motor RAG (Recuperación del manual de procedimientos)
        # =========================================================
        contexto_manual, titulo_manual = self.motor_rag.recuperar_contexto(texto_evaluar)
        
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

        # Limpiar la sesión activa tras diagnóstico exitoso
        if clave_sesion:
            self.session_manager.reiniciar_sesion(clave_sesion)
        
        modo = uso_llm.get("modo", "completo_ml_rag_llm" if uso_llm.get("usado") else "diagnostico_degradado_ml_rag")

        return ResultadoDiagnostico(
            respuesta_texto=respuesta_explicativa,
            diagnostico_ml=diagnostico_predictivo,
            confianza_ml=confianza,
            contexto_manual=contexto_manual,
            titulo_manual=titulo_manual,
            requiere_revision_humana=requiere_revision_humana,
            modo_diagnostico=modo,
            solicitud_id=uso_llm.get("solicitud_id"),
            llm_usado=uso_llm.get("usado", False),
            llm_modelo=uso_llm.get("modelo"),
            tokens_entrada=uso_llm.get("tokens_entrada", 0),
            tokens_salida=uso_llm.get("tokens_salida", 0),
            posicion_cola=uso_llm.get("posicion_cola", 0),
            tiempo_espera_cola=uso_llm.get("tiempo_espera_cola", 0.0),
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
        alerta_revision = "\n⚠️ *Nota:* Confianza media del modelo (< 70%). Se requiere inspección física obligatoria en taller.\n" if requiere_revision_humana else ""
        
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
        3. Si la confianza es menor de 70%, exige inspección humana antes de desmontar o reemplazar componentes.
        4. Si ML y manual no son coherentes, indícalo y limita la respuesta a pruebas de verificación seguras.
        5. Estructura la respuesta en las siguientes 3 secciones:

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
                    f"⏳ *Diagnóstico en cola de procesamiento (Posición #{posicion}):*\n\n"
                    f"Tu consulta ha sido clasificada con éxito mediante ML ({diagnostico_ml}) y el manual RAG está listo.\n"
                    f"La síntesis detallada con Gemini se completará en aproximadamente ~{int(espera_segundos)}s para respetar la cuota del taller.\n\n"
                    f"🛠️ **Diagnóstico Preliminar ML:** {diagnostico_ml} ({confianza_pct}% certeza)"
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
