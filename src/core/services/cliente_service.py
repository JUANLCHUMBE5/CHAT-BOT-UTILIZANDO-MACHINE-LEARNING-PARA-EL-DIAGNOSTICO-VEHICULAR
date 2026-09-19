"""
Servicio de atención automatizada para clientes de WhatsApp.

Gestiona las consultas informativas del taller (horarios, servicios, ubicación, citas)
y la creación de solicitudes de acceso para mecánicos, sin ejecutar modelos de ML, RAG ni Gemini.
"""

from __future__ import annotations

import unicodedata

from sqlalchemy.ext.asyncio import AsyncSession

from src.infrastructure.database.models.catalogs import Taller, Usuario
from src.infrastructure.database.repositories.solicitud_acceso_repository import SolicitudAccesoRepository


class ClienteService:
    """Procesador de interacciones conversacionales para contactos con rol cliente."""

    def __init__(self, session: AsyncSession):
        self.session = session
        self.solicitud_repo = SolicitudAccesoRepository(session)

    def _obtener_datos_taller(self, taller: Taller) -> dict[str, str]:
        """Extrae y formatea los datos informativos reales del taller."""
        nombre = taller.nombre or "Taller Automotriz"
        horario = taller.horario_atencion or "Horario disponible en recepción"
        direccion = taller.direccion or "Por favor consultar dirección exacta con el taller"
        telefono = taller.telefono or ""
        servicios = taller.servicios or "• Diagnóstico y mantenimiento automotriz integral"
        maps_url = taller.google_maps_url or ""
        return {
            "nombre": nombre,
            "horario": horario,
            "direccion": direccion,
            "telefono": telefono,
            "servicios": servicios,
            "maps_url": maps_url,
        }

    async def procesar_mensaje_cliente(
        self,
        usuario: Usuario,
        taller: Taller,
        texto_usuario: str,
    ) -> str:
        """
        Analiza el texto del cliente y genera la respuesta correspondiente.
        Garantiza que no se invoque ML, RAG ni Gemini.
        """
        info = self._obtener_datos_taller(taller)
        texto_limpio = (texto_usuario or "").strip().lower()
        texto_sin_acentos = "".join(
            caracter
            for caracter in unicodedata.normalize("NFD", texto_limpio)
            if unicodedata.category(caracter) != "Mn"
        )

        # 0. Saludos directos -> Menú de bienvenida principal
        if any(
            g in texto_sin_acentos
            for g in (
                "hola",
                "buenos dias",
                "buenas tardes",
                "buenas noches",
                "buen dia",
                "saludos",
                "menu",
                "menú",
                "inicio",
                "opciones",
                "ayuda",
            )
        ) and not any(k in texto_sin_acentos for k in ("mecanico", "acceso", "precio", "cita", "donde")):
            return (
                f"👋 *Hola, bienvenido a {info['nombre']}*\n\n"
                f"🕐 *Horario:* {info['horario']}\n"
                f"📍 *Dirección:* {info['direccion']}\n\n"
                "¿En qué podemos ayudarte hoy? Responde con el número de tu opción:\n"
                "1️⃣ *Consultar nuestros servicios*\n"
                "2️⃣ *Solicitar una cita*\n"
                "3️⃣ *Ver nuestra ubicación y horarios*\n"
                "4️⃣ *Solicitar acceso como mecánico*\n\n"
                "_Escribe el número de la opción o tu consulta._"
            )

        # 1. Opción: Solicitar acceso como mecánico
        if (
            texto_sin_acentos in ("4", "opcion 4", "opción 4")
            or "soy mecanico" in texto_sin_acentos
            or "quiero acceso" in texto_sin_acentos
            or "solicitar acceso" in texto_sin_acentos
            or "acceso mecanico" in texto_sin_acentos
            or "dar acceso" in texto_sin_acentos
        ):
            return await self._manejar_solicitud_mecanico(usuario, taller, info)

        # 2. Opción: Consultar servicios y precios
        if (
            texto_sin_acentos in ("1", "opcion 1", "opción 1")
            or any(k in texto_sin_acentos for k in ("servicio", "servicios", "que hacen", "trabajos", "precio", "precios", "costo", "costos", "tarifa"))
        ):
            return (
                f"🔧 *Servicios ofrecidos en {info['nombre']}*\n\n"
                f"{info['servicios']}\n\n"
                "💰 *Precios referenciales:* Los presupuestos formales se emiten tras la inspección física en el taller.\n\n"
                "💡 _Para agendar una revisión, responde *2* o escribe *cita*._"
            )

        # 3. Opción: Solicitar cita / Reservar atención
        if (
            texto_sin_acentos in ("2", "opcion 2", "opción 2")
            or any(k in texto_sin_acentos for k in ("cita", "citas", "reservar", "reserva", "agendar", "agenda", "turno", "atencion", "atención"))
        ):
            contacto = (
                f"📞 *Teléfono / WhatsApp de Recepción:* {info['telefono']}\n"
                if info["telefono"]
                else "💬 *Contacto:* Continúa la reserva por este mismo chat.\n"
            )
            return (
                f"📅 *Reserva de Atención - {info['nombre']}*\n\n"
                "Para agendar una cita o revisión prioritaria:\n"
                f"{contacto}"
                f"📍 *Dirección:* {info['direccion']}\n"
                f"🕐 *Horario de atención:* {info['horario']}\n\n"
                "Puedes escribirnos el modelo de tu vehículo y el motivo de tu visita para tener preparado a nuestro equipo."
            )

        # 4. Opción: Ver ubicación / Dirección / Horario
        if (
            texto_sin_acentos in ("3", "opcion 3", "opción 3")
            or any(k in texto_sin_acentos for k in ("ubicacion", "donde", "direccion", "llegar", "mapa", "maps", "horario", "dias de atencion", "telefono", "contacto"))
        ):
            maps_sec = f"\n🗺️ *Google Maps:* {info['maps_url']}" if info['maps_url'] else ""
            telefono_sec = (
                f"📞 *Teléfono de contacto:* {info['telefono']}\n"
                if info["telefono"]
                else ""
            )
            return (
                f"📍 *Ubicación y Contacto - {info['nombre']}*\n\n"
                f"🏠 *Dirección:* {info['direccion']}{maps_sec}\n"
                f"🕐 *Horario de atención:* {info['horario']}\n"
                f"{telefono_sec}\n"
                "¡Te esperamos!"
            )

        # 5. Saludo o menú general por defecto
        maps_inline = f"\n🗺️ *Ubicación:* {info['maps_url']}" if info['maps_url'] else ""
        return (
            f"👋 *Hola, bienvenido a {info['nombre']}*\n\n"
            f"🕐 *Horario:* {info['horario']}\n"
            f"📍 *Dirección:* {info['direccion']}{maps_inline}\n\n"
            "¿En qué podemos ayudarte hoy? Responde con el número de tu opción:\n"
            "1️⃣ *Consultar nuestros servicios*\n"
            "2️⃣ *Solicitar una cita*\n"
            "3️⃣ *Ver nuestra ubicación y horarios*\n"
            "4️⃣ *Solicitar acceso como mecánico*\n\n"
            "_Escribe el número de la opción o tu consulta._"
        )

    async def _manejar_solicitud_mecanico(
        self, usuario: Usuario, taller: Taller, info: dict[str, str]
    ) -> str:
        """Crea o verifica una solicitud de acceso como mecánico."""
        solicitud_pendiente = await self.solicitud_repo.obtener_pendiente_por_usuario(
            usuario_id=usuario.id,
            taller_id=taller.id,
        )
        if solicitud_pendiente:
            return (
                f"⏳ *Solicitud de Mecánico en Trámite*\n\n"
                f"Ya tienes una solicitud pendiente de revisión por el administrador de *{info['nombre']}*.\n\n"
                "Te enviaremos una confirmación por este medio en cuanto tu acceso sea autorizado."
            )

        await self.solicitud_repo.crear_solicitud(
            usuario_id=usuario.id,
            taller_id=taller.id,
            rol_solicitado="mecanico",
            observaciones="Solicitado vía menú interactivo de WhatsApp",
        )

        return (
            f"📋 *Solicitud de Acceso como Mecánico Registrada*\n\n"
            f"Tu solicitud ha sido enviada al administrador de *{info['nombre']}*.\n\n"
            "✅ *Próximos pasos:*\n"
            "1. El administrador validará tu identidad en el panel del taller.\n"
            "2. Recibirás la confirmación por este mismo chat de WhatsApp.\n"
            "3. Desde ese momento podrás consultar diagnósticos vehiculares con asistencia técnica inteligente.\n\n"
            "_No necesitas usuario ni contraseña para el panel web._"
        )
