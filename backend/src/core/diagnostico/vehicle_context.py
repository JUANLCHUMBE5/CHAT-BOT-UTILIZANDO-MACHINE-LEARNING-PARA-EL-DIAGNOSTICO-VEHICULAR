"""Formateo y resolución de perfil de vehículo para diagnóstico y consultas técnicas."""

from __future__ import annotations

from typing import List

from src.core.diagnostico.models import ResultadoDiagnostico


def formatear_perfil_vehiculo(perfil: dict) -> str:
    """Formatea los datos confirmados del vehículo para inyectar en el contexto técnico."""
    etiquetas = {
        "marca": "Marca",
        "modelo": "Modelo",
        "anio": "Año",
        "motor": "Motor",
        "combustible": "Combustible",
        "kilometraje": "Kilometraje confirmado",
        "equipo_gas": "Equipo GNV/GLP",
    }
    return "\n".join(
        f"- {etiquetas[campo]}: {valor}"
        for campo, valor in perfil.items()
        if campo in etiquetas and valor not in (None, "")
    )


def resultado_solicitud_datos_vehiculo(sesion) -> ResultadoDiagnostico:
    """Genera la respuesta solicitando datos faltantes del vehículo si es indispensable."""
    etiquetas = {
        "marca": "marca",
        "modelo": "modelo",
        "anio": "año",
        "motor": "motor o cilindrada",
        "equipo_gas": "marca y modelo del equipo GNV/GLP",
    }
    faltantes = sesion.campos_faltantes()
    lista = "\n".join(
        f"{indice}. {etiquetas.get(campo, campo)}"
        for indice, campo in enumerate(faltantes, start=1)
    )
    solicitud = (
        f"Envíame en un solo mensaje:\n{lista}"
        if lista
        else "Solo falta confirmar el dato indicado a continuación."
    )
    aclaracion = (
        "\n\nTambién aclara el kilometraje: ¿quisiste decir *100 km* o *100 000 km*?"
        if sesion.kilometraje_por_aclarar
        else ""
    )
    return ResultadoDiagnostico(
        respuesta_texto=(
            "🔎 *Necesito aclarar un dato antes de dar una cifra exacta*\n\n"
            f"{solicitud}{aclaracion}\n\n"
            "Marca, modelo y año son opcionales y no bloquean el análisis."
        ),
        diagnostico_ml="Consulta técnica pendiente de datos del vehículo",
        confianza_ml=0.0,
        contexto_manual="",
        titulo_manual="",
        modo_diagnostico="esperando_datos_vehiculo",
        estado_sesion="esperando_datos_vehiculo",
        sintoma_evaluado=sesion.consulta_tecnica_pendiente or "",
        tipo_consulta="consulta_tecnica",
    )


def campos_requeridos_consulta_tecnica(pregunta: str) -> List[str]:
    """Los datos del vehículo enriquecen la respuesta, pero no bloquean la consulta."""
    del pregunta
    return []
