import threading
import time
from typing import Any, Dict, List, Optional

from src.core.logger import logger


class DiagnosticSession:
    """Representa el estado de una sesión de diálogo conversacional multiturno."""
    
    def __init__(self, session_id: str):
        self.session_id: str = session_id
        self.placa: Optional[str] = None
        self.marca_modelo: Optional[str] = None
        self.sintomas: List[str] = []
        self.perfil_vehiculo: Dict[str, Any] = {}
        self.consulta_tecnica_pendiente: Optional[str] = None
        self.campos_requeridos: List[str] = []
        self.kilometraje_por_aclarar: bool = False
        self.estado: str = "inicio"  # inicio, esperando_clarificacion, completo
        self.created_at: float = time.time()
        self.updated_at: float = time.time()
        self._lock = threading.RLock()

    def agregar_sintoma(self, texto: str):
        with self._lock:
            texto_limpio = texto.strip()
            if texto_limpio:
                if texto_limpio not in self.sintomas:
                    self.sintomas.append(texto_limpio)
                self.updated_at = time.time()

    def obtener_sintoma_completo(self) -> str:
        with self._lock:
            return " ".join(self.sintomas).strip()

    def reiniciar(self):
        with self._lock:
            self.sintomas = []
            self.consulta_tecnica_pendiente = None
            self.campos_requeridos = []
            self.kilometraje_por_aclarar = False
            self.estado = "inicio"
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
                "perfil_vehiculo": dict(self.perfil_vehiculo),
                "consulta_tecnica_pendiente": self.consulta_tecnica_pendiente,
                "campos_requeridos": list(self.campos_requeridos),
                "kilometraje_por_aclarar": self.kilometraje_por_aclarar,
                "estado": self.estado,
            }

    def cargar_contexto(self, contexto: Dict[str, Any]) -> None:
        with self._lock:
            self.perfil_vehiculo = dict(contexto.get("perfil_vehiculo") or {})
            marca = self.perfil_vehiculo.get("marca")
            modelo = self.perfil_vehiculo.get("modelo")
            self.marca_modelo = f"{marca} {modelo}" if marca and modelo else None
            self.consulta_tecnica_pendiente = contexto.get("consulta_tecnica_pendiente")
            self.campos_requeridos = list(contexto.get("campos_requeridos") or [])
            self.kilometraje_por_aclarar = bool(contexto.get("kilometraje_por_aclarar", False))
            self.estado = str(contexto.get("estado") or "inicio")
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
