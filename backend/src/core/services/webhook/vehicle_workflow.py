"""Validación de placa y perfil sin descartar mensajes multidato."""
import re
from typing import Any

from src.core.conversacion.extractor_hechos import ExtractorHechos
from src.core.services.whatsapp_provider import whatsapp_provider_service
from src.core.vehicle_profile import extraer_datos_vehiculo
from src.infrastructure.database.repositories.vehiculo_repository import normalizar_placa

_COMANDO_NUEVO_CASO = re.compile(
    r"^\s*(?:nuevo\s+(?:caso|problema|diagnostico|diagnóstico|vehiculo|vehículo)|"
    r"nueva\s+consulta|otro\s+(?:caso|vehiculo|vehículo|carro)|reiniciar)\s*[.!]*\s*$",
    re.IGNORECASE,
)
_COMANDO_CANCELAR_CASO = re.compile(
    r"^\s*(?:cancelar\s+(?:consulta|caso|diagnostico|diagnóstico)|cancelar)\s*[.!]*\s*$",
    re.IGNORECASE,
)


def _comando_caso(texto: str) -> str | None:
    """Reconoce comandos explícitos para evitar mezclar vehículos o síntomas."""

    if _COMANDO_CANCELAR_CASO.match(texto or ""):
        return "cancelar"
    if _COMANDO_NUEVO_CASO.match(texto or ""):
        return "nuevo"
    return None


def _perfil_completo(datos: dict[str, Any]) -> bool:
    return all(datos.get(campo) for campo in ("marca", "modelo", "anio"))


def _texto_perfil_vehiculo(datos: dict[str, Any]) -> str:
    partes = [str(datos[campo]) for campo in ("marca", "modelo", "anio") if datos.get(campo)]
    return " ".join(partes)


def _mensaje_solicitar_perfil() -> str:
    return (
        "🚗 Indica *marca, modelo y año* del vehículo.\n"
        "Ejemplo: *Toyota Yaris 2018*."
    )


async def preparar_flujo_vehiculo(
    self, session, conversacion, texto_cliente, tipo_mensaje, proveedor, remitente, placa, marca_modelo,
):
    contexto_placa = dict(conversacion.contexto or {})
    comando_caso = _comando_caso(texto_cliente) if tipo_mensaje == 'text' else None
    if comando_caso == 'cancelar':
        self.gestor.session_manager.finalizar_caso(str(conversacion.id))
        for clave in ('validacion_diagnostico', 'conversation_state', 'estado_conversacion', 'posttest_placa_pendiente', 'preplate_pending_input', 'nueva_consulta_placa_pendiente', 'perfil_vehiculo_pendiente', 'perfil_vehiculo', 'placa', 'placa_posttest'):
            contexto_placa.pop(clave, None)
        contexto_placa['posttest_placa_pendiente'] = True
        conversacion.contexto = contexto_placa
        respuesta_cancelar = '🛑 Consulta cancelada. El historial anterior se conserva.\n\nPara iniciar otro diagnóstico escribe *NUEVO CASO*.'
        await whatsapp_provider_service.enviar(proveedor, remitente, respuesta_cancelar)
        await session.commit()
        return ({'status': 'consulta_cancelada', 'respuesta': respuesta_cancelar}, placa, marca_modelo, texto_cliente)
    if comando_caso == 'nuevo':
        self.gestor.session_manager.finalizar_caso(str(conversacion.id))
        for clave in ('validacion_diagnostico', 'conversation_state', 'estado_conversacion'):
            contexto_placa.pop(clave, None)
        placa_anterior = contexto_placa.get('placa_posttest') or contexto_placa.get('placa')
        if placa_anterior:
            contexto_placa['nueva_consulta_placa_pendiente'] = True
            respuesta_nuevo = '🔄 Nueva consulta iniciada. ¿Deseas usar la misma placa registrada?\nResponde *SÍ* para usarla o envía la placa del otro vehículo.'
        else:
            contexto_placa['posttest_placa_pendiente'] = True
            respuesta_nuevo = '🔄 Nueva consulta iniciada. Ingresa la placa del vehículo.'
        conversacion.contexto = contexto_placa
        await whatsapp_provider_service.enviar(proveedor, remitente, respuesta_nuevo)
        await session.commit()
        return ({'status': 'esperando_placa', 'respuesta': respuesta_nuevo}, placa, marca_modelo, texto_cliente)
    if contexto_placa.get('nueva_consulta_placa_pendiente'):
        respuesta_corta = texto_cliente.strip().lower().strip(' .,!¡¿?')
        if respuesta_corta in {'si', 'sí', 's', 'correcto', 'correcta'}:
            contexto_placa.pop('nueva_consulta_placa_pendiente', None)
            contexto_placa['perfil_vehiculo_pendiente'] = True
            conversacion.contexto = contexto_placa
            respuesta_perfil = _mensaje_solicitar_perfil()
            await whatsapp_provider_service.enviar(proveedor, remitente, respuesta_perfil)
            await session.commit()
            return ({'status': 'esperando_perfil_vehiculo', 'respuesta': respuesta_perfil}, placa, marca_modelo, texto_cliente)
        try:
            placa_nueva = normalizar_placa(texto_cliente)
        except ValueError:
            respuesta_placa = 'Responde *SÍ* para usar la misma placa o ingresa una placa válida.'
            await whatsapp_provider_service.enviar(proveedor, remitente, respuesta_placa)
            await session.commit()
            return ({'status': 'esperando_placa', 'respuesta': respuesta_placa}, placa, marca_modelo, texto_cliente)
        contexto_placa['placa'] = placa_nueva
        contexto_placa['placa_posttest'] = placa_nueva
        contexto_placa.pop('nueva_consulta_placa_pendiente', None)
        contexto_placa['perfil_vehiculo_pendiente'] = True
        conversacion.contexto = contexto_placa
        respuesta_perfil = _mensaje_solicitar_perfil()
        await whatsapp_provider_service.enviar(proveedor, remitente, respuesta_perfil)
        await session.commit()
        return ({'status': 'esperando_perfil_vehiculo', 'respuesta': respuesta_perfil}, placa, marca_modelo, texto_cliente)
    placa_persistida = contexto_placa.get('placa_posttest') or contexto_placa.get('placa')
    if placa_persistida and placa in ('WAPP-01', 'SIN-PLACA', ''):
        placa = placa_persistida
    if placa in ('WAPP-01', 'SIN-PLACA', ''):
        continuar_diagnostico_preplate = False
        placa_en_texto = ExtractorHechos.extraer_placa(texto_cliente) if tipo_mensaje == 'text' else None
        if placa_en_texto:
            placa = normalizar_placa(placa_en_texto)
            contexto_placa['placa'] = placa
            contexto_placa['placa_posttest'] = placa
            contexto_placa.pop('posttest_placa_pendiente', None)
            conversacion.contexto = contexto_placa
            continuar_diagnostico_preplate = True
        if not continuar_diagnostico_preplate and contexto_placa.get('posttest_placa_pendiente'):
            try:
                placa = normalizar_placa(texto_cliente)
            except ValueError:
                respuesta_placa = 'Indique una placa válida para continuar el diagnóstico.'
            else:
                contexto_placa['placa_posttest'] = placa
                contexto_placa['placa'] = placa
                contexto_placa.pop('posttest_placa_pendiente', None)
                texto_preplate = contexto_placa.pop('preplate_pending_input', None)
                conversacion.contexto = contexto_placa
                if texto_preplate:
                    texto_cliente = texto_preplate
                    continuar_diagnostico_preplate = True
                else:
                    respuesta_placa = 'Placa registrada. ' + _mensaje_solicitar_perfil()
                    contexto_placa['perfil_vehiculo_pendiente'] = True
        elif not continuar_diagnostico_preplate:
            contexto_placa['posttest_placa_pendiente'] = True
            if tipo_mensaje == 'image':
                respuesta_placa = '📷 Para asociar la foto al vehículo, primero indica su placa y luego vuelve a enviar la imagen. No guardamos el archivo de la foto.'
            elif ExtractorHechos.contiene_informacion_diagnostica(texto_cliente):
                contexto_placa['preplate_pending_input'] = texto_cliente
            if tipo_mensaje != 'image':
                respuesta_placa = 'Hola, ¿qué tal? Soy CarBot y estoy aquí para apoyarte con el diagnóstico del vehículo. Para comenzar, ingresa la placa del vehículo.'
            conversacion.contexto = contexto_placa
        if not continuar_diagnostico_preplate:
            await whatsapp_provider_service.enviar(proveedor, remitente, respuesta_placa)
            await session.commit()
            return ({'status': 'esperando_placa', 'respuesta': respuesta_placa}, placa, marca_modelo, texto_cliente)
    placa = contexto_placa.get('placa_posttest') or contexto_placa.get('placa') or placa
    if contexto_placa.get('perfil_vehiculo_pendiente') and tipo_mensaje == 'text':
        datos_perfil = extraer_datos_vehiculo(texto_cliente)
        if not _perfil_completo(datos_perfil):
            respuesta_perfil = _mensaje_solicitar_perfil()
            await whatsapp_provider_service.enviar(proveedor, remitente, respuesta_perfil)
            await session.commit()
            return ({'status': 'esperando_perfil_vehiculo', 'respuesta': respuesta_perfil}, placa, marca_modelo, texto_cliente)
        contexto_placa['perfil_vehiculo'] = datos_perfil
        contexto_placa.pop('perfil_vehiculo_pendiente', None)
        conversacion.contexto = contexto_placa
        if ExtractorHechos.contiene_informacion_diagnostica(texto_cliente):
            pass
        else:
            respuesta_perfil = f'✅ Vehículo registrado: *{_texto_perfil_vehiculo(datos_perfil)}*.\n\nAhora describe el síntoma del vehículo.'
            await whatsapp_provider_service.enviar(proveedor, remitente, respuesta_perfil)
            await session.commit()
            return ({'status': 'esperando_sintoma', 'respuesta': respuesta_perfil}, placa, marca_modelo, texto_cliente)
    perfil_vehiculo = contexto_placa.get('perfil_vehiculo') or {}
    if tipo_mensaje == 'text' and texto_cliente:
        datos_correccion = extraer_datos_vehiculo(texto_cliente)
        if datos_correccion.get('marca') and datos_correccion['marca'].lower() not in ('generico', 'vehiculo', 'desconocido'):
            perfil_vehiculo.update(datos_correccion)
            contexto_placa['perfil_vehiculo'] = perfil_vehiculo
            conversacion.contexto = contexto_placa
    if perfil_vehiculo.get('marca') or _perfil_completo(perfil_vehiculo):
        marca_modelo = _texto_perfil_vehiculo(perfil_vehiculo)
    return None, placa, marca_modelo, texto_cliente
