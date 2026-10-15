"""Regresiones de integridad para la confirmación humana POST-TEST."""

from __future__ import annotations

import asyncio
import uuid
from types import SimpleNamespace

import pytest
from fastapi import HTTPException
from pydantic import ValidationError

from src.interfaces.api.v1.endpoints import posttest
from src.interfaces.api.v1.endpoints.posttest import ConfirmacionHumanaPostTestDTO


def _dto(**overrides: object) -> ConfirmacionHumanaPostTestDTO:
    values: dict[str, object] = {
        "falla_real": "Fuga confirmada en manguera",
        "tiempo_diagnostico_minutos": 35,
        "prediccion_correcta": 0,
        "metodo_confirmacion": "Prueba de presión en taller",
        "evidencia_ref": "orden-qa-001 / foto-qa-001",
    }
    values.update(overrides)
    return ConfirmacionHumanaPostTestDTO(**values)


@pytest.mark.parametrize(
    "campo",
    ["falla_real", "metodo_confirmacion", "evidencia_ref"],
)
def test_confirmacion_rechaza_campos_solo_con_espacios(campo: str) -> None:
    with pytest.raises(ValidationError):
        _dto(**{campo: "   "})


def test_confirmacion_requiere_referencia_de_evidencia() -> None:
    with pytest.raises(ValidationError):
        ConfirmacionHumanaPostTestDTO(
            falla_real="Fuga confirmada en manguera",
            tiempo_diagnostico_minutos=35,
            prediccion_correcta=0,
            metodo_confirmacion="Prueba de presión en taller",
        )


@pytest.mark.parametrize("campo", ["falla_real", "metodo_confirmacion"])
def test_longitud_minima_se_valida_despues_de_limpiar(campo: str) -> None:
    with pytest.raises(ValidationError):
        _dto(**{campo: " a "})


class _AsyncScope:
    async def __aenter__(self):
        return self

    async def __aexit__(self, *_args: object) -> bool:
        return False


class _SessionDouble:
    def __init__(self, caso: SimpleNamespace) -> None:
        self.caso = caso

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_args: object) -> bool:
        return False

    def begin(self) -> _AsyncScope:
        return _AsyncScope()

    async def get(self, *_args: object, **_kwargs: object) -> SimpleNamespace:
        return self.caso


def test_confirmar_posttest_no_sobrescribe_un_caso_verificado(monkeypatch: pytest.MonkeyPatch) -> None:
    taller_id = uuid.uuid4()
    caso = SimpleNamespace(
        id=uuid.uuid4(),
        taller_id=taller_id,
        tipo_registro="THESIS_POSTTEST",
        estado_registro="verificado",
        falla_real="Falla física original",
        evidencia_ref="informe-original-001",
        prediccion_correcta=1,
    )
    original = (caso.falla_real, caso.evidencia_ref, caso.prediccion_correcta)
    session = _SessionDouble(caso)

    monkeypatch.setattr(posttest, "database_configurada", lambda: True)
    monkeypatch.setattr(posttest, "obtener_engine", lambda: object())
    monkeypatch.setattr(posttest, "AsyncSession", lambda *_args, **_kwargs: session)

    with pytest.raises(HTTPException) as error:
        asyncio.run(
            posttest.confirmar_posttest(
                caso.id,
                _dto(),
                {"taller_id": str(taller_id), "usuario_id": str(uuid.uuid4())},
            )
        )

    assert error.value.status_code == 409
    assert (caso.falla_real, caso.evidencia_ref, caso.prediccion_correcta) == original
