"""Regresiones del inicio explícito de casos técnicos por WhatsApp."""

from src.core.services.webhook_service import (
    _comando_caso,
    _mensaje_solicitar_perfil,
    _perfil_completo,
    _texto_perfil_vehiculo,
)
from src.core.vehicle_profile import extraer_datos_vehiculo


def test_comandos_de_caso_no_se_confunden_con_sintomas():
    assert _comando_caso("NUEVO CASO") == "nuevo"
    assert _comando_caso("otro vehículo") == "nuevo"
    assert _comando_caso("CANCELAR CONSULTA") == "cancelar"
    assert _comando_caso("no entra segunda") is None


def test_perfil_guiado_exige_marca_modelo_y_anio():
    datos = extraer_datos_vehiculo("Toyota Yaris 2018")

    assert _perfil_completo(datos)
    assert _texto_perfil_vehiculo(datos) == "Toyota YARIS 2018"
    assert "marca, modelo y año" in _mensaje_solicitar_perfil()


def test_perfil_incompleto_no_inicia_diagnostico():
    assert not _perfil_completo({"marca": "Toyota", "modelo": "YARIS"})
