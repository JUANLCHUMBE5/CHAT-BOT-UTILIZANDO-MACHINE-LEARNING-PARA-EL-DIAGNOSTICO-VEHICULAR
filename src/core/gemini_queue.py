"""
Gestor de tasa (Rate Limiter) y cola real persistente de solicitudes para la API de Google Gemini (12 req/min / 18 req/día).

Implementa:
- Ventana de 12 solicitudes por minuto y límite diario configurable (18 req/día) sincronizado en PostgreSQL.
- Cola real persistente en PostgreSQL (tabla trabajos_gemini) con bloqueo atómico FOR UPDATE SKIP LOCKED.
- Cifrado simétrico reversible del remitente para estricta privacidad de datos en base de datos.
- Despacho continuo en worker background con soporte multi-proveedor (Meta Graph API / Twilio WhatsApp).
- Transiciones de estado auditadas: pendiente -> procesando -> completado / fallido / pendiente_reintento.
- Registro de filas en uso_api con costo $0.00 en nivel gratuito (Free Tier) y cálculo exacto en plan pagado.
- Persistencia del segundo mensaje saliente de diagnóstico en la tabla mensajes.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from collections import deque
from datetime import date, datetime, timezone
from decimal import Decimal
import inspect
import requests
import threading
import time
from typing import Any, Callable, Optional, Tuple
import uuid

from sqlalchemy.ext.asyncio import AsyncSession

from src.config import settings
from src.core.logger import logger
from src.core.security import cifrar_texto_reversible, descifrar_texto_reversible
from src.core.services.whatsapp_provider import whatsapp_provider_service
from src.infrastructure.database.connection import database_configurada, obtener_engine
from src.infrastructure.database.repositories.cuota_gemini_repository import CuotaGeminiRepository
from src.infrastructure.database.repositories.diagnostico_repository import DiagnosticoRepository
from src.infrastructure.database.repositories.mensaje_repository import MensajeRepository
from src.infrastructure.database.repositories.operaciones_repository import OperacionesRepository
from src.infrastructure.database.repositories.trabajo_gemini_repository import TrabajoGeminiRepository


# Costo de WhatsApp Meta en ventana de servicio (24h) = $0.00
COSTO_META_MENSAJE_SERVICIO_USD = Decimal(str(settings.meta_message_price_usd))


@dataclass
class SolicitudGeminiEncolada:
    """Representa una solicitud de diagnóstico vehicular encolada para procesamiento."""

    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    timestamp_ingreso: float = field(default_factory=time.time)
    sintoma: str = ""
    diagnostico_ml: str = ""
    confianza_ml: float = 0.0
    contexto_manual: str = ""
    titulo_manual: str = ""
    requiere_revision_humana: bool = False
    callback_completado: Optional[Callable] = None
    futuro_resultado: Optional[Any] = None

    # Contexto para persistencia en DB y notificación WhatsApp
    diagnostico_id: Optional[str] = None
    remitente: Optional[str] = None
    taller_id: Optional[str] = None
    usuario_id: Optional[str] = None
    conversacion_id: Optional[str] = None
    placa: Optional[str] = None
    marca_modelo: Optional[str] = None

    # Proveedor de entrega y referencias de mensaje
    proveedor: str = "meta"  # "meta" | "twilio" | "api"
    mensaje_inicial_id: Optional[str] = None
    mensaje_salida_preliminar_id: Optional[str] = None


class GeminiRateLimiter:
    """
    Controlador de tasa y cola persistente con FOR UPDATE SKIP LOCKED para Google Gemini.
    Sincronizado entre procesos y compatible con despliegue en AWS / producción.
    """

    def __init__(
        self,
        max_por_minuto: Optional[int] = None,
        max_por_dia: Optional[int] = None,
        ventana_segundos: float = 60.0,
    ):
        self.max_por_minuto = max_por_minuto or getattr(settings, "gemini_max_requests_per_minute", 12)
        self.max_por_dia = max_por_dia or getattr(settings, "gemini_max_requests_per_day", 18)
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

            # Verificar límite diario local
            if self._solicitudes_hoy_conteo >= self.max_por_dia:
                logger.warning(
                    f"[Gemini Quota] Límite diario ({self.max_por_dia} req/día) alcanzado."
                )
                return False

            ahora = time.time()
            limite_inferior = ahora - self.ventana_segundos

            while self._historial_tiempos and self._historial_tiempos[0] < limite_inferior:
                self._historial_tiempos.popleft()

            # Solo conceder inmediato si no hay elementos esperando en cola y hay espacio en el minuto
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
        Adquiere de forma atómica y compartida un slot en PostgreSQL (usando CuotaGeminiRepository).
        Garantiza sincronización exacta entre múltiples workers o procesos Uvicorn.
        """
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
                        # registrar_slot_consumido ya adquiere self._lock.
                        # Tomarlo aquí otra vez congelaba el worker (Lock no reentrante).
                        self.registrar_slot_consumido()
                    return concedido, motivo
        except Exception as e:
            # Con PostgreSQL habilitado, fallar cerrado: conceder localmente
            # permitiría superar la cuota global durante una caída de DB.
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
        futuro_resultado: Optional[Any] = None,
        solicitud_id: Optional[str] = None,
    ) -> tuple[SolicitudGeminiEncolada, int, float]:
        """
        Inserta una solicitud en la cola FIFO (y en PostgreSQL si está habilitada) y retorna
        (solicitud, posicion, tiempo_espera_estimado).
        """
        with self._lock:
            solicitud = SolicitudGeminiEncolada(
                id=solicitud_id or str(uuid.uuid4()),
                sintoma=sintoma,
                diagnostico_ml=diagnostico_ml,
                confianza_ml=confianza_ml,
                contexto_manual=contexto_manual,
                titulo_manual=titulo_manual,
                requiere_revision_humana=requiere_revision_humana,
                callback_completado=callback_completado,
                diagnostico_id=diagnostico_id,
                remitente=remitente,
                taller_id=taller_id,
                usuario_id=usuario_id,
                conversacion_id=conversacion_id,
                placa=placa,
                marca_modelo=marca_modelo,
                proveedor=proveedor or "meta",
                mensaje_inicial_id=mensaje_inicial_id,
                mensaje_salida_preliminar_id=mensaje_salida_preliminar_id,
                futuro_resultado=futuro_resultado,
            )
            self._cola_pendientes.append(solicitud)
            self._mapa_solicitudes[solicitud.id] = solicitud
            posicion = len(self._cola_pendientes)
            tiempo_estimado = self._calcular_tiempo_espera_con_lock(posicion)

            logger.info(
                f"[Gemini Queue] Solicitud {solicitud.id[:8]} encolada (Proveedor: {solicitud.proveedor}). "
                f"Posición en cola: {posicion} | Espera estimada: {tiempo_estimado}s."
            )

            # Intentar activar el worker background si hay un event loop disponible
            self.asegurar_worker_activo()

            return solicitud, posicion, tiempo_estimado

    async def encolar_solicitud_persistente_db(
        self,
        sintoma: str,
        diagnostico_ml: str,
        confianza_ml: float,
        contexto_manual: str,
        titulo_manual: str,
        requiere_revision_humana: bool = False,
        remitente: Optional[str] = None,
        taller_id: Optional[str] = None,
        usuario_id: Optional[str] = None,
        conversacion_id: Optional[str] = None,
        diagnostico_id: Optional[str] = None,
        proveedor: str = "meta",
        solicitud_id: Optional[str] = None,
    ) -> Tuple[SolicitudGeminiEncolada, int, float]:
        """
        Encola la solicitud tanto en memoria como en la tabla trabajos_gemini de PostgreSQL
        con el remitente cifrado de forma reversible.
        """
        solicitud, pos, espera = self.encolar_solicitud(
            sintoma=sintoma,
            diagnostico_ml=diagnostico_ml,
            confianza_ml=confianza_ml,
            contexto_manual=contexto_manual,
            titulo_manual=titulo_manual,
            requiere_revision_humana=requiere_revision_humana,
            remitente=remitente,
            taller_id=taller_id,
            usuario_id=usuario_id,
            conversacion_id=conversacion_id,
            diagnostico_id=diagnostico_id,
            proveedor=proveedor,
            solicitud_id=solicitud_id,
        )

        if database_configurada():
            try:
                db_engine = obtener_engine()
                async with AsyncSession(db_engine, expire_on_commit=False) as session:
                    async with session.begin():
                        trabajo_repo = TrabajoGeminiRepository(session)
                        await trabajo_repo.crear_trabajo(
                            trabajo_id=uuid.UUID(solicitud.id),
                            sintoma=sintoma,
                            diagnostico_ml=diagnostico_ml,
                            confianza_ml=confianza_ml,
                            contexto_manual=contexto_manual,
                            titulo_manual=titulo_manual,
                            requiere_revision_humana=requiere_revision_humana,
                            remitente=remitente,
                            proveedor=proveedor,
                            taller_id=uuid.UUID(taller_id) if taller_id else None,
                            usuario_id=uuid.UUID(usuario_id) if usuario_id else None,
                            conversacion_id=uuid.UUID(conversacion_id) if conversacion_id else None,
                            diagnostico_id=uuid.UUID(diagnostico_id) if diagnostico_id else None,
                        )
                        logger.info(
                            f"[Gemini Queue DB] Trabajo persistente {solicitud.id[:8]} creado en PostgreSQL."
                        )
            except Exception as e:
                logger.error(f"[Gemini Queue DB Insert Error] {e}")
                raise

        return solicitud, pos, espera

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
        remitente: Optional[str],
        proveedor: str,
        taller_id: str,
        usuario_id: str,
        conversacion_id: str,
        diagnostico_id: str,
    ) -> None:
        """Persiste el trabajo en la misma transacción del webhook.

        El worker solo podrá reclamarlo después del commit, por lo que nunca
        observará un diagnóstico o una conversación a medio guardar.
        """
        proveedor_normalizado = "meta" if proveedor.lower() in ("meta", "whatsapp") else proveedor.lower()
        if proveedor_normalizado not in {"meta", "twilio", "api"}:
            raise ValueError(f"Proveedor de cola no soportado: {proveedor}")

        repo = TrabajoGeminiRepository(session)
        await repo.crear_trabajo(
            trabajo_id=uuid.UUID(solicitud_id),
            sintoma=sintoma,
            diagnostico_ml=diagnostico_ml,
            confianza_ml=confianza_ml,
            contexto_manual=contexto_manual,
            titulo_manual=titulo_manual,
            requiere_revision_humana=requiere_revision_humana,
            remitente=remitente,
            proveedor=proveedor_normalizado,
            taller_id=uuid.UUID(taller_id),
            usuario_id=uuid.UUID(usuario_id),
            conversacion_id=uuid.UUID(conversacion_id),
            diagnostico_id=uuid.UUID(diagnostico_id),
        )

    def actualizar_contexto_encolado(
        self,
        solicitud_id: str,
        diagnostico_id: Optional[str] = None,
        remitente: Optional[str] = None,
        taller_id: Optional[str] = None,
        usuario_id: Optional[str] = None,
        conversacion_id: Optional[str] = None,
        proveedor: Optional[str] = None,
    ):
        """Actualiza la información de contexto (DB ID, teléfono, proveedor) de una solicitud ya encolada."""
        with self._lock:
            solicitud = self._mapa_solicitudes.get(solicitud_id)
            if solicitud:
                if diagnostico_id:
                    solicitud.diagnostico_id = diagnostico_id
                if remitente:
                    solicitud.remitente = remitente
                if taller_id:
                    solicitud.taller_id = taller_id
                if usuario_id:
                    solicitud.usuario_id = usuario_id
                if conversacion_id:
                    solicitud.conversacion_id = conversacion_id
                if proveedor:
                    solicitud.proveedor = proveedor

    def descolar_siguiente(self) -> Optional[SolicitudGeminiEncolada]:
        """Extrae el siguiente elemento de la cola FIFO para procesamiento."""
        with self._lock:
            if self._cola_pendientes:
                sol = self._cola_pendientes.popleft()
                self._mapa_solicitudes.pop(sol.id, None)
                return sol
            return None

    def tamaño_cola(self) -> int:
        """Retorna la cantidad actual de solicitudes encoladas en espera."""
        with self._lock:
            return len(self._cola_pendientes)

    def slots_utilizados(self) -> int:
        """Devuelve la cantidad de slots actualmente ocupados en la ventana."""
        with self._lock:
            ahora = time.time()
            limite_inferior = ahora - self.ventana_segundos
            while self._historial_tiempos and self._historial_tiempos[0] < limite_inferior:
                self._historial_tiempos.popleft()
            return len(self._historial_tiempos)

    def tiempo_espera_estimado(self) -> float:
        """Calcula el tiempo en segundos para que se libere el próximo slot."""
        with self._lock:
            return self._calcular_tiempo_espera_con_lock(posicion=1)

    def _calcular_tiempo_espera_con_lock(self, posicion: int = 1) -> float:
        """Cálculo interno del tiempo de espera para una posición dada."""
        ahora = time.time()
        limite_inferior = ahora - self.ventana_segundos
        while self._historial_tiempos and self._historial_tiempos[0] < limite_inferior:
            self._historial_tiempos.popleft()

        slots_libres = self.max_por_minuto - len(self._historial_tiempos)
        if slots_libres >= posicion:
            return 0.0

        if not self._historial_tiempos:
            return 0.0

        idx_relevante = min(len(self._historial_tiempos) - 1, max(0, posicion - slots_libres - 1))
        tiempo_mas_antiguo = self._historial_tiempos[idx_relevante]
        espera = max(0.5, (tiempo_mas_antiguo + self.ventana_segundos) - ahora)
        return round(espera, 2)

    def asegurar_worker_activo(self):
        """Activa el worker background en el loop de eventos activo si no está corriendo."""
        if not self._worker_corriendo:
            try:
                loop = asyncio.get_running_loop()
                self._loop = loop
                self._worker_corriendo = True
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
                # Alternar outbox y diagnosticos para evitar inanicion de la cola Gemini.
                if (
                    preferir_entrega
                    and database_configurada()
                    and await self._procesar_siguiente_entrega_whatsapp()
                ):
                    preferir_entrega = False
                    continue
                preferir_entrega = True

                # 1. Verificar si hay solicitudes en memoria o en PostgreSQL
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
                    espera = self.tiempo_espera_estimado()
                    if espera > 0:
                        await asyncio.sleep(min(espera, 0.5))
                        continue

                    # Adquirir slot compartido en PostgreSQL
                    concedido, motivo = await self.intentar_adquirir_slot_db()
                    
                    # Si no hay slot o se superó el límite diario RPD
                    if not concedido:
                        if "rpd_excedido" in motivo:
                            logger.warning("[Gemini Worker] Límite RPD alcanzado. Procesando en modo degradado...")
                        else:
                            if trabajo_db:
                                await self._posponer_trabajo_por_cuota_db(
                                    str(trabajo_db.id), motivo
                                )
                            await asyncio.sleep(1.0)
                            continue

                    # Extraer de memoria o usar el obtenido de PostgreSQL
                    if trabajo_db:
                        if trabajo_db.intentos > 3:
                            await self._marcar_trabajo_fallido_db(
                                str(trabajo_db.id), "Máximo de 3 intentos excedido."
                            )
                            continue
                        try:
                            remitente_descifrado = (
                                descifrar_texto_reversible(trabajo_db.remitente_cifrado)
                                if trabajo_db.remitente_cifrado else None
                            )
                        except ValueError as exc:
                            await self._marcar_trabajo_fallido_db(str(trabajo_db.id), str(exc))
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
                            requiere_revision_humana=trabajo_db.requiere_revision_humana,
                        )
                    else:
                        solicitud = self.descolar_siguiente()

                    if solicitud:
                        await self._procesar_solicitud_encolada(solicitud, forzar_degradado=(not concedido))
                else:
                    await asyncio.sleep(0.5)
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"[Gemini Queue Worker Loop Error] {e}")
                await asyncio.sleep(1.0)
        self._worker_corriendo = False

    async def procesar_siguiente_en_cola(self) -> Optional[Tuple[str, dict]]:
        """
        Procesa manualmente el siguiente elemento de la cola.
        Útil para pruebas unitarias o despacho forzado explícito.
        """
        solicitud = self.descolar_siguiente()
        if not solicitud:
            return None
        self.registrar_slot_consumido()
        return await self._procesar_solicitud_encolada(solicitud)

    async def _procesar_solicitud_encolada(
        self, solicitud: SolicitudGeminiEncolada, forzar_degradado: bool = False
    ) -> Tuple[str, dict]:
        """Procesa una solicitud descolada realizando la síntesis con Gemini o fallback local."""
        confianza_pct = int(solicitud.confianza_ml * 100)
        alerta_revision = (
            "\n⚠️ *Nota:* Confianza media del modelo (< 70%). Se requiere inspección física obligatoria en taller.\n"
            if solicitud.requiere_revision_humana
            else ""
        )

        prompt_sistema = f"""
        Eres 'CarBot', el asistente técnico de diagnóstico de precisión para mecánicos de taller automotriz.

        INFORMACIÓN CLAVE DE IA:
        - Diagnóstico Principal (Machine Learning): {solicitud.diagnostico_ml} (Confianza del modelo: {confianza_pct}%){alerta_revision}
        - Manual Técnico Recuperado (RAG): [{solicitud.titulo_manual}]
        {solicitud.contexto_manual}
        
        Consulta técnica del usuario: "{solicitud.sintoma}"
        
        REGLAS DE SEGURIDAD:
        1. La predicción ML es una HIPÓTESIS, no una falla confirmada.
        2. Usa exclusivamente pruebas y procedimientos presentes en el contexto RAG. No inventes pares de apriete, piezas ni pasos.
        3. Si la confianza es menor de 70%, exige inspección humana antes de desmontar o reemplazar componentes.
        4. Si ML y manual no son coherentes, indícalo y limita la respuesta a pruebas seguras.
        5. Si la consulta menciona GNV/GLP y pérdida de fuerza, exige primero una prueba comparativa controlada gasolina vs gas. Si solo falla a gas, prioriza presión del reductor, filtros, inyectores y calibración GNV; si falla con ambos, revisa encendido, admisión, escape, compresión y alimentación. No atribuyas la falla al embrague solo por mencionar GNV.
        6. Estructura la respuesta en las siguientes 3 secciones:

        🛠️ **1. Posible Falla Vehicular**
        Presenta la hipótesis ({solicitud.diagnostico_ml}), su confianza ({confianza_pct}%) y la evidencia pendiente.

        📖 **2. Procedimiento Técnico de Reparación**
        Primero pruebas de confirmación; luego pasos extraídos del manual RAG.

        ⏱️ **3. Tiempo Estimado y Gravedad**
        Indica urgencia, riesgos y necesidad de validación del mecánico.
        """

        api_key = settings.GEMINI_API_KEY
        texto_respuesta = ""
        metadatos = {}
        error_reintentable: Optional[str] = None

        if api_key and not forzar_degradado:
            try:
                modelo = settings.GEMINI_MODEL or "gemini-3.5-flash-lite"
                url = f"https://generativelanguage.googleapis.com/v1beta/models/{modelo}:generateContent"
                headers = {
                    "Content-Type": "application/json",
                    "x-goog-api-key": api_key,
                }
                payload = {"contents": [{"parts": [{"text": prompt_sistema}]}]}

                response = await asyncio.to_thread(
                    requests.post, url, json=payload, headers=headers, timeout=10
                )
                if response.status_code == 200:
                    data = response.json()
                    usage = data.get("usageMetadata", {})
                    texto_gemini = data['candidates'][0]['content']['parts'][0]['text'].strip()
                    tokens_in = int(usage.get("promptTokenCount", max(1, len(prompt_sistema) // 4)))
                    tokens_out = int(usage.get("candidatesTokenCount", max(1, len(texto_gemini) // 4)))

                    texto_respuesta = texto_gemini
                    metadatos = {
                        "usado": True,
                        "modelo": modelo,
                        "modo": "completo_ml_rag_llm",
                        "tokens_entrada": tokens_in,
                        "tokens_salida": tokens_out,
                    }
                else:
                    logger.warning(f"[Gemini Worker] HTTP {response.status_code}; aplicando fallback degradado.")
                    if response.status_code == 429 or response.status_code >= 500:
                        error_reintentable = f"Gemini HTTP {response.status_code}"
            except Exception as e:
                logger.error(f"[Gemini Worker Error] Falló llamada HTTP a Gemini: {e}")
                error_reintentable = f"Error temporal Gemini: {type(e).__name__}"

        if error_reintentable and database_configurada():
            await self._marcar_trabajo_reintento_db(solicitud.id, error_reintentable)
            logger.warning(
                f"[Gemini Worker] Solicitud {solicitud.id[:8]} programada para reintento: {error_reintentable}"
            )
            return "", {
                "usado": False,
                "modo": "en_cola_gemini",
                "reintentar": True,
                "error": error_reintentable,
            }

        # Si no hubo respuesta exitosa de Gemini, generar fallback degradado
        if not texto_respuesta:
            no_manual = "No se encontró" in solicitud.contexto_manual or "Coincidencia baja" in solicitud.titulo_manual
            seccion_1 = f"🛠️ **1. Posible Falla Vehicular (Modo Degradado ML+RAG):**\n• **Diagnóstico Sugerido (ML):** {solicitud.diagnostico_ml}\n• **Certeza del Modelo:** {confianza_pct}%{alerta_revision}"
            if no_manual:
                seccion_2 = "📖 **2. Procedimiento Técnico de Reparación:**\n⚠️ *Nota:* No se encontró un procedimiento específico en el manual de taller para esta consulta. Se sugiere revisión visual directa."
                seccion_3 = "⏱️ **3. Tiempo Estimado y Gravedad:**\n• **Tiempo Estimado:** 30-45 minutos (Evaluación inicial)\n• **Gravedad:** Por determinar en taller"
            else:
                seccion_2 = f"📖 **2. Procedimiento Técnico de Reparación ({solicitud.titulo_manual}):**\n{solicitud.contexto_manual}"
                seccion_3 = "⏱️ **3. Tiempo Estimado y Gravedad:**\n• **Recomendación Técnica:** Siga los pasos del manual de taller adjunto y realice las pruebas de verificación correspondientes."

            texto_respuesta = f"{seccion_1}\n\n{seccion_2}\n\n{seccion_3}"
            metadatos = {
                "usado": False,
                "modelo": None,
                "modo": "diagnostico_degradado_ml_rag",
                "tokens_entrada": 0,
                "tokens_salida": 0,
            }

        # 1. Actualizar registro en PostgreSQL si diagnostico_id o trabajo persistente está presente
        if settings.database.enabled:
            await self._actualizar_diagnostico_y_trabajo_db(solicitud, texto_respuesta, metadatos)

        # 2. Persistir primero el segundo mensaje en el outbox durable. Otro ciclo
        # del worker lo enviará y reintentará sin volver a consumir Gemini.
        if solicitud.conversacion_id and settings.database.enabled:
            resumen_whatsapp = self._crear_resumen_whatsapp(solicitud, texto_respuesta)
            await self._persistir_mensaje_saliente_db(solicitud, resumen_whatsapp, "pendiente")

        # 4. Invocar callback de completado si existe
        if solicitud.callback_completado:
            try:
                if inspect.iscoroutinefunction(solicitud.callback_completado):
                    await solicitud.callback_completado(solicitud, texto_respuesta, metadatos)
                else:
                    solicitud.callback_completado(solicitud, texto_respuesta, metadatos)
            except Exception as cb_err:
                logger.error(f"[Gemini Worker Callback Error] {cb_err}")

        # 5. Resolver el futuro si existe
        if solicitud.futuro_resultado and hasattr(solicitud.futuro_resultado, "set_result"):
            if not solicitud.futuro_resultado.done():
                solicitud.futuro_resultado.set_result((texto_respuesta, metadatos))

        logger.info(
            f"[Gemini Queue Worker] Solicitud {solicitud.id[:8]} procesada exitosamente. Modo: {metadatos.get('modo')}"
        )

        return texto_respuesta, metadatos

    async def _marcar_trabajo_reintento_db(self, solicitud_id: str, error: str) -> None:
        try:
            trabajo_id = uuid.UUID(solicitud_id)
        except (ValueError, TypeError):
            return
        async with AsyncSession(obtener_engine(), expire_on_commit=False) as session:
            async with session.begin():
                await TrabajoGeminiRepository(session).marcar_reintento(
                    trabajo_id, espera_segundos=15, error_mensaje=error
                )

    async def _posponer_trabajo_por_cuota_db(self, solicitud_id: str, motivo: str) -> None:
        """Libera el lease sin contar un intento porque Gemini no fue invocado."""
        try:
            trabajo_id = uuid.UUID(solicitud_id)
        except (ValueError, TypeError):
            return
        async with AsyncSession(obtener_engine(), expire_on_commit=False) as session:
            async with session.begin():
                await TrabajoGeminiRepository(session).posponer_por_cuota(
                    trabajo_id, espera_segundos=5, motivo=motivo
                )

    async def _marcar_trabajo_fallido_db(self, solicitud_id: str, error: str) -> None:
        try:
            trabajo_id = uuid.UUID(solicitud_id)
        except (ValueError, TypeError):
            return
        async with AsyncSession(obtener_engine(), expire_on_commit=False) as session:
            async with session.begin():
                await TrabajoGeminiRepository(session).marcar_fallido(trabajo_id, error)

    async def _procesar_siguiente_entrega_whatsapp(self) -> bool:
        """Reclama, envía y actualiza un mensaje del outbox."""
        mensaje = None
        async with AsyncSession(obtener_engine(), expire_on_commit=False) as session:
            async with session.begin():
                mensaje = await MensajeRepository(session).obtener_siguiente_salida_bloqueada()
        if not mensaje:
            return False

        try:
            destino = descifrar_texto_reversible(mensaje.destinatario_cifrado)
        except ValueError as exc:
            resultado_estado, externo, error = "fallido", None, str(exc)
        else:
            resultado = await whatsapp_provider_service.enviar(
                mensaje.proveedor or "meta", destino, mensaje.texto or ""
            )
            externo = resultado.id_externo
            error = resultado.error
            if resultado.exitoso:
                resultado_estado = "enviado"
            elif resultado.reintentable and mensaje.intentos_entrega < 3:
                resultado_estado = "pendiente_reintento"
            else:
                resultado_estado = "fallido"

        async with AsyncSession(obtener_engine(), expire_on_commit=False) as session:
            async with session.begin():
                await MensajeRepository(session).registrar_resultado_entrega(
                    mensaje.id,
                    estado=resultado_estado,
                    id_externo=externo,
                    error=error,
                    reintentar_en_segundos=min(300, 15 * (2 ** max(0, mensaje.intentos_entrega - 1))),
                )
        return True

    async def _actualizar_diagnostico_y_trabajo_db(
        self, solicitud: SolicitudGeminiEncolada, texto_respuesta: str, metadatos: dict
    ):
        """Actualiza el estado de la fila en PostgreSQL y marca el trabajo como completado."""
        try:
            db_engine = obtener_engine()
            modo_final = metadatos.get("modo", "completo_ml_rag_llm")
            fuente_final = "gemini" if metadatos.get("usado") else "hibrido"
            conclusion_final = (
                f"[{modo_final.upper()}] Síntesis Gemini ({metadatos.get('modelo') or settings.GEMINI_MODEL})"
                if metadatos.get("usado")
                else f"[{modo_final.upper()}] Fallback tras salida de cola"
            )

            async with AsyncSession(db_engine, expire_on_commit=False) as session:
                async with session.begin():
                    # 1. Actualizar trabajo_gemini
                    trabajo_repo = TrabajoGeminiRepository(session)
                    trabajo_id = None
                    try:
                        trabajo_id = uuid.UUID(solicitud.id)
                    except ValueError:
                        pass

                    if trabajo_id:
                        await trabajo_repo.marcar_completado(trabajo_id)

                    # 2. Actualizar diagnostico
                    if solicitud.diagnostico_id:
                        diag_repo = DiagnosticoRepository(session)
                        diag = await diag_repo.obtener_por_id(uuid.UUID(solicitud.diagnostico_id))
                        if diag:
                            diag.modo_diagnostico = modo_final
                            diag.fuente = fuente_final
                            diag.conclusion_mecanico = conclusion_final
                            diag.sintesis_llm = texto_respuesta

                            if metadatos.get("usado"):
                                operaciones_repo = OperacionesRepository(session)
                                tokens_in = metadatos.get("tokens_entrada", 0)
                                tokens_out = metadatos.get("tokens_salida", 0)
                                
                                # Manejar nivel gratuito vs plan pagado
                                if settings.gemini_use_free_tier:
                                    costo = Decimal("0.000000")
                                else:
                                    p_in = Decimal(str(settings.gemini_input_price_per_million / 1_000_000))
                                    p_out = Decimal(str(settings.gemini_output_price_per_million / 1_000_000))
                                    costo = Decimal(tokens_in) * p_in + Decimal(tokens_out) * p_out

                                await operaciones_repo.registrar_uso_api(
                                    taller_id=diag.taller_id,
                                    proveedor="google",
                                    operacion="gemini_generacion_diagnostico_cola",
                                    modelo=metadatos.get("modelo") or settings.GEMINI_MODEL,
                                    tokens_entrada=tokens_in,
                                    tokens_salida=tokens_out,
                                    unidades=Decimal(str(tokens_in + tokens_out)),
                                    costo_estimado=costo,
                                    moneda="USD",
                                    diagnostico_id=diag.id,
                                )
                    logger.info(
                        f"[Gemini Worker DB] Diagnóstico {solicitud.diagnostico_id or solicitud.id[:8]} actualizado en DB -> {modo_final}."
                    )
        except Exception as e:
            logger.error(f"[Gemini Worker DB Update Error] {e}")
            raise

    @staticmethod
    def _crear_resumen_whatsapp(
        solicitud: SolicitudGeminiEncolada, texto_respuesta: str
    ) -> str:
        """Crea una salida breve y operativa; el detalle completo queda en PostgreSQL."""
        confianza = max(0, min(100, int(solicitud.confianza_ml * 100)))
        sintoma = solicitud.sintoma.lower()
        es_gas = "gnv" in sintoma or "gas natural" in sintoma or "glp" in sintoma
        hipotesis = solicitud.diagnostico_ml
        describe_patinamiento = (
            ("rpm" in sintoma or "revoluciones" in sintoma)
            and ("no avanza" in sintoma or "sin aumentar velocidad" in sintoma)
        )
        if es_gas and not describe_patinamiento and any(
            termino in hipotesis.lower() for termino in ("embrague", "clutch", "disco")
        ):
            hipotesis = "Pérdida de potencia bajo carga: diferenciar sistema GNV/GLP y motor"

        if es_gas:
            primera_prueba = (
                "Comparar el comportamiento en gasolina y GNV/GLP bajo carga. "
                "Si solo falla a gas, revisar presión, filtros, inyectores y calibración."
            )
        else:
            primera_prueba = "Realizar escaneo DTC e inspección funcional antes de desmontar o cambiar piezas."

        texto_limpio = texto_respuesta.lower().replace("*", "")
        if "gravedad: alta" in texto_limpio:
            gravedad = "Alta"
        elif "gravedad: media" in texto_limpio:
            gravedad = "Media"
        elif "gravedad: baja" in texto_limpio:
            gravedad = "Baja"
        else:
            gravedad = "Por confirmar"
        revision = " Se requiere validación física." if solicitud.requiere_revision_humana else ""
        return (
            "🔧 *Resumen de diagnóstico*\n"
            f"Hipótesis: *{hipotesis}*\n"
            f"Confianza ML: *{confianza}%*.{revision}\n"
            f"Primera prueba: {primera_prueba}\n"
            f"Gravedad: *{gravedad}*.\n"
            "📋 Análisis completo disponible en el panel del taller."
        )

    async def _despachar_mensaje_proveedor(self, solicitud: SolicitudGeminiEncolada, texto_respuesta: str) -> str:
        """Despacha la notificación según el proveedor (Meta Graph API o Twilio) usando remitente configurable."""
        prov = (solicitud.proveedor or "meta").lower()
        remitente = solicitud.remitente or ""
        mensaje_notif = self._crear_resumen_whatsapp(solicitud, texto_respuesta)

        try:
            if prov == "twilio" and settings.TWILIO_ACCOUNT_SID and settings.TWILIO_AUTH_TOKEN:
                url = f"https://api.twilio.com/2010-04-01/Accounts/{settings.TWILIO_ACCOUNT_SID}/Messages.json"
                auth = (settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
                dest = remitente if remitente.startswith("whatsapp:") else f"whatsapp:{remitente}"
                from_num = getattr(settings, "twilio_whatsapp_from", "whatsapp:+14155238886")
                data = {
                    "From": from_num,
                    "To": dest,
                    "Body": mensaje_notif,
                }
                res = await asyncio.to_thread(requests.post, url, auth=auth, data=data, timeout=5)
                if res.status_code in (200, 201):
                    logger.info(f"[Twilio Worker WhatsApp] Notificación enviada a {remitente} (Status {res.status_code}).")
                    return "enviado"
                elif res.status_code == 429:
                    logger.warning(f"[Twilio Worker WhatsApp] HTTP 429 Límite de tasa para {remitente}.")
                    return "pendiente_reintento"
                else:
                    logger.error(f"[Twilio Worker WhatsApp Error] HTTP {res.status_code} para {remitente}.")
                    return "fallido"

            elif prov == "meta" and settings.TOKEN_WHATSAPP and settings.TELEFONO_ID:
                version = settings.meta_graph_api_version.strip("/")
                url = f"https://graph.facebook.com/{version}/{settings.TELEFONO_ID}/messages"
                headers = {
                    "Authorization": f"Bearer {settings.TOKEN_WHATSAPP}",
                    "Content-Type": "application/json",
                }
                num_dest = remitente.replace("whatsapp:", "").strip()
                payload = {
                    "messaging_product": "whatsapp",
                    "to": num_dest,
                    "type": "text",
                    "text": {"body": mensaje_notif},
                }
                res = await asyncio.to_thread(requests.post, url, headers=headers, json=payload, timeout=5)
                if res.status_code in (200, 201):
                    logger.info(f"[Meta Worker WhatsApp] Notificación enviada a {remitente} (Status {res.status_code}).")
                    return "enviado"
                elif res.status_code == 429:
                    logger.warning(f"[Meta Worker WhatsApp] HTTP 429 Límite de tasa para {remitente}.")
                    return "pendiente_reintento"
                else:
                    logger.error(f"[Meta Worker WhatsApp Error] HTTP {res.status_code} para {remitente}.")
                    return "fallido"

            return "no_aplica"
        except Exception as e:
            logger.error(f"[Worker WhatsApp Dispatch Error] {e}")
            return "fallido"

    async def _persistir_mensaje_saliente_db(
        self, solicitud: SolicitudGeminiEncolada, texto_respuesta: str, estado_entrega: str
    ):
        """Persiste el segundo mensaje de salida (síntesis de Gemini) en la tabla `mensajes` de PostgreSQL."""
        try:
            db_engine = obtener_engine()
            out_msg_id = f"out_gemini_{uuid.uuid4()}"
            texto_completo = texto_respuesta
            costo_msg = Decimal(str(getattr(settings, "twilio_message_price_usd", 0.0))) if solicitud.proveedor == "twilio" else COSTO_META_MENSAJE_SERVICIO_USD

            async with AsyncSession(db_engine, expire_on_commit=False) as session:
                async with session.begin():
                    msg_repo = MensajeRepository(session)
                    await msg_repo.crear_mensaje(
                        conversacion_id=uuid.UUID(solicitud.conversacion_id),
                        taller_id=uuid.UUID(solicitud.taller_id) if solicitud.taller_id else None,
                        usuario_id=uuid.UUID(solicitud.usuario_id) if solicitud.usuario_id else None,
                        meta_message_id=out_msg_id,
                        direccion="salida",
                        tipo="texto",
                        texto=texto_completo,
                        categoria_cobro="servicio",
                        estado_entrega="pendiente",
                        costo_estimado=costo_msg,
                        moneda="USD",
                        proveedor=("meta" if solicitud.proveedor == "whatsapp" else solicitud.proveedor),
                        destinatario_cifrado=(
                            cifrar_texto_reversible(solicitud.remitente)
                            if solicitud.remitente else None
                        ),
                        disponible_entrega_en=datetime.now(timezone.utc),
                    )
                logger.info(
                    f"[Gemini Worker DB] Segundo mensaje de síntesis guardado en DB para conv {solicitud.conversacion_id[:8]}."
                )
        except Exception as e:
            logger.error(f"[Gemini Worker DB Message Save Error] {e}")
            raise

    def reiniciar(self):
        """Reinicia el historial de marcas y vacía la cola (útil para pruebas unitarias)."""
        with self._lock:
            self._historial_tiempos.clear()
            self._cola_pendientes.clear()
            self._mapa_solicitudes.clear()
            self._solicitudes_hoy_conteo = 0


# Instancia global del limitador y cola de Gemini (12 req/min / 18 req/día)
gemini_rate_limiter = GeminiRateLimiter()
