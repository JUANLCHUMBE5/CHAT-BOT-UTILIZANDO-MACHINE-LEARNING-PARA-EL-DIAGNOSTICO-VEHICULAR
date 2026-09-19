import threading
import time
from typing import Any, Dict, List, Optional

from src.core.conversacion.extractor_hechos import ExtractorHechos
from src.core.conversacion.models import ConversationState
from src.core.conversacion.sintetizador_consulta import SintetizadorConsulta
from src.core.logger import logger


class DiagnosticSession:
    """Representa el estado de una sesión de diálogo conversacional multiturno."""
    
    def __init__(self, session_id: str):
        self.session_id: str = session_id
        self.case_id: Optional[str] = None
        self.placa: Optional[str] = None
        self.marca_modelo: Optional[str] = None
        self.sintomas: List[str] = []
        self.conversation_state: ConversationState = ConversationState(session_id=session_id)
        self.perfil_vehiculo: Dict[str, Any] = {}
        self.consulta_tecnica_pendiente: Optional[str] = None
        self.consulta_combustible_pendiente: Optional[str] = None
        self.modo_falla_combustible: Optional[str] = None
        self.autopregunta_sintoma_base: Optional[str] = None
        self.autopregunta_opciones: List[str] = []
        self.autopregunta_hipotesis: List[str] = []
        self.ultimas_hipotesis_diferenciales: List[str] = []
        self.campos_requeridos: List[str] = []
        self.kilometraje_por_aclarar: bool = False
        self.contexto: Dict[str, Any] = {}
        self.estado: str = "inicio"  # inicio, esperando_clarificacion, esperando_autopregunta, completo
        self.created_at: float = time.time()
        self.updated_at: float = time.time()
        self._lock = threading.RLock()

    def agregar_sintoma(self, texto: str):
        with self._lock:
            texto_limpio = texto.strip()
            if texto_limpio:
                if texto_limpio not in self.sintomas:
                    self.sintomas.append(texto_limpio)
                ExtractorHechos.extraer_y_actualizar(self.conversation_state, texto_limpio)
                self.updated_at = time.time()

    def obtener_sintoma_completo(self) -> str:
        with self._lock:
            texto_sintomas = " ".join(self.sintomas).strip()
            if texto_sintomas:
                return texto_sintomas
            tiene_sintomas = any(
                h.categoria == "sintoma" and h.estado.value == "CONFIRMADO"
                for h in self.conversation_state.hechos.values()
            )
            sintetizado = SintetizadorConsulta.sintetizar(self.conversation_state)
            if tiene_sintomas and sintetizado and sintetizado != "Consulta vehicular técnica general":
                return sintetizado
            return ""

    def reiniciar(self):
        with self._lock:
            self.case_id = None
            self.sintomas = []
            self.conversation_state.reiniciar()
            self.consulta_tecnica_pendiente = None
            self.consulta_combustible_pendiente = None
            self.modo_falla_combustible = None
            self.autopregunta_sintoma_base = None
            self.autopregunta_opciones = []
            self.autopregunta_hipotesis = []
            self.ultimas_hipotesis_diferenciales = []
            self.campos_requeridos = []
            self.kilometraje_por_aclarar = False
            self.estado = "inicio"
            self.updated_at = time.time()

    def finalizar_caso(self, nuevo_case_id: Optional[str] = None) -> str:
        """Cierra el caso diagnóstico activo y prepara un estado limpio conservando trazabilidad."""
        with self._lock:
            self.sintomas = []
            self.conversation_state.iniciar_nuevo_caso(nuevo_case_id)
            self.case_id = self.conversation_state.case_id
            self.consulta_tecnica_pendiente = None
            self.consulta_combustible_pendiente = None
            self.modo_falla_combustible = None
            self.autopregunta_sintoma_base = None
            self.autopregunta_opciones = []
            self.autopregunta_hipotesis = []
            self.ultimas_hipotesis_diferenciales = []
            self.campos_requeridos = []
            self.kilometraje_por_aclarar = False
            self.estado = "inicio"
            self.updated_at = time.time()
            return str(self.case_id)

    def establecer_autopregunta(
        self,
        sintoma_base: str,
        opciones: List[str],
        hipotesis: List[str],
    ) -> None:
        with self._lock:
            self.autopregunta_sintoma_base = sintoma_base
            self.autopregunta_opciones = list(opciones)
            self.autopregunta_hipotesis = list(hipotesis)
            self.estado = "esperando_autopregunta"
            self.updated_at = time.time()

    def establecer_consulta_combustible(self, sintoma: str) -> None:
        with self._lock:
            self.consulta_combustible_pendiente = sintoma
            self.modo_falla_combustible = None
            self.estado = "esperando_combustible"
            self.updated_at = time.time()

    def establecer_modo_falla_combustible(self, modo: Optional[str]) -> None:
        with self._lock:
            if modo:
                self.modo_falla_combustible = modo
            self.updated_at = time.time()

    def establecer_consulta_tecnica(
        self, pregunta: str, campos_requeridos: List[str], kilometraje_por_aclarar: bool
    ) -> None:
        with self._lock:
            self.consulta_tecnica_pendiente = pregunta
            self.campos_requeridos = list(dict.fromkeys(campos_requeridos))
            self.kilometraje_por_aclarar = kilometraje_por_aclarar
            self.estado = "esperando_datos_vehiculo"
            self.updated_at = time.time()

    def actualizar_perfil(self, datos: Dict[str, Any]) -> None:
        with self._lock:
            self.perfil_vehiculo.update({k: v for k, v in datos.items() if v not in (None, "")})
            marca = self.perfil_vehiculo.get("marca")
            modelo = self.perfil_vehiculo.get("modelo")
            if marca and modelo:
                self.marca_modelo = f"{marca} {modelo}"
            if "kilometraje" in datos:
                self.kilometraje_por_aclarar = False
            self.updated_at = time.time()

    def campos_faltantes(self) -> List[str]:
        with self._lock:
            return [campo for campo in self.campos_requeridos if not self.perfil_vehiculo.get(campo)]

    def exportar_contexto(self) -> Dict[str, Any]:
        with self._lock:
            return {
                "case_id": self.case_id,
                "perfil_vehiculo": dict(self.perfil_vehiculo),
                "consulta_tecnica_pendiente": self.consulta_tecnica_pendiente,
                "consulta_combustible_pendiente": self.consulta_combustible_pendiente,
                "modo_falla_combustible": self.modo_falla_combustible,
                "autopregunta_sintoma_base": self.autopregunta_sintoma_base,
                "autopregunta_opciones": list(self.autopregunta_opciones),
                "autopregunta_hipotesis": list(self.autopregunta_hipotesis),
                "ultimas_hipotesis_diferenciales": list(self.ultimas_hipotesis_diferenciales),
                "campos_requeridos": list(self.campos_requeridos),
                "kilometraje_por_aclarar": self.kilometraje_por_aclarar,
                "estado": self.estado,
                "conversation_state": self.conversation_state.exportar_dict(),
            }

    def cargar_contexto(self, contexto: Dict[str, Any]) -> None:
        with self._lock:
            self.case_id = contexto.get("case_id")
            self.perfil_vehiculo = dict(contexto.get("perfil_vehiculo") or {})
            marca = self.perfil_vehiculo.get("marca")
            modelo = self.perfil_vehiculo.get("modelo")
            self.marca_modelo = f"{marca} {modelo}" if marca and modelo else None
            self.consulta_tecnica_pendiente = contexto.get("consulta_tecnica_pendiente")
            self.consulta_combustible_pendiente = contexto.get("consulta_combustible_pendiente")
            self.modo_falla_combustible = contexto.get("modo_falla_combustible")
            self.autopregunta_sintoma_base = contexto.get("autopregunta_sintoma_base")
            self.autopregunta_opciones = list(contexto.get("autopregunta_opciones") or [])
            self.autopregunta_hipotesis = list(contexto.get("autopregunta_hipotesis") or [])
            self.ultimas_hipotesis_diferenciales = list(contexto.get("ultimas_hipotesis_diferenciales") or [])
            self.campos_requeridos = list(contexto.get("campos_requeridos") or [])
            self.kilometraje_por_aclarar = bool(contexto.get("kilometraje_por_aclarar", False))
            self.estado = str(contexto.get("estado") or "inicio")
            if "conversation_state" in contexto and isinstance(contexto["conversation_state"], dict):
                self.conversation_state = ConversationState.from_dict(contexto["conversation_state"])
                if self.case_id and not self.conversation_state.case_id:
                    self.conversation_state.case_id = self.case_id
                elif self.conversation_state.case_id and not self.case_id:
                    self.case_id = self.conversation_state.case_id
            self.updated_at = time.time()

    def ha_expirado(self, ttl_segundos: int = 1800) -> bool:
        with self._lock:
            return (time.time() - self.updated_at) > ttl_segundos

class SessionManager:
    """Gestor en memoria THREAD-SAFE de sesiones de diálogo conversacional y slot-filling."""
    
    def __init__(self, ttl_seconds: int = 1800):
        self._sesiones: Dict[str, DiagnosticSession] = {}
        self.ttl_seconds: int = ttl_seconds
        self._ultimo_limpieza: float = 0.0
        self._lock = threading.RLock()

    def obtener_sesion(self, session_id: str, ttl_segundos: Optional[int] = None) -> Optional[DiagnosticSession]:
        with self._lock:
            ttl = ttl_segundos if ttl_segundos is not None else self.ttl_seconds
            self._limpiar_sesiones_expiradas(ttl_segundos=ttl)
            sesion = self._sesiones.get(session_id)
            if sesion and sesion.ha_expirado(ttl):
                logger.debug(f"[SessionManager] Expulsando sesión expirada instantáneamente session_id='{session_id}'")
                self._sesiones.pop(session_id, None)
                return None
            return sesion

    def obtener_o_crear_sesion(self, session_id: str, ttl_segundos: Optional[int] = None) -> DiagnosticSession:
        with self._lock:
            ttl = ttl_segundos if ttl_segundos is not None else self.ttl_seconds
            self._limpiar_sesiones_expiradas(ttl_segundos=ttl)
            sesion = self._sesiones.get(session_id)
            if sesion and sesion.ha_expirado(ttl):
                logger.debug(f"[SessionManager] Expulsando sesión expirada instantáneamente session_id='{session_id}'")
                self._sesiones.pop(session_id, None)
                sesion = None

            if sesion is None:
                logger.debug(f"[SessionManager] Creando nueva sesión de diálogo para session_id='{session_id}'")
                sesion = DiagnosticSession(session_id)
                self._sesiones[session_id] = sesion
            return sesion

    def actualizar_datos_vehiculo(
        self, 
        session_id: str, 
        placa: Optional[str] = None, 
        marca_modelo: Optional[str] = None,
        sesion: Optional[DiagnosticSession] = None
    ):
        with self._lock:
            if sesion is None:
                sesion = self.obtener_o_crear_sesion(session_id)
            if placa and placa not in ("REST-API", "WAPP-01", "DESCONOCIDO"):
                sesion.placa = placa
            if marca_modelo and marca_modelo not in ("Vehiculo Generico", "Generico Generico", "Generico", ""):
                sesion.marca_modelo = marca_modelo

    def acumular_input_usuario(
        self, 
        session_id: str, 
        texto_usuario: str, 
        placa: Optional[str] = None, 
        marca_modelo: Optional[str] = None
    ) -> DiagnosticSession:
        with self._lock:
            sesion = self.obtener_o_crear_sesion(session_id)
            self.actualizar_datos_vehiculo(session_id, placa, marca_modelo, sesion=sesion)
            sesion.agregar_sintoma(texto_usuario)
            return sesion

    def cerrar_sesion(self, session_id: str):
        with self._lock:
            if session_id in self._sesiones:
                logger.debug(f"[SessionManager] Cerrando sesión para session_id='{session_id}'")
                del self._sesiones[session_id]

    def reiniciar_sesion(self, session_id: str):
        with self._lock:
            if session_id in self._sesiones:
                logger.debug(f"[SessionManager] Reiniciando sesión para session_id='{session_id}'")
                self._sesiones[session_id].reiniciar()

    def finalizar_caso(self, session_id: str, nuevo_case_id: Optional[str] = None) -> Optional[str]:
        """Finaliza el caso activo en memoria y prepara un nuevo case_id sin residuos sintomáticos."""
        with self._lock:
            if session_id in self._sesiones:
                logger.debug(f"[SessionManager] Finalizando caso activo para session_id='{session_id}'")
                return self._sesiones[session_id].finalizar_caso(nuevo_case_id)
            return None

    def exportar_contexto(self, session_id: str) -> Dict[str, Any]:
        sesion = self.obtener_sesion(session_id)
        return sesion.exportar_contexto() if sesion else {}

    def cargar_contexto(self, session_id: str, contexto: Optional[Dict[str, Any]]) -> None:
        if not contexto:
            return
        self.obtener_o_crear_sesion(session_id).cargar_contexto(contexto)

    def _limpiar_sesiones_expiradas(self, ttl_segundos: int = 1800, force: bool = False):
        with self._lock:
            ahora = time.time()
            ttl = ttl_segundos if ttl_segundos != 1800 else self.ttl_seconds
            if not force and len(self._sesiones) >= 100 and (ahora - self._ultimo_limpieza < 30):
                return

            self._ultimo_limpieza = ahora
            expiradas = [
                sid for sid, s in list(self._sesiones.items())
                if s.ha_expirado(ttl)
            ]
            for sid in expiradas:
                self._sesiones.pop(sid, None)
