"""Permisos de aplicación centralizados por capacidad y no por controlador."""

from __future__ import annotations

from enum import StrEnum
from typing import Any, Callable

from fastapi import Depends, HTTPException, status

from src.core.security import verificar_jwt_token


class Permiso(StrEnum):
    USUARIOS_LEER = "usuarios:leer"
    USUARIOS_GESTIONAR = "usuarios:gestionar"
    DIAGNOSTICOS_LEER = "diagnosticos:leer"
    DIAGNOSTICOS_CREAR = "diagnosticos:crear"
    DIAGNOSTICOS_CONFIRMAR = "diagnosticos:confirmar"
    METRICAS_LEER = "metricas:leer"
    TRABAJOS_GESTIONAR = "trabajos:gestionar"
    VALIDACION_LEER = "validacion:leer"
    VALIDACION_GESTIONAR = "validacion:gestionar"


_PERMISOS_POR_ROL: dict[str, frozenset[Permiso]] = {
    "administrador": frozenset(Permiso),
    "admin": frozenset(Permiso),
    "supervisor": frozenset(
        {
            Permiso.DIAGNOSTICOS_LEER,
            Permiso.DIAGNOSTICOS_CREAR,
            Permiso.DIAGNOSTICOS_CONFIRMAR,
            Permiso.METRICAS_LEER,
            Permiso.VALIDACION_LEER,
            Permiso.VALIDACION_GESTIONAR,
        }
    ),
    "jefe_taller": frozenset(
        {
            Permiso.DIAGNOSTICOS_LEER,
            Permiso.DIAGNOSTICOS_CREAR,
            Permiso.DIAGNOSTICOS_CONFIRMAR,
            Permiso.METRICAS_LEER,
            Permiso.VALIDACION_LEER,
            Permiso.VALIDACION_GESTIONAR,
        }
    ),
    "mecanico": frozenset({Permiso.DIAGNOSTICOS_LEER, Permiso.DIAGNOSTICOS_CREAR}),
    "cliente": frozenset(),
}


def tiene_permiso(payload: dict[str, Any], permiso: Permiso) -> bool:
    rol = str(payload.get("rol", "")).strip().lower()
    return permiso in _PERMISOS_POR_ROL.get(rol, frozenset())


def requerir_permiso(permiso: Permiso) -> Callable[..., dict[str, Any]]:
    """Construye una dependencia FastAPI reutilizable para una capacidad concreta."""

    def dependencia(payload: dict[str, Any] = Depends(verificar_jwt_token)) -> dict[str, Any]:
        if not tiene_permiso(payload, permiso):
            detalle = (
                "Acceso denegado. Se requiere rol administrativo para gestionar usuarios."
                if permiso == Permiso.USUARIOS_GESTIONAR
                else f"Acceso denegado. Se requiere el permiso '{permiso.value}'."
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=detalle,
            )
        return payload

    return dependencia


exigir_gestion_usuarios = requerir_permiso(Permiso.USUARIOS_GESTIONAR)
exigir_lectura_diagnosticos = requerir_permiso(Permiso.DIAGNOSTICOS_LEER)
exigir_creacion_diagnosticos = requerir_permiso(Permiso.DIAGNOSTICOS_CREAR)
exigir_confirmacion_diagnosticos = requerir_permiso(Permiso.DIAGNOSTICOS_CONFIRMAR)
exigir_lectura_metricas = requerir_permiso(Permiso.METRICAS_LEER)
exigir_gestion_trabajos = requerir_permiso(Permiso.TRABAJOS_GESTIONAR)
exigir_lectura_validacion = requerir_permiso(Permiso.VALIDACION_LEER)
exigir_gestion_validacion = requerir_permiso(Permiso.VALIDACION_GESTIONAR)
