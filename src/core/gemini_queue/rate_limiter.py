"""Controlador de tasa y orquestador de la cola para Google Gemini."""

from __future__ import annotations

import asyncio
import threading
import time
from collections import deque
from datetime import date, datetime, timezone
from typing import Any, Callable, Optional, Tuple

from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.core.gemini_queue.db_persistence import (
    marcar_trabajo_fallido_db,
    persistir_solicitud_en_sesion_db,
    posponer_trabajo_por_cuota_db,
    procesar_siguiente_entrega_whatsapp,
)
from src.core.gemini_queue.db_persistence import (
    obtener_estado_gemini_compartido as db_obtener_estado_gemini_compartido,
)
from src.core.gemini_queue.db_persistence import (
    persistir_estado_local_db as db_persistir_estado_local_db,
)
from src.core.gemini_queue.models import SolicitudGeminiEncolada
from src.core.gemini_queue.summary_formatter import crear_resumen_whatsapp
from src.core.logger import logger
from src.core.security import descifrar_texto_reversible
from src.infrastructure.database.connection import database_configurada, obtener_engine
from src.infrastructure.database.repositories.cuota_gemini_repository import CuotaGeminiRepository
from src.infrastructure.database.repositories.trabajo_gemini_repository import TrabajoGeminiRepository


class GeminiRateLimiter:
    """
    Controlador de tasa y cola persistente con FOR UPDATE SKIP LOCKED para Google Gemini.
    Sincronizado entre procesos y compatible con despliegue en producción.
    """

    def __init__(
        self,
        max_por_minuto: Optional[int] = None,
        max_por_dia: Optional[int] = None,
        ventana_segundos: float = 60.0,
    ):
        self.max_por_minuto = max_por_minuto or getattr(settings, "gemini_max_requests_per_minute", 10)
        self.max_por_dia = max_por_dia or getattr(settings, "gemini_max_requests_per_day", 450)
        self.ventana_segundos = ventana_segundos
        self._historial_tiempos: deque[float] = deque()
        self._cola_pendientes: deque[SolicitudGeminiEncolada] = deque()
        self._mapa_solicitudes: dict[str, SolicitudGeminiEncolada] = {}
        self._solicitudes_hoy_fecha: str = date.today().isoformat()
        self._solicitudes_hoy_conteo: int = 0
        self._lock = threading.Lock()
        self._worker_corriendo = False
        self._worker_task: Optional[asyncio.Task] = None
        self._loop: Optional[asyncio.AbstractEventLoop] = None
        self._gemini_ultimo_exito: Optional[str] = None
        self._gemini_ultimo_error: Optional[str] = None
        self._gemini_ultimo_codigo_http: Optional[int] = None
        self._gemini_ultima_verificacion: Optional[str] = None
        self._gemini_cooldown_hasta_epoch: float = 0.0

    def registrar_estado_gemini(
        self,
        exitoso: bool,
        codigo_http: Optional[int] = None,
        error: Optional[str] = None,
        retry_after_segundos: int = 0,
    ) -> None:
        """Registra el resultado realmente observado en la API externa de Gemini."""
        ahora = datetime.now(timezone.utc).isoformat()
        with self._lock:
            self._gemini_ultima_verificacion = ahora
            self._gemini_ultimo_codigo_http = codigo_http
            if exitoso:
                self._gemini_ultimo_exito = ahora
                self._gemini_ultimo_error = None
            else:
                self._gemini_ultimo_error = (error or "Error no especificado")[:300]
                if retry_after_segundos > 0:
                    self._gemini_cooldown_hasta_epoch = max(
                        self._gemini_cooldown_hasta_epoch,
                        time.time() + retry_after_segundos,
                    )

    @staticmethod
    def extraer_retry_after_segundos(response: Any, default: int = 60) -> int:
        """Interpreta Retry-After o google.rpc.RetryInfo y devuelve una espera segura."""
        valor_header = None
        headers = getattr(response, "headers", None)
        if headers:
            valor_header = headers.get("Retry-After") or headers.get("retry-after")
        if valor_header:
            try:
                return max(1, min(300, int(float(valor_header))))
            except (TypeError, ValueError):
                pass

        try:
            detalles = response.json().get("error", {}).get("details", [])
            for detalle in detalles:
                valor = detalle.get("retryDelay")
                if isinstance(valor, str) and valor.endswith("s"):
                    return max(1, min(300, int(float(valor[:-1])) + 1))
        except (AttributeError, TypeError, ValueError):
            pass
        return max(1, min(300, default))

    def segundos_cooldown_restantes(self) -> int:
        with self._lock:
            return max(0, int(self._gemini_cooldown_hasta_epoch - time.time()) + 1)

    def obtener_estado_gemini(self, api_key_valida: bool) -> dict[str, Any]:
        """Devuelve un estado auditable sin confundir configuración con disponibilidad real."""
        with self._lock:
            self._verificar_y_resetear_conteo_diario()
            codigo_http = self._gemini_ultimo_codigo_http
            ultimo_error = self._gemini_ultimo_error
            ultima_verificacion = self._gemini_ultima_verificacion
            ultimo_exito = self._gemini_ultimo_exito
            cuota_local_agotada = self._solicitudes_hoy_conteo >= self.max_por_dia
            cooldown_segundos = max(
                0,
                int(self._gemini_cooldown_hasta_epoch - time.time()) + 1,
            )

        if not api_key_valida:
            estado = "sin_api_key"
        elif cuota_local_agotada or codigo_http == 429 or cooldown_segundos > 0:
            estado = "degradado_sin_cuota"
        elif ultima_verificacion is None:
            estado = "no_verificado"
        elif ultimo_error:
            estado = "degradado"
        else:
            estado = "disponible"

        return {
            "estado": estado,
            "disponible": estado == "disponible",
            "ultima_verificacion": ultima_verificacion,
            "ultimo_exito": ultimo_exito,
            "ultimo_codigo_http": codigo_http,
            "ultimo_error": ultimo_error,
            "cooldown_segundos": cooldown_segundos,
        }

    async def persistir_estado_local_db(self) -> None:
        """Replica el estado local en PostgreSQL para coordinar todos los workers."""
        estado = self.obtener_estado_gemini(api_key_valida=True)
        await db_persistir_estado_local_db(estado)

    async def obtener_estado_gemini_compartido(self, api_key_valida: bool) -> dict[str, Any]:
        """Prioriza el último estado persistido para que todos los workers informen lo mismo."""
        local = self.obtener_estado_gemini(api_key_valida)
        return await db_obtener_estado_gemini_compartido(local, api_key_valida)

    def _verificar_y_resetear_conteo_diario(self):
        """Reinicia el contador diario local si cambió la fecha."""
        hoy = date.today().isoformat()
        if self._solicitudes_hoy_fecha != hoy:
            self._solicitudes_hoy_fecha = hoy
            self._solicitudes_hoy_conteo = 0

    def intentar_adquirir_slot(self) -> bool:
        """
        Intenta adquirir un slot inmediato en la ventana deslizante y dentro del límite diario.
        Si la cola tiene elementos pendientes o se superó la cuota diaria, retorna False.
        """
        with self._lock:
            self._verificar_y_resetear_conteo_diario()

            if self._gemini_cooldown_hasta_epoch > time.time():
                return False

            if self._solicitudes_hoy_conteo >= self.max_por_dia:
                logger.warning(
                    f"[Gemini Quota] Límite diario ({self.max_por_dia} req/día) alcanzado."
                )
                return False

            ahora = time.time()
            limite_inferior = ahora - self.ventana_segundos

            while self._historial_tiempos and self._historial_tiempos[0] < limite_inferior:
                self._historial_tiempos.popleft()

            if len(self._historial_tiempos) < self.max_por_minuto and len(self._cola_pendientes) == 0:
                self._historial_tiempos.append(ahora)
                self._solicitudes_hoy_conteo += 1
                logger.debug(
                    f"[Gemini Rate Limiter] Slot concedido ({len(self._historial_tiempos)}/{self.max_por_minuto} min | {self._solicitudes_hoy_conteo}/{self.max_por_dia} día)."
                )
                return True

            return False

    async def intentar_adquirir_slot_db(self) -> Tuple[bool, str]:
        """
        Adquiere de forma atómica y compartida un slot en PostgreSQL.
        Garantiza sincronización exacta entre múltiples workers o procesos Uvicorn.
        """
        cooldown = self.segundos_cooldown_restantes()
        if cooldown > 0:
            return False, f"cooldown_activo ({cooldown}s)"

        if not database_configurada():
            concedido = self.intentar_adquirir_slot()
            return concedido, "concedido_local" if concedido else "limite_local"

        try:
            db_engine = obtener_engine()
            async with AsyncSession(db_engine, expire_on_commit=False) as session:
                async with session.begin():
                    cuota_repo = CuotaGeminiRepository(session)
                    concedido, motivo, hoy, min_cnt = await cuota_repo.adquirir_slot_compartido(
                        max_rpm=self.max_por_minuto, max_rpd=self.max_por_dia
                    )
                    if concedido:
                        self.registrar_slot_consumido()
                    return concedido, motivo
        except Exception as e:
            logger.error(f"[Gemini Rate Limiter DB] No se pudo consultar la cuota global: {e}")
            return False, "db_no_disponible"

    def registrar_slot_consumido(self):
        """Registra explícitamente el consumo de un slot cuando se despacha un elemento de la cola."""
        with self._lock:
            self._verificar_y_resetear_conteo_diario()
            self._historial_tiempos.append(time.time())
            self._solicitudes_hoy_conteo += 1

    def encolar_solicitud(
        self,
        sintoma: str,
        diagnostico_ml: str,
        confianza_ml: float,
        contexto_manual: str,
        titulo_manual: str,
        requiere_revision_humana: bool = False,
        callback_completado: Optional[Callable] = None,
        diagnostico_id: Optional[str] = None,
        remitente: Optional[str] = None,
        taller_id: Optional[str] = None,
        usuario_id: Optional[str] = None,
        conversacion_id: Optional[str] = None,
        placa: Optional[str] = None,
        marca_modelo: Optional[str] = None,
        proveedor: str = "meta",
        mensaje_inicial_id: Optional[str] = None,
        mensaje_salida_preliminar_id: Optional[str] = None,
        tipo_consulta: str = "diagnostico",
        predicciones_ml: Optional[list[dict]] = None,
        solicitud_id: Optional[str] = None,
    ) -> Tuple[SolicitudGeminiEncolada, int, float]:
        """Encola una solicitud para procesamiento asíncrono respetando la cuota."""
        kwargs_solicitud = {}
        if solicitud_id:
            kwargs_solicitud["id"] = solicitud_id

        solicitud = SolicitudGeminiEncolada(
            sintoma=sintoma,
            diagnostico_ml=diagnostico_ml,
            confianza_ml=confianza_ml,
            contexto_manual=contexto_manual,
            titulo_manual=titulo_manual,
            tipo_consulta=tipo_consulta,
            requiere_revision_humana=requiere_revision_humana,
            callback_completado=callback_completado,
            diagnostico_id=diagnostico_id,
            remitente=remitente,
            taller_id=taller_id,
            usuario_id=usuario_id,
            conversacion_id=conversacion_id,
            placa=placa,
            marca_modelo=marca_modelo,
            proveedor=proveedor,
            mensaje_inicial_id=mensaje_inicial_id,
            mensaje_salida_preliminar_id=mensaje_salida_preliminar_id,
            predicciones_ml=predicciones_ml or [],
            **kwargs_solicitud,
        )

        with self._lock:
            self._cola_pendientes.append(solicitud)
            self._mapa_solicitudes[solicitud.id] = solicitud
            posicion = len(self._cola_pendientes)
            espera_estimada = self._calcular_tiempo_espera_con_lock(posicion)

        self.asegurar_worker_activo()
        return solicitud, posicion, espera_estimada

    def actualizar_contexto_encolado(
        self,
        solicitud_id: str,
        *,
        diagnostico_id: Optional[str] = None,
        conversacion_id: Optional[str] = None,
        taller_id: Optional[str] = None,
        usuario_id: Optional[str] = None,
        remitente: Optional[str] = None,
        proveedor: Optional[str] = None,
    ) -> bool:
        """Actualiza metadatos de persistencia en una solicitud que ya estaba en cola."""
        with self._lock:
            solicitud = self._mapa_solicitudes.get(solicitud_id)
            if not solicitud:
                return False
            if diagnostico_id is not None:
                solicitud.diagnostico_id = diagnostico_id
            if conversacion_id is not None:
                solicitud.conversacion_id = conversacion_id
            if taller_id is not None:
                solicitud.taller_id = taller_id
            if usuario_id is not None:
                solicitud.usuario_id = usuario_id
            if remitente is not None:
                solicitud.remitente = remitente
            if proveedor is not None:
                solicitud.proveedor = proveedor
            return True

    async def persistir_solicitud_en_sesion(
        self,
        session: AsyncSession,
        *,
        solicitud_id: str,
        sintoma: str,
        diagnostico_ml: str,
        confianza_ml: float,
        contexto_manual: str,
        titulo_manual: str,
        requiere_revision_humana: bool,
        remitente: Optional[str] = None,
        proveedor: str = "meta",
        taller_id: Optional[str] = None,
        usuario_id: Optional[str] = None,
        conversacion_id: Optional[str] = None,
        diagnostico_id: Optional[str] = None,
        tipo_consulta: str = "diagnostico",
    ) -> None:
        """Persiste el trabajo de Gemini en la misma transacción del webhook."""
        await persistir_solicitud_en_sesion_db(
            session,
            solicitud_id=solicitud_id,
            sintoma=sintoma,
            diagnostico_ml=diagnostico_ml,
            confianza_ml=confianza_ml,
            contexto_manual=contexto_manual,
            titulo_manual=titulo_manual,
            requiere_revision_humana=requiere_revision_humana,
            remitente=remitente,
            proveedor=proveedor,
            taller_id=taller_id,
            usuario_id=usuario_id,
            conversacion_id=conversacion_id,
            diagnostico_id=diagnostico_id,
            tipo_consulta=tipo_consulta,
        )

    def descolar_siguiente(self) -> Optional[SolicitudGeminiEncolada]:
        """Extrae la siguiente solicitud de la cola en memoria."""
        with self._lock:
            if not self._cola_pendientes:
                return None
            solicitud = self._cola_pendientes.popleft()
            self._mapa_solicitudes.pop(solicitud.id, None)
            return solicitud

    def tamaño_cola(self) -> int:
        with self._lock:
            return len(self._cola_pendientes)

    def slots_utilizados(self) -> int:
        with self._lock:
            ahora = time.time()
            limite = ahora - self.ventana_segundos
            while self._historial_tiempos and self._historial_tiempos[0] < limite:
                self._historial_tiempos.popleft()
            return len(self._historial_tiempos)

    def tiempo_espera_estimado(self) -> float:
        with self._lock:
            pos = len(self._cola_pendientes) + 1
            return self._calcular_tiempo_espera_con_lock(pos)

    def _calcular_tiempo_espera_con_lock(self, posicion: int = 1) -> float:
        if posicion <= 0:
            return 0.0
        intervalo = self.ventana_segundos / self.max_por_minuto
        return round(posicion * intervalo, 1)

    def asegurar_worker_activo(self):
        """Inicia automáticamente el worker si no está corriendo y hay event loop."""
        if self._worker_corriendo:
            return
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return
        with self._lock:
            if self._worker_corriendo:
                return
            self._loop = loop
            self._worker_corriendo = True
            try:
                self._worker_task = loop.create_task(self._worker_loop())
                logger.info("[Gemini Queue] Worker background de la cola iniciado automáticamente.")
            except RuntimeError:
                pass

    def iniciar_worker(self, loop: Optional[asyncio.AbstractEventLoop] = None):
        """Inicia explícitamente el worker background para procesar la cola."""
        with self._lock:
            if self._worker_corriendo and self._worker_task and not self._worker_task.done():
                return
            target_loop = loop or self._loop
            if target_loop is None:
                try:
                    target_loop = asyncio.get_running_loop()
                except RuntimeError:
                    return
            self._loop = target_loop
            self._worker_corriendo = True
            self._worker_task = target_loop.create_task(self._worker_loop())
            logger.info("[Gemini Queue] Worker background de cola Gemini iniciado explícitamente.")

    async def detener_worker(self):
        """Detiene de forma limpia y asíncrona el worker background de la cola."""
        self._worker_corriendo = False
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except (asyncio.CancelledError, Exception):
                pass
            self._worker_task = None
        logger.info("[Gemini Queue] Worker background detenido de forma limpia.")

    async def _worker_loop(self):
        """Ciclo continuo que descola solicitudes de memoria y de PostgreSQL respetando RPM y RPD."""
        preferir_entrega = True
        while self._worker_corriendo:
            try:
                if (
                    preferir_entrega
                    and database_configurada()
                    and await procesar_siguiente_entrega_whatsapp()
                ):
                    preferir_entrega = False
                    continue
                preferir_entrega = True

                cooldown = self.segundos_cooldown_restantes()
                if cooldown > 0:
                    await asyncio.sleep(min(cooldown, 1.0))
                    continue

                tiene_trabajo = self.tamaño_cola() > 0
                trabajo_db = None

                if not tiene_trabajo and database_configurada():
                    try:
                        db_engine = obtener_engine()
                        async with AsyncSession(db_engine, expire_on_commit=False) as session:
                            async with session.begin():
                                repo = TrabajoGeminiRepository(session)
                                trabajo_db = await repo.obtener_siguiente_pendiente_bloqueado(bloqueo_segundos=60)
                                if trabajo_db:
                                    tiene_trabajo = True
                    except Exception as e:
                        logger.debug(f"[Gemini Worker DB Poll] {e}")

                if tiene_trabajo:
                    concedido, motivo = await self.intentar_adquirir_slot_db()
                    forzar_degradado = not concedido
                    if not concedido:
                        if "rpd_excedido" in motivo or "cooldown" in motivo or (trabajo_db and trabajo_db.intentos >= 1):
                            logger.warning(f"[Gemini Worker] {motivo}. Procesando en modo degradado ML+RAG...")
                            forzar_degradado = True
                        else:
                            if trabajo_db:
                                await posponer_trabajo_por_cuota_db(str(trabajo_db.id), motivo)
                            await asyncio.sleep(1.0)
                            continue

                    if trabajo_db:
                        if trabajo_db.intentos > 3:
                            logger.warning(
                                f"[Gemini Worker] Solicitud {trabajo_db.id} alcanzó {trabajo_db.intentos} intentos. "
                                "Forzando modo degradado ML+RAG para asegurar entrega al usuario."
                            )
                            forzar_degradado = True
                        try:
                            remitente_descifrado = (
                                descifrar_texto_reversible(trabajo_db.remitente_cifrado)
                                if trabajo_db.remitente_cifrado else None
                            )
                        except ValueError as exc:
                            await marcar_trabajo_fallido_db(str(trabajo_db.id), str(exc))
                            continue

                        solicitud = SolicitudGeminiEncolada(
                            id=str(trabajo_db.id),
                            diagnostico_id=str(trabajo_db.diagnostico_id) if trabajo_db.diagnostico_id else None,
                            taller_id=str(trabajo_db.taller_id) if trabajo_db.taller_id else None,
                            usuario_id=str(trabajo_db.usuario_id) if trabajo_db.usuario_id else None,
                            conversacion_id=str(trabajo_db.conversacion_id) if trabajo_db.conversacion_id else None,
                            remitente=remitente_descifrado,
                            proveedor=trabajo_db.proveedor or "meta",
                            sintoma=trabajo_db.sintoma,
                            diagnostico_ml=trabajo_db.diagnostico_ml,
                            confianza_ml=float(trabajo_db.confianza_ml or 0.0),
                            contexto_manual=trabajo_db.contexto_manual or "",
                            titulo_manual=trabajo_db.titulo_manual or "",
                            tipo_consulta=trabajo_db.tipo_consulta or "diagnostico",
                            requiere_revision_humana=trabajo_db.requiere_revision_humana,
                        )
                    else:
                        solicitud = self.descolar_siguiente()

                    if solicitud:
                        await self._procesar_solicitud_encolada(solicitud, forzar_degradado=forzar_degradado)
                else:
                    await asyncio.sleep(0.15)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[Gemini Queue Worker Loop Error] {e}")
                await asyncio.sleep(1.0)
        self._worker_corriendo = False

    async def procesar_siguiente_en_cola(self) -> Optional[Tuple[str, dict]]:
        """Procesa manualmente el siguiente elemento de la cola (para pruebas unitarias)."""
        solicitud = self.descolar_siguiente()
        if not solicitud:
            return None
        self.registrar_slot_consumido()
        return await self._procesar_solicitud_encolada(solicitud)

    async def _procesar_solicitud_encolada(
        self, solicitud: SolicitudGeminiEncolada, forzar_degradado: bool = False
    ) -> Tuple[str, dict]:
        """Procesa una solicitud descolada realizando la síntesis con Gemini o fallback local."""
        from src.core.gemini_queue.worker_processor import procesar_solicitud_encolada

        return await procesar_solicitud_encolada(solicitud, self, forzar_degradado=forzar_degradado)

    @staticmethod
    def _crear_resumen_whatsapp(
        solicitud: SolicitudGeminiEncolada, texto_respuesta: str
    ) -> str:
        return crear_resumen_whatsapp(solicitud, texto_respuesta)

    def reiniciar(self):
        """Reinicia el historial de marcas y vacía la cola (útil para pruebas unitarias)."""
        with self._lock:
            self._historial_tiempos.clear()
            self._cola_pendientes.clear()
            self._mapa_solicitudes.clear()
            self._solicitudes_hoy_conteo = 0
            self._gemini_ultimo_exito = None
            self._gemini_ultimo_error = None
            self._gemini_ultimo_codigo_http = None
            self._gemini_ultima_verificacion = None
            self._gemini_cooldown_hasta_epoch = 0.0
