"""
Orquestador principal del flujo tripartito de diagnóstico automotriz (ML + RAG + LLM).
Desacoplado y modularizado respetando Clean Architecture.
"""

from __future__ import annotations

from typing import Any, List, Optional, Tuple

import numpy as np
import requests
from requests.adapters import HTTPAdapter
from urllib3.util import Retry

from src.config import settings
from src.core.audio_processor import AudioProcessor

# Re-exports de compatibilidad y lógica desacoplada desde submódulos de src.core.diagnostico
from src.core.diagnostico import (
    PALABRAS_MECANICAS,
    VERBOS_FALLA,
    VOCABULARIO_COMPONENTES,
    PrediccionML,
    ResultadoDiagnostico,
    campos_requeridos_consulta_tecnica,
    es_consulta_ambigua,
    es_continuacion_contextual,
    es_perdida_potencia_bajo_carga,
    es_respuesta_cordial,
    es_saludo_o_contacto_inicial,
    extraer_contexto_combustible,
    formatear_perfil_vehiculo,
    purificar_sintoma_para_vectorizador_ml,
    registrar_en_tracker,
    resultado_solicitud_combustible,
    resultado_solicitud_datos_vehiculo,
    texto_modo_combustible,
)
from src.core.diagnostico.constants import _vocabulario_desde_taxonomia
from src.core.diagnostico.diagnostico_tracker import _tracker_lock
from src.core.interfaces import IModeloML, IMotorRAG
from src.core.session_manager import SessionManager
from src.infrastructure.container import ServiceContainer

__all__ = [
    "GestorDiagnostico",
    "PrediccionML",
    "ResultadoDiagnostico",
    "VOCABULARIO_COMPONENTES",
    "VERBOS_FALLA",
    "PALABRAS_MECANICAS",
    "_tracker_lock",
    "_vocabulario_desde_taxonomia",
]


class GestorDiagnostico:
    """
    Clase orquestadora THREAD-SAFE encargada de coordinar el flujo de diagnóstico tripartito (ML + RAG + LLM).
    No almacena estado mutable de solicitudes previas.
    """

    def __init__(
        self,
        gemini_api_key: str = "",
        modelo_ml: Optional[IModeloML] = None,
        motor_rag: Optional[IMotorRAG] = None,
    ):
        self.api_key = gemini_api_key or settings.gemini_api_key
        # Inyección de dependencias vía ServiceContainer Singleton (evita duplicación de memoria)
        self.modelo_ml: IModeloML = modelo_ml or ServiceContainer.get_modelo_ml()
        self.motor_rag: IMotorRAG = motor_rag or ServiceContainer.get_motor_rag()
        self.procesador_audio = AudioProcessor()
        self.session_manager = SessionManager()

        # Pool de conexiones HTTP persistente con Keep-Alive para reducir latencia TLS/TCP con Google API
        self._http_session = requests.Session()
        retry_strategy = Retry(
            total=2,
            backoff_factor=0.3,
            status_forcelist=[500, 502, 503, 504],
        )
        adapter = HTTPAdapter(pool_connections=25, pool_maxsize=25, max_retries=retry_strategy)
        self._http_session.mount("https://", adapter)
        self._http_session.mount("http://", adapter)

    # Fachadas estáticas para compatibilidad con código existente y tests unitarios
    @staticmethod
    def _es_saludo_o_contacto_inicial(texto: str) -> Tuple[bool, str]:
        return es_saludo_o_contacto_inicial(texto)

    @staticmethod
    def _es_respuesta_cordial(texto: str) -> bool:
        return es_respuesta_cordial(texto)

    @staticmethod
    def _es_continuacion_contextual(texto: str) -> bool:
        return es_continuacion_contextual(texto)

    @staticmethod
    def _es_perdida_potencia_bajo_carga(texto: str) -> bool:
        return es_perdida_potencia_bajo_carga(texto)

    @staticmethod
    def _purificar_sintoma_para_vectorizador_ml(texto: str) -> str:
        return purificar_sintoma_para_vectorizador_ml(texto)

    @staticmethod
    def _extraer_contexto_combustible(
        texto: str, combustible_previo: Optional[str] = None
    ) -> Tuple[Optional[str], Optional[str]]:
        return extraer_contexto_combustible(texto, combustible_previo)

    @staticmethod
    def _texto_modo_combustible(combustible: str, modo: str) -> str:
        return texto_modo_combustible(combustible, modo)

    def _resultado_solicitud_combustible(
        self, sesion, combustible: Optional[str] = None
    ) -> ResultadoDiagnostico:
        return resultado_solicitud_combustible(sesion, combustible)

    @staticmethod
    def _es_consulta_ambigua(texto: str) -> Tuple[bool, str]:
        return es_consulta_ambigua(texto)

    @staticmethod
    def _campos_requeridos_consulta_tecnica(pregunta: str) -> List[str]:
        return campos_requeridos_consulta_tecnica(pregunta)

    @staticmethod
    def _formatear_perfil_vehiculo(perfil: dict) -> str:
        return formatear_perfil_vehiculo(perfil)

    def _resultado_solicitud_datos_vehiculo(self, sesion) -> ResultadoDiagnostico:
        return resultado_solicitud_datos_vehiculo(sesion)

    def _registrar_en_tracker(
        self,
        placa: str,
        marca_modelo: str,
        sintoma: str,
        diagnostico_ml: str,
        campos_completos: int = 1,
    ) -> None:
        registrar_en_tracker(placa, marca_modelo, sintoma, diagnostico_ml, campos_completos)

    def _procesar_consulta_tecnica(
        self,
        pregunta: str,
        *,
        inicio_total: float,
        remitente: Optional[str],
        proveedor: str,
        taller_id: Optional[str],
        usuario_id: Optional[str],
        conversacion_id: Optional[str],
        slot_gemini_preconcedido: Optional[bool],
        diferir_encolado_persistente: bool,
    ) -> ResultadoDiagnostico:
        """Responde información automotriz sin forzar una clase de avería ML."""
        from src.core.diagnostico.text_processor import procesar_consulta_tecnica

        return procesar_consulta_tecnica(
            self,
            pregunta,
            inicio_total=inicio_total,
            remitente=remitente,
            proveedor=proveedor,
            taller_id=taller_id,
            usuario_id=usuario_id,
            conversacion_id=conversacion_id,
            slot_gemini_preconcedido=slot_gemini_preconcedido,
            diferir_encolado_persistente=diferir_encolado_persistente,
        )

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
        diagnostico_forzado: Optional[str] = None,
        orquestado: bool = False,
    ) -> ResultadoDiagnostico:
        """
        Flujo tripartito secuencial THREAD-SAFE para consultas de texto:
        1. ML clasifica el síntoma y calcula confianza.
        2. RAG recupera el procedimiento del manual de taller.
        3. Gemini LLM sintetiza la respuesta técnica estructurada en 3 secciones.
        """
        from src.core.diagnostico.text_processor import procesar_consulta_texto

        return procesar_consulta_texto(
            self,
            texto_usuario,
            placa=placa,
            marca_modelo=marca_modelo,
            session_id=session_id,
            remitente=remitente,
            proveedor=proveedor,
            taller_id=taller_id,
            usuario_id=usuario_id,
            conversacion_id=conversacion_id,
            slot_gemini_preconcedido=slot_gemini_preconcedido,
            diferir_encolado_persistente=diferir_encolado_persistente,
            diagnostico_forzado=diagnostico_forzado,
            orquestado=orquestado,
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
        frecuencias = np.fft.rfftfreq(len(datos_norm), d=1.0 / self.procesador_audio.samplerate)
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
        tipo_consulta: str = "diagnostico",
        predicciones_ml: Optional[list[Any]] = None,
        dtc_info: Optional[str] = None,
        perfil_vehiculo: Optional[str] = None,
        evidencia_confirmada: Optional[list[str]] = None,
        componentes_descartados: Optional[list[str]] = None,
        datos_faltantes: Optional[list[str]] = None,
    ) -> tuple[str, dict]:
        """Sintetiza la respuesta final con Gemini LLM integrando Síntoma + ML + RAG."""
        from src.core.diagnostico.response_generator import generar_respuesta_con_metadatos

        return generar_respuesta_con_metadatos(
            self,
            pregunta=pregunta,
            diagnostico_ml=diagnostico_ml,
            contexto_manual=contexto_manual,
            confianza_ml=confianza_ml,
            titulo_manual=titulo_manual,
            requiere_revision_humana=requiere_revision_humana,
            remitente=remitente,
            proveedor=proveedor,
            taller_id=taller_id,
            usuario_id=usuario_id,
            conversacion_id=conversacion_id,
            slot_gemini_preconcedido=slot_gemini_preconcedido,
            diferir_encolado_persistente=diferir_encolado_persistente,
            tipo_consulta=tipo_consulta,
            predicciones_ml=predicciones_ml,
            dtc_info=dtc_info,
            perfil_vehiculo=perfil_vehiculo,
            evidencia_confirmada=evidencia_confirmada,
            componentes_descartados=componentes_descartados,
            datos_faltantes=datos_faltantes,
        )

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
